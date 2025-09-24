from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.core.database import get_db
from app.models.database import MLModels, TargetParameters
from app.models.schemas import (
    MLModel, MLModelCreate, ModelTrainingRequest, ModelTrainingResponse,
    PredictionRequest, PredictionResponse, ModelPerformance, MessageResponse
)
from app.services.ml_service import MLService

router = APIRouter(prefix="/ml-models", tags=["ml-models"])


@router.post("/train", response_model=ModelTrainingResponse)
def train_model(
    training_request: ModelTrainingRequest,
    db: Session = Depends(get_db)
):
    """Entraîner un nouveau modèle de machine learning"""
    try:
        # Vérifier que le paramètre de cible existe
        target_param = db.query(TargetParameters).filter(
            TargetParameters.id == training_request.target_parameter_id
        ).first()
        
        if not target_param:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paramètre de cible non trouvé"
            )
        
        if not target_param.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le paramètre de cible n'est pas actif"
            )
        
        ml_service = MLService(db)
        
        # Entraîner le modèle selon le type
        if training_request.model_type == "classification":
            result = ml_service.train_classification_model(
                training_request.symbol, target_param, db
            )
        elif training_request.model_type == "regression":
            result = ml_service.train_regression_model(
                training_request.symbol, target_param, db
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Type de modèle non supporté. Utilisez 'classification' ou 'regression'"
            )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        # Préparer la réponse
        performance_metrics = {}
        if training_request.model_type == "classification":
            performance_metrics = {
                "accuracy": result["accuracy"],
                "precision": result["precision"],
                "recall": result["recall"],
                "f1_score": result["f1_score"],
                "cv_mean": result["cv_mean"],
                "cv_std": result["cv_std"]
            }
        else:  # regression
            performance_metrics = {
                "r2_score": result["r2_score"],
                "rmse": result["rmse"],
                "mse": result["mse"],
                "cv_mean": result["cv_mean"],
                "cv_std": result["cv_std"]
            }
        
        training_data_info = {
            "symbol": training_request.symbol,
            "target_parameter": target_param.parameter_name,
            "target_return_percentage": target_param.target_return_percentage,
            "time_horizon_days": target_param.time_horizon_days,
            "test_size": training_request.test_size,
            "random_state": training_request.random_state
        }
        
        return ModelTrainingResponse(
            model_id=result["model_id"],
            model_name=result["model_name"],
            model_type=training_request.model_type,
            performance_metrics=performance_metrics,
            feature_importance=result["feature_importance"],
            training_data_info=training_data_info,
            message=f"Modèle {training_request.model_type} entraîné avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'entraînement du modèle: {str(e)}"
        )


@router.get("/", response_model=List[MLModel])
def list_models(
    skip: int = 0,
    limit: int = 100,
    model_type: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Lister tous les modèles ML"""
    try:
        query = db.query(MLModels)
        
        if model_type:
            query = query.filter(MLModels.model_type == model_type)
        
        if active_only:
            query = query.filter(MLModels.is_active == True)
        
        models = query.offset(skip).limit(limit).all()
        
        # Extraire les scores depuis performance_metrics
        for model in models:
            if model.performance_metrics:
                # Extraire directement les scores stockés
                if "validation_score" in model.performance_metrics:
                    model.validation_score = model.performance_metrics["validation_score"]
                if "test_score" in model.performance_metrics:
                    model.test_score = model.performance_metrics["test_score"]
                
                # Extraire les dates d'entraînement depuis model_parameters
                if model.model_parameters:
                    if "training_data_start" in model.model_parameters:
                        model.training_data_start = model.model_parameters["training_data_start"]
                    if "training_data_end" in model.model_parameters:
                        model.training_data_end = model.model_parameters["training_data_end"]
        
        return models
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des modèles: {str(e)}"
        )


@router.get("/{model_id}", response_model=MLModel)
def get_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer un modèle ML par ID"""
    try:
        model = db.query(MLModels).filter(MLModels.id == model_id).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modèle non trouvé"
            )
        
        # Extraire les scores depuis performance_metrics
        if model.performance_metrics:
            # Extraire directement les scores stockés
            if "validation_score" in model.performance_metrics:
                model.validation_score = model.performance_metrics["validation_score"]
            if "test_score" in model.performance_metrics:
                model.test_score = model.performance_metrics["test_score"]
            
            # Extraire les dates d'entraînement depuis model_parameters
            if model.model_parameters:
                if "training_data_start" in model.model_parameters:
                    model.training_data_start = model.model_parameters["training_data_start"]
                if "training_data_end" in model.model_parameters:
                    model.training_data_end = model.model_parameters["training_data_end"]
        
        return model
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du modèle: {str(e)}"
        )


