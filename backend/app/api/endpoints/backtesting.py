"""
API Endpoints pour le Backtesting
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from pydantic import BaseModel, Field

from ...core.database import get_db
from ...models.database import BacktestRun, MLModels
from ...services.backtesting_service import BacktestingService

router = APIRouter()


# ==================== PYDANTIC MODELS ====================

class BacktestRunCreate(BaseModel):
    name: str = Field(..., description="Nom du backtest")
    description: Optional[str] = Field(None, description="Description du backtest")
    model_id: int = Field(..., description="ID du modèle ML à tester")
    strategy_id: Optional[int] = Field(None, description="ID de la stratégie de trading")
    start_date: date = Field(..., description="Date de début du backtesting")
    end_date: date = Field(..., description="Date de fin du backtesting")
    initial_capital: float = Field(100000.0, description="Capital initial")
    position_size_percentage: float = Field(10.0, description="Pourcentage du capital par position")
    commission_rate: float = Field(0.001, description="Taux de commission")
    slippage_rate: float = Field(0.0005, description="Taux de slippage")
    confidence_threshold: float = Field(0.60, description="Seuil de confiance minimum")
    max_positions: int = Field(10, description="Nombre maximum de positions simultanées")
    created_by: str = Field("user", description="Utilisateur créateur")


class BacktestRunResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    model_id: int
    model_name: Optional[str]
    start_date: date
    end_date: date
    initial_capital: float
    position_size_percentage: float
    commission_rate: float
    slippage_rate: float
    confidence_threshold: float
    max_positions: int
    status: str
    created_by: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]


class BacktestMetricsResponse(BaseModel):
    total_return: float
    annualized_return: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    max_drawdown: float
    max_drawdown_duration: int
    volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    avg_return_per_trade: float
    avg_winning_trade: float
    avg_losing_trade: float
    profit_factor: float
    avg_holding_period: float
    final_capital: float
    max_capital: float
    min_capital: float
    calmar_ratio: float
    recovery_factor: float
    expectancy: float


class BacktestTradeResponse(BaseModel):
    id: int
    symbol: str
    entry_date: date
    exit_date: date
    entry_price: float
    exit_price: float
    quantity: int
    position_type: str
    entry_confidence: float
    exit_reason: str
    gross_pnl: float
    commission: float
    slippage: float
    net_pnl: float
    return_percentage: float
    holding_days: int


class BacktestEquityPointResponse(BaseModel):
    date: date
    equity_value: float
    drawdown: float
    daily_return: float
    cumulative_return: float


class BacktestResultsResponse(BaseModel):
    backtest_run: BacktestRunResponse
    metrics: Optional[BacktestMetricsResponse]
    trades: List[BacktestTradeResponse]
    equity_curve: List[BacktestEquityPointResponse]


class MessageResponse(BaseModel):
    message: str
    success: bool = True


# ==================== API ENDPOINTS ====================

@router.post("/create", response_model=Dict[str, Any])
def create_backtest_run(
    backtest_data: BacktestRunCreate,
    db: Session = Depends(get_db)
):
    """Créer une nouvelle exécution de backtesting"""
    try:
        backtesting_service = BacktestingService(db)
        
        result = backtesting_service.create_backtest_run(
            name=backtest_data.name,
            description=backtest_data.description,
            model_id=backtest_data.model_id,
            strategy_id=backtest_data.strategy_id,
            start_date=backtest_data.start_date,
            end_date=backtest_data.end_date,
            initial_capital=backtest_data.initial_capital,
            position_size_percentage=backtest_data.position_size_percentage,
            commission_rate=backtest_data.commission_rate,
            slippage_rate=backtest_data.slippage_rate,
            confidence_threshold=backtest_data.confidence_threshold,
            max_positions=backtest_data.max_positions,
            created_by=backtest_data.created_by
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du backtest: {str(e)}"
        )


@router.post("/run/{backtest_run_id}", response_model=Dict[str, Any])
def run_backtest(
    backtest_run_id: int,
    db: Session = Depends(get_db)
):
    """Exécuter un backtesting"""
    try:
        backtesting_service = BacktestingService(db)
        
        result = backtesting_service.run_backtest(backtest_run_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result["error"]
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'exécution du backtesting: {str(e)}"
        )


@router.get("/runs", response_model=List[BacktestRunResponse])
def get_backtest_runs(
    skip: int = 0,
    limit: int = 100,
    model_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Récupérer la liste des exécutions de backtesting"""
    try:
        query = db.query(BacktestRun)
        
        # Filtres optionnels
        if model_id:
            query = query.filter(BacktestRun.model_id == model_id)
        if status:
            query = query.filter(BacktestRun.status == status)
        
        # Pagination et tri
        backtest_runs = query.order_by(BacktestRun.created_at.desc()).offset(skip).limit(limit).all()
        
        # Récupérer les noms des modèles
        model_ids = [run.model_id for run in backtest_runs]
        models = db.query(MLModels).filter(MLModels.id.in_(model_ids)).all()
        model_names = {model.id: model.model_name for model in models}
        
        return [
            BacktestRunResponse(
                id=run.id,
                name=run.name,
                description=run.description,
                model_id=run.model_id,
                model_name=model_names.get(run.model_id),
                start_date=run.start_date,
                end_date=run.end_date,
                initial_capital=float(run.initial_capital),
                position_size_percentage=float(run.position_size_percentage),
                commission_rate=float(run.commission_rate),
                slippage_rate=float(run.slippage_rate),
                confidence_threshold=float(run.confidence_threshold),
                max_positions=run.max_positions,
                status=run.status,
                created_by=run.created_by,
                created_at=run.created_at,
                started_at=run.started_at,
                completed_at=run.completed_at,
                error_message=run.error_message
            )
            for run in backtest_runs
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des backtests: {str(e)}"
        )


