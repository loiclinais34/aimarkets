#!/usr/bin/env python3
"""
Script de test pour l'API FastAPI
"""

import requests
import json
from datetime import datetime, date
import time

# Configuration
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

def test_api_connection():
    """Tester la connexion à l'API"""
    print("🔗 Test de connexion à l'API...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("   ✅ API accessible")
            print(f"   📊 Status: {response.json()}")
            return True
        else:
            print(f"   ❌ Erreur de connexion: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
        return False

def test_target_parameters():
    """Tester les endpoints des paramètres de cible"""
    print("\n📊 Test des paramètres de cible...")
    
    # 1. Créer un paramètre de cible
    print("   1. Création d'un paramètre de cible...")
    target_data = {
        "user_id": "test_user_api",
        "parameter_name": "Test API 1.5% sur 7 jours",
        "target_return_percentage": 1.5,
        "time_horizon_days": 7,
        "risk_tolerance": "medium",
        "min_confidence_threshold": 0.7,
        "max_drawdown_percentage": 5.0
    }
    
    try:
        response = requests.post(f"{API_BASE}/target-parameters/", json=target_data)
        if response.status_code == 201:
            param = response.json()
            print(f"   ✅ Paramètre créé: ID {param['id']}")
            param_id = param['id']
        else:
            print(f"   ❌ Erreur création: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return None
    
    # 2. Récupérer les paramètres de l'utilisateur
    print("   2. Récupération des paramètres utilisateur...")
    try:
        response = requests.get(f"{API_BASE}/target-parameters/user/test_user_api")
        if response.status_code == 200:
            params = response.json()
            print(f"   ✅ {len(params)} paramètre(s) trouvé(s)")
        else:
            print(f"   ❌ Erreur récupération: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 3. Calculer un prix cible
    print("   3. Calcul de prix cible...")
    try:
        response = requests.post(
            f"{API_BASE}/target-parameters/calculate-target-price",
            params={
                "current_price": 100.0,
                "target_return_percentage": 1.5,
                "time_horizon_days": 7
            }
        )
        if response.status_code == 200:
            calc = response.json()
            print(f"   ✅ Prix cible calculé: ${calc['target_price']:.2f}")
            print(f"   📈 Rendement attendu: {calc['expected_return']:.2f}%")
        else:
            print(f"   ❌ Erreur calcul: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    return param_id

def test_ml_models(param_id):
    """Tester les endpoints des modèles ML"""
    print("\n🤖 Test des modèles ML...")
    
    if not param_id:
        print("   ⚠️ Pas de paramètre de cible disponible")
        return
    
    # 1. Entraîner un modèle de classification
    print("   1. Entraînement d'un modèle de classification...")
    training_data = {
        "symbol": "AAPL",
        "target_parameter_id": param_id,
        "model_type": "classification",
        "test_size": 0.2,
        "random_state": 42
    }
    
    try:
        response = requests.post(f"{API_BASE}/ml-models/train", json=training_data)
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Modèle entraîné: {result['model_name']}")
            print(f"   📊 Performance: {result['performance_metrics']}")
            model_id = result['model_id']
        else:
            print(f"   ❌ Erreur entraînement: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return None
    
    # 2. Lister les modèles
    print("   2. Liste des modèles...")
    try:
        response = requests.get(f"{API_BASE}/ml-models/")
        if response.status_code == 200:
            models = response.json()
            print(f"   ✅ {len(models)} modèle(s) trouvé(s)")
        else:
            print(f"   ❌ Erreur liste: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 3. Obtenir les performances du modèle
    print("   3. Performances du modèle...")
    try:
        response = requests.get(f"{API_BASE}/ml-models/{model_id}/performance")
        if response.status_code == 200:
            perf = response.json()
            print(f"   ✅ Performance récupérée: {perf['validation_score']:.3f}")
        else:
            print(f"   ❌ Erreur performance: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 4. Statistiques des modèles
    print("   4. Statistiques des modèles...")
    try:
        response = requests.get(f"{API_BASE}/ml-models/stats/overview")
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Statistiques: {stats['total_models']} modèles")
        else:
            print(f"   ❌ Erreur stats: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    return model_id

def test_data_endpoints():
    """Tester les endpoints de données"""
    print("\n📈 Test des endpoints de données...")
    
    # 1. Lister les symboles
    print("   1. Liste des symboles...")
    try:
        response = requests.get(f"{API_BASE}/data/symbols")
        if response.status_code == 200:
            symbols = response.json()
            print(f"   ✅ {len(symbols)} symbole(s) trouvé(s)")
            if symbols:
                test_symbol = symbols[0]
                print(f"   🔍 Test avec le symbole: {test_symbol}")
            else:
                print("   ⚠️ Aucun symbole disponible")
                return
        else:
            print(f"   ❌ Erreur symboles: {response.status_code}")
            return
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # 2. Informations sur le symbole
    print("   2. Informations du symbole...")
    try:
        response = requests.get(f"{API_BASE}/data/symbols/{test_symbol}/info")
        if response.status_code == 200:
            info = response.json()
            print(f"   ✅ Infos récupérées: {info['historical_records']} enregistrements")
        else:
            print(f"   ❌ Erreur info: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 3. Données historiques
    print("   3. Données historiques...")
    try:
        response = requests.get(f"{API_BASE}/data/historical/{test_symbol}?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {len(data)} enregistrement(s) historique(s)")
        else:
            print(f"   ❌ Erreur historique: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 4. Indicateurs techniques
    print("   4. Indicateurs techniques...")
    try:
        response = requests.get(f"{API_BASE}/data/technical/{test_symbol}?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {len(data)} indicateur(s) technique(s)")
        else:
            print(f"   ❌ Erreur technique: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 5. Indicateurs de sentiment
    print("   5. Indicateurs de sentiment...")
    try:
        response = requests.get(f"{API_BASE}/data/sentiment/{test_symbol}?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {len(data)} indicateur(s) de sentiment")
        else:
            print(f"   ❌ Erreur sentiment: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 6. Données combinées
    print("   6. Données combinées...")
    try:
        response = requests.get(f"{API_BASE}/data/combined/{test_symbol}?limit=3")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ {len(data)} enregistrement(s) combiné(s)")
        else:
            print(f"   ❌ Erreur combiné: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
    
    # 7. Statistiques globales
    print("   7. Statistiques globales...")
    try:
        response = requests.get(f"{API_BASE}/data/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Statistiques: {stats['total_symbols']} symboles, {stats['total_historical_records']} enregistrements")
        else:
            print(f"   ❌ Erreur stats: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")

def main():
    """Fonction principale de test"""
    print("🚀 Test de l'API FastAPI AIMarkets")
    print("=" * 50)
    
    # Test de connexion
    if not test_api_connection():
        print("\n❌ Impossible de se connecter à l'API. Assurez-vous qu'elle est démarrée.")
        return
    
    # Test des paramètres de cible
    param_id = test_target_parameters()
    
    # Test des modèles ML
    model_id = test_ml_models(param_id)
    
    # Test des données
    test_data_endpoints()
    
    print("\n" + "=" * 50)
    print("✅ Tests terminés!")
    print(f"📚 Documentation API: {BASE_URL}/docs")
    print(f"🔍 Redoc: {BASE_URL}/redoc")

if __name__ == "__main__":
    main()
