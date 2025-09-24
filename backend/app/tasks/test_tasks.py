"""
Tâches de test simples pour déboguer Celery
"""
from celery import current_task
from app.core.celery_app import celery_app

@celery_app.task(bind=True, name="test_simple_task")
def test_simple_task(self):
    """
    Tâche de test simple
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Test en cours...', 'progress': 50})
        
        # Simulation d'un travail
        import time
        time.sleep(2)
        
        self.update_state(state='SUCCESS', meta={'status': 'Test terminé!', 'progress': 100})
        
        return {
            "message": "Test réussi!",
            "status": "completed"
        }
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'status': f'Erreur: {str(e)}', 'progress': 0})
        raise e
