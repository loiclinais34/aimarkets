"""
Endpoints API pour le backtesting ML
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
from pydantic import BaseModel
import logging

from app.core.database import get_db
from app.services.ml_backtesting.backtesting_pipeline import BacktestingPipeline
from app.services.ml_backtesting.historical_opportunity_generator import HistoricalOpportunityGenerator
from app.services.ml_backtesting.opportunity_validator import OpportunityValidator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml-backtesting", tags=["ML Backtesting"])


# Modèles Pydantic pour les requêtes
class BacktestRequest(BaseModel):
    start_date: date
    end_date: date
    symbols: Optional[List[str]] = None
    limit_symbols: Optional[int] = None
    validation_periods: List[int] = [1, 7, 30]


class QuickBacktestRequest(BaseModel):
    test_date: date
    symbols: Optional[List[str]] = None
    limit_symbols: int = 10


class GenerateOpportunitiesRequest(BaseModel):
    target_date: date
    symbols: Optional[List[str]] = None
    limit_symbols: Optional[int] = None


class ValidateOpportunitiesRequest(BaseModel):
    opportunity_ids: List[int]
    validation_periods: List[int] = [1, 7, 30]


# Endpoints
@router.post("/run-backtest")
async def run_full_backtest(
    request: BacktestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Exécute un backtest complet sur une plage de dates
    """
    try:
        logger.info(f"Démarrage du backtest du {request.start_date} au {request.end_date}")
        
        # Vérifier que les dates sont valides
        if request.start_date >= request.end_date:
            raise HTTPException(
                status_code=400,
                detail="La date de début doit être antérieure à la date de fin"
            )
        
        # Vérifier que la plage de dates n'est pas trop large
        date_range = (request.end_date - request.start_date).days
        if date_range > 365:
            raise HTTPException(
                status_code=400,
                detail="La plage de dates ne peut pas dépasser 365 jours"
            )
        
        # Créer le pipeline de backtesting
        pipeline = BacktestingPipeline(db)
        
        # Exécuter le backtest
        results = await pipeline.run_full_backtest(
            start_date=request.start_date,
            end_date=request.end_date,
            symbols=request.symbols,
            limit_symbols=request.limit_symbols,
            validation_periods=request.validation_periods
        )
        
        return {
            "status": "success",
            "message": "Backtest terminé avec succès",
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du backtest: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du backtest: {str(e)}"
        )


@router.post("/quick-backtest")
async def run_quick_backtest(
    request: QuickBacktestRequest,
    db: Session = Depends(get_db)
):
    """
    Exécute un backtest rapide sur une date donnée
    """
    try:
        logger.info(f"Backtest rapide pour la date {request.test_date}")
        
        # Vérifier que la date n'est pas dans le futur
        if request.test_date > date.today():
            raise HTTPException(
                status_code=400,
                detail="La date de test ne peut pas être dans le futur"
            )
        
        # Créer le pipeline de backtesting
        pipeline = BacktestingPipeline(db)
        
        # Exécuter le backtest rapide
        results = await pipeline.run_quick_backtest(
            test_date=request.test_date,
            symbols=request.symbols,
            limit_symbols=request.limit_symbols
        )
        
        return results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du backtest rapide: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors du backtest rapide: {str(e)}"
        )


@router.post("/generate-opportunities")
async def generate_historical_opportunities(
    request: GenerateOpportunitiesRequest,
    db: Session = Depends(get_db)
):
    """
    Génère des opportunités historiques pour une date donnée
    """
    try:
        logger.info(f"Génération d'opportunités pour la date {request.target_date}")
        
        # Vérifier que la date n'est pas dans le futur
        if request.target_date > date.today():
            raise HTTPException(
                status_code=400,
                detail="La date cible ne peut pas être dans le futur"
            )
        
        # Créer le générateur d'opportunités
        generator = HistoricalOpportunityGenerator(db)
        
        # Générer les opportunités
        opportunities = await generator.generate_opportunities_for_date(
            target_date=request.target_date,
            symbols=request.symbols,
            limit_symbols=request.limit_symbols
        )
        
        return {
            "status": "success",
            "message": f"{len(opportunities)} opportunités générées",
            "opportunities_count": len(opportunities),
            "target_date": request.target_date.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la génération d'opportunités: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la génération d'opportunités: {str(e)}"
        )


@router.post("/validate-opportunities")
async def validate_opportunities(
    request: ValidateOpportunitiesRequest,
    db: Session = Depends(get_db)
):
    """
    Valide les performances d'opportunités historiques
    """
    try:
        logger.info(f"Validation de {len(request.opportunity_ids)} opportunités")
        
        # Récupérer les opportunités depuis la base de données
        from app.models.historical_opportunities import HistoricalOpportunities
        
        opportunities = db.query(HistoricalOpportunities).filter(
            HistoricalOpportunities.id.in_(request.opportunity_ids)
        ).all()
        
        if not opportunities:
            raise HTTPException(
                status_code=404,
                detail="Aucune opportunité trouvée avec les IDs fournis"
            )
        
        # Créer le validateur
        validator = OpportunityValidator(db)
        
        # Valider les opportunités
        results = await validator.validate_opportunities_batch(
            opportunities=opportunities,
            validation_periods=request.validation_periods
        )
        
        return {
            "status": "success",
            "message": f"{len(results)} opportunités validées",
            "validation_results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la validation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la validation: {str(e)}"
        )


