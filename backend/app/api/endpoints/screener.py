from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import asyncio

from ...core.database import get_db
from ...models.schemas import (
    ScreenerRequest, ScreenerResponse, ScreenerRun, ScreenerResult,
    ScreenerConfig, ScreenerConfigCreate, ScreenerConfigUpdate
)
from ...services.screener_service import ScreenerService
from ...services.celery_manager import CeleryManager
from ...tasks.screener_tasks import get_task_status

router = APIRouter()

def ensure_celery_ready():
    """
    S'assure que Celery est prêt avant de lancer une tâche
    """
    celery_manager = CeleryManager()
    result = celery_manager.ensure_celery_running()
    
    if not result['success']:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Celery n'est pas disponible: {result['error']}"
        )
    
    return result

@router.post("/run", response_model=ScreenerResponse)
async def run_screener(
    request: ScreenerRequest,
    db: Session = Depends(get_db)
):
    """
    Exécute un screener complet avec les paramètres fournis.
    
    Le processus inclut:
    1. Création d'une configuration de screener
    2. Entraînement des modèles pour tous les symboles disponibles
    3. Calcul des prédictions pour tous les modèles
    4. Filtrage des opportunités selon le seuil de confiance
    5. Retour des résultats triés par confiance
    """
    try:
        # Validation des paramètres
        if request.target_return_percentage <= 0 or request.target_return_percentage > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le rendement attendu doit être entre 0.1% et 100%"
            )
        
        if request.time_horizon_days <= 0 or request.time_horizon_days > 365:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'horizon temporel doit être entre 1 et 365 jours"
            )
        
        if request.risk_tolerance < 0.1 or request.risk_tolerance > 1.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La tolérance au risque doit être entre 0.1 et 1.0"
            )
        
        # Exécuter le screener
        screener_service = ScreenerService(db=db)
        result = await screener_service.run_screener(request)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'exécution du screener: {str(e)}"
        )

@router.post("/run-demo", response_model=Dict[str, Any])
def run_demo_screener_endpoint(
    request: ScreenerRequest,
    db: Session = Depends(get_db)
):
    """Lancer un screener de démonstration de manière asynchrone"""
    try:
        # Vérifier et démarrer Celery si nécessaire
        celery_result = ensure_celery_ready()
        
        from app.tasks.demo_screener_tasks import run_demo_screener
        
        # Conversion de la requête en dictionnaire pour la tâche
        request_dict = {
            "target_return_percentage": request.target_return_percentage,
            "time_horizon_days": request.time_horizon_days,
            "risk_tolerance": request.risk_tolerance
        }
        
        # Lancement de la tâche asynchrone de démonstration
        task = run_demo_screener.delay(request_dict, "demo_user")
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Screener de démonstration lancé en arrière-plan",
            "celery_status": celery_result['status']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement du screener de démonstration: {str(e)}"
        )


@router.post("/run-real", response_model=Dict[str, Any])
def run_real_screener_endpoint(
    request: ScreenerRequest,
    db: Session = Depends(get_db)
):
    """Lancer un screener réel de manière asynchrone"""
    try:
        # Vérifier et démarrer Celery si nécessaire
        celery_result = ensure_celery_ready()
        
        from app.tasks.real_screener_tasks import run_real_screener
        
        # Conversion de la requête en dictionnaire pour la tâche
        request_dict = {
            "target_return_percentage": request.target_return_percentage,
            "time_horizon_days": request.time_horizon_days,
            "risk_tolerance": request.risk_tolerance
        }
        
        # Lancement de la tâche asynchrone réelle
        task = run_real_screener.delay(request_dict, "screener_user")
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Screener réel lancé en arrière-plan",
            "celery_status": celery_result['status']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement du screener réel: {str(e)}"
        )

