#!/usr/bin/env python3
"""
Script de démarrage automatique pour Celery
S'assure toujours d'être dans le bon répertoire
"""

import os
import sys
import subprocess
import signal
from pathlib import Path

def main():
    # Définir le répertoire de travail
    backend_dir = Path(__file__).parent.absolute()
    
    # Vérifier que le répertoire existe
    if not backend_dir.exists():
        print(f"❌ Erreur: Le répertoire {backend_dir} n'existe pas")
        sys.exit(1)
    
    # Changer vers le répertoire backend
    os.chdir(backend_dir)
    
    # Vérifier que nous sommes dans le bon répertoire
    celery_app_path = backend_dir / "app" / "core" / "celery_app.py"
    if not celery_app_path.exists():
        print(f"❌ Erreur: Impossible de trouver {celery_app_path}")
        print(f"   Répertoire actuel: {os.getcwd()}")
        sys.exit(1)
    
    print(f"✅ Démarrage de Celery depuis: {os.getcwd()}")
    
    # Vérifier que Redis est en cours d'exécution
    try:
        result = subprocess.run(["pgrep", "-x", "redis-server"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("⚠️  Attention: Redis ne semble pas être en cours d'exécution")
            print("   Démarrez Redis avec: brew services start redis")
    except FileNotFoundError:
        print("⚠️  Impossible de vérifier le statut de Redis")
    
    # Fonction de gestion des signaux pour un arrêt propre
    def signal_handler(sig, frame):
        print("\n🛑 Arrêt du worker Celery...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Démarrer Celery
    print("🚀 Lancement du worker Celery...")
    try:
        subprocess.run([
            "celery", "-A", "app.core.celery_app", 
            "worker", "--loglevel=info", "--concurrency=1"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du worker Celery...")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage de Celery: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()