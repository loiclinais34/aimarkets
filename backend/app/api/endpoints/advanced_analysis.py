"""
API d'Analyse Avancée
Phase 4: Intégration et Optimisation

Endpoints pour l'analyse combinée et le scoring hybride.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.models.advanced_analysis_schemas import AnalysisRequest, AnalysisResponse, HybridAnalysisRequest, HybridSearchRequest
from app.services.advanced_analysis.advanced_trading_analysis import AdvancedTradingAnalysis
from app.services.advanced_analysis.hybrid_scoring import HybridScoringSystem
from app.services.advanced_analysis.composite_scoring import CompositeScoringEngine, AnalysisType, RiskLevel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Analysis"])

# Initialiser les services
advanced_analyzer = AdvancedTradingAnalysis()
hybrid_scorer = HybridScoringSystem()
composite_scorer = CompositeScoringEngine()

@router.post("/opportunity/{symbol}")
async def analyze_opportunity(
    symbol: str,
    time_horizon: int = Query(30, ge=1, le=365, description="Horizon temporel en jours"),
    include_ml: bool = Query(True, description="Inclure l'analyse ML"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analyse complète d'une opportunité d'investissement
    
    Args:
        symbol: Symbole à analyser
        time_horizon: Horizon temporel en jours
        include_ml: Inclure l'analyse ML existante
        
    Returns:
        Dict contenant l'analyse complète
    """
    try:
        logger.info(f"Starting comprehensive analysis for {symbol}")
        
        # Effectuer l'analyse complète
        result = await advanced_analyzer.analyze_opportunity(
            symbol=symbol,
            time_horizon=time_horizon,
            include_ml=include_ml,
            db=db
        )
        
        logger.info(f"Analysis completed for {symbol}: {result.recommendation}")
        
        return {
            "symbol": symbol,
            "analysis_date": result.analysis_date,
            "recommendation": result.recommendation,
            "risk_level": result.risk_level,
            "composite_score": result.composite_score,
            "confidence_level": result.confidence_level,
            "scores": {
                "technical": result.technical_score,
                "sentiment": result.sentiment_score,
                "market": result.market_score,
                "ml": result.ml_score,
                "candlestick": result.candlestick_score,
                "garch": result.garch_score,
                "monte_carlo": result.monte_carlo_score,
                "markov": result.markov_score,
                "volatility": result.volatility_score
            },
            "analysis_details": {
                "technical": result.technical_analysis,
                "sentiment": result.sentiment_analysis,
                "market": result.market_indicators,
                "ml": result.ml_analysis,
                "candlestick": result.candlestick_analysis,
                "garch": result.garch_analysis,
                "monte_carlo": result.monte_carlo_analysis,
                "markov": result.markov_analysis,
                "volatility": result.volatility_analysis
            }
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive analysis for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse complète: {str(e)}"
        )

