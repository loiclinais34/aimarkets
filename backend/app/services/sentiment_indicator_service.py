"""
Service pour calculer les indicateurs de sentiment
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models.database import SentimentData, SentimentIndicators
import logging

logger = logging.getLogger(__name__)

class SentimentIndicatorService:
    """Service pour calculer les indicateurs de sentiment"""
    
    def __init__(self):
        pass
    
    def calculate_sentiment_indicators(self, db: Session, symbol: str, limit_per_symbol: int = 500) -> bool:
        """
        Calculer les indicateurs de sentiment pour un symbole
        
        Args:
            db: Session de base de données
            symbol: Symbole à traiter
            limit_per_symbol: Nombre maximum d'enregistrements à traiter
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            # Récupérer les données de sentiment
            sentiment_data = db.query(SentimentData).filter(
                SentimentData.symbol == symbol
            ).order_by(SentimentData.date.desc()).limit(limit_per_symbol).all()
            
            if not sentiment_data:
                logger.warning(f"Aucune donnée de sentiment trouvée pour {symbol}")
                return False
            
            # Convertir en DataFrame
            data = []
            for record in sentiment_data:
                data.append({
                    'date': record.date,
                    'news_count': record.news_count or 0,
                    'news_sentiment_score': float(record.news_sentiment_score or 0),
                    'news_sentiment_std': float(record.news_sentiment_std or 0),
                    'news_positive_count': record.news_positive_count or 0,
                    'news_negative_count': record.news_negative_count or 0,
                    'news_neutral_count': record.news_neutral_count or 0,
                    'top_news_sentiment': float(record.top_news_sentiment or 0),
                    'sentiment_reasoning': record.sentiment_reasoning,
                    'sentiment_momentum_5d': float(record.sentiment_momentum_5d or 0),
                    'sentiment_momentum_20d': float(record.sentiment_momentum_20d or 0),
                    'sentiment_volatility_5d': float(record.sentiment_volatility_5d or 0),
                    'sentiment_relative_strength': float(record.sentiment_relative_strength or 0),
                    'data_quality_score': float(record.data_quality_score or 0.5)
                })
            
            df = pd.DataFrame(data)
            
            # Trier par date croissante pour les calculs
            df = df.sort_values('date').reset_index(drop=True)
            
            # Calculer les indicateurs de sentiment
            df = self._calculate_indicators(df)
            
            # Sauvegarder les indicateurs
            self._save_indicators(db, symbol, df)
            
            # Mettre à jour les colonnes manquantes dans SentimentData
            self._update_sentiment_data_columns(db, symbol, df)
            
            logger.info(f"Indicateurs de sentiment calculés pour {symbol}: {len(df)} enregistrements")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des indicateurs de sentiment pour {symbol}: {e}")
            return False
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculer tous les indicateurs de sentiment"""
        
        # 1. Sentiment Score Normalisé (0-100)
        df['sentiment_score_normalized'] = ((df['news_sentiment_score'] + 1) / 2) * 100
        
        # 2. Sentiment Momentum (différence sur différentes périodes)
        df['sentiment_momentum_1d'] = df['news_sentiment_score'].diff(1)
        df['sentiment_momentum_3d'] = df['news_sentiment_score'].diff(3)
        df['sentiment_momentum_7d'] = df['news_sentiment_score'].diff(7)
        df['sentiment_momentum_14d'] = df['news_sentiment_score'].diff(14)
        
        # 3. Sentiment Volatility (écart-type mobile)
        df['sentiment_volatility_3d'] = df['news_sentiment_score'].rolling(window=3, min_periods=1).std()
        df['sentiment_volatility_7d'] = df['news_sentiment_score'].rolling(window=7, min_periods=1).std()
        df['sentiment_volatility_14d'] = df['news_sentiment_score'].rolling(window=14, min_periods=1).std()
        df['sentiment_volatility_30d'] = df['news_sentiment_score'].rolling(window=30, min_periods=1).std()
        
        # 4. Sentiment Moving Averages
        df['sentiment_sma_3'] = df['news_sentiment_score'].rolling(window=3, min_periods=1).mean()
        df['sentiment_sma_7'] = df['news_sentiment_score'].rolling(window=7, min_periods=1).mean()
        df['sentiment_sma_14'] = df['news_sentiment_score'].rolling(window=14, min_periods=1).mean()
        df['sentiment_sma_30'] = df['news_sentiment_score'].rolling(window=30, min_periods=1).mean()
        
        df['sentiment_ema_3'] = df['news_sentiment_score'].ewm(span=3, min_periods=1).mean()
        df['sentiment_ema_7'] = df['news_sentiment_score'].ewm(span=7, min_periods=1).mean()
        df['sentiment_ema_14'] = df['news_sentiment_score'].ewm(span=14, min_periods=1).mean()
        df['sentiment_ema_30'] = df['news_sentiment_score'].ewm(span=30, min_periods=1).mean()
        
        # 5. Sentiment RSI (Relative Strength Index)
        delta = df['news_sentiment_score'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss
        df['sentiment_rsi_14'] = 100 - (100 / (1 + rs))
        
        # 6. Sentiment MACD
        ema_12 = df['news_sentiment_score'].ewm(span=12, min_periods=1).mean()
        ema_26 = df['news_sentiment_score'].ewm(span=26, min_periods=1).mean()
        df['sentiment_macd'] = ema_12 - ema_26
        df['sentiment_macd_signal'] = df['sentiment_macd'].ewm(span=9, min_periods=1).mean()
        df['sentiment_macd_histogram'] = df['sentiment_macd'] - df['sentiment_macd_signal']
        
        # 7. News Volume Indicators
        df['news_volume_sma_7'] = df['news_count'].rolling(window=7, min_periods=1).mean()
        df['news_volume_sma_14'] = df['news_count'].rolling(window=14, min_periods=1).mean()
        df['news_volume_sma_30'] = df['news_count'].rolling(window=30, min_periods=1).mean()
        
        df['news_volume_roc_7d'] = ((df['news_count'] - df['news_count'].shift(7)) / df['news_count'].shift(7)) * 100
        df['news_volume_roc_14d'] = ((df['news_count'] - df['news_count'].shift(14)) / df['news_count'].shift(14)) * 100
        
        # 8. News Sentiment Distribution
        total_news = df['news_positive_count'] + df['news_negative_count'] + df['news_neutral_count']
        df['news_positive_ratio'] = df['news_positive_count'] / total_news.replace(0, 1)
        df['news_negative_ratio'] = df['news_negative_count'] / total_news.replace(0, 1)
        df['news_neutral_ratio'] = df['news_neutral_count'] / total_news.replace(0, 1)
        
        # 9. News Sentiment Quality Score
        df['news_sentiment_quality'] = df['news_count'] * (1 - df['news_sentiment_std'])
        
        # 10. Short Interest Indicators (désactivés - données non récupérées)
        # Ces indicateurs ne sont plus calculés car les données short_interest et short_volume
        # ne sont plus récupérées via les API (trop sparses et non pertinentes)
        df['short_interest_momentum_5d'] = None
        df['short_interest_momentum_10d'] = None
        df['short_interest_momentum_20d'] = None
        df['short_interest_volatility_7d'] = None
        df['short_interest_volatility_14d'] = None
        df['short_interest_volatility_30d'] = None
        df['short_interest_sma_7'] = None
        df['short_interest_sma_14'] = None
        df['short_interest_sma_30'] = None
        
        # 11. Short Volume Indicators (désactivés - données non récupérées)
        df['short_volume_momentum_5d'] = None
        df['short_volume_momentum_10d'] = None
        df['short_volume_momentum_20d'] = None
        df['short_volume_volatility_7d'] = None
        df['short_volume_volatility_14d'] = None
        df['short_volume_volatility_30d'] = None
        
        # 12. Indicateurs composites (adaptés sans short interest/volume)
        df['sentiment_strength_index'] = (
            df['sentiment_score_normalized'] * 0.4 +
            df['news_positive_ratio'].fillna(0) * 100 * 0.3 +
            (1 - df['news_negative_ratio'].fillna(0)) * 100 * 0.3
        )
        
        # Market sentiment index basé uniquement sur les news (sans short interest)
        df['market_sentiment_index'] = (
            df['sentiment_score_normalized'] * 0.6 +
            df['news_positive_ratio'].fillna(0) * 100 * 0.4
        )
        
        df['sentiment_divergence'] = df['news_sentiment_score'] - df['sentiment_momentum_5d'].fillna(0)
        df['sentiment_acceleration'] = df['sentiment_momentum_1d'].diff(1)
        df['sentiment_trend_strength'] = abs(df['sentiment_momentum_7d']) / df['sentiment_volatility_7d'].replace(0, np.nan)
        
        df['sentiment_quality_index'] = (
            df['data_quality_score'] * 0.4 +
            (1 - df['news_sentiment_std']) * 0.3 +
            (df['news_count'] / df['news_count'].rolling(window=30, min_periods=1).mean()).fillna(0) * 0.3
        )
        
        # Sentiment risk score basé uniquement sur les news (sans short interest)
        df['sentiment_risk_score'] = (
            df['sentiment_volatility_14d'].fillna(0) * 0.5 +
            df['news_negative_ratio'].fillna(0) * 0.5
        )
        
        # Nettoyer les données
        df = df.replace([np.inf, -np.inf], np.nan)
        
        return df
    
    def _save_indicators(self, db: Session, symbol: str, df: pd.DataFrame) -> None:
        """Sauvegarder les indicateurs en base de données"""
        
        for _, row in df.iterrows():
            # Vérifier si l'enregistrement existe déjà
            existing = db.query(SentimentIndicators).filter(
                SentimentIndicators.symbol == symbol,
                SentimentIndicators.date == row['date']
            ).first()
            
            if existing:
                # Mettre à jour l'enregistrement existant
                existing.sentiment_score_normalized = row.get('sentiment_score_normalized')
                existing.sentiment_momentum_1d = row.get('sentiment_momentum_1d')
                existing.sentiment_momentum_3d = row.get('sentiment_momentum_3d')
                existing.sentiment_momentum_7d = row.get('sentiment_momentum_7d')
                existing.sentiment_momentum_14d = row.get('sentiment_momentum_14d')
                existing.sentiment_volatility_3d = row.get('sentiment_volatility_3d')
                existing.sentiment_volatility_7d = row.get('sentiment_volatility_7d')
                existing.sentiment_volatility_14d = row.get('sentiment_volatility_14d')
                existing.sentiment_volatility_30d = row.get('sentiment_volatility_30d')
                existing.sentiment_sma_3 = row.get('sentiment_sma_3')
                existing.sentiment_sma_7 = row.get('sentiment_sma_7')
                existing.sentiment_sma_14 = row.get('sentiment_sma_14')
                existing.sentiment_sma_30 = row.get('sentiment_sma_30')
                existing.sentiment_ema_3 = row.get('sentiment_ema_3')
                existing.sentiment_ema_7 = row.get('sentiment_ema_7')
                existing.sentiment_ema_14 = row.get('sentiment_ema_14')
                existing.sentiment_ema_30 = row.get('sentiment_ema_30')
                existing.sentiment_rsi_14 = row.get('sentiment_rsi_14')
                existing.sentiment_macd = row.get('sentiment_macd')
                existing.sentiment_macd_signal = row.get('sentiment_macd_signal')
                existing.sentiment_macd_histogram = row.get('sentiment_macd_histogram')
                existing.news_volume_sma_7 = row.get('news_volume_sma_7')
                existing.news_volume_sma_14 = row.get('news_volume_sma_14')
                existing.news_volume_sma_30 = row.get('news_volume_sma_30')
                existing.news_volume_roc_7d = row.get('news_volume_roc_7d')
                existing.news_volume_roc_14d = row.get('news_volume_roc_14d')
                existing.news_positive_ratio = row.get('news_positive_ratio')
                existing.news_negative_ratio = row.get('news_negative_ratio')
                existing.news_neutral_ratio = row.get('news_neutral_ratio')
                existing.news_sentiment_quality = row.get('news_sentiment_quality')
                existing.sentiment_strength_index = row.get('sentiment_strength_index')
                existing.market_sentiment_index = row.get('market_sentiment_index')
                existing.sentiment_divergence = row.get('sentiment_divergence')
                existing.sentiment_acceleration = row.get('sentiment_acceleration')
                existing.sentiment_trend_strength = row.get('sentiment_trend_strength')
                existing.sentiment_quality_index = row.get('sentiment_quality_index')
                existing.sentiment_risk_score = row.get('sentiment_risk_score')
            else:
                # Créer un nouvel enregistrement
                indicator = SentimentIndicators(
                    symbol=symbol,
                    date=row['date'],
                    sentiment_score_normalized=row.get('sentiment_score_normalized'),
                    sentiment_momentum_1d=row.get('sentiment_momentum_1d'),
                    sentiment_momentum_3d=row.get('sentiment_momentum_3d'),
                    sentiment_momentum_7d=row.get('sentiment_momentum_7d'),
                    sentiment_momentum_14d=row.get('sentiment_momentum_14d'),
                    sentiment_volatility_3d=row.get('sentiment_volatility_3d'),
                    sentiment_volatility_7d=row.get('sentiment_volatility_7d'),
                    sentiment_volatility_14d=row.get('sentiment_volatility_14d'),
                    sentiment_volatility_30d=row.get('sentiment_volatility_30d'),
                    sentiment_sma_3=row.get('sentiment_sma_3'),
                    sentiment_sma_7=row.get('sentiment_sma_7'),
                    sentiment_sma_14=row.get('sentiment_sma_14'),
                    sentiment_sma_30=row.get('sentiment_sma_30'),
                    sentiment_ema_3=row.get('sentiment_ema_3'),
                    sentiment_ema_7=row.get('sentiment_ema_7'),
                    sentiment_ema_14=row.get('sentiment_ema_14'),
                    sentiment_ema_30=row.get('sentiment_ema_30'),
                    sentiment_rsi_14=row.get('sentiment_rsi_14'),
                    sentiment_macd=row.get('sentiment_macd'),
                    sentiment_macd_signal=row.get('sentiment_macd_signal'),
                    sentiment_macd_histogram=row.get('sentiment_macd_histogram'),
                    news_volume_sma_7=row.get('news_volume_sma_7'),
                    news_volume_sma_14=row.get('news_volume_sma_14'),
                    news_volume_sma_30=row.get('news_volume_sma_30'),
                    news_volume_roc_7d=row.get('news_volume_roc_7d'),
                    news_volume_roc_14d=row.get('news_volume_roc_14d'),
                    news_positive_ratio=row.get('news_positive_ratio'),
                    news_negative_ratio=row.get('news_negative_ratio'),
                    news_neutral_ratio=row.get('news_neutral_ratio'),
                    news_sentiment_quality=row.get('news_sentiment_quality'),
                    sentiment_strength_index=row.get('sentiment_strength_index'),
                    market_sentiment_index=row.get('market_sentiment_index'),
                    sentiment_divergence=row.get('sentiment_divergence'),
                    sentiment_acceleration=row.get('sentiment_acceleration'),
                    sentiment_trend_strength=row.get('sentiment_trend_strength'),
                    sentiment_quality_index=row.get('sentiment_quality_index'),
                    sentiment_risk_score=row.get('sentiment_risk_score')
                )
                db.add(indicator)
        
        db.commit()
    
    def _update_sentiment_data_columns(self, db: Session, symbol: str, df: pd.DataFrame) -> None:
        """Mettre à jour les colonnes manquantes dans SentimentData"""
        try:
            from app.services.polygon_service import PolygonService
            polygon_service = PolygonService()
            
            for _, row in df.iterrows():
                # Trouver l'enregistrement SentimentData correspondant
                sentiment_record = db.query(SentimentData).filter(
                    SentimentData.symbol == symbol,
                    SentimentData.date == row['date']
                ).first()
                
                if sentiment_record:
                    # Mettre à jour les colonnes manquantes
                    sentiment_record.sentiment_momentum_5d = row.get('sentiment_momentum_7d')  # Utiliser 7d comme approximation
                    sentiment_record.sentiment_momentum_20d = row.get('sentiment_momentum_14d')  # Utiliser 14d comme approximation
                    sentiment_record.sentiment_volatility_5d = row.get('sentiment_volatility_7d')  # Utiliser 7d comme approximation
                    sentiment_record.sentiment_relative_strength = row.get('sentiment_relative_strength')
                    sentiment_record.processing_notes = f"Calculé le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                    
                    # Recalculer les colonnes top_news_* si elles sont vides ou par défaut
                    if (sentiment_record.top_news_title is None or 
                        sentiment_record.top_news_title == "" or 
                        sentiment_record.top_news_title == "Aucune news disponible"):
                        
                        # Récupérer les news pour cette date et recalculer
                        try:
                            from datetime import timedelta
                            end_date = row['date'] + timedelta(days=1)
                            start_date = row['date']
                            
                            news_data = polygon_service.get_news_data(
                                symbol, 
                                start_date.strftime('%Y-%m-%d'), 
                                end_date.strftime('%Y-%m-%d')
                            )
                            
                            # Filtrer pour la date spécifique
                            date_news = []
                            for n in news_data:
                                published_utc = n.get('published_utc', '')
                                if published_utc:
                                    try:
                                        news_date = datetime.fromisoformat(published_utc.replace('Z', '+00:00')).date()
                                        if news_date == row['date']:
                                            date_news.append(n)
                                    except:
                                        continue
                            
                            if date_news:
                                # Recalculer le sentiment pour obtenir les bonnes valeurs top_news_*
                                sentiment_result = polygon_service.calculate_sentiment_from_news(date_news, symbol)
                                sentiment_record.top_news_title = sentiment_result.get('top_news_title', "Aucune news disponible")
                                sentiment_record.top_news_sentiment = sentiment_result.get('top_news_sentiment', 0.0)
                                sentiment_record.top_news_url = sentiment_result.get('top_news_url', "")
                            else:
                                sentiment_record.top_news_title = "Aucune news disponible"
                                sentiment_record.top_news_sentiment = 0.0
                                sentiment_record.top_news_url = ""
                        except Exception as e:
                            logger.warning(f"Erreur lors du recalcul des top_news pour {symbol} le {row['date']}: {e}")
                            sentiment_record.top_news_title = "Aucune news disponible"
                            sentiment_record.top_news_sentiment = 0.0
                            sentiment_record.top_news_url = ""
            
            db.commit()
            logger.info(f"Colonnes SentimentData mises à jour pour {symbol}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des colonnes SentimentData pour {symbol}: {e}")
            db.rollback()
