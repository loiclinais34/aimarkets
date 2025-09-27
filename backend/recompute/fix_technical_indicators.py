#!/usr/bin/env python3
"""
Script de correction des indicateurs techniques
Supprime les valeurs NaN et recalcule les indicateurs manquants
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, date
from sqlalchemy.orm import Session
import logging

from app.core.database import get_db
from app.models.database import TechnicalIndicators, HistoricalData
from app.services.technical_indicators import TechnicalIndicatorsCalculator

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_technical_indicators_for_symbol(symbol: str, force_recalculate: bool = False):
    """
    Corrige les indicateurs techniques pour un symbole spécifique
    
    Args:
        symbol: Symbole à corriger
        force_recalculate: Forcer le recalcul complet
    
    Returns:
        Dict contenant le résultat de la correction
    """
    try:
        logger.info(f"Starting technical indicators fix for {symbol}")
        
        db = next(get_db())
        
        # Vérifier les données existantes
        existing_count = db.query(TechnicalIndicators).filter(
            TechnicalIndicators.symbol == symbol
        ).count()
        
        logger.info(f"Found {existing_count} existing technical indicators for {symbol}")
        
        if existing_count == 0:
            logger.warning(f"No technical indicators found for {symbol}")
            return {"status": "error", "symbol": symbol, "error": "No existing indicators"}
        
        # Vérifier les données historiques
        historical_count = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol
        ).count()
        
        if historical_count == 0:
            logger.warning(f"No historical data found for {symbol}")
            return {"status": "error", "symbol": symbol, "error": "No historical data"}
        
        logger.info(f"Found {historical_count} historical data points for {symbol}")
        
        # Supprimer les anciens indicateurs si force_recalculate
        if force_recalculate:
            deleted_count = db.query(TechnicalIndicators).filter(
                TechnicalIndicators.symbol == symbol
            ).delete()
            logger.info(f"Deleted {deleted_count} old indicators for {symbol}")
            db.commit()
        
        # Recalculer les indicateurs avec le service corrigé
        calculator = TechnicalIndicatorsCalculator(db)
        success = calculator.calculate_all_indicators(symbol)
        
        if success:
            # Vérifier les nouveaux indicateurs
            new_count = db.query(TechnicalIndicators).filter(
                TechnicalIndicators.symbol == symbol
            ).count()
            
            # Compter les indicateurs avec des valeurs valides
            valid_indicators = db.query(TechnicalIndicators).filter(
                TechnicalIndicators.symbol == symbol,
                TechnicalIndicators.rsi_14.isnot(None),
                TechnicalIndicators.macd.isnot(None)
            ).count()
            
            logger.info(f"Technical indicators fixed for {symbol}: {new_count} total, {valid_indicators} with valid values")
            return {
                "status": "success", 
                "symbol": symbol, 
                "total_indicators": new_count,
                "valid_indicators": valid_indicators
            }
        else:
            logger.error(f"Failed to recalculate technical indicators for {symbol}")
            return {"status": "error", "symbol": symbol, "error": "Recalculation failed"}
            
    except Exception as e:
        logger.error(f"Error fixing technical indicators for {symbol}: {e}")
        db.rollback()
        return {"status": "error", "symbol": symbol, "error": str(e)}
    finally:
        db.close()

def fix_technical_indicators_for_symbols(symbols: list, force_recalculate: bool = False):
    """
    Corrige les indicateurs techniques pour plusieurs symboles
    
    Args:
        symbols: Liste des symboles à corriger
        force_recalculate: Forcer le recalcul complet
    
    Returns:
        Dict contenant les résultats
    """
    results = {
        "total_symbols": len(symbols),
        "processed_symbols": 0,
        "successful_symbols": 0,
        "failed_symbols": 0,
        "errors": [],
        "start_time": datetime.now().isoformat()
    }
    
    logger.info(f"Starting technical indicators fix for {len(symbols)} symbols")
    
    for symbol in symbols:
        try:
            logger.info(f"Processing technical indicators fix for {symbol}")
            result = fix_technical_indicators_for_symbol(symbol, force_recalculate)
            
            results["processed_symbols"] += 1
            
            if result["status"] == "success":
                results["successful_symbols"] += 1
                logger.info(f"Technical indicators fixed successfully for {symbol}")
            else:
                results["failed_symbols"] += 1
                results["errors"].append({
                    "symbol": symbol,
                    "error": result.get("error", "Unknown error")
                })
                logger.error(f"Failed to fix technical indicators for {symbol}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            results["processed_symbols"] += 1
            results["failed_symbols"] += 1
            results["errors"].append({
                "symbol": symbol,
                "error": str(e)
            })
            logger.error(f"Error processing {symbol}: {e}")
    
    results["end_time"] = datetime.now().isoformat()
    results["duration"] = (datetime.fromisoformat(results["end_time"]) - 
                          datetime.fromisoformat(results["start_time"])).total_seconds()
    
    logger.info(f"Technical indicators fix completed: {results}")
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fix technical indicators")
    parser.add_argument("--symbols", nargs="+", help="Symbols to fix", default=["PLTR", "ABNB"])
    parser.add_argument("--force", action="store_true", help="Force recalculate")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Exécuter la correction
    results = fix_technical_indicators_for_symbols(args.symbols, args.force)
    
    # Afficher les résultats
    print("\n" + "="*80)
    print("TECHNICAL INDICATORS FIX RESULTS")
    print("="*80)
    print(f"Total symbols: {results['total_symbols']}")
    print(f"Processed: {results['processed_symbols']}")
    print(f"Successful: {results['successful_symbols']}")
    print(f"Failed: {results['failed_symbols']}")
    print(f"Duration: {results['duration']:.2f} seconds")
    print(f"Success rate: {(results['successful_symbols']/results['processed_symbols']*100):.1f}%")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  {error['symbol']}: {error['error']}")
    
    print("="*80)
