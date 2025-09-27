#!/usr/bin/env python3
"""
Script de recalcul des patterns de candlesticks
Détecte et calcule les patterns de chandeliers pour les symboles
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging

from app.core.database import get_db
from app.models.database import HistoricalData
from app.models.technical_analysis import CandlestickPatterns

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CandlestickPatternDetector:
    """Détecteur de patterns de candlesticks"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def detect_candlestick_patterns(self, symbol: str, force_update: bool = False) -> dict:
        """
        Détecte les patterns de candlesticks pour un symbole
        
        Args:
            symbol: Symbole à traiter
            force_update: Forcer le recalcul
        
        Returns:
            Dict contenant le résultat de la détection
        """
        try:
            logger.info(f"Detecting candlestick patterns for {symbol}")
            
            # Vérifier si les patterns existent déjà et sont récents
            if not force_update:
                latest_pattern = self.db.query(CandlestickPatterns)\
                    .filter(CandlestickPatterns.symbol == symbol)\
                    .order_by(CandlestickPatterns.created_at.desc())\
                    .first()
                
                if latest_pattern and latest_pattern.created_at >= datetime.now() - timedelta(days=1):
                    logger.info(f"Candlestick patterns for {symbol} are already up to date")
                    return {"status": "skipped", "reason": "already_up_to_date"}
            
            # Récupérer les données historiques (30 derniers jours)
            historical_data = self.db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol
            ).order_by(HistoricalData.date.desc()).limit(30).all()
            
            if not historical_data:
                logger.warning(f"No historical data found for {symbol}")
                return {"status": "error", "symbol": symbol, "error": "No historical data"}
            
            # Convertir en DataFrame
            data = []
            for row in historical_data:
                data.append({
                    'date': row.date,
                    'open': float(row.open),
                    'high': float(row.high),
                    'low': float(row.low),
                    'close': float(row.close),
                    'volume': int(row.volume)
                })
            
            df = pd.DataFrame(data)
            df = df.sort_values('date').reset_index(drop=True)
            
            # Supprimer les anciens patterns si force_update
            if force_update:
                self.db.query(CandlestickPatterns).filter(CandlestickPatterns.symbol == symbol).delete()
            
            # Détecter les patterns
            patterns_detected = self._detect_patterns(df, symbol)
            
            logger.info(f"Candlestick patterns detected for {symbol}: {len(patterns_detected)} patterns")
            return {
                "status": "success", 
                "symbol": symbol, 
                "patterns_detected": len(patterns_detected)
            }
            
        except Exception as e:
            logger.error(f"Error detecting candlestick patterns for {symbol}: {e}")
            self.db.rollback()
            return {"status": "error", "symbol": symbol, "error": str(e)}
    
    def _detect_patterns(self, df: pd.DataFrame, symbol: str) -> list:
        """Détecter les patterns de candlesticks"""
        patterns = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            
            # Calculer les caractéristiques de la bougie
            body_size = abs(row['close'] - row['open'])
            upper_shadow = row['high'] - max(row['open'], row['close'])
            lower_shadow = min(row['open'], row['close']) - row['low']
            total_range = row['high'] - row['low']
            
            # Éviter la division par zéro
            if total_range == 0:
                continue
            
            body_ratio = body_size / total_range
            upper_shadow_ratio = upper_shadow / total_range
            lower_shadow_ratio = lower_shadow / total_range
            
            # Détecter les patterns
            pattern_info = self._identify_pattern(
                row, body_ratio, upper_shadow_ratio, lower_shadow_ratio
            )
            
            if pattern_info:
                pattern = CandlestickPatterns(
                    symbol=symbol,
                    pattern_type=pattern_info['type'],
                    pattern_direction=pattern_info['direction'],
                    pattern_strength=float(pattern_info['strength']),
                    open_price=float(row['open']),
                    high_price=float(row['high']),
                    low_price=float(row['low']),
                    close_price=float(row['close']),
                    volume=float(row['volume'])
                )
                self.db.add(pattern)
                patterns.append(pattern_info)
        
        self.db.commit()
        return patterns
    
    def _identify_pattern(self, row: pd.Series, body_ratio: float, upper_shadow_ratio: float, lower_shadow_ratio: float) -> dict:
        """Identifier le pattern de candlestick"""
        
        # Doji
        if body_ratio < 0.1:
            return {
                'type': 'DOJI',
                'direction': 'NEUTRAL',
                'strength': 0.7
            }
        
        # Hammer
        if body_ratio > 0.3 and lower_shadow_ratio > 0.6 and upper_shadow_ratio < 0.1:
            direction = 'BULLISH' if row['close'] > row['open'] else 'BEARISH'
            return {
                'type': 'HAMMER',
                'direction': direction,
                'strength': 0.8
            }
        
        # Shooting Star
        if body_ratio > 0.3 and upper_shadow_ratio > 0.6 and lower_shadow_ratio < 0.1:
            direction = 'BEARISH' if row['close'] < row['open'] else 'BULLISH'
            return {
                'type': 'SHOOTING_STAR',
                'direction': direction,
                'strength': 0.8
            }
        
        # Marubozu
        if body_ratio > 0.9:
            direction = 'BULLISH' if row['close'] > row['open'] else 'BEARISH'
            return {
                'type': 'MARUBOZU',
                'direction': direction,
                'strength': 0.9
            }
        
        # Spinning Top
        if 0.2 < body_ratio < 0.4 and upper_shadow_ratio > 0.3 and lower_shadow_ratio > 0.3:
            return {
                'type': 'SPINNING_TOP',
                'direction': 'NEUTRAL',
                'strength': 0.5
            }
        
        return None

