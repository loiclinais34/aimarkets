"""
Endpoints API pour les ratios financiers
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.database import FinancialRatios, SymbolMetadata
from app.tasks.financial_ratios_tasks import (
    update_financial_ratios_task,
    update_financial_ratios_for_symbols_task,
    update_financial_ratios_incremental_task
)
from app.core.celery_app import celery_app

router = APIRouter()

@router.get("/financial-ratios/{symbol}")
async def get_financial_ratios(symbol: str, db: Session = Depends(get_db)):
    """
    Récupère les ratios financiers pour un symbole spécifique
    """
    try:
        ratios = db.query(FinancialRatios).filter(
            FinancialRatios.symbol == symbol.upper()
        ).first()
        
        if not ratios:
            raise HTTPException(status_code=404, detail=f"Ratios financiers non trouvés pour {symbol}")
        
        return {
            "success": True,
            "data": {
                "symbol": ratios.symbol,
                "name": ratios.name,
                "sector": ratios.sector,
                "industry": ratios.industry,
                "pe_ratio": float(ratios.pe_ratio) if ratios.pe_ratio else None,
                "peg_ratio": float(ratios.peg_ratio) if ratios.peg_ratio else None,
                "price_to_book_ratio": float(ratios.price_to_book_ratio) if ratios.price_to_book_ratio else None,
                "price_to_sales_ratio_ttm": float(ratios.price_to_sales_ratio_ttm) if ratios.price_to_sales_ratio_ttm else None,
                "return_on_equity_ttm": float(ratios.return_on_equity_ttm) if ratios.return_on_equity_ttm else None,
                "return_on_assets_ttm": float(ratios.return_on_assets_ttm) if ratios.return_on_assets_ttm else None,
                "profit_margin": float(ratios.profit_margin) if ratios.profit_margin else None,
                "operating_margin_ttm": float(ratios.operating_margin_ttm) if ratios.operating_margin_ttm else None,
                "beta": float(ratios.beta) if ratios.beta else None,
                "market_capitalization": float(ratios.market_capitalization) if ratios.market_capitalization else None,
                "dividend_yield": float(ratios.dividend_yield) if ratios.dividend_yield else None,
                "dividend_per_share": float(ratios.dividend_per_share) if ratios.dividend_per_share else None,
                "eps": float(ratios.eps) if ratios.eps else None,
                "book_value": float(ratios.book_value) if ratios.book_value else None,
                "fifty_two_week_high": float(ratios.fifty_two_week_high) if ratios.fifty_two_week_high else None,
                "fifty_two_week_low": float(ratios.fifty_two_week_low) if ratios.fifty_two_week_low else None,
                "last_updated": ratios.last_updated.isoformat() if ratios.last_updated else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des ratios: {str(e)}")

@router.get("/financial-ratios")
async def get_all_financial_ratios(
    limit: int = 100,
    offset: int = 0,
    sector: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Récupère tous les ratios financiers avec filtres optionnels
    """
    try:
        query = db.query(FinancialRatios)
        
        if sector:
            query = query.filter(FinancialRatios.sector == sector.upper())
        
        total_count = query.count()
        ratios = query.offset(offset).limit(limit).all()
        
        return {
            "success": True,
            "data": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "ratios": [
                    {
                        "symbol": ratio.symbol,
                        "name": ratio.name,
                        "sector": ratio.sector,
                        "pe_ratio": float(ratio.pe_ratio) if ratio.pe_ratio else None,
                        "price_to_book_ratio": float(ratio.price_to_book_ratio) if ratio.price_to_book_ratio else None,
                        "return_on_equity_ttm": float(ratio.return_on_equity_ttm) if ratio.return_on_equity_ttm else None,
                        "beta": float(ratio.beta) if ratio.beta else None,
                        "market_capitalization": float(ratio.market_capitalization) if ratio.market_capitalization else None,
                        "last_updated": ratio.last_updated.isoformat() if ratio.last_updated else None
                    }
                    for ratio in ratios
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des ratios: {str(e)}")

@router.post("/financial-ratios/update")
async def update_financial_ratios(
    symbols: Optional[List[str]] = None,
    batch_size: int = 25,
    delay_minutes: int = 0,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Lance la mise à jour des ratios financiers pour tous les symboles ou une liste spécifique
    """
    try:
        # Lancer la tâche en arrière-plan
        result = update_financial_ratios_task.delay(
            symbols=symbols,
            batch_size=batch_size,
            delay_minutes=delay_minutes
        )
        
        return {
            "success": True,
            "message": "Mise à jour des ratios financiers lancée",
            "task_id": result.id,
            "parameters": {
                "symbols": symbols,
                "batch_size": batch_size,
                "delay_minutes": delay_minutes
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du lancement de la mise à jour: {str(e)}")

@router.post("/financial-ratios/update-incremental")
async def update_financial_ratios_incremental(
    days_since_update: int = 30,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Lance la mise à jour incrémentale des ratios financiers
    """
    try:
        # Lancer la tâche en arrière-plan
        result = update_financial_ratios_incremental_task.delay(
            days_since_update=days_since_update
        )
        
        return {
            "success": True,
            "message": "Mise à jour incrémentale des ratios financiers lancée",
            "task_id": result.id,
            "parameters": {
                "days_since_update": days_since_update
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du lancement de la mise à jour incrémentale: {str(e)}")

@router.get("/financial-ratios/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Récupère le statut d'une tâche de mise à jour des ratios financiers
    """
    try:
        result = celery_app.AsyncResult(task_id)
        
        if result.state == 'PENDING':
            return {
                "success": True,
                "data": {
                    "task_id": task_id,
                    "state": result.state,
                    "status": "En attente"
                }
            }
        elif result.state == 'PROGRESS':
            return {
                "success": True,
                "data": {
                    "task_id": task_id,
                    "state": result.state,
                    "status": "En cours",
                    "progress": result.info.get('progress', 0),
                    "current_status": result.info.get('status', ''),
                    "current_symbol": result.info.get('current_symbol', ''),
                    "successful_updates": result.info.get('successful_updates', 0),
                    "failed_updates": result.info.get('failed_updates', 0)
                }
            }
        elif result.state == 'SUCCESS':
            return {
                "success": True,
                "data": {
                    "task_id": task_id,
                    "state": result.state,
                    "status": "Terminé avec succès",
                    "result": result.result
                }
            }
        else:  # FAILURE
            return {
                "success": True,
                "data": {
                    "task_id": task_id,
                    "state": result.state,
                    "status": "Échec",
                    "error": result.info.get('error', 'Erreur inconnue')
                }
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du statut: {str(e)}")

@router.get("/financial-ratios/stats")
async def get_financial_ratios_stats(db: Session = Depends(get_db)):
    """
    Récupère les statistiques des ratios financiers
    """
    try:
        # Statistiques générales
        total_ratios = db.query(FinancialRatios).count()
        total_symbols = db.query(SymbolMetadata).count()
        
        # Statistiques par secteur
        sector_stats = db.query(
            FinancialRatios.sector,
            db.func.count(FinancialRatios.symbol).label('count')
        ).group_by(FinancialRatios.sector).all()
        
        # Dernières mises à jour
        recent_updates = db.query(FinancialRatios).order_by(
            FinancialRatios.last_updated.desc()
        ).limit(5).all()
        
        return {
            "success": True,
            "data": {
                "total_ratios": total_ratios,
                "total_symbols": total_symbols,
                "coverage_percentage": round((total_ratios / total_symbols * 100), 2) if total_symbols > 0 else 0,
                "sector_distribution": [
                    {"sector": stat.sector, "count": stat.count}
                    for stat in sector_stats
                ],
                "recent_updates": [
                    {
                        "symbol": ratio.symbol,
                        "name": ratio.name,
                        "last_updated": ratio.last_updated.isoformat() if ratio.last_updated else None
                    }
                    for ratio in recent_updates
                ]
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des statistiques: {str(e)}")
