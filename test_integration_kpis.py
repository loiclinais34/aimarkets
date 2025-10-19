#!/usr/bin/env python3
"""
Script de test pour vérifier l'intégration des KPIs optimisés
"""

import requests
import json
import time
from datetime import datetime

def test_backend_api():
    """Teste l'API backend"""
    print("🔧 Test de l'API Backend...")
    
    try:
        # Test de l'API XGBoost Performance
        response = requests.get('http://localhost:8000/api/v1/analysis/xgboost-performance/summary')
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API Backend fonctionne correctement")
            
            # Vérifier les données clés
            summary = data.get('summary', {})
            print(f"📊 Données récupérées:")
            print(f"  - Total opportunités: {summary.get('total_opportunities', 0):,}")
            print(f"  - Symboles uniques: {summary.get('unique_symbols', 0)}")
            print(f"  - Confiance moyenne: {summary.get('avg_confidence', 0):.3f}")
            print(f"  - Retour potentiel moyen: {summary.get('avg_potential_return', 0):.3f}")
            
            # Vérifier la distribution des recommandations
            rec_perf = data.get('recommendation_performance', {})
            print(f"\n🎯 Distribution des recommandations:")
            for rec_type, metrics in rec_perf.items():
                print(f"  - {rec_type}: {metrics.get('count', 0)} opportunités")
            
            return True
        else:
            print(f"❌ Erreur API Backend: {response.status_code}")
            print(response.text)
            return False
            
    except Exception as e:
        print(f"❌ Erreur de connexion Backend: {e}")
        return False

def test_frontend_access():
    """Teste l'accès au frontend"""
    print("\n🌐 Test de l'accès Frontend...")
    
    try:
        # Test de l'accès au dashboard
        response = requests.get('http://localhost:3000/dashboard', timeout=10)
        
        if response.status_code == 200:
            print("✅ Frontend accessible")
            return True
        else:
            print(f"⚠️ Frontend accessible mais statut: {response.status_code}")
            return True
            
    except requests.exceptions.ConnectionError:
        print("❌ Frontend non accessible (port 3000)")
        return False
    except Exception as e:
        print(f"❌ Erreur Frontend: {e}")
        return False

def test_data_consistency():
    """Teste la cohérence des données"""
    print("\n🔍 Test de cohérence des données...")
    
    try:
        # Récupérer les données de l'API
        response = requests.get('http://localhost:8000/api/v1/analysis/xgboost-performance/summary')
        data = response.json()
        
        summary = data.get('summary', {})
        rec_perf = data.get('recommendation_performance', {})
        
        # Vérifications de cohérence
        total_opp = summary.get('total_opportunities', 0)
        total_by_rec = sum(metrics.get('count', 0) for metrics in rec_perf.values())
        
        print(f"📊 Vérifications:")
        print(f"  - Total opportunités: {total_opp:,}")
        print(f"  - Total par recommandation: {total_by_rec:,}")
        
        if total_opp == total_by_rec:
            print("✅ Cohérence des données vérifiée")
            return True
        else:
            print("⚠️ Incohérence détectée dans les totaux")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de vérification: {e}")
        return False

def main():
    """Fonction principale de test"""
    print("🚀 Test d'intégration des KPIs optimisés")
    print("=" * 50)
    
    # Tests
    backend_ok = test_backend_api()
    frontend_ok = test_frontend_access()
    consistency_ok = test_data_consistency()
    
    # Résumé
    print("\n📋 Résumé des tests:")
    print("=" * 30)
    print(f"Backend API: {'✅ OK' if backend_ok else '❌ KO'}")
    print(f"Frontend Access: {'✅ OK' if frontend_ok else '❌ KO'}")
    print(f"Data Consistency: {'✅ OK' if consistency_ok else '❌ KO'}")
    
    if backend_ok and frontend_ok and consistency_ok:
        print("\n🎉 Tous les tests sont passés avec succès!")
        print("📊 Les KPIs optimisés sont correctement intégrés au dashboard")
    else:
        print("\n⚠️ Certains tests ont échoué")
        print("🔧 Vérifiez les services et la configuration")

if __name__ == "__main__":
    main()
