#!/usr/bin/env python3
"""
Test séquentiel des tâches de la pipeline d'analyse avancée
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tasks.advanced_analysis_pipeline_tasks import (
    calculate_technical_indicators_for_symbol,
    calculate_sentiment_indicators_for_symbol,
    calculate_market_indicators_for_symbol
)
import asyncio

async def test_individual_tasks():
    """Test séquentiel de chaque tâche individuelle"""
    
    symbols = ["AAPL", "MSFT", "GOOGL"]
    
    print("🚀 Démarrage du test séquentiel des tâches individuelles")
    print(f"📊 Symboles à tester: {symbols}")
    print("=" * 60)
    
    # Test 1: Indicateurs techniques
    print("\n🔧 TEST 1: Indicateurs Techniques")
    print("-" * 40)
    
    for symbol in symbols:
        try:
            print(f"📈 Test technique pour {symbol}...")
            result = calculate_technical_indicators_for_symbol(symbol, force_update=True)
            print(f"✅ {symbol}: {result}")
        except Exception as e:
            print(f"❌ {symbol}: Erreur - {e}")
    
    print("\n🔍 TEST 2: Indicateurs de Sentiment")
    print("-" * 40)
    
    for symbol in symbols:
        try:
            print(f"📊 Test sentiment pour {symbol}...")
            result = calculate_sentiment_indicators_for_symbol(symbol, force_update=True)
            print(f"✅ {symbol}: {result}")
        except Exception as e:
            print(f"❌ {symbol}: Erreur - {e}")
    
    print("\n📈 TEST 3: Indicateurs de Marché")
    print("-" * 40)
    
    for symbol in symbols:
        try:
            print(f"🏪 Test marché pour {symbol}...")
            result = calculate_market_indicators_for_symbol(symbol, force_update=True)
            print(f"✅ {symbol}: {result}")
        except Exception as e:
            print(f"❌ {symbol}: Erreur - {e}")
    
    print("\n🎯 Résumé des tests:")
    print("=" * 60)
    print("✅ Tests terminés - Vérifiez les résultats ci-dessus")

if __name__ == "__main__":
    asyncio.run(test_individual_tasks())

