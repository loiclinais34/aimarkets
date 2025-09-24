#!/usr/bin/env python3
"""
Script de test pour le système de gestion de Celery
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.celery_manager import CeleryManager

def test_celery_manager():
    """Test du gestionnaire de Celery"""
    print("🔧 Test du gestionnaire de Celery...")
    
    celery_manager = CeleryManager()
    
    # Test 1: Statut de Celery
    print("\n1. Test statut de Celery...")
    status = celery_manager.get_celery_status()
    print(f"   Celery en cours: {status['celery_running']}")
    print(f"   Redis en cours: {status['redis_running']}")
    print(f"   Prêt: {status['ready']}")
    print(f"   Script existe: {status['script_exists']}")
    
    if status['celery_running']:
        print(f"   PIDs Celery: {status.get('celery_pids', [])}")
    
    # Test 2: Vérification Redis
    print("\n2. Test vérification Redis...")
    redis_running = celery_manager.is_redis_running()
    print(f"   Redis en cours: {redis_running}")
    
    # Test 3: Vérification Celery
    print("\n3. Test vérification Celery...")
    celery_running = celery_manager.is_celery_running()
    print(f"   Celery en cours: {celery_running}")
    
    # Test 4: Assurer que Celery est prêt
    print("\n4. Test ensure_celery_running...")
    result = celery_manager.ensure_celery_running()
    print(f"   Succès: {result['success']}")
    print(f"   Action: {result['action']}")
    if result['success']:
        print(f"   Message: {result['message']}")
    else:
        print(f"   Erreur: {result['error']}")
    
    return result['success']

def test_api_endpoints():
    """Test des endpoints API"""
    print("\n🌐 Test des endpoints API...")
    
    import requests
    
    base_url = "http://localhost:8000"
    
    # Test 1: Statut de Celery
    print("\n1. Test endpoint /api/v1/celery/status...")
    try:
        response = requests.get(f"{base_url}/api/v1/celery/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Statut récupéré: {data['data']['ready']}")
            print(f"   Celery: {data['data']['celery_running']}")
            print(f"   Redis: {data['data']['redis_running']}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
    
    # Test 2: Health check
    print("\n2. Test endpoint /api/v1/celery/health...")
    try:
        response = requests.get(f"{base_url}/api/v1/celery/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check: {data['status']}")
            print(f"   Message: {data['message']}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
    
    # Test 3: Ensure running
    print("\n3. Test endpoint /api/v1/celery/ensure-running...")
    try:
        response = requests.post(f"{base_url}/api/v1/celery/ensure-running", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Ensure running: {data['data']['success']}")
            print(f"   Action: {data['data']['action']}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            print(f"   Détail: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")

def main():
    """Fonction principale de test"""
    print("🚀 Test du système de gestion de Celery")
    print("=" * 50)
    
    # Test 1: Gestionnaire de Celery
    try:
        celery_ready = test_celery_manager()
        print(f"\n✅ Tests du gestionnaire de Celery terminés (Prêt: {celery_ready})")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests du gestionnaire: {e}")
    
    # Test 2: Endpoints API
    try:
        test_api_endpoints()
        print("\n✅ Tests des endpoints API terminés")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests API: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Recommandations:")
    print("   1. Vérifiez que Redis est démarré: brew services start redis")
    print("   2. Le système peut démarrer Celery automatiquement")
    print("   3. Utilisez les endpoints API pour vérifier l'état")
    print("   4. Les screeners vérifient maintenant Celery automatiquement")

if __name__ == "__main__":
    main()
