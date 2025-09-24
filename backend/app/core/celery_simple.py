"""
Configuration Celery simplifiée pour les tâches asynchrones
"""
from celery import Celery
import os

# Configuration Redis simple
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Configuration Celery
celery_app = Celery(
    "aimarkets",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

# Configuration des tâches
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max par tâche
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=True,
    broker_connection_retry_on_startup=True,
)

# Configuration des résultats
celery_app.conf.result_expires = 3600  # 1 heure

if __name__ == "__main__":
    celery_app.start()
