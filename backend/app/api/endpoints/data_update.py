"""
Endpoints API pour la gestion des mises à jour de données
"""
import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.data_update_service import DataUpdateService
from app.tasks.data_update_tasks import (
    check_data_freshness_task,
    update_historical_data_task,
    calculate_technical_indicators_task,
    update_sentiment_data_task,
    calculate_sentiment_indicators_task,
    full_data_update_workflow_task
)

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status", response_model=Dict[str, Any])
def get_data_update_status(db: Session = Depends(get_db)):
    """
    Récupérer le statut des mises à jour de données
    """
    try:
        service = DataUpdateService(db)
        status = service.get_update_status()
        
        return {
            'success': True,
            'data': status
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")

@router.get("/freshness", response_model=Dict[str, Any])
def check_data_freshness(db: Session = Depends(get_db)):
    """
    Vérifier la fraîcheur des données
    """
    try:
        service = DataUpdateService(db)
        
        historical_freshness = service.check_historical_data_freshness()
        sentiment_freshness = service.check_sentiment_data_freshness()
        
        return {
            'success': True,
            'data': {
                'historical_freshness': historical_freshness,
                'sentiment_freshness': sentiment_freshness,
                'overall_needs_update': historical_freshness.get('needs_update', False)
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de la fraîcheur: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")

@router.get("/stats", response_model=Dict[str, Any])
def get_data_stats(db: Session = Depends(get_db)):
    """
    Récupérer les statistiques des données
    """
    try:
        service = DataUpdateService(db)
        stats = service.get_data_stats()
        
        return {
            'success': True,
            'data': stats
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")

@router.post("/trigger-update", response_model=Dict[str, Any])
def trigger_data_update(
    force_update: bool = False,
    db: Session = Depends(get_db)
):
    """
    Déclencher une mise à jour complète des données via Celery
    """
    try:
        # Lancer le workflow complet de mise à jour
        task = full_data_update_workflow_task.delay(force_update=force_update)
        
        logger.info(f"Mise à jour des données déclenchée - Task ID: {task.id}")
        
        return {
            'success': True,
            'message': 'Mise à jour des données déclenchée avec succès',
            'task_id': task.id,
            'force_update': force_update
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du déclenchement de la mise à jour: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")

@router.post("/trigger-historical-update", response_model=Dict[str, Any])
def trigger_historical_data_update(
    force_update: bool = False,
    db: Session = Depends(get_db)
):
    """
    Déclencher une mise à jour des données historiques uniquement
    """
    try:
        task = update_historical_data_task.delay(force_update=force_update)
        
        logger.info(f"Mise à jour des données historiques déclenchée - Task ID: {task.id}")
        
        return {
            'success': True,
            'message': 'Mise à jour des données historiques déclenchée avec succès',
            'task_id': task.id,
            'force_update': force_update
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du déclenchement de la mise à jour historique: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")

@router.post("/trigger-sentiment-update", response_model=Dict[str, Any])
def trigger_sentiment_data_update(
    force_update: bool = False,
    db: Session = Depends(get_db)
):
    """
    Déclencher une mise à jour des données de sentiment uniquement
    """
    try:
        task = update_sentiment_data_task.delay(force_update=force_update)
        
        logger.info(f"Mise à jour des données de sentiment déclenchée - Task ID: {task.id}")
        
        return {
            'success': True,
            'message': 'Mise à jour des données de sentiment déclenchée avec succès',
            'task_id': task.id,
            'force_update': force_update
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du déclenchement de la mise à jour de sentiment: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")

@router.post("/trigger-technical-indicators", response_model=Dict[str, Any])
def trigger_technical_indicators_calculation(db: Session = Depends(get_db)):
    """
    Déclencher le calcul des indicateurs techniques
    """
    try:
        task = calculate_technical_indicators_task.delay()
        
        logger.info(f"Calcul des indicateurs techniques déclenché - Task ID: {task.id}")
        
        return {
            'success': True,
            'message': 'Calcul des indicateurs techniques déclenché avec succès',
            'task_id': task.id
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du déclenchement du calcul des indicateurs techniques: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")

@router.post("/trigger-sentiment-indicators", response_model=Dict[str, Any])
def trigger_sentiment_indicators_calculation(db: Session = Depends(get_db)):
    """
    Déclencher le calcul des indicateurs de sentiment
    """
    try:
        task = calculate_sentiment_indicators_task.delay()
        
        logger.info(f"Calcul des indicateurs de sentiment déclenché - Task ID: {task.id}")
        
        return {
            'success': True,
            'message': 'Calcul des indicateurs de sentiment déclenché avec succès',
            'task_id': task.id
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du déclenchement du calcul des indicateurs de sentiment: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")

@router.get("/task-status/{task_id}", response_model=Dict[str, Any])
def get_task_status(task_id: str):
    """
    Récupérer le statut d'une tâche Celery
    """
    try:
        from app.core.celery_app import celery_app
        
        task_result = celery_app.AsyncResult(task_id)
        
        if task_result.state == 'PENDING':
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'status': 'En attente...'
            }
        elif task_result.state == 'PROGRESS':
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'status': task_result.info.get('status', 'En cours...'),
                'progress': task_result.info.get('progress', 0),
                'current_symbol': task_result.info.get('current_symbol'),
                'total_symbols': task_result.info.get('total_symbols')
            }
        elif task_result.state == 'SUCCESS':
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'status': 'Terminé avec succès',
                'result': task_result.result
            }
        else:  # FAILURE
            response = {
                'task_id': task_id,
                'state': task_result.state,
                'status': 'Échec',
                'error': str(task_result.info)
            }
        
        return {
            'success': True,
            'data': response
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut de la tâche {task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")

@router.get("/active-tasks", response_model=Dict[str, Any])
def get_active_tasks():
    """
    Récupérer la liste des tâches actives
    """
    try:
        from app.core.celery_app import celery_app
        
        # Récupérer les tâches actives depuis Celery
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        if not active_tasks:
            return {
                'success': True,
                'data': {
                    'active_tasks': [],
                    'total_active': 0
                }
            }
        
        # Formater les tâches actives
        formatted_tasks = []
        total_active = 0
        
        for worker, tasks in active_tasks.items():
            for task in tasks:
                formatted_tasks.append({
                    'task_id': task['id'],
                    'name': task['name'],
                    'worker': worker,
                    'args': task.get('args', []),
                    'kwargs': task.get('kwargs', {}),
                    'time_start': task.get('time_start')
                })
                total_active += 1
        
        return {
            'success': True,
            'data': {
                'active_tasks': formatted_tasks,
                'total_active': total_active
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des tâches actives: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne du serveur: {e}")