def recompute_candlestick_patterns_for_symbol(symbol: str, force_update: bool = False) -> dict:
    """
    Recalculer les patterns de candlesticks pour un symbole
    
    Args:
        symbol: Symbole à traiter
        force_update: Forcer le recalcul
    
    Returns:
        Dict contenant le résultat
    """
    try:
        db = next(get_db())
        detector = CandlestickPatternDetector(db)
        result = detector.detect_candlestick_patterns(symbol, force_update)
        return result
    except Exception as e:
        logger.error(f"Error in recompute_candlestick_patterns_for_symbol: {e}")
        return {"status": "error", "symbol": symbol, "error": str(e)}
    finally:
        db.close()

def recompute_candlestick_patterns_for_symbols(symbols: list, force_update: bool = False) -> dict:
    """
    Recalculer les patterns de candlesticks pour plusieurs symboles
    
    Args:
        symbols: Liste des symboles à traiter
        force_update: Forcer le recalcul
    
    Returns:
        Dict contenant les résultats
    """
    results = {
        "total_symbols": len(symbols),
        "processed_symbols": 0,
        "successful_symbols": 0,
        "failed_symbols": 0,
        "total_patterns_detected": 0,
        "errors": [],
        "start_time": datetime.now().isoformat()
    }
    
    logger.info(f"Starting candlestick patterns recompute for {len(symbols)} symbols")
    
    for symbol in symbols:
        try:
            logger.info(f"Processing candlestick patterns for {symbol}")
            result = recompute_candlestick_patterns_for_symbol(symbol, force_update)
            
            results["processed_symbols"] += 1
            
            if result["status"] == "success":
                results["successful_symbols"] += 1
                results["total_patterns_detected"] += result.get("patterns_detected", 0)
                logger.info(f"Candlestick patterns calculated successfully for {symbol}: {result.get('patterns_detected', 0)} patterns")
            elif result["status"] == "skipped":
                results["successful_symbols"] += 1
                logger.info(f"Candlestick patterns skipped for {symbol}: {result.get('reason', 'Unknown')}")
            else:
                results["failed_symbols"] += 1
                results["errors"].append({
                    "symbol": symbol,
                    "error": result.get("error", "Unknown error")
                })
                logger.error(f"Failed to calculate candlestick patterns for {symbol}: {result.get('error', 'Unknown error')}")
                
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
    
    logger.info(f"Candlestick patterns recompute completed: {results}")
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Recompute candlestick patterns")
    parser.add_argument("--symbols", nargs="+", help="Symbols to recompute", default=["PLTR"])
    parser.add_argument("--force", action="store_true", help="Force recalculate")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Exécuter le recalcul
    results = recompute_candlestick_patterns_for_symbols(args.symbols, args.force)
    
    # Afficher les résultats
    print("\n" + "="*80)
    print("CANDLESTICK PATTERNS RECOMPUTE RESULTS")
    print("="*80)
    print(f"Total symbols: {results['total_symbols']}")
    print(f"Processed: {results['processed_symbols']}")
    print(f"Successful: {results['successful_symbols']}")
    print(f"Failed: {results['failed_symbols']}")
    print(f"Total patterns detected: {results['total_patterns_detected']}")
    print(f"Duration: {results['duration']:.2f} seconds")
    print(f"Success rate: {(results['successful_symbols']/results['processed_symbols']*100):.1f}%")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  {error['symbol']}: {error['error']}")
    
    print("="*80)
