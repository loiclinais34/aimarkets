#!/usr/bin/env python3
"""
Script de recalcul des indicateurs techniques

Ce script permet de recalculer tous les indicateurs techniques pour tous les symboles
ou pour des symboles spécifiques.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime
import argparse

from app.core.database import get_db
from app.models.database import HistoricalData, TechnicalIndicators
from app.services.technical_indicators import TechnicalIndicatorsCalculator

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_all_symbols(db: Session) -> List[str]:
    """Récupère tous les symboles disponibles dans la base de données"""
    symbols = db.query(HistoricalData.symbol).distinct().all()
    return [symbol[0] for symbol in symbols]

def recompute_technical_indicators(
    symbols: Optional[List[str]] = None,
    force_update: bool = False,
    db: Session = None
) -> dict:
    """
    Recalcule les indicateurs techniques pour les symboles spécifiés
    
    Args:
        symbols: Liste des symboles à traiter (None = tous)
        force_update: Forcer le recalcul même si les indicateurs existent
        db: Session de base de données
    
    Returns:
        Dict contenant le résumé du recalcul
    """
    if db is None:
        db = next(get_db())
    
    try:
        # Déterminer les symboles à traiter
        if symbols is None:
            symbols = get_all_symbols(db)
        
        logger.info(f"Starting technical indicators recompute for {len(symbols)} symbols")
        
        results = {
            "total_symbols": len(symbols),
            "processed_symbols": 0,
            "successful_symbols": 0,
            "failed_symbols": 0,
            "errors": [],
            "start_time": datetime.now().isoformat()
        }
        
        calculator = TechnicalIndicatorsCalculator(db)
        
        for symbol in symbols:
            try:
                logger.info(f"Processing technical indicators for {symbol}")
                
                # Vérifier si les indicateurs existent déjà
                if not force_update:
                    existing_count = db.query(TechnicalIndicators)\
                        .filter(TechnicalIndicators.symbol == symbol)\
                        .count()
                    
                    if existing_count > 0:
                        logger.info(f"Technical indicators for {symbol} already exist ({existing_count} records)")
                        results["processed_symbols"] += 1
                        continue
                
                # Supprimer les anciens indicateurs si force_update
                if force_update:
                    db.query(TechnicalIndicators)\
                        .filter(TechnicalIndicators.symbol == symbol)\
                        .delete()
                
                # Calculer les nouveaux indicateurs
                success = calculator.calculate_all_indicators(symbol)
                
                if success:
                    logger.info(f"Technical indicators calculated successfully for {symbol}")
                    results["successful_symbols"] += 1
                else:
                    logger.warning(f"Failed to calculate technical indicators for {symbol}")
                    results["failed_symbols"] += 1
                    results["errors"].append(f"{symbol}: Calculation failed")
                
                results["processed_symbols"] += 1
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                results["failed_symbols"] += 1
                results["errors"].append(f"{symbol}: {str(e)}")
                results["processed_symbols"] += 1
        
        results["end_time"] = datetime.now().isoformat()
        results["duration"] = (
            datetime.fromisoformat(results["end_time"]) - 
            datetime.fromisoformat(results["start_time"])
        ).total_seconds()
        
        logger.info(f"Technical indicators recompute completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in technical indicators recompute: {e}")
        return {"error": str(e)}
    finally:
        db.close()

def main():
    """Fonction principale pour l'exécution en ligne de commande"""
    parser = argparse.ArgumentParser(description="Recalculate technical indicators")
    parser.add_argument(
        "--symbols", 
        nargs="+", 
        help="Specific symbols to process (default: all symbols)"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force recalculation even if indicators exist"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Exécuter le recalcul
    db = next(get_db())
    results = recompute_technical_indicators(
        symbols=args.symbols,
        force_update=args.force,
        db=db
    )
    
    # Afficher les résultats
    print("\n" + "="*60)
    print("TECHNICAL INDICATORS RECOMPUTE RESULTS")
    print("="*60)
    print(f"Total symbols: {results.get('total_symbols', 0)}")
    print(f"Processed symbols: {results.get('processed_symbols', 0)}")
    print(f"Successful symbols: {results.get('successful_symbols', 0)}")
    print(f"Failed symbols: {results.get('failed_symbols', 0)}")
    
    if results.get('duration'):
        print(f"Duration: {results['duration']:.2f} seconds")
    
    if results.get('errors'):
        print(f"\nErrors ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("="*60)

if __name__ == "__main__":
    main()
