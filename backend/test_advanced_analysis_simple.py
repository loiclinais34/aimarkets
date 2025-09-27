#!/usr/bin/env python3
"""
Test simple du service d'analyse avancée
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.advanced_analysis.advanced_trading_analysis import AdvancedTradingAnalysis
import asyncio

async def test_analysis():
    """Test simple de l'analyse"""
    try:
        analyzer = AdvancedTradingAnalysis()
        print("✅ Service initialisé avec succès")
        
        # Test d'analyse
        result = await analyzer.analyze_opportunity("AAPL", time_horizon=30, include_ml=True)
        print(f"✅ Analyse réussie pour AAPL:")
        print(f"   - Score composite: {result.composite_score:.2f}")
        print(f"   - Recommandation: {result.recommendation}")
        print(f"   - Niveau de risque: {result.risk_level}")
        print(f"   - Confiance: {result.confidence_level:.2f}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_analysis())

