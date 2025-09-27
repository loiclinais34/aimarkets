"""
API endpoints pour la pipeline d'analyse avancée
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from app.core.database import get_db
from app.services.data_freshness_service import DataFreshnessService
from app.models.pipeline_schemas import PipelineStartRequest, IndicatorsCalculationRequest, OpportunitiesAnalysisRequest
from app.tasks.advanced_analysis_pipeline_tasks import (
    advanced_analysis_pipeline,
    check_data_freshness_task,
    calculate_all_indicators_task,
    analyze_advanced_opportunities_task
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/advanced-analysis", tags=["Advanced Analysis Pipeline"])

@router.get("/data-freshness")
async def get_data_freshness(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Vérifie la fraîcheur de toutes les données
    
    Returns:
        Dict contenant le résumé de la fraîcheur des données
    """
    try:
        freshness_service = DataFreshnessService(db)
        summary = freshness_service.get_data_freshness_summary()
        
        return {
            "success": True,
            "data": summary,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error checking data freshness: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la vérification de la fraîcheur des données: {str(e)}"
        )

@router.post("/pipeline/start")
async def start_analysis_pipeline(
    request: PipelineStartRequest,
    background_tasks: BackgroundTasks = None
) -> Dict[str, Any]:
    """
    Démarre la pipeline d'analyse avancée complète
    
    Args:
        force_update: Forcer la mise à jour même si les données sont récentes
        symbols: Liste spécifique de symboles à analyser (None = tous)
    
    Returns:
        Dict contenant l'ID de la tâche et le statut
    """
    try:
        logger.info(f"Starting advanced analysis pipeline - Force update: {request.force_update}")
        
        # Démarrer la tâche en arrière-plan
        task = advanced_analysis_pipeline.delay(force_update=request.force_update, symbols=request.symbols)
        
        return {
            "success": True,
            "task_id": task.id,
            "status": "started",
            "message": "Pipeline d'analyse avancée démarrée",
            "force_update": request.force_update,
            "symbols": request.symbols,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting analysis pipeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du démarrage de la pipeline: {str(e)}"
        )

@router.post("/pipeline/indicators")
async def start_indicators_calculation(
    request: IndicatorsCalculationRequest
) -> Dict[str, Any]:
    """
    Démarre le calcul des indicateurs pour les symboles donnés
    
    Args:
        symbols: Liste des symboles à traiter
        force_update: Forcer le recalcul même si les données existent
    
    Returns:
        Dict contenant l'ID de la tâche et le statut
    """
    try:
        logger.info(f"Starting indicators calculation for {len(request.symbols)} symbols")
        
        task = calculate_all_indicators_task.delay(request.symbols, request.force_update)
        
        return {
            "success": True,
            "task_id": task.id,
            "status": "started",
            "message": "Calcul des indicateurs démarré",
            "symbols": request.symbols,
            "force_update": request.force_update,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting indicators calculation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du démarrage du calcul des indicateurs: {str(e)}"
        )

@router.post("/pipeline/opportunities")
async def start_opportunities_analysis(
    request: OpportunitiesAnalysisRequest
) -> Dict[str, Any]:
    """
    Démarre l'analyse des opportunités avancées pour les symboles donnés
    
    Args:
        symbols: Liste des symboles à analyser
    
    Returns:
        Dict contenant l'ID de la tâche et le statut
    """
    try:
        logger.info(f"Starting opportunities analysis for {len(request.symbols)} symbols")
        
        task = analyze_advanced_opportunities_task.delay(request.symbols)
        
        return {
            "success": True,
            "task_id": task.id,
            "status": "started",
            "message": "Analyse des opportunités démarrée",
            "symbols": request.symbols,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting opportunities analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du démarrage de l'analyse des opportunités: {str(e)}"
        )

@router.get("/pipeline/status/{task_id}")
async def get_pipeline_status(task_id: str) -> Dict[str, Any]:
    """
    Obtient le statut d'une tâche de pipeline
    
    Args:
        task_id: ID de la tâche
    
    Returns:
        Dict contenant le statut de la tâche
    """
    try:
        from celery.result import AsyncResult
        
        result = AsyncResult(task_id)
        
        if result.state == 'PENDING':
            status_info = {
                "task_id": task_id,
                "status": "pending",
                "message": "Tâche en attente"
            }
        elif result.state == 'PROGRESS':
            status_info = {
                "task_id": task_id,
                "status": "progress",
                "message": "Tâche en cours",
                "progress": result.info.get('progress', 0) if result.info else 0
            }
        elif result.state == 'SUCCESS':
            status_info = {
                "task_id": task_id,
                "status": "success",
                "message": "Tâche terminée avec succès",
                "result": result.result
            }
        elif result.state == 'FAILURE':
            status_info = {
                "task_id": task_id,
                "status": "failure",
                "message": "Tâche échouée",
                "error": str(result.info)
            }
        else:
            status_info = {
                "task_id": task_id,
                "status": result.state,
                "message": f"Statut: {result.state}"
            }
        
        return {
            "success": True,
            "data": status_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting pipeline status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du statut: {str(e)}"
        )

@router.get("/pipeline/symbols-needing-update")
async def get_symbols_needing_update(
    data_type: str = "all",
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Obtient la liste des symboles qui ont besoin d'être mis à jour
    
    Args:
        data_type: Type de données à vérifier ("historical", "sentiment", "technical", "all")
        db: Session de base de données
    
    Returns:
        Dict contenant la liste des symboles nécessitant une mise à jour
    """
    try:
        freshness_service = DataFreshnessService(db)
        symbols = freshness_service.get_symbols_needing_update(data_type)
        
        return {
            "success": True,
            "data": {
                "symbols": symbols,
                "count": len(symbols),
                "data_type": data_type
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting symbols needing update: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des symboles: {str(e)}"
        )
