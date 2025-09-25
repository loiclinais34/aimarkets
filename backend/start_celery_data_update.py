#!/usr/bin/env python3
"""
Script pour démarrer le worker Celery pour les tâches de mise à jour de données
"""
import os
import sys
import subprocess
from pathlib import Path

# Ajouter le répertoire backend au PYTHONPATH
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def start_celery_worker():
    """Démarrer le worker Celery pour les tâches de mise à jour de données"""
    
    print("🚀 Démarrage du worker Celery pour les mises à jour de données...")
    
    # Configuration Celery
    celery_config = {
        'CELERY_BROKER_URL': 'redis://localhost:6379/0',
        'CELERY_RESULT_BACKEND': 'redis://localhost:6379/0',
        'CELERY_TASK_SERIALIZER': 'json',
        'CELERY_RESULT_SERIALIZER': 'json',
        'CELERY_ACCEPT_CONTENT': ['json'],
        'CELERY_TIMEZONE': 'UTC',
        'CELERY_ENABLE_UTC': True,
        'CELERY_TASK_TRACK_STARTED': True,
        'CELERY_TASK_TIME_LIMIT': 30 * 60,  # 30 minutes
        'CELERY_TASK_SOFT_TIME_LIMIT': 25 * 60,  # 25 minutes
        'CELERY_WORKER_PREFETCH_MULTIPLIER': 1,
        'CELERY_WORKER_MAX_TASKS_PER_CHILD': 50,
    }
    
    # Construire la commande Celery
    cmd = [
        'celery',
        '-A', 'app.core.celery_app',
        'worker',
        '--loglevel=info',
        '--concurrency=2',
        '--queues=data_update,ml_tasks',
        '--hostname=data-update-worker@%h',
        '--without-gossip',
        '--without-mingle',
        '--without-heartbeat'
    ]
    
    # Ajouter les variables d'environnement
    env = os.environ.copy()
    for key, value in celery_config.items():
        env[key] = value
    
    try:
        print(f"Commande: {' '.join(cmd)}")
        print("Configuration Celery:")
        for key, value in celery_config.items():
            print(f"  {key}: {value}")
        print()
        
        # Démarrer le worker
        process = subprocess.Popen(
            cmd,
            env=env,
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        print(f"✅ Worker Celery démarré avec PID: {process.pid}")
        print("📋 Logs du worker:")
        print("-" * 50)
        
        # Afficher les logs en temps réel
        for line in iter(process.stdout.readline, ''):
            print(line.rstrip())
        
        process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du worker Celery...")
        if 'process' in locals():
            process.terminate()
            process.wait()
        print("✅ Worker Celery arrêté")
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du worker Celery: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_celery_worker()
