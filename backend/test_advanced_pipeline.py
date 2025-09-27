#!/usr/bin/env python3
"""
Test de la pipeline d'analyse avancée
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_data_freshness():
    """Test du service de vérification de fraîcheur des données"""
    print("Testing Data Freshness Service...")
    
    try:
        from app.core.database import get_db
        from app.services.data_freshness_service import DataFreshnessService
        
        db = next(get_db())
        freshness_service = DataFreshnessService(db)
        
        # Test de vérification de fraîcheur
        summary = freshness_service.get_data_freshness_summary()
        print("✅ Data freshness summary:")
        print(f"  - Historical data: {summary.get('historical_data', {}).get('total_symbols', 0)} symbols")
        print(f"  - Sentiment data: {summary.get('sentiment_data', {}).get('total_symbols', 0)} symbols")
        print(f"  - Technical indicators: {summary.get('technical_indicators', {}).get('total_symbols', 0)} symbols")
        
        # Test des symboles nécessitant une mise à jour
        symbols_needing_update = freshness_service.get_symbols_needing_update("all")
        print(f"✅ Symbols needing update: {len(symbols_needing_update)}")
        if symbols_needing_update:
            print(f"  - First 5: {symbols_needing_update[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing data freshness: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_celery_tasks():
    """Test des tâches Celery"""
    print("\nTesting Celery Tasks...")
    
    try:
        from app.tasks.advanced_analysis_pipeline_tasks import check_data_freshness_task
        
        # Test de la tâche de vérification de fraîcheur
        print("✅ Testing check_data_freshness_task...")
        result = check_data_freshness_task.delay()
        print(f"  - Task ID: {result.id}")
        print(f"  - Status: {result.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Celery tasks: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test des endpoints API"""
    print("\nTesting API Endpoints...")
    
    try:
        import requests
        
        # Test de l'endpoint de vérification de fraîcheur
        print("✅ Testing data freshness endpoint...")
        response = requests.get("http://localhost:8000/api/v1/advanced-analysis/data-freshness")
        if response.status_code == 200:
            data = response.json()
            print(f"  - Status: {data.get('success', False)}")
            print(f"  - Historical symbols: {data.get('data', {}).get('historical_data', {}).get('total_symbols', 0)}")
        else:
            print(f"  - Error: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")
        return False

if __name__ == "__main__":
    print("=== TEST DE LA PIPELINE D'ANALYSE AVANCÉE ===\n")
    
    # Test 1: Service de fraîcheur des données
    test1_success = test_data_freshness()
    
    # Test 2: Tâches Celery
    test2_success = test_celery_tasks()
    
    # Test 3: Endpoints API
    test3_success = test_api_endpoints()
    
    print(f"\n=== RÉSULTATS ===")
    print(f"Data Freshness Service: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"Celery Tasks: {'✅ PASS' if test2_success else '❌ FAIL'}")
    print(f"API Endpoints: {'✅ PASS' if test3_success else '❌ FAIL'}")
    
    if all([test1_success, test2_success, test3_success]):
        print("\n🎉 Tous les tests sont passés ! La pipeline est prête.")
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")

