from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
from datetime import date, datetime

from app.core.database import get_db
from app.models.database import HistoricalData, TechnicalIndicators, SentimentIndicators, SymbolMetadata
from app.models.schemas import (
    HistoricalDataSchema,
    TechnicalIndicatorsSchema,
    SentimentIndicatorsSchema,
    StatisticsResponse, MessageResponse
)

router = APIRouter(prefix="/data", tags=["data"])


# === ENDPOINTS POUR LES DONNÉES HISTORIQUES ===

@router.get("/historical/{symbol}", response_model=List[HistoricalDataSchema])
def get_historical_data(
    symbol: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Récupérer les données historiques pour un symbole"""
    try:
        query = db.query(HistoricalData).filter(HistoricalData.symbol == symbol.upper())
        
        if start_date:
            query = query.filter(HistoricalData.date >= start_date)
        
        if end_date:
            query = query.filter(HistoricalData.date <= end_date)
        
        data = query.order_by(HistoricalData.date.desc()).offset(skip).limit(limit).all()
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune donnée historique trouvée pour le symbole {symbol}"
            )
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des données historiques: {str(e)}"
        )


@router.get("/historical/{symbol}/latest", response_model=HistoricalDataSchema)
def get_latest_historical_data(
    symbol: str,
    db: Session = Depends(get_db)
):
    """Récupérer la dernière donnée historique pour un symbole"""
    try:
        data = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol.upper()
        ).order_by(HistoricalData.date.desc()).first()
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune donnée historique trouvée pour le symbole {symbol}"
            )
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de la dernière donnée: {str(e)}"
        )


# === ENDPOINTS POUR LES INDICATEURS TECHNIQUES ===

@router.get("/technical/{symbol}", response_model=List[TechnicalIndicatorsSchema])
def get_technical_indicators(
    symbol: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Récupérer les indicateurs techniques pour un symbole"""
    try:
        query = db.query(TechnicalIndicators).filter(TechnicalIndicators.symbol == symbol.upper())
        
        if start_date:
            query = query.filter(TechnicalIndicators.date >= start_date)
        
        if end_date:
            query = query.filter(TechnicalIndicators.date <= end_date)
        
        data = query.order_by(TechnicalIndicators.date.desc()).offset(skip).limit(limit).all()
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun indicateur technique trouvé pour le symbole {symbol}"
            )
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des indicateurs techniques: {str(e)}"
        )


@router.get("/technical/{symbol}/latest", response_model=TechnicalIndicatorsSchema)
def get_latest_technical_indicators(
    symbol: str,
    db: Session = Depends(get_db)
):
    """Récupérer les derniers indicateurs techniques pour un symbole"""
    try:
        data = db.query(TechnicalIndicators).filter(
            TechnicalIndicators.symbol == symbol.upper()
        ).order_by(TechnicalIndicators.date.desc()).first()
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun indicateur technique trouvé pour le symbole {symbol}"
            )
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des derniers indicateurs: {str(e)}"
        )


# === ENDPOINTS POUR LES INDICATEURS DE SENTIMENT ===