@router.get("/runs/{backtest_run_id}", response_model=BacktestRunResponse)
def get_backtest_run(
    backtest_run_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer une exécution de backtesting spécifique"""
    try:
        backtest_run = db.query(BacktestRun).filter(
            BacktestRun.id == backtest_run_id
        ).first()
        
        if not backtest_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest run {backtest_run_id} non trouvé"
            )
        
        # Récupérer le nom du modèle
        model = db.query(MLModels).filter(MLModels.id == backtest_run.model_id).first()
        model_name = model.model_name if model else None
        
        return BacktestRunResponse(
            id=backtest_run.id,
            name=backtest_run.name,
            description=backtest_run.description,
            model_id=backtest_run.model_id,
            model_name=model_name,
            start_date=backtest_run.start_date,
            end_date=backtest_run.end_date,
            initial_capital=float(backtest_run.initial_capital),
            position_size_percentage=float(backtest_run.position_size_percentage),
            commission_rate=float(backtest_run.commission_rate),
            slippage_rate=float(backtest_run.slippage_rate),
            confidence_threshold=float(backtest_run.confidence_threshold),
            max_positions=backtest_run.max_positions,
            status=backtest_run.status,
            created_by=backtest_run.created_by,
            created_at=backtest_run.created_at,
            started_at=backtest_run.started_at,
            completed_at=backtest_run.completed_at,
            error_message=backtest_run.error_message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du backtest: {str(e)}"
        )


@router.get("/results/{backtest_run_id}", response_model=BacktestResultsResponse)
def get_backtest_results(
    backtest_run_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer les résultats complets d'un backtesting"""
    try:
        backtesting_service = BacktestingService(db)
        
        result = backtesting_service.get_backtest_results(backtest_run_id)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result["error"]
            )
        
        # Convertir les données en modèles Pydantic
        backtest_run_data = result["backtest_run"]
        
        # Récupérer le nom du modèle
        model = db.query(MLModels).filter(MLModels.id == backtest_run_data["model_id"]).first()
        model_name = model.model_name if model else None
        
        backtest_run_response = BacktestRunResponse(
            id=backtest_run_data["id"],
            name=backtest_run_data["name"],
            description=backtest_run_data["description"],
            model_id=backtest_run_data["model_id"],
            model_name=model_name,
            start_date=date.fromisoformat(backtest_run_data["start_date"]),
            end_date=date.fromisoformat(backtest_run_data["end_date"]),
            initial_capital=backtest_run_data["initial_capital"],
            position_size_percentage=10.0,  # Valeur par défaut
            commission_rate=0.001,  # Valeur par défaut
            slippage_rate=0.0005,  # Valeur par défaut
            confidence_threshold=0.60,  # Valeur par défaut
            max_positions=10,  # Valeur par défaut
            status=backtest_run_data["status"],
            created_by="user",  # Valeur par défaut
            created_at=datetime.fromisoformat(backtest_run_data["created_at"]),
            started_at=datetime.fromisoformat(backtest_run_data["completed_at"]) if backtest_run_data["completed_at"] else None,
            completed_at=datetime.fromisoformat(backtest_run_data["completed_at"]) if backtest_run_data["completed_at"] else None,
            error_message=None
        )
        
        metrics_response = None
        if result["metrics"]:
            metrics_response = BacktestMetricsResponse(**result["metrics"])
        
        trades_response = [BacktestTradeResponse(**trade) for trade in result["trades"]]
        equity_curve_response = [BacktestEquityPointResponse(**point) for point in result["equity_curve"]]
        
        return BacktestResultsResponse(
            backtest_run=backtest_run_response,
            metrics=metrics_response,
            trades=trades_response,
            equity_curve=equity_curve_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des résultats: {str(e)}"
        )


