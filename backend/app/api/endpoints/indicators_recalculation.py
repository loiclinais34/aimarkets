"""
Endpoints API pour le recalcul des indicateurs
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import date

from ...core.database import get_db
from ...services.indicators_recalculation_service import IndicatorsRecalculationService

router = APIRouter()

@router.post("/indicators/recalculate-technical/{symbol}", response_model=Dict[str, Any])
def recalculate_technical_indicators(
    symbol: str,
    start_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Recalcule les indicateurs techniques pour un symbole spécifique
    
    Args:
        symbol: Symbole à traiter
        start_date: Date de début pour le recalcul (format YYYY-MM-DD)
    
    Returns:
        Résultat du recalcul des indicateurs techniques
    """
    try:
        indicators_service = IndicatorsRecalculationService(db)
        
        # Convertir la date de début si fournie
        start_date_obj = None
        if start_date:
            try:
                start_date_obj = date.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Format de date invalide. Utilisez YYYY-MM-DD"
                )
        
        result = indicators_service.recalculate_technical_indicators(symbol, start_date_obj)
        
        if result['success']:
            return {
                "status": "success",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['error']
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du recalcul des indicateurs techniques: {str(e)}"
        )

@router.post("/indicators/recalculate-sentiment/{symbol}", response_model=Dict[str, Any])
def recalculate_sentiment_indicators(
    symbol: str,
    start_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Recalcule les indicateurs de sentiment pour un symbole spécifique
    
    Args:
        symbol: Symbole à traiter
        start_date: Date de début pour le recalcul (format YYYY-MM-DD)
    
    Returns:
        Résultat du recalcul des indicateurs de sentiment
    """
    try:
        indicators_service = IndicatorsRecalculationService(db)
        
        # Convertir la date de début si fournie
        start_date_obj = None
        if start_date:
            try:
                start_date_obj = date.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Format de date invalide. Utilisez YYYY-MM-DD"
                )
        
        result = indicators_service.recalculate_sentiment_indicators(symbol, start_date_obj)
        
        if result['success']:
            return {
                "status": "success",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['error']
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du recalcul des indicateurs de sentiment: {str(e)}"
        )

@router.post("/indicators/recalculate-correlations", response_model=Dict[str, Any])
def recalculate_correlations(
    symbols: List[str],
    start_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Recalcule les corrélations pour une liste de symboles
    
    Args:
        symbols: Liste des symboles à traiter
        start_date: Date de début pour le recalcul (format YYYY-MM-DD)
    
    Returns:
        Résultat du recalcul des corrélations
    """
    try:
        if not symbols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La liste des symboles ne peut pas être vide"
            )
        
        indicators_service = IndicatorsRecalculationService(db)
        
        # Convertir la date de début si fournie
        start_date_obj = None
        if start_date:
            try:
                start_date_obj = date.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Format de date invalide. Utilisez YYYY-MM-DD"
                )
        
        result = indicators_service.recalculate_correlations(symbols, start_date_obj)
        
        if result['success']:
            return {
                "status": "success",
                "data": result
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result['error']
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du recalcul des corrélations: {str(e)}"
        )

@router.post("/indicators/recalculate-all", response_model=Dict[str, Any])
def recalculate_all_indicators(
    symbols: List[str],
    start_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Recalcule tous les indicateurs (techniques, sentiment, corrélations) pour une liste de symboles
    
    Args:
        symbols: Liste des symboles à traiter
        start_date: Date de début pour le recalcul (format YYYY-MM-DD)
    
    Returns:
        Résultat complet du recalcul de tous les indicateurs
    """
    try:
        if not symbols:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La liste des symboles ne peut pas être vide"
            )
        
        indicators_service = IndicatorsRecalculationService(db)
        
        # Convertir la date de début si fournie
        start_date_obj = None
        if start_date:
            try:
                start_date_obj = date.fromisoformat(start_date)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Format de date invalide. Utilisez YYYY-MM-DD"
                )
        
        result = indicators_service.recalculate_all_indicators(symbols, start_date_obj)
        
        return {
            "status": "success" if result['success'] else "partial_success",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du recalcul complet des indicateurs: {str(e)}"
        )

@router.get("/indicators/status/{symbol}", response_model=Dict[str, Any])
def get_indicators_status(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Récupère le statut des indicateurs pour un symbole
    
    Args:
        symbol: Symbole à vérifier
    
    Returns:
        Statut des indicateurs pour le symbole
    """
    try:
        from ...models.database import TechnicalIndicators, SentimentIndicators
        
        # Vérifier les indicateurs techniques
        technical_count = db.query(TechnicalIndicators).filter(
            TechnicalIndicators.symbol == symbol
        ).count()
        
        latest_technical = db.query(TechnicalIndicators).filter(
            TechnicalIndicators.symbol == symbol
        ).order_by(TechnicalIndicators.date.desc()).first()
        
        # Vérifier les indicateurs de sentiment
        sentiment_count = db.query(SentimentIndicators).filter(
            SentimentIndicators.symbol == symbol
        ).count()
        
        latest_sentiment = db.query(SentimentIndicators).filter(
            SentimentIndicators.symbol == symbol
        ).order_by(SentimentIndicators.date.desc()).first()
        
        return {
            "status": "success",
            "data": {
                "symbol": symbol,
                "technical_indicators": {
                    "count": technical_count,
                    "latest_date": latest_technical.date.isoformat() if latest_technical else None,
                    "has_data": technical_count > 0
                },
                "sentiment_indicators": {
                    "count": sentiment_count,
                    "latest_date": latest_sentiment.date.isoformat() if latest_sentiment else None,
                    "has_data": sentiment_count > 0
                },
                "overall_status": "complete" if (technical_count > 0 and sentiment_count > 0) else "incomplete"
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du statut des indicateurs: {str(e)}"
        )
