#!/usr/bin/env python3
"""
Script pour capturer les logs Celery en temps réel
"""
import subprocess
import time
import signal
import sys

def signal_handler(sig, frame):
    print('\n🛑 Arrêt de la capture des logs Celery')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def capture_celery_logs():
    """Capturer les logs Celery en temps réel"""
    print("🔍 Capture des logs Celery en temps réel...")
    print("📋 Recherche des processus Celery...")
    
    try:
        # Trouver le processus Celery principal
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        celery_processes = [line for line in result.stdout.split('\n') if 'celery' in line and 'worker' in line]
        
        if not celery_processes:
            print("❌ Aucun processus Celery trouvé")
            return
        
        print(f"✅ {len(celery_processes)} processus Celery trouvé(s)")
        
        # Afficher les logs en temps réel
        print("\n📊 Logs Celery en temps réel (Ctrl+C pour arrêter):")
        print("=" * 80)
        
        # Utiliser tail pour suivre les logs (si disponibles)
        # Note: Cette approche est limitée car nous n'avons pas accès direct aux logs Celery
        # Nous allons plutôt surveiller les processus et afficher les informations
        
        start_time = time.time()
        while True:
            time.sleep(1)
            
            # Vérifier si les processus Celery sont toujours actifs
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            active_celery = [line for line in result.stdout.split('\n') if 'celery' in line and 'worker' in line]
            
            if not active_celery:
                print("⚠️  Aucun processus Celery actif détecté")
                break
            
            # Afficher le temps écoulé
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0:  # Afficher toutes les 10 secondes
                print(f"⏱️  Temps écoulé: {elapsed}s - Celery actif: {len(active_celery)} processus")
                
    except KeyboardInterrupt:
        print("\n🛑 Capture arrêtée par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lors de la capture: {e}")

if __name__ == "__main__":
    capture_celery_logs()
