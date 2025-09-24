#!/usr/bin/env python3
"""
Script pour forcer le recalcul de tous les indicateurs
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.indicators_recalculation_service import IndicatorsRecalculationService
from app.core.database import get_db
from app.models.database import SymbolMetadata
from datetime import date

def force_recalculate_all_indicators():
    """Force le recalcul de tous les indicateurs pour tous les symboles actifs"""
    print("🔄 Début du recalcul forcé de tous les indicateurs...")
    
    # Obtenir une session de base de données
    db = next(get_db())
    
    try:
        # Récupérer tous les symboles actifs
        active_symbols = db.query(SymbolMetadata.symbol).filter(
            SymbolMetadata.is_active == True
        ).all()
        
        symbols = [symbol[0] for symbol in active_symbols]
        print(f"📊 {len(symbols)} symboles actifs trouvés")
        
        if not symbols:
            print("❌ Aucun symbole actif trouvé")
            return
        
        # Initialiser le service de recalcul
        indicators_service = IndicatorsRecalculationService(db)
        
        # Afficher les premiers symboles pour confirmation
        print(f"🎯 Symboles à traiter: {symbols[:10]}{'...' if len(symbols) > 10 else ''}")
        
        # Lancer le recalcul complet
        print("\n🚀 Lancement du recalcul complet...")
        result = indicators_service.recalculate_all_indicators(symbols)
        
        # Afficher les résultats
        print("\n📈 Résultats du recalcul:")
        print(f"   ✅ Symboles traités: {result['symbols_processed']}")
        print(f"   📊 Indicateurs techniques: {result['technical_indicators']['success']} succès, {result['technical_indicators']['failed']} échecs")
        print(f"   💭 Indicateurs de sentiment: {result['sentiment_indicators']['success']} succès, {result['sentiment_indicators']['failed']} échecs")
        print(f"   🔗 Corrélations: {result['correlations']['success']} succès, {result['correlations']['failed']} échecs")
        
        if result['errors']:
            print(f"\n⚠️ Erreurs rencontrées ({len(result['errors'])}):")
            for i, error in enumerate(result['errors'][:5]):  # Afficher les 5 premières erreurs
                print(f"   {i+1}. {error}")
            if len(result['errors']) > 5:
                print(f"   ... et {len(result['errors']) - 5} autres erreurs")
        
        # Déterminer le statut global
        total_failed = (
            result['technical_indicators']['failed'] +
            result['sentiment_indicators']['failed'] +
            result['correlations']['failed']
        )
        
        if result['success']:
            print(f"\n🎉 Recalcul terminé avec succès!")
        else:
            print(f"\n⚠️ Recalcul terminé avec {total_failed} échecs")
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur lors du recalcul: {e}")
        return None
    finally:
        db.close()

def force_recalculate_specific_symbols(symbols_list):
    """Force le recalcul pour des symboles spécifiques"""
    print(f"🔄 Recalcul forcé pour {len(symbols_list)} symboles spécifiques...")
    
    db = next(get_db())
    
    try:
        indicators_service = IndicatorsRecalculationService(db)
        
        print(f"🎯 Symboles: {symbols_list}")
        
        result = indicators_service.recalculate_all_indicators(symbols_list)
        
        print("\n📈 Résultats:")
        print(f"   ✅ Symboles traités: {result['symbols_processed']}")
        print(f"   📊 Indicateurs techniques: {result['technical_indicators']['success']} succès, {result['technical_indicators']['failed']} échecs")
        print(f"   💭 Indicateurs de sentiment: {result['sentiment_indicators']['success']} succès, {result['sentiment_indicators']['failed']} échecs")
        print(f"   🔗 Corrélations: {result['correlations']['success']} succès, {result['correlations']['failed']} échecs")
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None
    finally:
        db.close()

def main():
    """Fonction principale"""
    print("🚀 Script de recalcul forcé des indicateurs")
    print("=" * 60)
    
    # Vérifier les arguments
    if len(sys.argv) > 1:
        # Symboles spécifiques fournis en argument
        symbols = sys.argv[1].split(',')
        symbols = [s.strip().upper() for s in symbols if s.strip()]
        print(f"📋 Symboles spécifiques: {symbols}")
        result = force_recalculate_specific_symbols(symbols)
    else:
        # Tous les symboles actifs
        print("📋 Tous les symboles actifs")
        result = force_recalculate_all_indicators()
    
    print("\n" + "=" * 60)
    
    if result and result['success']:
        print("✅ Script terminé avec succès!")
    else:
        print("⚠️ Script terminé avec des erreurs")
    
    print("\n💡 Utilisation:")
    print("   python3 force_recalculate_indicators.py                    # Tous les symboles")
    print("   python3 force_recalculate_indicators.py AAPL,MSFT,GOOGL  # Symboles spécifiques")

if __name__ == "__main__":
    main()
