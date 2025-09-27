#!/usr/bin/env python3
"""
Script de recalcul des opportunités avancées

Ce script permet de recalculer toutes les opportunités avancées pour tous les symboles
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
import asyncio

from app.core.database import get_db
from app.models.database import HistoricalData
from app.models.advanced_opportunities import AdvancedOpportunity
from app.services.advanced_analysis.advanced_trading_analysis import AdvancedTradingAnalysis

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

async def analyze_opportunity_for_symbol(
    symbol: str, 
    time_horizon: int = 30,
    include_ml: bool = True,
    db: Session = None
) -> bool:
    """
    Analyse une opportunité pour un symbole spécifique
    
    Args:
        symbol: Symbole à analyser
        time_horizon: Horizon temporel en jours
        include_ml: Inclure l'analyse ML
        db: Session de base de données
    
    Returns:
        True si l'analyse a réussi, False sinon
    """
    try:
        analyzer = AdvancedTradingAnalysis()
        
        # Effectuer l'analyse avancée
        analysis_result = await analyzer.analyze_opportunity(
            symbol=symbol,
            time_horizon=time_horizon,
            include_ml=include_ml,
            db=db
        )
        
        # Vérifier si une opportunité existe déjà pour ce symbole aujourd'hui
        existing_opportunity = db.query(AdvancedOpportunity)\
            .filter(AdvancedOpportunity.symbol == symbol)\
            .filter(AdvancedOpportunity.analysis_date >= datetime.now().date())\
            .first()
        
        if existing_opportunity:
            # Mettre à jour l'opportunité existante
            existing_opportunity.technical_score = analysis_result.technical_score
            existing_opportunity.sentiment_score = analysis_result.sentiment_score
            existing_opportunity.market_score = analysis_result.market_score
            existing_opportunity.ml_score = getattr(analysis_result, 'ml_score', 0.5)
            existing_opportunity.hybrid_score = analysis_result.composite_score
            existing_opportunity.confidence_level = analysis_result.confidence_level
            existing_opportunity.recommendation = analysis_result.recommendation
            existing_opportunity.risk_level = analysis_result.risk_level
            existing_opportunity.updated_at = datetime.now()
            
            logger.info(f"Updated existing opportunity for {symbol}")
        else:
            # Créer une nouvelle opportunité
            new_opportunity = AdvancedOpportunity(
                symbol=symbol,
                analysis_date=datetime.now(),
                technical_score=analysis_result.technical_score,
                sentiment_score=analysis_result.sentiment_score,
                market_score=analysis_result.market_score,
                ml_score=getattr(analysis_result, 'ml_score', 0.5),
                hybrid_score=analysis_result.composite_score,
                confidence_level=analysis_result.confidence_level,
                recommendation=analysis_result.recommendation,
                risk_level=analysis_result.risk_level,
                technical_analysis=analysis_result.technical_analysis,
                sentiment_analysis=analysis_result.sentiment_analysis,
                market_analysis=analysis_result.market_indicators,
                ml_analysis=getattr(analysis_result, 'ml_analysis', {}),
                time_horizon=time_horizon,
                analysis_types=["technical", "sentiment", "market", "ml"]
            )
            
            db.add(new_opportunity)
            logger.info(f"Created new opportunity for {symbol}")
        
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"Error analyzing opportunity for {symbol}: {e}")
        db.rollback()
        return False

def recompute_advanced_opportunities(
    symbols: Optional[List[str]] = None,
    force_update: bool = False,
    time_horizon: int = 30,
    include_ml: bool = True,
    db: Session = None
) -> dict:
    """
    Recalcule les opportunités avancées pour les symboles spécifiés
    
    Args:
        symbols: Liste des symboles à traiter (None = tous)
        force_update: Forcer le recalcul même si les opportunités existent
        time_horizon: Horizon temporel en jours
        include_ml: Inclure l'analyse ML
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
        
        logger.info(f"Starting advanced opportunities recompute for {len(symbols)} symbols")
        
        results = {
            "total_symbols": len(symbols),
            "processed_symbols": 0,
            "successful_symbols": 0,
            "failed_symbols": 0,
            "opportunities_created": 0,
            "opportunities_updated": 0,
            "errors": [],
            "start_time": datetime.now().isoformat()
        }
        
        for symbol in symbols:
            try:
                logger.info(f"Processing advanced opportunity for {symbol}")
                
                # Vérifier si l'opportunité existe déjà
                if not force_update:
                    existing_opportunity = db.query(AdvancedOpportunity)\
                        .filter(AdvancedOpportunity.symbol == symbol)\
                        .filter(AdvancedOpportunity.analysis_date >= datetime.now().date())\
                        .first()
                    
                    if existing_opportunity:
                        logger.info(f"Advanced opportunity for {symbol} already exists")
                        results["processed_symbols"] += 1
                        continue
                
                # Supprimer les anciennes opportunités si force_update
                if force_update:
                    db.query(AdvancedOpportunity)\
                        .filter(AdvancedOpportunity.symbol == symbol)\
                        .delete()
                
                # Analyser l'opportunité
                success = asyncio.run(analyze_opportunity_for_symbol(
                    symbol=symbol,
                    time_horizon=time_horizon,
                    include_ml=include_ml,
                    db=db
                ))
                
                if success:
                    logger.info(f"Advanced opportunity calculated successfully for {symbol}")
                    results["successful_symbols"] += 1
                    
                    # Compter les créations/mises à jour
                    if force_update:
                        results["opportunities_created"] += 1
                    else:
                        # Vérifier si c'était une création ou une mise à jour
                        opportunity = db.query(AdvancedOpportunity)\
                            .filter(AdvancedOpportunity.symbol == symbol)\
                            .filter(AdvancedOpportunity.analysis_date >= datetime.now().date())\
                            .first()
                        
                        if opportunity and opportunity.created_at == opportunity.updated_at:
                            results["opportunities_created"] += 1
                        else:
                            results["opportunities_updated"] += 1
                else:
                    logger.warning(f"Failed to calculate advanced opportunity for {symbol}")
                    results["failed_symbols"] += 1
                    results["errors"].append(f"{symbol}: Analysis failed")
                
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
        
        logger.info(f"Advanced opportunities recompute completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in advanced opportunities recompute: {e}")
        return {"error": str(e)}
    finally:
        db.close()

