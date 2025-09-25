#!/usr/bin/env python3
"""
Surveillance des logs Celery en temps réel
Pour déboguer PyTorchLSTM
"""

import subprocess
import sys
import time
from datetime import datetime

def monitor_celery_logs():
    print("📊 Surveillance des logs Celery en temps réel")
    print("=" * 60)
    print(f"Démarrage: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🔄 Surveillance active... (Ctrl+C pour arrêter)")
    print()
    
    try:
        # Commande pour surveiller les logs Celery
        # On utilise ps pour trouver le processus Celery et surveiller ses logs
        cmd = ["ps", "aux"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        celery_processes = []
        for line in result.stdout.split('\n'):
            if 'celery' in line and 'worker' in line and 'app.tasks.ml_tasks' in line:
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    celery_processes.append(pid)
                    print(f"🔍 Processus Celery trouvé: PID {pid}")
        
        if not celery_processes:
            print("❌ Aucun processus Celery trouvé")
            print("💡 Assurez-vous que le worker Celery est démarré avec:")
            print("   python3 start_celery_ml.py")
            return
        
        print(f"✅ {len(celery_processes)} processus Celery surveillés")
        print()
        
        # Surveiller les logs en continu
        while True:
            try:
                # Vérifier que les processus sont toujours actifs
                cmd = ["ps", "aux"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                active_processes = []
                for line in result.stdout.split('\n'):
                    if 'celery' in line and 'worker' in line and 'app.tasks.ml_tasks' in line:
                        parts = line.split()
                        if len(parts) > 1:
                            pid = parts[1]
                            active_processes.append(pid)
                
                if not active_processes:
                    print(f"⚠️ {datetime.now().strftime('%H:%M:%S')} - Aucun processus Celery actif")
                else:
                    print(f"✅ {datetime.now().strftime('%H:%M:%S')} - {len(active_processes)} processus Celery actifs")
                
                time.sleep(10)  # Vérifier toutes les 10 secondes
                
            except KeyboardInterrupt:
                print("\n🛑 Arrêt de la surveillance")
                break
            except Exception as e:
                print(f"⚠️ Erreur lors de la surveillance: {e}")
                time.sleep(5)
                
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de la surveillance")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    monitor_celery_logs()
