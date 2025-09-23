from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from ...core.database import get_db
from ...models.database import MLModels, MLPredictions
from ...models.schemas import (
    MLModel as MLModelSchema,
    MLPrediction as MLPredictionSchema
)

router = APIRouter()


@router.get("/models", response_model=List[MLModelSchema])
async def get_ml_models(
    model_type: Optional[str] = Query(None, description="Type de modèle"),
    is_active: Optional[bool] = Query(None, description="Modèle actif"),
    db: Session = Depends(get_db)
):
    """Récupérer les modèles de machine learning"""
    try:
        query = db.query(MLModels)
        
        # Filtres
        if model_type:
            query = query.filter(MLModels.model_type == model_type)
        if is_active is not None:
            query = query.filter(MLModels.is_active == is_active)
        
        query = query.order_by(MLModels.created_at.desc())
        items = query.all()
        
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des modèles: {str(e)}")


@router.get("/models/{model_id}", response_model=MLModelSchema)
async def get_ml_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer un modèle de machine learning spécifique"""
    try:
        model = db.query(MLModels).filter(MLModels.id == model_id).first()
        
        if not model:
            raise HTTPException(status_code=404, detail=f"Modèle avec l'ID {model_id} non trouvé")
        
        return model
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du modèle: {str(e)}")


@router.get("/predictions", response_model=List[MLPredictionSchema])
async def get_ml_predictions(
    symbol: Optional[str] = Query(None, description="Symbole du titre"),
    model_id: Optional[int] = Query(None, description="ID du modèle"),
    prediction_type: Optional[str] = Query(None, description="Type de prédiction"),
    start_date: Optional[date] = Query(None, description="Date de début"),
    end_date: Optional[date] = Query(None, description="Date de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
):
    """Récupérer les prédictions de machine learning"""
    try:
        query = db.query(MLPredictions)
        
        # Filtres
        if symbol:
            query = query.filter(MLPredictions.symbol == symbol.upper())
        if model_id:
            query = query.filter(MLPredictions.model_id == model_id)
        if prediction_type:
            query = query.filter(MLPredictions.prediction_type == prediction_type)
        if start_date:
            query = query.filter(MLPredictions.date >= start_date)
        if end_date:
            query = query.filter(MLPredictions.date <= end_date)
        
        query = query.order_by(MLPredictions.date.desc()).limit(limit)
        items = query.all()
        
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des prédictions: {str(e)}")


@router.post("/train")
async def train_ml_model(
    model_name: str,
    model_type: str,
    training_data_start: date,
    training_data_end: date,
    db: Session = Depends(get_db)
):
    """Entraîner un nouveau modèle de machine learning"""
    try:
        # TODO: Implémenter l'entraînement des modèles
        # Cette fonction sera implémentée dans le service ML
        
        return {
            "message": f"Entraînement du modèle {model_name} en cours...",
            "model_name": model_name,
            "model_type": model_type,
            "training_data_start": training_data_start,
            "training_data_end": training_data_end
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de l'entraînement du modèle: {str(e)}")


@router.post("/predict")
async def make_prediction(
    symbol: str,
    model_id: int,
    prediction_type: str,
    db: Session = Depends(get_db)
):
    """Faire une prédiction avec un modèle"""
    try:
        # TODO: Implémenter la prédiction
        # Cette fonction sera implémentée dans le service ML
        
        return {
            "message": f"Prédiction pour {symbol} avec le modèle {model_id} en cours...",
            "symbol": symbol,
            "model_id": model_id,
            "prediction_type": prediction_type
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la prédiction: {str(e)}")


@router.get("/stats")
async def get_ml_stats(db: Session = Depends(get_db)):
    """Récupérer les statistiques des modèles ML"""
    try:
        total_models = db.query(MLModels).count()
        active_models = db.query(MLModels).filter(MLModels.is_active == True).count()
        total_predictions = db.query(MLPredictions).count()
        
        return {
            "total_models": total_models,
            "active_models": active_models,
            "total_predictions": total_predictions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des statistiques: {str(e)}")
