#!/usr/bin/env python3
"""
Script pour démarrer Celery Worker pour l'entraînement asynchrone des modèles ML
"""

import os
import sys
import subprocess
import signal
import time

def start_celery_worker():
    """Démarre un worker Celery"""
    print("🚀 Démarrage du worker Celery pour AIMarkets ML...")
    
    # Configuration
    celery_app = "app.tasks.ml_tasks:celery_app"
    concurrency = 2  # Nombre de workers parallèles
    log_level = "info"
    
    # Commande Celery
    cmd = [
        "celery",
        "-A", celery_app,
        "worker",
        "--loglevel", log_level,
        "--concurrency", str(concurrency),
        "--pool", "solo",  # Utilise solo pool pour éviter les problèmes sur Mac M1
        "--without-gossip",
        "--without-mingle",
        "--without-heartbeat"
    ]
    
    print(f"Commande: {' '.join(cmd)}")
    
    try:
        # Démarrer le processus Celery
        process = subprocess.Popen(cmd, cwd=os.getcwd())
        
        print(f"✅ Worker Celery démarré avec PID {process.pid}")
        print("📊 Worker prêt pour l'entraînement asynchrone des modèles ML")
        print("🔄 Appuyez sur Ctrl+C pour arrêter")
        
        # Attendre l'interruption
        try:
            process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Arrêt du worker Celery...")
            process.terminate()
            process.wait()
            print("✅ Worker Celery arrêté")
            
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du worker Celery: {e}")
        return False
    
    return True

if __name__ == "__main__":
    # Vérifier que nous sommes dans le bon répertoire
    if not os.path.exists("app"):
        print("❌ Erreur: Le répertoire 'app' n'est pas trouvé")
        print("Assurez-vous d'être dans le répertoire backend")
        sys.exit(1)
    
    start_celery_worker()
