#!/usr/bin/env python3
"""
Script de calcul des indicateurs techniques
Calcule tous les indicateurs techniques pour les données historiques
"""

import sys
import os
import argparse
from datetime import datetime, date
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_db
from app.services.technical_indicators import TechnicalIndicatorsCalculator
from app.core.config import settings
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description='Calcul des indicateurs techniques')
    parser.add_argument('--symbol', type=str, help='Symbole spécifique à traiter')
    parser.add_argument('--start-date', type=str, help='Date de début (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='Date de fin (YYYY-MM-DD)')
    parser.add_argument('--all', action='store_true', help='Traiter tous les symboles')
    parser.add_argument('--summary', action='store_true', help='Afficher le résumé des indicateurs')
    
    args = parser.parse_args()
    
    # Validation des arguments
    if not any([args.symbol, args.all, args.summary]):
        parser.error("Vous devez spécifier --symbol, --all ou --summary")
    
    # Conversion des dates
    start_date = None
    end_date = None
    
    if args.start_date:
        try:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d').date()
        except ValueError:
            logger.error("Format de date invalide pour --start-date. Utilisez YYYY-MM-DD")
            sys.exit(1)
    
    if args.end_date:
        try:
            end_date = datetime.strptime(args.end_date, '%Y-%m-%d').date()
        except ValueError:
            logger.error("Format de date invalide pour --end-date. Utilisez YYYY-MM-DD")
            sys.exit(1)
    
    # Connexion à la base de données
    try:
        db = next(get_db())
        calculator = TechnicalIndicatorsCalculator(db)
        
        if args.summary:
            # Afficher le résumé
            summary = calculator.get_indicators_summary()
            print("\n📊 Résumé des indicateurs techniques:")
            print(f"   Total des indicateurs: {summary['total_indicators']:,}")
            print(f"   Symboles uniques: {summary['unique_symbols']}")
            print(f"   Dates uniques: {summary['unique_dates']}")
            
        elif args.symbol:
            # Traiter un symbole spécifique
            symbol = args.symbol.upper()
            print(f"\n🔄 Calcul des indicateurs pour {symbol}...")
            
            if start_date:
                print(f"   Date de début: {start_date}")
            if end_date:
                print(f"   Date de fin: {end_date}")
            
            success = calculator.calculate_all_indicators(symbol, start_date, end_date)
            
            if success:
                print(f"✅ Indicateurs calculés avec succès pour {symbol}")
            else:
                print(f"❌ Échec du calcul des indicateurs pour {symbol}")
                sys.exit(1)
                
        elif args.all:
            # Traiter tous les symboles
            print(f"\n🔄 Calcul des indicateurs pour tous les symboles...")
            
            if start_date:
                print(f"   Date de début: {start_date}")
            if end_date:
                print(f"   Date de fin: {end_date}")
            
            results = calculator.calculate_indicators_for_all_symbols(start_date, end_date)
            
            # Afficher les résultats
            successful = sum(1 for success in results.values() if success)
            total = len(results)
            
            print(f"\n📊 Résultats du calcul:")
            print(f"   Symboles traités avec succès: {successful}/{total}")
            print(f"   Taux de réussite: {(successful/total)*100:.1f}%")
            
            # Afficher les échecs
            failures = [symbol for symbol, success in results.items() if not success]
            if failures:
                print(f"\n⚠️ Symboles en échec ({len(failures)}):")
                for symbol in failures[:10]:  # Afficher les 10 premiers
                    print(f"   - {symbol}")
                if len(failures) > 10:
                    print(f"   ... et {len(failures) - 10} autres")
        
        # Afficher le résumé final
        if not args.summary:
            summary = calculator.get_indicators_summary()
            print(f"\n📈 Résumé final:")
            print(f"   Total des indicateurs: {summary['total_indicators']:,}")
            print(f"   Symboles uniques: {summary['unique_symbols']}")
            print(f"   Dates uniques: {summary['unique_dates']}")
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul des indicateurs: {e}")
        sys.exit(1)
    
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    main()
