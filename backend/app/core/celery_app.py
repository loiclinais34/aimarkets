"""
Configuration Celery pour les tâches asynchrones
"""
from celery import Celery
from app.core.config import settings

# Configuration Celery
celery_app = Celery(
    "aimarkets",
    broker=f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
    backend=f"redis://{settings.redis_host}:{settings.redis_port}/{settings.redis_db}",
    include=[
        "app.tasks.screener_tasks",
        "app.tasks.real_screener_tasks",
        "app.tasks.full_screener_tasks",
        "app.tasks.full_screener_limited_tasks",
        "app.tasks.full_screener_ml_tasks",
        "app.tasks.test_tasks",
        "app.tasks.data_update_tasks",
        "app.tasks.ml_tasks",
        "app.tasks.financial_ratios_tasks",
        "app.tasks.advanced_analysis_pipeline_tasks",
    ]
)

# Import des tâches pour les enregistrer
from app.tasks import screener_tasks, test_tasks, real_screener_tasks, full_screener_tasks, full_screener_limited_tasks, full_screener_ml_tasks, data_update_tasks, ml_tasks, financial_ratios_tasks, advanced_analysis_pipeline_tasks

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
)

# Configuration des résultats
celery_app.conf.result_expires = 3600  # 1 heure

if __name__ == "__main__":
    celery_app.start()
