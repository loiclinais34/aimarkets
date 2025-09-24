"""
Endpoints API pour la gestion de Celery
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from ...core.database import get_db
from ...services.celery_manager import CeleryManager

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/celery/status", response_model=Dict[str, Any])
def get_celery_status():
    """
    Récupère le statut de Celery et Redis
    
    Returns:
        Statut complet de Celery et Redis
    """
    try:
        celery_manager = CeleryManager()
        status = celery_manager.get_celery_status()
        
        return {
            "status": "success",
            "data": status
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut de Celery: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du statut: {str(e)}"
        )

@router.post("/celery/start", response_model=Dict[str, Any])
def start_celery():
    """
    Démarre Celery en arrière-plan
    
    Returns:
        Résultat du démarrage de Celery
    """
    try:
        celery_manager = CeleryManager()
        result = celery_manager.start_celery()
        
        if result['success']:
            return {
                "status": "success",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['error']
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du démarrage de Celery: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du démarrage: {str(e)}"
        )

@router.post("/celery/stop", response_model=Dict[str, Any])
def stop_celery():
    """
    Arrête tous les processus Celery
    
    Returns:
        Résultat de l'arrêt de Celery
    """
    try:
        celery_manager = CeleryManager()
        result = celery_manager.stop_celery()
        
        return {
            "status": "success",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'arrêt de Celery: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'arrêt: {str(e)}"
        )

@router.post("/celery/ensure-running", response_model=Dict[str, Any])
def ensure_celery_running():
    """
    S'assure que Celery est en cours d'exécution
    Le démarre automatiquement si nécessaire
    
    Returns:
        Résultat de l'opération
    """
    try:
        celery_manager = CeleryManager()
        result = celery_manager.ensure_celery_running()
        
        if result['success']:
            return {
                "status": "success",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['error']
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la vérification/démarrage de Celery: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'opération: {str(e)}"
        )

@router.get("/celery/health", response_model=Dict[str, Any])
def celery_health_check():
    """
    Vérification de santé rapide de Celery
    
    Returns:
        Statut de santé de Celery
    """
    try:
        celery_manager = CeleryManager()
        status = celery_manager.get_celery_status()
        
        if status['ready']:
            return {
                "status": "healthy",
                "message": "Celery et Redis sont opérationnels",
                "data": {
                    "celery_running": status['celery_running'],
                    "redis_running": status['redis_running']
                }
            }
        else:
            return {
                "status": "unhealthy",
                "message": "Celery ou Redis ne sont pas opérationnels",
                "data": {
                    "celery_running": status['celery_running'],
                    "redis_running": status['redis_running']
                }
            }
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de santé de Celery: {e}")
        return {
            "status": "error",
            "message": f"Erreur lors de la vérification: {str(e)}",
            "data": {}
        }
