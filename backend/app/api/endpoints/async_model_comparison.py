"""
Endpoints API pour l'entraînement asynchrone des modèles ML avec Celery
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field

from ...tasks.ml_tasks import train_model_task, compare_models_async, get_task_status, celery_app

logger = logging.getLogger(__name__)

router = APIRouter()

# Modèles Pydantic pour les requêtes
class AsyncModelComparisonRequest(BaseModel):
    """Requête pour comparer les modèles de manière asynchrone"""
    symbol: str = Field(..., description="Symbole à analyser")
    models_to_test: Optional[List[str]] = Field(None, description="Liste des modèles à tester")
    parameters: Optional[Dict[str, Dict[str, Any]]] = Field(None, description="Paramètres spécifiques par modèle")

class TaskStatusRequest(BaseModel):
    """Requête pour obtenir le statut d'une tâche"""
    task_id: str = Field(..., description="ID de la tâche Celery")

@router.post("/compare-async", response_model=Dict[str, Any])
def compare_models_async_endpoint(request: AsyncModelComparisonRequest):
    """
    Lance une comparaison asynchrone de modèles
    """
    try:
        logger.info(f"Début de la comparaison asynchrone pour {request.symbol}")
        
        # Lancer la tâche asynchrone
        task = compare_models_async.delay(
            symbol=request.symbol,
            models_to_test=request.models_to_test,
            parameters=request.parameters
        )
        
        return {
            'success': True,
            'message': f'Comparaison asynchrone lancée pour {request.symbol}',
            'task_id': task.id,
            'symbol': request.symbol,
            'models_to_test': request.models_to_test or ['RandomForest', 'XGBoost', 'LightGBM', 'NeuralNetwork', 'PyTorchLSTM'],
            'status': 'started'
        }
        
    except Exception as e:
        logger.error(f"Erreur lors du lancement de la comparaison asynchrone: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement de la comparaison: {str(e)}"
        )

@router.get("/task-status/{task_id}", response_model=Dict[str, Any])
def get_task_status_endpoint(task_id: str):
    """
    Obtient le statut d'une tâche Celery
    """
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'task_id': task_id,
                'status': 'PENDING',
                'message': 'Tâche en attente...'
            }
        elif task.state == 'PROGRESS':
            response = {
                'task_id': task_id,
                'status': 'PROGRESS',
                'progress': task.info.get('progress', 0),
                'message': task.info.get('status', 'En cours...'),
                'model_name': task.info.get('model_name'),
                'symbol': task.info.get('symbol'),
                'details': task.info
            }
        elif task.state == 'SUCCESS':
            response = {
                'task_id': task_id,
                'status': 'SUCCESS',
                'result': task.result,
                'message': 'Tâche terminée avec succès'
            }
        elif task.state == 'FAILURE':
            response = {
                'task_id': task_id,
                'status': 'FAILURE',
                'error': str(task.info),
                'message': 'Tâche échouée'
            }
        else:
            response = {
                'task_id': task_id,
                'status': task.state,
                'message': f'Statut inconnu: {task.state}'
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du statut de la tâche {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du statut: {str(e)}"
        )

@router.get("/task-results/{task_id}", response_model=Dict[str, Any])
def get_task_results_endpoint(task_id: str):
    """
    Obtient les résultats d'une tâche terminée
    """
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'SUCCESS':
            return {
                'success': True,
                'task_id': task_id,
                'status': 'completed',
                'results': task.result
            }
        elif task.state == 'FAILURE':
            return {
                'success': False,
                'task_id': task_id,
                'status': 'failed',
                'error': str(task.info)
            }
        else:
            return {
                'success': False,
                'task_id': task_id,
                'status': task.state,
                'message': f'Tâche pas encore terminée. Statut: {task.state}'
            }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des résultats de la tâche {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des résultats: {str(e)}"
        )

@router.get("/active-tasks", response_model=Dict[str, Any])
def get_active_tasks_endpoint():
    """
    Obtient la liste des tâches actives
    """
    try:
        # Obtenir les tâches actives depuis Celery
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        if active_tasks:
            all_tasks = []
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    all_tasks.append({
                        'task_id': task['id'],
                        'name': task['name'],
                        'args': task['args'],
                        'kwargs': task['kwargs'],
                        'worker': worker,
                        'time_start': task.get('time_start')
                    })
            
            return {
                'success': True,
                'active_tasks': all_tasks,
                'total': len(all_tasks)
            }
        else:
            return {
                'success': True,
                'active_tasks': [],
                'total': 0,
                'message': 'Aucune tâche active'
            }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des tâches actives: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des tâches actives: {str(e)}"
        )

@router.post("/cancel-task/{task_id}", response_model=Dict[str, Any])
def cancel_task_endpoint(task_id: str):
    """
    Annule une tâche en cours
    """
    try:
        celery_app.control.revoke(task_id, terminate=True)
        
        return {
            'success': True,
            'task_id': task_id,
            'message': 'Tâche annulée avec succès'
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de l'annulation de la tâche {task_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'annulation de la tâche: {str(e)}"
        )
