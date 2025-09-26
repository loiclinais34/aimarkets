"""
Service de recalcul des indicateurs après mise à jour des données historiques
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from ..models.database import (
    HistoricalData, TechnicalIndicators, SentimentIndicators, 
    SentimentData, CorrelationMatrices, CrossAssetCorrelations, 
    CorrelationFeatures, SymbolMetadata
)

logger = logging.getLogger(__name__)

class IndicatorsRecalculationService:
    """Service pour recalculer tous les indicateurs après mise à jour des données historiques"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def recalculate_technical_indicators(self, symbol: str, start_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Recalcule tous les indicateurs techniques pour un symbole
        
        Args:
            symbol: Symbole à traiter
            start_date: Date de début pour le recalcul (optionnel)
            
        Returns:
            Dictionnaire avec les résultats du recalcul
        """
        try:
            logger.info(f"Recalcul des indicateurs techniques pour {symbol}")
            
            # Récupérer les données historiques
            query = self.db.query(HistoricalData).filter(HistoricalData.symbol == symbol)
            if start_date:
                query = query.filter(HistoricalData.date >= start_date)
            
            historical_data = query.order_by(HistoricalData.date.asc()).all()
            
            if not historical_data:
                return {
                    'success': False,
                    'error': f'Aucune donnée historique trouvée pour {symbol}',
                    'processed_dates': 0
                }
            
            processed_dates = 0
            
            # Traiter chaque date
            for i, data in enumerate(historical_data):
                try:
                    # Récupérer les données pour le calcul des indicateurs
                    # (besoin de données historiques pour les moyennes mobiles, etc.)
                    historical_window = self.db.query(HistoricalData).filter(
                        HistoricalData.symbol == symbol,
                        HistoricalData.date <= data.date
                    ).order_by(HistoricalData.date.desc()).limit(200).all()
                    
                    if len(historical_window) < 20:  # Minimum pour les calculs
                        continue
                    
                    # Calculer les indicateurs techniques
                    indicators = self._calculate_technical_indicators(historical_window)
                    
                    # Convertir les types numpy en types Python natifs
                    indicators = self._convert_numpy_types(indicators)
                    
                    # Sauvegarder ou mettre à jour les indicateurs
                    existing = self.db.query(TechnicalIndicators).filter(
                        TechnicalIndicators.symbol == symbol,
                        TechnicalIndicators.date == data.date
                    ).first()
                    
                    if existing:
                        # Mettre à jour
                        for key, value in indicators.items():
                            if hasattr(existing, key) and value is not None:
                                setattr(existing, key, value)
                        existing.updated_at = datetime.now()
                    else:
                        # Créer nouveau - s'assurer que tous les champs obligatoires sont présents
                        new_indicators = TechnicalIndicators(
                            symbol=symbol,
                            date=data.date,
                            sma_5=indicators.get('sma_5'),
                            sma_10=indicators.get('sma_10'),
                            sma_20=indicators.get('sma_20'),
                            sma_50=indicators.get('sma_50'),
                            sma_200=indicators.get('sma_200'),
                            ema_5=indicators.get('ema_5'),
                            ema_10=indicators.get('ema_10'),
                            ema_20=indicators.get('ema_20'),
                            ema_50=indicators.get('ema_50'),
                            ema_200=indicators.get('ema_200'),
                            rsi_14=indicators.get('rsi_14'),
                            macd=indicators.get('macd'),
                            macd_signal=indicators.get('macd_signal'),
                            macd_histogram=indicators.get('macd_histogram'),
                            stochastic_k=indicators.get('stochastic_k'),
                            stochastic_d=indicators.get('stochastic_d'),
                            williams_r=indicators.get('williams_r'),
                            roc=indicators.get('roc'),
                            cci=indicators.get('cci'),
                            bb_upper=indicators.get('bb_upper'),
                            bb_middle=indicators.get('bb_middle'),
                            bb_lower=indicators.get('bb_lower'),
                            bb_width=indicators.get('bb_width'),
                            bb_position=indicators.get('bb_position'),
                            obv=indicators.get('obv'),
                            volume_roc=indicators.get('volume_roc'),
                            volume_sma_20=indicators.get('volume_sma_20'),
                            atr_14=indicators.get('atr_14')
                        )
                        self.db.add(new_indicators)
                    
                    processed_dates += 1
                    
                except Exception as e:
                    logger.error(f"Erreur lors du calcul des indicateurs pour {symbol} le {data.date}: {e}")
                    continue
            
            self.db.commit()
            
            logger.info(f"Recalcul terminé pour {symbol}: {processed_dates} dates traitées")
            
            return {
                'success': True,
                'symbol': symbol,
                'processed_dates': processed_dates,
                'total_dates': len(historical_data)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors du recalcul des indicateurs techniques pour {symbol}: {e}")
            return {
                'success': False,
                'error': str(e),
                'processed_dates': 0
            }
    
    def _calculate_technical_indicators(self, historical_data: List[HistoricalData]) -> Dict[str, Any]:
        """
        Calcule les indicateurs techniques à partir des données historiques
        
        Args:
            historical_data: Liste des données historiques (du plus récent au plus ancien)
            
        Returns:
            Dictionnaire avec tous les indicateurs calculés
        """
        import pandas as pd
        import numpy as np
        
        # Convertir en DataFrame
        df = pd.DataFrame([{
            'date': h.date,
            'open': float(h.open),
            'high': float(h.high),
            'low': float(h.low),
            'close': float(h.close),
            'volume': h.volume,
            'vwap': float(h.vwap) if h.vwap else None
        } for h in reversed(historical_data)])  # Inverser pour avoir l'ordre chronologique
        
        indicators = {}
        
        try:
            # Moyennes mobiles simples
            indicators['sma_5'] = df['close'].rolling(window=5).mean().iloc[-1] if len(df) >= 5 else None
            indicators['sma_10'] = df['close'].rolling(window=10).mean().iloc[-1] if len(df) >= 10 else None
            indicators['sma_20'] = df['close'].rolling(window=20).mean().iloc[-1] if len(df) >= 20 else None
            indicators['sma_50'] = df['close'].rolling(window=50).mean().iloc[-1] if len(df) >= 50 else None
            indicators['sma_200'] = df['close'].rolling(window=200).mean().iloc[-1] if len(df) >= 200 else None
            
            # Moyennes mobiles exponentielles
            indicators['ema_5'] = df['close'].ewm(span=5).mean().iloc[-1] if len(df) >= 5 else None
            indicators['ema_10'] = df['close'].ewm(span=10).mean().iloc[-1] if len(df) >= 10 else None
            indicators['ema_20'] = df['close'].ewm(span=20).mean().iloc[-1] if len(df) >= 20 else None
            indicators['ema_50'] = df['close'].ewm(span=50).mean().iloc[-1] if len(df) >= 50 else None
            indicators['ema_200'] = df['close'].ewm(span=200).mean().iloc[-1] if len(df) >= 200 else None
            
            # RSI
            if len(df) >= 14:
                delta = df['close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                rs = gain / loss
                indicators['rsi_14'] = 100 - (100 / (1 + rs)).iloc[-1]
            else:
                indicators['rsi_14'] = None
            
            # MACD
            if len(df) >= 26:
                ema_12 = df['close'].ewm(span=12).mean()
                ema_26 = df['close'].ewm(span=26).mean()
                macd_line = ema_12 - ema_26
                signal_line = macd_line.ewm(span=9).mean()
                
                indicators['macd'] = macd_line.iloc[-1]
                indicators['macd_signal'] = signal_line.iloc[-1]
                indicators['macd_histogram'] = (macd_line - signal_line).iloc[-1]
            else:
                indicators['macd'] = None
                indicators['macd_signal'] = None
                indicators['macd_histogram'] = None
            
            # Bollinger Bands
            if len(df) >= 20:
                sma_20 = df['close'].rolling(window=20).mean()
                std_20 = df['close'].rolling(window=20).std()
                
                indicators['bb_upper'] = (sma_20 + (std_20 * 2)).iloc[-1]
                indicators['bb_middle'] = sma_20.iloc[-1]
                indicators['bb_lower'] = (sma_20 - (std_20 * 2)).iloc[-1]
                indicators['bb_width'] = ((indicators['bb_upper'] - indicators['bb_lower']) / indicators['bb_middle'] * 100) if indicators['bb_middle'] else None
                indicators['bb_position'] = ((df['close'].iloc[-1] - indicators['bb_lower']) / (indicators['bb_upper'] - indicators['bb_lower']) * 100) if indicators['bb_upper'] and indicators['bb_lower'] else None
            else:
                indicators['bb_upper'] = None
                indicators['bb_middle'] = None
                indicators['bb_lower'] = None
                indicators['bb_width'] = None
                indicators['bb_position'] = None
            
            # ATR
            if len(df) >= 14:
                high_low = df['high'] - df['low']
                high_close = np.abs(df['high'] - df['close'].shift())
                low_close = np.abs(df['low'] - df['close'].shift())
                true_range = np.maximum(high_low, np.maximum(high_close, low_close))
                indicators['atr_14'] = true_range.rolling(window=14).mean().iloc[-1]
            else:
                indicators['atr_14'] = None
            
            # OBV
            if len(df) >= 2:
                obv = np.where(df['close'] > df['close'].shift(), df['volume'], 
                              np.where(df['close'] < df['close'].shift(), -df['volume'], 0))
                indicators['obv'] = np.cumsum(obv)[-1]
            else:
                indicators['obv'] = None
            
            # Stochastic
            if len(df) >= 14:
                lowest_low = df['low'].rolling(window=14).min()
                highest_high = df['high'].rolling(window=14).max()
                k_percent = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
                indicators['stochastic_k'] = k_percent.iloc[-1]
                indicators['stochastic_d'] = k_percent.rolling(window=3).mean().iloc[-1]
            else:
                indicators['stochastic_k'] = None
                indicators['stochastic_d'] = None
            
            # Williams %R
            if len(df) >= 14:
                highest_high = df['high'].rolling(window=14).max()
                lowest_low = df['low'].rolling(window=14).min()
                indicators['williams_r'] = -100 * ((highest_high - df['close']) / (highest_high - lowest_low)).iloc[-1]
            else:
                indicators['williams_r'] = None
            
            # ROC (Rate of Change)
            if len(df) >= 10:
                indicators['roc'] = ((df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10] * 100) if df['close'].iloc[-10] != 0 else None
            else:
                indicators['roc'] = None
            
            # CCI (Commodity Channel Index)
            if len(df) >= 20:
                typical_price = (df['high'] + df['low'] + df['close']) / 3
                sma_tp = typical_price.rolling(window=20).mean()
                mad = typical_price.rolling(window=20).apply(lambda x: np.mean(np.abs(x - x.mean())))
                indicators['cci'] = ((typical_price - sma_tp) / (0.015 * mad)).iloc[-1]
            else:
                indicators['cci'] = None
            
            # Volume indicators
            if len(df) >= 20:
                indicators['volume_sma_20'] = df['volume'].rolling(window=20).mean().iloc[-1]
                indicators['volume_roc'] = ((df['volume'].iloc[-1] - df['volume'].iloc[-10]) / df['volume'].iloc[-10] * 100) if df['volume'].iloc[-10] != 0 else None
            else:
                indicators['volume_sma_20'] = None
                indicators['volume_roc'] = None
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des indicateurs techniques: {e}")
            # Retourner des valeurs par défaut
            indicators = {key: None for key in [
                'sma_5', 'sma_10', 'sma_20', 'sma_50', 'sma_200',
                'ema_5', 'ema_10', 'ema_20', 'ema_50', 'ema_200',
                'rsi_14', 'macd', 'macd_signal', 'macd_histogram',
                'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_position',
                'atr_14', 'obv', 'stochastic_k', 'stochastic_d',
                'williams_r', 'roc', 'cci', 'volume_sma_20', 'volume_roc'
            ]}
        
        return indicators
    
    def _convert_numpy_types(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convertit les types numpy en types Python natifs pour la compatibilité avec PostgreSQL
        
        Args:
            indicators: Dictionnaire des indicateurs avec des types numpy
            
        Returns:
            Dictionnaire avec des types Python natifs
        """
        import numpy as np
        
        converted = {}
        for key, value in indicators.items():
            if value is None:
                converted[key] = None
            elif isinstance(value, (np.integer, np.int64, np.int32)):
                converted[key] = int(value)
            elif isinstance(value, (np.floating, np.float64, np.float32)):
                converted[key] = float(value)
            elif isinstance(value, np.ndarray):
                # Pour les arrays numpy, prendre la première valeur
                converted[key] = float(value.item()) if value.size > 0 else None
            else:
                converted[key] = value
        
        return converted
    
    def recalculate_sentiment_indicators(self, symbol: str, start_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Recalcule tous les indicateurs de sentiment pour un symbole
        
        Args:
            symbol: Symbole à traiter
            start_date: Date de début pour le recalcul (optionnel)
            
        Returns:
            Dictionnaire avec les résultats du recalcul
        """
        try:
            logger.info(f"Recalcul des indicateurs de sentiment pour {symbol}")
            
            # Récupérer les données de sentiment
            query = self.db.query(SentimentData).filter(SentimentData.symbol == symbol)
            if start_date:
                query = query.filter(SentimentData.date >= start_date)
            
            sentiment_data = query.order_by(SentimentData.date.asc()).all()
            
            if not sentiment_data:
                return {
                    'success': False,
                    'error': f'Aucune donnée de sentiment trouvée pour {symbol}',
                    'processed_dates': 0
                }
            
            processed_dates = 0
            
            # Traiter chaque date
            for i, data in enumerate(sentiment_data):
                try:
                    # Récupérer les données pour le calcul des indicateurs
                    sentiment_window = self.db.query(SentimentData).filter(
                        SentimentData.symbol == symbol,
                        SentimentData.date <= data.date
                    ).order_by(SentimentData.date.desc()).limit(30).all()
                    
                    if len(sentiment_window) < 5:  # Minimum pour les calculs
                        continue
                    
                    # Calculer les indicateurs de sentiment
                    indicators = self._calculate_sentiment_indicators(sentiment_window)
                    
                    # Sauvegarder ou mettre à jour les indicateurs
                    existing = self.db.query(SentimentIndicators).filter(
                        SentimentIndicators.symbol == symbol,
                        SentimentIndicators.date == data.date
                    ).first()
                    
                    if existing:
                        # Mettre à jour
                        for key, value in indicators.items():
                            if hasattr(existing, key):
                                setattr(existing, key, value)
                        existing.updated_at = datetime.now()
                    else:
                        # Créer nouveau
                        new_indicators = SentimentIndicators(
                            symbol=symbol,
                            date=data.date,
                            **indicators
                        )
                        self.db.add(new_indicators)
                    
                    processed_dates += 1
                    
                except Exception as e:
                    logger.error(f"Erreur lors du calcul des indicateurs de sentiment pour {symbol} le {data.date}: {e}")
                    continue
            
            self.db.commit()
            
            logger.info(f"Recalcul terminé pour {symbol}: {processed_dates} dates traitées")
            
            return {
                'success': True,
                'symbol': symbol,
                'processed_dates': processed_dates,
                'total_dates': len(sentiment_data)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors du recalcul des indicateurs de sentiment pour {symbol}: {e}")
            return {
                'success': False,
                'error': str(e),
                'processed_dates': 0
            }
    
    def _calculate_sentiment_indicators(self, sentiment_data: List[SentimentData]) -> Dict[str, Any]:
        """
        Calcule les indicateurs de sentiment à partir des données de sentiment
        
        Args:
            sentiment_data: Liste des données de sentiment (du plus récent au plus ancien)
            
        Returns:
            Dictionnaire avec tous les indicateurs calculés
        """
        import pandas as pd
        import numpy as np
        
        # Convertir en DataFrame
        df = pd.DataFrame([{
            'date': s.date,
            'news_count': s.news_count,
            'news_sentiment_score': float(s.news_sentiment_score) if s.news_sentiment_score else 0.0,
            'news_positive_count': s.news_positive_count,
            'news_negative_count': s.news_negative_count,
            'news_neutral_count': s.news_neutral_count,
        } for s in reversed(sentiment_data)])  # Inverser pour avoir l'ordre chronologique
        
        indicators = {}
        
        try:
            # Score de sentiment normalisé
            if len(df) > 0:
                total_news = df['news_positive_count'] + df['news_negative_count'] + df['news_neutral_count']
                indicators['sentiment_score_normalized'] = (
                    (df['news_positive_count'] - df['news_negative_count']) / total_news
                ).iloc[-1] if total_news.iloc[-1] > 0 else 0.0
            else:
                indicators['sentiment_score_normalized'] = 0.0
            
            # Momentum de sentiment
            if len(df) >= 7:
                indicators['sentiment_momentum_7d'] = (
                    df['news_sentiment_score'].rolling(window=7).mean().iloc[-1] -
                    df['news_sentiment_score'].rolling(window=7).mean().iloc[-7]
                ) if len(df) >= 14 else 0.0
            else:
                indicators['sentiment_momentum_7d'] = 0.0
            
            # Volatilité de sentiment
            if len(df) >= 14:
                indicators['sentiment_volatility_14d'] = df['news_sentiment_score'].rolling(window=14).std().iloc[-1]
            else:
                indicators['sentiment_volatility_14d'] = 0.0
            
            # Ratios de nouvelles
            if len(df) > 0:
                total_news = df['news_positive_count'] + df['news_negative_count'] + df['news_neutral_count']
                indicators['news_positive_ratio'] = (
                    df['news_positive_count'] / total_news
                ).iloc[-1] if total_news.iloc[-1] > 0 else 0.0
                indicators['news_negative_ratio'] = (
                    df['news_negative_count'] / total_news
                ).iloc[-1] if total_news.iloc[-1] > 0 else 0.0
            else:
                indicators['news_positive_ratio'] = 0.0
                indicators['news_negative_ratio'] = 0.0
            
            
            # Score de qualité des données
            if len(df) > 0:
                news_count_score = min(df['news_count'].iloc[-1] / 10.0, 1.0)  # Normaliser sur 10 nouvelles
                sentiment_consistency = 1.0 - df['news_sentiment_score'].rolling(window=7).std().iloc[-1] if len(df) >= 7 else 0.5
                indicators['data_quality_score'] = (news_count_score + sentiment_consistency) / 2.0
            else:
                indicators['data_quality_score'] = 0.0
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des indicateurs de sentiment: {e}")
            # Retourner des valeurs par défaut
            indicators = {
                'sentiment_score_normalized': 0.0,
                'sentiment_momentum_7d': 0.0,
                'sentiment_volatility_14d': 0.0,
                'news_positive_ratio': 0.0,
                'news_negative_ratio': 0.0,
                'data_quality_score': 0.0
            }
        
        return indicators
    
    def recalculate_correlations(self, symbols: List[str], start_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Recalcule toutes les corrélations pour une liste de symboles
        
        Args:
            symbols: Liste des symboles à traiter
            start_date: Date de début pour le recalcul (optionnel)
            
        Returns:
            Dictionnaire avec les résultats du recalcul
        """
        try:
            logger.info(f"Recalcul des corrélations pour {len(symbols)} symboles")
            
            processed_correlations = 0
            correlation_pairs = set()  # Pour éviter les doublons
            
            # Calculer toutes les paires de corrélations
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols):
                    if i >= j:  # Éviter les doublons et les auto-corrélations
                        continue
                    
                    # Créer une paire ordonnée pour éviter les doublons
                    pair = tuple(sorted([symbol1, symbol2]))
                    if pair in correlation_pairs:
                        continue
                    
                    correlation_pairs.add(pair)
                    
                    try:
                        # Calculer la corrélation entre les deux symboles
                        correlation_value = self._calculate_pair_correlation(symbol1, symbol2, start_date)
                        
                        if correlation_value is not None:
                            # Sauvegarder la corrélation avec un symbole composite pour éviter les conflits
                            composite_symbol = f"{symbol1}_{symbol2}"
                            self._save_correlation_unique(composite_symbol, symbol1, symbol2, correlation_value)
                            processed_correlations += 1
                    
                    except Exception as e:
                        logger.error(f"Erreur lors du calcul de la corrélation {symbol1}-{symbol2}: {e}")
                        continue
            
            self.db.commit()
            
            logger.info(f"Recalcul des corrélations terminé: {processed_correlations} corrélations traitées")
            
            return {
                'success': True,
                'processed_correlations': processed_correlations,
                'symbols_count': len(symbols)
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors du recalcul des corrélations: {e}")
            return {
                'success': False,
                'error': str(e),
                'processed_correlations': 0
            }
    
    def _calculate_pair_correlation(self, symbol1: str, symbol2: str, start_date: Optional[date] = None) -> Optional[float]:
        """
        Calcule la corrélation entre deux symboles spécifiques
        
        Args:
            symbol1: Premier symbole
            symbol2: Deuxième symbole
            start_date: Date de début pour le calcul
            
        Returns:
            Valeur de corrélation ou None si impossible à calculer
        """
        import pandas as pd
        import numpy as np
        
        try:
            # Récupérer les données des deux symboles
            query1 = self.db.query(HistoricalData).filter(HistoricalData.symbol == symbol1)
            query2 = self.db.query(HistoricalData).filter(HistoricalData.symbol == symbol2)
            
            if start_date:
                query1 = query1.filter(HistoricalData.date >= start_date)
                query2 = query2.filter(HistoricalData.date >= start_date)
            
            data1 = query1.order_by(HistoricalData.date.asc()).all()
            data2 = query2.order_by(HistoricalData.date.asc()).all()
            
            if len(data1) < 30 or len(data2) < 30:
                return None
            
            # Créer les DataFrames
            df1 = pd.DataFrame([{'date': d.date, 'close': float(d.close)} for d in data1])
            df2 = pd.DataFrame([{'date': d.date, 'close': float(d.close)} for d in data2])
            
            # Fusionner sur la date pour avoir les mêmes périodes
            merged = pd.merge(df1, df2, on='date', suffixes=('_1', '_2'))
            
            if len(merged) < 30:
                return None
            
            # Calculer la corrélation
            correlation = merged['close_1'].corr(merged['close_2'])
            
            return float(correlation) if not np.isnan(correlation) else None
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la corrélation {symbol1}-{symbol2}: {e}")
            return None
    
    def _save_correlation(self, symbol: str, target_symbol: str, correlation_value: float):
        """
        Sauvegarde une corrélation dans la base de données
        
        Args:
            symbol: Symbole de référence
            target_symbol: Symbole cible
            correlation_value: Valeur de corrélation
        """
        try:
            # Vérifier si la corrélation existe déjà avec le symbole cible
            existing = self.db.query(CorrelationMatrices).filter(
                CorrelationMatrices.symbol == symbol,
                CorrelationMatrices.date == datetime.now().date(),
                CorrelationMatrices.correlation_type == 'price',
                CorrelationMatrices.variable1 == 'close',
                CorrelationMatrices.variable2 == 'close',
                CorrelationMatrices.correlation_method == 'pearson',
                CorrelationMatrices.window_size == 30
            ).first()
            
            if existing:
                # Mettre à jour la corrélation existante
                existing.correlation_value = correlation_value
                existing.created_at = datetime.now()
                logger.debug(f"Corrélation mise à jour pour {symbol}: {correlation_value:.4f}")
            else:
                # Créer une nouvelle corrélation
                new_correlation = CorrelationMatrices(
                    symbol=symbol,
                    date=datetime.now().date(),
                    correlation_type='price',
                    variable1='close',
                    variable2='close',
                    correlation_value=correlation_value,
                    correlation_method='pearson',
                    window_size=30
                )
                self.db.add(new_correlation)
                logger.debug(f"Nouvelle corrélation créée pour {symbol}: {correlation_value:.4f}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la corrélation {symbol}-{target_symbol}: {e}")
            raise
    
    def _save_correlation_unique(self, composite_symbol: str, symbol1: str, symbol2: str, correlation_value: float):
        """
        Sauvegarde une corrélation unique dans la base de données
        
        Args:
            composite_symbol: Symbole composite (ex: "AAPL_MSFT")
            symbol1: Premier symbole
            symbol2: Deuxième symbole
            correlation_value: Valeur de corrélation
        """
        try:
            # Vérifier si la corrélation existe déjà avec ce symbole composite
            existing = self.db.query(CorrelationMatrices).filter(
                CorrelationMatrices.symbol == composite_symbol,
                CorrelationMatrices.date == datetime.now().date(),
                CorrelationMatrices.correlation_type == 'price',
                CorrelationMatrices.variable1 == 'close',
                CorrelationMatrices.variable2 == 'close',
                CorrelationMatrices.correlation_method == 'pearson',
                CorrelationMatrices.window_size == 30
            ).first()
            
            if existing:
                # Mettre à jour la corrélation existante
                existing.correlation_value = correlation_value
                existing.created_at = datetime.now()
                logger.debug(f"Corrélation mise à jour pour {composite_symbol}: {correlation_value:.4f}")
            else:
                # Créer une nouvelle corrélation
                new_correlation = CorrelationMatrices(
                    symbol=composite_symbol,
                    date=datetime.now().date(),
                    correlation_type='price',
                    variable1='close',
                    variable2='close',
                    correlation_value=correlation_value,
                    correlation_method='pearson',
                    window_size=30
                )
                self.db.add(new_correlation)
                logger.debug(f"Nouvelle corrélation créée pour {composite_symbol}: {correlation_value:.4f}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la corrélation unique {composite_symbol}: {e}")
            raise
    
    def _calculate_correlations(self, symbol: str, all_symbols: List[str], start_date: Optional[date] = None) -> Dict[str, float]:
        """
        Calcule les corrélations entre un symbole et tous les autres
        
        Args:
            symbol: Symbole de référence
            all_symbols: Liste de tous les symboles
            start_date: Date de début pour le calcul
            
        Returns:
            Dictionnaire avec les corrélations
        """
        import pandas as pd
        import numpy as np
        
        correlations = {}
        
        try:
            # Récupérer les données du symbole de référence
            query = self.db.query(HistoricalData).filter(HistoricalData.symbol == symbol)
            if start_date:
                query = query.filter(HistoricalData.date >= start_date)
            
            ref_data = query.order_by(HistoricalData.date.asc()).all()
            
            if len(ref_data) < 30:
                return correlations
            
            ref_df = pd.DataFrame([{
                'date': d.date,
                'close': float(d.close)
            } for d in ref_data])
            
            # Calculer les corrélations avec chaque autre symbole
            for other_symbol in all_symbols:
                if other_symbol == symbol:
                    continue
                
                try:
                    # Récupérer les données de l'autre symbole
                    other_query = self.db.query(HistoricalData).filter(HistoricalData.symbol == other_symbol)
                    if start_date:
                        other_query = other_query.filter(HistoricalData.date >= start_date)
                    
                    other_data = other_query.order_by(HistoricalData.date.asc()).all()
                    
                    if len(other_data) < 30:
                        correlations[other_symbol] = None
                        continue
                    
                    other_df = pd.DataFrame([{
                        'date': d.date,
                        'close': float(d.close)
                        } for d in other_data])
                    
                    # Fusionner les données sur les dates communes
                    merged = pd.merge(ref_df, other_df, on='date', suffixes=('_ref', '_other'))
                    
                    if len(merged) < 20:  # Minimum pour une corrélation fiable
                        correlations[other_symbol] = None
                        continue
                    
                    # Calculer la corrélation
                    correlation = merged['close_ref'].corr(merged['close_other'])
                    correlations[other_symbol] = correlation if not np.isnan(correlation) else None
                    
                except Exception as e:
                    logger.error(f"Erreur lors du calcul de corrélation entre {symbol} et {other_symbol}: {e}")
                    correlations[other_symbol] = None
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des corrélations pour {symbol}: {e}")
        
        return correlations
    
    def recalculate_all_indicators(self, symbols: List[str], start_date: Optional[date] = None) -> Dict[str, Any]:
        """
        Recalcule tous les indicateurs (techniques, sentiment, corrélations) pour une liste de symboles
        
        Args:
            symbols: Liste des symboles à traiter
            start_date: Date de début pour le recalcul (optionnel)
            
        Returns:
            Dictionnaire avec les résultats complets du recalcul
        """
        logger.info(f"Début du recalcul complet des indicateurs pour {len(symbols)} symboles")
        
        results = {
            'success': True,
            'symbols_processed': 0,
            'technical_indicators': {'success': 0, 'failed': 0},
            'sentiment_indicators': {'success': 0, 'failed': 0},
            'correlations': {'success': 0, 'failed': 0},
            'errors': []
        }
        
        # Recalculer les indicateurs techniques
        logger.info("1. Recalcul des indicateurs techniques...")
        for symbol in symbols:
            try:
                result = self.recalculate_technical_indicators(symbol, start_date)
                if result['success']:
                    results['technical_indicators']['success'] += 1
                else:
                    results['technical_indicators']['failed'] += 1
                    results['errors'].append(f"Technical indicators for {symbol}: {result['error']}")
            except Exception as e:
                results['technical_indicators']['failed'] += 1
                results['errors'].append(f"Technical indicators for {symbol}: {str(e)}")
        
        # Recalculer les indicateurs de sentiment
        logger.info("2. Recalcul des indicateurs de sentiment...")
        for symbol in symbols:
            try:
                result = self.recalculate_sentiment_indicators(symbol, start_date)
                if result['success']:
                    results['sentiment_indicators']['success'] += 1
                else:
                    results['sentiment_indicators']['failed'] += 1
                    results['errors'].append(f"Sentiment indicators for {symbol}: {result['error']}")
            except Exception as e:
                results['sentiment_indicators']['failed'] += 1
                results['errors'].append(f"Sentiment indicators for {symbol}: {str(e)}")
        
        # Recalculer les corrélations
        logger.info("3. Recalcul des corrélations...")
        try:
            result = self.recalculate_correlations(symbols, start_date)
            if result['success']:
                results['correlations']['success'] = result['processed_correlations']
            else:
                results['correlations']['failed'] = 1
                results['errors'].append(f"Correlations: {result['error']}")
        except Exception as e:
            results['correlations']['failed'] = 1
            results['errors'].append(f"Correlations: {str(e)}")
        
        results['symbols_processed'] = len(symbols)
        
        # Déterminer le succès global
        total_failed = (
            results['technical_indicators']['failed'] +
            results['sentiment_indicators']['failed'] +
            results['correlations']['failed']
        )
        
        if total_failed > len(symbols) * 0.5:  # Plus de 50% d'échecs
            results['success'] = False
        
        logger.info(f"Recalcul complet terminé: {results}")
        
        return results
