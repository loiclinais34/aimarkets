"""
Analyse de support et résistance pour l'analyse technique.

Ce module implémente des méthodes pour identifier les niveaux
de support et de résistance dans les données de prix.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from scipy.signal import argrelextrema

logger = logging.getLogger(__name__)


class SupportResistanceAnalyzer:
    """
    Classe pour analyser les niveaux de support et de résistance.
    
    Cette classe fournit des méthodes pour identifier les niveaux
    clés de support et de résistance dans les données de prix.
    """
    
    @staticmethod
    def calculate_pivot_points(high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, pd.Series]:
        """
        Calcule les points pivots et niveaux de support/résistance.
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            
        Returns:
            Dictionnaire contenant les niveaux de pivot
        """
        try:
            # Point pivot standard
            pivot = (high + low + close) / 3
            
            # Niveaux de résistance
            r1 = 2 * pivot - low
            r2 = pivot + (high - low)
            r3 = high + 2 * (pivot - low)
            
            # Niveaux de support
            s1 = 2 * pivot - high
            s2 = pivot - (high - low)
            s3 = low - 2 * (high - pivot)
            
            return {
                'pivot': pivot,
                'r1': r1,
                'r2': r2,
                'r3': r3,
                's1': s1,
                's2': s2,
                's3': s3
            }
        except Exception as e:
            logger.error(f"Erreur lors du calcul des points pivots: {e}")
            return {
                'pivot': pd.Series(index=high.index, dtype=float),
                'r1': pd.Series(index=high.index, dtype=float),
                'r2': pd.Series(index=high.index, dtype=float),
                'r3': pd.Series(index=high.index, dtype=float),
                's1': pd.Series(index=high.index, dtype=float),
                's2': pd.Series(index=high.index, dtype=float),
                's3': pd.Series(index=high.index, dtype=float)
            }
    
    @staticmethod
    def calculate_fibonacci_retracements(high: pd.Series, low: pd.Series, 
                                       trend_direction: str = 'up') -> Dict[str, pd.Series]:
        """
        Calcule les niveaux de retracement de Fibonacci.
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            trend_direction: Direction de la tendance ('up' ou 'down')
            
        Returns:
            Dictionnaire contenant les niveaux de Fibonacci
        """
        try:
            # Niveaux de Fibonacci
            fib_levels = [0.0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0]
            
            if trend_direction == 'up':
                # Tendance haussière - retracement depuis le haut
                swing_high = high.rolling(window=20).max()
                swing_low = low.rolling(window=20).min()
                diff = swing_high - swing_low
                
                fib_retracements = {}
                for level in fib_levels:
                    fib_retracements[f'fib_{int(level*1000)}'] = swing_high - (diff * level)
            else:
                # Tendance baissière - retracement depuis le bas
                swing_high = high.rolling(window=20).max()
                swing_low = low.rolling(window=20).min()
                diff = swing_high - swing_low
                
                fib_retracements = {}
                for level in fib_levels:
                    fib_retracements[f'fib_{int(level*1000)}'] = swing_low + (diff * level)
            
            return fib_retracements
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des retracements de Fibonacci: {e}")
            return {}
    
    @staticmethod
    def find_support_resistance_levels(high: pd.Series, low: pd.Series, close: pd.Series,
                                     window: int = 20, min_touches: int = 2) -> Dict[str, List[float]]:
        """
        Trouve les niveaux de support et de résistance basés sur les extrêmes locaux.
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            window: Fenêtre pour identifier les extrêmes
            min_touches: Nombre minimum de touches pour valider un niveau
            
        Returns:
            Dictionnaire contenant les niveaux de support et résistance
        """
        try:
            # Trouver les maxima locaux (résistance)
            resistance_indices = argrelextrema(high.values, np.greater, order=window)[0]
            resistance_levels = high.iloc[resistance_indices].values
            
            # Trouver les minima locaux (support)
            support_indices = argrelextrema(low.values, np.less, order=window)[0]
            support_levels = low.iloc[support_indices].values
            
            # Filtrer les niveaux avec suffisamment de touches
            validated_resistance = SupportResistanceAnalyzer._validate_levels(
                resistance_levels, close, min_touches
            )
            
            validated_support = SupportResistanceAnalyzer._validate_levels(
                support_levels, close, min_touches
            )
            
            return {
                'resistance_levels': validated_resistance,
                'support_levels': validated_support
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des niveaux de support/résistance: {e}")
            return {
                'resistance_levels': [],
                'support_levels': []
            }
    
    @staticmethod
    def _validate_levels(levels: np.ndarray, prices: pd.Series, min_touches: int, 
                        tolerance: float = 0.02) -> List[float]:
        """
        Valide les niveaux de support/résistance en comptant les touches.
        
        Args:
            levels: Niveaux à valider
            prices: Série de prix pour compter les touches
            min_touches: Nombre minimum de touches
            tolerance: Tolérance pour considérer une "touche"
            
        Returns:
            Liste des niveaux validés
        """
        try:
            validated_levels = []
            
            for level in levels:
                touches = 0
                
                # Compter les touches dans une fenêtre de tolérance
                for price in prices:
                    if abs(price - level) / level <= tolerance:
                        touches += 1
                
                if touches >= min_touches:
                    validated_levels.append(float(level))
            
            return validated_levels
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation des niveaux: {e}")
            return []
    
    @staticmethod
    def calculate_volume_profile(high: pd.Series, low: pd.Series, close: pd.Series,
                               volume: pd.Series, bins: int = 20) -> Dict[str, any]:
        """
        Calcule le profil de volume pour identifier les zones de prix importantes.
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            volume: Série des volumes
            bins: Nombre de bins pour le profil
            
        Returns:
            Dictionnaire contenant le profil de volume
        """
        try:
            # Créer des bins de prix
            price_range = high.max() - low.min()
            bin_size = price_range / bins
            
            # Calculer le volume par bin
            volume_profile = {}
            for i in range(bins):
                bin_low = low.min() + i * bin_size
                bin_high = low.min() + (i + 1) * bin_size
                
                # Volume dans ce bin
                mask = (close >= bin_low) & (close < bin_high)
                bin_volume = volume[mask].sum()
                
                volume_profile[f'bin_{i}'] = {
                    'price_range': (bin_low, bin_high),
                    'volume': bin_volume,
                    'center_price': (bin_low + bin_high) / 2
                }
            
            # Identifier les zones de volume élevé
            volumes = [data['volume'] for data in volume_profile.values()]
            high_volume_threshold = np.percentile(volumes, 75)
            
            high_volume_zones = []
            for bin_name, data in volume_profile.items():
                if data['volume'] >= high_volume_threshold:
                    high_volume_zones.append({
                        'price_range': data['price_range'],
                        'volume': data['volume'],
                        'center_price': data['center_price']
                    })
            
            return {
                'volume_profile': volume_profile,
                'high_volume_zones': high_volume_zones,
                'total_volume': volume.sum(),
                'price_range': (low.min(), high.max())
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du profil de volume: {e}")
            return {
                'volume_profile': {},
                'high_volume_zones': [],
                'total_volume': 0,
                'price_range': (0, 0)
            }
    
    @staticmethod
    def identify_trend_lines(high: pd.Series, low: pd.Series, close: pd.Series,
                           min_points: int = 3, max_deviation: float = 0.02) -> Dict[str, List[Dict]]:
        """
        Identifie les lignes de tendance basées sur les points pivots.
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            min_points: Nombre minimum de points pour une ligne de tendance
            max_deviation: Déviation maximale autorisée
            
        Returns:
            Dictionnaire contenant les lignes de tendance
        """
        try:
            # Trouver les points pivots
            pivot_points = SupportResistanceAnalyzer.find_support_resistance_levels(
                high, low, close, window=10, min_touches=1
            )
            
            # Identifier les lignes de tendance haussières (support)
            support_lines = SupportResistanceAnalyzer._find_trend_lines(
                pivot_points['support_levels'], 'support', min_points, max_deviation
            )
            
            # Identifier les lignes de tendance baissières (résistance)
            resistance_lines = SupportResistanceAnalyzer._find_trend_lines(
                pivot_points['resistance_levels'], 'resistance', min_points, max_deviation
            )
            
            return {
                'support_lines': support_lines,
                'resistance_lines': resistance_lines
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'identification des lignes de tendance: {e}")
            return {
                'support_lines': [],
                'resistance_lines': []
            }
    
    @staticmethod
    def _find_trend_lines(levels: List[float], line_type: str, min_points: int, 
                         max_deviation: float) -> List[Dict]:
        """
        Trouve les lignes de tendance à partir d'une liste de niveaux.
        
        Args:
            levels: Liste des niveaux de prix
            line_type: Type de ligne ('support' ou 'resistance')
            min_points: Nombre minimum de points
            max_deviation: Déviation maximale
            
        Returns:
            Liste des lignes de tendance identifiées
        """
        try:
            if len(levels) < min_points:
                return []
            
            trend_lines = []
            
            # Algorithme simplifié pour identifier les lignes de tendance
            # Dans une implémentation complète, on utiliserait des algorithmes
            # plus sophistiqués comme RANSAC ou Hough Transform
            
            # Trier les niveaux
            sorted_levels = sorted(levels)
            
            # Chercher des séquences de niveaux alignés
            for i in range(len(sorted_levels) - min_points + 1):
                sequence = sorted_levels[i:i + min_points]
                
                # Calculer la pente moyenne
                if len(sequence) >= 2:
                    slopes = []
                    for j in range(1, len(sequence)):
                        slope = (sequence[j] - sequence[0]) / j
                        slopes.append(slope)
                    
                    avg_slope = np.mean(slopes)
                    
                    # Vérifier la cohérence de la pente
                    slope_std = np.std(slopes)
                    if slope_std <= max_deviation:
                        trend_lines.append({
                            'type': line_type,
                            'slope': avg_slope,
                            'points': sequence,
                            'strength': len(sequence),
                            'deviation': slope_std
                        })
            
            return trend_lines
            
        except Exception as e:
            logger.error(f"Erreur lors de la recherche des lignes de tendance: {e}")
            return []
    
    @staticmethod
    def analyze_all_levels(high: pd.Series, low: pd.Series, close: pd.Series,
                          volume: Optional[pd.Series] = None) -> Dict[str, any]:
        """
        Effectue une analyse complète des niveaux de support et résistance.
        
        Args:
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            volume: Série des volumes (optionnel)
            
        Returns:
            Dictionnaire contenant toutes les analyses
        """
        try:
            analysis = {}
            
            # Points pivots
            analysis['pivot_points'] = SupportResistanceAnalyzer.calculate_pivot_points(high, low, close)
            
            # Retracements de Fibonacci
            analysis['fibonacci_up'] = SupportResistanceAnalyzer.calculate_fibonacci_retracements(
                high, low, 'up'
            )
            analysis['fibonacci_down'] = SupportResistanceAnalyzer.calculate_fibonacci_retracements(
                high, low, 'down'
            )
            
            # Niveaux de support/résistance
            analysis['support_resistance'] = SupportResistanceAnalyzer.find_support_resistance_levels(
                high, low, close
            )
            
            # Lignes de tendance
            analysis['trend_lines'] = SupportResistanceAnalyzer.identify_trend_lines(high, low, close)
            
            # Profil de volume (si disponible)
            if volume is not None:
                analysis['volume_profile'] = SupportResistanceAnalyzer.calculate_volume_profile(
                    high, low, close, volume
                )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse complète des niveaux: {e}")
            return {}
