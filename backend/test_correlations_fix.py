#!/usr/bin/env python3
"""
Test spécifique pour les corrélations
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.indicators_recalculation_service import IndicatorsRecalculationService
from app.core.database import get_db

def test_correlations_only():
    """Test spécifique pour les corrélations"""
    print("🧪 Test spécifique des corrélations...")
    
    db = next(get_db())
    
    try:
        indicators_service = IndicatorsRecalculationService(db)
        
        # Tester avec quelques symboles
        test_symbols = ["AAPL", "MSFT"]
        print(f"🎯 Test des corrélations avec: {test_symbols}")
        
        # Recalculer uniquement les corrélations
        result = indicators_service.recalculate_correlations(test_symbols)
        
        print(f"\n📊 Résultat du recalcul des corrélations:")
        print(f"   Succès: {result['success']}")
        print(f"   Corrélations traitées: {result.get('processed_correlations', 0)}")
        print(f"   Symboles: {result.get('symbols_count', 0)}")
        
        if not result['success']:
            print(f"   Erreur: {result.get('error', 'Inconnue')}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 Test des corrélations corrigées")
    print("=" * 40)
    
    success = test_correlations_only()
    
    print("\n" + "=" * 40)
    
    if success:
        print("✅ Test des corrélations réussi!")
    else:
        print("❌ Test des corrélations échoué")