@router.get("/opportunities/{symbol}")
async def get_historical_opportunities(
    symbol: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Récupère les opportunités historiques pour un symbole
    """
    try:
        from app.models.historical_opportunities import HistoricalOpportunities
        
        # Construire la requête
        query = db.query(HistoricalOpportunities).filter(
            HistoricalOpportunities.symbol == symbol
        )
        
        # Appliquer les filtres de date
        if start_date:
            query = query.filter(HistoricalOpportunities.opportunity_date >= start_date)
        
        if end_date:
            query = query.filter(HistoricalOpportunities.opportunity_date <= end_date)
        
        # Ordonner par date et limiter
        opportunities = query.order_by(
            HistoricalOpportunities.opportunity_date.desc()
        ).limit(limit).all()
        
        # Convertir en format JSON
        opportunities_data = []
        for opp in opportunities:
            opportunities_data.append({
                "id": opp.id,
                "symbol": opp.symbol,
                "opportunity_date": opp.opportunity_date.isoformat(),
                "generation_timestamp": opp.generation_timestamp.isoformat(),
                "technical_score": float(opp.technical_score) if opp.technical_score else None,
                "sentiment_score": float(opp.sentiment_score) if opp.sentiment_score else None,
                "market_score": float(opp.market_score) if opp.market_score else None,
                "composite_score": float(opp.composite_score) if opp.composite_score else None,
                "recommendation": opp.recommendation,
                "confidence_level": opp.confidence_level,
                "risk_level": opp.risk_level,
                "price_at_generation": float(opp.price_at_generation) if opp.price_at_generation else None,
                "return_1_day": float(opp.return_1_day) if opp.return_1_day else None,
                "return_7_days": float(opp.return_7_days) if opp.return_7_days else None,
                "return_30_days": float(opp.return_30_days) if opp.return_30_days else None,
                "performance_score": float(opp.performance_score) if opp.performance_score else None,
                "created_at": opp.created_at.isoformat(),
                "updated_at": opp.updated_at.isoformat()
            })
        
        return {
            "status": "success",
            "symbol": symbol,
            "opportunities_count": len(opportunities_data),
            "opportunities": opportunities_data
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des opportunités: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des opportunités: {str(e)}"
        )


@router.get("/validation-results/{opportunity_id}")
async def get_validation_results(
    opportunity_id: int,
    db: Session = Depends(get_db)
):
    """
    Récupère les résultats de validation pour une opportunité
    """
    try:
        from app.models.historical_opportunities import HistoricalOpportunityValidation
        
        # Récupérer les résultats de validation
        validation_results = db.query(HistoricalOpportunityValidation).filter(
            HistoricalOpportunityValidation.historical_opportunity_id == opportunity_id
        ).all()
        
        if not validation_results:
            raise HTTPException(
                status_code=404,
                detail="Aucun résultat de validation trouvé pour cette opportunité"
            )
        
        # Convertir en format JSON
        results_data = []
        for result in validation_results:
            results_data.append({
                "id": result.id,
                "validation_period_days": result.validation_period_days,
                "validation_date": result.validation_date.isoformat(),
                "actual_return": float(result.actual_return) if result.actual_return else None,
                "predicted_return": float(result.predicted_return) if result.predicted_return else None,
                "prediction_error": float(result.prediction_error) if result.prediction_error else None,
                "sharpe_ratio": float(result.sharpe_ratio) if result.sharpe_ratio else None,
                "max_drawdown": float(result.max_drawdown) if result.max_drawdown else None,
                "volatility": float(result.volatility) if result.volatility else None,
                "performance_category": result.performance_category,
                "market_return": float(result.market_return) if result.market_return else None,
                "beta": float(result.beta) if result.beta else None,
                "created_at": result.created_at.isoformat(),
                "updated_at": result.updated_at.isoformat()
            })
        
        return {
            "status": "success",
            "opportunity_id": opportunity_id,
            "validation_results_count": len(results_data),
            "validation_results": results_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des résultats de validation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des résultats de validation: {str(e)}"
        )


@router.get("/stats")
async def get_backtesting_stats(
    db: Session = Depends(get_db)
):
    """
    Récupère les statistiques générales du backtesting
    """
    try:
        from app.models.historical_opportunities import HistoricalOpportunities, HistoricalOpportunityValidation
        
        # Statistiques des opportunités
        total_opportunities = db.query(HistoricalOpportunities).count()
        
        from sqlalchemy import func
        
        # Statistiques par symbole
        symbol_stats = db.query(
            HistoricalOpportunities.symbol,
            func.count(HistoricalOpportunities.id).label('count')
        ).group_by(HistoricalOpportunities.symbol).all()
        
        # Statistiques par date
        date_stats = db.query(
            HistoricalOpportunities.opportunity_date,
            func.count(HistoricalOpportunities.id).label('count')
        ).group_by(HistoricalOpportunities.opportunity_date).order_by(
            HistoricalOpportunities.opportunity_date.desc()
        ).limit(10).all()
        
        # Statistiques des validations
        total_validations = db.query(HistoricalOpportunityValidation).count()
        
        # Statistiques par période de validation
        period_stats = db.query(
            HistoricalOpportunityValidation.validation_period_days,
            func.count(HistoricalOpportunityValidation.id).label('count')
        ).group_by(HistoricalOpportunityValidation.validation_period_days).all()
        
        return {
            "status": "success",
            "stats": {
                "total_opportunities": total_opportunities,
                "total_validations": total_validations,
                "symbols_count": len(symbol_stats),
                "top_symbols": [
                    {"symbol": stat.symbol, "count": stat.count}
                    for stat in symbol_stats[:10]
                ],
                "recent_dates": [
                    {"date": stat.opportunity_date.isoformat(), "count": stat.count}
                    for stat in date_stats
                ],
                "validation_periods": [
                    {"period_days": stat.validation_period_days, "count": stat.count}
                    for stat in period_stats
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des statistiques: {str(e)}"
        )
