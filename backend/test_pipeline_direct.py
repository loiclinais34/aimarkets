#!/usr/bin/env python3
"""
Test simple de la pipeline d'analyse avancée
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_pipeline_direct():
    """Test direct de la pipeline sans Celery"""
    print("Testing Advanced Analysis Pipeline Directly...")
    
    try:
        from app.services.advanced_analysis.advanced_trading_analysis_simple import AdvancedTradingAnalysis
        import asyncio
        
        analyzer = AdvancedTradingAnalysis()
        
        # Test d'analyse pour AAPL
        print("Analyzing AAPL...")
        result = asyncio.run(analyzer.analyze_opportunity("AAPL", time_horizon=30, include_ml=True))
        
        print("✅ Analysis completed!")
        print(f"  - Symbol: {result.symbol}")
        print(f"  - Recommendation: {result.recommendation}")
        print(f"  - Composite Score: {result.composite_score:.2f}")
        print(f"  - Technical Score: {result.technical_score:.2f}")
        print(f"  - Sentiment Score: {result.sentiment_score:.2f}")
        print(f"  - Market Score: {result.market_score:.2f}")
        print(f"  - Confidence: {result.confidence_level:.2f}")
        print(f"  - Risk Level: {result.risk_level}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in direct pipeline test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_freshness():
    """Test du service de fraîcheur des données"""
    print("\nTesting Data Freshness Service...")
    
    try:
        from app.core.database import get_db
        from app.services.data_freshness_service import DataFreshnessService
        
        db = next(get_db())
        freshness_service = DataFreshnessService(db)
        
        summary = freshness_service.get_data_freshness_summary()
        print("✅ Data freshness check completed!")
        print(f"  - Historical data: {summary.get('historical_data', {}).get('total_symbols', 0)} symbols")
        print(f"  - Sentiment data: {summary.get('sentiment_data', {}).get('total_symbols', 0)} symbols")
        print(f"  - Technical indicators: {summary.get('technical_indicators', {}).get('total_symbols', 0)} symbols")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in data freshness test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("=== TEST DIRECT DE LA PIPELINE D'ANALYSE AVANCÉE ===\n")
    
    # Test 1: Service de fraîcheur des données
    test1_success = test_data_freshness()
    
    # Test 2: Analyse directe
    test2_success = test_pipeline_direct()
    
    print(f"\n=== RÉSULTATS ===")
    print(f"Data Freshness Service: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"Direct Analysis: {'✅ PASS' if test2_success else '❌ FAIL'}")
    
    if all([test1_success, test2_success]):
        print("\n🎉 La pipeline fonctionne correctement !")
        print("Le problème est probablement avec le worker Celery qui doit être redémarré.")
    else:
        print("\n⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")