@router.post("/run-real-limited", response_model=Dict[str, Any])
def run_real_screener_limited_endpoint(
    request: ScreenerRequest,
    max_symbols: int = 20,
    db: Session = Depends(get_db)
):
    """Lancer un screener réel limité de manière asynchrone"""
    try:
        from app.tasks.real_screener_limited_tasks import run_real_screener_limited
        
        # Conversion de la requête en dictionnaire pour la tâche
        request_dict = {
            "target_return_percentage": request.target_return_percentage,
            "time_horizon_days": request.time_horizon_days,
            "risk_tolerance": request.risk_tolerance
        }
        
        # Lancement de la tâche asynchrone réelle limitée
        task = run_real_screener_limited.delay(request_dict, "screener_user", max_symbols)
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": f"Screener réel limité ({max_symbols} symboles) lancé en arrière-plan"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement du screener réel limité: {str(e)}"
        )

@router.post("/run-real-fixed", response_model=Dict[str, Any])
def run_real_screener_fixed_endpoint(
    request: ScreenerRequest,
    max_symbols: int = 20,
    db: Session = Depends(get_db)
):
    """Lancer un screener réel corrigé de manière asynchrone"""
    try:
        from app.tasks.real_screener_fixed_tasks import run_real_screener_limited_fixed
        
        # Conversion de la requête en dictionnaire pour la tâche
        request_dict = {
            "target_return_percentage": request.target_return_percentage,
            "time_horizon_days": request.time_horizon_days,
            "risk_tolerance": request.risk_tolerance
        }
        
        # Lancement de la tâche asynchrone réelle corrigée
        task = run_real_screener_limited_fixed.delay(request_dict, "screener_user", max_symbols)
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": f"Screener réel corrigé ({max_symbols} symboles) lancé en arrière-plan"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement du screener réel corrigé: {str(e)}"
        )

@router.post("/run-ultra-simple-real", response_model=Dict[str, Any])
def run_ultra_simple_real_screener_endpoint(
    request: ScreenerRequest,
    max_symbols: int = 5,
    db: Session = Depends(get_db)
):
    """Lancer un screener ultra-simple réel de manière asynchrone"""
    try:
        from app.tasks.ultra_simple_real_tasks import run_ultra_simple_real_screener
        
        # Conversion de la requête en dictionnaire pour la tâche
        request_dict = {
            "target_return_percentage": request.target_return_percentage,
            "time_horizon_days": request.time_horizon_days,
            "risk_tolerance": request.risk_tolerance
        }
        
        # Lancement de la tâche asynchrone ultra-simple réelle
        task = run_ultra_simple_real_screener.delay(request_dict, "screener_user", max_symbols)
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": f"Screener ultra-simple réel ({max_symbols} symboles) lancé en arrière-plan"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement du screener ultra-simple réel: {str(e)}"
        )

@router.get("/latest-opportunities", response_model=List[Dict[str, Any]])
def get_latest_opportunities(db: Session = Depends(get_db)):
    """Récupérer les dernières opportunités (prediction_value=1) du screener le plus récent"""
    try:
        from app.models.database import MLPredictions, MLModels, SymbolMetadata, ScreenerRun
        
        # Trouver le screener_run_id le plus récent
        latest_screener_run = db.query(ScreenerRun).order_by(ScreenerRun.created_at.desc()).first()
        
        if not latest_screener_run:
            return []
        
        # Récupérer les prédictions avec prediction_value=1 pour ce screener_run_id
        predictions = db.query(MLPredictions).join(MLModels).join(SymbolMetadata, SymbolMetadata.symbol == MLPredictions.symbol).filter(
            MLPredictions.screener_run_id == latest_screener_run.id,
            MLPredictions.prediction_value == 1.0
        ).order_by(MLPredictions.confidence.desc()).all()
        
        results = []
        for pred in predictions:
            # Récupérer les métadonnées du symbole
            symbol_metadata = db.query(SymbolMetadata).filter(SymbolMetadata.symbol == pred.symbol).first()
            
            # Récupérer les informations du modèle
            model = db.query(MLModels).filter(MLModels.id == pred.model_id).first()
            
            results.append({
                "symbol": pred.symbol,
                "company_name": symbol_metadata.company_name if symbol_metadata else pred.symbol,
                "prediction": float(pred.prediction_value),
                "confidence": float(pred.confidence),
                "model_id": pred.model_id,
                "model_name": model.model_name if model else "Unknown",
                "target_return": float(model.target_parameter.target_return_percentage) if model and model.target_parameter else None,
                "time_horizon": model.target_parameter.time_horizon_days if model and model.target_parameter else None,
                "prediction_date": pred.prediction_date.isoformat() if pred.prediction_date else None,
                "screener_run_id": pred.screener_run_id,
                "rank": len(results) + 1
            })
        
        return results
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des dernières opportunités: {str(e)}"
        )


