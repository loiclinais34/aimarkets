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
        "app.tasks.simple_screener_tasks", # Added simplified screener
        "app.tasks.ultra_simple_screener_tasks", # Added ultra-simplified screener
        "app.tasks.demo_screener_tasks", # Added demo screener
        "app.tasks.real_screener_tasks", # Added real screener
        "app.tasks.real_screener_limited_tasks", # Added limited real screener
        "app.tasks.real_screener_fixed_tasks", # Added fixed real screener
        "app.tasks.ultra_simple_real_tasks", # Added ultra-simple real screener
        "app.tasks.full_screener_tasks", # Added full screener
        "app.tasks.full_screener_limited_tasks", # Added full screener limited
        "app.tasks.full_screener_simple_tasks", # Added full screener simple
        "app.tasks.full_screener_ml_tasks", # Added full screener ML
        "app.tasks.full_screener_ml_limited_tasks", # Added full screener ML limited
        "app.tasks.full_screener_ml_web_tasks", # Added full screener ML web
        "app.tasks.test_tasks", # Added for testing
    ]
)

# Import des tâches pour les enregistrer
from app.tasks import screener_tasks, test_tasks, simple_screener_tasks, ultra_simple_screener_tasks, demo_screener_tasks, real_screener_tasks, real_screener_limited_tasks, real_screener_fixed_tasks, ultra_simple_real_tasks, full_screener_tasks, full_screener_limited_tasks, full_screener_simple_tasks, full_screener_ml_tasks, full_screener_ml_limited_tasks, full_screener_ml_web_tasks

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
