"""
Générateur de signaux pour l'analyse technique.

Ce module implémente la logique de génération de signaux basée
sur les indicateurs techniques et patterns de chandeliers.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from .indicators import TechnicalIndicators
from .patterns import CandlestickPatterns

logger = logging.getLogger(__name__)


class SignalGenerator:
    """
    Classe pour générer des signaux de trading basés sur l'analyse technique.
    
    Cette classe combine les indicateurs techniques et les patterns de chandeliers
    pour générer des signaux d'achat, de vente ou de maintien.
    """
    
    def __init__(self):
        self.indicators = TechnicalIndicators()
        self.patterns = CandlestickPatterns()
    
    def generate_rsi_signal(self, rsi_value: float, oversold: float = 30, 
                           overbought: float = 70) -> Dict[str, Any]:
        """
        Génère un signal basé sur le RSI.
        
        Args:
            rsi_value: Valeur actuelle du RSI
            oversold: Seuil de survente
            overbought: Seuil de surachat
            
        Returns:
            Dictionnaire contenant le signal et sa force
        """
        try:
            if rsi_value > overbought:
                strength = min((rsi_value - overbought) / (100 - overbought), 1.0)
                return {
                    "signal": "SELL",
                    "strength": strength,
                    "indicator": "RSI",
                    "value": rsi_value,
                    "reason": f"RSI suracheté ({rsi_value:.2f} > {overbought})"
                }
            elif rsi_value < oversold:
                strength = min((oversold - rsi_value) / oversold, 1.0)
                return {
                    "signal": "BUY",
                    "strength": strength,
                    "indicator": "RSI",
                    "value": rsi_value,
                    "reason": f"RSI survendu ({rsi_value:.2f} < {oversold})"
                }
            else:
                return {
                    "signal": "HOLD",
                    "strength": 0.0,
                    "indicator": "RSI",
                    "value": rsi_value,
                    "reason": f"RSI neutre ({rsi_value:.2f})"
                }
        except Exception as e:
            logger.error(f"Erreur lors de la génération du signal RSI: {e}")
            return {
                "signal": "HOLD",
                "strength": 0.0,
                "indicator": "RSI",
                "value": 0.0,
                "reason": "Erreur de calcul"
            }
    
    def generate_macd_signal(self, macd_line: float, signal_line: float, 
                           histogram: float) -> Dict[str, Any]:
        """
        Génère un signal basé sur le MACD.
        
        Args:
            macd_line: Valeur de la ligne MACD
            signal_line: Valeur de la ligne de signal
            histogram: Valeur de l'histogramme
            
        Returns:
            Dictionnaire contenant le signal et sa force
        """
        try:
            # Signal basé sur le croisement des lignes
            if macd_line > signal_line and histogram > 0:
                strength = min(abs(histogram) / max(abs(macd_line), abs(signal_line), 0.001), 1.0)
                return {
                    "signal": "BUY",
                    "strength": strength,
                    "indicator": "MACD",
                    "value": histogram,
                    "reason": f"MACD croise au-dessus du signal (histogramme: {histogram:.4f})"
                }
            elif macd_line < signal_line and histogram < 0:
                strength = min(abs(histogram) / max(abs(macd_line), abs(signal_line), 0.001), 1.0)
                return {
                    "signal": "SELL",
                    "strength": strength,
                    "indicator": "MACD",
                    "value": histogram,
                    "reason": f"MACD croise en dessous du signal (histogramme: {histogram:.4f})"
                }
            else:
                return {
                    "signal": "HOLD",
                    "strength": 0.0,
                    "indicator": "MACD",
                    "value": histogram,
                    "reason": f"MACD neutre (histogramme: {histogram:.4f})"
                }
        except Exception as e:
            logger.error(f"Erreur lors de la génération du signal MACD: {e}")
            return {
                "signal": "HOLD",
                "strength": 0.0,
                "indicator": "MACD",
                "value": 0.0,
                "reason": "Erreur de calcul"
            }
    
    def generate_bollinger_signal(self, price: float, upper_band: float, 
                                lower_band: float, middle_band: float) -> Dict[str, Any]:
        """
        Génère un signal basé sur les Bandes de Bollinger.
        
        Args:
            price: Prix actuel
            upper_band: Bande supérieure
            lower_band: Bande inférieure
            middle_band: Bande médiane
            
        Returns:
            Dictionnaire contenant le signal et sa force
        """
        try:
            band_width = upper_band - lower_band
            
            if price <= lower_band:
                # Prix touche la bande inférieure - signal d'achat
                strength = min((lower_band - price) / band_width, 1.0)
                return {
                    "signal": "BUY",
                    "strength": strength,
                    "indicator": "Bollinger Bands",
                    "value": price,
                    "reason": f"Prix touche la bande inférieure ({price:.2f} <= {lower_band:.2f})"
                }
            elif price >= upper_band:
                # Prix touche la bande supérieure - signal de vente
                strength = min((price - upper_band) / band_width, 1.0)
                return {
                    "signal": "SELL",
                    "strength": strength,
                    "indicator": "Bollinger Bands",
                    "value": price,
                    "reason": f"Prix touche la bande supérieure ({price:.2f} >= {upper_band:.2f})"
                }
            else:
                # Prix dans la bande - signal neutre
                distance_from_middle = abs(price - middle_band) / band_width
                return {
                    "signal": "HOLD",
                    "strength": 1.0 - distance_from_middle,
                    "indicator": "Bollinger Bands",
                    "value": price,
                    "reason": f"Prix dans la bande ({price:.2f})"
                }
        except Exception as e:
            logger.error(f"Erreur lors de la génération du signal Bollinger: {e}")
            return {
                "signal": "HOLD",
                "strength": 0.0,
                "indicator": "Bollinger Bands",
                "value": 0.0,
                "reason": "Erreur de calcul"
            }
    
    def generate_stochastic_signal(self, k_percent: float, d_percent: float,
                                 oversold: float = 20, overbought: float = 80) -> Dict[str, Any]:
        """
        Génère un signal basé sur l'oscillateur stochastique.
        
        Args:
            k_percent: Valeur de %K
            d_percent: Valeur de %D
            oversold: Seuil de survente
            overbought: Seuil de surachat
            
        Returns:
            Dictionnaire contenant le signal et sa force
        """
        try:
            # Signal basé sur les niveaux et le croisement
            if k_percent < oversold and d_percent < oversold and k_percent > d_percent:
                strength = min((oversold - k_percent) / oversold, 1.0)
                return {
                    "signal": "BUY",
                    "strength": strength,
                    "indicator": "Stochastic",
                    "value": k_percent,
                    "reason": f"Stochastique survendu et %K > %D ({k_percent:.2f}, {d_percent:.2f})"
                }
            elif k_percent > overbought and d_percent > overbought and k_percent < d_percent:
                strength = min((k_percent - overbought) / (100 - overbought), 1.0)
                return {
                    "signal": "SELL",
                    "strength": strength,
                    "indicator": "Stochastic",
                    "value": k_percent,
                    "reason": f"Stochastique suracheté et %K < %D ({k_percent:.2f}, {d_percent:.2f})"
                }
            else:
                return {
                    "signal": "HOLD",
                    "strength": 0.0,
                    "indicator": "Stochastic",
                    "value": k_percent,
                    "reason": f"Stochastique neutre ({k_percent:.2f}, {d_percent:.2f})"
                }
        except Exception as e:
            logger.error(f"Erreur lors de la génération du signal Stochastique: {e}")
            return {
                "signal": "HOLD",
                "strength": 0.0,
                "indicator": "Stochastic",
                "value": 0.0,
                "reason": "Erreur de calcul"
            }
    
    def generate_pattern_signal(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un signal basé sur les patterns de chandeliers.
        
        Args:
            patterns: Dictionnaire des patterns détectés
            
        Returns:
            Dictionnaire contenant le signal et sa force
        """
        try:
            # Analyser les signaux des patterns
            pattern_signals = self.patterns.get_pattern_signals(patterns)
            
            bullish_signals = pattern_signals.get('bullish_signals', 0)
            bearish_signals = pattern_signals.get('bearish_signals', 0)
            total_patterns = pattern_signals.get('total_patterns', 0)
            
            if total_patterns == 0:
                return {
                    "signal": "HOLD",
                    "strength": 0.0,
                    "indicator": "Candlestick Patterns",
                    "value": 0,
                    "reason": "Aucun pattern détecté"
                }
            
            # Calculer le ratio de signaux
            bullish_ratio = bullish_signals / total_patterns
            bearish_ratio = bearish_signals / total_patterns
            
            if bullish_ratio > 0.6:
                return {
                    "signal": "BUY",
                    "strength": bullish_ratio,
                    "indicator": "Candlestick Patterns",
                    "value": bullish_signals,
                    "reason": f"Patterns haussiers dominants ({bullish_signals}/{total_patterns})"
                }
            elif bearish_ratio > 0.6:
                return {
                    "signal": "SELL",
                    "strength": bearish_ratio,
                    "indicator": "Candlestick Patterns",
                    "value": bearish_signals,
                    "reason": f"Patterns baissiers dominants ({bearish_signals}/{total_patterns})"
                }
            else:
                return {
                    "signal": "HOLD",
                    "strength": 0.0,
                    "indicator": "Candlestick Patterns",
                    "value": total_patterns,
                    "reason": f"Patterns mixtes ({bullish_signals} haussiers, {bearish_signals} baissiers)"
                }
        except Exception as e:
            logger.error(f"Erreur lors de la génération du signal de patterns: {e}")
            return {
                "signal": "HOLD",
                "strength": 0.0,
                "indicator": "Candlestick Patterns",
                "value": 0,
                "reason": "Erreur de calcul"
            }
    
    def generate_composite_signal(self, indicators: Dict[str, Any], 
                                patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un signal composite basé sur tous les indicateurs et patterns.
        
        Args:
            indicators: Dictionnaire des indicateurs techniques
            patterns: Dictionnaire des patterns de chandeliers
            
        Returns:
            Dictionnaire contenant le signal composite
        """
        try:
            signals = []
            weights = {
                'RSI': 0.2,
                'MACD': 0.25,
                'Bollinger Bands': 0.2,
                'Stochastic': 0.15,
                'Candlestick Patterns': 0.2
            }
            
            # RSI
            if 'rsi' in indicators and not indicators['rsi'].empty:
                rsi_value = indicators['rsi'].iloc[-1]
                rsi_signal = self.generate_rsi_signal(rsi_value)
                rsi_signal['weight'] = weights['RSI']
                signals.append(rsi_signal)
            
            # MACD
            if 'macd' in indicators and not indicators['macd']['histogram'].empty:
                macd_hist = indicators['macd']['histogram'].iloc[-1]
                macd_line = indicators['macd']['macd'].iloc[-1]
                signal_line = indicators['macd']['signal'].iloc[-1]
                macd_signal = self.generate_macd_signal(macd_line, signal_line, macd_hist)
                macd_signal['weight'] = weights['MACD']
                signals.append(macd_signal)
            
            # Bollinger Bands
            if 'bollinger_bands' in indicators:
                bb = indicators['bollinger_bands']
                if not bb['upper'].empty:
                    # Utiliser le dernier prix disponible
                    price = bb['middle'].iloc[-1]  # Approximation
                    upper = bb['upper'].iloc[-1]
                    lower = bb['lower'].iloc[-1]
                    middle = bb['middle'].iloc[-1]
                    bb_signal = self.generate_bollinger_signal(price, upper, lower, middle)
                    bb_signal['weight'] = weights['Bollinger Bands']
                    signals.append(bb_signal)
            
            # Stochastic
            if 'stochastic' in indicators and not indicators['stochastic']['k_percent'].empty:
                k_percent = indicators['stochastic']['k_percent'].iloc[-1]
                d_percent = indicators['stochastic']['d_percent'].iloc[-1]
                stoch_signal = self.generate_stochastic_signal(k_percent, d_percent)
                stoch_signal['weight'] = weights['Stochastic']
                signals.append(stoch_signal)
            
            # Patterns
            pattern_signal = self.generate_pattern_signal(patterns)
            pattern_signal['weight'] = weights['Candlestick Patterns']
            signals.append(pattern_signal)
            
            # Calculer le signal composite
            buy_strength = 0.0
            sell_strength = 0.0
            total_weight = 0.0
            
            for signal in signals:
                weight = signal.get('weight', 0.0)
                total_weight += weight
                
                if signal['signal'] == 'BUY':
                    buy_strength += signal['strength'] * weight
                elif signal['signal'] == 'SELL':
                    sell_strength += signal['strength'] * weight
            
            # Normaliser les forces
            if total_weight > 0:
                buy_strength /= total_weight
                sell_strength /= total_weight
            
            # Déterminer le signal final
            if buy_strength > sell_strength and buy_strength > 0.3:
                final_signal = "BUY"
                final_strength = buy_strength
            elif sell_strength > buy_strength and sell_strength > 0.3:
                final_signal = "SELL"
                final_strength = sell_strength
            else:
                final_signal = "HOLD"
                final_strength = 0.0
            
            return {
                "signal": final_signal,
                "strength": final_strength,
                "indicator": "Composite",
                "value": len(signals),
                "reason": f"Signal composite basé sur {len(signals)} indicateurs",
                "individual_signals": signals,
                "buy_strength": buy_strength,
                "sell_strength": sell_strength
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du signal composite: {e}")
            return {
                "signal": "HOLD",
                "strength": 0.0,
                "indicator": "Composite",
                "value": 0,
                "reason": "Erreur de calcul",
                "individual_signals": [],
                "buy_strength": 0.0,
                "sell_strength": 0.0
            }
    
    def analyze_symbol(self, symbol: str, high: pd.Series, low: pd.Series, 
                      close: pd.Series, open_prices: pd.Series,
                      volume: Optional[pd.Series] = None) -> Dict[str, Any]:
        """
        Effectue une analyse complète d'un symbole et génère tous les signaux.
        
        Args:
            symbol: Symbole à analyser
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            open_prices: Série des prix d'ouverture
            volume: Série des volumes (optionnel)
            
        Returns:
            Dictionnaire contenant l'analyse complète
        """
        try:
            # Calculer tous les indicateurs
            indicators = self.indicators.calculate_all_indicators(high, low, close, volume)
            
            # Détecter tous les patterns
            patterns = self.patterns.detect_all_patterns(open_prices, high, low, close)
            
            # Générer le signal composite
            composite_signal = self.generate_composite_signal(indicators, patterns)
            
            return {
                "symbol": symbol,
                "timestamp": close.index[-1] if not close.empty else None,
                "indicators": indicators,
                "patterns": patterns,
                "composite_signal": composite_signal,
                "analysis_summary": {
                    "total_indicators": len(indicators),
                    "total_patterns": len(patterns),
                    "signal_strength": composite_signal["strength"],
                    "recommendation": composite_signal["signal"]
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse du symbole {symbol}: {e}")
            return {
                "symbol": symbol,
                "timestamp": None,
                "indicators": {},
                "patterns": {},
                "composite_signal": {
                    "signal": "HOLD",
                    "strength": 0.0,
                    "indicator": "Error",
                    "value": 0,
                    "reason": f"Erreur d'analyse: {str(e)}"
                },
                "analysis_summary": {
                    "total_indicators": 0,
                    "total_patterns": 0,
                    "signal_strength": 0.0,
                    "recommendation": "HOLD"
                }
            }
