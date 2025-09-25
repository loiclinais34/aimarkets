"""
Tâches Celery pour l'entraînement asynchrone des modèles ML
"""

import logging
from typing import Dict, Any, List
from celery import Celery
from datetime import datetime
import traceback

# Configuration Celery
celery_app = Celery('aimarkets_ml')

# Configuration Redis comme broker
celery_app.conf.update(
    broker_url='redis://localhost:6379/0',
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max par tâche
    task_soft_time_limit=540,  # 9 minutes soft limit
)

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def train_model_task(self, model_name: str, symbol: str, X_train, y_train, X_test, y_test, parameters: Dict[str, Any] = None):
    """
    Tâche Celery pour entraîner un modèle ML de manière asynchrone
    """
    try:
        # Conversion des données de liste vers arrays NumPy si nécessaire
        import numpy as np
        if isinstance(X_train, list):
            X_train = np.array(X_train)
        if isinstance(y_train, list):
            y_train = np.array(y_train)
        if isinstance(X_test, list):
            X_test = np.array(X_test)
        if isinstance(y_test, list):
            y_test = np.array(y_test)
        
        # Mise à jour du statut
        self.update_state(
            state='PROGRESS',
            meta={
                'status': f'Initialisation du modèle {model_name}',
                'progress': 0,
                'model_name': model_name,
                'symbol': symbol
            }
        )
        
        # Import du framework de comparaison
        from app.services.model_comparison_framework import ModelComparisonFramework
        
        framework = ModelComparisonFramework()
        
        # Sélection du modèle
        if model_name not in framework.models:
            raise ValueError(f"Modèle {model_name} non disponible")
        
        model = framework.models[model_name]
        
        # Configuration des paramètres si fournis
        if parameters:
            model.parameters.update(parameters)
        
        # Mise à jour du statut
        self.update_state(
            state='PROGRESS',
            meta={
                'status': f'Entraînement du modèle {model_name} en cours...',
                'progress': 10,
                'model_name': model_name,
                'symbol': symbol
            }
        )
        
        # Entraînement du modèle
        start_time = datetime.now()
        
        # Entraînement standard pour tous les modèles
        training_result = model_instance.fit(X_train, y_train)
        
        training_time = (datetime.now() - start_time).total_seconds()
        
        # Mise à jour du statut
        self.update_state(
            state='PROGRESS',
            meta={
                'status': f'Évaluation du modèle {model_name}...',
                'progress': 80,
                'model_name': model_name,
                'symbol': symbol,
                'training_time': training_time
            }
        )
        
        # Prédictions et évaluation
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None
        
        # Calcul des métriques
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        roc_auc = None
        if y_pred_proba is not None and len(y_pred_proba.shape) > 1 and y_pred_proba.shape[1] > 1:
            try:
                roc_auc = roc_auc_score(y_test, y_pred_proba[:, 1])
            except:
                roc_auc = None
        
        # Résultat final
        result = {
            'model_name': model_name,
            'symbol': symbol,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'roc_auc': roc_auc,
            'training_time': training_time,
            'training_result': training_result,
            'status': 'completed',
            'progress': 100
        }
        
        logger.info(f"Modèle {model_name} entraîné avec succès pour {symbol} - Accuracy: {accuracy:.3f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de l'entraînement du modèle {model_name}: {e}")
        logger.error(traceback.format_exc())
        
        return {
            'model_name': model_name,
            'symbol': symbol,
            'error': str(e),
            'status': 'failed',
            'progress': 0
        }

@celery_app.task
def compare_models_async(symbol: str, models_to_test: List[str] = None, parameters: Dict[str, Any] = None):
    """
    Compare plusieurs modèles de manière asynchrone
    """
    try:
        # Import du service de comparaison
        from app.services.model_comparison_service import ModelComparisonService
        from app.core.database import get_db
        
        # Préparation des données
        db = next(get_db())
        service = ModelComparisonService(db)
        
        # Préparation des données pour le symbole
        X_train, y_train, X_test, y_test, feature_names = service.prepare_training_data(symbol)
        if X_train is None or len(X_train) == 0:
            return {'error': f'Aucune donnée disponible pour {symbol}'}
        
        # Si aucun modèle spécifié, utiliser tous les modèles disponibles
        if not models_to_test:
            models_to_test = ['RandomForest', 'XGBoost', 'LightGBM', 'NeuralNetwork']
        
        # Lancer les tâches d'entraînement
        tasks = []
        for model_name in models_to_test:
            task = train_model_task.delay(
                model_name=model_name,
                symbol=symbol,
                X_train=X_train.tolist() if hasattr(X_train, 'tolist') else X_train,
                y_train=y_train.tolist() if hasattr(y_train, 'tolist') else y_train,
                X_test=X_test.tolist() if hasattr(X_test, 'tolist') else X_test,
                y_test=y_test.tolist() if hasattr(y_test, 'tolist') else y_test,
                parameters=parameters.get(model_name) if parameters else None
            )
            tasks.append({
                'model_name': model_name,
                'task_id': task.id,
                'status': 'started'
            })
        
        return {
            'symbol': symbol,
            'tasks': tasks,
            'status': 'started',
            'total_models': len(models_to_test)
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la comparaison asynchrone: {e}")
        return {'error': str(e)}

# Tâche pour obtenir le statut d'une tâche
@celery_app.task
def get_task_status(task_id: str):
    """
    Obtient le statut d'une tâche Celery
    """
    try:
        task = celery_app.AsyncResult(task_id)
        return {
            'task_id': task_id,
            'status': task.status,
            'result': task.result,
            'info': task.info
        }
    except Exception as e:
        return {'error': str(e)}
