from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from ...core.database import get_db
from ...models.database import TechnicalIndicators
from ...models.schemas import TechnicalIndicators as TechnicalIndicatorsSchema

router = APIRouter()


@router.get("/technical", response_model=List[TechnicalIndicatorsSchema])
async def get_technical_indicators(
    symbol: Optional[str] = Query(None, description="Symbole du titre"),
    start_date: Optional[date] = Query(None, description="Date de début"),
    end_date: Optional[date] = Query(None, description="Date de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
):
    """Récupérer les indicateurs techniques"""
    try:
        query = db.query(TechnicalIndicators)
        
        # Filtres
        if symbol:
            query = query.filter(TechnicalIndicators.symbol == symbol.upper())
        if start_date:
            query = query.filter(TechnicalIndicators.date >= start_date)
        if end_date:
            query = query.filter(TechnicalIndicators.date <= end_date)
        
        query = query.order_by(TechnicalIndicators.date.desc()).limit(limit)
        items = query.all()
        
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des indicateurs: {str(e)}")


@router.get("/technical/{symbol}", response_model=List[TechnicalIndicatorsSchema])
async def get_technical_indicators_by_symbol(
    symbol: str,
    start_date: Optional[date] = Query(None, description="Date de début"),
    end_date: Optional[date] = Query(None, description="Date de fin"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
):
    """Récupérer les indicateurs techniques pour un symbole spécifique"""
    try:
        query = db.query(TechnicalIndicators).filter(TechnicalIndicators.symbol == symbol.upper())
        
        if start_date:
            query = query.filter(TechnicalIndicators.date >= start_date)
        if end_date:
            query = query.filter(TechnicalIndicators.date <= end_date)
        
        query = query.order_by(TechnicalIndicators.date.desc()).limit(limit)
        items = query.all()
        
        if not items:
            raise HTTPException(status_code=404, detail=f"Aucun indicateur technique trouvé pour le symbole {symbol}")
        
        return items
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des indicateurs: {str(e)}")


@router.post("/technical/calculate")
async def calculate_technical_indicators(
    symbol: str,
    start_date: Optional[date] = Query(None, description="Date de début"),
    end_date: Optional[date] = Query(None, description="Date de fin"),
    db: Session = Depends(get_db)
):
    """Calculer les indicateurs techniques pour un symbole"""
    try:
        # TODO: Implémenter le calcul des indicateurs techniques
        # Cette fonction sera implémentée dans le service des indicateurs techniques
        
        return {
            "message": f"Calcul des indicateurs techniques pour {symbol} en cours...",
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors du calcul des indicateurs: {str(e)}")


@router.get("/technical/stats")
async def get_technical_indicators_stats(db: Session = Depends(get_db)):
    """Récupérer les statistiques des indicateurs techniques"""
    try:
        total_indicators = db.query(TechnicalIndicators).count()
        unique_symbols = db.query(TechnicalIndicators.symbol).distinct().count()
        unique_dates = db.query(TechnicalIndicators.date).distinct().count()
        
        return {
            "total_indicators": total_indicators,
            "unique_symbols": unique_symbols,
            "unique_dates": unique_dates
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des statistiques: {str(e)}")
