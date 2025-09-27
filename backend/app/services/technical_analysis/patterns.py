"""
Patterns de chandeliers pour l'analyse technique.

Ce module implémente la détection de patterns de chandeliers japonais
utilisés dans l'analyse technique.
"""

import pandas as pd
import numpy as np
import talib
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CandlestickPatterns:
    """
    Classe pour détecter les patterns de chandeliers japonais.
    
    Cette classe fournit des méthodes pour identifier les principaux
    patterns de chandeliers utilisés dans l'analyse technique.
    """
    
    @staticmethod
    def detect_doji(open_prices: pd.Series, high: pd.Series, low: pd.Series, 
                   close: pd.Series, threshold: float = 0.1) -> pd.Series:
        """
        Détecte les patterns Doji (indécision).
        
        Args:
            open_prices: Série des prix d'ouverture
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            threshold: Seuil pour considérer un Doji (défaut: 0.1%)
            
        Returns:
            Série booléenne indiquant la présence de Doji
        """
        try:
            # Un Doji est caractérisé par une ouverture et fermeture très proches
            body_size = abs(close - open_prices)
            total_range = high - low
            
            # Éviter la division par zéro
            doji_condition = (total_range > 0) & (body_size / total_range <= threshold / 100)
            
            return doji_condition
        except Exception as e:
            logger.error(f"Erreur lors de la détection des Doji: {e}")
            return pd.Series(index=open_prices.index, dtype=bool)
    
    @staticmethod
    def detect_hammer(open_prices: pd.Series, high: pd.Series, low: pd.Series, 
                     close: pd.Series) -> pd.Series:
        """
        Détecte les patterns Hammer (marteau) - signal de retournement haussier.
        
        Args:
            open_prices: Série des prix d'ouverture
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            
        Returns:
            Série booléenne indiquant la présence de Hammer
        """
        try:
            return pd.Series(
                talib.CDLHAMMER(open_prices.values, high.values, low.values, close.values) > 0,
                index=open_prices.index
            )
        except Exception as e:
            logger.error(f"Erreur lors de la détection des Hammer: {e}")
            return pd.Series(index=open_prices.index, dtype=bool)
    
    @staticmethod
    def detect_hanging_man(open_prices: pd.Series, high: pd.Series, low: pd.Series, 
                          close: pd.Series) -> pd.Series:
        """
        Détecte les patterns Hanging Man (pendu) - signal de retournement baissier.
        
        Args:
            open_prices: Série des prix d'ouverture
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            
        Returns:
            Série booléenne indiquant la présence de Hanging Man
        """
        try:
            return pd.Series(
                talib.CDLHANGINGMAN(open_prices.values, high.values, low.values, close.values) > 0,
                index=open_prices.index
            )
        except Exception as e:
            logger.error(f"Erreur lors de la détection des Hanging Man: {e}")
            return pd.Series(index=open_prices.index, dtype=bool)
    
    @staticmethod
    def detect_engulfing(open_prices: pd.Series, high: pd.Series, low: pd.Series, 
                        close: pd.Series) -> Dict[str, pd.Series]:
        """
        Détecte les patterns Engulfing (englobant).
        
        Args:
            open_prices: Série des prix d'ouverture
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            
        Returns:
            Dictionnaire contenant les patterns Bullish et Bearish Engulfing
        """
        try:
            bullish_engulfing = pd.Series(
                talib.CDLENGULFING(open_prices.values, high.values, low.values, close.values) > 0,
                index=open_prices.index
            )
            
            bearish_engulfing = pd.Series(
                talib.CDLENGULFING(open_prices.values, high.values, low.values, close.values) < 0,
                index=open_prices.index
            )
            
            return {
                'bullish_engulfing': bullish_engulfing,
                'bearish_engulfing': bearish_engulfing
            }
        except Exception as e:
            logger.error(f"Erreur lors de la détection des Engulfing: {e}")
            return {
                'bullish_engulfing': pd.Series(index=open_prices.index, dtype=bool),
                'bearish_engulfing': pd.Series(index=open_prices.index, dtype=bool)
            }
    
    @staticmethod
    def detect_morning_star(open_prices: pd.Series, high: pd.Series, low: pd.Series, 
                           close: pd.Series) -> pd.Series:
        """
        Détecte les patterns Morning Star (étoile du matin) - signal de retournement haussier.
        
        Args:
            open_prices: Série des prix d'ouverture
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            
        Returns:
            Série booléenne indiquant la présence de Morning Star
        """
        try:
            return pd.Series(
                talib.CDLMORNINGSTAR(open_prices.values, high.values, low.values, close.values) > 0,
                index=open_prices.index
            )
        except Exception as e:
            logger.error(f"Erreur lors de la détection des Morning Star: {e}")
            return pd.Series(index=open_prices.index, dtype=bool)
    
    @staticmethod
    def detect_evening_star(open_prices: pd.Series, high: pd.Series, low: pd.Series, 
                           close: pd.Series) -> pd.Series:
        """
        Détecte les patterns Evening Star (étoile du soir) - signal de retournement baissier.
        
        Args:
            open_prices: Série des prix d'ouverture
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            
        Returns:
            Série booléenne indiquant la présence de Evening Star
        """
        try:
            return pd.Series(
                talib.CDLEVENINGSTAR(open_prices.values, high.values, low.values, close.values) > 0,
                index=open_prices.index
            )
        except Exception as e:
            logger.error(f"Erreur lors de la détection des Evening Star: {e}")
            return pd.Series(index=open_prices.index, dtype=bool)
    
    @staticmethod
    def detect_three_white_soldiers(open_prices: pd.Series, high: pd.Series, low: pd.Series, 
                                   close: pd.Series) -> pd.Series:
        """
        Détecte les patterns Three White Soldiers (trois soldats blancs) - signal de continuation haussier.
        
        Args:
            open_prices: Série des prix d'ouverture
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            
        Returns:
            Série booléenne indiquant la présence de Three White Soldiers
        """
        try:
            return pd.Series(
                talib.CDL3WHITESOLDIERS(open_prices.values, high.values, low.values, close.values) > 0,
                index=open_prices.index
            )
        except Exception as e:
            logger.error(f"Erreur lors de la détection des Three White Soldiers: {e}")
            return pd.Series(index=open_prices.index, dtype=bool)
    
    @staticmethod
    def detect_three_black_crows(open_prices: pd.Series, high: pd.Series, low: pd.Series, 
                                close: pd.Series) -> pd.Series:
        """
        Détecte les patterns Three Black Crows (trois corbeaux noirs) - signal de continuation baissier.
        
        Args:
            open_prices: Série des prix d'ouverture
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            
        Returns:
            Série booléenne indiquant la présence de Three Black Crows
        """
        try:
            return pd.Series(
                talib.CDL3BLACKCROWS(open_prices.values, high.values, low.values, close.values) > 0,
                index=open_prices.index
            )
        except Exception as e:
            logger.error(f"Erreur lors de la détection des Three Black Crows: {e}")
            return pd.Series(index=open_prices.index, dtype=bool)
    
    @staticmethod
    def detect_harami(open_prices: pd.Series, high: pd.Series, low: pd.Series, 
                     close: pd.Series) -> Dict[str, pd.Series]:
        """
        Détecte les patterns Harami (enceinte).
        
        Args:
            open_prices: Série des prix d'ouverture
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            
        Returns:
            Dictionnaire contenant les patterns Bullish et Bearish Harami
        """
        try:
            bullish_harami = pd.Series(
                talib.CDLHARAMI(open_prices.values, high.values, low.values, close.values) > 0,
                index=open_prices.index
            )
            
            bearish_harami = pd.Series(
                talib.CDLHARAMI(open_prices.values, high.values, low.values, close.values) < 0,
                index=open_prices.index
            )
            
            return {
                'bullish_harami': bullish_harami,
                'bearish_harami': bearish_harami
            }
        except Exception as e:
            logger.error(f"Erreur lors de la détection des Harami: {e}")
            return {
                'bullish_harami': pd.Series(index=open_prices.index, dtype=bool),
                'bearish_harami': pd.Series(index=open_prices.index, dtype=bool)
            }
    
    @staticmethod
    def detect_shooting_star(open_prices: pd.Series, high: pd.Series, low: pd.Series, 
                            close: pd.Series) -> pd.Series:
        """
        Détecte les patterns Shooting Star (étoile filante) - signal de retournement baissier.
        
        Args:
            open_prices: Série des prix d'ouverture
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            
        Returns:
            Série booléenne indiquant la présence de Shooting Star
        """
        try:
            return pd.Series(
                talib.CDLSHOOTINGSTAR(open_prices.values, high.values, low.values, close.values) > 0,
                index=open_prices.index
            )
        except Exception as e:
            logger.error(f"Erreur lors de la détection des Shooting Star: {e}")
            return pd.Series(index=open_prices.index, dtype=bool)
    
    @staticmethod
    def detect_inverted_hammer(open_prices: pd.Series, high: pd.Series, low: pd.Series, 
                              close: pd.Series) -> pd.Series:
        """
        Détecte les patterns Inverted Hammer (marteau inversé) - signal de retournement haussier.
        
        Args:
            open_prices: Série des prix d'ouverture
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            
        Returns:
            Série booléenne indiquant la présence de Inverted Hammer
        """
        try:
            return pd.Series(
                talib.CDLINVERTEDHAMMER(open_prices.values, high.values, low.values, close.values) > 0,
                index=open_prices.index
            )
        except Exception as e:
            logger.error(f"Erreur lors de la détection des Inverted Hammer: {e}")
            return pd.Series(index=open_prices.index, dtype=bool)
    
    @staticmethod
    def detect_all_patterns(open_prices: pd.Series, high: pd.Series, low: pd.Series, 
                           close: pd.Series) -> Dict[str, any]:
        """
        Détecte tous les patterns de chandeliers disponibles.
        
        Args:
            open_prices: Série des prix d'ouverture
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            
        Returns:
            Dictionnaire contenant tous les patterns détectés
        """
        try:
            patterns = {}
            
            # Patterns de retournement
            patterns['doji'] = CandlestickPatterns.detect_doji(open_prices, high, low, close)
            patterns['hammer'] = CandlestickPatterns.detect_hammer(open_prices, high, low, close)
            patterns['hanging_man'] = CandlestickPatterns.detect_hanging_man(open_prices, high, low, close)
            patterns['shooting_star'] = CandlestickPatterns.detect_shooting_star(open_prices, high, low, close)
            patterns['inverted_hammer'] = CandlestickPatterns.detect_inverted_hammer(open_prices, high, low, close)
            
            # Patterns d'englobement
            engulfing_patterns = CandlestickPatterns.detect_engulfing(open_prices, high, low, close)
            patterns.update(engulfing_patterns)
            
            # Patterns d'étoiles
            patterns['morning_star'] = CandlestickPatterns.detect_morning_star(open_prices, high, low, close)
            patterns['evening_star'] = CandlestickPatterns.detect_evening_star(open_prices, high, low, close)
            
            # Patterns de continuation
            patterns['three_white_soldiers'] = CandlestickPatterns.detect_three_white_soldiers(open_prices, high, low, close)
            patterns['three_black_crows'] = CandlestickPatterns.detect_three_black_crows(open_prices, high, low, close)
            
            # Patterns Harami
            harami_patterns = CandlestickPatterns.detect_harami(open_prices, high, low, close)
            patterns.update(harami_patterns)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection de tous les patterns: {e}")
            return {}
    
    @staticmethod
    def get_pattern_signals(patterns: Dict[str, any]) -> Dict[str, int]:
        """
        Analyse les patterns détectés et génère des signaux.
        
        Args:
            patterns: Dictionnaire des patterns détectés
            
        Returns:
            Dictionnaire contenant les signaux générés
        """
        try:
            signals = {
                'bullish_signals': 0,
                'bearish_signals': 0,
                'neutral_signals': 0,
                'total_patterns': 0
            }
            
            # Patterns haussiers
            bullish_patterns = [
                'hammer', 'bullish_engulfing', 'morning_star', 
                'three_white_soldiers', 'bullish_harami', 'inverted_hammer'
            ]
            
            # Patterns baissiers
            bearish_patterns = [
                'hanging_man', 'bearish_engulfing', 'evening_star',
                'three_black_crows', 'bearish_harami', 'shooting_star'
            ]
            
            # Patterns neutres
            neutral_patterns = ['doji']
            
            for pattern_name, pattern_data in patterns.items():
                if isinstance(pattern_data, pd.Series):
                    # Compter les occurrences récentes (dernières 5 périodes)
                    recent_patterns = pattern_data.tail(5).sum()
                    signals['total_patterns'] += recent_patterns
                    
                    if pattern_name in bullish_patterns:
                        signals['bullish_signals'] += recent_patterns
                    elif pattern_name in bearish_patterns:
                        signals['bearish_signals'] += recent_patterns
                    elif pattern_name in neutral_patterns:
                        signals['neutral_signals'] += recent_patterns
            
            return signals
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des signaux de patterns: {e}")
            return {
                'bullish_signals': 0,
                'bearish_signals': 0,
                'neutral_signals': 0,
                'total_patterns': 0
            }
