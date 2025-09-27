"""
Moteur de Scoring Composite
Phase 4: Intégration et Optimisation

Ce module implémente le moteur de scoring composite qui combine
tous les types d'analyse en un score unifié.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class AnalysisType(Enum):
    """Types d'analyse disponibles"""
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"
    MARKET = "market"
    ML = "ml"
    HYBRID = "hybrid"

class RiskLevel(Enum):
    """Niveaux de risque"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

@dataclass
class CompositeScore:
    """Score composite unifié"""
    symbol: str
    analysis_date: datetime
    overall_score: float
    confidence_level: float
    risk_level: RiskLevel
    recommendation: str
    score_breakdown: Dict[str, float]
    analysis_quality: Dict[str, float]
    convergence_metrics: Dict[str, float]

class CompositeScoringEngine:
    """
    Moteur de scoring composite qui unifie tous les types d'analyse
    """
    
    def __init__(self):
        """Initialise le moteur de scoring composite"""
        # Configuration des poids par défaut
        self.default_weights = {
            AnalysisType.TECHNICAL: 0.30,
            AnalysisType.SENTIMENT: 0.25,
            AnalysisType.MARKET: 0.25,
            AnalysisType.ML: 0.20
        }
        
        # Seuils de qualité d'analyse
        self.quality_thresholds = {
            'excellent': 0.8,
            'good': 0.6,
            'fair': 0.4,
            'poor': 0.2
        }
        
        # Seuils de recommandation
        self.recommendation_thresholds = {
            'STRONG_BUY': 0.8,
            'BUY': 0.6,
            'HOLD': 0.4,
            'SELL': 0.2,
            'STRONG_SELL': 0.0
        }
        
        # Seuils de risque
        self.risk_thresholds = {
            RiskLevel.VERY_LOW: 0.8,
            RiskLevel.LOW: 0.6,
            RiskLevel.MEDIUM: 0.4,
            RiskLevel.HIGH: 0.2,
            RiskLevel.VERY_HIGH: 0.0
        }
        
        logger.info("CompositeScoringEngine initialized")
    
    def calculate_composite_score(self, analyses: Dict[AnalysisType, Dict[str, Any]], 
                                custom_weights: Optional[Dict[AnalysisType, float]] = None) -> CompositeScore:
        """
        Calcule le score composite unifié
        
        Args:
            analyses: Dictionnaire des analyses par type
            custom_weights: Poids personnalisés (optionnel)
            
        Returns:
            CompositeScore: Score composite calculé
        """
        try:
            symbol = self._extract_symbol(analyses)
            weights = custom_weights or self.default_weights
            
            # Calculer les scores individuels
            score_breakdown = {}
            analysis_quality = {}
            
            # Calculer le score composite pondéré
            composite_score = 0.0
            total_weight = 0.0
            
            for analysis_type, analysis_data in analyses.items():
                if analysis_type in weights:
                    score = self._extract_score(analysis_type, analysis_data)
                    weight = weights[analysis_type]
                    
                    score_breakdown[analysis_type.value] = score
                    composite_score += score * weight
                    total_weight += weight
                    
                    # Évaluer la qualité de l'analyse
                    quality = self._evaluate_analysis_quality(analysis_type, analysis_data)
                    analysis_quality[analysis_type.value] = quality
            
            # Normaliser le score composite
            if total_weight > 0:
                composite_score = composite_score / total_weight
            
            # Calculer le niveau de confiance global
            confidence = self._calculate_global_confidence(analysis_quality)
            
            # Déterminer le niveau de risque
            risk_level = self.determine_risk_level(composite_score)
            
            # Générer la recommandation
            recommendation = self._generate_recommendation(composite_score, confidence)
            
            return CompositeScore(
                symbol=symbol,
                composite_score=composite_score,
                confidence_level=confidence,
                risk_level=risk_level,
                recommendation=recommendation,
                score_breakdown=score_breakdown,
                analysis_quality=analysis_quality,
                weights_used=weights,
                analysis_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            raise
    
    def calculate_simple_composite_score(self, technical_score: float, sentiment_score: float,
                                       market_score: float, ml_score: float, candlestick_score: float,
                                       garch_score: float, monte_carlo_score: float, markov_score: float,
                                       volatility_score: float, weights: Optional[Dict[str, float]] = None) -> float:
        """
        Calcule un score composite simple à partir des scores individuels
        
        Args:
            technical_score: Score technique
            sentiment_score: Score de sentiment
            market_score: Score de marché
            ml_score: Score ML
            candlestick_score: Score des patterns de chandeliers
            garch_score: Score GARCH
            monte_carlo_score: Score Monte Carlo
            markov_score: Score Markov
            volatility_score: Score de volatilité
            weights: Poids personnalisés
            
        Returns:
            float: Score composite calculé
        """
        try:
            # Poids par défaut
            default_weights = {
                'technical': 0.15,
                'sentiment': 0.15,
                'market': 0.15,
                'ml': 0.10,
                'candlestick': 0.10,
                'garch': 0.10,
                'monte_carlo': 0.10,
                'markov': 0.10,
                'volatility': 0.05
            }
            
            # Utiliser les poids personnalisés ou par défaut
            used_weights = weights or default_weights
            
            # Calculer le score composite pondéré
            composite_score = (
                used_weights.get('technical', 0.15) * technical_score +
                used_weights.get('sentiment', 0.15) * sentiment_score +
                used_weights.get('market', 0.15) * market_score +
                used_weights.get('ml', 0.10) * ml_score +
                used_weights.get('candlestick', 0.10) * candlestick_score +
                used_weights.get('garch', 0.10) * garch_score +
                used_weights.get('monte_carlo', 0.10) * monte_carlo_score +
                used_weights.get('markov', 0.10) * markov_score +
                used_weights.get('volatility', 0.05) * volatility_score
            )
            
            return composite_score
            
        except Exception as e:
            logger.error(f"Error calculating simple composite score: {e}")
            return 0.5  # Score neutre en cas d'erreur
    
    def determine_risk_level(self, composite_score: float) -> str:
        """
        Détermine le niveau de risque basé sur le score composite
        
        Args:
            composite_score: Score composite (0-1)
            
        Returns:
            str: Niveau de risque (LOW, MEDIUM, HIGH)
        """
        try:
            if composite_score >= 0.7:
                return "LOW"
            elif composite_score >= 0.4:
                return "MEDIUM"
            else:
                return "HIGH"
        except Exception as e:
            logger.error(f"Error determining risk level: {e}")
            return "MEDIUM"  # Niveau par défaut
            
            for analysis_type, analysis_data in analyses.items():
                if analysis_data:
                    score = self._calculate_individual_score(analysis_type, analysis_data)
                    quality = self._assess_analysis_quality(analysis_type, analysis_data)
                    
                    score_breakdown[analysis_type.value] = score
                    analysis_quality[analysis_type.value] = quality
                else:
                    score_breakdown[analysis_type.value] = 0.0
                    analysis_quality[analysis_type.value] = 0.0
            
            # Calculer le score composite pondéré
            overall_score = self._calculate_weighted_score(score_breakdown, weights)
            
            # Calculer le niveau de confiance
            confidence_level = self._calculate_confidence_level(score_breakdown, analysis_quality)
            
            # Évaluer le niveau de risque
            risk_level = self._assess_risk_level(analyses, score_breakdown)
            
            # Générer la recommandation
            recommendation = self._generate_recommendation(overall_score, confidence_level, risk_level)
            
            # Calculer les métriques de convergence
            convergence_metrics = self._calculate_convergence_metrics(score_breakdown)
            
            return CompositeScore(
                symbol=symbol,
                analysis_date=datetime.now(),
                overall_score=overall_score,
                confidence_level=confidence_level,
                risk_level=risk_level,
                recommendation=recommendation,
                score_breakdown=score_breakdown,
                analysis_quality=analysis_quality,
                convergence_metrics=convergence_metrics
            )
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            raise
    
    def _extract_symbol(self, analyses: Dict[AnalysisType, Dict[str, Any]]) -> str:
        """Extrait le symbole des analyses"""
        for analysis_data in analyses.values():
            if analysis_data and 'symbol' in analysis_data:
                return analysis_data['symbol']
        return 'UNKNOWN'
    
    def _calculate_individual_score(self, analysis_type: AnalysisType, 
                                  analysis_data: Dict[str, Any]) -> float:
        """Calcule le score individuel pour un type d'analyse"""
        try:
            if analysis_type == AnalysisType.TECHNICAL:
                return self._calculate_technical_score(analysis_data)
            elif analysis_type == AnalysisType.SENTIMENT:
                return self._calculate_sentiment_score(analysis_data)
            elif analysis_type == AnalysisType.MARKET:
                return self._calculate_market_score(analysis_data)
            elif analysis_type == AnalysisType.ML:
                return self._calculate_ml_score(analysis_data)
            elif analysis_type == AnalysisType.HYBRID:
                return self._calculate_hybrid_score(analysis_data)
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating {analysis_type.value} score: {e}")
            return 0.0
    
    def _calculate_technical_score(self, technical_data: Dict[str, Any]) -> float:
        """Calcule le score technique"""
        try:
            if 'error' in technical_data:
                return 0.0
            
            signals = technical_data.get('signals', {})
            patterns = technical_data.get('candlestick_patterns', {})
            support_resistance = technical_data.get('support_resistance', {})
            
            # Score basé sur les signaux
            signal_score = 0.5  # Score neutre par défaut
            if signals:
                # Logique de scoring des signaux
                buy_signals = signals.get('buy_signals', [])
                sell_signals = signals.get('sell_signals', [])
                
                if buy_signals or sell_signals:
                    signal_ratio = len(buy_signals) / (len(buy_signals) + len(sell_signals))
                    signal_score = signal_ratio
            
            # Score basé sur les patterns
            pattern_score = 0.5  # Score neutre par défaut
            if patterns:
                bullish_count = sum(1 for p in patterns.values() if p.get('sentiment') == 'bullish')
                bearish_count = sum(1 for p in patterns.values() if p.get('sentiment') == 'bearish')
                
                if bullish_count + bearish_count > 0:
                    pattern_score = bullish_count / (bullish_count + bearish_count)
            
            # Score basé sur support/résistance
            sr_score = 0.5  # Score neutre par défaut
            if support_resistance:
                # Logique de scoring SR
                # TODO: Implémenter la logique de scoring SR
                pass
            
            # Score composite technique
            technical_score = (signal_score * 0.5 + pattern_score * 0.3 + sr_score * 0.2)
            return min(1.0, max(0.0, technical_score))
            
        except Exception as e:
            logger.error(f"Error calculating technical score: {e}")
            return 0.0
    
    def _calculate_sentiment_score(self, sentiment_data: Dict[str, Any]) -> float:
        """Calcule le score de sentiment"""
        try:
            if 'error' in sentiment_data:
                return 0.0
            
            garch_analysis = sentiment_data.get('garch_analysis', {})
            monte_carlo_analysis = sentiment_data.get('monte_carlo_analysis', {})
            markov_analysis = sentiment_data.get('markov_analysis', {})
            volatility_forecast = sentiment_data.get('volatility_forecast', {})
            
            # Score basé sur GARCH
            garch_score = 0.5  # Score neutre par défaut
            if garch_analysis and 'model_comparison' in garch_analysis:
                # Logique de scoring GARCH
                # TODO: Implémenter la logique de scoring GARCH
                pass
            
            # Score basé sur Monte Carlo
            mc_score = 0.5  # Score neutre par défaut
            if monte_carlo_analysis and 'risk_metrics' in monte_carlo_analysis:
                # Logique de scoring Monte Carlo
                # TODO: Implémenter la logique de scoring Monte Carlo
                pass
            
            # Score basé sur Markov
            markov_score = 0.5  # Score neutre par défaut
            if markov_analysis and 'current_state' in markov_analysis:
                # Logique de scoring Markov
                # TODO: Implémenter la logique de scoring Markov
                pass
            
            # Score basé sur la prédiction de volatilité
            volatility_score = 0.5  # Score neutre par défaut
            if volatility_forecast:
                # Logique de scoring volatilité
                # TODO: Implémenter la logique de scoring volatilité
                pass
            
            # Score composite sentiment
            sentiment_score = (garch_score * 0.3 + mc_score * 0.3 + markov_score * 0.2 + volatility_score * 0.2)
            return min(1.0, max(0.0, sentiment_score))
            
        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.0
    
    def _calculate_market_score(self, market_data: Dict[str, Any]) -> float:
        """Calcule le score des indicateurs de marché"""
        try:
            if 'error' in market_data:
                return 0.0
            
            volatility_indicators = market_data.get('volatility_indicators', {})
            momentum_indicators = market_data.get('momentum_indicators', {})
            
            # Score basé sur les indicateurs de volatilité
            volatility_score = 0.5  # Score neutre par défaut
            if volatility_indicators:
                # Logique de scoring volatilité
                # TODO: Implémenter la logique de scoring volatilité
                pass
            
            # Score basé sur les indicateurs de momentum
            momentum_score = 0.5  # Score neutre par défaut
            if momentum_indicators:
                # Logique de scoring momentum
                # TODO: Implémenter la logique de scoring momentum
                pass
            
            # Score composite marché
            market_score = (volatility_score * 0.4 + momentum_score * 0.6)
            return min(1.0, max(0.0, market_score))
            
        except Exception as e:
            logger.error(f"Error calculating market score: {e}")
            return 0.0
    
    def _calculate_ml_score(self, ml_data: Dict[str, Any]) -> float:
        """Calcule le score ML"""
        try:
            if not ml_data:
                return 0.0
            
            ml_score = ml_data.get('ml_score', 0.0)
            return min(1.0, max(0.0, float(ml_score)))
            
        except Exception as e:
            logger.error(f"Error calculating ML score: {e}")
            return 0.0
    
    def _calculate_hybrid_score(self, hybrid_data: Dict[str, Any]) -> float:
        """Calcule le score hybride"""
        try:
            if not hybrid_data:
                return 0.0
            
            hybrid_score = hybrid_data.get('hybrid_score', 0.0)
            return min(1.0, max(0.0, float(hybrid_score)))
            
        except Exception as e:
            logger.error(f"Error calculating hybrid score: {e}")
            return 0.0
    
    def _assess_analysis_quality(self, analysis_type: AnalysisType, 
                               analysis_data: Dict[str, Any]) -> float:
        """Évalue la qualité d'une analyse"""
        try:
            if not analysis_data or 'error' in analysis_data:
                return 0.0
            
            # Critères de qualité basés sur le type d'analyse
            if analysis_type == AnalysisType.TECHNICAL:
                return self._assess_technical_quality(analysis_data)
            elif analysis_type == AnalysisType.SENTIMENT:
                return self._assess_sentiment_quality(analysis_data)
            elif analysis_type == AnalysisType.MARKET:
                return self._assess_market_quality(analysis_data)
            elif analysis_type == AnalysisType.ML:
                return self._assess_ml_quality(analysis_data)
            else:
                return 0.5  # Qualité neutre par défaut
                
        except Exception as e:
            logger.error(f"Error assessing {analysis_type.value} quality: {e}")
            return 0.0
    
    def _assess_technical_quality(self, technical_data: Dict[str, Any]) -> float:
        """Évalue la qualité de l'analyse technique"""
        try:
            quality_factors = []
            
            # Facteur 1: Présence de données
            data_points = technical_data.get('data_points', 0)
            if data_points > 100:
                quality_factors.append(1.0)
            elif data_points > 50:
                quality_factors.append(0.8)
            elif data_points > 20:
                quality_factors.append(0.6)
            else:
                quality_factors.append(0.2)
            
            # Facteur 2: Présence de signaux
            signals = technical_data.get('signals', {})
            if signals and (signals.get('buy_signals') or signals.get('sell_signals')):
                quality_factors.append(1.0)
            else:
                quality_factors.append(0.5)
            
            # Facteur 3: Présence de patterns
            patterns = technical_data.get('candlestick_patterns', {})
            if patterns:
                quality_factors.append(1.0)
            else:
                quality_factors.append(0.3)
            
            return np.mean(quality_factors)
            
        except Exception as e:
            logger.error(f"Error assessing technical quality: {e}")
            return 0.0
    
    def _assess_sentiment_quality(self, sentiment_data: Dict[str, Any]) -> float:
        """Évalue la qualité de l'analyse de sentiment"""
        try:
            quality_factors = []
            
            # Facteur 1: Présence de données
            data_points = sentiment_data.get('data_points', 0)
            if data_points > 200:
                quality_factors.append(1.0)
            elif data_points > 100:
                quality_factors.append(0.8)
            elif data_points > 50:
                quality_factors.append(0.6)
            else:
                quality_factors.append(0.2)
            
            # Facteur 2: Présence d'analyses complètes
            analyses_present = 0
            if sentiment_data.get('garch_analysis'):
                analyses_present += 1
            if sentiment_data.get('monte_carlo_analysis'):
                analyses_present += 1
            if sentiment_data.get('markov_analysis'):
                analyses_present += 1
            if sentiment_data.get('volatility_forecast'):
                analyses_present += 1
            
            quality_factors.append(analyses_present / 4.0)
            
            return np.mean(quality_factors)
            
        except Exception as e:
            logger.error(f"Error assessing sentiment quality: {e}")
            return 0.0
    
    def _assess_market_quality(self, market_data: Dict[str, Any]) -> float:
        """Évalue la qualité des indicateurs de marché"""
        try:
            quality_factors = []
            
            # Facteur 1: Présence de données
            data_points = market_data.get('data_points', 0)
            if data_points > 100:
                quality_factors.append(1.0)
            elif data_points > 50:
                quality_factors.append(0.8)
            elif data_points > 20:
                quality_factors.append(0.6)
            else:
                quality_factors.append(0.2)
            
            # Facteur 2: Présence d'indicateurs
            indicators_present = 0
            if market_data.get('volatility_indicators'):
                indicators_present += 1
            if market_data.get('momentum_indicators'):
                indicators_present += 1
            
            quality_factors.append(indicators_present / 2.0)
            
            return np.mean(quality_factors)
            
        except Exception as e:
            logger.error(f"Error assessing market quality: {e}")
            return 0.0
    
    def _assess_ml_quality(self, ml_data: Dict[str, Any]) -> float:
        """Évalue la qualité de l'analyse ML"""
        try:
            if not ml_data:
                return 0.0
            
            # Facteur 1: Présence de score ML
            ml_score = ml_data.get('ml_score', 0.0)
            if ml_score > 0:
                quality_factors = [1.0]
            else:
                quality_factors = [0.0]
            
            # Facteur 2: Présence de confiance ML
            ml_confidence = ml_data.get('ml_confidence', 0.0)
            quality_factors.append(ml_confidence)
            
            return np.mean(quality_factors)
            
        except Exception as e:
            logger.error(f"Error assessing ML quality: {e}")
            return 0.0
    
    def _calculate_weighted_score(self, score_breakdown: Dict[str, float], 
                                weights: Dict[AnalysisType, float]) -> float:
        """Calcule le score pondéré"""
        try:
            weighted_score = 0.0
            total_weight = 0.0
            
            for analysis_type, weight in weights.items():
                score = score_breakdown.get(analysis_type.value, 0.0)
                weighted_score += score * weight
                total_weight += weight
            
            if total_weight > 0:
                return weighted_score / total_weight
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating weighted score: {e}")
            return 0.0
    
    def _calculate_confidence_level(self, score_breakdown: Dict[str, float], 
                                  analysis_quality: Dict[str, float]) -> float:
        """Calcule le niveau de confiance global"""
        try:
            # Confiance basée sur la qualité des analyses
            quality_confidence = np.mean(list(analysis_quality.values()))
            
            # Confiance basée sur la convergence des scores
            scores = list(score_breakdown.values())
            if len(scores) > 1:
                score_std = np.std(scores)
                convergence_confidence = max(0.0, 1.0 - score_std)
            else:
                convergence_confidence = 0.5
            
            # Confiance composite
            confidence = (quality_confidence * 0.6 + convergence_confidence * 0.4)
            return min(1.0, max(0.0, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence level: {e}")
            return 0.0
    
    def _assess_risk_level(self, analyses: Dict[AnalysisType, Dict[str, Any]], 
                          score_breakdown: Dict[str, float]) -> RiskLevel:
        """Évalue le niveau de risque"""
        try:
            # Logique d'évaluation du risque basée sur les analyses
            # TODO: Implémenter la logique d'évaluation du risque
            
            # Pour l'instant, retourner un niveau de risque basé sur le score composite
            overall_score = np.mean(list(score_breakdown.values()))
            
            if overall_score >= 0.8:
                return RiskLevel.VERY_LOW
            elif overall_score >= 0.6:
                return RiskLevel.LOW
            elif overall_score >= 0.4:
                return RiskLevel.MEDIUM
            elif overall_score >= 0.2:
                return RiskLevel.HIGH
            else:
                return RiskLevel.VERY_HIGH
                
        except Exception as e:
            logger.error(f"Error assessing risk level: {e}")
            return RiskLevel.HIGH
    
    def _generate_recommendation(self, overall_score: float, confidence_level: float, 
                              risk_level: RiskLevel) -> str:
        """Génère une recommandation basée sur le score, la confiance et le risque"""
        try:
            # Ajuster le score basé sur la confiance et le risque
            risk_adjustment = {
                RiskLevel.VERY_LOW: 1.0,
                RiskLevel.LOW: 0.9,
                RiskLevel.MEDIUM: 0.8,
                RiskLevel.HIGH: 0.6,
                RiskLevel.VERY_HIGH: 0.4
            }
            
            adjusted_score = overall_score * confidence_level * risk_adjustment[risk_level]
            
            # Déterminer la recommandation
            for recommendation, threshold in sorted(self.recommendation_thresholds.items(), 
                                                  key=lambda x: x[1], reverse=True):
                if adjusted_score >= threshold:
                    return recommendation
            
            return "STRONG_SELL"
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return "HOLD"
    
    def _calculate_convergence_metrics(self, score_breakdown: Dict[str, float]) -> Dict[str, float]:
        """Calcule les métriques de convergence"""
        try:
            scores = list(score_breakdown.values())
            
            if len(scores) < 2:
                return {'convergence_score': 0.0, 'score_std': 0.0, 'score_range': 0.0}
            
            # Score de convergence basé sur l'écart-type
            score_std = np.std(scores)
            convergence_score = max(0.0, 1.0 - score_std)
            
            # Plage des scores
            score_range = max(scores) - min(scores)
            
            return {
                'convergence_score': convergence_score,
                'score_std': score_std,
                'score_range': score_range,
                'score_count': len(scores)
            }
            
        except Exception as e:
            logger.error(f"Error calculating convergence metrics: {e}")
            return {'convergence_score': 0.0, 'score_std': 0.0, 'score_range': 0.0}
    
    def get_scoring_configuration(self) -> Dict[str, Any]:
        """Retourne la configuration actuelle du scoring"""
        return {
            'default_weights': {k.value: v for k, v in self.default_weights.items()},
            'quality_thresholds': self.quality_thresholds,
            'recommendation_thresholds': self.recommendation_thresholds,
            'risk_thresholds': {k.value: v for k, v in self.risk_thresholds.items()}
        }
    
    def update_scoring_configuration(self, config: Dict[str, Any]) -> bool:
        """Met à jour la configuration du scoring"""
        try:
            # Mettre à jour les poids par défaut
            if 'default_weights' in config:
                new_weights = {}
                for k, v in config['default_weights'].items():
                    analysis_type = AnalysisType(k)
                    new_weights[analysis_type] = v
                self.default_weights = new_weights
            
            # Mettre à jour les seuils de qualité
            if 'quality_thresholds' in config:
                self.quality_thresholds.update(config['quality_thresholds'])
            
            # Mettre à jour les seuils de recommandation
            if 'recommendation_thresholds' in config:
                self.recommendation_thresholds.update(config['recommendation_thresholds'])
            
            logger.info("Scoring configuration updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating scoring configuration: {e}")
            return False
