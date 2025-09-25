#!/usr/bin/env python3
"""
Test du système d'entraînement asynchrone avec Celery
"""

import requests
import json
import time
import sys

def test_async_model_comparison():
    """Test de la comparaison asynchrone de modèles"""
    print("🧪 Test de la comparaison asynchrone de modèles")
    print("=" * 60)
    
    base_url = "http://localhost:8000/api/v1/model-comparison"
    
    # 1. Lancer une comparaison asynchrone
    print("🚀 Lancement d'une comparaison asynchrone...")
    
    payload = {
        "symbol": "AAPL",
        "models_to_test": ["RandomForest", "XGBoost", "PyTorchLSTM"],
        "parameters": {
            "PyTorchLSTM": {
                "sequence_length": 3,
                "hidden_sizes": [8],
                "epochs": 2,
                "batch_size": 2
            }
        }
    }
    
    try:
        response = requests.post(f"{base_url}/compare-async", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Comparaison asynchrone lancée!")
            print(f"Task ID: {data['task_id']}")
            print(f"Symbol: {data['symbol']}")
            print(f"Modèles: {data['models_to_test']}")
            
            task_id = data['task_id']
            
            # 2. Surveiller le progrès
            print("\n📊 Surveillance du progrès...")
            
            while True:
                time.sleep(2)  # Attendre 2 secondes
                
                status_response = requests.get(f"{base_url}/task-status/{task_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data['status']
                    
                    if status == 'PROGRESS':
                        progress = status_data.get('progress', 0)
                        message = status_data.get('message', 'En cours...')
                        model_name = status_data.get('model_name', 'Unknown')
                        
                        print(f"🔄 {model_name}: {progress}% - {message}")
                        
                        # Afficher les détails pour PyTorchLSTM
                        if model_name == 'PyTorchLSTM' and 'details' in status_data:
                            details = status_data['details']
                            if 'epoch' in details:
                                print(f"   📈 Epoch {details['epoch']}/{details.get('total_epochs', '?')} - Loss: {details.get('loss', 0):.4f}")
                    
                    elif status == 'SUCCESS':
                        print("🎉 Comparaison terminée avec succès!")
                        results = status_data.get('result', {})
                        
                        if isinstance(results, dict) and 'results' in results:
                            print("\n📊 Résultats:")
                            for model_name, metrics in results['results'].items():
                                print(f"  {model_name}:")
                                print(f"    Accuracy: {metrics.get('accuracy', 'N/A'):.3f}")
                                print(f"    Training time: {metrics.get('training_time', 'N/A'):.2f}s")
                                print(f"    F1-Score: {metrics.get('f1_score', 'N/A'):.3f}")
                        
                        break
                    
                    elif status == 'FAILURE':
                        print("❌ Comparaison échouée!")
                        error = status_data.get('error', 'Erreur inconnue')
                        print(f"Erreur: {error}")
                        break
                    
                    elif status == 'PENDING':
                        print("⏳ Tâche en attente...")
                    
                    else:
                        print(f"❓ Statut inconnu: {status}")
                
                else:
                    print(f"❌ Erreur lors de la récupération du statut: {status_response.status_code}")
                    break
            
        else:
            print(f"❌ Erreur lors du lancement: {response.status_code}")
            print(f"Contenu: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Erreur de connexion - Le backend n'est pas accessible")
        print("Assurez-vous que le backend est démarré sur http://localhost:8000")
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_task_status():
    """Test de récupération du statut d'une tâche"""
    print("\n🔍 Test de récupération du statut d'une tâche")
    print("-" * 40)
    
    base_url = "http://localhost:8000/api/v1/model-comparison"
    
    try:
        # Tester avec un ID de tâche fictif
        fake_task_id = "fake-task-id-123"
        
        response = requests.get(f"{base_url}/task-status/{fake_task_id}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Statut récupéré pour {fake_task_id}")
            print(f"Statut: {data['status']}")
            print(f"Message: {data['message']}")
        else:
            print(f"❌ Erreur: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_active_tasks():
    """Test de récupération des tâches actives"""
    print("\n📋 Test de récupération des tâches actives")
    print("-" * 40)
    
    base_url = "http://localhost:8000/api/v1/model-comparison"
    
    try:
        response = requests.get(f"{base_url}/active-tasks")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Tâches actives récupérées")
            print(f"Total: {data.get('total', 0)}")
            
            active_tasks = data.get('active_tasks', [])
            if active_tasks:
                print("Tâches actives:")
                for task in active_tasks:
                    print(f"  - {task['task_id']}: {task['name']}")
            else:
                print("Aucune tâche active")
        else:
            print(f"❌ Erreur: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    print("🧪 Test du système d'entraînement asynchrone avec Celery")
    print("=" * 60)
    
    # Vérifier que le backend est accessible
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Backend accessible")
        else:
            print("❌ Backend non accessible")
            sys.exit(1)
    except:
        print("❌ Backend non accessible")
        print("Assurez-vous que le backend est démarré sur http://localhost:8000")
        sys.exit(1)
    
    # Tests
    test_async_model_comparison()
    test_task_status()
    test_active_tasks()
    
    print("\n🎉 Tests terminés!")
