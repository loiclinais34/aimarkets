"""
Modèles GARCH pour l'analyse de volatilité et de sentiment de marché.

Ce module implémente les modèles GARCH (Generalized Autoregressive
Conditional Heteroskedasticity) pour analyser la volatilité des prix.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from arch import arch_model
from arch.univariate import GARCH, EGARCH, GARCH as GJR_GARCH
import warnings

# Supprimer les avertissements de convergence
warnings.filterwarnings('ignore', category=UserWarning)

logger = logging.getLogger(__name__)


class GARCHModels:
    """
    Classe pour ajuster et analyser les modèles GARCH.
    
    Cette classe fournit des méthodes pour ajuster différents types
    de modèles GARCH et extraire des informations sur la volatilité.
    """
    
    @staticmethod
    def calculate_returns(prices: pd.Series, method: str = 'log') -> pd.Series:
        """
        Calcule les rendements à partir des prix.
        
        Args:
            prices: Série de prix
            method: Méthode de calcul ('log' ou 'simple')
            
        Returns:
            Série des rendements
        """
        try:
            # Convertir en float64 pour éviter les erreurs de type
            prices_float = prices.astype('float64')
            
            if method == 'log':
                returns = np.log(prices_float / prices_float.shift(1))
            else:  # simple
                returns = (prices_float - prices_float.shift(1)) / prices_float.shift(1)
            
            return returns.dropna()
        except Exception as e:
            logger.error(f"Erreur lors du calcul des rendements: {e}")
            return pd.Series(dtype=float)
    
    @staticmethod
    def fit_garch(returns: pd.Series, model_type: str = "GARCH", 
                  p: int = 1, q: int = 1, **kwargs) -> Dict[str, Any]:
        """
        Ajuste un modèle GARCH aux rendements.
        
        Args:
            returns: Série des rendements
            model_type: Type de modèle ("GARCH", "EGARCH", "GJR-GARCH")
            p: Ordre de la partie ARCH
            q: Ordre de la partie GARCH
            **kwargs: Arguments supplémentaires pour le modèle
            
        Returns:
            Dictionnaire contenant le modèle ajusté et les métriques
        """
        try:
            if len(returns) < 50:
                raise ValueError("Pas assez de données pour ajuster un modèle GARCH")
            
            # Préparer les données
            returns_clean = returns.dropna()
            
            if model_type == "GARCH":
                model = arch_model(returns_clean, vol='GARCH', p=p, q=q, **kwargs)
            elif model_type == "EGARCH":
                model = arch_model(returns_clean, vol='EGARCH', p=p, q=q, **kwargs)
            elif model_type == "GJR-GARCH":
                model = arch_model(returns_clean, vol='GARCH', p=p, o=1, q=q, **kwargs)
            else:
                raise ValueError(f"Type de modèle non supporté: {model_type}")
            
            # Ajuster le modèle
            fitted_model = model.fit(disp='off', show_warning=False)
            
            # Extraire les métriques
            volatility_forecast = fitted_model.forecast(horizon=1).variance.iloc[-1, 0] ** 0.5
            
            # Calculer la Value at Risk
            var_95 = GARCHModels._calculate_var(fitted_model, 0.05)
            var_99 = GARCHModels._calculate_var(fitted_model, 0.01)
            
            return {
                "model": fitted_model,
                "model_type": model_type,
                "volatility_forecast": volatility_forecast,
                "var_95": var_95,
                "var_99": var_99,
                "aic": fitted_model.aic,
                "bic": fitted_model.bic,
                "log_likelihood": fitted_model.loglikelihood,
                "parameters": fitted_model.params.to_dict(),
                "residuals": fitted_model.resid,
                "conditional_volatility": fitted_model.conditional_volatility,
                "fitted_values": fitted_model.fittedvalues
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ajustement du modèle GARCH: {e}")
            return {
                "model": None,
                "model_type": model_type,
                "volatility_forecast": 0.0,
                "var_95": 0.0,
                "var_99": 0.0,
                "aic": float('inf'),
                "bic": float('inf'),
                "log_likelihood": -float('inf'),
                "parameters": {},
                "residuals": pd.Series(dtype=float),
                "conditional_volatility": pd.Series(dtype=float),
                "fitted_values": pd.Series(dtype=float),
                "error": str(e)
            }
    
    @staticmethod
    def _calculate_var(fitted_model, confidence_level: float) -> float:
        """
        Calcule la Value at Risk basée sur le modèle GARCH ajusté.
        
        Args:
            fitted_model: Modèle GARCH ajusté
            confidence_level: Niveau de confiance (ex: 0.05 pour 95%)
            
        Returns:
            Valeur de la VaR
        """
        try:
            # Utiliser la distribution normale pour calculer la VaR
            from scipy.stats import norm
            
            # Prévision de la volatilité
            volatility_forecast = fitted_model.forecast(horizon=1).variance.iloc[-1, 0] ** 0.5
            
            # Calculer la VaR
            z_score = norm.ppf(confidence_level)
            var = z_score * volatility_forecast
            
            return var
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la VaR: {e}")
            return 0.0
    
    @staticmethod
    def compare_models(returns: pd.Series, models: List[str] = None) -> Dict[str, Any]:
        """
        Compare différents modèles GARCH et sélectionne le meilleur.
        
        Args:
            returns: Série des rendements
            models: Liste des modèles à comparer
            
        Returns:
            Dictionnaire contenant la comparaison des modèles
        """
        try:
            if models is None:
                models = ["GARCH", "EGARCH", "GJR-GARCH"]
            
            results = {}
            
            for model_type in models:
                try:
                    result = GARCHModels.fit_garch(returns, model_type)
                    results[model_type] = {
                        "aic": result["aic"],
                        "bic": result["bic"],
                        "log_likelihood": result["log_likelihood"],
                        "volatility_forecast": result["volatility_forecast"],
                        "var_95": result["var_95"],
                        "var_99": result["var_99"],
                        "success": True
                    }
                except Exception as e:
                    results[model_type] = {
                        "aic": float('inf'),
                        "bic": float('inf'),
                        "log_likelihood": -float('inf'),
                        "volatility_forecast": 0.0,
                        "var_95": 0.0,
                        "var_99": 0.0,
                        "success": False,
                        "error": str(e)
                    }
            
            # Sélectionner le meilleur modèle basé sur l'AIC
            best_model = min(results.keys(), key=lambda x: results[x]["aic"])
            
            return {
                "comparison": results,
                "best_model": best_model,
                "best_model_results": results[best_model]
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la comparaison des modèles: {e}")
            return {
                "comparison": {},
                "best_model": None,
                "best_model_results": None,
                "error": str(e)
            }
    
    @staticmethod
    def forecast_volatility(returns: pd.Series, model_type: str = "GARCH", 
                          horizon: int = 5) -> Dict[str, Any]:
        """
        Prédit la volatilité future basée sur un modèle GARCH.
        
        Args:
            returns: Série des rendements
            model_type: Type de modèle GARCH
            horizon: Horizon de prédiction en jours
            
        Returns:
            Dictionnaire contenant les prédictions de volatilité
        """
        try:
            # Ajuster le modèle
            garch_result = GARCHModels.fit_garch(returns, model_type)
            
            if garch_result["model"] is None:
                raise ValueError("Impossible d'ajuster le modèle GARCH")
            
            fitted_model = garch_result["model"]
            
            # Générer les prédictions
            forecasts = fitted_model.forecast(horizon=horizon)
            
            # Extraire les prédictions de volatilité
            volatility_forecasts = np.sqrt(forecasts.variance.values[-1])
            
            # Calculer les intervalles de confiance
            confidence_intervals = GARCHModels._calculate_confidence_intervals(
                fitted_model, horizon
            )
            
            return {
                "volatility_forecasts": volatility_forecasts,
                "confidence_intervals": confidence_intervals,
                "model_type": model_type,
                "horizon": horizon,
                "current_volatility": garch_result["volatility_forecast"],
                "model_metrics": {
                    "aic": garch_result["aic"],
                    "bic": garch_result["bic"],
                    "log_likelihood": garch_result["log_likelihood"]
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction de volatilité: {e}")
            return {
                "volatility_forecasts": np.zeros(horizon),
                "confidence_intervals": {},
                "model_type": model_type,
                "horizon": horizon,
                "current_volatility": 0.0,
                "model_metrics": {},
                "error": str(e)
            }
    
    @staticmethod
    def _calculate_confidence_intervals(fitted_model, horizon: int, 
                                      confidence_levels: List[float] = [0.05, 0.95]) -> Dict[str, List[float]]:
        """
        Calcule les intervalles de confiance pour les prédictions de volatilité.
        
        Args:
            fitted_model: Modèle GARCH ajusté
            horizon: Horizon de prédiction
            confidence_levels: Niveaux de confiance
            
        Returns:
            Dictionnaire contenant les intervalles de confiance
        """
        try:
            # Générer des simulations Monte Carlo pour les intervalles de confiance
            simulations = fitted_model.forecast(horizon=horizon, method='simulation', simulations=1000)
            
            # Extraire les simulations de volatilité
            volatility_simulations = np.sqrt(simulations.variance.values)
            
            # Calculer les percentiles
            intervals = {}
            for level in confidence_levels:
                percentile = level * 100
                intervals[f"p{percentile}"] = np.percentile(volatility_simulations, percentile, axis=0)
            
            return intervals
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des intervalles de confiance: {e}")
            return {}
    
    @staticmethod
    def analyze_volatility_clustering(returns: pd.Series, window: int = 20) -> Dict[str, Any]:
        """
        Analyse le clustering de volatilité dans les rendements.
        
        Args:
            returns: Série des rendements
            window: Fenêtre mobile pour l'analyse
            
        Returns:
            Dictionnaire contenant l'analyse du clustering
        """
        try:
            # Calculer la volatilité mobile
            rolling_volatility = returns.rolling(window=window).std()
            
            # Calculer l'autocorrélation des rendements au carré
            squared_returns = returns ** 2
            autocorr = squared_returns.autocorr(lag=1)
            
            # Calculer les statistiques de clustering
            volatility_mean = rolling_volatility.mean()
            volatility_std = rolling_volatility.std()
            volatility_skewness = rolling_volatility.skew()
            volatility_kurtosis = rolling_volatility.kurtosis()
            
            # Identifier les périodes de haute volatilité
            high_vol_threshold = volatility_mean + 2 * volatility_std
            high_vol_periods = (rolling_volatility > high_vol_threshold).sum()
            
            return {
                "rolling_volatility": rolling_volatility,
                "autocorrelation": autocorr,
                "volatility_mean": volatility_mean,
                "volatility_std": volatility_std,
                "volatility_skewness": volatility_skewness,
                "volatility_kurtosis": volatility_kurtosis,
                "high_volatility_periods": high_vol_periods,
                "high_volatility_ratio": high_vol_periods / len(rolling_volatility),
                "clustering_strength": abs(autocorr)  # Force du clustering
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du clustering de volatilité: {e}")
            return {
                "rolling_volatility": pd.Series(dtype=float),
                "autocorrelation": 0.0,
                "volatility_mean": 0.0,
                "volatility_std": 0.0,
                "volatility_skewness": 0.0,
                "volatility_kurtosis": 0.0,
                "high_volatility_periods": 0,
                "high_volatility_ratio": 0.0,
                "clustering_strength": 0.0,
                "error": str(e)
            }
    
    @staticmethod
    def comprehensive_analysis(returns: pd.Series) -> Dict[str, Any]:
        """
        Effectue une analyse complète GARCH des rendements.
        
        Args:
            returns: Série des rendements
            
        Returns:
            Dictionnaire contenant l'analyse complète
        """
        try:
            # Comparer les modèles
            model_comparison = GARCHModels.compare_models(returns)
            
            # Prédiction de volatilité
            volatility_forecast = GARCHModels.forecast_volatility(returns, horizon=5)
            
            # Analyse du clustering
            clustering_analysis = GARCHModels.analyze_volatility_clustering(returns)
            
            # Statistiques descriptives
            descriptive_stats = {
                "mean_return": returns.mean(),
                "std_return": returns.std(),
                "skewness": returns.skew(),
                "kurtosis": returns.kurtosis(),
                "min_return": returns.min(),
                "max_return": returns.max(),
                "total_observations": len(returns)
            }
            
            return {
                "model_comparison": model_comparison,
                "volatility_forecast": volatility_forecast,
                "clustering_analysis": clustering_analysis,
                "descriptive_stats": descriptive_stats,
                "analysis_timestamp": pd.Timestamp.now().isoformat(),
                "data_period": {
                    "start": returns.index[0].isoformat() if hasattr(returns.index[0], 'isoformat') else str(returns.index[0]),
                    "end": returns.index[-1].isoformat() if hasattr(returns.index[-1], 'isoformat') else str(returns.index[-1]),
                    "duration_days": (returns.index[-1] - returns.index[0]).days
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse complète GARCH: {e}")
            return {
                "model_comparison": {},
                "volatility_forecast": {},
                "clustering_analysis": {},
                "descriptive_stats": {},
                "analysis_timestamp": pd.Timestamp.now(),
                "data_period": {},
                "error": str(e)
            }