def main():
    """Fonction principale pour l'exécution en ligne de commande"""
    parser = argparse.ArgumentParser(description="Recalculate advanced opportunities")
    parser.add_argument(
        "--symbols", 
        nargs="+", 
        help="Specific symbols to process (default: all symbols)"
    )
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force recalculation even if opportunities exist"
    )
    parser.add_argument(
        "--time-horizon", 
        type=int, 
        default=30, 
        help="Time horizon in days (default: 30)"
    )
    parser.add_argument(
        "--no-ml", 
        action="store_true", 
        help="Disable ML analysis"
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
    results = recompute_advanced_opportunities(
        symbols=args.symbols,
        force_update=args.force,
        time_horizon=args.time_horizon,
        include_ml=not args.no_ml,
        db=db
    )
    
    # Afficher les résultats
    print("\n" + "="*60)
    print("ADVANCED OPPORTUNITIES RECOMPUTE RESULTS")
    print("="*60)
    print(f"Total symbols: {results.get('total_symbols', 0)}")
    print(f"Processed symbols: {results.get('processed_symbols', 0)}")
    print(f"Successful symbols: {results.get('successful_symbols', 0)}")
    print(f"Failed symbols: {results.get('failed_symbols', 0)}")
    print(f"Opportunities created: {results.get('opportunities_created', 0)}")
    print(f"Opportunities updated: {results.get('opportunities_updated', 0)}")
    
    if results.get('duration'):
        print(f"Duration: {results['duration']:.2f} seconds")
    
    if results.get('errors'):
        print(f"\nErrors ({len(results['errors'])}):")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("="*60)

if __name__ == "__main__":
    main()