@router.delete("/runs/{backtest_run_id}", response_model=MessageResponse)
def delete_backtest_run(
    backtest_run_id: int,
    db: Session = Depends(get_db)
):
    """Supprimer une exécution de backtesting"""
    try:
        backtest_run = db.query(BacktestRun).filter(
            BacktestRun.id == backtest_run_id
        ).first()
        
        if not backtest_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest run {backtest_run_id} non trouvé"
            )
        
        # Supprimer les données associées (cascade)
        db.delete(backtest_run)
        db.commit()
        
        return MessageResponse(
            message=f"Backtest run {backtest_run_id} supprimé avec succès",
            success=True
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la suppression du backtest: {str(e)}"
        )


@router.get("/symbols", response_model=Dict[str, Any])
def get_available_symbols(db: Session = Depends(get_db)):
    """Récupérer la liste des symboles disponibles pour le backtesting"""
    try:
        from ...models.database import MLPredictions
        
        # Récupérer les symboles qui ont des prédictions > 1
        symbols = db.query(MLPredictions.symbol).filter(
            MLPredictions.prediction_value >= 1.0
        ).distinct().all()
        
        result = []
        for symbol_tuple in symbols:
            symbol = symbol_tuple[0]
            # Compter le nombre total de prédictions pour ce symbole
            prediction_count = db.query(MLPredictions).filter(
                MLPredictions.symbol == symbol,
                MLPredictions.prediction_value >= 1.0
            ).count()
            
            # Compter le nombre de modèles différents pour ce symbole
            model_count = db.query(MLModels).join(MLPredictions).filter(
                MLPredictions.symbol == symbol,
                MLPredictions.prediction_value >= 1.0
            ).distinct().count()
            
            result.append({
                "symbol": symbol,
                "prediction_count": prediction_count,
                "model_count": model_count
            })
        
        # Trier par nombre de prédictions décroissant
        result.sort(key=lambda x: x["prediction_count"], reverse=True)
        
        return {
            "success": True,
            "symbols": result,
            "total": len(result)
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des symboles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des symboles: {str(e)}"
        )


