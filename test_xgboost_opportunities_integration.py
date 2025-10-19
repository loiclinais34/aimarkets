#!/usr/bin/env python3
"""
Script de test pour vérifier l'intégration de la page opportunités XGBoost
"""

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:8000/api/v1/analysis/xgboost-opportunities"
FRONTEND_DASHBOARD_URL = "http://localhost:3000/opportunities"

def test_xgboost_api():
    print("🔧 Test de l'API XGBoost Opportunities...")
    try:
        # Test de l'endpoint principal
        response = requests.get(f"{BACKEND_URL}?limit=10")
        response.raise_for_status()
        data = response.json()
        
        print("✅ API XGBoost fonctionne correctement")
        print("📊 Données récupérées:")
        print(f"  - Nombre d'opportunités: {data['count']}")
        print(f"  - Filtres appliqués: {data['filters']}")
        
        if data['opportunities']:
            first_opp = data['opportunities'][0]
            print(f"  - Première opportunité: {first_opp['symbol']} - {first_opp['recommendation']}")
            print(f"  - Confiance: {first_opp['confidence_level']:.3f}")
            print(f"  - Retour potentiel: {first_opp['potential_return']}")
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de l'appel API XGBoost: {e}")
        return None

def test_xgboost_summary():
    print("\n📈 Test de l'API Summary XGBoost...")
    try:
        response = requests.get(f"{BACKEND_URL}/summary")
        response.raise_for_status()
        data = response.json()
        
        print("✅ API Summary XGBoost fonctionne")
        print("📊 Résumé:")
        print(f"  - Total opportunités: {data['summary']['total_opportunities']:,}")
        print(f"  - Symboles uniques: {data['summary']['unique_symbols']}")
        print(f"  - Confiance moyenne: {data['summary']['avg_confidence']:.3f}")
        print(f"  - Retour moyen: {data['summary']['avg_return']:.3f}")
        
        print("\n🎯 Distribution des recommandations:")
        for rec in data['recommendations']:
            print(f"  - {rec['recommendation']}: {rec['count']:,} opportunités (confiance: {rec['avg_confidence']:.3f})")
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de l'appel API Summary: {e}")
        return None

def test_xgboost_top_performers():
    print("\n🏆 Test de l'API Top Performers...")
    try:
        response = requests.get(f"{BACKEND_URL}/top-performers?limit=5&min_confidence=0.8")
        response.raise_for_status()
        data = response.json()
        
        print("✅ API Top Performers fonctionne")
        print("🏆 Top Performers:")
        for i, performer in enumerate(data['top_performers'][:3], 1):
            print(f"  {i}. {performer['symbol']} - {performer['recommendation']} (confiance: {performer['confidence_level']:.3f})")
        
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de l'appel API Top Performers: {e}")
        return None

def test_xgboost_filters():
    print("\n🔍 Test des filtres XGBoost...")
    try:
        # Test avec différents filtres
        filters_tests = [
            {"symbol": "AAPL", "limit": 5},
            {"recommendation": "BUY_STRONG", "limit": 5},
            {"min_confidence": 0.8, "limit": 5},
            {"sort_by": "confidence_level", "sort_order": "desc", "limit": 5}
        ]
        
        for i, filters in enumerate(filters_tests, 1):
            params = "&".join([f"{k}={v}" for k, v in filters.items()])
            response = requests.get(f"{BACKEND_URL}?{params}")
            response.raise_for_status()
            data = response.json()
            
            print(f"  ✅ Test {i}: {len(data['opportunities'])} opportunités trouvées")
        
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors du test des filtres: {e}")
        return False

def test_frontend_access():
    print("\n🌐 Test de l'accès Frontend...")
    try:
        response = requests.get(FRONTEND_DASHBOARD_URL, timeout=5)
        if response.status_code == 200:
            print("✅ Frontend Dashboard: Accessible")
            return True
        else:
            print(f"⚠️ Frontend Dashboard: Status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de l'accès Frontend: {e}")
        return False

def test_data_consistency():
    print("\n🔍 Test de cohérence des données...")
    try:
        # Récupérer les données de base
        response = requests.get(f"{BACKEND_URL}?limit=100")
        response.raise_for_status()
        data = response.json()
        
        # Récupérer le résumé
        summary_response = requests.get(f"{BACKEND_URL}/summary")
        summary_response.raise_for_status()
        summary_data = summary_response.json()
        
        # Vérifier la cohérence
        total_from_list = len(data['opportunities'])
        total_from_summary = summary_data['summary']['total_opportunities']
        
        print(f"📊 Vérifications:")
        print(f"  - Opportunités dans la liste: {total_from_list}")
        print(f"  - Total dans le résumé: {total_from_summary}")
        
        if total_from_list <= total_from_summary:
            print("✅ Cohérence des données vérifiée")
            return True
        else:
            print("❌ Incohérence des données détectée!")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de cohérence: {e}")
        return False

def main():
    print("🚀 Test d'intégration de la page opportunités XGBoost")
    print("=" * 60)
    
    # Tests API
    api_data = test_xgboost_api()
    summary_data = test_xgboost_summary()
    top_performers_data = test_xgboost_top_performers()
    filters_ok = test_xgboost_filters()
    
    # Tests Frontend
    frontend_ok = test_frontend_access()
    
    # Tests de cohérence
    consistency_ok = test_data_consistency()
    
    print("\n📋 Résumé des tests:")
    print("=" * 30)
    print(f"API XGBoost Opportunities: {'✅ OK' if api_data else '❌ FAILED'}")
    print(f"API XGBoost Summary: {'✅ OK' if summary_data else '❌ FAILED'}")
    print(f"API XGBoost Top Performers: {'✅ OK' if top_performers_data else '❌ FAILED'}")
    print(f"Filtres XGBoost: {'✅ OK' if filters_ok else '❌ FAILED'}")
    print(f"Frontend Dashboard: {'✅ OK' if frontend_ok else '❌ FAILED'}")
    print(f"Cohérence des données: {'✅ OK' if consistency_ok else '❌ FAILED'}")
    
    all_tests_passed = all([
        api_data, summary_data, top_performers_data, 
        filters_ok, frontend_ok, consistency_ok
    ])
    
    if all_tests_passed:
        print("\n🎉 Tous les tests sont passés avec succès!")
        print("📊 La page opportunités XGBoost est correctement intégrée")
        print("\n✨ Nouvelles fonctionnalités disponibles:")
        print("  - Opportunités basées sur XGBoost ML")
        print("  - Indicateurs techniques avancés TA-Lib")
        print("  - Filtrage par confiance ML")
        print("  - Analyse des indicateurs composites")
        print("  - Onglet 'Indicateurs Avancés'")
    else:
        print("\n❌ Des tests ont échoué. Veuillez vérifier les logs ci-dessus.")
        print("🔧 Vérifiez que:")
        print("  - Le backend est démarré sur le port 8000")
        print("  - Le frontend est démarré sur le port 3000")
        print("  - Les données XGBoost sont disponibles dans la base")

if __name__ == "__main__":
    main()
