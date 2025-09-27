"""
Générateur de signaux avancé pour l'analyse technique.

Ce module implémente un système de génération de signaux sophistiqué avec :
- Pondération dynamique des indicateurs
- Système de scoring (0-100)
- Niveaux de confiance
- Historique des signaux
- Intégration avec les modèles ML
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Union
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json

from .indicators import TechnicalIndicators
from .patterns import CandlestickPatterns

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types de signaux possibles."""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    WEAK_BUY = "WEAK_BUY"
    HOLD = "HOLD"
    WEAK_SELL = "WEAK_SELL"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class ConfidenceLevel(Enum):
    """Niveaux de confiance des signaux."""
    VERY_HIGH = "VERY_HIGH"  # 90-100%
    HIGH = "HIGH"           # 70-89%
    MEDIUM = "MEDIUM"       # 50-69%
    LOW = "LOW"            # 30-49%
    VERY_LOW = "VERY_LOW"   # 0-29%


@dataclass
class SignalResult:
    """Structure pour stocker un résultat de signal."""
    signal_type: SignalType
    score: float  # 0-100
    confidence: float  # 0-1
    confidence_level: ConfidenceLevel
    strength: float  # 0-1
    timestamp: datetime
    indicators_used: List[str]
    reasoning: str
    individual_signals: List[Dict[str, Any]]
    ml_signal: Optional[Dict[str, Any]] = None
    risk_level: str = "MEDIUM"
    time_horizon: str = "SHORT_TERM"