@router.post("/run-full-ml-web", response_model=Dict[str, Any])
def run_full_screener_ml_web_endpoint(
    request: ScreenerRequest,
    max_symbols: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Lancer un screener ML complet avec service web robuste"""
    try:
        # Vérifier et démarrer Celery si nécessaire
        celery_result = ensure_celery_ready()
        
        from app.tasks.full_screener_ml_web_tasks import run_full_screener_ml_web
        
        # Conversion de la requête en dictionnaire pour la tâche
        request_dict = {
            "target_return_percentage": request.target_return_percentage,
            "time_horizon_days": request.time_horizon_days,
            "risk_tolerance": request.risk_tolerance
        }
        
        # Lancement de la tâche asynchrone ML web
        task = run_full_screener_ml_web.delay(request_dict, "screener_user", max_symbols)
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": f"Screener ML complet lancé en arrière-plan{' (limité à ' + str(max_symbols) + ' symboles)' if max_symbols else ''}",
            "celery_status": celery_result['status']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement du screener ML complet: {str(e)}"
        )

@router.post("/run-full-ml-limited", response_model=Dict[str, Any])
def run_full_screener_ml_limited_endpoint(
    request: ScreenerRequest,
    max_symbols: int = 5,
    db: Session = Depends(get_db)
):
    """Lancer un screener ML limité de manière asynchrone"""
    try:
        from app.tasks.full_screener_ml_limited_tasks import run_full_screener_ml_limited
        
        # Conversion de la requête en dictionnaire pour la tâche
        request_dict = {
            "target_return_percentage": request.target_return_percentage,
            "time_horizon_days": request.time_horizon_days,
            "risk_tolerance": request.risk_tolerance
        }
        
        # Lancement de la tâche asynchrone ML limitée
        task = run_full_screener_ml_limited.delay(request_dict, "screener_user", max_symbols)
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": f"Screener ML limité ({max_symbols} symboles) lancé en arrière-plan"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement du screener ML limité: {str(e)}"
        )

@router.post("/run-full-ml", response_model=Dict[str, Any])
def run_full_screener_ml_endpoint(
    request: ScreenerRequest,
    db: Session = Depends(get_db)
):
    """Lancer un screener complet avec vrais modèles ML de manière asynchrone"""
    try:
        from app.tasks.full_screener_ml_tasks import run_full_screener_ml
        
        # Conversion de la requête en dictionnaire pour la tâche
        request_dict = {
            "target_return_percentage": request.target_return_percentage,
            "time_horizon_days": request.time_horizon_days,
            "risk_tolerance": request.risk_tolerance
        }
        
        # Lancement de la tâche asynchrone complète ML
        task = run_full_screener_ml.delay(request_dict, "screener_user")
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Screener complet ML lancé en arrière-plan (tous les symboles avec vrais modèles)"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement du screener complet ML: {str(e)}"
        )

@router.post("/run-full-simple", response_model=Dict[str, Any])
def run_full_screener_simple_endpoint(
    request: ScreenerRequest,
    db: Session = Depends(get_db)
):
    """Lancer un screener complet simple de manière asynchrone"""
    try:
        from app.tasks.full_screener_simple_tasks import run_full_screener_simple
        
        # Conversion de la requête en dictionnaire pour la tâche
        request_dict = {
            "target_return_percentage": request.target_return_percentage,
            "time_horizon_days": request.time_horizon_days,
            "risk_tolerance": request.risk_tolerance
        }
        
        # Lancement de la tâche asynchrone complète simple
        task = run_full_screener_simple.delay(request_dict, "screener_user")
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Screener complet simple lancé en arrière-plan (tous les symboles)"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement du screener complet simple: {str(e)}"
        )

@router.post("/run-full-limited", response_model=Dict[str, Any])
def run_full_screener_limited_endpoint(
    request: ScreenerRequest,
    max_symbols: int = 20,
    db: Session = Depends(get_db)
):
    """Lancer un screener complet limité de manière asynchrone"""
    try:
        from app.tasks.full_screener_limited_tasks import run_full_screener_limited
        
        # Conversion de la requête en dictionnaire pour la tâche
        request_dict = {
            "target_return_percentage": request.target_return_percentage,
            "time_horizon_days": request.time_horizon_days,
            "risk_tolerance": request.risk_tolerance
        }
        
        # Lancement de la tâche asynchrone complète limitée
        task = run_full_screener_limited.delay(request_dict, "screener_user", max_symbols)
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": f"Screener complet limité ({max_symbols} symboles) lancé en arrière-plan"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement du screener complet limité: {str(e)}"
        )

@router.post("/run-full", response_model=Dict[str, Any])
def run_full_screener_endpoint(
    request: ScreenerRequest,
    db: Session = Depends(get_db)
):
    """Lancer un screener complet avec tous les symboles de manière asynchrone"""
    try:
        from app.tasks.full_screener_tasks import run_full_screener
        
        # Conversion de la requête en dictionnaire pour la tâche
        request_dict = {
            "target_return_percentage": request.target_return_percentage,
            "time_horizon_days": request.time_horizon_days,
            "risk_tolerance": request.risk_tolerance
        }
        
        # Lancement de la tâche asynchrone complète
        task = run_full_screener.delay(request_dict, "screener_user")
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Screener complet lancé en arrière-plan (tous les symboles)"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement du screener complet: {str(e)}"
        )






@router.post("/test-task", response_model=Dict[str, Any])
def test_simple_task():
    """Tester une tâche simple"""
    try:
        from app.tasks.test_tasks import test_simple_task
        
        task = test_simple_task.delay()
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Tâche de test lancée"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du lancement de la tâche de test: {str(e)}"
        )

@router.get("/task/{task_id}/status", response_model=Dict[str, Any])
def get_screener_task_status(task_id: str):
    """Récupérer le statut d'une tâche de screener"""
    try:
        from celery.result import AsyncResult
        from app.core.celery_app import celery_app
        
        task = AsyncResult(task_id, app=celery_app)
        
        # Gestion spéciale pour les erreurs Celery
        try:
            task_state = task.state
        except ValueError as e:
            if "Exception information must include the exception type" in str(e):
                return {
                    "state": "FAILURE",
                    "status": "Erreur lors de l'exécution de la tâche",
                    "progress": 0,
                    "error": "Tâche échouée avec des informations d'exception incomplètes"
                }
            else:
                raise e
        
        if task_state == "PENDING":
            return {
                "state": task_state,
                "status": "En attente...",
                "progress": 0
            }
        elif task_state == "PROGRESS":
            return {
                "state": task_state,
                "status": task.info.get("status", "En cours..."),
                "progress": task.info.get("progress", 0),
                "meta": task.info
            }
        elif task_state == "SUCCESS":
            return {
                "state": task_state,
                "status": "Terminé avec succès!",
                "progress": 100,
                "result": task.result
            }
        else:  # FAILURE
            error_info = task.info
            if isinstance(error_info, dict) and 'exc_type' in error_info:
                error_message = f"{error_info.get('exc_type', 'Unknown')}: {error_info.get('exc_message', str(error_info))}"
            else:
                error_message = str(error_info) if error_info else "Erreur inconnue"
            
            return {
                "state": task_state,
                "status": f"Erreur: {error_message}",
                "progress": 0
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du statut: {str(e)}"
        )

@router.get("/history", response_model=List[ScreenerRun])
def get_screener_history(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Récupère l'historique des exécutions de screener"""
    try:
        screener_service = ScreenerService(db=db)
        history = screener_service.get_screener_history(limit=limit)
        return history
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
        )

@router.get("/results/{screener_run_id}", response_model=List[ScreenerResult])
def get_screener_results(
    screener_run_id: int,
    db: Session = Depends(get_db)
):
    """Récupère les résultats d'une exécution de screener spécifique"""
    try:
        screener_service = ScreenerService(db=db)
        results = screener_service.get_screener_results(screener_run_id)
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucun résultat trouvé pour cette exécution de screener"
            )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des résultats: {str(e)}"
        )

