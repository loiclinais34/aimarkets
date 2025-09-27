"""
Indicateurs de volatilité pour l'analyse de marché.

Ce module implémente des méthodes pour analyser la volatilité
du marché et ses implications.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
import yfinance as yf
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class VolatilityIndicators:
    """
    Classe pour analyser les indicateurs de volatilité du marché.
    
    Cette classe fournit des méthodes pour calculer et analyser
    différents types de volatilité.
    """
    
    @staticmethod
    def get_vix_data(period: str = "1y") -> pd.DataFrame:
        """
        Récupère les données du VIX (indice de peur).
        
        Args:
            period: Période des données ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
            
        Returns:
            DataFrame contenant les données du VIX
        """
        try:
            vix = yf.Ticker("^VIX")
            data = vix.history(period=period)
            return data
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données VIX: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def calculate_historical_volatility(prices: pd.Series, window: int = 20, 
                                      annualized: bool = True) -> pd.Series:
        """
        Calcule la volatilité historique.
        
        Args:
            prices: Série de prix
            window: Fenêtre de calcul
            annualized: Si True, annualise la volatilité
            
        Returns:
            Série de la volatilité historique
        """
        try:
            # Calculer les rendements
            returns = np.log(prices / prices.shift(1))
            
            # Calculer la volatilité mobile
            volatility = returns.rolling(window=window).std()
            
            # Annualiser si demandé
            if annualized:
                volatility = volatility * np.sqrt(252)
            
            return volatility
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la volatilité historique: {e}")
            return pd.Series(dtype=float)
    
    @staticmethod
    def calculate_implied_volatility(option_prices: pd.DataFrame, 
                                   underlying_price: float, strike_price: float,
                                   risk_free_rate: float = 0.02, 
                                   time_to_expiry: float = 0.25) -> float:
        """
        Calcule la volatilité implicite à partir des prix d'options.
        
        Args:
            option_prices: DataFrame des prix d'options
            underlying_price: Prix du sous-jacent
            strike_price: Prix d'exercice
            risk_free_rate: Taux sans risque
            time_to_expiry: Temps jusqu'à l'expiration (en années)
            
        Returns:
            Volatilité implicite
        """
        try:
            # Utiliser la formule de Black-Scholes inversée
            # Approximation simple pour la volatilité implicite
            
            # Calculer le prix moyen de l'option
            avg_option_price = option_prices.mean().mean()
            
            # Approximation de la volatilité implicite
            # Formule simplifiée pour l'approximation
            d1 = (np.log(underlying_price / strike_price) + 
                  (risk_free_rate + 0.5 * 0.2**2) * time_to_expiry) / \
                 (0.2 * np.sqrt(time_to_expiry))
            
            # Approximation itérative simple
            implied_vol = 0.2  # Valeur initiale
            tolerance = 0.001
            max_iterations = 100
            
            for i in range(max_iterations):
                # Calculer le prix Black-Scholes
                d1 = (np.log(underlying_price / strike_price) + 
                      (risk_free_rate + 0.5 * implied_vol**2) * time_to_expiry) / \
                     (implied_vol * np.sqrt(time_to_expiry))
                d2 = d1 - implied_vol * np.sqrt(time_to_expiry)
                
                # Prix de l'option call
                from scipy.stats import norm
                bs_price = (underlying_price * norm.cdf(d1) - 
                           strike_price * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2))
                
                # Ajuster la volatilité
                if abs(bs_price - avg_option_price) < tolerance:
                    break
                
                implied_vol += (avg_option_price - bs_price) / 1000  # Ajustement simple
            
            return max(0.01, min(2.0, implied_vol))  # Limiter entre 1% et 200%
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la volatilité implicite: {e}")
            return 0.2  # Valeur par défaut
    
    @staticmethod
    def calculate_volatility_ratio(current_volatility: float, 
                                 historical_volatility: pd.Series) -> Dict[str, float]:
        """
        Calcule le ratio de volatilité actuelle par rapport à l'historique.
        
        Args:
            current_volatility: Volatilité actuelle
            historical_volatility: Série de volatilité historique
            
        Returns:
            Dictionnaire contenant les ratios
        """
        try:
            if historical_volatility.empty:
                return {"ratio": 1.0, "percentile": 50.0}
            
            # Calculer les statistiques
            mean_vol = historical_volatility.mean()
            median_vol = historical_volatility.median()
            std_vol = historical_volatility.std()
            
            # Ratios
            ratio_to_mean = current_volatility / mean_vol if mean_vol > 0 else 1.0
            ratio_to_median = current_volatility / median_vol if median_vol > 0 else 1.0
            
            # Percentile
            percentile = (historical_volatility <= current_volatility).mean() * 100
            
            # Z-score
            z_score = (current_volatility - mean_vol) / std_vol if std_vol > 0 else 0.0
            
            return {
                "ratio_to_mean": ratio_to_mean,
                "ratio_to_median": ratio_to_median,
                "percentile": percentile,
                "z_score": z_score,
                "current_volatility": current_volatility,
                "mean_volatility": mean_vol,
                "median_volatility": median_vol,
                "std_volatility": std_vol
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du ratio de volatilité: {e}")
            return {"ratio": 1.0, "percentile": 50.0}
    
    @staticmethod
    def analyze_volatility_regimes(volatility: pd.Series, n_regimes: int = 3) -> Dict[str, Any]:
        """
        Analyse les régimes de volatilité.
        
        Args:
            volatility: Série de volatilité
            n_regimes: Nombre de régimes à identifier
            
        Returns:
            Dictionnaire contenant l'analyse des régimes
        """
        try:
            from sklearn.mixture import GaussianMixture
            
            # Préparer les données
            vol_clean = volatility.dropna()
            
            if len(vol_clean) < 50:
                raise ValueError("Pas assez de données pour analyser les régimes")
            
            # Identifier les régimes
            gmm = GaussianMixture(n_components=n_regimes, random_state=42)
            regimes = gmm.fit_predict(vol_clean.values.reshape(-1, 1))
            
            # Analyser chaque régime
            regime_analysis = {}
            for regime in range(n_regimes):
                regime_data = vol_clean[regimes == regime]
                
                regime_analysis[f"regime_{regime}"] = {
                    "count": len(regime_data),
                    "percentage": len(regime_data) / len(vol_clean) * 100,
                    "mean_volatility": regime_data.mean(),
                    "std_volatility": regime_data.std(),
                    "min_volatility": regime_data.min(),
                    "max_volatility": regime_data.max()
                }
            
            # Identifier le régime actuel
            current_regime = regimes[-1] if len(regimes) > 0 else 0
            
            return {
                "regimes": regimes,
                "regime_analysis": regime_analysis,
                "current_regime": current_regime,
                "n_regimes": n_regimes,
                "model": gmm
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des régimes de volatilité: {e}")
            return {
                "regimes": np.array([]),
                "regime_analysis": {},
                "current_regime": 0,
                "n_regimes": n_regimes,
                "error": str(e)
            }
    
    @staticmethod
    def calculate_volatility_skew(returns: pd.Series, window: int = 20) -> pd.Series:
        """
        Calcule le skew de volatilité (différence entre volatilité des rendements positifs et négatifs).
        
        Args:
            returns: Série des rendements
            window: Fenêtre de calcul
            
        Returns:
            Série du skew de volatilité
        """
        try:
            # Séparer les rendements positifs et négatifs
            positive_returns = returns.where(returns > 0, 0)
            negative_returns = returns.where(returns < 0, 0)
            
            # Calculer la volatilité pour chaque type
            pos_vol = positive_returns.rolling(window=window).std()
            neg_vol = negative_returns.rolling(window=window).std()
            
            # Calculer le skew
            volatility_skew = pos_vol - neg_vol
            
            return volatility_skew
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du skew de volatilité: {e}")
            return pd.Series(dtype=float)
    
    @staticmethod
    def calculate_volatility_risk_premium(current_volatility: float, 
                                        implied_volatility: float) -> Dict[str, float]:
        """
        Calcule la prime de risque de volatilité.
        
        Args:
            current_volatility: Volatilité actuelle
            implied_volatility: Volatilité implicite
            
        Returns:
            Dictionnaire contenant la prime de risque
        """
        try:
            # Prime de risque de volatilité
            risk_premium = implied_volatility - current_volatility
            
            # Ratio de la prime
            premium_ratio = risk_premium / current_volatility if current_volatility > 0 else 0.0
            
            # Classification du niveau de risque
            if risk_premium > 0.05:
                risk_level = "High"
            elif risk_premium > 0.02:
                risk_level = "Medium"
            elif risk_premium > 0:
                risk_level = "Low"
            else:
                risk_level = "Negative"
            
            return {
                "risk_premium": risk_premium,
                "premium_ratio": premium_ratio,
                "risk_level": risk_level,
                "current_volatility": current_volatility,
                "implied_volatility": implied_volatility
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la prime de risque: {e}")
            return {
                "risk_premium": 0.0,
                "premium_ratio": 0.0,
                "risk_level": "Unknown",
                "current_volatility": 0.0,
                "implied_volatility": 0.0
            }
    
    @staticmethod
    def comprehensive_volatility_analysis(prices: pd.Series, returns: pd.Series,
                                        window: int = 20) -> Dict[str, Any]:
        """
        Effectue une analyse complète de la volatilité.
        
        Args:
            prices: Série de prix
            returns: Série des rendements
            window: Fenêtre de calcul
            
        Returns:
            Dictionnaire contenant l'analyse complète
        """
        try:
            # Volatilité historique
            historical_vol = VolatilityIndicators.calculate_historical_volatility(prices, window)
            
            # Volatilité actuelle
            current_vol = historical_vol.iloc[-1] if not historical_vol.empty else 0.0
            
            # Ratio de volatilité
            vol_ratio = VolatilityIndicators.calculate_volatility_ratio(current_vol, historical_vol)
            
            # Analyse des régimes
            regime_analysis = VolatilityIndicators.analyze_volatility_regimes(historical_vol)
            
            # Skew de volatilité
            vol_skew = VolatilityIndicators.calculate_volatility_skew(returns, window)
            
            # Données VIX
            vix_data = VolatilityIndicators.get_vix_data("1y")
            current_vix = vix_data['Close'].iloc[-1] if not vix_data.empty else 0.0
            
            # Prime de risque de volatilité (approximation)
            implied_vol = current_vix / 100  # VIX en pourcentage
            risk_premium = VolatilityIndicators.calculate_volatility_risk_premium(current_vol, implied_vol)
            
            return {
                "historical_volatility": historical_vol,
                "current_volatility": current_vol,
                "volatility_ratio": vol_ratio,
                "regime_analysis": regime_analysis,
                "volatility_skew": vol_skew,
                "vix_data": vix_data,
                "current_vix": current_vix,
                "risk_premium": risk_premium,
                "analysis_timestamp": pd.Timestamp.now(),
                "data_period": {
                    "start": prices.index[0],
                    "end": prices.index[-1],
                    "duration_days": (prices.index[-1] - prices.index[0]).days
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse complète de volatilité: {e}")
            return {
                "historical_volatility": pd.Series(dtype=float),
                "current_volatility": 0.0,
                "volatility_ratio": {},
                "regime_analysis": {},
                "volatility_skew": pd.Series(dtype=float),
                "vix_data": pd.DataFrame(),
                "current_vix": 0.0,
                "risk_premium": {},
                "analysis_timestamp": pd.Timestamp.now(),
                "data_period": {},
                "error": str(e)
            }