@router.get("/sentiment/{symbol}", response_model=List[SentimentIndicatorsSchema])
def get_sentiment_indicators(
    symbol: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Récupérer les indicateurs de sentiment pour un symbole"""
    try:
        query = db.query(SentimentIndicators).filter(SentimentIndicators.symbol == symbol.upper())
        
        if start_date:
            query = query.filter(SentimentIndicators.date >= start_date)
        
        if end_date:
            query = query.filter(SentimentIndicators.date <= end_date)
        
        data = query.order_by(SentimentIndicators.date.desc()).offset(skip).limit(limit).all()
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun indicateur de sentiment trouvé pour le symbole {symbol}"
            )
        
        # Filtrer les données avec des valeurs NaN et les convertir en None
        filtered_data = []
        for item in data:
            # Créer un dictionnaire des attributs
            item_dict = {}
            for column in item.__table__.columns:
                value = getattr(item, column.name)
                # Convertir les valeurs NaN en None pour la sérialisation JSON
                if value is not None and str(value).lower() == 'nan':
                    value = None
                item_dict[column.name] = value
            filtered_data.append(item_dict)
        
        return filtered_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des indicateurs de sentiment: {str(e)}"
        )


@router.get("/sentiment/{symbol}/latest", response_model=SentimentIndicatorsSchema)
def get_latest_sentiment_indicators(
    symbol: str,
    db: Session = Depends(get_db)
):
    """Récupérer les derniers indicateurs de sentiment pour un symbole"""
    try:
        data = db.query(SentimentIndicators).filter(
            SentimentIndicators.symbol == symbol.upper()
        ).order_by(SentimentIndicators.date.desc()).first()
        
        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun indicateur de sentiment trouvé pour le symbole {symbol}"
            )
        
        # Convertir les valeurs NaN en None pour la sérialisation JSON
        item_dict = {}
        for column in data.__table__.columns:
            value = getattr(data, column.name)
            if value is not None and str(value).lower() == 'nan':
                value = None
            item_dict[column.name] = value
        
        return item_dict
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des derniers indicateurs de sentiment: {str(e)}"
        )


# === ENDPOINTS POUR LES DONNÉES COMBINÉES ===

@router.get("/combined/{symbol}")
def get_combined_data(
    symbol: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(100, ge=1, le=1000),
    skip: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Récupérer les données historiques, techniques et de sentiment combinées"""
    try:
        # Requête SQL pour joindre toutes les tables
        query = text("""
            SELECT 
                h.date,
                h.symbol,
                h.open,
                h.high,
                h.low,
                h.close,
                h.volume,
                h.vwap,
                t.sma_5, t.sma_20, t.rsi_14, t.macd, t.bb_position, t.atr_14,
                s.sentiment_score_normalized, s.sentiment_momentum_7d, s.sentiment_volatility_14d
            FROM historical_data h
            LEFT JOIN technical_indicators t ON h.symbol = t.symbol AND h.date = t.date
            LEFT JOIN sentiment_indicators s ON h.symbol = s.symbol AND h.date = s.date
            WHERE h.symbol = :symbol
        """)
        
        params = {"symbol": symbol.upper()}
        
        if start_date:
            query = text(str(query) + " AND h.date >= :start_date")
            params["start_date"] = start_date
        
        if end_date:
            query = text(str(query) + " AND h.date <= :end_date")
            params["end_date"] = end_date
        
        query = text(str(query) + " ORDER BY h.date DESC LIMIT :limit OFFSET :skip")
        params["limit"] = limit
        params["skip"] = skip
        
        result = db.execute(query, params)
        rows = result.fetchall()
        
        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune donnée combinée trouvée pour le symbole {symbol}"
            )
        
        # Convertir les résultats en dictionnaires
        data = []
        for row in rows:
            data.append({
                "date": row.date,
                "symbol": row.symbol,
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
                "vwap": row.vwap,
                "technical": {
                    "sma_5": row.sma_5,
                    "sma_20": row.sma_20,
                    "rsi_14": row.rsi_14,
                    "macd": row.macd,
                    "bb_position": row.bb_position,
                    "atr_14": row.atr_14
                },
                "sentiment": {
                    "sentiment_score_normalized": row.sentiment_score_normalized,
                    "sentiment_momentum_7d": row.sentiment_momentum_7d,
                    "sentiment_volatility_14d": row.sentiment_volatility_14d
                }
            })
        
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des données combinées: {str(e)}"
        )


# === ENDPOINTS POUR LES SYMBOLES ===

@router.get("/symbols", response_model=List[dict])
def get_available_symbols(
    db: Session = Depends(get_db)
):
    """Récupérer la liste des symboles disponibles avec leurs métadonnées"""
    try:
        # Récupérer les symboles avec leurs métadonnées
        symbols_with_metadata = db.query(
            HistoricalData.symbol,
            SymbolMetadata.company_name,
            SymbolMetadata.sector
        ).join(
            SymbolMetadata, HistoricalData.symbol == SymbolMetadata.symbol
        ).distinct().order_by(HistoricalData.symbol.asc()).all()
        
        # Si pas de métadonnées, récupérer juste les symboles
        if not symbols_with_metadata:
            symbols = db.query(HistoricalData.symbol).distinct().order_by(HistoricalData.symbol.asc()).all()
            return [{"symbol": symbol[0], "company_name": symbol[0], "sector": "Unknown"} for symbol in symbols]
        
        return [
            {
                "symbol": symbol[0],
                "company_name": symbol[1] or symbol[0],
                "sector": symbol[2] or "Unknown"
            }
            for symbol in symbols_with_metadata
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des symboles: {str(e)}"
        )


