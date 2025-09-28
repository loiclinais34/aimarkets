#!/usr/bin/env python3
"""
Script principal de recalcul complet

Ce script orchestre le recalcul de tous les éléments :
- Indicateurs techniques
- Indicateurs de sentiment
- Indicateurs de marché
- Opportunités avancées
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

# Import des scripts de recalcul
from recompute_technical_indicators import recompute_technical_indicators
from recompute_sentiment_indicators import recompute_sentiment_indicators
from recompute_market_indicators import recompute_market_indicators
from recompute_volatility_indicators import recompute_volatility_indicators_for_symbols
from recompute_candlestick_patterns import recompute_candlestick_patterns_for_symbols
from recompute_garch_models import recompute_garch_models_for_symbols
from recompute_monte_carlo import recompute_monte_carlo_simulations_for_symbols
from recompute_markov_chains import recompute_markov_chain_analysis_for_symbols
from recompute_advanced_opportunities import recompute_advanced_opportunities

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def recompute_all(
    symbols: Optional[List[str]] = None,
    force_update: bool = False,
    skip_technical: bool = False,
    skip_sentiment: bool = False,
    skip_market: bool = False,
    skip_volatility: bool = False,
    skip_candlestick: bool = False,
    skip_garch: bool = False,
    skip_monte_carlo: bool = False,
    skip_markov: bool = False,
    skip_opportunities: bool = False,
    time_horizon: int = 30,
    include_ml: bool = True,
    db: Session = None
) -> dict:
    """
    Recalcule tous les éléments pour les symboles spécifiés
    
    Args:
        symbols: Liste des symboles à traiter (None = tous)
        force_update: Forcer le recalcul même si les données existent
        skip_technical: Ignorer le recalcul des indicateurs techniques
        skip_sentiment: Ignorer le recalcul des indicateurs de sentiment
        skip_market: Ignorer le recalcul des indicateurs de marché
        skip_volatility: Ignorer le recalcul des indicateurs de volatilité
        skip_candlestick: Ignorer le recalcul des patterns de candlesticks
        skip_garch: Ignorer le recalcul des modèles GARCH
        skip_monte_carlo: Ignorer le recalcul des simulations Monte Carlo
        skip_markov: Ignorer le recalcul des chaînes de Markov
        skip_opportunities: Ignorer le recalcul des opportunités avancées
        time_horizon: Horizon temporel en jours pour les opportunités
        include_ml: Inclure l'analyse ML dans les opportunités
        db: Session de base de données
    
    Returns:
        Dict contenant le résumé complet du recalcul
    """
    if db is None:
        db = next(get_db())
    
    try:
        logger.info("Starting complete recompute process")
        
        # Si aucun symbole n'est spécifié, récupérer tous les symboles de la base
        if symbols is None:
            from app.models.database import HistoricalData
            distinct_symbols = db.query(HistoricalData.symbol).distinct().all()
            symbols = [s[0] for s in distinct_symbols]
            logger.info(f"Retrieved {len(symbols)} symbols from database")
        
        overall_results = {
            "start_time": datetime.now().isoformat(),
            "symbols": symbols,
            "force_update": force_update,
            "components": {},
            "total_duration": 0,
            "success": True
        }
        
        # 1. Recalcul des indicateurs techniques
        if not skip_technical:
            logger.info("="*60)
            logger.info("STEP 1: RECOMPUTING TECHNICAL INDICATORS")
            logger.info("="*60)
            
            technical_results = recompute_technical_indicators(
                symbols=symbols,
                force_update=True,
                db=db
            )
            overall_results["components"]["technical_indicators"] = technical_results
            
            if technical_results.get("error"):
                logger.error(f"Technical indicators recompute failed: {technical_results['error']}")
                overall_results["success"] = False
        else:
            logger.info("Skipping technical indicators recompute")
            overall_results["components"]["technical_indicators"] = {"skipped": True}
        
        # 2. Recalcul des indicateurs de sentiment
        if not skip_sentiment:
            logger.info("="*60)
            logger.info("STEP 2: RECOMPUTING SENTIMENT INDICATORS")
            logger.info("="*60)
            
            sentiment_results = recompute_sentiment_indicators(
                symbols=symbols,
                force_update=True,
                db=db
            )
            overall_results["components"]["sentiment_indicators"] = sentiment_results
            
            if sentiment_results.get("error"):
                logger.error(f"Sentiment indicators recompute failed: {sentiment_results['error']}")
                overall_results["success"] = False
        else:
            logger.info("Skipping sentiment indicators recompute")
            overall_results["components"]["sentiment_indicators"] = {"skipped": True}
        
        # 3. Recalcul des indicateurs de marché
        if not skip_market:
            logger.info("="*60)
            logger.info("STEP 3: RECOMPUTING MARKET INDICATORS")
            logger.info("="*60)
            
            market_results = recompute_market_indicators(
                symbols=symbols,
                force_update=True,
                db=db
            )
            overall_results["components"]["market_indicators"] = market_results
            
            if market_results.get("error"):
                logger.error(f"Market indicators recompute failed: {market_results['error']}")
                overall_results["success"] = False
        else:
            logger.info("Skipping market indicators recompute")
            overall_results["components"]["market_indicators"] = {"skipped": True}
        
        # 4. Recalcul des indicateurs de volatilité
        if not skip_volatility:
            logger.info("="*60)
            logger.info("STEP 4: RECOMPUTING VOLATILITY INDICATORS")
            logger.info("="*60)
            
            logger.info(f"Symbols to process: {symbols}")
            logger.info(f"Force update: {force_update}")
            
            volatility_results = recompute_volatility_indicators_for_symbols(
                symbols=symbols,
                force_update=force_update
            )
            
            logger.info(f"Volatility results type: {type(volatility_results)}")
            logger.info(f"Volatility results: {volatility_results}")
            
            if volatility_results is None:
                logger.error("Volatility indicators recompute returned None")
                volatility_results = {"error": "Function returned None", "total_symbols": 0, "processed_symbols": 0, "successful_symbols": 0, "failed_symbols": len(symbols) if symbols else 0}
                overall_results["success"] = False
            
            overall_results["components"]["volatility_indicators"] = volatility_results
            
            if volatility_results.get("error"):
                logger.error(f"Volatility indicators recompute failed: {volatility_results['error']}")
                overall_results["success"] = False
        else:
            logger.info("Skipping volatility indicators recompute")
            overall_results["components"]["volatility_indicators"] = {"skipped": True}
        
        # 5. Recalcul des patterns de candlesticks
        if not skip_candlestick:
            logger.info("="*60)
            logger.info("STEP 5: RECOMPUTING CANDLESTICK PATTERNS")
            logger.info("="*60)
            
            candlestick_results = recompute_candlestick_patterns_for_symbols(
                symbols=symbols,
                force_update=force_update
            )
            overall_results["components"]["candlestick_patterns"] = candlestick_results
            
            if candlestick_results.get("error"):
                logger.error(f"Candlestick patterns recompute failed: {candlestick_results['error']}")
                overall_results["success"] = False
        else:
            logger.info("Skipping candlestick patterns recompute")
            overall_results["components"]["candlestick_patterns"] = {"skipped": True}
        
        # 6. Recalcul des modèles GARCH
        if not skip_garch:
            logger.info("="*60)
            logger.info("STEP 6: RECOMPUTING GARCH MODELS")
            logger.info("="*60)
            
            garch_results = recompute_garch_models_for_symbols(
                symbols=symbols,
                force_update=force_update
            )
            overall_results["components"]["garch_models"] = garch_results
            
            if garch_results.get("error"):
                logger.error(f"GARCH models recompute failed: {garch_results['error']}")
                overall_results["success"] = False
        else:
            logger.info("Skipping GARCH models recompute")
            overall_results["components"]["garch_models"] = {"skipped": True}
        
        # 7. Recalcul des simulations Monte Carlo
        if not skip_monte_carlo:
            logger.info("="*60)
            logger.info("STEP 7: RECOMPUTING MONTE CARLO SIMULATIONS")
            logger.info("="*60)
            
            monte_carlo_results = recompute_monte_carlo_simulations_for_symbols(
                symbols=symbols,
                force_update=force_update,
                time_horizon=time_horizon
            )
            overall_results["components"]["monte_carlo_simulations"] = monte_carlo_results
            
            if monte_carlo_results.get("error"):
                logger.error(f"Monte Carlo simulations recompute failed: {monte_carlo_results['error']}")
                overall_results["success"] = False
        else:
            logger.info("Skipping Monte Carlo simulations recompute")
            overall_results["components"]["monte_carlo_simulations"] = {"skipped": True}
        
        # 8. Recalcul des chaînes de Markov
        if not skip_markov:
            logger.info("="*60)
            logger.info("STEP 8: RECOMPUTING MARKOV CHAIN ANALYSIS")
            logger.info("="*60)
            
            markov_results = recompute_markov_chain_analysis_for_symbols(
                symbols=symbols,
                force_update=force_update
            )
            overall_results["components"]["markov_chain_analysis"] = markov_results
            
            if markov_results.get("error"):
                logger.error(f"Markov chain analysis recompute failed: {markov_results['error']}")
                overall_results["success"] = False
        else:
            logger.info("Skipping Markov chain analysis recompute")
            overall_results["components"]["markov_chain_analysis"] = {"skipped": True}
        
        # 9. Recalcul des opportunités avancées
        if not skip_opportunities:
            logger.info("="*60)
            logger.info("STEP 9: RECOMPUTING ADVANCED OPPORTUNITIES")
            logger.info("="*60)
            
            opportunities_results = recompute_advanced_opportunities(
                symbols=symbols,
                force_update=force_update,
                time_horizon=time_horizon,
                include_ml=include_ml,
                db=db
            )
            overall_results["components"]["advanced_opportunities"] = opportunities_results
            
            if opportunities_results.get("error"):
                logger.error(f"Advanced opportunities recompute failed: {opportunities_results['error']}")
                overall_results["success"] = False
        else:
            logger.info("Skipping advanced opportunities recompute")
            overall_results["components"]["advanced_opportunities"] = {"skipped": True}
        
        # Calculer le résumé global
        overall_results["end_time"] = datetime.now().isoformat()
        overall_results["total_duration"] = (
            datetime.fromisoformat(overall_results["end_time"]) - 
            datetime.fromisoformat(overall_results["start_time"])
        ).total_seconds()
        
        # Compter les succès et échecs globaux
        total_successful = 0
        total_failed = 0
        total_processed = 0
        
        for component, results in overall_results["components"].items():
            if not results.get("skipped") and not results.get("error"):
                total_successful += results.get("successful_symbols", 0)
                total_failed += results.get("failed_symbols", 0)
                total_processed += results.get("processed_symbols", 0)
        
        overall_results["summary"] = {
            "total_processed": total_processed,
            "total_successful": total_successful,
            "total_failed": total_failed,
            "success_rate": (total_successful / total_processed * 100) if total_processed > 0 else 0
        }
        
        logger.info("="*60)
        logger.info("COMPLETE RECOMPUTE FINISHED")
        logger.info("="*60)
        logger.info(f"Total duration: {overall_results['total_duration']:.2f} seconds")
        logger.info(f"Success rate: {overall_results['summary']['success_rate']:.1f}%")
        logger.info(f"Overall success: {overall_results['success']}")
        
        return overall_results
        
    except Exception as e:
        logger.error(f"Error in complete recompute: {e}")
        return {"error": str(e), "success": False}
    finally:
        db.close()

def main():
    """Fonction principale pour l'exécution en ligne de commande"""
    parser = argparse.ArgumentParser(description="Complete recompute of all data")
    parser.add_argument(
        "--symbols", 
        nargs="+", 
        help="Specific symbols to process (default: all symbols)"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force recalculation even if data exists"
    )
    parser.add_argument(
        "--skip-technical", 
        action="store_true", 
        help="Skip technical indicators recompute"
    )
    parser.add_argument(
        "--skip-sentiment", 
        action="store_true", 
        help="Skip sentiment indicators recompute"
    )
    parser.add_argument(
        "--skip-market", 
        action="store_true", 
        help="Skip market indicators recompute"
    )
    parser.add_argument(
        "--skip-volatility", 
        action="store_true", 
        help="Skip volatility indicators recompute"
    )
    parser.add_argument(
        "--skip-candlestick", 
        action="store_true", 
        help="Skip candlestick patterns recompute"
    )
    parser.add_argument(
        "--skip-garch", 
        action="store_true", 
        help="Skip GARCH models recompute"
    )
    parser.add_argument(
        "--skip-monte-carlo", 
        action="store_true", 
        help="Skip Monte Carlo simulations recompute"
    )
    parser.add_argument(
        "--skip-markov", 
        action="store_true", 
        help="Skip Markov chain analysis recompute"
    )
    parser.add_argument(
        "--skip-opportunities", 
        action="store_true", 
        help="Skip advanced opportunities recompute"
    )
    parser.add_argument(
        "--time-horizon", 
        type=int, 
        default=30, 
        help="Time horizon in days for opportunities (default: 30)"
    )
    parser.add_argument(
        "--no-ml", 
        action="store_true", 
        help="Disable ML analysis in opportunities"
    )
    parser.add_argument(
        "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Exécuter le recalcul complet
    db = next(get_db())
    results = recompute_all(
        symbols=args.symbols,
        force_update=args.force,
        skip_technical=args.skip_technical,
        skip_sentiment=args.skip_sentiment,
        skip_market=args.skip_market,
        skip_volatility=args.skip_volatility,
        skip_candlestick=args.skip_candlestick,
        skip_garch=args.skip_garch,
        skip_monte_carlo=args.skip_monte_carlo,
        skip_markov=args.skip_markov,
        skip_opportunities=args.skip_opportunities,
        time_horizon=args.time_horizon,
        include_ml=not args.no_ml,
        db=db
    )
    
    # Afficher les résultats
    print("\n" + "="*80)
    print("COMPLETE RECOMPUTE RESULTS")
    print("="*80)
    
    if results.get("error"):
        print(f"ERROR: {results['error']}")
        return
    
    summary = results.get("summary", {})
    print(f"Total processed: {summary.get('total_processed', 0)}")
    print(f"Total successful: {summary.get('total_successful', 0)}")
    print(f"Total failed: {summary.get('total_failed', 0)}")
    print(f"Success rate: {summary.get('success_rate', 0):.1f}%")
    print(f"Total duration: {results.get('total_duration', 0):.2f} seconds")
    print(f"Overall success: {results.get('success', False)}")
    
    print("\nComponent Details:")
    for component, component_results in results.get("components", {}).items():
        if component_results.get("skipped"):
            print(f"  {component}: SKIPPED")
        elif component_results.get("error"):
            print(f"  {component}: ERROR - {component_results['error']}")
        else:
            print(f"  {component}: {component_results.get('successful_symbols', 0)}/{component_results.get('processed_symbols', 0)} successful")
    
    print("="*80)

if __name__ == "__main__":
    main()
