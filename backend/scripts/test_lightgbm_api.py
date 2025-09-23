#!/usr/bin/env python3
"""
Test des endpoints API LightGBM
"""
import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000"

def test_lightgbm_api():
    """Test des endpoints API LightGBM"""
    print("🧪 Test des endpoints API LightGBM...")
    
    try:
        # Test de l'endpoint de statistiques
        print("\n📊 Test de l'endpoint de statistiques...")
        response = requests.get(f"{BASE_URL}/api/v1/lightgbm/stats/overview")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Statistiques récupérées: {stats}")
        else:
            print(f"❌ Erreur statistiques: {response.status_code} - {response.text}")
        
        # Test de l'endpoint de liste des modèles
        print("\n📋 Test de l'endpoint de liste des modèles...")
        response = requests.get(f"{BASE_URL}/api/v1/lightgbm/models")
        if response.status_code == 200:
            models = response.json()
            print(f"✅ Modèles récupérés: {len(models)} modèles")
            for model in models[:3]:  # Afficher les 3 premiers
                print(f"   - {model['name']} ({model['model_type']})")
        else:
            print(f"❌ Erreur liste modèles: {response.status_code} - {response.text}")
        
        # Test de l'endpoint de classification binaire
        print("\n🔍 Test de l'endpoint de classification binaire...")
        training_request = {
            "symbol": "AAPL",
            "target_parameter_id": 1  # Supposons qu'il y a un paramètre cible avec ID 1
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/lightgbm/train/binary",
            json=training_request
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Modèle de classification binaire entraîné: {result['model_name']}")
            print(f"   - Performance: {result['performance']}")
            model_id = result['model_id']
            
            # Test de prédiction
            print("\n🔮 Test de prédiction...")
            prediction_request = {
                "model_id": model_id,
                "symbol": "AAPL",
                "prediction_date": date.today().isoformat()
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/lightgbm/predict",
                json=prediction_request
            )
            
            if response.status_code == 200:
                prediction = response.json()
                print(f"✅ Prédiction effectuée:")
                print(f"   - Classe: {prediction['prediction_class']}")
                print(f"   - Valeur: {prediction['prediction_value']:.3f}")
                print(f"   - Confiance: {prediction['confidence']:.3f}")
            else:
                print(f"❌ Erreur prédiction: {response.status_code} - {response.text}")
                
        else:
            print(f"❌ Erreur entraînement: {response.status_code} - {response.text}")
        
        print("\n🎉 Tests des endpoints API LightGBM terminés!")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lightgbm_api()
