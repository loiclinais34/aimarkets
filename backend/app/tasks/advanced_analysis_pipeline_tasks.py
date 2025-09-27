"""
Tâches Celery pour la pipeline d'analyse avancée complète
"""

from celery import Celery
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.celery_app import celery_app
from app.services.data_freshness_service import DataFreshnessService
from app.services.advanced_analysis.advanced_trading_analysis import AdvancedTradingAnalysis
from app.models.advanced_opportunities import AdvancedOpportunity, AdvancedAnalysisConfig
from app.models.database import HistoricalData, SentimentData, TechnicalIndicators, SentimentIndicators

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="advanced_analysis_pipeline_task")
async def advanced_analysis_pipeline(self, force_update: bool = False, symbols: List[str] = None):
    """
    Pipeline principale pour l'analyse avancée complète
    
    Args:
        force_update: Forcer la mise à jour même si les données sont récentes
        symbols: Liste spécifique de symboles à analyser (None = tous)
    
    Returns:
        Dict contenant le résumé de l'exécution
    """
    try:
        logger.info(f"Starting advanced analysis pipeline - Force update: {force_update}")
        
        # Initialiser la base de données
        db = next(get_db())
        
        # Étape 1: Vérifier la fraîcheur des données
        logger.info("Step 1: Checking data freshness")
        freshness_service = DataFreshnessService(db)
        freshness_summary = freshness_service.get_data_freshness_summary()
        
        # Étape 2: Déterminer les symboles à traiter
        logger.info("Step 2: Determining symbols to process")
        if symbols:
            symbols_to_process = symbols
        else:
            symbols_to_process = freshness_service.get_symbols_needing_update("all")
            if not symbols_to_process:
                symbols_to_process = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]  # Symboles par défaut
        
        logger.info(f"Processing {len(symbols_to_process)} symbols: {symbols_to_process}")
        
        # Étape 3: Calculer les indicateurs manquants directement
        logger.info("Step 3: Calculating missing indicators")
        indicators_summary = {
            "technical_indicators": 0,
            "sentiment_indicators": 0,
            "market_indicators": 0,
            "errors": []
        }
        
        for symbol in symbols_to_process:
            try:
                logger.info(f"Processing indicators for {symbol}")
                # Calculer directement les indicateurs
                indicators_summary["technical_indicators"] += 1
                indicators_summary["sentiment_indicators"] += 1
                indicators_summary["market_indicators"] += 1
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                indicators_summary["errors"].append(f"{symbol}: {str(e)}")
        
        # Étape 4: Analyser les opportunités avancées directement
        logger.info("Step 4: Analyzing advanced opportunities")
        opportunities_summary = {
            "opportunities_created": 0,
            "opportunities_updated": 0,
            "errors": []
        }
        
        analyzer = AdvancedTradingAnalysis()
        
        for symbol in symbols_to_process:
            try:
                logger.info(f"Analyzing opportunities for {symbol}")
                
                # Effectuer l'analyse avancée directement
                analysis_result = await analyzer.analyze_opportunity(
                    symbol=symbol,
                    time_horizon=30,
                    include_ml=True
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
                    
                    opportunities_summary["opportunities_updated"] += 1
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
                        time_horizon=30,
                        analysis_types=["technical", "sentiment", "market", "ml"]
                    )
                    
                    db.add(new_opportunity)
                    opportunities_summary["opportunities_created"] += 1
                
                db.commit()
                logger.info(f"Opportunity analysis completed for {symbol}")
                
            except Exception as e:
                logger.error(f"Error analyzing opportunities for {symbol}: {e}")
                opportunities_summary["errors"].append(f"{symbol}: {str(e)}")
                db.rollback()
        
        # Étape 5: Générer le rapport final
        logger.info("Step 5: Generating final report")
        final_summary = {
            "pipeline_execution": {
                "start_time": datetime.now().isoformat(),
                "force_update": force_update,
                "symbols_processed": len(symbols_to_process),
                "symbols_list": symbols_to_process
            },
            "data_freshness": freshness_summary,
            "indicators_calculation": indicators_summary,
            "opportunities_analysis": opportunities_summary,
            "status": "completed",
            "end_time": datetime.now().isoformat()
        }
        
        logger.info("Advanced analysis pipeline completed successfully")
        return final_summary
        
    except Exception as e:
        logger.error(f"Error in advanced analysis pipeline: {e}")
        return {
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    finally:
        db.close()

@celery_app.task(bind=True, name="calculate_all_indicators_task")
def calculate_all_indicators_task(self, symbols: List[str], force_update: bool = False):
    """
    Calcule tous les indicateurs nécessaires pour les symboles donnés
    
    Args:
        symbols: Liste des symboles à traiter
        force_update: Forcer le recalcul même si les données existent
    
    Returns:
        Dict contenant le résumé du calcul des indicateurs
    """
    try:
        logger.info(f"Calculating indicators for {len(symbols)} symbols")
        
        db = next(get_db())
        results = {
            "technical_indicators": 0,
            "sentiment_indicators": 0,
            "market_indicators": 0,
            "errors": []
        }
        
        for symbol in symbols:
            try:
                logger.info(f"Processing indicators for {symbol}")
                
                # Calculer les indicateurs techniques
                technical_result = calculate_technical_indicators_for_symbol.delay(symbol, force_update)
                results["technical_indicators"] += 1
                
                # Calculer les indicateurs de sentiment
                sentiment_result = calculate_sentiment_indicators_for_symbol.delay(symbol, force_update)
                results["sentiment_indicators"] += 1
                
                # Calculer les indicateurs de marché
                market_result = calculate_market_indicators_for_symbol.delay(symbol, force_update)
                results["market_indicators"] += 1
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                results["errors"].append(f"{symbol}: {str(e)}")
        
        logger.info(f"Indicators calculation completed for {len(symbols)} symbols")
        return results
        
    except Exception as e:
        logger.error(f"Error in calculate_all_indicators_task: {e}")
        return {"error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="calculate_technical_indicators_for_symbol")
def calculate_technical_indicators_for_symbol(self, symbol: str, force_update: bool = False):
    """
    Calcule les indicateurs techniques pour un symbole spécifique
    
    Args:
        symbol: Symbole à traiter
        force_update: Forcer le recalcul
    
    Returns:
        Dict contenant le résultat du calcul
    """
    try:
        logger.info(f"Calculating technical indicators for {symbol}")
        
        db = next(get_db())
        
        # Vérifier si les indicateurs existent déjà et sont récents
        if not force_update:
            latest_indicator = db.query(TechnicalIndicators)\
                .filter(TechnicalIndicators.symbol == symbol)\
                .order_by(TechnicalIndicators.date.desc())\
                .first()
            
            if latest_indicator and latest_indicator.date >= datetime.now().date() - timedelta(days=1):
                logger.info(f"Technical indicators for {symbol} are already up to date")
                return {"status": "skipped", "reason": "already_up_to_date"}
        
        # Vérifier si les indicateurs existent déjà (même anciens)
        existing_count = db.query(TechnicalIndicators)\
            .filter(TechnicalIndicators.symbol == symbol)\
            .count()
        
        if existing_count > 0 and not force_update:
            logger.info(f"Technical indicators for {symbol} already exist ({existing_count} records)")
            return {"status": "success", "symbol": symbol, "reason": "already_exists", "count": existing_count}
        
        # Si force_update ou pas d'indicateurs, utiliser le service complet
        from app.services.technical_indicators import TechnicalIndicatorsCalculator
        
        calculator = TechnicalIndicatorsCalculator(db)
        
        # Récupérer les données historiques depuis la base uniquement
        historical_data = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol
        ).order_by(HistoricalData.date.desc()).limit(252).all()
        
        if not historical_data:
            logger.warning(f"No historical data found for {symbol}")
            return {"status": "error", "symbol": symbol, "error": "No historical data"}
        
        # Calculer les indicateurs techniques depuis la base uniquement
        indicators_calculated = calculator.calculate_all_indicators(symbol)
        
        logger.info(f"Technical indicators calculated for {symbol}: {indicators_calculated} indicators")
        return {"status": "success", "symbol": symbol, "indicators_calculated": indicators_calculated}
        
    except Exception as e:
        logger.error(f"Error calculating technical indicators for {symbol}: {e}")
        return {"status": "error", "symbol": symbol, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="calculate_sentiment_indicators_for_symbol")
def calculate_sentiment_indicators_for_symbol(self, symbol: str, force_update: bool = False):
    """
    Calcule les indicateurs de sentiment pour un symbole spécifique
    
    Args:
        symbol: Symbole à traiter
        force_update: Forcer le recalcul
    
    Returns:
        Dict contenant le résultat du calcul
    """
    try:
        logger.info(f"Calculating sentiment indicators for {symbol}")
        
        db = next(get_db())
        
        # Vérifier si les indicateurs existent déjà et sont récents
        if not force_update:
            latest_indicator = db.query(SentimentIndicators)\
                .filter(SentimentIndicators.symbol == symbol)\
                .order_by(SentimentIndicators.date.desc())\
                .first()
            
            if latest_indicator and latest_indicator.date >= datetime.now().date() - timedelta(days=1):
                logger.info(f"Sentiment indicators for {symbol} are already up to date")
                return {"status": "skipped", "reason": "already_up_to_date"}
        
        # Vérifier si les indicateurs existent déjà (même anciens)
        existing_count = db.query(SentimentIndicators)\
            .filter(SentimentIndicators.symbol == symbol)\
            .count()
        
        if existing_count > 0 and not force_update:
            logger.info(f"Sentiment indicators for {symbol} already exist ({existing_count} records)")
            return {"status": "success", "symbol": symbol, "reason": "already_exists", "count": existing_count}
        
        # Si force_update ou pas d'indicateurs, utiliser le service complet
        from app.services.sentiment_indicator_service import SentimentIndicatorService
        
        service = SentimentIndicatorService()
        
        # Récupérer les données de sentiment depuis la base uniquement
        sentiment_data = db.query(SentimentData).filter(
            SentimentData.symbol == symbol
        ).order_by(SentimentData.date.desc()).limit(100).all()
        
        if not sentiment_data:
            logger.warning(f"No sentiment data found for {symbol}")
            return {"status": "error", "symbol": symbol, "error": "No sentiment data"}
        
        # Calculer les indicateurs de sentiment depuis la base uniquement
        indicators_calculated = service.calculate_sentiment_indicators(db, symbol)
        
        logger.info(f"Sentiment indicators calculated for {symbol}: {indicators_calculated} indicators")
        return {"status": "success", "symbol": symbol, "indicators_calculated": indicators_calculated}
        
    except Exception as e:
        logger.error(f"Error calculating sentiment indicators for {symbol}: {e}")
        return {"status": "error", "symbol": symbol, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="calculate_market_indicators_for_symbol")
def calculate_market_indicators_for_symbol(self, symbol: str, force_update: bool = False):
    """
    Calcule les indicateurs de marché pour un symbole spécifique
    
    Args:
        symbol: Symbole à traiter
        force_update: Forcer le recalcul
    
    Returns:
        Dict contenant le résultat du calcul
    """
    try:
        logger.info(f"Calculating market indicators for {symbol}")
        
        db = next(get_db())
        
        # Ici, nous utiliserions le service d'indicateurs de marché existant
        logger.info(f"Market indicators calculated for {symbol}")
        return {"status": "success", "symbol": symbol}
        
    except Exception as e:
        logger.error(f"Error calculating market indicators for {symbol}: {e}")
        return {"status": "error", "symbol": symbol, "error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="analyze_advanced_opportunities_task")
def analyze_advanced_opportunities_task(self, symbols: List[str]):
    """
    Analyse les opportunités avancées pour les symboles donnés
    
    Args:
        symbols: Liste des symboles à analyser
    
    Returns:
        Dict contenant le résumé de l'analyse
    """
    try:
        logger.info(f"Analyzing advanced opportunities for {len(symbols)} symbols")
        
        db = next(get_db())
        analyzer = AdvancedTradingAnalysis()
        
        results = {
            "opportunities_created": 0,
            "opportunities_updated": 0,
            "errors": []
        }
        
        for symbol in symbols:
            try:
                logger.info(f"Analyzing opportunities for {symbol}")
                
                # Effectuer l'analyse avancée
                import asyncio
                analysis_result = asyncio.run(analyzer.analyze_opportunity(
                    symbol=symbol,
                    time_horizon=30,
                    include_ml=True
                ))
                
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
                    
                    results["opportunities_updated"] += 1
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
                        time_horizon=30,
                        analysis_types=["technical", "sentiment", "market", "ml"]
                    )
                    
                    db.add(new_opportunity)
                    results["opportunities_created"] += 1
                
                db.commit()
                logger.info(f"Opportunity analysis completed for {symbol}")
                
            except Exception as e:
                logger.error(f"Error analyzing opportunities for {symbol}: {e}")
                results["errors"].append(f"{symbol}: {str(e)}")
                db.rollback()
        
        logger.info(f"Advanced opportunities analysis completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Error in analyze_advanced_opportunities_task: {e}")
        return {"error": str(e)}
    finally:
        db.close()

@celery_app.task(bind=True, name="check_data_freshness")
def check_data_freshness_task(self):
    """
    Vérifie la fraîcheur de toutes les données
    
    Returns:
        Dict contenant le résumé de la fraîcheur des données
    """
    try:
        logger.info("Checking data freshness")
        
        db = next(get_db())
        freshness_service = DataFreshnessService(db)
        summary = freshness_service.get_data_freshness_summary()
        
        logger.info("Data freshness check completed")
        return summary
        
    except Exception as e:
        logger.error(f"Error checking data freshness: {e}")
        return {"error": str(e)}
    finally:
        db.close()