@router.get("/symbols/{symbol}/models", response_model=Dict[str, Any])
def get_models_for_symbol(
    symbol: str,
    limit: int = 50,
    offset: int = 0,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Récupérer les modèles disponibles pour le backtesting d'un symbole donné avec pagination"""
    try:
        from ...models.database import MLPredictions
        
        # Requête optimisée avec une seule jointure et agrégation
        query = db.query(
            MLModels.id,
            MLModels.model_name,
            MLModels.model_type,
            MLModels.model_version,
            MLModels.symbol,
            func.count(MLPredictions.id).label('prediction_count'),
            func.min(MLPredictions.prediction_date).label('min_date'),
            func.max(MLPredictions.prediction_date).label('max_date')
        ).join(MLPredictions).filter(
            MLPredictions.symbol == symbol.upper(),
            MLPredictions.prediction_value >= 1.0
        ).group_by(
            MLModels.id,
            MLModels.model_name,
            MLModels.model_type,
            MLModels.model_version,
            MLModels.symbol
        )
        
        # Filtre de recherche si fourni
        if search:
            query = query.filter(MLModels.model_name.ilike(f"%{search}%"))
        
        # Compter le total avant pagination
        total_count = query.count()
        
        # Appliquer pagination et tri par nombre de prédictions décroissant
        models_data = query.order_by(func.count(MLPredictions.id).desc()).offset(offset).limit(limit).all()
        
        result = []
        for model_data in models_data:
            result.append({
                "id": model_data.id,
                "name": model_data.model_name,
                "type": model_data.model_type,
                "version": model_data.model_version,
                "symbol": model_data.symbol,
                "prediction_count": model_data.prediction_count,
                "date_range": {
                    "start": model_data.min_date.isoformat() if model_data.min_date else None,
                    "end": model_data.max_date.isoformat() if model_data.max_date else None
                }
            })
        
        return {
            "success": True,
            "symbol": symbol.upper(),
            "models": result,
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "has_more": offset + limit < total_count
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des modèles pour {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des modèles: {str(e)}"
        )


@router.get("/models/{model_id}/available-dates", response_model=Dict[str, Any])
def get_available_dates_for_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer les dates disponibles pour le backtesting d'un modèle"""
    try:
        from ...models.database import MLPredictions
        
        # Vérifier que le modèle existe
        model = db.query(MLModels).filter(MLModels.id == model_id).first()
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Modèle {model_id} non trouvé"
            )
        
        # Récupérer les dates des prédictions
        predictions = db.query(MLPredictions).filter(
            MLPredictions.model_id == model_id
        ).order_by(MLPredictions.prediction_date.asc()).all()
        
        if not predictions:
            return {
                "success": True,
                "available_dates": [],
                "message": "Aucune prédiction trouvée pour ce modèle"
            }
        
        dates = [pred.prediction_date for pred in predictions]
        
        return {
            "success": True,
            "available_dates": [date.isoformat() for date in dates],
            "start_date": dates[0].isoformat(),
            "end_date": dates[-1].isoformat(),
            "total_predictions": len(predictions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des dates: {str(e)}"
        )


@router.get("/status/{backtest_run_id}", response_model=Dict[str, Any])
def get_backtest_status(
    backtest_run_id: int,
    db: Session = Depends(get_db)
):
    """Récupérer le statut d'un backtesting"""
    try:
        backtest_run = db.query(BacktestRun).filter(
            BacktestRun.id == backtest_run_id
        ).first()
        
        if not backtest_run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backtest run {backtest_run_id} non trouvé"
            )
        
        return {
            "success": True,
            "backtest_run_id": backtest_run_id,
            "status": backtest_run.status,
            "created_at": backtest_run.created_at.isoformat(),
            "started_at": backtest_run.started_at.isoformat() if backtest_run.started_at else None,
            "completed_at": backtest_run.completed_at.isoformat() if backtest_run.completed_at else None,
            "error_message": backtest_run.error_message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du statut: {str(e)}"
        )
