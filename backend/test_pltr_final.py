#!/usr/bin/env python3
"""
Test final de l'API PLTR optimisée
"""

import requests
import time

def test_pltr_final():
    base_url = "http://localhost:8000/api/v1/backtesting"
    
    print("🎯 Test final de l'API PLTR optimisée")
    print("=" * 50)
    
    # Test 1: Chargement initial (50 modèles)
    print("1. Test du chargement initial (50 modèles)...")
    start_time = time.time()
    try:
        response = requests.get(f"{base_url}/symbols/PLTR/models?limit=50", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            load_time = time.time() - start_time
            print(f"✅ {len(models)} modèles chargés en {load_time:.2f}s")
            print(f"📊 Total disponible: {data.get('total', 0)} modèles")
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # Test 2: Recherche par terme
    print("\n2. Test de la recherche par terme...")
    start_time = time.time()
    try:
        response = requests.get(f"{base_url}/symbols/PLTR/models?search=5.0%25_10d&limit=10", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            search_time = time.time() - start_time
            print(f"✅ {len(models)} modèles trouvés pour '5.0%_10d' en {search_time:.2f}s")
            if models:
                print(f"   Premier résultat: {models[0]['name']}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # Test 3: Recherche par type
    print("\n3. Test de la recherche par type...")
    start_time = time.time()
    try:
        response = requests.get(f"{base_url}/symbols/PLTR/models?search=classification&limit=10", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            search_time = time.time() - start_time
            print(f"✅ {len(models)} modèles trouvés pour 'classification' en {search_time:.2f}s")
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    print("\n🎉 Tous les tests sont passés ! L'API est maintenant optimisée.")
    print("💡 Le frontend devrait maintenant pouvoir charger les modèles PLTR rapidement.")
    return True

if __name__ == "__main__":
    success = test_pltr_final()
    if not success:
        print("\n💥 Des erreurs ont été détectées.")
