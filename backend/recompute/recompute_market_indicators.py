#!/usr/bin/env python3
"""
Script de recalcul des indicateurs de marché

Ce script permet de recalculer tous les indicateurs de marché pour tous les symboles
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
import numpy as np

from app.core.database import get_db
from app.models.database import HistoricalData
from app.models.market_indicators import MarketIndicators

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

def calculate_market_indicators_for_symbol(symbol: str, db: Session) -> int:
    """
    Calcule les indicateurs de marché pour un symbole spécifique
    
    Args:
        symbol: Symbole à traiter
        db: Session de base de données
    
    Returns:
        Nombre d'indicateurs créés
    """
    try:
        # Récupérer les données historiques
        historical_data = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol
        ).order_by(HistoricalData.created_at.desc()).limit(252).all()
        
        if not historical_data:
            logger.warning(f"No historical data found for {symbol}")
            return 0
        
        indicators_created = 0
        
        # Calculer la volatilité historique (20 jours)
        if len(historical_data) >= 20:
            recent_prices = [float(data.close) for data in historical_data[:20]]
            returns = [np.log(recent_prices[i] / recent_prices[i+1]) for i in range(len(recent_prices)-1)]
            volatility_20d = np.std(returns) * np.sqrt(252)  # Annualisée
            
            market_indicator = MarketIndicators(
                symbol=symbol,
                indicator_type="VOLATILITY_20D",
                indicator_value=float(volatility_20d),
                indicator_name="Volatilité Historique 20 jours",
                analysis_date=datetime.now()
            )
            db.add(market_indicator)
            indicators_created += 1
        
        # Calculer le momentum de prix (5 jours)
        if len(historical_data) >= 5:
            current_price = float(historical_data[0].close)
            price_5d_ago = float(historical_data[4].close)
            momentum_5d = (current_price - price_5d_ago) / price_5d_ago
            
            market_indicator = MarketIndicators(
                symbol=symbol,
                indicator_type="MOMENTUM_5D",
                indicator_value=float(momentum_5d),
                indicator_name="Momentum Prix 5 jours",
                analysis_date=datetime.now()
            )
            db.add(market_indicator)
            indicators_created += 1
        
        # Calculer le momentum de prix (20 jours)
        if len(historical_data) >= 20:
            current_price = float(historical_data[0].close)
            price_20d_ago = float(historical_data[19].close)
            momentum_20d = (current_price - price_20d_ago) / price_20d_ago
            
            market_indicator = MarketIndicators(
                symbol=symbol,
                indicator_type="MOMENTUM_20D",
                indicator_value=float(momentum_20d),
                indicator_name="Momentum Prix 20 jours",
                analysis_date=datetime.now()
            )
            db.add(market_indicator)
            indicators_created += 1
        
        # Calculer le ratio de volume moyen
        if len(historical_data) >= 20:
            recent_volumes = [float(data.volume) for data in historical_data[:5]]
            avg_volumes_20d = [float(data.volume) for data in historical_data[5:25]]
            
            if avg_volumes_20d:
                avg_recent_volume = np.mean(recent_volumes)
                avg_volume_20d = np.mean(avg_volumes_20d)
                volume_ratio = avg_recent_volume / avg_volume_20d if avg_volume_20d > 0 else 1.0
                
                market_indicator = MarketIndicators(
                    symbol=symbol,
                    indicator_type="VOLUME_RATIO",
                    indicator_value=float(volume_ratio),
                    indicator_name="Ratio Volume Moyen",
                    analysis_date=datetime.now()
                )
                db.add(market_indicator)
                indicators_created += 1
        
        # Calculer le RSI basique (14 jours)
        if len(historical_data) >= 15:
            prices = [float(data.close) for data in historical_data[:15]]
            gains = []
            losses = []
            
            for i in range(1, len(prices)):
                change = prices[i-1] - prices[i]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            if gains and losses:
                avg_gain = np.mean(gains)
                avg_loss = np.mean(losses)
                
                if avg_loss > 0:
                    rs = avg_gain / avg_loss
                    rsi = 100 - (100 / (1 + rs))
                    
                    market_indicator = MarketIndicators(
                        symbol=symbol,
                        indicator_type="RSI_14D",
                        indicator_value=float(rsi),
                        indicator_name="RSI 14 jours",
                        analysis_date=datetime.now()
                    )
                    db.add(market_indicator)
                    indicators_created += 1
        
        return indicators_created
        
    except Exception as e:
        logger.error(f"Error calculating market indicators for {symbol}: {e}")
        return 0

def recompute_market_indicators(
    symbols: Optional[List[str]] = None,
    force_update: bool = False,
    db: Session = None
) -> dict:
    """
    Recalcule les indicateurs de marché pour les symboles spécifiés
    
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
        
        logger.info(f"Starting market indicators recompute for {len(symbols)} symbols")
        
        results = {
            "total_symbols": len(symbols),
            "processed_symbols": 0,
            "successful_symbols": 0,
            "failed_symbols": 0,
            "total_indicators_created": 0,
            "errors": [],
            "start_time": datetime.now().isoformat()
        }
        
        for symbol in symbols:
            try:
                logger.info(f"Processing market indicators for {symbol}")
                
                # Vérifier si les indicateurs existent déjà
                if not force_update:
                    existing_count = db.query(MarketIndicators)\
                        .filter(MarketIndicators.symbol == symbol)\
                        .count()
                    
                    if existing_count > 0:
                        logger.info(f"Market indicators for {symbol} already exist ({existing_count} records)")
                        results["processed_symbols"] += 1
                        continue
                
                # Supprimer les anciens indicateurs si force_update
                if force_update:
                    db.query(MarketIndicators)\
                        .filter(MarketIndicators.symbol == symbol)\
                        .delete()
                
                # Calculer les nouveaux indicateurs
                indicators_created = calculate_market_indicators_for_symbol(symbol, db)
                
                if indicators_created > 0:
                    logger.info(f"Market indicators calculated successfully for {symbol}: {indicators_created} indicators")
                    results["successful_symbols"] += 1
                    results["total_indicators_created"] += indicators_created
                else:
                    logger.warning(f"No market indicators calculated for {symbol}")
                    results["failed_symbols"] += 1
                    results["errors"].append(f"{symbol}: No indicators calculated")
                
                results["processed_symbols"] += 1
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                results["failed_symbols"] += 1
                results["errors"].append(f"{symbol}: {str(e)}")
                results["processed_symbols"] += 1
        
        # Commit des changements
        db.commit()
        
        results["end_time"] = datetime.now().isoformat()
        results["duration"] = (
            datetime.fromisoformat(results["end_time"]) - 
            datetime.fromisoformat(results["start_time"])
        ).total_seconds()
        
        logger.info(f"Market indicators recompute completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in market indicators recompute: {e}")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()

def main():
    """Fonction principale pour l'exécution en ligne de commande"""
    parser = argparse.ArgumentParser(description="Recalculate market indicators")
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
    results = recompute_market_indicators(
        symbols=args.symbols,
        force_update=args.force,
        db=db
    )
    
    # Afficher les résultats
    print("\n" + "="*60)
    print("MARKET INDICATORS RECOMPUTE RESULTS")
    print("="*60)
    print(f"Total symbols: {results.get('total_symbols', 0)}")
    print(f"Processed symbols: {results.get('processed_symbols', 0)}")
    print(f"Successful symbols: {results.get('successful_symbols', 0)}")
    print(f"Failed symbols: {results.get('failed_symbols', 0)}")
    print(f"Total indicators created: {results.get('total_indicators_created', 0)}")
    
    if results.get('duration'):
        print(f"Duration: {results['duration']:.2f} seconds")
    
    if results.get('errors'):
        print(f"\nErrors ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("="*60)

if __name__ == "__main__":
    main()
