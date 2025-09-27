"""
Module d'analyse de sentiment pour AIMarkets.

Ce module fournit des outils d'analyse de sentiment avancés incluant :
- Modèles GARCH pour la volatilité
- Simulations Monte Carlo
- Chaînes de Markov pour les états de marché
- Prédiction de volatilité
"""

from .garch_models import GARCHModels
from .monte_carlo import MonteCarloSimulation
from .markov_chains import MarkovChainAnalysis
from .volatility_forecasting import VolatilityForecaster

__all__ = [
    'GARCHModels',
    'MonteCarloSimulation',
    'MarkovChainAnalysis',
    'VolatilityForecaster'
]
