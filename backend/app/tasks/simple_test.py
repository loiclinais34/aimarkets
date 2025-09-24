"""
Tâche de test simple avec configuration Celery simplifiée
"""
from app.core.celery_simple import celery_app

@celery_app.task(bind=True)
def simple_test_task(self):
    """
    Tâche de test très simple
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Test en cours...', 'progress': 50})
        
        # Simulation d'un travail
        import time
        time.sleep(1)
        
        self.update_state(state='SUCCESS', meta={'status': 'Test terminé!', 'progress': 100})
        
        return {
            "message": "Test réussi!",
            "status": "completed"
        }
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'status': f'Erreur: {str(e)}', 'progress': 0})
        raise e