@router.get("/{model_id}/performance", response_model=ModelPerformance)
def get_model_performance(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer les performances d'un modèle"""
    try:
        ml_service = MLService(db)
        performance = ml_service.get_model_performance(model_id)
        
        if "error" in performance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=performance["error"]
            )
        
        return ModelPerformance(**performance)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des performances: {str(e)}"
        )


@router.post("/predict", response_model=PredictionResponse)
def make_prediction(
    prediction_request: PredictionRequest,
    db: Session = Depends(get_db)
):
    """Faire une prédiction avec un modèle entraîné"""
    try:
        # Vérifier que le modèle existe et est actif
        model = db.query(MLModels).filter(
            MLModels.id == prediction_request.model_id,
            MLModels.is_active == True
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modèle non trouvé ou inactif"
            )
        
        ml_service = MLService(db)
        
        # Faire la prédiction
        result = ml_service.predict(
            prediction_request.symbol,
            prediction_request.model_id,
            prediction_request.prediction_date,
            db
        )
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return PredictionResponse(
            symbol=result["symbol"],
            prediction_date=result["date"],
            prediction=result["prediction"],
            confidence=result["confidence"],
            prediction_type=result["prediction_type"],
            model_name=result["model_name"],
            features_used=result.get("features_used", []),
            data_date_used=result.get("data_date_used")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la prédiction: {str(e)}"
        )


@router.put("/{model_id}/activate", response_model=MessageResponse)
def activate_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Activer un modèle ML"""
    try:
        model = db.query(MLModels).filter(MLModels.id == model_id).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modèle non trouvé"
            )
        
        model.is_active = True
        model.updated_at = datetime.utcnow()
        db.commit()
        
        return MessageResponse(
            message=f"Modèle '{model.model_name}' activé avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'activation du modèle: {str(e)}"
        )


@router.put("/{model_id}/deactivate", response_model=MessageResponse)
def deactivate_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Désactiver un modèle ML"""
    try:
        model = db.query(MLModels).filter(MLModels.id == model_id).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modèle non trouvé"
            )
        
        model.is_active = False
        model.updated_at = datetime.utcnow()
        db.commit()
        
        return MessageResponse(
            message=f"Modèle '{model.model_name}' désactivé avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la désactivation du modèle: {str(e)}"
        )


@router.delete("/{model_id}", response_model=MessageResponse)
def delete_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Supprimer un modèle ML (désactivation)"""
    try:
        model = db.query(MLModels).filter(MLModels.id == model_id).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modèle non trouvé"
            )
        
        # Désactiver au lieu de supprimer
        model.is_active = False
        model.updated_at = datetime.utcnow()
        db.commit()
        
        return MessageResponse(
            message=f"Modèle '{model.model_name}' supprimé avec succès"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression du modèle: {str(e)}"
        )


@router.get("/symbol/{symbol}", response_model=List[MLModel])
def get_models_for_symbol(
    symbol: str,
    model_type: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Récupérer les modèles pour un symbole spécifique"""
    try:
        query = db.query(MLModels).filter(
            MLModels.model_name.like(f"%{symbol}%")
        )
        
        if model_type:
            query = query.filter(MLModels.model_type == model_type)
        
        if active_only:
            query = query.filter(MLModels.is_active == True)
        
        models = query.all()
        
        return models
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des modèles: {str(e)}"
        )


