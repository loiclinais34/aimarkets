"""
API endpoints pour l'analyse avancée - Version Simplifiée
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.models.advanced_analysis_schemas import AnalysisRequest, AnalysisResponse, HybridAnalysisRequest, HybridSearchRequest
from app.services.advanced_analysis.advanced_trading_analysis import AdvancedTradingAnalysis

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Advanced Analysis"])

@router.post("/hybrid-search")
async def hybrid_search(
    request: HybridSearchRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Recherche hybride d'opportunités combinant ML et analyse conventionnelle
    
    Args:
        request: Requête contenant les symboles et types d'analyse
        
    Returns:
        Dict contenant les opportunités hybrides trouvées
    """
    try:
        logger.info(f"Hybrid search for symbols: {request.symbols}")
        
        analyzer = AdvancedTradingAnalysis()
        opportunities = []
        
        for symbol in request.symbols:
            try:
                # Analyse avancée pour chaque symbole
                analysis_result = await analyzer.analyze_opportunity(
                    symbol=symbol,
                    time_horizon=request.time_horizon,
                    include_ml=True
                )
                
                opportunity = {
                    "symbol": symbol,
                    "hybrid_score": analysis_result.composite_score,
                    "confidence": analysis_result.confidence_level,
                    "recommendation": analysis_result.recommendation,
                    "risk_level": analysis_result.risk_level,
                    "technical_score": analysis_result.technical_score,
                    "sentiment_score": analysis_result.sentiment_score,
                    "market_score": analysis_result.market_score,
                    "ml_score": analysis_result.ml_analysis.get('accuracy', 0.5) if analysis_result.ml_analysis else 0.5,
                    "analysis_details": {
                        "technical_summary": f"Score: {analysis_result.technical_score:.2f}",
                        "sentiment_summary": f"Score: {analysis_result.sentiment_score:.2f}", 
                        "market_summary": f"Score: {analysis_result.market_score:.2f}",
                        "ml_summary": f"Score: {analysis_result.ml_analysis.get('accuracy', 0.5):.2f}" if analysis_result.ml_analysis else "No ML model"
                    }
                }
                
                opportunities.append(opportunity)
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {str(e)}")
                # Ajouter une opportunité avec score par défaut même en cas d'erreur
                opportunity = {
                    "symbol": symbol,
                    "hybrid_score": 0.0,
                    "confidence": 0.0,
                    "recommendation": "HOLD",
                    "risk_level": "HIGH",
                    "technical_score": 0.0,
                    "sentiment_score": 0.0,
                    "market_score": 0.0,
                    "ml_score": 0.0,
                    "analysis_details": {"error": str(e)}
                }
                opportunities.append(opportunity)
                continue
        
        # Trier par score hybride décroissant
        opportunities.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return {
            "opportunities": opportunities,
            "total_found": len(opportunities),
            "search_timestamp": datetime.now().isoformat(),
            "analysis_types": request.analysis_types,
            "time_horizon": request.time_horizon
        }
        
    except Exception as e:
        logger.error(f"Error in hybrid search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la recherche hybride: {str(e)}"
        )

@router.post("/opportunity/{symbol}")
async def analyze_opportunity(
    symbol: str,
    request: AnalysisRequest,
    db: Session = Depends(get_db)
) -> AnalysisResponse:
    """
    Analyse une opportunité d'investissement pour un symbole donné
    
    Args:
        symbol: Symbole de l'actif à analyser
        request: Paramètres d'analyse
        
    Returns:
        Résultat de l'analyse
    """
    try:
        logger.info(f"Analyzing opportunity for {symbol}")
        
        analyzer = AdvancedTradingAnalysis()
        
        # Effectuer l'analyse
        result = await analyzer.analyze_opportunity(
            symbol=symbol,
            time_horizon=request.time_horizon,
            include_ml=request.include_ml
        )
        
        return AnalysisResponse(
            symbol=result.symbol,
            analysis_date=result.analysis_date,
            technical_score=result.technical_score,
            sentiment_score=result.sentiment_score,
            market_score=result.market_score,
            composite_score=result.composite_score,
            confidence_level=result.confidence_level,
            recommendation=result.recommendation,
            risk_level=result.risk_level,
            technical_analysis=result.technical_analysis,
            sentiment_analysis=result.sentiment_analysis,
            market_indicators=result.market_indicators,
            ml_analysis=result.ml_analysis
        )
        
    except Exception as e:
        logger.error(f"Error analyzing opportunity for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse de l'opportunité: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Vérification de l'état du service d'analyse avancée"""
    return {
        "status": "healthy",
        "service": "Advanced Analysis API",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-simplified"
    }