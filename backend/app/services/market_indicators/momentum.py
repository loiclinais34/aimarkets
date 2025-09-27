"""
Indicateurs de momentum pour l'analyse de marché.

Ce module implémente des méthodes pour analyser le momentum
des prix, volumes et autres indicateurs de marché.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
import yfinance as yf
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class MomentumIndicators:
    """
    Classe pour analyser les indicateurs de momentum.
    
    Cette classe fournit des méthodes pour calculer et analyser
    différents types de momentum.
    """
    
    @staticmethod
    def calculate_price_momentum(prices: pd.Series, periods: List[int] = [1, 5, 10, 20, 50]) -> Dict[str, pd.Series]:
        """
        Calcule le momentum des prix sur différentes périodes.
        
        Args:
            prices: Série de prix
            periods: Liste des périodes de calcul
            
        Returns:
            Dictionnaire contenant les momentum pour chaque période
        """
        try:
            momentum_indicators = {}
            
            for period in periods:
                if period <= len(prices):
                    # Momentum simple
                    momentum = (prices / prices.shift(period) - 1) * 100
                    momentum_indicators[f"momentum_{period}"] = momentum
                    
                    # Momentum normalisé
                    momentum_norm = (prices - prices.shift(period)) / prices.shift(period).rolling(window=period).std()
                    momentum_indicators[f"momentum_{period}_norm"] = momentum_norm
            
            return momentum_indicators
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du momentum des prix: {e}")
            return {}
    
    @staticmethod
    def calculate_volume_momentum(volume: pd.Series, prices: pd.Series, 
                                periods: List[int] = [5, 10, 20]) -> Dict[str, pd.Series]:
        """
        Calcule le momentum du volume.
        
        Args:
            volume: Série des volumes
            prices: Série des prix
            periods: Liste des périodes de calcul
            
        Returns:
            Dictionnaire contenant les indicateurs de momentum du volume
        """
        try:
            volume_momentum = {}
            
            for period in periods:
                if period <= len(volume):
                    # Momentum du volume
                    vol_momentum = (volume / volume.shift(period) - 1) * 100
                    volume_momentum[f"volume_momentum_{period}"] = vol_momentum
                    
                    # Ratio volume/prix
                    price_change = (prices / prices.shift(period) - 1) * 100
                    volume_price_ratio = vol_momentum / (price_change + 1e-8)  # Éviter la division par zéro
                    volume_momentum[f"volume_price_ratio_{period}"] = volume_price_ratio
                    
                    # Volume relatif
                    avg_volume = volume.rolling(window=period).mean()
                    relative_volume = volume / avg_volume
                    volume_momentum[f"relative_volume_{period}"] = relative_volume
            
            return volume_momentum
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du momentum du volume: {e}")
            return {}
    
    @staticmethod
    def calculate_earnings_momentum(earnings: pd.Series, periods: List[int] = [1, 4]) -> Dict[str, pd.Series]:
        """
        Calcule le momentum des bénéfices.
        
        Args:
            earnings: Série des bénéfices
            periods: Liste des périodes de calcul
            
        Returns:
            Dictionnaire contenant les indicateurs de momentum des bénéfices
        """
        try:
            earnings_momentum = {}
            
            for period in periods:
                if period <= len(earnings):
                    # Momentum des bénéfices
                    earnings_mom = (earnings / earnings.shift(period) - 1) * 100
                    earnings_momentum[f"earnings_momentum_{period}"] = earnings_mom
                    
                    # Accélération des bénéfices
                    if period > 1:
                        earnings_accel = earnings_mom - earnings_mom.shift(period)
                        earnings_momentum[f"earnings_acceleration_{period}"] = earnings_accel
            
            return earnings_momentum
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du momentum des bénéfices: {e}")
            return {}
    
    @staticmethod
    def calculate_relative_strength(prices: pd.Series, benchmark_prices: pd.Series, 
                                  period: int = 20) -> pd.Series:
        """
        Calcule la force relative par rapport à un benchmark.
        
        Args:
            prices: Série de prix de l'actif
            benchmark_prices: Série de prix du benchmark
            period: Période de calcul
            
        Returns:
            Série de la force relative
        """
        try:
            # Aligner les données
            aligned_data = pd.DataFrame({
                'asset': prices,
                'benchmark': benchmark_prices
            }).dropna()
            
            if len(aligned_data) < period:
                return pd.Series(dtype=float)
            
            # Calculer les rendements
            asset_returns = aligned_data['asset'].pct_change()
            benchmark_returns = aligned_data['benchmark'].pct_change()
            
            # Calculer la force relative
            relative_strength = (1 + asset_returns).rolling(window=period).apply(np.prod) / \
                              (1 + benchmark_returns).rolling(window=period).apply(np.prod)
            
            return relative_strength
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la force relative: {e}")
            return pd.Series(dtype=float)
    
    @staticmethod
    def calculate_momentum_score(prices: pd.Series, volume: Optional[pd.Series] = None,
                               periods: List[int] = [5, 10, 20, 50]) -> Dict[str, Any]:
        """
        Calcule un score de momentum composite.
        
        Args:
            prices: Série de prix
            volume: Série des volumes (optionnel)
            periods: Liste des périodes de calcul
            
        Returns:
            Dictionnaire contenant le score de momentum
        """
        try:
            # Calculer le momentum des prix
            price_momentum = MomentumIndicators.calculate_price_momentum(prices, periods)
            
            # Calculer le score de momentum
            momentum_scores = []
            weights = [0.4, 0.3, 0.2, 0.1]  # Poids pour les différentes périodes
            
            for i, period in enumerate(periods):
                if f"momentum_{period}" in price_momentum:
                    momentum = price_momentum[f"momentum_{period}"].iloc[-1]
                    if not np.isnan(momentum):
                        momentum_scores.append(momentum * weights[i])
            
            # Score composite
            composite_score = np.sum(momentum_scores) if momentum_scores else 0.0
            
            # Classification du momentum
            if composite_score > 5:
                momentum_class = "Strong Positive"
            elif composite_score > 2:
                momentum_class = "Positive"
            elif composite_score > -2:
                momentum_class = "Neutral"
            elif composite_score > -5:
                momentum_class = "Negative"
            else:
                momentum_class = "Strong Negative"
            
            # Ajouter le momentum du volume si disponible
            volume_momentum_score = 0.0
            if volume is not None:
                volume_momentum = MomentumIndicators.calculate_volume_momentum(volume, prices, [10, 20])
                if "volume_momentum_10" in volume_momentum:
                    vol_mom = volume_momentum["volume_momentum_10"].iloc[-1]
                    if not np.isnan(vol_mom):
                        volume_momentum_score = vol_mom
            
            return {
                "composite_score": composite_score,
                "momentum_class": momentum_class,
                "individual_scores": momentum_scores,
                "volume_momentum_score": volume_momentum_score,
                "periods_used": periods,
                "weights": weights
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du score de momentum: {e}")
            return {
                "composite_score": 0.0,
                "momentum_class": "Unknown",
                "individual_scores": [],
                "volume_momentum_score": 0.0,
                "periods_used": periods,
                "weights": []
            }
    
    @staticmethod
    def calculate_momentum_divergence(prices: pd.Series, momentum: pd.Series, 
                                    period: int = 20) -> Dict[str, Any]:
        """
        Calcule la divergence entre les prix et le momentum.
        
        Args:
            prices: Série de prix
            momentum: Série de momentum
            period: Période de calcul
            
        Returns:
            Dictionnaire contenant l'analyse de divergence
        """
        try:
            # Aligner les données
            aligned_data = pd.DataFrame({
                'prices': prices,
                'momentum': momentum
            }).dropna()
            
            if len(aligned_data) < period:
                return {"divergence": 0.0, "signal": "No Data"}
            
            # Calculer les tendances
            price_trend = aligned_data['prices'].rolling(window=period).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0]
            )
            momentum_trend = aligned_data['momentum'].rolling(window=period).apply(
                lambda x: np.polyfit(range(len(x)), x, 1)[0]
            )
            
            # Calculer la divergence
            divergence = price_trend.iloc[-1] - momentum_trend.iloc[-1]
            
            # Classification de la divergence
            if divergence > 0.1:
                signal = "Bearish Divergence"
            elif divergence < -0.1:
                signal = "Bullish Divergence"
            else:
                signal = "No Divergence"
            
            return {
                "divergence": divergence,
                "signal": signal,
                "price_trend": price_trend.iloc[-1],
                "momentum_trend": momentum_trend.iloc[-1],
                "period": period
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la divergence: {e}")
            return {
                "divergence": 0.0,
                "signal": "Error",
                "price_trend": 0.0,
                "momentum_trend": 0.0,
                "period": period
            }
    
    @staticmethod
    def calculate_momentum_ranking(returns: pd.DataFrame, period: int = 20) -> Dict[str, Any]:
        """
        Calcule le classement de momentum pour plusieurs actifs.
        
        Args:
            returns: DataFrame des rendements
            period: Période de calcul
            
        Returns:
            Dictionnaire contenant le classement
        """
        try:
            # Calculer le momentum pour chaque actif
            momentum_scores = {}
            
            for symbol in returns.columns:
                # Calculer le rendement cumulé sur la période
                cumulative_return = (1 + returns[symbol]).rolling(window=period).apply(np.prod) - 1
                momentum_scores[symbol] = cumulative_return.iloc[-1] if not cumulative_return.empty else 0.0
            
            # Trier par momentum
            sorted_momentum = sorted(momentum_scores.items(), key=lambda x: x[1], reverse=True)
            
            # Créer le classement
            ranking = []
            for i, (symbol, score) in enumerate(sorted_momentum):
                ranking.append({
                    "rank": i + 1,
                    "symbol": symbol,
                    "momentum_score": score,
                    "percentile": (len(sorted_momentum) - i) / len(sorted_momentum) * 100
                })
            
            return {
                "ranking": ranking,
                "top_performers": ranking[:5],
                "bottom_performers": ranking[-5:],
                "average_momentum": np.mean(list(momentum_scores.values())),
                "momentum_std": np.std(list(momentum_scores.values())),
                "period": period
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du classement de momentum: {e}")
            return {
                "ranking": [],
                "top_performers": [],
                "bottom_performers": [],
                "average_momentum": 0.0,
                "momentum_std": 0.0,
                "period": period
            }
    
    @staticmethod
    def comprehensive_momentum_analysis(prices: pd.Series, volume: Optional[pd.Series] = None,
                                      benchmark_prices: Optional[pd.Series] = None) -> Dict[str, Any]:
        """
        Effectue une analyse complète du momentum.
        
        Args:
            prices: Série de prix
            volume: Série des volumes (optionnel)
            benchmark_prices: Série de prix du benchmark (optionnel)
            
        Returns:
            Dictionnaire contenant l'analyse complète
        """
        try:
            # Momentum des prix
            price_momentum = MomentumIndicators.calculate_price_momentum(prices)
            
            # Momentum du volume
            volume_momentum = {}
            if volume is not None:
                volume_momentum = MomentumIndicators.calculate_volume_momentum(volume, prices)
            
            # Score de momentum composite
            momentum_score = MomentumIndicators.calculate_momentum_score(prices, volume)
            
            # Force relative
            relative_strength = pd.Series(dtype=float)
            if benchmark_prices is not None:
                relative_strength = MomentumIndicators.calculate_relative_strength(prices, benchmark_prices)
            
            # Divergence de momentum
            momentum_divergence = {}
            if "momentum_20" in price_momentum:
                momentum_divergence = MomentumIndicators.calculate_momentum_divergence(
                    prices, price_momentum["momentum_20"]
                )
            
            return {
                "price_momentum": price_momentum,
                "volume_momentum": volume_momentum,
                "momentum_score": momentum_score,
                "relative_strength": relative_strength,
                "momentum_divergence": momentum_divergence,
                "analysis_timestamp": pd.Timestamp.now(),
                "data_period": {
                    "start": prices.index[0],
                    "end": prices.index[-1],
                    "duration_days": (prices.index[-1] - prices.index[0]).days
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse complète du momentum: {e}")
            return {
                "price_momentum": {},
                "volume_momentum": {},
                "momentum_score": {},
                "relative_strength": pd.Series(dtype=float),
                "momentum_divergence": {},
                "analysis_timestamp": pd.Timestamp.now(),
                "data_period": {},
                "error": str(e)
            }
