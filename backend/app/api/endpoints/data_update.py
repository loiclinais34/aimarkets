"""
Endpoints API pour la mise à jour des données
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import logging

from ...core.database import get_db
from ...services.data_update_service import DataUpdateService
from ...services.polygon_service import PolygonService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/data-freshness", response_model=Dict[str, Any])
def get_data_freshness_status(db: Session = Depends(get_db)):
    """
    Récupère le statut de fraîcheur des données
    
    Returns:
        Statut de fraîcheur des données historiques et de sentiment
    """
    try:
        data_service = DataUpdateService(db)
        status = data_service.get_data_freshness_status()
        
        return {
            "status": "success",
            "data": status
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut de fraîcheur: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du statut: {str(e)}"
        )

@router.post("/update-historical/{symbol}", response_model=Dict[str, Any])
def update_historical_data_for_symbol(
    symbol: str,
    force_update: bool = False,
    db: Session = Depends(get_db)
):
    """
    Met à jour les données historiques pour un symbole spécifique
    
    Args:
        symbol: Symbole du titre à mettre à jour
        force_update: Forcer la mise à jour même si les données semblent à jour
    
    Returns:
        Résultat de la mise à jour
    """
    try:
        data_service = DataUpdateService(db)
        result = data_service.update_historical_data_for_symbol(symbol, force_update)
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des données historiques pour {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )

@router.post("/update-sentiment/{symbol}", response_model=Dict[str, Any])
def update_sentiment_data_for_symbol(
    symbol: str,
    force_update: bool = False,
    db: Session = Depends(get_db)
):
    """
    Met à jour les données de sentiment pour un symbole spécifique
    
    Args:
        symbol: Symbole du titre à mettre à jour
        force_update: Forcer la mise à jour même si les données semblent à jour
    
    Returns:
        Résultat de la mise à jour
    """
    try:
        data_service = DataUpdateService(db)
        result = data_service.update_sentiment_data_for_symbol(symbol, force_update)
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des données de sentiment pour {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )

@router.post("/update-all-historical", response_model=Dict[str, Any])
def update_all_historical_data(
    force_update: bool = False,
    max_symbols: Optional[int] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Met à jour les données historiques pour tous les symboles actifs
    
    Args:
        force_update: Forcer la mise à jour même si les données semblent à jour
        max_symbols: Nombre maximum de symboles à traiter (pour les tests)
        background_tasks: Tâches en arrière-plan
    
    Returns:
        Résultat de la mise à jour globale
    """
    try:
        data_service = DataUpdateService(db)
        
        if background_tasks and not max_symbols:
            # Exécuter en arrière-plan pour éviter les timeouts
            background_tasks.add_task(
                data_service.update_all_symbols,
                force_update=force_update
            )
            
            return {
                "status": "success",
                "message": "Mise à jour des données historiques lancée en arrière-plan",
                "data": {
                    "background_task": True,
                    "force_update": force_update
                }
            }
        else:
            # Exécution synchrone (pour les tests ou petits volumes)
            result = data_service.update_all_symbols(force_update, max_symbols)
            
            return {
                "status": "success",
                "data": result
            }
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour globale des données historiques: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour globale: {str(e)}"
        )

@router.post("/update-all-sentiment", response_model=Dict[str, Any])
def update_all_sentiment_data(
    force_update: bool = False,
    max_symbols: Optional[int] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Met à jour les données de sentiment pour tous les symboles actifs
    
    Args:
        force_update: Forcer la mise à jour même si les données semblent à jour
        max_symbols: Nombre maximum de symboles à traiter (pour les tests)
        background_tasks: Tâches en arrière-plan
    
    Returns:
        Résultat de la mise à jour globale
    """
    try:
        data_service = DataUpdateService(db)
        
        if background_tasks and not max_symbols:
            # Exécuter en arrière-plan pour éviter les timeouts
            background_tasks.add_task(
                data_service.update_all_symbols,
                force_update=force_update
            )
            
            return {
                "status": "success",
                "message": "Mise à jour des données de sentiment lancée en arrière-plan",
                "data": {
                    "background_task": True,
                    "force_update": force_update
                }
            }
        else:
            # Exécution synchrone (pour les tests ou petits volumes)
            result = data_service.update_all_symbols(force_update, max_symbols)
            
            return {
                "status": "success",
                "data": result
            }
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour globale des données de sentiment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour globale: {str(e)}"
        )

@router.post("/update-all-data", response_model=Dict[str, Any])
def update_all_data(
    force_update: bool = False,
    max_symbols: Optional[int] = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Met à jour toutes les données (historiques et de sentiment) pour tous les symboles actifs
    
    Args:
        force_update: Forcer la mise à jour même si les données semblent à jour
        max_symbols: Nombre maximum de symboles à traiter (pour les tests)
        background_tasks: Tâches en arrière-plan
    
    Returns:
        Résultat de la mise à jour globale
    """
    try:
        data_service = DataUpdateService(db)
        
        if background_tasks and not max_symbols:
            # Exécuter en arrière-plan pour éviter les timeouts
            background_tasks.add_task(
                data_service.update_all_symbols,
                force_update=force_update
            )
            
            return {
                "status": "success",
                "message": "Mise à jour complète des données lancée en arrière-plan",
                "data": {
                    "background_task": True,
                    "force_update": force_update
                }
            }
        else:
            # Exécution synchrone (pour les tests ou petits volumes)
            result = data_service.update_all_symbols(force_update, max_symbols)
            
            return {
                "status": "success",
                "data": result
            }
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour complète des données: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour complète: {str(e)}"
        )

@router.get("/symbols-status", response_model=Dict[str, Any])
def get_symbols_update_status(db: Session = Depends(get_db)):
    """
    Récupère le statut de mise à jour pour tous les symboles
    
    Returns:
        Statut de mise à jour par symbole
    """
    try:
        polygon_service = PolygonService()
        symbols = polygon_service.get_symbols_to_update(db)
        
        results = []
        
        for symbol in symbols[:10]:  # Limiter à 10 symboles pour la démo
            should_update, db_latest_date, polygon_latest_date = polygon_service.should_update_data(db, symbol)
            
            results.append({
                "symbol": symbol,
                "should_update": should_update,
                "db_latest_date": db_latest_date.isoformat() if db_latest_date else None,
                "polygon_latest_date": polygon_latest_date.isoformat() if polygon_latest_date else None,
                "days_behind": (polygon_service.get_last_trading_day() - db_latest_date).days if db_latest_date else None
            })
        
        return {
            "status": "success",
            "data": {
                "total_symbols": len(symbols),
                "sample_results": results,
                "last_trading_day": polygon_service.get_last_trading_day().isoformat(),
                "market_is_open": polygon_service.is_market_open()
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut des symboles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du statut: {str(e)}"
        )

@router.get("/market-status", response_model=Dict[str, Any])
def get_market_status():
    """
    Récupère le statut du marché Nasdaq
    
    Returns:
        Statut du marché (ouvert/fermé) et informations temporelles
    """
    try:
        polygon_service = PolygonService()
        
        return {
            "status": "success",
            "data": {
                "is_open": polygon_service.is_market_open(),
                "last_trading_day": polygon_service.get_last_trading_day().isoformat(),
                "current_date": polygon_service.get_last_trading_day().isoformat(),
                "timezone_info": {
                    "market_timezone": "America/New_York",
                    "server_timezone": "Europe/Paris",
                    "note": "Le marché Nasdaq suit le fuseau horaire de New York"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut du marché: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du statut du marché: {str(e)}"
        )
