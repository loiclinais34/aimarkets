from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from ...core.database import get_db
from ...models.database import TradingSignals, CorrelationAlerts
from ...models.schemas import (
    TradingSignal as TradingSignalSchema,
    CorrelationAlert as CorrelationAlertSchema
)

router = APIRouter()


@router.get("/trading", response_model=List[TradingSignalSchema])
async def get_trading_signals(
    symbol: Optional[str] = Query(None, description="Symbole du titre"),
    signal_type: Optional[str] = Query(None, description="Type de signal"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1, description="Confiance minimale"),
    start_date: Optional[date] = Query(None, description="Date de début"),
    end_date: Optional[date] = Query(None, description="Date de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
):
    """Récupérer les signaux de trading"""
    try:
        query = db.query(TradingSignals)
        
        # Filtres
        if symbol:
            query = query.filter(TradingSignals.symbol == symbol.upper())
        if signal_type:
            query = query.filter(TradingSignals.signal_type == signal_type.upper())
        if min_confidence:
            query = query.filter(TradingSignals.confidence >= min_confidence)
        if start_date:
            query = query.filter(TradingSignals.date >= start_date)
        if end_date:
            query = query.filter(TradingSignals.date <= end_date)
        
        query = query.order_by(TradingSignals.date.desc()).limit(limit)
        items = query.all()
        
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des signaux: {str(e)}")


@router.get("/trading/{symbol}", response_model=List[TradingSignalSchema])
async def get_trading_signals_by_symbol(
    symbol: str,
    signal_type: Optional[str] = Query(None, description="Type de signal"),
    min_confidence: Optional[float] = Query(None, ge=0, le=1, description="Confiance minimale"),
    start_date: Optional[date] = Query(None, description="Date de début"),
    end_date: Optional[date] = Query(None, description="Date de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
):
    """Récupérer les signaux de trading pour un symbole spécifique"""
    try:
        query = db.query(TradingSignals).filter(TradingSignals.symbol == symbol.upper())
        
        if signal_type:
            query = query.filter(TradingSignals.signal_type == signal_type.upper())
        if min_confidence:
            query = query.filter(TradingSignals.confidence >= min_confidence)
        if start_date:
            query = query.filter(TradingSignals.date >= start_date)
        if end_date:
            query = query.filter(TradingSignals.date <= end_date)
        
        query = query.order_by(TradingSignals.date.desc()).limit(limit)
        items = query.all()
        
        if not items:
            raise HTTPException(status_code=404, detail=f"Aucun signal de trading trouvé pour le symbole {symbol}")
        
        return items
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des signaux: {str(e)}")


@router.get("/alerts", response_model=List[CorrelationAlertSchema])
async def get_correlation_alerts(
    symbol: Optional[str] = Query(None, description="Symbole du titre"),
    alert_type: Optional[str] = Query(None, description="Type d'alerte"),
    severity: Optional[str] = Query(None, description="Sévérité"),
    is_resolved: Optional[bool] = Query(None, description="Alerte résolue"),
    start_date: Optional[date] = Query(None, description="Date de début"),
    end_date: Optional[date] = Query(None, description="Date de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
):
    """Récupérer les alertes de corrélation"""
    try:
        query = db.query(CorrelationAlerts)
        
        # Filtres
        if symbol:
            query = query.filter(CorrelationAlerts.symbol == symbol.upper())
        if alert_type:
            query = query.filter(CorrelationAlerts.alert_type == alert_type)
        if severity:
            query = query.filter(CorrelationAlerts.severity == severity)
        if is_resolved is not None:
            query = query.filter(CorrelationAlerts.is_resolved == is_resolved)
        if start_date:
            query = query.filter(CorrelationAlerts.date >= start_date)
        if end_date:
            query = query.filter(CorrelationAlerts.date <= end_date)
        
        query = query.order_by(CorrelationAlerts.date.desc()).limit(limit)
        items = query.all()
        
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des alertes: {str(e)}")


@router.post("/generate")
async def generate_trading_signals(
    symbol: str,
    model_id: Optional[int] = Query(None, description="ID du modèle à utiliser"),
    db: Session = Depends(get_db)
):
    """Générer des signaux de trading pour un symbole"""
    try:
        # TODO: Implémenter la génération de signaux
        # Cette fonction sera implémentée dans le service des signaux
        
        return {
            "message": f"Génération de signaux pour {symbol} en cours...",
            "symbol": symbol,
            "model_id": model_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la génération des signaux: {str(e)}")


@router.post("/alerts/resolve/{alert_id}")
async def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """Marquer une alerte comme résolue"""
    try:
        alert = db.query(CorrelationAlerts).filter(CorrelationAlerts.id == alert_id).first()
        
        if not alert:
            raise HTTPException(status_code=404, detail=f"Alerte avec l'ID {alert_id} non trouvée")
        
        alert.is_resolved = True
        db.commit()
        
        return {"message": f"Alerte {alert_id} marquée comme résolue"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la résolution de l'alerte: {str(e)}")


@router.get("/stats")
async def get_signals_stats(db: Session = Depends(get_db)):
    """Récupérer les statistiques des signaux"""
    try:
        total_signals = db.query(TradingSignals).count()
        buy_signals = db.query(TradingSignals).filter(TradingSignals.signal_type == "BUY").count()
        sell_signals = db.query(TradingSignals).filter(TradingSignals.signal_type == "SELL").count()
        hold_signals = db.query(TradingSignals).filter(TradingSignals.signal_type == "HOLD").count()
        
        total_alerts = db.query(CorrelationAlerts).count()
        unresolved_alerts = db.query(CorrelationAlerts).filter(CorrelationAlerts.is_resolved == False).count()
        
        return {
            "trading_signals": {
                "total": total_signals,
                "buy": buy_signals,
                "sell": sell_signals,
                "hold": hold_signals
            },
            "correlation_alerts": {
                "total": total_alerts,
                "unresolved": unresolved_alerts
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des statistiques: {str(e)}")
