#!/usr/bin/env python3
"""
Script de diagnostic pour l'API Polygon.io
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from datetime import datetime, date, timedelta

def test_polygon_api_directly():
    """Test direct de l'API Polygon.io"""
    print("🔍 Test direct de l'API Polygon.io...")
    
    api_key = "HVxEJr0Up37u0LNBN24tqb23qGKHW6Qt"
    base_url = "https://api.polygon.io"
    
    # Test 1: Détails du ticker
    print("\n1. Test détails ticker AAPL...")
    endpoint = f"{base_url}/v3/reference/tickers/AAPL"
    params = {'apikey': api_key}
    
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Status API: {data.get('status')}")
            if data.get('status') == 'OK':
                print(f"   ✅ Succès: {data.get('results', {}).get('name', 'N/A')}")
            else:
                print(f"   ❌ Erreur API: {data.get('message', 'Unknown')}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 2: Données historiques
    print("\n2. Test données historiques AAPL...")
    end_date = date.today()
    start_date = end_date - timedelta(days=5)
    
    endpoint = f"{base_url}/v2/aggs/ticker/AAPL/range/1/day/{start_date}/{end_date}"
    params = {'apikey': api_key}
    
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        print(f"   Status Code: {response.status_code}")
        print(f"   URL: {endpoint}")
        print(f"   Response: {response.text[:300]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Status API: {data.get('status')}")
            if data.get('status') == 'OK':
                results = data.get('results', [])
                print(f"   ✅ Succès: {len(results)} jours de données")
                if results:
                    print(f"   📊 Premier jour: {results[0]}")
            else:
                print(f"   ❌ Erreur API: {data.get('message', 'Unknown')}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 3: Test avec un symbole problématique (AMGN)
    print("\n3. Test symbole problématique AMGN...")
    endpoint = f"{base_url}/v2/aggs/ticker/AMGN/range/1/day/{start_date}/{end_date}"
    params = {'apikey': api_key}
    
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:300]}...")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Status API: {data.get('status')}")
            if data.get('status') == 'OK':
                results = data.get('results', [])
                print(f"   ✅ Succès: {len(results)} jours de données")
            else:
                print(f"   ❌ Erreur API: {data.get('message', 'Unknown')}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
    
    # Test 4: Vérification des limites de l'API
    print("\n4. Test limites de l'API...")
    endpoint = f"{base_url}/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-01-02"
    params = {'apikey': api_key}
    
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Status API: {data.get('status')}")
            if data.get('status') == 'OK':
                print(f"   ✅ API fonctionnelle")
            else:
                print(f"   ❌ Erreur API: {data.get('message', 'Unknown')}")
        elif response.status_code == 429:
            print(f"   ⚠️ Rate limit atteint")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def test_api_key_validity():
    """Test de validité de la clé API"""
    print("\n🔑 Test de validité de la clé API...")
    
    api_key = "HVxEJr0Up37u0LNBN24tqb23qGKHW6Qt"
    base_url = "https://api.polygon.io"
    
    # Test simple pour vérifier la clé
    endpoint = f"{base_url}/v3/reference/tickers/AAPL"
    params = {'apikey': api_key}
    
    try:
        response = requests.get(endpoint, params=params, timeout=30)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'OK':
                print(f"   ✅ Clé API valide")
            else:
                print(f"   ❌ Clé API invalide: {data.get('message', 'Unknown')}")
        elif response.status_code == 401:
            print(f"   ❌ Clé API invalide (401 Unauthorized)")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")

def main():
    """Fonction principale de diagnostic"""
    print("🚀 Diagnostic de l'API Polygon.io")
    print("=" * 50)
    
    test_api_key_validity()
    test_polygon_api_directly()
    
    print("\n" + "=" * 50)
    print("🎯 Recommandations:")
    print("   1. Vérifiez que la clé API est correcte")
    print("   2. Vérifiez les limites de l'API (rate limiting)")
    print("   3. Vérifiez que les symboles existent sur Polygon.io")
    print("   4. Vérifiez les dates (pas de données futures)")
    print("   5. Vérifiez le plan d'abonnement Polygon.io")

if __name__ == "__main__":
    main()
