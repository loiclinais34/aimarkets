"""
Analyse des corrélations pour l'analyse de marché.

Ce module implémente des méthodes pour analyser les corrélations
entre différents actifs et leurs évolutions dans le temps.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
import yfinance as yf
from scipy.stats import pearsonr, spearmanr
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class CorrelationAnalyzer:
    """
    Classe pour analyser les corrélations entre actifs.
    
    Cette classe fournit des méthodes pour calculer et analyser
    les corrélations dynamiques entre différents actifs.
    """
    
    @staticmethod
    def calculate_correlation_matrix(returns: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
        """
        Calcule la matrice de corrélation.
        
        Args:
            returns: DataFrame des rendements
            method: Méthode de corrélation ("pearson" ou "spearman")
            
        Returns:
            DataFrame de la matrice de corrélation
        """
        try:
            if method == "pearson":
                correlation_matrix = returns.corr()
            elif method == "spearman":
                correlation_matrix = returns.corr(method='spearman')
            else:
                raise ValueError(f"Méthode de corrélation non supportée: {method}")
            
            return correlation_matrix
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la matrice de corrélation: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def calculate_rolling_correlation(returns1: pd.Series, returns2: pd.Series, 
                                    window: int = 20) -> pd.Series:
        """
        Calcule la corrélation mobile entre deux séries.
        
        Args:
            returns1: Première série de rendements
            returns2: Deuxième série de rendements
            window: Fenêtre de calcul
            
        Returns:
            Série de corrélation mobile
        """
        try:
            # Aligner les séries
            aligned_returns = pd.DataFrame({
                'returns1': returns1,
                'returns2': returns2
            }).dropna()
            
            if len(aligned_returns) < window:
                return pd.Series(dtype=float)
            
            # Calculer la corrélation mobile
            rolling_corr = aligned_returns['returns1'].rolling(window=window).corr(
                aligned_returns['returns2']
            )
            
            return rolling_corr
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la corrélation mobile: {e}")
            return pd.Series(dtype=float)
    
    @staticmethod
    def calculate_dynamic_correlation(returns: pd.DataFrame, window: int = 20) -> Dict[str, pd.DataFrame]:
        """
        Calcule les corrélations dynamiques pour toutes les paires d'actifs.
        
        Args:
            returns: DataFrame des rendements
            window: Fenêtre de calcul
            
        Returns:
            Dictionnaire contenant les corrélations dynamiques
        """
        try:
            symbols = returns.columns.tolist()
            dynamic_correlations = {}
            
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols):
                    if i < j:  # Éviter les doublons
                        pair_name = f"{symbol1}_{symbol2}"
                        rolling_corr = CorrelationAnalyzer.calculate_rolling_correlation(
                            returns[symbol1], returns[symbol2], window
                        )
                        dynamic_correlations[pair_name] = rolling_corr
            
            return dynamic_correlations
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des corrélations dynamiques: {e}")
            return {}
    
    @staticmethod
    def analyze_correlation_stability(correlation_matrix: pd.DataFrame, 
                                    threshold: float = 0.7) -> Dict[str, Any]:
        """
        Analyse la stabilité des corrélations.
        
        Args:
            correlation_matrix: Matrice de corrélation
            threshold: Seuil pour considérer une corrélation forte
            
        Returns:
            Dictionnaire contenant l'analyse de stabilité
        """
        try:
            # Extraire les corrélations (sans la diagonale)
            correlations = correlation_matrix.values
            np.fill_diagonal(correlations, np.nan)
            
            # Flatten et supprimer les NaN
            flat_correlations = correlations.flatten()
            flat_correlations = flat_correlations[~np.isnan(flat_correlations)]
            
            # Statistiques
            mean_correlation = np.mean(flat_correlations)
            std_correlation = np.std(flat_correlations)
            min_correlation = np.min(flat_correlations)
            max_correlation = np.max(flat_correlations)
            
            # Corrélations fortes
            strong_correlations = np.abs(flat_correlations) >= threshold
            strong_corr_count = np.sum(strong_correlations)
            strong_corr_ratio = strong_corr_count / len(flat_correlations)
            
            # Corrélations négatives
            negative_correlations = flat_correlations < -threshold
            negative_corr_count = np.sum(negative_correlations)
            negative_corr_ratio = negative_corr_count / len(flat_correlations)
            
            return {
                "mean_correlation": mean_correlation,
                "std_correlation": std_correlation,
                "min_correlation": min_correlation,
                "max_correlation": max_correlation,
                "strong_correlations": {
                    "count": strong_corr_count,
                    "ratio": strong_corr_ratio
                },
                "negative_correlations": {
                    "count": negative_corr_count,
                    "ratio": negative_corr_ratio
                },
                "correlation_range": max_correlation - min_correlation
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de stabilité: {e}")
            return {}
    
    @staticmethod
    def calculate_correlation_breakdown(returns: pd.DataFrame, 
                                      market_returns: pd.Series) -> Dict[str, Any]:
        """
        Calcule la décomposition de corrélation avec le marché.
        
        Args:
            returns: DataFrame des rendements des actifs
            market_returns: Série des rendements du marché
            
        Returns:
            Dictionnaire contenant la décomposition
        """
        try:
            # Aligner les données
            aligned_data = pd.DataFrame({
                'market': market_returns
            })
            
            for symbol in returns.columns:
                aligned_data[symbol] = returns[symbol]
            
            aligned_data = aligned_data.dropna()
            
            if len(aligned_data) < 20:
                raise ValueError("Pas assez de données pour la décomposition")
            
            # Calculer les corrélations avec le marché
            market_correlations = {}
            for symbol in returns.columns:
                if symbol in aligned_data.columns:
                    corr, p_value = pearsonr(aligned_data['market'], aligned_data[symbol])
                    market_correlations[symbol] = {
                        "correlation": corr,
                        "p_value": p_value,
                        "significance": "significant" if p_value < 0.05 else "not_significant"
                    }
            
            # Calculer la corrélation moyenne
            avg_correlation = np.mean([data["correlation"] for data in market_correlations.values()])
            
            # Identifier les actifs les plus corrélés
            sorted_correlations = sorted(
                market_correlations.items(), 
                key=lambda x: abs(x[1]["correlation"]), 
                reverse=True
            )
            
            return {
                "market_correlations": market_correlations,
                "average_correlation": avg_correlation,
                "most_correlated": sorted_correlations[:5],
                "least_correlated": sorted_correlations[-5:],
                "total_assets": len(market_correlations)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la décomposition de corrélation: {e}")
            return {}
    
    @staticmethod
    def calculate_correlation_network(returns: pd.DataFrame, 
                                    threshold: float = 0.5) -> Dict[str, Any]:
        """
        Calcule le réseau de corrélations entre actifs.
        
        Args:
            returns: DataFrame des rendements
            threshold: Seuil pour considérer une connexion
            
        Returns:
            Dictionnaire contenant le réseau de corrélations
        """
        try:
            # Calculer la matrice de corrélation
            correlation_matrix = CorrelationAnalyzer.calculate_correlation_matrix(returns)
            
            # Créer le réseau
            network = {
                "nodes": [],
                "edges": [],
                "adjacency_matrix": correlation_matrix
            }
            
            # Ajouter les nœuds
            for symbol in returns.columns:
                network["nodes"].append({
                    "id": symbol,
                    "name": symbol,
                    "degree": 0
                })
            
            # Ajouter les arêtes
            symbols = returns.columns.tolist()
            for i, symbol1 in enumerate(symbols):
                for j, symbol2 in enumerate(symbols):
                    if i < j:  # Éviter les doublons
                        correlation = correlation_matrix.loc[symbol1, symbol2]
                        
                        if abs(correlation) >= threshold:
                            network["edges"].append({
                                "source": symbol1,
                                "target": symbol2,
                                "weight": abs(correlation),
                                "correlation": correlation
                            })
            
            # Calculer le degré de chaque nœud
            for node in network["nodes"]:
                degree = sum(1 for edge in network["edges"] 
                           if edge["source"] == node["id"] or edge["target"] == node["id"])
                node["degree"] = degree
            
            # Statistiques du réseau
            network_stats = {
                "total_nodes": len(network["nodes"]),
                "total_edges": len(network["edges"]),
                "average_degree": np.mean([node["degree"] for node in network["nodes"]]),
                "density": len(network["edges"]) / (len(network["nodes"]) * (len(network["nodes"]) - 1) / 2)
            }
            
            return {
                "network": network,
                "network_stats": network_stats,
                "threshold": threshold
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du réseau de corrélations: {e}")
            return {}
    
    @staticmethod
    def calculate_correlation_risk(returns: pd.DataFrame, 
                                 portfolio_weights: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Calcule le risque de corrélation d'un portefeuille.
        
        Args:
            returns: DataFrame des rendements
            portfolio_weights: Poids du portefeuille (optionnel)
            
        Returns:
            Dictionnaire contenant l'analyse du risque de corrélation
        """
        try:
            # Calculer la matrice de corrélation
            correlation_matrix = CorrelationAnalyzer.calculate_correlation_matrix(returns)
            
            # Calculer la matrice de covariance
            covariance_matrix = returns.cov()
            
            # Si pas de poids spécifiés, utiliser des poids égaux
            if portfolio_weights is None:
                portfolio_weights = np.ones(len(returns.columns)) / len(returns.columns)
            
            # Calculer la variance du portefeuille
            portfolio_variance = np.dot(portfolio_weights, np.dot(covariance_matrix, portfolio_weights))
            
            # Calculer la contribution de chaque actif au risque
            risk_contributions = {}
            for i, symbol in enumerate(returns.columns):
                contribution = portfolio_weights[i] * np.dot(covariance_matrix.iloc[i], portfolio_weights)
                risk_contributions[symbol] = contribution / portfolio_variance
            
            # Calculer l'indice de concentration de corrélation
            correlation_concentration = np.sum(np.abs(correlation_matrix.values)) / (len(returns.columns) ** 2)
            
            # Calculer le risque de corrélation
            correlation_risk = np.sqrt(portfolio_variance) * correlation_concentration
            
            return {
                "portfolio_variance": portfolio_variance,
                "portfolio_volatility": np.sqrt(portfolio_variance),
                "risk_contributions": risk_contributions,
                "correlation_concentration": correlation_concentration,
                "correlation_risk": correlation_risk,
                "portfolio_weights": dict(zip(returns.columns, portfolio_weights))
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du risque de corrélation: {e}")
            return {}
    
    @staticmethod
    def comprehensive_correlation_analysis(returns: pd.DataFrame, 
                                         market_returns: Optional[pd.Series] = None) -> Dict[str, Any]:
        """
        Effectue une analyse complète des corrélations.
        
        Args:
            returns: DataFrame des rendements
            market_returns: Série des rendements du marché (optionnel)
            
        Returns:
            Dictionnaire contenant l'analyse complète
        """
        try:
            # Matrice de corrélation
            correlation_matrix = CorrelationAnalyzer.calculate_correlation_matrix(returns)
            
            # Corrélations dynamiques
            dynamic_correlations = CorrelationAnalyzer.calculate_dynamic_correlation(returns)
            
            # Analyse de stabilité
            stability_analysis = CorrelationAnalyzer.analyze_correlation_stability(correlation_matrix)
            
            # Réseau de corrélations
            correlation_network = CorrelationAnalyzer.calculate_correlation_network(returns)
            
            # Risque de corrélation
            correlation_risk = CorrelationAnalyzer.calculate_correlation_risk(returns)
            
            # Décomposition avec le marché (si disponible)
            market_breakdown = {}
            if market_returns is not None:
                market_breakdown = CorrelationAnalyzer.calculate_correlation_breakdown(returns, market_returns)
            
            return {
                "correlation_matrix": correlation_matrix,
                "dynamic_correlations": dynamic_correlations,
                "stability_analysis": stability_analysis,
                "correlation_network": correlation_network,
                "correlation_risk": correlation_risk,
                "market_breakdown": market_breakdown,
                "analysis_timestamp": pd.Timestamp.now(),
                "data_period": {
                    "start": returns.index[0],
                    "end": returns.index[-1],
                    "duration_days": (returns.index[-1] - returns.index[0]).days
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse complète des corrélations: {e}")
            return {
                "correlation_matrix": pd.DataFrame(),
                "dynamic_correlations": {},
                "stability_analysis": {},
                "correlation_network": {},
                "correlation_risk": {},
                "market_breakdown": {},
                "analysis_timestamp": pd.Timestamp.now(),
                "data_period": {},
                "error": str(e)
            }