@router.get("/configs", response_model=List[ScreenerConfig])
def get_screener_configs(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Récupère les configurations de screener"""
    try:
        from ...models.database import ScreenerConfig as ScreenerConfigDB
        
        query = db.query(ScreenerConfigDB)
        
        if active_only:
            query = query.filter(ScreenerConfigDB.is_active == True)
        
        configs = query.order_by(ScreenerConfigDB.created_at.desc()).all()
        return configs
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des configurations: {str(e)}"
        )

@router.post("/configs", response_model=ScreenerConfig)
def create_screener_config(
    config: ScreenerConfigCreate,
    db: Session = Depends(get_db)
):
    """Crée une nouvelle configuration de screener"""
    try:
        from ...models.database import ScreenerConfig as ScreenerConfigDB
        
        # Vérifier si une configuration similaire existe déjà
        existing_config = db.query(ScreenerConfigDB).filter(
            ScreenerConfigDB.name == config.name
        ).first()
        
        if existing_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Une configuration avec ce nom existe déjà"
            )
        
        # Créer la nouvelle configuration
        new_config = ScreenerConfigDB(
            name=config.name,
            target_return_percentage=config.target_return_percentage,
            time_horizon_days=config.time_horizon_days,
            risk_tolerance=config.risk_tolerance,
            confidence_threshold=config.confidence_threshold,
            created_by=config.created_by
        )
        
        db.add(new_config)
        db.commit()
        db.refresh(new_config)
        
        return new_config
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la configuration: {str(e)}"
        )

@router.get("/stats")
def get_screener_stats(db: Session = Depends(get_db)):
    """Récupère les statistiques des screeners"""
    try:
        from ...models.database import ScreenerRun, ScreenerResult
        
        # Statistiques générales
        total_runs = db.query(ScreenerRun).count()
        completed_runs = db.query(ScreenerRun).filter(ScreenerRun.status == "completed").count()
        failed_runs = db.query(ScreenerRun).filter(ScreenerRun.status == "failed").count()
        
        # Statistiques des opportunités
        total_opportunities = db.query(ScreenerResult).count()
        
        # Dernière exécution
        last_run = db.query(ScreenerRun).order_by(ScreenerRun.created_at.desc()).first()
        
        stats = {
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "success_rate": (completed_runs / total_runs * 100) if total_runs > 0 else 0,
            "total_opportunities_found": total_opportunities,
            "last_run": {
                "id": last_run.id if last_run else None,
                "date": last_run.run_date if last_run else None,
                "opportunities": last_run.opportunities_found if last_run else 0,
                "status": last_run.status if last_run else None
            }
        }
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )
