"""
Endpoints API pour les modèles LightGBM
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.schemas import (
    ModelTrainingRequest, ModelTrainingResponse, PredictionRequest, PredictionResponse,
    MLModel, ModelPerformance
)
from app.services.lightgbm_service import LightGBMService

router = APIRouter()


@router.post("/train/binary", response_model=ModelTrainingResponse)
async def train_binary_classification_model(
    symbol: str,
    target_parameter_id: int,
    db: Session = Depends(get_db)
):
    """Entraîne un modèle LightGBM de classification binaire"""
    try:
        service = LightGBMService(db)
        
        # Récupération du paramètre cible
        from app.models.database import TargetParameters
        target_param = db.query(TargetParameters).filter(
            TargetParameters.id == target_parameter_id
        ).first()
        
        if not target_param:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paramètre cible non trouvé"
            )
        
        result = service.train_binary_classification_model(
            symbol=symbol,
            target_param=target_param,
            db=db
        )
        
        return ModelTrainingResponse(
            model_id=result["model_id"],
            model_name=result["model_name"],
            model_type="lightgbm_binary_classification",
            symbol=symbol,
            performance=ModelPerformance(**result["performance"]),
            training_samples=result["training_samples"],
            test_samples=result["test_samples"],
            message="Modèle LightGBM de classification binaire entraîné avec succès"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'entraînement: {str(e)}"
        )


@router.post("/train/multiclass", response_model=ModelTrainingResponse)
async def train_multiclass_classification_model(
    symbol: str,
    target_parameter_id: int,
    db: Session = Depends(get_db)
):
    """Entraîne un modèle LightGBM de classification multi-classe"""
    try:
        service = LightGBMService(db)
        
        # Récupération du paramètre cible
        from app.models.database import TargetParameters
        target_param = db.query(TargetParameters).filter(
            TargetParameters.id == target_parameter_id
        ).first()
        
        if not target_param:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paramètre cible non trouvé"
            )
        
        result = service.train_multiclass_classification_model(
            symbol=symbol,
            target_param=target_param,
            db=db
        )
        
        return ModelTrainingResponse(
            model_id=result["model_id"],
            model_name=result["model_name"],
            model_type="lightgbm_multiclass_classification",
            symbol=symbol,
            performance=ModelPerformance(**result["performance"]),
            training_samples=result["training_samples"],
            test_samples=result["test_samples"],
            message="Modèle LightGBM de classification multi-classe entraîné avec succès"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'entraînement: {str(e)}"
        )


@router.post("/train/regression", response_model=ModelTrainingResponse)
async def train_regression_model(
    symbol: str,
    target_parameter_id: int,
    db: Session = Depends(get_db)
):
    """Entraîne un modèle LightGBM de régression"""
    try:
        service = LightGBMService(db)
        
        # Récupération du paramètre cible
        from app.models.database import TargetParameters
        target_param = db.query(TargetParameters).filter(
            TargetParameters.id == target_parameter_id
        ).first()
        
        if not target_param:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paramètre cible non trouvé"
            )
        
        result = service.train_regression_model(
            symbol=symbol,
            target_param=target_param,
            db=db
        )
        
        return ModelTrainingResponse(
            model_id=result["model_id"],
            model_name=result["model_name"],
            model_type="lightgbm_regression",
            symbol=symbol,
            performance=ModelPerformance(**result["performance"]),
            training_samples=result["training_samples"],
            test_samples=result["test_samples"],
            message="Modèle LightGBM de régression entraîné avec succès"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'entraînement: {str(e)}"
        )


@router.post("/predict", response_model=PredictionResponse)
async def predict_with_lightgbm(
    request: PredictionRequest,
    db: Session = Depends(get_db)
):
    """Effectue une prédiction avec un modèle LightGBM"""
    try:
        service = LightGBMService(db)
        
        result = service.predict(
            model_id=request.model_id,
            symbol=symbol,
            prediction_date=request.prediction_date,
            db=db
        )
        
        return PredictionResponse(
            prediction_id=result["prediction_id"],
            model_id=result["model_id"],
            symbol=result["symbol"],
            prediction_date=result["prediction_date"],
            prediction_value=result["prediction_value"],
            prediction_class=result["prediction_class"],
            confidence=result["confidence"],
            data_date_used=result["data_date_used"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la prédiction: {str(e)}"
        )


@router.get("/models", response_model=List[MLModel])
async def get_lightgbm_models(
    active_only: bool = True,
    symbol: Optional[str] = None,
    model_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Récupère la liste des modèles LightGBM"""
    try:
        from app.models.database import MLModels
        
        query = db.query(MLModels).filter(
            MLModels.model_type.like("lightgbm_%")
        )
        
        if active_only:
            query = query.filter(MLModels.is_active == True)
        
        if symbol:
            query = query.filter(MLModels.symbol == symbol)
        
        if model_type:
            query = query.filter(MLModels.model_type == model_type)
        
        models = query.order_by(MLModels.created_at.desc()).all()
        
        return [
            MLModel(
                id=model.id,
                name=model.name,
                model_type=model.model_type,
                symbol=model.symbol,
                target_parameter_id=model.target_parameter_id,
                model_parameters=model.model_parameters,
                performance_metrics=model.performance_metrics,
                model_path=model.model_path,
                is_active=model.is_active,
                created_at=model.created_at,
                updated_at=model.updated_at,
                created_by=model.created_by
            )
            for model in models
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des modèles: {str(e)}"
        )


@router.get("/models/{model_id}", response_model=MLModel)
async def get_lightgbm_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Récupère un modèle LightGBM spécifique"""
    try:
        from app.models.database import MLModels
        
        model = db.query(MLModels).filter(
            MLModels.id == model_id,
            MLModels.model_type.like("lightgbm_%")
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modèle LightGBM non trouvé"
            )
        
        return MLModel(
            id=model.id,
            name=model.name,
            model_type=model.model_type,
            symbol=model.symbol,
            target_parameter_id=model.target_parameter_id,
            model_parameters=model.model_parameters,
            performance_metrics=model.performance_metrics,
            model_path=model.model_path,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du modèle: {str(e)}"
        )


@router.put("/models/{model_id}/activate")
async def activate_lightgbm_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Active un modèle LightGBM"""
    try:
        from app.models.database import MLModels
        
        model = db.query(MLModels).filter(
            MLModels.id == model_id,
            MLModels.model_type.like("lightgbm_%")
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modèle LightGBM non trouvé"
            )
        
        model.is_active = True
        db.commit()
        
        return {"message": "Modèle LightGBM activé avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'activation du modèle: {str(e)}"
        )


@router.put("/models/{model_id}/deactivate")
async def deactivate_lightgbm_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Désactive un modèle LightGBM"""
    try:
        from app.models.database import MLModels
        
        model = db.query(MLModels).filter(
            MLModels.id == model_id,
            MLModels.model_type.like("lightgbm_%")
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modèle LightGBM non trouvé"
            )
        
        model.is_active = False
        db.commit()
        
        return {"message": "Modèle LightGBM désactivé avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la désactivation du modèle: {str(e)}"
        )


@router.delete("/models/{model_id}")
async def delete_lightgbm_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Supprime un modèle LightGBM"""
    try:
        from app.models.database import MLModels
        import os
        
        model = db.query(MLModels).filter(
            MLModels.id == model_id,
            MLModels.model_type.like("lightgbm_%")
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Modèle LightGBM non trouvé"
            )
        
        # Suppression du fichier de modèle
        if model.model_path and os.path.exists(model.model_path):
            os.remove(model.model_path)
        
        # Suppression de la base de données
        db.delete(model)
        db.commit()
        
        return {"message": "Modèle LightGBM supprimé avec succès"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression du modèle: {str(e)}"
        )


@router.get("/stats/overview")
async def get_lightgbm_stats_overview(db: Session = Depends(get_db)):
    """Récupère les statistiques globales des modèles LightGBM"""
    try:
        from app.models.database import MLModels
        from sqlalchemy import func
        
        # Statistiques générales
        total_models = db.query(MLModels).filter(
            MLModels.model_type.like("lightgbm_%")
        ).count()
        
        active_models = db.query(MLModels).filter(
            MLModels.model_type.like("lightgbm_%"),
            MLModels.is_active == True
        ).count()
        
        # Statistiques par type
        type_stats = db.query(
            MLModels.model_type,
            func.count(MLModels.id).label('count')
        ).filter(
            MLModels.model_type.like("lightgbm_%")
        ).group_by(MLModels.model_type).all()
        
        # Statistiques par symbole
        symbol_stats = db.query(
            MLModels.symbol,
            func.count(MLModels.id).label('count')
        ).filter(
            MLModels.model_type.like("lightgbm_%")
        ).group_by(MLModels.symbol).order_by(func.count(MLModels.id).desc()).limit(10).all()
        
        return {
            "total_models": total_models,
            "active_models": active_models,
            "inactive_models": total_models - active_models,
            "models_by_type": [
                {"type": stat.model_type, "count": stat.count}
                for stat in type_stats
            ],
            "top_symbols": [
                {"symbol": stat.symbol, "count": stat.count}
                for stat in symbol_stats
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )
