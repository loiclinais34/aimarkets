#!/usr/bin/env python3
"""
Script de test pour le système de mise à jour des données
"""
import sys
import time
import requests
from pathlib import Path

# Ajouter le répertoire backend au PYTHONPATH
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_data_update_system():
    """Tester le système de mise à jour des données"""
    
    base_url = "http://localhost:8000/api/v1/data-update"
    
    print("🧪 Test du système de mise à jour des données")
    print("=" * 50)
    
    # Test 1: Vérifier le statut des données
    print("\n1. Vérification du statut des données...")
    try:
        response = requests.get(f"{base_url}/status")
        if response.status_code == 200:
            data = response.json()
            print("✅ Statut récupéré avec succès")
            print(f"   Statut global: {data['data']['overall_status']}")
            print(f"   Données historiques: {data['data']['historical_freshness']['message']}")
            print(f"   Données de sentiment: {data['data']['sentiment_freshness']['message']}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Erreur lors de la vérification du statut: {e}")
    
    # Test 2: Vérifier la fraîcheur des données
    print("\n2. Vérification de la fraîcheur des données...")
    try:
        response = requests.get(f"{base_url}/freshness")
        if response.status_code == 200:
            data = response.json()
            print("✅ Fraîcheur vérifiée avec succès")
            print(f"   Mise à jour nécessaire: {data['data']['overall_needs_update']}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la fraîcheur: {e}")
    
    # Test 3: Récupérer les statistiques
    print("\n3. Récupération des statistiques...")
    try:
        response = requests.get(f"{base_url}/stats")
        if response.status_code == 200:
            data = response.json()
            print("✅ Statistiques récupérées avec succès")
            historical = data['data']['historical_data']
            sentiment = data['data']['sentiment_data']
            print(f"   Données historiques: {historical['total_records']} enregistrements, {historical['unique_symbols']} symboles")
            print(f"   Données de sentiment: {sentiment['total_records']} enregistrements, {sentiment['unique_symbols']} symboles")
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des statistiques: {e}")
    
    # Test 4: Déclencher une mise à jour (simulation)
    print("\n4. Test de déclenchement de mise à jour...")
    try:
        response = requests.post(f"{base_url}/trigger-update", json={"force_update": False})
        if response.status_code == 200:
            data = response.json()
            print("✅ Mise à jour déclenchée avec succès")
            print(f"   Task ID: {data['task_id']}")
            
            # Suivre le statut de la tâche
            task_id = data['task_id']
            print(f"\n5. Suivi de la tâche {task_id}...")
            
            for i in range(10):  # Suivre pendant 20 secondes maximum
                time.sleep(2)
                try:
                    status_response = requests.get(f"{base_url}/task-status/{task_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        task_info = status_data['data']
                        print(f"   État: {task_info['state']} - {task_info['status']}")
                        
                        if task_info.get('progress'):
                            print(f"   Progrès: {task_info['progress']}%")
                        
                        if task_info.get('current_symbol'):
                            print(f"   Symbole actuel: {task_info['current_symbol']}")
                        
                        if task_info['state'] in ['SUCCESS', 'FAILURE']:
                            print(f"   Résultat final: {task_info}")
                            break
                    else:
                        print(f"❌ Erreur lors du suivi: {status_response.status_code}")
                        break
                except Exception as e:
                    print(f"❌ Erreur lors du suivi: {e}")
                    break
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Erreur lors du déclenchement de la mise à jour: {e}")
    
    # Test 6: Vérifier les tâches actives
    print("\n6. Vérification des tâches actives...")
    try:
        response = requests.get(f"{base_url}/active-tasks")
        if response.status_code == 200:
            data = response.json()
            print("✅ Tâches actives récupérées avec succès")
            print(f"   Nombre de tâches actives: {data['data']['total_active']}")
            for task in data['data']['active_tasks']:
                print(f"   - {task['name']} (ID: {task['task_id'][:8]}...)")
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des tâches actives: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Test terminé")

if __name__ == "__main__":
    test_data_update_system()