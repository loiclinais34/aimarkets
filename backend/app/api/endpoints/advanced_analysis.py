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

from ...core.database import get_db
from ...models.advanced_analysis_schemas import AnalysisRequest, AnalysisResponse, HybridAnalysisRequest
from ...services.advanced_analysis import AdvancedTradingAnalysis, HybridScoringSystem, CompositeScoringEngine
from ...services.advanced_analysis.composite_scoring import AnalysisType, RiskLevel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advanced-analysis", tags=["Advanced Analysis"])

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
