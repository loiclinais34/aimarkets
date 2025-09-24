#!/usr/bin/env python3
"""
Test final des corrélations avec la nouvelle logique
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.indicators_recalculation_service import IndicatorsRecalculationService
from app.core.database import get_db

def test_correlations_final():
    """Test final des corrélations avec la nouvelle logique"""
    print("🧪 Test final des corrélations...")
    
    db = next(get_db())
    
    try:
        # Créer une nouvelle instance du service
        indicators_service = IndicatorsRecalculationService(db)
        
        # Tester avec 3 symboles pour voir les paires
        test_symbols = ["AAPL", "MSFT", "GOOGL"]
        print(f"🎯 Test des corrélations avec: {test_symbols}")
        print(f"   Paires attendues: AAPL-MSWT, AAPL-GOOGL, MSFT-GOOGL")
        
        # Recalculer uniquement les corrélations
        result = indicators_service.recalculate_correlations(test_symbols)
        
        print(f"\n📊 Résultat du recalcul des corrélations:")
        print(f"   Succès: {result['success']}")
        print(f"   Corrélations traitées: {result.get('processed_correlations', 0)}")
        print(f"   Symboles: {result.get('symbols_count', 0)}")
        
        if not result['success']:
            print(f"   Erreur: {result.get('error', 'Inconnue')}")
        
        # Vérifier les corrélations créées
        from app.models.database import CorrelationMatrices
        from datetime import datetime
        
        correlations = db.query(CorrelationMatrices).filter(
            CorrelationMatrices.date == datetime.now().date(),
            CorrelationMatrices.correlation_type == 'price'
        ).all()
        
        print(f"\n📋 Corrélations créées aujourd'hui: {len(correlations)}")
        for corr in correlations:
            print(f"   - {corr.symbol}: {corr.correlation_value:.4f}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 Test final des corrélations corrigées")
    print("=" * 50)
    
    success = test_correlations_final()
    
    print("\n" + "=" * 50)
    
    if success:
        print("✅ Test final des corrélations réussi!")
        print("\n💡 Vous pouvez maintenant lancer le recalcul complet:")
        print("   python3 force_recalculate_indicators.py")
    else:
        print("❌ Test final des corrélations échoué")
