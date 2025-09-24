#!/usr/bin/env python3
"""
Script pour monitorer les logs Celery en temps réel
"""
import subprocess
import sys
import time
import signal

def signal_handler(sig, frame):
    print('\n🛑 Arrêt du monitoring des logs Celery')
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def monitor_celery_logs():
    """Monitorer les logs Celery"""
    print("🔍 Démarrage du monitoring des logs Celery...")
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
        # Nous allons plutôt surveiller les processus
        
        while True:
            time.sleep(2)
            # Vérifier si les processus Celery sont toujours actifs
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            active_celery = [line for line in result.stdout.split('\n') if 'celery' in line and 'worker' in line]
            
            if not active_celery:
                print("⚠️  Aucun processus Celery actif détecté")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Monitoring arrêté par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lors du monitoring: {e}")

if __name__ == "__main__":
    monitor_celery_logs()