class AdvancedSignalGenerator:
    """
    Générateur de signaux avancé avec pondération, scoring et confiance.
    
    Cette classe améliore le générateur de signaux de base en ajoutant :
    - Pondération dynamique basée sur la performance historique
    - Système de scoring sophistiqué (0-100)
    - Calcul de confiance basé sur la cohérence des signaux
    - Historique des signaux pour l'apprentissage
    - Intégration avec les modèles ML
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialise le générateur de signaux avancé.
        
        Args:
            config: Configuration personnalisée (optionnel)
        """
        self.indicators = TechnicalIndicators()
        self.patterns = CandlestickPatterns()
        
        # Configuration par défaut
        self.config = {
            "weights": {
                "RSI": 0.15,
                "MACD": 0.20,
                "Bollinger_Bands": 0.15,
                "Stochastic": 0.10,
                "Williams_R": 0.08,
                "CCI": 0.08,
                "ADX": 0.10,
                "Parabolic_SAR": 0.08,
                "Ichimoku": 0.06
            },
            "scoring": {
                "strong_buy_threshold": 80,
                "buy_threshold": 60,
                "weak_buy_threshold": 45,
                "hold_threshold": 30,
                "weak_sell_threshold": 20,
                "sell_threshold": 10,
                "strong_sell_threshold": 0
            },
            "confidence": {
                "very_high_threshold": 0.9,
                "high_threshold": 0.7,
                "medium_threshold": 0.5,
                "low_threshold": 0.3
            },
            "ml_integration": {
                "enabled": True,
                "ml_weight": 0.3,  # Poids du signal ML dans le score final
                "technical_weight": 0.7  # Poids des signaux techniques
            }
        }
        
        # Mettre à jour avec la configuration personnalisée
        if config:
            self._update_config(config)
        
        # Historique des signaux pour l'apprentissage
        self.signal_history: List[SignalResult] = []
        self.performance_metrics: Dict[str, float] = {}
        
    def _update_config(self, config: Dict[str, Any]):
        """Met à jour la configuration avec les valeurs personnalisées."""
        for key, value in config.items():
            if key in self.config:
                if isinstance(value, dict):
                    self.config[key].update(value)
                else:
                    self.config[key] = value
    
    def calculate_dynamic_weights(self, symbol: str, lookback_days: int = 30) -> Dict[str, float]:
        """
        Calcule des poids dynamiques basés sur la performance historique.
        
        Args:
            symbol: Symbole à analyser
            lookback_days: Nombre de jours pour l'analyse historique
            
        Returns:
            Dictionnaire des poids dynamiques
        """
        try:
            # Pour l'instant, retourner les poids par défaut
            # TODO: Implémenter l'analyse de performance historique
            return self.config["weights"].copy()
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des poids dynamiques: {e}")
            return self.config["weights"].copy()
    
    def generate_enhanced_rsi_signal(self, rsi_value: float, rsi_series: pd.Series,
                                   oversold: float = 30, overbought: float = 70) -> Dict[str, Any]:
        """
        Génère un signal RSI amélioré avec analyse de tendance.
        
        Args:
            rsi_value: Valeur actuelle du RSI
            rsi_series: Série historique du RSI
            oversold: Seuil de survente
            overbought: Seuil de surachat
            
        Returns:
            Dictionnaire contenant le signal amélioré
        """
        try:
            # Signal de base
            if rsi_value > overbought:
                base_signal = "SELL"
                base_strength = min((rsi_value - overbought) / (100 - overbought), 1.0)
            elif rsi_value < oversold:
                base_signal = "BUY"
                base_strength = min((oversold - rsi_value) / oversold, 1.0)
            else:
                base_signal = "HOLD"
                base_strength = 0.0
            
            # Analyse de tendance
            trend_strength = 0.0
            if len(rsi_series) >= 5:
                recent_trend = rsi_series.tail(5).diff().mean()
                if base_signal == "BUY" and recent_trend > 0:
                    trend_strength = min(abs(recent_trend) / 10, 0.3)
                elif base_signal == "SELL" and recent_trend < 0:
                    trend_strength = min(abs(recent_trend) / 10, 0.3)
            
            # Divergence (simplifiée)
            divergence_bonus = 0.0
            if len(rsi_series) >= 20:
                # Détection simple de divergence
                rsi_high = rsi_series.tail(20).max()
                rsi_low = rsi_series.tail(20).min()
                if base_signal == "BUY" and rsi_value < rsi_low + (rsi_high - rsi_low) * 0.3:
                    divergence_bonus = 0.1
                elif base_signal == "SELL" and rsi_value > rsi_high - (rsi_high - rsi_low) * 0.3:
                    divergence_bonus = 0.1
            
            # Score final
            final_strength = min(base_strength + trend_strength + divergence_bonus, 1.0)
            score = final_strength * 100
            
            return {
                "signal": base_signal,
                "strength": final_strength,
                "score": score,
                "indicator": "RSI",
                "value": rsi_value,
                "reasoning": f"RSI {base_signal.lower()} ({rsi_value:.2f}) avec tendance {trend_strength:.2f}",
                "trend_strength": trend_strength,
                "divergence_bonus": divergence_bonus
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du signal RSI amélioré: {e}")
            return {
                "signal": "HOLD",
                "strength": 0.0,
                "score": 50.0,
                "indicator": "RSI",
                "value": 0.0,
                "reasoning": "Erreur de calcul",
                "trend_strength": 0.0,
                "divergence_bonus": 0.0
            }
    
    def generate_enhanced_macd_signal(self, macd_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """
        Génère un signal MACD amélioré avec analyse de momentum.
        
        Args:
            macd_data: Dictionnaire contenant macd, signal, histogram
            
        Returns:
            Dictionnaire contenant le signal amélioré
        """
        try:
            macd_line = macd_data['macd'].iloc[-1]
            signal_line = macd_data['signal'].iloc[-1]
            histogram = macd_data['histogram'].iloc[-1]
            
            # Signal de base
            if macd_line > signal_line and histogram > 0:
                base_signal = "BUY"
                base_strength = min(abs(histogram) / max(abs(macd_line), abs(signal_line), 0.001), 1.0)
            elif macd_line < signal_line and histogram < 0:
                base_signal = "SELL"
                base_strength = min(abs(histogram) / max(abs(macd_line), abs(signal_line), 0.001), 1.0)
            else:
                base_signal = "HOLD"
                base_strength = 0.0
            
            # Analyse de momentum
            momentum_bonus = 0.0
            if len(macd_data['histogram']) >= 3:
                recent_momentum = macd_data['histogram'].tail(3).diff().sum()
                if base_signal == "BUY" and recent_momentum > 0:
                    momentum_bonus = min(abs(recent_momentum) / 10, 0.2)
                elif base_signal == "SELL" and recent_momentum < 0:
                    momentum_bonus = min(abs(recent_momentum) / 10, 0.2)
            
            # Score final
            final_strength = min(base_strength + momentum_bonus, 1.0)
            score = final_strength * 100
            
            return {
                "signal": base_signal,
                "strength": final_strength,
                "score": score,
                "indicator": "MACD",
                "value": histogram,
                "reasoning": f"MACD {base_signal.lower()} (hist: {histogram:.4f}) avec momentum {momentum_bonus:.2f}",
                "momentum_bonus": momentum_bonus
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du signal MACD amélioré: {e}")
            return {
                "signal": "HOLD",
                "strength": 0.0,
                "score": 50.0,
                "indicator": "MACD",
                "value": 0.0,
                "reasoning": "Erreur de calcul",
                "momentum_bonus": 0.0
            }
    
    def calculate_signal_confidence(self, individual_signals: List[Dict[str, Any]]) -> float:
        """
        Calcule le niveau de confiance basé sur la cohérence des signaux.
        
        Args:
            individual_signals: Liste des signaux individuels
            
        Returns:
            Niveau de confiance (0-1)
        """
        try:
            if not individual_signals:
                return 0.0
            
            # Compter les signaux par type
            signal_counts = {"BUY": 0, "SELL": 0, "HOLD": 0}
            total_strength = 0.0
            
            for signal in individual_signals:
                signal_type = signal.get("signal", "HOLD")
                strength = signal.get("strength", 0.0)
                
                if signal_type in signal_counts:
                    signal_counts[signal_type] += 1
                total_strength += strength
            
            # Calculer la cohérence
            total_signals = len(individual_signals)
            max_count = max(signal_counts.values())
            consistency = max_count / total_signals if total_signals > 0 else 0.0
            
            # Calculer la force moyenne
            avg_strength = total_strength / total_signals if total_signals > 0 else 0.0
            
            # Confiance = cohérence * force moyenne
            confidence = consistency * avg_strength
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la confiance: {e}")
            return 0.0
    
    def determine_signal_type(self, score: float) -> SignalType:
        """
        Détermine le type de signal basé sur le score.
        
        Args:
            score: Score du signal (0-100)
            
        Returns:
            Type de signal
        """
        thresholds = self.config["scoring"]
        
        if score >= thresholds["strong_buy_threshold"]:
            return SignalType.STRONG_BUY
        elif score >= thresholds["buy_threshold"]:
            return SignalType.BUY
        elif score >= thresholds["weak_buy_threshold"]:
            return SignalType.WEAK_BUY
        elif score >= thresholds["hold_threshold"]:
            return SignalType.HOLD
        elif score >= thresholds["weak_sell_threshold"]:
            return SignalType.WEAK_SELL
        elif score >= thresholds["sell_threshold"]:
            return SignalType.SELL
        else:
            return SignalType.STRONG_SELL
    
    def determine_confidence_level(self, confidence: float) -> ConfidenceLevel:
        """
        Détermine le niveau de confiance basé sur la valeur.
        
        Args:
            confidence: Valeur de confiance (0-1)
            
        Returns:
            Niveau de confiance
        """
        thresholds = self.config["confidence"]
        
        if confidence >= thresholds["very_high_threshold"]:
            return ConfidenceLevel.VERY_HIGH
        elif confidence >= thresholds["high_threshold"]:
            return ConfidenceLevel.HIGH
        elif confidence >= thresholds["medium_threshold"]:
            return ConfidenceLevel.MEDIUM
        elif confidence >= thresholds["low_threshold"]:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW
    
    def integrate_ml_signal(self, ml_prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intègre un signal ML dans le système de scoring.
        
        Args:
            ml_prediction: Prédiction du modèle ML
            
        Returns:
            Signal ML formaté
        """
        try:
            prediction = ml_prediction.get("prediction", 0)
            confidence = ml_prediction.get("confidence", 0.5)
            
            # Convertir la prédiction ML en signal
            if prediction == 1:  # Opportunité positive
                signal = "BUY"
                score = confidence * 100
            else:  # Opportunité négative
                signal = "SELL"
                score = (1 - confidence) * 100
            
            return {
                "signal": signal,
                "strength": confidence,
                "score": score,
                "indicator": "ML_Model",
                "value": prediction,
                "reasoning": f"Modèle ML: {signal} (confiance: {confidence:.2f})",
                "model_name": ml_prediction.get("model_name", "Unknown"),
                "weight": self.config["ml_integration"]["ml_weight"],
                "model_type": ml_prediction.get("model_type", "Unknown")
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'intégration du signal ML: {e}")
            return {
                "signal": "HOLD",
                "strength": 0.0,
                "score": 50.0,
                "indicator": "ML_Model",
                "value": 0,
                "reasoning": "Erreur d'intégration ML",
                "model_name": "Unknown",
                "model_type": "Unknown"
            }
    
    def generate_advanced_signal(self, symbol: str, high: pd.Series, low: pd.Series,
                               close: pd.Series, open_prices: pd.Series,
                               volume: Optional[pd.Series] = None,
                               ml_prediction: Optional[Dict[str, Any]] = None) -> SignalResult:
        """
        Génère un signal avancé avec tous les indicateurs et l'intégration ML.
        
        Args:
            symbol: Symbole à analyser
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            open_prices: Série des prix d'ouverture
            volume: Série des volumes (optionnel)
            ml_prediction: Prédiction du modèle ML (optionnel)
            
        Returns:
            SignalResult avec tous les détails
        """
        try:
            # Calculer tous les indicateurs
            indicators = self.indicators.calculate_all_indicators(high, low, close, volume)
            
            # Détecter tous les patterns
            patterns = self.patterns.detect_all_patterns(open_prices, high, low, close)
            
            # Générer les signaux individuels améliorés
            individual_signals = []
            weights = self.calculate_dynamic_weights(symbol)
            
            # RSI amélioré
            if 'rsi' in indicators and not indicators['rsi'].empty:
                rsi_signal = self.generate_enhanced_rsi_signal(
                    indicators['rsi'].iloc[-1], indicators['rsi']
                )
                rsi_signal['weight'] = weights['RSI']
                individual_signals.append(rsi_signal)
            
            # MACD amélioré
            if 'macd' in indicators and not indicators['macd']['histogram'].empty:
                macd_signal = self.generate_enhanced_macd_signal(indicators['macd'])
                macd_signal['weight'] = weights['MACD']
                individual_signals.append(macd_signal)
            
            # Bollinger Bands
            if 'bollinger_bands' in indicators:
                bb = indicators['bollinger_bands']
                if not bb['upper'].empty:
                    price = close.iloc[-1]
                    upper = bb['upper'].iloc[-1]
                    lower = bb['lower'].iloc[-1]
                    middle = bb['middle'].iloc[-1]
                    
                    if price <= lower:
                        signal = "BUY"
                        strength = min((lower - price) / (upper - lower), 1.0)
                    elif price >= upper:
                        signal = "SELL"
                        strength = min((price - upper) / (upper - lower), 1.0)
                    else:
                        signal = "HOLD"
                        strength = 0.0
                    
                    bb_signal = {
                        "signal": signal,
                        "strength": strength,
                        "score": strength * 100,
                        "indicator": "Bollinger_Bands",
                        "value": price,
                        "reasoning": f"Prix {signal.lower()} par rapport aux bandes",
                        "weight": weights['Bollinger_Bands']
                    }
                    individual_signals.append(bb_signal)
            
            # Stochastic Oscillator
            if 'stochastic' in indicators:
                stoch = indicators['stochastic']
                if isinstance(stoch, dict) and 'k_percent' in stoch and 'd_percent' in stoch:
                    if not stoch['k_percent'].empty and not stoch['d_percent'].empty:
                        k_percent = stoch['k_percent'].iloc[-1]
                        d_percent = stoch['d_percent'].iloc[-1]
                        
                        if k_percent > 80 and d_percent > 80:
                            signal = "SELL"
                            strength = min((k_percent - 80) / 20, 1.0)
                        elif k_percent < 20 and d_percent < 20:
                            signal = "BUY"
                            strength = min((20 - k_percent) / 20, 1.0)
                        elif k_percent > d_percent:
                            signal = "BUY"
                            strength = min((k_percent - d_percent) / 20, 0.5)
                        elif k_percent < d_percent:
                            signal = "SELL"
                            strength = min((d_percent - k_percent) / 20, 0.5)
                        else:
                            signal = "HOLD"
                            strength = 0.0
                        
                        stoch_signal = {
                            "signal": signal,
                            "strength": strength,
                            "score": strength * 100,
                            "indicator": "Stochastic",
                            "value": k_percent,
                            "reasoning": f"Stochastic K={k_percent:.1f}%, D={d_percent:.1f}%",
                            "weight": weights['Stochastic']
                        }
                        individual_signals.append(stoch_signal)
            
            # Williams %R
            if 'williams_r' in indicators:
                try:
                    williams_r_series = indicators['williams_r']
                    if hasattr(williams_r_series, 'empty') and not williams_r_series.empty:
                        williams_r = williams_r_series.iloc[-1]
                        
                        if williams_r > -20:
                            signal = "SELL"
                            strength = min((williams_r + 20) / 20, 1.0)
                        elif williams_r < -80:
                            signal = "BUY"
                            strength = min((-80 - williams_r) / 20, 1.0)
                        else:
                            signal = "HOLD"
                            strength = 0.0
                        
                        williams_signal = {
                            "signal": signal,
                            "strength": strength,
                            "score": strength * 100,
                            "indicator": "Williams_R",
                            "value": williams_r,
                            "reasoning": f"Williams %R = {williams_r:.1f}%",
                            "weight": weights['Williams_R']
                        }
                        individual_signals.append(williams_signal)
                except Exception as e:
                    logger.warning(f"Erreur Williams %R: {e}")
            
            # CCI (Commodity Channel Index)
            if 'cci' in indicators:
                try:
                    cci_series = indicators['cci']
                    if hasattr(cci_series, 'empty') and not cci_series.empty:
                        cci = cci_series.iloc[-1]
                        
                        if cci > 100:
                            signal = "BUY"
                            strength = min((cci - 100) / 100, 1.0)
                        elif cci < -100:
                            signal = "SELL"
                            strength = min((-100 - cci) / 100, 1.0)
                        else:
                            signal = "HOLD"
                            strength = 0.0
                        
                        cci_signal = {
                            "signal": signal,
                            "strength": strength,
                            "score": strength * 100,
                            "indicator": "CCI",
                            "value": cci,
                            "reasoning": f"CCI = {cci:.1f}",
                            "weight": weights['CCI']
                        }
                        individual_signals.append(cci_signal)
                except Exception as e:
                    logger.warning(f"Erreur CCI: {e}")
            
            # ADX (Average Directional Index)
            if 'adx' in indicators:
                try:
                    adx_series = indicators['adx']
                    if hasattr(adx_series, 'empty') and not adx_series.empty:
                        adx = adx_series.iloc[-1]
                        
                        if adx > 25:
                            # ADX élevé = tendance forte
                            signal = "HOLD"  # ADX ne donne pas de direction
                            strength = min((adx - 25) / 25, 1.0)
                        else:
                            signal = "HOLD"
                            strength = 0.0
                        
                        adx_signal = {
                            "signal": signal,
                            "strength": strength,
                            "score": strength * 100,
                            "indicator": "ADX",
                            "value": adx,
                            "reasoning": f"ADX = {adx:.1f} (force de tendance)",
                            "weight": weights['ADX']
                        }
                        individual_signals.append(adx_signal)
                except Exception as e:
                    logger.warning(f"Erreur ADX: {e}")
            
            # Parabolic SAR
            if 'parabolic_sar' in indicators:
                try:
                    sar_series = indicators['parabolic_sar']
                    if hasattr(sar_series, 'empty') and not sar_series.empty:
                        sar = sar_series.iloc[-1]
                        current_price = close.iloc[-1]
                        
                        if current_price > sar:
                            signal = "BUY"
                            strength = min((current_price - sar) / sar * 10, 1.0)
                        elif current_price < sar:
                            signal = "SELL"
                            strength = min((sar - current_price) / sar * 10, 1.0)
                        else:
                            signal = "HOLD"
                            strength = 0.0
                        
                        sar_signal = {
                            "signal": signal,
                            "strength": strength,
                            "score": strength * 100,
                            "indicator": "Parabolic_SAR",
                            "value": sar,
                            "reasoning": f"SAR = {sar:.2f}, Prix = {current_price:.2f}",
                            "weight": weights['Parabolic_SAR']
                        }
                        individual_signals.append(sar_signal)
                except Exception as e:
                    logger.warning(f"Erreur Parabolic SAR: {e}")
            
            # Ichimoku Cloud
            if 'ichimoku' in indicators:
                try:
                    ichimoku = indicators['ichimoku']
                    if isinstance(ichimoku, dict) and all(key in ichimoku for key in ['tenkan', 'kijun', 'senkou_a', 'senkou_b']):
                        if all(hasattr(ichimoku[key], 'empty') and not ichimoku[key].empty for key in ['tenkan', 'kijun', 'senkou_a', 'senkou_b']):
                            current_price = close.iloc[-1]
                            tenkan = ichimoku['tenkan'].iloc[-1]
                            kijun = ichimoku['kijun'].iloc[-1]
                            senkou_a = ichimoku['senkou_a'].iloc[-1]
                            senkou_b = ichimoku['senkou_b'].iloc[-1]
                            
                            # Logique Ichimoku simplifiée
                            cloud_top = max(senkou_a, senkou_b)
                            cloud_bottom = min(senkou_a, senkou_b)
                            
                            if current_price > cloud_top and tenkan > kijun:
                                signal = "BUY"
                                strength = 0.8
                            elif current_price < cloud_bottom and tenkan < kijun:
                                signal = "SELL"
                                strength = 0.8
                            elif current_price > cloud_bottom and current_price < cloud_top:
                                signal = "HOLD"
                                strength = 0.3
                            else:
                                signal = "HOLD"
                                strength = 0.0
                            
                            ichimoku_signal = {
                                "signal": signal,
                                "strength": strength,
                                "score": strength * 100,
                                "indicator": "Ichimoku",
                                "value": current_price,
                                "reasoning": f"Prix dans le nuage Ichimoku (Tenkan={tenkan:.2f}, Kijun={kijun:.2f})",
                                "weight": weights['Ichimoku']
                            }
                            individual_signals.append(ichimoku_signal)
                except Exception as e:
                    logger.warning(f"Erreur Ichimoku: {e}")
            
            # Intégrer le signal ML si disponible
            ml_signal = None
            if ml_prediction and self.config["ml_integration"]["enabled"]:
                ml_signal = self.integrate_ml_signal(ml_prediction)
                individual_signals.append(ml_signal)
            
            # S'assurer que tous les signaux ont une clé 'weight'
            for signal in individual_signals:
                if 'weight' not in signal:
                    signal['weight'] = 0.1  # Poids par défaut
            
            # Calculer le score composite pondéré
            total_score = 0.0
            total_weight = 0.0
            
            for signal in individual_signals:
                weight = signal.get('weight', 0.0)
                score = signal.get('score', 50.0)
                
                # Ajuster le score selon le type de signal
                if signal['signal'] == 'BUY':
                    adjusted_score = score
                elif signal['signal'] == 'SELL':
                    adjusted_score = 100 - score
                else:  # HOLD
                    adjusted_score = 50.0
                
                total_score += adjusted_score * weight
                total_weight += weight
            
            # Score final
            final_score = total_score / total_weight if total_weight > 0 else 50.0
            
            # Calculer la confiance
            confidence = self.calculate_signal_confidence(individual_signals)
            
            # Déterminer le type de signal et le niveau de confiance
            signal_type = self.determine_signal_type(final_score)
            confidence_level = self.determine_confidence_level(confidence)
            
            # Calculer la force du signal
            if signal_type in [SignalType.STRONG_BUY, SignalType.STRONG_SELL]:
                strength = 0.9
            elif signal_type in [SignalType.BUY, SignalType.SELL]:
                strength = 0.7
            elif signal_type in [SignalType.WEAK_BUY, SignalType.WEAK_SELL]:
                strength = 0.5
            else:  # HOLD
                strength = 0.0
            
            # Créer le résultat
            result = SignalResult(
                signal_type=signal_type,
                score=final_score,
                confidence=confidence,
                confidence_level=confidence_level,
                strength=strength,
                timestamp=datetime.now(),
                indicators_used=[s['indicator'] for s in individual_signals],
                reasoning=f"Signal {signal_type.value} basé sur {len(individual_signals)} indicateurs",
                individual_signals=individual_signals,
                ml_signal=ml_signal,
                risk_level="MEDIUM",  # TODO: Calculer basé sur la volatilité
                time_horizon="SHORT_TERM"  # TODO: Déterminer basé sur les indicateurs
            )
            
            # Ajouter à l'historique
            self.signal_history.append(result)
            
            # Limiter l'historique à 1000 entrées
            if len(self.signal_history) > 1000:
                self.signal_history = self.signal_history[-1000:]
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du signal avancé pour {symbol}: {e}")
            return SignalResult(
                signal_type=SignalType.HOLD,
                score=50.0,
                confidence=0.0,
                confidence_level=ConfidenceLevel.VERY_LOW,
                strength=0.0,
                timestamp=datetime.now(),
                indicators_used=[],
                reasoning=f"Erreur d'analyse: {str(e)}",
                individual_signals=[],
                ml_signal=None,
                risk_level="HIGH",
                time_horizon="SHORT_TERM"
            )
    
    def get_signal_history(self, symbol: Optional[str] = None, 
                          days: int = 30) -> List[SignalResult]:
        """
        Récupère l'historique des signaux.
        
        Args:
            symbol: Symbole à filtrer (optionnel)
            days: Nombre de jours à récupérer
            
        Returns:
            Liste des signaux historiques
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            if symbol:
                filtered_history = [
                    signal for signal in self.signal_history
                    if signal.timestamp >= cutoff_date
                    # TODO: Ajouter le symbole au SignalResult
                ]
            else:
                filtered_history = [
                    signal for signal in self.signal_history
                    if signal.timestamp >= cutoff_date
                ]
            
            return filtered_history
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'historique: {e}")
            return []
    
    def calculate_performance_metrics(self, days: int = 30) -> Dict[str, float]:
        """
        Calcule les métriques de performance des signaux.
        
        Args:
            days: Nombre de jours pour l'analyse
            
        Returns:
            Dictionnaire des métriques de performance
        """
        try:
            recent_signals = self.get_signal_history(days=days)
            
            if not recent_signals:
                return {}
            
            # Calculer les métriques de base
            total_signals = len(recent_signals)
            buy_signals = len([s for s in recent_signals if s.signal_type.value.startswith('BUY')])
            sell_signals = len([s for s in recent_signals if s.signal_type.value.startswith('SELL')])
            hold_signals = len([s for s in recent_signals if s.signal_type == SignalType.HOLD])
            
            avg_confidence = sum(s.confidence for s in recent_signals) / total_signals
            avg_score = sum(s.score for s in recent_signals) / total_signals
            
            return {
                "total_signals": total_signals,
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "hold_signals": hold_signals,
                "buy_ratio": buy_signals / total_signals if total_signals > 0 else 0.0,
                "sell_ratio": sell_signals / total_signals if total_signals > 0 else 0.0,
                "hold_ratio": hold_signals / total_signals if total_signals > 0 else 0.0,
                "avg_confidence": avg_confidence,
                "avg_score": avg_score
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des métriques de performance: {e}")
            return {}
    
    def export_signal_history(self, filepath: str, format: str = "json") -> bool:
        """
        Exporte l'historique des signaux vers un fichier.
        
        Args:
            filepath: Chemin du fichier de destination
            format: Format d'export ("json" ou "csv")
            
        Returns:
            True si l'export a réussi, False sinon
        """
        try:
            if format == "json":
                # Convertir les SignalResult en dictionnaires
                history_data = []
                for signal in self.signal_history:
                    signal_dict = {
                        "signal_type": signal.signal_type.value,
                        "score": signal.score,
                        "confidence": signal.confidence,
                        "confidence_level": signal.confidence_level.value,
                        "strength": signal.strength,
                        "timestamp": signal.timestamp.isoformat(),
                        "indicators_used": signal.indicators_used,
                        "reasoning": signal.reasoning,
                        "risk_level": signal.risk_level,
                        "time_horizon": signal.time_horizon
                    }
                    history_data.append(signal_dict)
                
                with open(filepath, 'w') as f:
                    json.dump(history_data, f, indent=2)
                    
            elif format == "csv":
                import csv
                
                with open(filepath, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "timestamp", "signal_type", "score", "confidence", 
                        "confidence_level", "strength", "indicators_used", 
                        "reasoning", "risk_level", "time_horizon"
                    ])
                    
                    for signal in self.signal_history:
                        writer.writerow([
                            signal.timestamp.isoformat(),
                            signal.signal_type.value,
                            signal.score,
                            signal.confidence,
                            signal.confidence_level.value,
                            signal.strength,
                            ";".join(signal.indicators_used),
                            signal.reasoning,
                            signal.risk_level,
                            signal.time_horizon
                        ])
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'export de l'historique: {e}")
            return False
