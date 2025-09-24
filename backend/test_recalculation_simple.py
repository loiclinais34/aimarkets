#!/usr/bin/env python3
"""
Script de test simple pour le recalcul des indicateurs
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.indicators_recalculation_service import IndicatorsRecalculationService
from app.core.database import get_db

def test_single_symbol():
    """Test le recalcul pour un seul symbole"""
    print("🧪 Test du recalcul pour un symbole spécifique...")
    
    # Obtenir une session de base de données
    db = next(get_db())
    
    try:
        indicators_service = IndicatorsRecalculationService(db)
        
        # Tester avec AAPL
        test_symbol = "AAPL"
        print(f"🎯 Test avec le symbole: {test_symbol}")
        
        # Recalculer les indicateurs techniques
        result = indicators_service.recalculate_technical_indicators(test_symbol)
        
        print(f"\n📊 Résultat du recalcul:")
        print(f"   Succès: {result['success']}")
        print(f"   Symbol: {result.get('symbol', 'N/A')}")
        print(f"   Dates traitées: {result.get('processed_dates', 0)}")
        print(f"   Total dates: {result.get('total_dates', 0)}")
        
        if not result['success']:
            print(f"   Erreur: {result.get('error', 'Inconnue')}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False
    finally:
        db.close()

def test_multiple_symbols():
    """Test le recalcul pour plusieurs symboles"""
    print("\n🧪 Test du recalcul pour plusieurs symboles...")
    
    db = next(get_db())
    
    try:
        indicators_service = IndicatorsRecalculationService(db)
        
        # Tester avec quelques symboles
        test_symbols = ["AAPL", "MSFT", "GOOGL"]
        print(f"🎯 Test avec les symboles: {test_symbols}")
        
        # Recalculer tous les indicateurs
        result = indicators_service.recalculate_all_indicators(test_symbols)
        
        print(f"\n📊 Résultat du recalcul complet:")
        print(f"   Succès global: {result['success']}")
        print(f"   Symboles traités: {result['symbols_processed']}")
        print(f"   Indicateurs techniques: {result['technical_indicators']['success']} succès, {result['technical_indicators']['failed']} échecs")
        print(f"   Indicateurs de sentiment: {result['sentiment_indicators']['success']} succès, {result['sentiment_indicators']['failed']} échecs")
        print(f"   Corrélations: {result['correlations']['success']} succès, {result['correlations']['failed']} échecs")
        
        if result['errors']:
            print(f"\n⚠️ Erreurs ({len(result['errors'])}):")
            for i, error in enumerate(result['errors'][:3]):
                print(f"   {i+1}. {error}")
        
        return result['success']
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False
    finally:
        db.close()

def main():
    """Fonction principale"""
    print("🧪 Test du service de recalcul des indicateurs")
    print("=" * 50)
    
    # Test 1: Un seul symbole
    success1 = test_single_symbol()
    
    # Test 2: Plusieurs symboles
    success2 = test_multiple_symbols()
    
    print("\n" + "=" * 50)
    
    if success1 and success2:
        print("✅ Tous les tests sont passés avec succès!")
        print("\n💡 Vous pouvez maintenant lancer le recalcul complet:")
        print("   python3 force_recalculate_indicators.py")
    else:
        print("⚠️ Certains tests ont échoué")
        if not success1:
            print("   - Test du symbole unique: ÉCHEC")
        if not success2:
            print("   - Test des symboles multiples: ÉCHEC")

if __name__ == "__main__":
    main()