@router.post("/hybrid-search")
async def hybrid_search(
    request: HybridSearchRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Recherche hybride d'opportunités sur plusieurs symboles
    
    Args:
        request: Paramètres de recherche hybride
        
    Returns:
        Dict contenant les opportunités hybrides trouvées
    """
    try:
        logger.info(f"Hybrid search for symbols: {request.symbols}")
        
        opportunities = []
        
        for symbol in request.symbols:
            try:
                # Analyse avancée pour chaque symbole
                analysis_result = await advanced_analyzer.analyze_opportunity(
                    symbol=symbol,
                    time_horizon=request.time_horizon,
                    include_ml=True,
                    db=db
                )
                
                # Calculer le score hybride
                hybrid_score = hybrid_scorer.calculate_simple_hybrid_score(
                    ml_score=analysis_result.ml_score,
                    technical_score=analysis_result.technical_score,
                    sentiment_score=analysis_result.sentiment_score,
                    market_score=analysis_result.market_score
                )
                
                # Ajouter à la liste des opportunités
                opportunities.append({
                    "symbol": symbol,
                    "hybrid_score": hybrid_score,
                    "composite_score": analysis_result.composite_score,
                    "confidence": analysis_result.confidence_level,
                    "recommendation": analysis_result.recommendation,
                    "risk_level": analysis_result.risk_level,
                    "analysis": {
                        "technical": analysis_result.technical_analysis,
                        "sentiment": analysis_result.sentiment_analysis,
                        "market": analysis_result.market_indicators,
                        "ml": analysis_result.ml_analysis
                    }
                })
                
            except Exception as e:
                logger.warning(f"Failed to analyze {symbol}: {e}")
                continue
        
        # Trier par score hybride décroissant
        opportunities.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        return {
            "total_symbols": len(request.symbols),
            "analyzed_symbols": len(opportunities),
            "opportunities": opportunities[:request.limit] if request.limit else opportunities
        }
        
    except Exception as e:
        logger.error(f"Error in hybrid search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la recherche hybride: {str(e)}"
        )

@router.post("/composite-analysis")
async def composite_analysis(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Analyse composite avec scoring personnalisé
    
    Args:
        request: Paramètres d'analyse composite
        
    Returns:
        Dict contenant l'analyse composite
    """
    try:
        logger.info(f"Composite analysis for {request.symbol}")
        
        # Effectuer l'analyse complète
        result = await advanced_analyzer.analyze_opportunity(
            symbol=request.symbol,
            time_horizon=request.time_horizon,
            include_ml=request.include_ml,
            db=db
        )
        
        # Calculer le score composite personnalisé
        composite_score = composite_scorer.calculate_simple_composite_score(
            technical_score=result.technical_score,
            sentiment_score=result.sentiment_score,
            market_score=result.market_score,
            ml_score=result.ml_score,
            candlestick_score=result.candlestick_score,
            garch_score=result.garch_score,
            monte_carlo_score=result.monte_carlo_score,
            markov_score=result.markov_score,
            volatility_score=result.volatility_score,
            weights=request.weights
        )
        
        # Déterminer le niveau de risque
        risk_level = composite_scorer.determine_risk_level(composite_score)
        
        return {
            "symbol": request.symbol,
            "analysis_date": result.analysis_date,
            "composite_score": composite_score,
            "risk_level": risk_level,
            "recommendation": result.recommendation,
            "confidence_level": result.confidence_level,
            "scores_breakdown": {
                "technical": result.technical_score,
                "sentiment": result.sentiment_score,
                "market": result.market_score,
                "ml": result.ml_score,
                "candlestick": result.candlestick_score,
                "garch": result.garch_score,
                "monte_carlo": result.monte_carlo_score,
                "markov": result.markov_score,
                "volatility": result.volatility_score
            },
            "analysis_details": {
                "technical": result.technical_analysis,
                "sentiment": result.sentiment_analysis,
                "market": result.market_indicators,
                "ml": result.ml_analysis,
                "candlestick": result.candlestick_analysis,
                "garch": result.garch_analysis,
                "monte_carlo": result.monte_carlo_analysis,
                "markov": result.markov_analysis,
                "volatility": result.volatility_analysis
            }
        }
        
    except Exception as e:
        logger.error(f"Error in composite analysis for {request.symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse composite: {str(e)}"
        )

@router.get("/opportunities/search")
async def search_opportunities(
    # Filtres de base
    min_score: float = Query(0.5, ge=0.0, le=1.0, description="Score composite minimum"),
    max_risk: str = Query("HIGH", description="Niveau de risque maximum (LOW, MEDIUM, HIGH)"),
    limit: int = Query(10, ge=1, le=100, description="Nombre maximum de résultats"),
    
    # Filtres de dates
    date_from: str = Query(None, description="Date de début (YYYY-MM-DD) - basé sur updated_at"),
    date_to: str = Query(None, description="Date de fin (YYYY-MM-DD) - basé sur updated_at"),
    
    # Filtres de scores individuels
    min_technical_score: float = Query(None, ge=0.0, le=1.0, description="Score technique minimum"),
    min_sentiment_score: float = Query(None, ge=0.0, le=1.0, description="Score sentiment minimum"),
    min_market_score: float = Query(None, ge=0.0, le=1.0, description="Score marché minimum"),
    min_ml_score: float = Query(None, ge=0.0, le=1.0, description="Score ML minimum"),
    min_candlestick_score: float = Query(None, ge=0.0, le=1.0, description="Score chandeliers minimum"),
    min_garch_score: float = Query(None, ge=0.0, le=1.0, description="Score GARCH minimum"),
    min_monte_carlo_score: float = Query(None, ge=0.0, le=1.0, description="Score Monte Carlo minimum"),
    min_markov_score: float = Query(None, ge=0.0, le=1.0, description="Score Markov minimum"),
    min_volatility_score: float = Query(None, ge=0.0, le=1.0, description="Score volatilité minimum"),
    
    # Filtres de recommandation et confiance
    recommendations: str = Query(None, description="Recommandations séparées par virgule (BUY,SELL,HOLD,STRONG_BUY,STRONG_SELL)"),
    min_confidence: float = Query(None, ge=0.0, le=1.0, description="Niveau de confiance minimum"),
    max_confidence: float = Query(None, ge=0.0, le=1.0, description="Niveau de confiance maximum"),
    
    # Filtres de symboles
    symbols: str = Query(None, description="Symboles séparés par virgule (ex: AAPL,MSFT,GOOGL)"),
    
    # Tri
    sort_by: str = Query("composite_score", description="Champ de tri (composite_score, confidence_level, analysis_date, updated_at)"),
    sort_order: str = Query("desc", description="Ordre de tri (asc, desc)"),
    
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Recherche avancée d'opportunités existantes dans la base de données
    
    Args:
        min_score: Score composite minimum
        max_risk: Niveau de risque maximum (LOW, MEDIUM, HIGH)
        limit: Nombre maximum de résultats
        date_from: Date de début (YYYY-MM-DD) - basé sur updated_at
        date_to: Date de fin (YYYY-MM-DD) - basé sur updated_at
        min_technical_score: Score technique minimum
        min_sentiment_score: Score sentiment minimum
        min_market_score: Score marché minimum
        min_ml_score: Score ML minimum
        min_candlestick_score: Score chandeliers minimum
        min_garch_score: Score GARCH minimum
        min_monte_carlo_score: Score Monte Carlo minimum
        min_markov_score: Score Markov minimum
        min_volatility_score: Score volatilité minimum
        recommendations: Recommandations séparées par virgule
        min_confidence: Niveau de confiance minimum
        max_confidence: Niveau de confiance maximum
        symbols: Symboles séparés par virgule
        sort_by: Champ de tri
        sort_order: Ordre de tri (asc, desc)
        
    Returns:
        Dict contenant les opportunités trouvées avec métadonnées de filtrage
    """
    try:
        from app.models.advanced_opportunities import AdvancedOpportunity
        from datetime import datetime
        from sqlalchemy import and_, or_
        
        # Construire la requête
        query = db.query(AdvancedOpportunity)
        
        # Filtrer par score composite minimum
        query = query.filter(AdvancedOpportunity.composite_score >= min_score)
        
        # Filtrer par niveau de risque
        risk_levels = ["LOW", "MEDIUM", "HIGH"]
        if max_risk in risk_levels:
            max_risk_index = risk_levels.index(max_risk)
            allowed_risks = risk_levels[:max_risk_index + 1]
            query = query.filter(AdvancedOpportunity.risk_level.in_(allowed_risks))
        
        # Filtres de dates (basés sur updated_at)
        if date_from:
            try:
                date_from_obj = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(AdvancedOpportunity.updated_at >= date_from_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="Format de date_from invalide. Utilisez YYYY-MM-DD")
        
        if date_to:
            try:
                date_to_obj = datetime.strptime(date_to, "%Y-%m-%d")
                # Ajouter 23:59:59 pour inclure toute la journée
                date_to_obj = date_to_obj.replace(hour=23, minute=59, second=59)
                query = query.filter(AdvancedOpportunity.updated_at <= date_to_obj)
            except ValueError:
                raise HTTPException(status_code=400, detail="Format de date_to invalide. Utilisez YYYY-MM-DD")
        
        # Filtres de scores individuels
        if min_technical_score is not None:
            query = query.filter(AdvancedOpportunity.technical_score >= min_technical_score)
        if min_sentiment_score is not None:
            query = query.filter(AdvancedOpportunity.sentiment_score >= min_sentiment_score)
        if min_market_score is not None:
            query = query.filter(AdvancedOpportunity.market_score >= min_market_score)
        if min_ml_score is not None:
            query = query.filter(AdvancedOpportunity.ml_score >= min_ml_score)
        if min_candlestick_score is not None:
            query = query.filter(AdvancedOpportunity.candlestick_score >= min_candlestick_score)
        if min_garch_score is not None:
            query = query.filter(AdvancedOpportunity.garch_score >= min_garch_score)
        if min_monte_carlo_score is not None:
            query = query.filter(AdvancedOpportunity.monte_carlo_score >= min_monte_carlo_score)
        if min_markov_score is not None:
            query = query.filter(AdvancedOpportunity.markov_score >= min_markov_score)
        if min_volatility_score is not None:
            query = query.filter(AdvancedOpportunity.volatility_score >= min_volatility_score)
        
        # Filtres de recommandation
        if recommendations:
            try:
                rec_list = [rec.strip().upper() for rec in recommendations.split(",")]
                valid_recommendations = ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"]
                rec_list = [rec for rec in rec_list if rec in valid_recommendations]
                if rec_list:
                    query = query.filter(AdvancedOpportunity.recommendation.in_(rec_list))
            except Exception:
                pass  # Ignorer les erreurs de parsing
        
        # Filtres de confiance
        if min_confidence is not None:
            query = query.filter(AdvancedOpportunity.confidence_level >= min_confidence)
        if max_confidence is not None:
            query = query.filter(AdvancedOpportunity.confidence_level <= max_confidence)
        
        # Filtre de symboles
        if symbols:
            try:
                symbol_list = [sym.strip().upper() for sym in symbols.split(",")]
                if symbol_list:
                    query = query.filter(AdvancedOpportunity.symbol.in_(symbol_list))
            except Exception:
                pass  # Ignorer les erreurs de parsing
        
        # Tri
        valid_sort_fields = {
            "composite_score": AdvancedOpportunity.composite_score,
            "confidence_level": AdvancedOpportunity.confidence_level,
            "analysis_date": AdvancedOpportunity.analysis_date,
            "updated_at": AdvancedOpportunity.updated_at,
            "technical_score": AdvancedOpportunity.technical_score,
            "sentiment_score": AdvancedOpportunity.sentiment_score,
            "market_score": AdvancedOpportunity.market_score
        }
        
        sort_field = valid_sort_fields.get(sort_by, AdvancedOpportunity.composite_score)
        if sort_order.lower() == "asc":
            query = query.order_by(sort_field.asc())
        else:
            query = query.order_by(sort_field.desc())
        
        # Limiter les résultats
        opportunities = query.limit(limit).all()
        
        # Formater les résultats
        results = []
        for opp in opportunities:
            results.append({
                "symbol": opp.symbol,
                "analysis_date": opp.analysis_date.isoformat() if opp.analysis_date else None,
                "updated_at": opp.updated_at.isoformat() if opp.updated_at else None,
                "composite_score": float(opp.composite_score),
                "confidence_level": float(opp.confidence_level),
                "recommendation": opp.recommendation,
                "risk_level": opp.risk_level,
                "scores": {
                    "technical": float(opp.technical_score),
                    "sentiment": float(opp.sentiment_score),
                    "market": float(opp.market_score),
                    "ml": float(opp.ml_score),
                    "candlestick": float(opp.candlestick_score),
                    "garch": float(opp.garch_score),
                    "monte_carlo": float(opp.monte_carlo_score),
                    "markov": float(opp.markov_score),
                    "volatility": float(opp.volatility_score)
                }
            })
        
        # Compter le total sans limite pour les métadonnées
        total_count = db.query(AdvancedOpportunity).count()
        
        return {
            "total_found": len(results),
            "total_available": total_count,
            "filters_applied": {
                "min_score": min_score,
                "max_risk": max_risk,
                "date_from": date_from,
                "date_to": date_to,
                "recommendations": recommendations,
                "symbols": symbols,
                "sort_by": sort_by,
                "sort_order": sort_order
            },
            "opportunities": results
        }
        
    except Exception as e:
        logger.error(f"Error searching opportunities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la recherche d'opportunités: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Vérification de l'état du service d'analyse avancée"""
    return {
        "status": "healthy",
        "service": "Advanced Analysis API",
        "components": {
            "advanced_analyzer": "available",
            "hybrid_scorer": "available", 
            "composite_scorer": "available"
        }
    }