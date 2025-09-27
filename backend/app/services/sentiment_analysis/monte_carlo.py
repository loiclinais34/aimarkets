"""
Simulations Monte Carlo pour l'analyse de risque et de sentiment.

Ce module implémente des simulations Monte Carlo pour analyser
les risques de marché et générer des scénarios de prix.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from scipy.stats import norm, t
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class MonteCarloSimulation:
    """
    Classe pour effectuer des simulations Monte Carlo.
    
    Cette classe fournit des méthodes pour simuler des trajectoires
    de prix et calculer des métriques de risque.
    """
    
    @staticmethod
    def simulate_price_paths(current_price: float, volatility: float, drift: float,
                           time_horizon: int, simulations: int = 10000,
                           dt: float = 1/252) -> np.ndarray:
        """
        Simule des trajectoires de prix en utilisant le modèle de Black-Scholes.
        
        Args:
            current_price: Prix actuel
            volatility: Volatilité annuelle
            drift: Dérive annuelle (rendement attendu)
            time_horizon: Horizon temporel en jours
            simulations: Nombre de simulations
            dt: Pas de temps (défaut: 1/252 pour un jour)
            
        Returns:
            Array 2D contenant les trajectoires simulées
        """
        try:
            # Initialiser l'array des trajectoires
            paths = np.zeros((simulations, time_horizon + 1))
            paths[:, 0] = current_price
            
            # Générer les chocs aléatoires
            random_shocks = np.random.normal(0, 1, (simulations, time_horizon))
            
            # Simuler les trajectoires
            for t in range(1, time_horizon + 1):
                paths[:, t] = paths[:, t-1] * np.exp(
                    (drift - 0.5 * volatility**2) * dt + 
                    volatility * np.sqrt(dt) * random_shocks[:, t-1]
                )
            
            return paths
            
        except Exception as e:
            logger.error(f"Erreur lors de la simulation des trajectoires de prix: {e}")
            return np.zeros((simulations, time_horizon + 1))
    
    @staticmethod
    def calculate_var(paths: np.ndarray, confidence_level: float = 0.05) -> float:
        """
        Calcule la Value at Risk (VaR) à partir des trajectoires simulées.
        
        Args:
            paths: Trajectoires de prix simulées
            confidence_level: Niveau de confiance (ex: 0.05 pour 95%)
            
        Returns:
            Valeur de la VaR
        """
        try:
            # Calculer les rendements finaux
            final_prices = paths[:, -1]
            initial_price = paths[0, 0]
            returns = (final_prices - initial_price) / initial_price
            
            # Calculer le percentile
            var = np.percentile(returns, confidence_level * 100)
            
            return var
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la VaR: {e}")
            return 0.0
    
    @staticmethod
    def calculate_expected_shortfall(paths: np.ndarray, confidence_level: float = 0.05) -> float:
        """
        Calcule l'Expected Shortfall (ES) ou Conditional VaR.
        
        Args:
            paths: Trajectoires de prix simulées
            confidence_level: Niveau de confiance
            
        Returns:
            Valeur de l'Expected Shortfall
        """
        try:
            # Calculer les rendements finaux
            final_prices = paths[:, -1]
            initial_price = paths[0, 0]
            returns = (final_prices - initial_price) / initial_price
            
            # Calculer la VaR
            var = np.percentile(returns, confidence_level * 100)
            
            # Calculer l'ES comme la moyenne des pertes au-delà de la VaR
            tail_losses = returns[returns <= var]
            es = np.mean(tail_losses) if len(tail_losses) > 0 else var
            
            return es
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de l'Expected Shortfall: {e}")
            return 0.0
    
    @staticmethod
    def calculate_portfolio_var(returns: pd.DataFrame, weights: np.ndarray,
                              confidence_level: float = 0.05, 
                              simulations: int = 10000) -> Dict[str, float]:
        """
        Calcule la VaR d'un portefeuille en utilisant Monte Carlo.
        
        Args:
            returns: DataFrame des rendements des actifs
            weights: Poids du portefeuille
            confidence_level: Niveau de confiance
            simulations: Nombre de simulations
            
        Returns:
            Dictionnaire contenant les métriques de risque
        """
        try:
            # Calculer la matrice de covariance
            cov_matrix = returns.cov().values
            
            # Calculer le rendement attendu du portefeuille
            expected_returns = returns.mean().values
            portfolio_return = np.dot(weights, expected_returns)
            
            # Calculer la variance du portefeuille
            portfolio_variance = np.dot(weights, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            # Simuler les rendements du portefeuille
            portfolio_returns = np.random.multivariate_normal(
                [portfolio_return] * simulations,
                [[portfolio_variance]] * simulations
            ).flatten()
            
            # Calculer la VaR
            var = np.percentile(portfolio_returns, confidence_level * 100)
            
            # Calculer l'Expected Shortfall
            tail_losses = portfolio_returns[portfolio_returns <= var]
            es = np.mean(tail_losses) if len(tail_losses) > 0 else var
            
            return {
                "var": var,
                "expected_shortfall": es,
                "portfolio_return": portfolio_return,
                "portfolio_volatility": portfolio_volatility,
                "confidence_level": confidence_level
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la VaR du portefeuille: {e}")
            return {
                "var": 0.0,
                "expected_shortfall": 0.0,
                "portfolio_return": 0.0,
                "portfolio_volatility": 0.0,
                "confidence_level": confidence_level
            }
    
    @staticmethod
    def stress_testing(paths: np.ndarray, stress_scenarios: Dict[str, float]) -> Dict[str, Any]:
        """
        Effectue des tests de stress sur les trajectoires simulées.
        
        Args:
            paths: Trajectoires de prix simulées
            stress_scenarios: Dictionnaire des scénarios de stress
            
        Returns:
            Dictionnaire contenant les résultats des tests de stress
        """
        try:
            results = {}
            
            for scenario_name, stress_factor in stress_scenarios.items():
                # Appliquer le facteur de stress
                stressed_paths = paths * stress_factor
                
                # Calculer les métriques de risque
                var_95 = MonteCarloSimulation.calculate_var(stressed_paths, 0.05)
                var_99 = MonteCarloSimulation.calculate_var(stressed_paths, 0.01)
                es_95 = MonteCarloSimulation.calculate_expected_shortfall(stressed_paths, 0.05)
                
                results[scenario_name] = {
                    "stress_factor": stress_factor,
                    "var_95": var_95,
                    "var_99": var_99,
                    "expected_shortfall_95": es_95,
                    "max_loss": np.min((stressed_paths[:, -1] - stressed_paths[0, 0]) / stressed_paths[0, 0])
                }
            
            return results
            
        except Exception as e:
            logger.error(f"Erreur lors des tests de stress: {e}")
            return {}
    
    @staticmethod
    def calculate_option_prices(paths: np.ndarray, strike_price: float, 
                              risk_free_rate: float = 0.02,
                              option_type: str = "call") -> Dict[str, float]:
        """
        Calcule les prix d'options en utilisant Monte Carlo.
        
        Args:
            paths: Trajectoires de prix simulées
            strike_price: Prix d'exercice
            risk_free_rate: Taux sans risque
            option_type: Type d'option ("call" ou "put")
            
        Returns:
            Dictionnaire contenant les prix d'options
        """
        try:
            # Prix finaux simulés
            final_prices = paths[:, -1]
            
            # Calculer les payoffs
            if option_type == "call":
                payoffs = np.maximum(final_prices - strike_price, 0)
            else:  # put
                payoffs = np.maximum(strike_price - final_prices, 0)
            
            # Actualiser les payoffs
            time_to_expiry = (paths.shape[1] - 1) / 252  # en années
            discounted_payoffs = payoffs * np.exp(-risk_free_rate * time_to_expiry)
            
            # Prix de l'option
            option_price = np.mean(discounted_payoffs)
            
            # Calculer la volatilité implicite (approximation)
            # Utiliser la formule de Black-Scholes pour l'approximation
            current_price = paths[0, 0]
            d1 = (np.log(current_price / strike_price) + 
                  (risk_free_rate + 0.5 * np.var(np.diff(np.log(final_prices)))) * time_to_expiry) / \
                 (np.sqrt(np.var(np.diff(np.log(final_prices)))) * np.sqrt(time_to_expiry))
            
            d2 = d1 - np.sqrt(np.var(np.diff(np.log(final_prices)))) * np.sqrt(time_to_expiry)
            
            if option_type == "call":
                bs_price = (current_price * norm.cdf(d1) - 
                           strike_price * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2))
            else:
                bs_price = (strike_price * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) - 
                           current_price * norm.cdf(-d1))
            
            return {
                "monte_carlo_price": option_price,
                "black_scholes_price": bs_price,
                "implied_volatility": np.sqrt(np.var(np.diff(np.log(final_prices)))),
                "delta": norm.cdf(d1) if option_type == "call" else -norm.cdf(-d1),
                "gamma": norm.pdf(d1) / (current_price * np.sqrt(np.var(np.diff(np.log(final_prices)))) * np.sqrt(time_to_expiry)),
                "theta": -current_price * norm.pdf(d1) * np.sqrt(np.var(np.diff(np.log(final_prices)))) / (2 * np.sqrt(time_to_expiry)) - 
                        risk_free_rate * strike_price * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2),
                "vega": current_price * norm.pdf(d1) * np.sqrt(time_to_expiry)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des prix d'options: {e}")
            return {
                "monte_carlo_price": 0.0,
                "black_scholes_price": 0.0,
                "implied_volatility": 0.0,
                "delta": 0.0,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0
            }
    
    @staticmethod
    def analyze_tail_risk(paths: np.ndarray, confidence_levels: List[float] = [0.01, 0.05, 0.1]) -> Dict[str, Any]:
        """
        Analyse les risques de queue (tail risk) des trajectoires simulées.
        
        Args:
            paths: Trajectoires de prix simulées
            confidence_levels: Niveaux de confiance à analyser
            
        Returns:
            Dictionnaire contenant l'analyse des risques de queue
        """
        try:
            # Calculer les rendements finaux
            final_prices = paths[:, -1]
            initial_price = paths[0, 0]
            returns = (final_prices - initial_price) / initial_price
            
            # Calculer les métriques de queue
            tail_metrics = {}
            
            for level in confidence_levels:
                var = np.percentile(returns, level * 100)
                es = np.mean(returns[returns <= var]) if len(returns[returns <= var]) > 0 else var
                
                tail_metrics[f"var_{int(level*100)}"] = var
                tail_metrics[f"es_{int(level*100)}"] = es
            
            # Calculer les moments d'ordre supérieur
            skewness = np.mean((returns - np.mean(returns))**3) / (np.std(returns)**3)
            kurtosis = np.mean((returns - np.mean(returns))**4) / (np.std(returns)**4)
            
            # Calculer l'excès de kurtosis
            excess_kurtosis = kurtosis - 3
            
            # Identifier les événements extrêmes
            extreme_threshold = np.percentile(returns, 1)  # 1% des pires cas
            extreme_events = returns[returns <= extreme_threshold]
            
            return {
                "tail_metrics": tail_metrics,
                "skewness": skewness,
                "kurtosis": kurtosis,
                "excess_kurtosis": excess_kurtosis,
                "extreme_events_count": len(extreme_events),
                "extreme_events_ratio": len(extreme_events) / len(returns),
                "worst_case_scenario": np.min(returns),
                "best_case_scenario": np.max(returns)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des risques de queue: {e}")
            return {
                "tail_metrics": {},
                "skewness": 0.0,
                "kurtosis": 0.0,
                "excess_kurtosis": 0.0,
                "extreme_events_count": 0,
                "extreme_events_ratio": 0.0,
                "worst_case_scenario": 0.0,
                "best_case_scenario": 0.0
            }
    
    @staticmethod
    def comprehensive_monte_carlo_analysis(current_price: float, volatility: float, 
                                         drift: float, time_horizon: int,
                                         simulations: int = 10000) -> Dict[str, Any]:
        """
        Effectue une analyse Monte Carlo complète.
        
        Args:
            current_price: Prix actuel
            volatility: Volatilité annuelle
            drift: Dérive annuelle
            time_horizon: Horizon temporel en jours
            simulations: Nombre de simulations
            
        Returns:
            Dictionnaire contenant l'analyse complète
        """
        try:
            # Simuler les trajectoires
            paths = MonteCarloSimulation.simulate_price_paths(
                current_price, volatility, drift, time_horizon, simulations
            )
            
            # Calculer les métriques de risque
            var_95 = MonteCarloSimulation.calculate_var(paths, 0.05)
            var_99 = MonteCarloSimulation.calculate_var(paths, 0.01)
            es_95 = MonteCarloSimulation.calculate_expected_shortfall(paths, 0.05)
            es_99 = MonteCarloSimulation.calculate_expected_shortfall(paths, 0.01)
            
            # Tests de stress
            stress_scenarios = {
                "market_crash": 0.5,  # -50%
                "market_correction": 0.8,  # -20%
                "market_boom": 1.5,  # +50%
                "volatility_spike": 1.0  # Pas de changement de prix
            }
            
            stress_results = MonteCarloSimulation.stress_testing(paths, stress_scenarios)
            
            # Analyse des risques de queue
            tail_analysis = MonteCarloSimulation.analyze_tail_risk(paths)
            
            # Statistiques descriptives
            final_prices = paths[:, -1]
            returns = (final_prices - current_price) / current_price
            
            descriptive_stats = {
                "mean_return": np.mean(returns),
                "std_return": np.std(returns),
                "min_return": np.min(returns),
                "max_return": np.max(returns),
                "median_return": np.median(returns),
                "probability_positive_return": np.mean(returns > 0),
                "probability_negative_return": np.mean(returns < 0)
            }
            
            return {
                "paths": paths,
                "risk_metrics": {
                    "var_95": var_95,
                    "var_99": var_99,
                    "expected_shortfall_95": es_95,
                    "expected_shortfall_99": es_99
                },
                "stress_testing": stress_results,
                "tail_analysis": tail_analysis,
                "descriptive_stats": descriptive_stats,
                "simulation_parameters": {
                    "current_price": current_price,
                    "volatility": volatility,
                    "drift": drift,
                    "time_horizon": time_horizon,
                    "simulations": simulations
                },
                "analysis_timestamp": pd.Timestamp.now()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse Monte Carlo complète: {e}")
            return {
                "paths": np.zeros((simulations, time_horizon + 1)),
                "risk_metrics": {},
                "stress_testing": {},
                "tail_analysis": {},
                "descriptive_stats": {},
                "simulation_parameters": {},
                "analysis_timestamp": pd.Timestamp.now(),
                "error": str(e)
            }
