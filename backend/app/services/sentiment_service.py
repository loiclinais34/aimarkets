"""
Service de calcul des indicateurs de sentiment
Calcule tous les indicateurs de sentiment pour les données historiques
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from ..core.config import settings
from ..models.database import HistoricalData, SentimentIndicators

logger = logging.getLogger(__name__)


class SentimentIndicatorService:
    def __init__(self):
        pass
    
    def calculate_and_store_indicators(self, symbol: str, db: Session) -> Dict:
        """Calculer et stocker les indicateurs de sentiment pour un symbole"""
        try:
            # Récupérer les données historiques
            historical_data = db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol
            ).order_by(HistoricalData.date.asc()).all()
            
            if len(historical_data) < 30:
                return {"success": False, "error": f"Pas assez de données historiques pour {symbol} ({len(historical_data)} < 30)"}
            
            # Convertir en DataFrame
            df = pd.DataFrame([{
                'date': row.date,
                'close': float(row.close),
                'volume': row.volume,
                'high': float(row.high),
                'low': float(row.low),
                'open': float(row.open)
            } for row in historical_data])
            
            # Trier par date
            df = df.sort_values('date').reset_index(drop=True)
            
            count = 0
            for _, row in df.iterrows():
                # Vérifier si les indicateurs existent déjà
                existing = db.query(SentimentIndicators).filter(
                    SentimentIndicators.symbol == symbol,
                    SentimentIndicators.date == row['date']
                ).first()
                
                if existing:
                    continue  # Skip si déjà existant
                
                # Calculer des indicateurs de sentiment simulés basés sur les données de prix
                # En réalité, ces indicateurs proviendraient de sources externes (news, réseaux sociaux, etc.)
                
                # Score de sentiment normalisé (simulé basé sur la volatilité)
                price_change = (row['close'] - df['close'].shift(1).iloc[len(df) - 1]) / df['close'].shift(1).iloc[len(df) - 1] if len(df) > 1 else 0
                sentiment_score_normalized = max(-1, min(1, price_change * 10))  # Normaliser entre -1 et 1
                
                # Créer l'enregistrement
                sentiment_indicator = SentimentIndicators(
                    symbol=symbol,
                    date=row['date'],
                    sentiment_score_normalized=sentiment_score_normalized,
                    
                    # Momentum de sentiment (simulé)
                    sentiment_momentum_1d=sentiment_score_normalized * 0.8,
                    sentiment_momentum_3d=sentiment_score_normalized * 0.6,
                    sentiment_momentum_7d=sentiment_score_normalized * 0.4,
                    sentiment_momentum_14d=sentiment_score_normalized * 0.2,
                    
                    # Volatilité de sentiment (simulé)
                    sentiment_volatility_3d=abs(sentiment_score_normalized) * 0.5,
                    sentiment_volatility_7d=abs(sentiment_score_normalized) * 0.3,
                    sentiment_volatility_14d=abs(sentiment_score_normalized) * 0.2,
                    sentiment_volatility_30d=abs(sentiment_score_normalized) * 0.1,
                    
                    # Moyennes mobiles de sentiment
                    sentiment_sma_3=sentiment_score_normalized,
                    sentiment_sma_7=sentiment_score_normalized * 0.8,
                    sentiment_sma_14=sentiment_score_normalized * 0.6,
                    sentiment_sma_30=sentiment_score_normalized * 0.4,
                    sentiment_ema_3=sentiment_score_normalized,
                    sentiment_ema_7=sentiment_score_normalized * 0.9,
                    sentiment_ema_14=sentiment_score_normalized * 0.7,
                    sentiment_ema_30=sentiment_score_normalized * 0.5,
                    
                    # Oscillateurs de sentiment
                    sentiment_rsi_14=50 + sentiment_score_normalized * 20,  # RSI entre 30-70
                    sentiment_macd=sentiment_score_normalized * 0.1,
                    sentiment_macd_signal=sentiment_score_normalized * 0.08,
                    sentiment_macd_histogram=sentiment_score_normalized * 0.02,
                    
                    # Indicateurs de volume de news (simulés)
                    news_volume_sma_7=10 + abs(sentiment_score_normalized) * 5,
                    news_volume_sma_14=8 + abs(sentiment_score_normalized) * 4,
                    news_volume_sma_30=6 + abs(sentiment_score_normalized) * 3,
                    news_volume_roc_7d=sentiment_score_normalized * 0.1,
                    news_volume_roc_14d=sentiment_score_normalized * 0.08,
                    
                    # Ratios de distribution de sentiment
                    news_positive_ratio=0.5 + max(0, sentiment_score_normalized) * 0.3,
                    news_negative_ratio=0.3 + max(0, -sentiment_score_normalized) * 0.3,
                    news_neutral_ratio=0.2,
                    news_sentiment_quality=0.7 + abs(sentiment_score_normalized) * 0.2,
                    
                    # Indicateurs d'intérêt court (simulés)
                    short_interest_momentum_5d=sentiment_score_normalized * -0.1,  # Inverse du sentiment
                    short_interest_momentum_10d=sentiment_score_normalized * -0.08,
                    short_interest_momentum_20d=sentiment_score_normalized * -0.06,
                    short_interest_volatility_7d=abs(sentiment_score_normalized) * 0.1,
                    short_interest_volatility_14d=abs(sentiment_score_normalized) * 0.08,
                    short_interest_volatility_30d=abs(sentiment_score_normalized) * 0.06,
                    
                    # Indicateurs composites
                    sentiment_composite_bullish=max(0, sentiment_score_normalized) * 0.8,
                    sentiment_composite_bearish=max(0, -sentiment_score_normalized) * 0.8,
                    sentiment_composite_uncertainty=abs(sentiment_score_normalized) * 0.3,
                    sentiment_composite_stability=1 - abs(sentiment_score_normalized) * 0.5
                )
                
                db.add(sentiment_indicator)
                count += 1
            
            # Commit tous les changements
            db.commit()
            
            return {"success": True, "count": count}
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des indicateurs de sentiment pour {symbol}: {e}")
            db.rollback()
            return {"success": False, "error": str(e)}
