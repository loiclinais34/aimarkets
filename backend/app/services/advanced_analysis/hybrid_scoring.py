"""
Système de Scoring Hybride
Phase 4: Intégration et Optimisation

Ce module implémente le système de scoring hybride qui combine
l'analyse ML existante avec l'analyse conventionnelle avancée.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class HybridScore:
    """Score hybride combinant ML et analyse conventionnelle"""
    symbol: str
    ml_score: float
    conventional_score: float
    hybrid_score: float
    confidence: float
    convergence_factor: float
    recommendation: str
    analysis_date: datetime

class HybridScoringSystem:
    """
    Système de scoring hybride qui combine ML et analyse conventionnelle
    """
    
    def __init__(self):
        """Initialise le système de scoring hybride"""
        # Poids pour la combinaison des scores
        self.ml_weight = 0.4          # 40% pour ML
        self.conventional_weight = 0.6  # 60% pour analyse conventionnelle
        
        # Seuils de convergence
        self.convergence_threshold = 0.2  # Différence maximale pour convergence
        
        # Seuils de recommandation
        self.recommendation_thresholds = {
            'STRONG_BUY': 0.8,
            'BUY': 0.6,
            'HOLD': 0.4,
            'SELL': 0.2,
            'STRONG_SELL': 0.0
        }
        
        logger.info("HybridScoringSystem initialized")
    
    def calculate_hybrid_score(self, ml_analysis: Dict[str, Any], 
                            conventional_analysis: Dict[str, Any]) -> HybridScore:
        """
        Calcule le score hybride combinant ML et analyse conventionnelle
        
        Args:
            ml_analysis: Résultats de l'analyse ML
            conventional_analysis: Résultats de l'analyse conventionnelle
            
        Returns:
            HybridScore: Score hybride calculé
        """
        try:
            symbol = conventional_analysis.get('symbol', 'UNKNOWN')
            
            # Extraire les scores
            ml_score = self._extract_ml_score(ml_analysis)
            conventional_score = self._extract_conventional_score(conventional_analysis)
            
            # Calculer le score hybride pondéré
            hybrid_score = self._calculate_weighted_score(ml_score, conventional_score)
            
            # Calculer le facteur de convergence
            convergence_factor = self._calculate_convergence_factor(ml_score, conventional_score)
            
            # Calculer le niveau de confiance
            confidence = self._calculate_confidence(ml_score, conventional_score, convergence_factor)
            
            # Générer la recommandation
            recommendation = self._generate_recommendation(hybrid_score, confidence)
            
            return HybridScore(
                symbol=symbol,
                ml_score=ml_score,
                conventional_score=conventional_score,
                hybrid_score=hybrid_score,
                confidence=confidence,
                convergence_factor=convergence_factor,
                recommendation=recommendation,
                analysis_date=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculating hybrid score: {e}")
            raise
    
    def _extract_ml_score(self, ml_analysis: Dict[str, Any]) -> float:
        """Extrait le score ML de l'analyse"""
        try:
            if not ml_analysis:
                return 0.0
            
            # Extraire le score ML principal
            ml_score = ml_analysis.get('ml_score', 0.0)
            
            # Normaliser entre 0 et 1
            return min(1.0, max(0.0, float(ml_score)))
            
        except Exception as e:
            logger.error(f"Error extracting ML score: {e}")
            return 0.0
    
    def _extract_conventional_score(self, conventional_analysis: Dict[str, Any]) -> float:
        """Extrait le score conventionnel de l'analyse"""
        try:
            if not conventional_analysis:
                return 0.0
            
            # Extraire le score composite de l'analyse conventionnelle
            composite_score = conventional_analysis.get('composite_score', 0.0)
            
            # Normaliser entre 0 et 1
            return min(1.0, max(0.0, float(composite_score)))
            
        except Exception as e:
            logger.error(f"Error extracting conventional score: {e}")
            return 0.0
    
    def _calculate_weighted_score(self, ml_score: float, conventional_score: float) -> float:
        """Calcule le score pondéré"""
        try:
            weighted_score = (
                ml_score * self.ml_weight +
                conventional_score * self.conventional_weight
            )
            
            return min(1.0, max(0.0, weighted_score))
            
        except Exception as e:
            logger.error(f"Error calculating weighted score: {e}")
            return 0.0
    
    def _calculate_convergence_factor(self, ml_score: float, conventional_score: float) -> float:
        """Calcule le facteur de convergence entre ML et analyse conventionnelle"""
        try:
            # Calculer la différence absolue
            difference = abs(ml_score - conventional_score)
            
            # Plus la différence est faible, plus la convergence est élevée
            convergence_factor = max(0.0, 1.0 - (difference / self.convergence_threshold))
            
            return min(1.0, convergence_factor)
            
        except Exception as e:
            logger.error(f"Error calculating convergence factor: {e}")
            return 0.0
    
    def _calculate_confidence(self, ml_score: float, conventional_score: float, 
                            convergence_factor: float) -> float:
        """Calcule le niveau de confiance basé sur la convergence"""
        try:
            # Confiance basée sur la convergence
            convergence_confidence = convergence_factor
            
            # Confiance basée sur la magnitude des scores
            avg_score = (ml_score + conventional_score) / 2
            magnitude_confidence = abs(avg_score - 0.5) * 2  # Plus proche de 0 ou 1 = plus confiant
            
            # Confiance composite
            confidence = (convergence_confidence * 0.7 + magnitude_confidence * 0.3)
            
            return min(1.0, max(0.0, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.0
    
    def _generate_recommendation(self, hybrid_score: float, confidence: float) -> str:
        """Génère une recommandation basée sur le score hybride et la confiance"""
        try:
            # Ajuster le score basé sur la confiance
            adjusted_score = hybrid_score * confidence
            
            # Déterminer la recommandation
            for recommendation, threshold in sorted(self.recommendation_thresholds.items(), 
                                                  key=lambda x: x[1], reverse=True):
                if adjusted_score >= threshold:
                    return recommendation
            
            return "STRONG_SELL"
            
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return "HOLD"
    
    def analyze_score_convergence(self, scores_history: List[HybridScore]) -> Dict[str, Any]:
        """
        Analyse la convergence des scores dans le temps
        
        Args:
            scores_history: Historique des scores hybrides
            
        Returns:
            Dict contenant l'analyse de convergence
        """
        try:
            if len(scores_history) < 2:
                return {'error': 'Insufficient data for convergence analysis'}
            
            # Extraire les scores
            ml_scores = [score.ml_score for score in scores_history]
            conventional_scores = [score.conventional_score for score in scores_history]
            hybrid_scores = [score.hybrid_score for score in scores_history]
            
            # Calculer les statistiques
            ml_trend = self._calculate_trend(ml_scores)
            conventional_trend = self._calculate_trend(conventional_scores)
            hybrid_trend = self._calculate_trend(hybrid_scores)
            
            # Calculer la corrélation
            ml_conventional_correlation = np.corrcoef(ml_scores, conventional_scores)[0, 1]
            
            # Calculer la volatilité des scores
            ml_volatility = np.std(ml_scores)
            conventional_volatility = np.std(conventional_scores)
            hybrid_volatility = np.std(hybrid_scores)
            
            return {
                'period_analyzed': len(scores_history),
                'ml_trend': ml_trend,
                'conventional_trend': conventional_trend,
                'hybrid_trend': hybrid_trend,
                'ml_conventional_correlation': ml_conventional_correlation,
                'volatility': {
                    'ml': ml_volatility,
                    'conventional': conventional_volatility,
                    'hybrid': hybrid_volatility
                },
                'convergence_quality': self._assess_convergence_quality(
                    ml_conventional_correlation, ml_volatility, conventional_volatility
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing score convergence: {e}")
            return {'error': str(e)}
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """Calcule la tendance des scores"""
        try:
            if len(scores) < 2:
                return "INSUFFICIENT_DATA"
            
            # Régression linéaire simple
            x = np.arange(len(scores))
            y = np.array(scores)
            
            slope = np.polyfit(x, y, 1)[0]
            
            if slope > 0.01:
                return "INCREASING"
            elif slope < -0.01:
                return "DECREASING"
            else:
                return "STABLE"
                
        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return "ERROR"
    
    def _assess_convergence_quality(self, correlation: float, ml_volatility: float, 
                                  conventional_volatility: float) -> str:
        """Évalue la qualité de la convergence"""
        try:
            # Critères de qualité
            high_correlation = correlation > 0.7
            low_volatility = ml_volatility < 0.1 and conventional_volatility < 0.1
            
            if high_correlation and low_volatility:
                return "EXCELLENT"
            elif high_correlation or low_volatility:
                return "GOOD"
            elif correlation > 0.3:
                return "FAIR"
            else:
                return "POOR"
                
        except Exception as e:
            logger.error(f"Error assessing convergence quality: {e}")
            return "UNKNOWN"
    
    def get_scoring_weights(self) -> Dict[str, float]:
        """Retourne les poids actuels du scoring"""
        return {
            'ml_weight': self.ml_weight,
            'conventional_weight': self.conventional_weight
        }
    
    def update_scoring_weights(self, ml_weight: float, conventional_weight: float) -> bool:
        """
        Met à jour les poids du scoring
        
        Args:
            ml_weight: Nouveau poids pour ML
            conventional_weight: Nouveau poids pour l'analyse conventionnelle
            
        Returns:
            bool: True si la mise à jour a réussi
        """
        try:
            # Vérifier que les poids sont valides
            if not (0 <= ml_weight <= 1 and 0 <= conventional_weight <= 1):
                return False
            
            if abs(ml_weight + conventional_weight - 1.0) > 0.01:
                return False
            
            # Mettre à jour les poids
            self.ml_weight = ml_weight
            self.conventional_weight = conventional_weight
            
            logger.info(f"Updated scoring weights: ML={ml_weight}, Conventional={conventional_weight}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating scoring weights: {e}")
            return False
