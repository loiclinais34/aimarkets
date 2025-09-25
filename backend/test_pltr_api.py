#!/usr/bin/env python3
"""
Script de test pour vérifier l'API PLTR
"""

import requests
import json

def test_pltr_api():
    base_url = "http://localhost:8000/api/v1/backtesting"
    
    print("🔍 Test de l'API PLTR pour le backtesting")
    print("=" * 50)
    
    # 1. Tester la liste des symboles
    print("1. Test de la liste des symboles...")
    try:
        response = requests.get(f"{base_url}/symbols")
        if response.status_code == 200:
            data = response.json()
            pltr_symbol = None
            for symbol in data.get('symbols', []):
                if symbol['symbol'] == 'PLTR':
                    pltr_symbol = symbol
                    break
            
            if pltr_symbol:
                print(f"✅ PLTR trouvé: {pltr_symbol['prediction_count']} prédictions, {pltr_symbol['model_count']} modèles")
            else:
                print("❌ PLTR non trouvé dans la liste des symboles")
                return False
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # 2. Tester la récupération des modèles PLTR
    print("\n2. Test de la récupération des modèles PLTR...")
    try:
        response = requests.get(f"{base_url}/symbols/PLTR/models")
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"✅ {len(models)} modèles récupérés pour PLTR")
            
            # Afficher les 5 premiers modèles
            print("\n📋 Premiers modèles:")
            for i, model in enumerate(models[:5]):
                print(f"  {i+1}. ID: {model['id']}, Nom: {model['name']}, Prédictions: {model['prediction_count']}")
            
            return True
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = test_pltr_api()
    if success:
        print("\n🎉 Tous les tests sont passés ! L'API fonctionne correctement.")
    else:
        print("\n💥 Des erreurs ont été détectées.")