@router.get("/stats/overview")
def get_models_stats(
    db: Session = Depends(get_db)
):
    """Obtenir des statistiques globales sur les modèles ML"""
    try:
        # Compter les modèles par type
        classification_count = db.query(MLModels).filter(
            MLModels.model_type == "classification",
            MLModels.is_active == True
        ).count()
        
        regression_count = db.query(MLModels).filter(
            MLModels.model_type == "regression",
            MLModels.is_active == True
        ).count()
        
        total_count = db.query(MLModels).filter(
            MLModels.is_active == True
        ).count()
        
        # Obtenir les performances moyennes depuis performance_metrics
        models = db.query(MLModels).filter(
            MLModels.is_active == True
        ).all()
        
        if models:
            # Extraire les scores depuis performance_metrics
            validation_scores = []
            test_scores = []
            
            for model in models:
                if model.performance_metrics:
                    # Pour les modèles de classification
                    if model.model_type == "classification":
                        if "accuracy" in model.performance_metrics:
                            validation_scores.append(model.performance_metrics["accuracy"])
                        if "f1_score" in model.performance_metrics:
                            test_scores.append(model.performance_metrics["f1_score"])
                    # Pour les modèles de régression
                    elif model.model_type == "regression":
                        if "r2_score" in model.performance_metrics:
                            validation_scores.append(model.performance_metrics["r2_score"])
                        if "mse" in model.performance_metrics:
                            test_scores.append(model.performance_metrics["mse"])
            
            stats = {
                "total_models": total_count,
                "classification_models": classification_count,
                "regression_models": regression_count,
                "average_validation_score": sum(validation_scores) / len(validation_scores) if validation_scores else None,
                "average_test_score": sum(test_scores) / len(test_scores) if test_scores else None,
                "models_with_validation": len(validation_scores),
                "models_with_test": len(test_scores)
            }
        else:
            stats = {
                "total_models": 0,
                "classification_models": 0,
                "regression_models": 0,
                "average_validation_score": None,
                "average_test_score": None,
                "models_with_validation": 0,
                "models_with_test": 0
            }
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )


@router.get("/{model_id}/shap-explanations")
def get_shap_explanations(
    model_id: int,
    symbol: str,
    prediction_date: str,
    db: Session = Depends(get_db)
):
    """Récupérer les explications SHAP pour une prédiction"""
    try:
        from datetime import datetime
        prediction_date_obj = datetime.strptime(prediction_date, "%Y-%m-%d").date()
        
        ml_service = MLService(db=db)
        result = ml_service.calculate_shap_explanations(model_id, symbol, prediction_date_obj, db)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Format de date invalide. Utilisez YYYY-MM-DD"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des explications SHAP: {str(e)}"
        )


