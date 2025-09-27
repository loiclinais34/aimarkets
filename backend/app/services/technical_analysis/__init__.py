"""
Module d'analyse technique pour AIMarkets.

Ce module fournit des outils d'analyse technique avancés incluant :
- Indicateurs techniques (RSI, MACD, Bollinger Bands, etc.)
- Patterns de chandeliers
- Support/Résistance
- Génération de signaux
"""

from .indicators import TechnicalIndicators
from .patterns import CandlestickPatterns
from .support_resistance import SupportResistanceAnalyzer
from .signals import SignalGenerator

__all__ = [
    'TechnicalIndicators',
    'CandlestickPatterns', 
    'SupportResistanceAnalyzer',
    'SignalGenerator'
]
