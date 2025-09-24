#!/usr/bin/env python3
"""
Test complet de l'intégration Frontend-Backend pour les screeners
"""
import requests
import json
import time

def test_screener_integration():
    """Test complet de l'intégration des screeners"""
    print("🔧 Test d'intégration Frontend-Backend pour les screeners...")
    
    # Configuration
    backend_url = "http://localhost:8000"
    frontend_url = "http://localhost:3000"
    
    # Test 1: Vérifier que le backend est accessible
    print("\n1️⃣ Test de l'accessibilité du backend...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend accessible")
        else:
            print(f"❌ Backend répond avec le code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend inaccessible: {e}")
        return False
    
    # Test 2: Vérifier que le frontend est accessible
    print("\n2️⃣ Test de l'accessibilité du frontend...")
    try:
        response = requests.get(f"{frontend_url}", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend accessible")
        else:
            print(f"❌ Frontend répond avec le code {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend inaccessible: {e}")
        return False
    
    # Test 3: Vérifier les endpoints des screeners
    print("\n3️⃣ Test des endpoints des screeners...")
    
    screener_endpoints = [
        ("/api/v1/screener/run-demo", "Demo Screener"),
        ("/api/v1/screener/run-real", "Real Screener"),
        ("/api/v1/screener/run-full-ml-web", "Full ML Screener")
    ]
    
    for endpoint, name in screener_endpoints:
        try:
            response = requests.post(
                f"{backend_url}{endpoint}",
                json={
                    "target_return_percentage": 2.0,
                    "time_horizon_days": 7,
                    "risk_tolerance": 0.7
                },
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                if "task_id" in data:
                    print(f"✅ {name}: Task ID {data['task_id']}")
                else:
                    print(f"❌ {name}: Pas de task_id dans la réponse")
            else:
                print(f"❌ {name}: Code {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: Erreur {e}")
    
    # Test 4: Vérifier les données nécessaires
    print("\n4️⃣ Test des données nécessaires...")
    
    # Vérifier les symboles
    try:
        response = requests.get(f"{backend_url}/api/v1/data/symbols", timeout=5)
        if response.status_code == 200:
            symbols = response.json()
            print(f"✅ Symboles disponibles: {len(symbols)}")
        else:
            print(f"❌ Impossible de récupérer les symboles: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération des symboles: {e}")
    
    # Test 5: Test complet d'un screener
    print("\n5️⃣ Test complet d'un screener...")
    
    try:
        # Lancer un screener demo
        response = requests.post(
            f"{backend_url}/api/v1/screener/run-demo",
            json={
                "target_return_percentage": 2.0,
                "time_horizon_days": 7,
                "risk_tolerance": 0.7
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get("task_id")
            print(f"✅ Screener lancé avec succès: {task_id}")
            
            # Attendre un peu et vérifier le statut
            print("⏳ Attente de 5 secondes...")
            time.sleep(5)
            
            # Vérifier le statut
            status_response = requests.get(
                f"{backend_url}/api/v1/screener/task/{task_id}/status",
                timeout=5
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"✅ Statut récupéré: {status_data.get('state', 'Unknown')}")
                print(f"📊 Progression: {status_data.get('progress', 0)}%")
            else:
                print(f"❌ Impossible de récupérer le statut: {status_response.status_code}")
        else:
            print(f"❌ Échec du lancement du screener: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur lors du test complet: {e}")
    
    print("\n🎉 Test d'intégration terminé !")
    return True

if __name__ == "__main__":
    test_screener_integration()
