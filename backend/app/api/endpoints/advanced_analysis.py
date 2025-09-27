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
            include_ml=include_ml
        )
        
        # Retourner le résumé de l'analyse
        analysis_summary = advanced_analyzer.get_analysis_summary(result)
        
        return {
            "success": True,
            "symbol": symbol,
            "analysis_date": result.analysis_date.isoformat(),
            "time_horizon": time_horizon,
            "summary": analysis_summary,
            "detailed_analysis": {
                "technical": result.technical_analysis,
                "sentiment": result.sentiment_analysis,
                "market": result.market_indicators,
                "ml": result.ml_analysis
            }
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive analysis for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse complète: {str(e)}"
        )

>>>>>>> 9a31cdaa90ac59c5c2dba51e90814207bf0d73a6
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
        
<<<<<<< HEAD
        analyzer = AdvancedTradingAnalysis()
=======
>>>>>>> 9a31cdaa90ac59c5c2dba51e90814207bf0d73a6
        opportunities = []
        
        for symbol in request.symbols:
            try:
                # Analyse avancée pour chaque symbole
<<<<<<< HEAD
                analysis_result = await analyzer.analyze_opportunity(
                    symbol=symbol,
                    time_horizon=request.time_horizon,
                    include_ml=True
=======
                analysis_result = await advanced_analyzer.analyze_symbol(
                    symbol=symbol,
                    time_horizon=request.time_horizon,
                    analysis_types=request.analysis_types,
                    db=db
                )
                
                # Calculer le score hybride
                hybrid_score = hybrid_scorer.calculate_hybrid_score(
                    ml_score=analysis_result.get('ml_score', 0.5),
                    technical_score=analysis_result.get('technical_score', 0.5),
                    sentiment_score=analysis_result.get('sentiment_score', 0.5),
                    market_score=analysis_result.get('market_score', 0.5),
                    weights=request.weights
>>>>>>> 9a31cdaa90ac59c5c2dba51e90814207bf0d73a6
                )
                
                opportunity = {
                    "symbol": symbol,
<<<<<<< HEAD
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
=======
                    "hybrid_score": hybrid_score,
                    "confidence": analysis_result.get('confidence', 0.5),
                    "recommendation": analysis_result.get('recommendation', 'HOLD'),
                    "risk_level": analysis_result.get('risk_level', 'MEDIUM'),
                    "technical_score": analysis_result.get('technical_score', 0.5),
                    "sentiment_score": analysis_result.get('sentiment_score', 0.5),
                    "market_score": analysis_result.get('market_score', 0.5),
                    "ml_score": analysis_result.get('ml_score', 0.5),
                    "analysis_details": analysis_result
>>>>>>> 9a31cdaa90ac59c5c2dba51e90814207bf0d73a6
                }
                
                opportunities.append(opportunity)
                
            except Exception as e:
                logger.error(f"Error analyzing {symbol}: {str(e)}")
<<<<<<< HEAD
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
=======
>>>>>>> 9a31cdaa90ac59c5c2dba51e90814207bf0d73a6
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

<<<<<<< HEAD
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
=======
@router.post("/hybrid-score")
async def calculate_hybrid_score(
    request: HybridAnalysisRequest,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Calcule le score hybride combinant ML et analyse conventionnelle
    
    Args:
        request: Requête contenant les analyses ML et conventionnelle
        
    Returns:
        Dict contenant le score hybride
    """
    try:
        logger.info(f"Calculating hybrid score for {request.symbol}")
        
        # Calculer le score hybride
        hybrid_score = hybrid_scorer.calculate_hybrid_score(
            ml_analysis=request.ml_analysis,
            conventional_analysis=request.conventional_analysis
        )
        
        return {
            "success": True,
            "symbol": hybrid_score.symbol,
            "analysis_date": hybrid_score.analysis_date.isoformat(),
            "hybrid_score": hybrid_score.hybrid_score,
            "confidence": hybrid_score.confidence,
            "convergence_factor": hybrid_score.convergence_factor,
            "recommendation": hybrid_score.recommendation,
            "score_breakdown": {
                "ml_score": hybrid_score.ml_score,
                "conventional_score": hybrid_score.conventional_score
            },
            "scoring_weights": hybrid_scorer.get_scoring_weights()
        }
        
    except Exception as e:
        logger.error(f"Error calculating hybrid score: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul du score hybride: {str(e)}"
        )

@router.post("/composite-score")
async def calculate_composite_score(
    analyses: Dict[str, Dict[str, Any]],
    custom_weights: Optional[Dict[str, float]] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Calcule le score composite unifié
    
    Args:
        analyses: Dictionnaire des analyses par type
        custom_weights: Poids personnalisés (optionnel)
        
    Returns:
        Dict contenant le score composite
    """
    try:
        logger.info("Calculating composite score")
        
        # Convertir les analyses en format attendu
        analysis_types = {}
        for analysis_name, analysis_data in analyses.items():
            try:
                analysis_type = AnalysisType(analysis_name)
                analysis_types[analysis_type] = analysis_data
            except ValueError:
                logger.warning(f"Unknown analysis type: {analysis_name}")
                continue
        
        # Convertir les poids personnalisés
        custom_weights_converted = None
        if custom_weights:
            custom_weights_converted = {}
            for weight_name, weight_value in custom_weights.items():
                try:
                    analysis_type = AnalysisType(weight_name)
                    custom_weights_converted[analysis_type] = weight_value
                except ValueError:
                    logger.warning(f"Unknown analysis type in weights: {weight_name}")
                    continue
        
        # Calculer le score composite
        composite_score = composite_scorer.calculate_composite_score(
            analyses=analysis_types,
            custom_weights=custom_weights_converted
        )
        
        return {
            "success": True,
            "symbol": composite_score.symbol,
            "analysis_date": composite_score.analysis_date.isoformat(),
            "overall_score": composite_score.overall_score,
            "confidence_level": composite_score.confidence_level,
            "risk_level": composite_score.risk_level.value,
            "recommendation": composite_score.recommendation,
            "score_breakdown": composite_score.score_breakdown,
            "analysis_quality": composite_score.analysis_quality,
            "convergence_metrics": composite_score.convergence_metrics
        }
        
    except Exception as e:
        logger.error(f"Error calculating composite score: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul du score composite: {str(e)}"
        )

@router.get("/analysis/{symbol}/summary")
async def get_analysis_summary(
    symbol: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère un résumé de la dernière analyse pour un symbole
    
    Args:
        symbol: Symbole à analyser
        
    Returns:
        Dict contenant le résumé de l'analyse
    """
    try:
        logger.info(f"Getting analysis summary for {symbol}")
        
        # Effectuer une analyse rapide
        result = await advanced_analyzer.analyze_opportunity(
            symbol=symbol,
            time_horizon=30,
            include_ml=True
        )
        
        # Retourner le résumé
        summary = advanced_analyzer.get_analysis_summary(result)
        
        return {
            "success": True,
            "summary": summary
        }
        
    except Exception as e:
        logger.error(f"Error getting analysis summary for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du résumé: {str(e)}"
        )

@router.get("/scoring/configuration")
async def get_scoring_configuration() -> Dict[str, Any]:
    """
    Récupère la configuration actuelle du scoring
    
    Returns:
        Dict contenant la configuration du scoring
    """
    try:
        return {
            "success": True,
            "hybrid_scoring": hybrid_scorer.get_scoring_weights(),
            "composite_scoring": composite_scorer.get_scoring_configuration()
        }
        
    except Exception as e:
        logger.error(f"Error getting scoring configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de la configuration: {str(e)}"
        )

@router.post("/scoring/configuration")
async def update_scoring_configuration(
    config: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Met à jour la configuration du scoring
    
    Args:
        config: Nouvelle configuration du scoring
        
    Returns:
        Dict confirmant la mise à jour
    """
    try:
        logger.info("Updating scoring configuration")
        
        success = True
        
        # Mettre à jour la configuration du scoring hybride
        if 'hybrid_scoring' in config:
            hybrid_config = config['hybrid_scoring']
            if 'ml_weight' in hybrid_config and 'conventional_weight' in hybrid_config:
                success &= hybrid_scorer.update_scoring_weights(
                    ml_weight=hybrid_config['ml_weight'],
                    conventional_weight=hybrid_config['conventional_weight']
                )
        
        # Mettre à jour la configuration du scoring composite
        if 'composite_scoring' in config:
            composite_config = config['composite_scoring']
            success &= composite_scorer.update_scoring_configuration(composite_config)
        
        if success:
            return {
                "success": True,
                "message": "Configuration mise à jour avec succès"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erreur lors de la mise à jour de la configuration"
            )
        
    except Exception as e:
        logger.error(f"Error updating scoring configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour de la configuration: {str(e)}"
        )

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Vérification de l'état des services d'analyse avancée
    
    Returns:
        Dict contenant l'état des services
    """
    try:
        return {
            "success": True,
            "status": "healthy",
            "services": {
                "advanced_analyzer": "active",
                "hybrid_scorer": "active",
                "composite_scorer": "active"
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
>>>>>>> 9a31cdaa90ac59c5c2dba51e90814207bf0d73a6
