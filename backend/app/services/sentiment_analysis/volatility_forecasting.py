"""
Prédiction de volatilité pour l'analyse de sentiment.

Ce module implémente des méthodes avancées pour prédire
la volatilité future des prix.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from .garch_models import GARCHModels
from .monte_carlo import MonteCarloSimulation
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class VolatilityForecaster:
    """
    Classe pour prédire la volatilité future.
    
    Cette classe combine différents modèles pour fournir
    des prédictions robustes de volatilité.
    """
    
    def __init__(self):
        self.garch_models = GARCHModels()
        self.monte_carlo = MonteCarloSimulation()
    
    def forecast_volatility_ensemble(self, returns: pd.Series, horizon: int = 5,
                                   models: List[str] = None) -> Dict[str, Any]:
        """
        Prédit la volatilité en utilisant un ensemble de modèles.
        
        Args:
            returns: Série des rendements
            horizon: Horizon de prédiction en jours
            models: Liste des modèles à utiliser
            
        Returns:
            Dictionnaire contenant les prédictions d'ensemble
        """
        try:
            if models is None:
                models = ["GARCH", "EGARCH", "GJR-GARCH"]
            
            predictions = {}
            weights = {}
            
            for model_type in models:
                try:
                    # Prédiction GARCH
                    garch_forecast = self.garch_models.forecast_volatility(
                        returns, model_type, horizon
                    )
                    
                    if garch_forecast["volatility_forecasts"].size > 0:
                        predictions[model_type] = garch_forecast["volatility_forecasts"]
                        # Poids basé sur l'AIC (plus l'AIC est bas, plus le poids est élevé)
                        aic = garch_forecast["model_metrics"].get("aic", float('inf'))
                        weights[model_type] = 1.0 / (1.0 + aic) if aic != float('inf') else 0.1
                    else:
                        weights[model_type] = 0.0
                        
                except Exception as e:
                    logger.warning(f"Erreur avec le modèle {model_type}: {e}")
                    weights[model_type] = 0.0
            
            # Normaliser les poids
            total_weight = sum(weights.values())
            if total_weight > 0:
                weights = {k: v / total_weight for k, v in weights.items()}
            else:
                # Poids égaux si tous les modèles ont échoué
                weights = {k: 1.0 / len(models) for k in models}
            
            # Calculer la prédiction d'ensemble
            ensemble_forecast = np.zeros(horizon)
            for model_type, weight in weights.items():
                if model_type in predictions:
                    ensemble_forecast += weight * predictions[model_type]
            
            # Calculer l'incertitude de la prédiction
            uncertainty = self._calculate_forecast_uncertainty(predictions, weights)
            
            return {
                "ensemble_forecast": ensemble_forecast,
                "individual_predictions": predictions,
                "model_weights": weights,
                "uncertainty": uncertainty,
                "horizon": horizon,
                "models_used": list(predictions.keys())
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction d'ensemble de volatilité: {e}")
            return {
                "ensemble_forecast": np.zeros(horizon),
                "individual_predictions": {},
                "model_weights": {},
                "uncertainty": np.zeros(horizon),
                "horizon": horizon,
                "models_used": [],
                "error": str(e)
            }
    
    def _calculate_forecast_uncertainty(self, predictions: Dict[str, np.ndarray],
                                      weights: Dict[str, float]) -> np.ndarray:
        """
        Calcule l'incertitude de la prédiction d'ensemble.
        
        Args:
            predictions: Prédictions individuelles
            weights: Poids des modèles
            
        Returns:
            Array contenant l'incertitude
        """
        try:
            if not predictions:
                return np.array([])
            
            # Calculer la variance de la prédiction d'ensemble
            horizon = len(list(predictions.values())[0])
            uncertainty = np.zeros(horizon)
            
            for i in range(horizon):
                # Variance pondérée
                weighted_variance = 0.0
                for model_type, weight in weights.items():
                    if model_type in predictions:
                        pred_value = predictions[model_type][i]
                        weighted_variance += weight * (pred_value ** 2)
                
                # Soustraire le carré de la moyenne pondérée
                ensemble_mean = sum(
                    weight * predictions[model_type][i] 
                    for model_type, weight in weights.items() 
                    if model_type in predictions
                )
                
                uncertainty[i] = max(0, weighted_variance - ensemble_mean ** 2)
            
            return np.sqrt(uncertainty)
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de l'incertitude: {e}")
            return np.zeros(len(list(predictions.values())[0]) if predictions else 0)
    
    def forecast_volatility_regime_switching(self, returns: pd.Series, horizon: int = 5) -> Dict[str, Any]:
        """
        Prédit la volatilité en tenant compte des changements de régime.
        
        Args:
            returns: Série des rendements
            horizon: Horizon de prédiction en jours
            
        Returns:
            Dictionnaire contenant les prédictions avec changement de régime
        """
        try:
            from .markov_chains import MarkovChainAnalysis
            
            # Identifier les états de marché
            markov_analysis = MarkovChainAnalysis.comprehensive_markov_analysis(returns)
            
            if not markov_analysis["state_identification"]["states"].empty:
                states = markov_analysis["state_identification"]["states"]
                transition_matrix = markov_analysis["transition_analysis"]["transition_matrix"]
                current_state = markov_analysis["current_state"]
                
                # Prédire les états futurs
                future_predictions = MarkovChainAnalysis.predict_future_states(
                    transition_matrix, current_state, horizon
                )
                
                # Calculer la volatilité pour chaque état
                state_volatilities = {}
                for state in states.unique():
                    state_returns = returns[states == state]
                    if len(state_returns) > 10:  # Minimum de données
                        state_volatilities[state] = state_returns.std()
                    else:
                        state_volatilities[state] = returns.std()
                
                # Prédire la volatilité basée sur les états futurs
                volatility_forecast = np.zeros(horizon)
                for h in range(horizon):
                    state_probs = future_predictions["predictions"].iloc[h]
                    expected_volatility = sum(
                        state_probs[f"state_{state}"] * state_volatilities.get(state, returns.std())
                        for state in states.unique()
                    )
                    volatility_forecast[h] = expected_volatility
                
                return {
                    "volatility_forecast": volatility_forecast,
                    "state_predictions": future_predictions,
                    "state_volatilities": state_volatilities,
                    "current_state": current_state,
                    "horizon": horizon,
                    "method": "regime_switching"
                }
            else:
                # Fallback vers un modèle GARCH simple
                garch_forecast = self.garch_models.forecast_volatility(returns, "GARCH", horizon)
                return {
                    "volatility_forecast": garch_forecast["volatility_forecasts"],
                    "state_predictions": {},
                    "state_volatilities": {},
                    "current_state": None,
                    "horizon": horizon,
                    "method": "garch_fallback"
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction avec changement de régime: {e}")
            return {
                "volatility_forecast": np.zeros(horizon),
                "state_predictions": {},
                "state_volatilities": {},
                "current_state": None,
                "horizon": horizon,
                "method": "error",
                "error": str(e)
            }
    
    def forecast_volatility_monte_carlo(self, returns: pd.Series, horizon: int = 5,
                                      simulations: int = 10000) -> Dict[str, Any]:
        """
        Prédit la volatilité en utilisant des simulations Monte Carlo.
        
        Args:
            returns: Série des rendements
            horizon: Horizon de prédiction en jours
            simulations: Nombre de simulations
            
        Returns:
            Dictionnaire contenant les prédictions Monte Carlo
        """
        try:
            # Calculer les paramètres du modèle
            current_price = 100.0  # Prix de référence
            drift = returns.mean() * 252  # Dérive annuelle
            volatility = returns.std() * np.sqrt(252)  # Volatilité annuelle
            
            # Simuler les trajectoires
            paths = self.monte_carlo.simulate_price_paths(
                current_price, volatility, drift, horizon, simulations
            )
            
            # Calculer la volatilité pour chaque trajectoire
            path_volatilities = []
            for path in paths:
                path_returns = np.diff(np.log(path))
                if len(path_returns) > 0:
                    path_volatilities.append(np.std(path_returns) * np.sqrt(252))
                else:
                    path_volatilities.append(volatility)
            
            # Statistiques de la distribution des volatilités
            volatility_forecast = np.mean(path_volatilities)
            volatility_std = np.std(path_volatilities)
            volatility_percentiles = np.percentile(path_volatilities, [5, 25, 50, 75, 95])
            
            return {
                "volatility_forecast": volatility_forecast,
                "volatility_std": volatility_std,
                "volatility_percentiles": {
                    "p5": volatility_percentiles[0],
                    "p25": volatility_percentiles[1],
                    "p50": volatility_percentiles[2],
                    "p75": volatility_percentiles[3],
                    "p95": volatility_percentiles[4]
                },
                "path_volatilities": path_volatilities,
                "horizon": horizon,
                "simulations": simulations,
                "method": "monte_carlo"
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction Monte Carlo: {e}")
            return {
                "volatility_forecast": 0.0,
                "volatility_std": 0.0,
                "volatility_percentiles": {},
                "path_volatilities": [],
                "horizon": horizon,
                "simulations": simulations,
                "method": "monte_carlo",
                "error": str(e)
            }
    
    def calculate_volatility_risk_metrics(self, returns: pd.Series, 
                                        volatility_forecast: np.ndarray) -> Dict[str, Any]:
        """
        Calcule des métriques de risque basées sur la prédiction de volatilité.
        
        Args:
            returns: Série des rendements
            volatility_forecast: Prédiction de volatilité
            
        Returns:
            Dictionnaire contenant les métriques de risque
        """
        try:
            # Volatilité actuelle
            current_volatility = returns.std() * np.sqrt(252)
            
            # Volatilité moyenne prévue
            avg_forecast_volatility = np.mean(volatility_forecast)
            
            # Volatilité maximale prévue
            max_forecast_volatility = np.max(volatility_forecast)
            
            # Volatilité minimale prévue
            min_forecast_volatility = np.min(volatility_forecast)
            
            # Écart-type de la prédiction
            forecast_uncertainty = np.std(volatility_forecast)
            
            # Tendance de la volatilité
            if len(volatility_forecast) > 1:
                volatility_trend = (volatility_forecast[-1] - volatility_forecast[0]) / len(volatility_forecast)
            else:
                volatility_trend = 0.0
            
            # Niveau de risque basé sur la volatilité
            risk_level = self._assess_volatility_risk_level(avg_forecast_volatility)
            
            # Calculer la VaR basée sur la volatilité
            var_95 = -1.645 * avg_forecast_volatility / np.sqrt(252)  # VaR quotidienne
            var_99 = -2.326 * avg_forecast_volatility / np.sqrt(252)  # VaR quotidienne
            
            return {
                "current_volatility": current_volatility,
                "forecast_volatility": {
                    "mean": avg_forecast_volatility,
                    "max": max_forecast_volatility,
                    "min": min_forecast_volatility,
                    "std": forecast_uncertainty
                },
                "volatility_trend": volatility_trend,
                "risk_level": risk_level,
                "var_95": var_95,
                "var_99": var_99,
                "volatility_change": (avg_forecast_volatility - current_volatility) / current_volatility
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des métriques de risque: {e}")
            return {
                "current_volatility": 0.0,
                "forecast_volatility": {},
                "volatility_trend": 0.0,
                "risk_level": "Unknown",
                "var_95": 0.0,
                "var_99": 0.0,
                "volatility_change": 0.0,
                "error": str(e)
            }
    
    def _assess_volatility_risk_level(self, volatility: float) -> str:
        """
        Évalue le niveau de risque basé sur la volatilité.
        
        Args:
            volatility: Volatilité annuelle
            
        Returns:
            Niveau de risque
        """
        try:
            if volatility < 0.15:  # 15%
                return "Low"
            elif volatility < 0.25:  # 25%
                return "Medium"
            elif volatility < 0.35:  # 35%
                return "High"
            else:
                return "Very High"
                
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation du niveau de risque: {e}")
            return "Unknown"
    
    def comprehensive_volatility_forecast(self, returns: pd.Series, horizon: int = 5) -> Dict[str, Any]:
        """
        Effectue une prédiction complète de volatilité en utilisant plusieurs méthodes.
        
        Args:
            returns: Série des rendements
            horizon: Horizon de prédiction en jours
            
        Returns:
            Dictionnaire contenant l'analyse complète
        """
        try:
            # Prédiction d'ensemble
            ensemble_forecast = self.forecast_volatility_ensemble(returns, horizon)
            
            # Prédiction avec changement de régime
            regime_forecast = self.forecast_volatility_regime_switching(returns, horizon)
            
            # Prédiction Monte Carlo
            monte_carlo_forecast = self.forecast_volatility_monte_carlo(returns, horizon)
            
            # Calculer les métriques de risque
            risk_metrics = self.calculate_volatility_risk_metrics(
                returns, ensemble_forecast["ensemble_forecast"]
            )
            
            # Combiner les prédictions
            combined_forecast = self._combine_forecasts([
                ensemble_forecast["ensemble_forecast"],
                regime_forecast["volatility_forecast"],
                [monte_carlo_forecast["volatility_forecast"]] * horizon
            ])
            
            return {
                "ensemble_forecast": ensemble_forecast,
                "regime_forecast": regime_forecast,
                "monte_carlo_forecast": monte_carlo_forecast,
                "combined_forecast": combined_forecast,
                "risk_metrics": risk_metrics,
                "horizon": horizon,
                "analysis_timestamp": pd.Timestamp.now(),
                "data_period": {
                    "start": returns.index[0],
                    "end": returns.index[-1],
                    "duration_days": (returns.index[-1] - returns.index[0]).days
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction complète de volatilité: {e}")
            return {
                "ensemble_forecast": {},
                "regime_forecast": {},
                "monte_carlo_forecast": {},
                "combined_forecast": np.zeros(horizon),
                "risk_metrics": {},
                "horizon": horizon,
                "analysis_timestamp": pd.Timestamp.now(),
                "data_period": {},
                "error": str(e)
            }
    
    def _combine_forecasts(self, forecasts: List[np.ndarray]) -> np.ndarray:
        """
        Combine plusieurs prédictions de volatilité.
        
        Args:
            forecasts: Liste des prédictions
            
        Returns:
            Prédiction combinée
        """
        try:
            if not forecasts:
                return np.array([])
            
            # Filtrer les prédictions valides
            valid_forecasts = [f for f in forecasts if len(f) > 0]
            
            if not valid_forecasts:
                return np.array([])
            
            # Combiner en utilisant la moyenne
            combined = np.mean(valid_forecasts, axis=0)
            
            return combined
            
        except Exception as e:
            logger.error(f"Erreur lors de la combinaison des prédictions: {e}")
            return np.array([])
