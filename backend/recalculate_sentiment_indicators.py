#!/usr/bin/env python3
"""
Script de recalcul manuel des indicateurs de sentiment
Usage: python3 recalculate_sentiment_indicators.py [symbols]
Exemples:
  python3 recalculate_sentiment_indicators.py                    # Tous les symboles
  python3 recalculate_sentiment_indicators.py AAPL,MSFT,GOOGL    # Symboles spécifiques
"""
import sys
import os
from datetime import datetime, date
import logging

# Ajouter le répertoire parent au PYTHONPATH pour les imports relatifs
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.services.indicators_recalculation_service import IndicatorsRecalculationService
from app.models.database import SymbolMetadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recalculate_sentiment_indicators(symbols: list = None):
    """
    Recalcule les indicateurs de sentiment pour les symboles spécifiés
    
    Args:
        symbols: Liste des symboles à traiter (None = tous les symboles actifs)
    """
    db = SessionLocal()
    try:
        indicators_service = IndicatorsRecalculationService(db)
        
        # Si aucun symbole spécifié, récupérer tous les symboles actifs
        if not symbols:
            symbols_metadata = db.query(SymbolMetadata).filter(SymbolMetadata.is_active == True).all()
            symbols = [s.symbol for s in symbols_metadata]
            
            if not symbols:
                logger.warning("Aucun symbole actif trouvé.")
                return {"success": False, "message": "Aucun symbole actif trouvé."}

        logger.info(f"Début du recalcul des indicateurs de sentiment pour {len(symbols)} symboles.")
        logger.info(f"Symboles: {', '.join(symbols[:10])}{'...' if len(symbols) > 10 else ''}")
        
        results = {
            "success": 0,
            "failed": 0,
            "details": [],
            "total_symbols": len(symbols)
        }

        # Recalculer les indicateurs de sentiment pour chaque symbole
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"[{i}/{len(symbols)}] Recalcul des indicateurs de sentiment pour: {symbol}")
            
            try:
                result = indicators_service.recalculate_sentiment_indicators(symbol, start_date=date(2000, 1, 1))
                
                if result['success']:
                    results['success'] += 1
                    results['details'].append(f"{symbol}: ✅ Succès ({result['processed_dates']} dates)")
                    logger.info(f"✅ {symbol}: {result['processed_dates']} dates traitées")
                else:
                    results['failed'] += 1
                    results['details'].append(f"{symbol}: ❌ Échec - {result['error']}")
                    logger.error(f"❌ {symbol}: {result['error']}")
                    
            except Exception as e:
                results['failed'] += 1
                results['details'].append(f"{symbol}: ❌ Erreur - {str(e)}")
                logger.error(f"❌ {symbol}: Erreur inattendue - {str(e)}")

        logger.info("Recalcul des indicateurs de sentiment terminé.")
        return {"success": True, "message": "Recalcul terminé.", "results": results}

    except Exception as e:
        logger.error(f"Erreur inattendue lors du recalcul des indicateurs de sentiment: {e}")
        return {"success": False, "message": f"Erreur inattendue: {str(e)}"}
    finally:
        db.close()

def main():
    """Fonction principale"""
    print("📊 Script de recalcul des indicateurs de sentiment")
    print("=" * 60)
    
    # Analyser les arguments de ligne de commande
    symbols = None
    if len(sys.argv) > 1:
        symbols_arg = sys.argv[1]
        if symbols_arg.strip():
            symbols = [s.strip().upper() for s in symbols_arg.split(',')]
            print(f"🎯 Symboles spécifiés: {', '.join(symbols)}")
        else:
            print("📋 Tous les symboles actifs seront traités")
    else:
        print("📋 Tous les symboles actifs seront traités")
    
    print(f"⏰ Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Lancer le recalcul
    recalculate_results = recalculate_sentiment_indicators(symbols)
    
    print("\n" + "=" * 60)
    print("📈 Résultats du recalcul des indicateurs de sentiment:")
    print(f"✅ Succès global: {recalculate_results['success']}")
    
    if 'results' in recalculate_results:
        results = recalculate_results['results']
        print(f"📊 Symboles traités: {results['total_symbols']}")
        print(f"✅ Succès: {results['success']}")
        print(f"❌ Échecs: {results['failed']}")
        print(f"📈 Taux de succès: {(results['success'] / results['total_symbols'] * 100):.1f}%")
        
        # Afficher les détails des échecs
        failed_details = [detail for detail in results['details'] if '❌' in detail]
        if failed_details:
            print(f"\n⚠️ Détails des échecs ({len(failed_details)}):")
            for detail in failed_details[:10]:  # Limiter à 10 pour la lisibilité
                print(f"   {detail}")
            if len(failed_details) > 10:
                print(f"   ... et {len(failed_details) - 10} autres échecs")
    else:
        print(f"💬 Message: {recalculate_results['message']}")
    
    print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n💡 Utilisation:")
    print("   python3 recalculate_sentiment_indicators.py                    # Tous les symboles")
    print("   python3 recalculate_sentiment_indicators.py AAPL,MSFT,GOOGL    # Symboles spécifiques")

if __name__ == "__main__":
    main()
