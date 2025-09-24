#!/usr/bin/env python3
"""
Script pour surveiller les logs de Celery et diagnostiquer les problèmes
"""
import subprocess
import time
import sys

def monitor_celery_logs():
    """Surveille les logs de Celery en temps réel"""
    print("🔍 Surveillance des logs de Celery...")
    print("Appuyez sur Ctrl+C pour arrêter")
    print("=" * 60)
    
    try:
        # Lancer celery avec les logs en temps réel
        process = subprocess.Popen(
            ['celery', '-A', 'app.core.celery_app', 'worker', '--loglevel=debug'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        for line in iter(process.stdout.readline, ''):
            print(f"[CELERY] {line.strip()}")
            
    except KeyboardInterrupt:
        print("\n🛑 Arrêt de la surveillance")
        process.terminate()
    except Exception as e:
        print(f"❌ Erreur lors de la surveillance: {e}")

def check_task_status(task_id):
    """Vérifie le statut d'une tâche spécifique"""
    print(f"🔍 Vérification du statut de la tâche: {task_id}")
    
    try:
        result = subprocess.run(
            ['celery', '-A', 'app.core.celery_app', 'inspect', 'active'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Tâches actives:")
            print(result.stdout)
        else:
            print(f"❌ Erreur: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")

def check_redis_connection():
    """Vérifie la connexion Redis"""
    print("🔍 Vérification de la connexion Redis...")
    
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        info = r.info()
        print(f"✅ Redis connecté - Version: {info.get('redis_version')}")
        print(f"   Mémoire utilisée: {info.get('used_memory_human')}")
        print(f"   Clients connectés: {info.get('connected_clients')}")
        
        # Vérifier les queues
        queues = r.keys('celery*')
        print(f"   Queues Celery: {len(queues)} trouvées")
        
    except Exception as e:
        print(f"❌ Erreur de connexion Redis: {e}")

def main():
    """Fonction principale"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "monitor":
            monitor_celery_logs()
        elif sys.argv[1] == "status":
            check_task_status(sys.argv[2] if len(sys.argv) > 2 else None)
        elif sys.argv[1] == "redis":
            check_redis_connection()
        else:
            print("Usage: python3 monitor_celery.py [monitor|status|redis]")
    else:
        print("🔧 Diagnostic de Celery")
        print("=" * 40)
        
        # Vérifications de base
        check_redis_connection()
        print()
        
        # Vérifier les tâches actives
        try:
            result = subprocess.run(
                ['celery', '-A', 'app.core.celery_app', 'inspect', 'active'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                print("✅ Tâches actives:")
                print(result.stdout)
            else:
                print(f"❌ Erreur: {result.stderr}")
                
        except Exception as e:
            print(f"❌ Erreur lors de la vérification des tâches: {e}")
        
        print("\n💡 Commandes disponibles:")
        print("  python3 monitor_celery.py monitor  - Surveiller les logs")
        print("  python3 monitor_celery.py status    - Vérifier le statut")
        print("  python3 monitor_celery.py redis    - Vérifier Redis")

if __name__ == "__main__":
    main()
