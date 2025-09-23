from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from ...core.database import get_db
from ...models.database import CorrelationMatrices, CrossAssetCorrelations, CorrelationFeatures
from ...models.schemas import (
    CorrelationMatrix as CorrelationMatrixSchema,
    CrossAssetCorrelation as CrossAssetCorrelationSchema,
    CorrelationFeature as CorrelationFeatureSchema
)

router = APIRouter()


@router.get("/matrices", response_model=List[CorrelationMatrixSchema])
async def get_correlation_matrices(
    symbol: Optional[str] = Query(None, description="Symbole du titre"),
    correlation_type: Optional[str] = Query(None, description="Type de corrélation"),
    start_date: Optional[date] = Query(None, description="Date de début"),
    end_date: Optional[date] = Query(None, description="Date de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
):
    """Récupérer les matrices de corrélation"""
    try:
        query = db.query(CorrelationMatrices)
        
        # Filtres
        if symbol:
            query = query.filter(CorrelationMatrices.symbol == symbol.upper())
        if correlation_type:
            query = query.filter(CorrelationMatrices.correlation_type == correlation_type)
        if start_date:
            query = query.filter(CorrelationMatrices.date >= start_date)
        if end_date:
            query = query.filter(CorrelationMatrices.date <= end_date)
        
        query = query.order_by(CorrelationMatrices.date.desc()).limit(limit)
        items = query.all()
        
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des corrélations: {str(e)}")


@router.get("/cross-asset", response_model=List[CrossAssetCorrelationSchema])
async def get_cross_asset_correlations(
    symbol1: Optional[str] = Query(None, description="Premier symbole"),
    symbol2: Optional[str] = Query(None, description="Deuxième symbole"),
    correlation_type: Optional[str] = Query(None, description="Type de corrélation"),
    start_date: Optional[date] = Query(None, description="Date de début"),
    end_date: Optional[date] = Query(None, description="Date de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
):
    """Récupérer les corrélations cross-asset"""
    try:
        query = db.query(CrossAssetCorrelations)
        
        # Filtres
        if symbol1:
            query = query.filter(CrossAssetCorrelations.symbol1 == symbol1.upper())
        if symbol2:
            query = query.filter(CrossAssetCorrelations.symbol2 == symbol2.upper())
        if correlation_type:
            query = query.filter(CrossAssetCorrelations.correlation_type == correlation_type)
        if start_date:
            query = query.filter(CrossAssetCorrelations.date >= start_date)
        if end_date:
            query = query.filter(CrossAssetCorrelations.date <= end_date)
        
        query = query.order_by(CrossAssetCorrelations.date.desc()).limit(limit)
        items = query.all()
        
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des corrélations cross-asset: {str(e)}")


@router.get("/features", response_model=List[CorrelationFeatureSchema])
async def get_correlation_features(
    symbol: Optional[str] = Query(None, description="Symbole du titre"),
    feature_type: Optional[str] = Query(None, description="Type de feature"),
    start_date: Optional[date] = Query(None, description="Date de début"),
    end_date: Optional[date] = Query(None, description="Date de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
):
    """Récupérer les features de corrélation"""
    try:
        query = db.query(CorrelationFeatures)
        
        # Filtres
        if symbol:
            query = query.filter(CorrelationFeatures.symbol == symbol.upper())
        if feature_type:
            query = query.filter(CorrelationFeatures.feature_type == feature_type)
        if start_date:
            query = query.filter(CorrelationFeatures.date >= start_date)
        if end_date:
            query = query.filter(CorrelationFeatures.date <= end_date)
        
        query = query.order_by(CorrelationFeatures.date.desc()).limit(limit)
        items = query.all()
        
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des features: {str(e)}")


@router.post("/calculate")
async def calculate_correlations(
    symbol: str,
    correlation_types: List[str] = Query(["sentiment", "technical", "combined"], description="Types de corrélation à calculer"),
    window_sizes: List[int] = Query([5, 20, 60], description="Tailles de fenêtre"),
    methods: List[str] = Query(["pearson", "spearman"], description="Méthodes de corrélation"),
    db: Session = Depends(get_db)
):
    """Calculer les corrélations pour un symbole"""
    try:
        # TODO: Implémenter le calcul des corrélations
        # Cette fonction sera implémentée dans le service des corrélations
        
        return {
            "message": f"Calcul des corrélations pour {symbol} en cours...",
            "symbol": symbol,
            "correlation_types": correlation_types,
            "window_sizes": window_sizes,
            "methods": methods
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul des corrélations: {str(e)}")


@router.get("/stats")
async def get_correlation_stats(db: Session = Depends(get_db)):
    """Récupérer les statistiques des corrélations"""
    try:
        matrices_count = db.query(CorrelationMatrices).count()
        cross_asset_count = db.query(CrossAssetCorrelations).count()
        features_count = db.query(CorrelationFeatures).count()
        
        return {
            "correlation_matrices": matrices_count,
            "cross_asset_correlations": cross_asset_count,
            "correlation_features": features_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des statistiques: {str(e)}")