@router.get("/{model_id}/feature-importance")
def get_model_feature_importance(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer l'importance des features d'un modèle"""
    try:
        ml_service = MLService(db=db)
        result = ml_service.get_model_feature_importance(model_id, db)
        
        if "error" in result:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de l'importance des features: {str(e)}"
        )


@router.get("/analysis/{symbol}", response_model=Dict[str, Any])
def get_detailed_analysis(symbol: str, model_id: int, db: Session = Depends(get_db)):
    """Récupérer l'analyse détaillée complète pour un symbole"""
    try:
        from app.services.ml_service import MLService
        from app.models.database import HistoricalData, TechnicalIndicators, SentimentIndicators, MLModels
        
        ml_service = MLService(db)
        
        # 1. Récupérer le modèle
        model = db.query(MLModels).filter(MLModels.id == model_id).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modèle non trouvé"
            )
        
        # 2. Récupérer les données historiques récentes (30 derniers jours)
        historical_data = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol
        ).order_by(HistoricalData.date.desc()).limit(30).all()
        
        if not historical_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune donnée historique trouvée pour {symbol}"
            )
        
        # 3. Récupérer les indicateurs techniques récents
        latest_date = historical_data[0].date
        technical_indicators = db.query(TechnicalIndicators).filter(
            TechnicalIndicators.symbol == symbol,
            TechnicalIndicators.date == latest_date
        ).first()
        
        # 4. Récupérer les indicateurs de sentiment récents
        sentiment_indicators = db.query(SentimentIndicators).filter(
            SentimentIndicators.symbol == symbol,
            SentimentIndicators.date == latest_date
        ).first()
        
        # 5. Calculer les explications SHAP
        shap_explanations = ml_service.calculate_shap_explanations(model_id, symbol, latest_date, db)
        
        # 6. Préparer les données historiques pour les graphiques
        chart_data = []
        for data in reversed(historical_data):  # Inverser pour avoir l'ordre chronologique
            chart_data.append({
                "date": data.date.isoformat(),
                "open": float(data.open),
                "high": float(data.high),
                "low": float(data.low),
                "close": float(data.close),
                "volume": data.volume,
                "vwap": float(data.vwap) if data.vwap else None
            })
        
        # 7. Préparer les indicateurs techniques pour les graphiques
        technical_data = {}
        if technical_indicators:
            technical_data = {
                "sma_20": float(technical_indicators.sma_20) if technical_indicators.sma_20 else None,
                "ema_20": float(technical_indicators.ema_20) if technical_indicators.ema_20 else None,
                "rsi_14": float(technical_indicators.rsi_14) if technical_indicators.rsi_14 else None,
                "macd": float(technical_indicators.macd) if technical_indicators.macd else None,
                "macd_signal": float(technical_indicators.macd_signal) if technical_indicators.macd_signal else None,
                "bb_upper": float(technical_indicators.bb_upper) if technical_indicators.bb_upper else None,
                "bb_middle": float(technical_indicators.bb_middle) if technical_indicators.bb_middle else None,
                "bb_lower": float(technical_indicators.bb_lower) if technical_indicators.bb_lower else None,
                "atr_14": float(technical_indicators.atr_14) if technical_indicators.atr_14 else None,
                "obv": float(technical_indicators.obv) if technical_indicators.obv else None,
            }
        
        # 8. Préparer les indicateurs de sentiment
        sentiment_data = {}
        if sentiment_indicators:
            sentiment_data = {
                "sentiment_score_normalized": float(sentiment_indicators.sentiment_score_normalized) if sentiment_indicators.sentiment_score_normalized else None,
                "sentiment_momentum_7d": float(sentiment_indicators.sentiment_momentum_7d) if sentiment_indicators.sentiment_momentum_7d else None,
                "sentiment_volatility_14d": float(sentiment_indicators.sentiment_volatility_14d) if sentiment_indicators.sentiment_volatility_14d else None,
                "news_positive_ratio": float(sentiment_indicators.news_positive_ratio) if sentiment_indicators.news_positive_ratio else None,
                "news_negative_ratio": float(sentiment_indicators.news_negative_ratio) if sentiment_indicators.news_negative_ratio else None,
            }
        
        # 9. Informations sur le modèle
        model_info = {
            "id": model.id,
            "name": model.model_name,
            "version": model.model_version,
            "type": model.model_type,
            "target_return": float(model.target_parameter.target_return_percentage) if model.target_parameter else None,
            "time_horizon": model.target_parameter.time_horizon_days if model.target_parameter else None,
            "created_at": model.created_at.isoformat() if model.created_at else None,
        }
        
        return {
            "symbol": symbol,
            "model_info": model_info,
            "chart_data": chart_data,
            "technical_indicators": technical_data,
            "sentiment_indicators": sentiment_data,
            "shap_explanations": shap_explanations,
            "analysis_date": latest_date.isoformat(),
            "data_points": len(chart_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse détaillée: {str(e)}"
        )
