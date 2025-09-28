"""
Indicateurs techniques pour l'analyse de trading.

Ce module implémente les principaux indicateurs techniques utilisés
dans l'analyse de trading conventionnelle.
"""

import pandas as pd
import numpy as np
import talib
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """
    Classe pour calculer les indicateurs techniques.
    
    Cette classe fournit des méthodes pour calculer les principaux
    indicateurs techniques utilisés dans l'analyse de trading.
    """
    
    @staticmethod
    def rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calcule le Relative Strength Index (RSI).
        
        Args:
            prices: Série de prix (généralement les prix de clôture)
            period: Période de calcul (défaut: 14)
            
        Returns:
            Série pandas contenant les valeurs RSI
        """
        try:
            # Convertir en float64 pour TA-Lib
            prices_float = prices.astype('float64')
            return pd.Series(talib.RSI(prices_float.values, timeperiod=period), index=prices.index)
        except Exception as e:
            logger.error(f"Erreur lors du calcul du RSI: {e}")
            return pd.Series(index=prices.index, dtype=float)
    
    @staticmethod
    def macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """
        Calcule le MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Série de prix de clôture
            fast: Période de la moyenne mobile rapide
            slow: Période de la moyenne mobile lente
            signal: Période de la ligne de signal
            
        Returns:
            Dictionnaire contenant MACD, signal et histogramme
        """
        try:
            # Convertir en float64 pour TA-Lib
            prices_float = prices.astype('float64')
            macd_line, signal_line, histogram = talib.MACD(
                prices_float.values, 
                fastperiod=fast, 
                slowperiod=slow, 
                signalperiod=signal
            )
            
            return {
                'macd': pd.Series(macd_line, index=prices.index),
                'signal': pd.Series(signal_line, index=prices.index),
                'histogram': pd.Series(histogram, index=prices.index)
            }
        except Exception as e:
            logger.error(f"Erreur lors du calcul du MACD: {e}")
            return {
                'macd': pd.Series(index=prices.index, dtype=float),
                'signal': pd.Series(index=prices.index, dtype=float),
                'histogram': pd.Series(index=prices.index, dtype=float)
            }
    
    @staticmethod
    def bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, pd.Series]:
        """
        Calcule les Bandes de Bollinger.
        
        Args:
            prices: Série de prix de clôture
            period: Période de la moyenne mobile
            std_dev: Nombre d'écarts-types
            
        Returns:
            Dictionnaire contenant les bandes supérieure, moyenne et inférieure
        """
        try:
            # Convertir en float64 pour TA-Lib
            prices_float = prices.astype('float64')
            upper, middle, lower = talib.BBANDS(
                prices_float.values, 
                timeperiod=period, 
                nbdevup=std_dev, 
                nbdevdn=std_dev
            )
            
            return {
                'upper': pd.Series(upper, index=prices.index),
                'middle': pd.Series(middle, index=prices.index),
                'lower': pd.Series(lower, index=prices.index)
            }
        except Exception as e:
            logger.error(f"Erreur lors du calcul des Bandes de Bollinger: {e}")
            return {
                'upper': pd.Series(index=prices.index, dtype=float),
                'middle': pd.Series(index=prices.index, dtype=float),
                'lower': pd.Series(index=prices.index, dtype=float)
            }
    
    @staticmethod
    def stochastic(high: pd.Series, low: pd.Series, close: pd.Series, 
                   k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """
        Calcule l'oscillateur stochastique.
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            k_period: Période pour %K
            d_period: Période pour %D
            
        Returns:
            Dictionnaire contenant %K et %D
        """
        try:
            # Convertir en float64 pour TA-Lib
            high_float = high.astype('float64')
            low_float = low.astype('float64')
            close_float = close.astype('float64')
            k_percent, d_percent = talib.STOCH(
                high_float.values, 
                low_float.values, 
                close_float.values,
                fastk_period=k_period,
                slowk_period=d_period,
                slowd_period=d_period
            )
            
            return {
                'k_percent': pd.Series(k_percent, index=close.index),
                'd_percent': pd.Series(d_percent, index=close.index)
            }
        except Exception as e:
            logger.error(f"Erreur lors du calcul du stochastique: {e}")
            return {
                'k_percent': pd.Series(index=close.index, dtype=float),
                'd_percent': pd.Series(index=close.index, dtype=float)
            }
    
    @staticmethod
    def williams_r(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Calcule le Williams %R.
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            period: Période de calcul
            
        Returns:
            Série pandas contenant les valeurs Williams %R
        """
        try:
            # Convertir en float64 pour TA-Lib
            high_float = high.astype('float64')
            low_float = low.astype('float64')
            close_float = close.astype('float64')
            return pd.Series(
                talib.WILLR(high_float.values, low_float.values, close_float.values, timeperiod=period),
                index=close.index
            )
        except Exception as e:
            logger.error(f"Erreur lors du calcul du Williams %R: {e}")
            return pd.Series(index=close.index, dtype=float)
    
    @staticmethod
    def cci(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Calcule le Commodity Channel Index (CCI).
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            period: Période de calcul
            
        Returns:
            Série pandas contenant les valeurs CCI
        """
        try:
            # Convertir en float64 pour TA-Lib
            high_float = high.astype('float64')
            low_float = low.astype('float64')
            close_float = close.astype('float64')
            return pd.Series(
                talib.CCI(high_float.values, low_float.values, close_float.values, timeperiod=period),
                index=close.index
            )
        except Exception as e:
            logger.error(f"Erreur lors du calcul du CCI: {e}")
            return pd.Series(index=close.index, dtype=float)
    
    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> Dict[str, pd.Series]:
        """
        Calcule l'Average Directional Index (ADX).
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            period: Période de calcul
            
        Returns:
            Dictionnaire contenant ADX, +DI et -DI
        """
        try:
            # Convertir en float64 pour TA-Lib
            high_float = high.astype('float64')
            low_float = low.astype('float64')
            close_float = close.astype('float64')
            adx_values = talib.ADX(high_float.values, low_float.values, close_float.values, timeperiod=period)
            plus_di = talib.PLUS_DI(high_float.values, low_float.values, close_float.values, timeperiod=period)
            minus_di = talib.MINUS_DI(high_float.values, low_float.values, close_float.values, timeperiod=period)
            
            return {
                'adx': pd.Series(adx_values, index=close.index),
                'plus_di': pd.Series(plus_di, index=close.index),
                'minus_di': pd.Series(minus_di, index=close.index)
            }
        except Exception as e:
            logger.error(f"Erreur lors du calcul de l'ADX: {e}")
            return {
                'adx': pd.Series(index=close.index, dtype=float),
                'plus_di': pd.Series(index=close.index, dtype=float),
                'minus_di': pd.Series(index=close.index, dtype=float)
            }
    
    @staticmethod
    def parabolic_sar(high: pd.Series, low: pd.Series, acceleration: float = 0.02, 
                     maximum: float = 0.2) -> pd.Series:
        """
        Calcule le Parabolic SAR.
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            acceleration: Facteur d'accélération initial
            maximum: Facteur d'accélération maximum
            
        Returns:
            Série pandas contenant les valeurs Parabolic SAR
        """
        try:
            # Convertir en float64 pour TA-Lib
            high_float = high.astype('float64')
            low_float = low.astype('float64')
            return pd.Series(
                talib.SAR(high_float.values, low_float.values, acceleration=acceleration, maximum=maximum),
                index=high.index
            )
        except Exception as e:
            logger.error(f"Erreur lors du calcul du Parabolic SAR: {e}")
            return pd.Series(index=high.index, dtype=float)
    
    @staticmethod
    def ichimoku(high: pd.Series, low: pd.Series, close: pd.Series, 
                tenkan_period: int = 9, kijun_period: int = 26, 
                senkou_b_period: int = 52) -> Dict[str, pd.Series]:
        """
        Calcule l'Ichimoku Cloud.
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            tenkan_period: Période pour Tenkan-sen
            kijun_period: Période pour Kijun-sen
            senkou_b_period: Période pour Senkou Span B
            
        Returns:
            Dictionnaire contenant tous les composants Ichimoku
        """
        try:
            # Tenkan-sen (ligne de conversion)
            tenkan_high = high.rolling(window=tenkan_period).max()
            tenkan_low = low.rolling(window=tenkan_period).min()
            tenkan_sen = (tenkan_high + tenkan_low) / 2
            
            # Kijun-sen (ligne de base)
            kijun_high = high.rolling(window=kijun_period).max()
            kijun_low = low.rolling(window=kijun_period).min()
            kijun_sen = (kijun_high + kijun_low) / 2
            
            # Senkou Span A (première ligne du nuage)
            senkou_span_a = ((tenkan_sen + kijun_sen) / 2).shift(kijun_period)
            
            # Senkou Span B (deuxième ligne du nuage)
            senkou_b_high = high.rolling(window=senkou_b_period).max()
            senkou_b_low = low.rolling(window=senkou_b_period).min()
            senkou_span_b = ((senkou_b_high + senkou_b_low) / 2).shift(kijun_period)
            
            # Chikou Span (ligne de retard)
            chikou_span = close.shift(-kijun_period)
            
            return {
                'tenkan_sen': tenkan_sen,
                'kijun_sen': kijun_sen,
                'senkou_span_a': senkou_span_a,
                'senkou_span_b': senkou_span_b,
                'chikou_span': chikou_span
            }
        except Exception as e:
            logger.error(f"Erreur lors du calcul de l'Ichimoku: {e}")
            return {
                'tenkan_sen': pd.Series(index=close.index, dtype=float),
                'kijun_sen': pd.Series(index=close.index, dtype=float),
                'senkou_span_a': pd.Series(index=close.index, dtype=float),
                'senkou_span_b': pd.Series(index=close.index, dtype=float),
                'chikou_span': pd.Series(index=close.index, dtype=float)
            }
    
    @staticmethod
    def calculate_all_indicators(high: pd.Series, low: pd.Series, close: pd.Series, 
                                volume: Optional[pd.Series] = None) -> Dict[str, any]:
        """
        Calcule tous les indicateurs techniques disponibles.
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            volume: Série des volumes (optionnel)
            
        Returns:
            Dictionnaire contenant tous les indicateurs calculés
        """
        try:
            indicators = {}
            
            # Indicateurs de tendance (moyennes mobiles)
            indicators['sma_20'] = close.rolling(window=20).mean()
            indicators['sma_50'] = close.rolling(window=50).mean()
            indicators['sma_200'] = close.rolling(window=200).mean()
            indicators['ema_20'] = close.ewm(span=20).mean()
            indicators['ema_50'] = close.ewm(span=50).mean()
            
            # Indicateurs de momentum
            indicators['rsi'] = TechnicalIndicators.rsi(close)
            indicators['macd'] = TechnicalIndicators.macd(close)
            indicators['stochastic'] = TechnicalIndicators.stochastic(high, low, close)
            indicators['williams_r'] = TechnicalIndicators.williams_r(high, low, close)
            indicators['cci'] = TechnicalIndicators.cci(high, low, close)
            
            # Indicateurs de volatilité
            indicators['bollinger_bands'] = TechnicalIndicators.bollinger_bands(close)
            
            # Indicateurs de tendance
            indicators['adx'] = TechnicalIndicators.adx(high, low, close)
            indicators['parabolic_sar'] = TechnicalIndicators.parabolic_sar(high, low)
            indicators['ichimoku'] = TechnicalIndicators.ichimoku(high, low, close)
            
            return indicators
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de tous les indicateurs: {e}")
            return {}