@router.get("/symbols/{symbol}/info")
def get_symbol_info(
    symbol: str,
    db: Session = Depends(get_db)
):
    """Récupérer les informations sur un symbole"""
    try:
        # Données historiques
        historical_count = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol.upper()
        ).count()
        
        if historical_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Symbole {symbol} non trouvé"
            )
        
        # Dates min et max
        min_date = db.query(HistoricalData.date).filter(
            HistoricalData.symbol == symbol.upper()
        ).order_by(HistoricalData.date.asc()).first()
        
        max_date = db.query(HistoricalData.date).filter(
            HistoricalData.symbol == symbol.upper()
        ).order_by(HistoricalData.date.desc()).first()
        
        # Indicateurs techniques
        technical_count = db.query(TechnicalIndicators).filter(
            TechnicalIndicators.symbol == symbol.upper()
        ).count()
        
        # Indicateurs de sentiment
        sentiment_count = db.query(SentimentIndicators).filter(
            SentimentIndicators.symbol == symbol.upper()
        ).count()
        
        # Dernière donnée
        latest_data = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol.upper()
        ).order_by(HistoricalData.date.desc()).first()
        
        info = {
            "symbol": symbol.upper(),
            "historical_records": historical_count,
            "technical_indicators": technical_count,
            "sentiment_indicators": sentiment_count,
            "date_range": {
                "start": min_date[0] if min_date else None,
                "end": max_date[0] if max_date else None
            },
            "latest_data": {
                "date": latest_data.date if latest_data else None,
                "close": float(latest_data.close) if latest_data else None,
                "volume": latest_data.volume if latest_data else None
            },
            "data_completeness": {
                "historical": historical_count > 0,
                "technical": technical_count > 0,
                "sentiment": sentiment_count > 0
            }
        }
        
        return info
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des informations du symbole: {str(e)}"
        )


# === ENDPOINTS POUR LES STATISTIQUES ===

@router.get("/stats", response_model=StatisticsResponse)
def get_data_statistics(
    db: Session = Depends(get_db)
):
    """Récupérer les statistiques globales des données"""
    try:
        # Compter les enregistrements
        total_symbols = db.query(HistoricalData.symbol).distinct().count()
        total_historical = db.query(HistoricalData).count()
        total_technical = db.query(TechnicalIndicators).count()
        total_sentiment = db.query(SentimentIndicators).count()
        
        # Compter les modèles ML
        from app.models.database import MLModels, MLPredictions
        total_ml_models = db.query(MLModels).filter(MLModels.is_active == True).count()
        total_predictions = db.query(MLPredictions).count()
        
        # Couverture des données
        symbols_with_technical = db.query(TechnicalIndicators.symbol).distinct().count()
        symbols_with_sentiment = db.query(SentimentIndicators.symbol).distinct().count()
        
        data_coverage = {
            "symbols_with_technical": symbols_with_technical,
            "symbols_with_sentiment": symbols_with_sentiment,
            "technical_coverage_percentage": (symbols_with_technical / total_symbols * 100) if total_symbols > 0 else 0,
            "sentiment_coverage_percentage": (symbols_with_sentiment / total_symbols * 100) if total_symbols > 0 else 0
        }
        
        return StatisticsResponse(
            total_symbols=total_symbols,
            total_historical_records=total_historical,
            total_technical_indicators=total_technical,
            total_sentiment_indicators=total_sentiment,
            total_ml_models=total_ml_models,
            total_predictions=total_predictions,
            data_coverage=data_coverage,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors du calcul des statistiques: {str(e)}"
        )