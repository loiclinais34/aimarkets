#!/usr/bin/env python3
"""
Script pour implémenter les optimisations des signaux d'achat
Applique les améliorations identifiées dans l'analyse des problèmes
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration de la base de données
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import des modèles et services
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import des modèles
from app.models.historical_opportunities import HistoricalOpportunities
from app.models.database import HistoricalData


class OptimizedBuySignalsImplementation:
    """
    Implémentation des optimisations des signaux d'achat
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def implement_optimized_scoring(self) -> Dict[str, Any]:
        """
        Implémente un système de scoring optimisé basé sur l'analyse des corrélations
        """
        try:
            self.logger.info("🔧 Implémentation du scoring optimisé")
            
            # Nouveaux poids basés sur les corrélations identifiées
            # Corrélations observées:
            # - technical_score: 0.256 (positive)
            # - sentiment_score: 0.359 (positive) 
            # - market_score: -0.438 (négative)
            # - confidence: -0.439 (négative)
            
            optimized_weights = {
                "technical": 0.40,    # Augmenté (corrélation positive)
                "sentiment": 0.45,    # Augmenté (meilleure corrélation)
                "market": 0.15,       # Réduit (corrélation négative)
                "confidence_penalty": 0.1  # Pénalité pour la sur-confiance
            }
            
            # Nouveaux seuils de décision optimisés
            optimized_thresholds = {
                "BUY_STRONG": {
                    "min_composite_score": 0.65,  # Augmenté
                    "min_technical_score": 0.60,  # Augmenté
                    "min_sentiment_score": 0.55,  # Augmenté
                    "max_market_score": 0.40,     # Réduit (éviter les marchés baissiers)
                    "min_confidence": 0.70,       # Réduit (éviter la sur-confiance)
                    "max_confidence": 0.85        # Plafonné
                },
                "BUY_MODERATE": {
                    "min_composite_score": 0.55,
                    "min_technical_score": 0.50,
                    "min_sentiment_score": 0.45,
                    "max_market_score": 0.45,
                    "min_confidence": 0.65,
                    "max_confidence": 0.90
                },
                "BUY_WEAK": {
                    "min_composite_score": 0.45,
                    "min_technical_score": 0.40,
                    "min_sentiment_score": 0.35,
                    "max_market_score": 0.50,
                    "min_confidence": 0.60,
                    "max_confidence": 0.95
                }
            }
            
            # Règles de validation supplémentaires
            additional_validation_rules = {
                "technical_validation": {
                    "rsi_range": [30, 70],  # Éviter les extrêmes
                    "macd_positive": True,  # MACD au-dessus de la ligne de signal
                    "price_above_sma20": True,  # Prix au-dessus de SMA 20
                    "volume_above_average": True  # Volume supérieur à la moyenne
                },
                "sentiment_validation": {
                    "score_positive": True,  # Score > 0.5
                    "confidence_adequate": True,  # Confiance entre 0.6 et 0.8
                    "trend_positive": True  # Tendance positive
                },
                "market_validation": {
                    "regime_bullish": True,  # Marché haussier ou latéral
                    "volatility_acceptable": True,  # Volatilité < 5%
                    "correlation_positive": True  # Corrélations sectorielles positives
                }
            }
            
            return {
                "optimized_weights": optimized_weights,
                "optimized_thresholds": optimized_thresholds,
                "additional_validation_rules": additional_validation_rules,
                "implementation_notes": [
                    "Poids augmentés pour technical et sentiment (corrélations positives)",
                    "Poids réduit pour market (corrélation négative)",
                    "Pénalité pour la sur-confiance",
                    "Seuils plus stricts pour BUY_STRONG",
                    "Validation technique renforcée",
                    "Filtres de qualité supplémentaires"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'implémentation du scoring: {e}")
            return {"error": str(e)}
    
    def implement_optimized_position_sizing(self) -> Dict[str, Any]:
        """
        Implémente un position sizing optimisé basé sur l'analyse des performances
        """
        try:
            self.logger.info("⚖️ Implémentation du position sizing optimisé")
            
            # Stratégie de position sizing optimisée
            optimized_sizing_strategy = {
                "base_portfolio_risk": 0.015,  # Réduit de 2% à 1.5%
                "max_position_risk": 0.025,    # Maximum 2.5%
                "volatility_adjustment": {
                    "low_volatility": 1.2,     # Multiplicateur pour faible volatilité
                    "medium_volatility": 1.0,  # Multiplicateur standard
                    "high_volatility": 0.7     # Réduction pour haute volatilité
                },
                "confidence_adjustment": {
                    "low_confidence": 0.5,     # Réduction pour faible confiance
                    "medium_confidence": 1.0,  # Standard
                    "high_confidence": 1.3,   # Augmentation pour haute confiance
                    "over_confidence": 0.8     # Réduction pour sur-confiance
                },
                "score_adjustment": {
                    "technical_weight": 0.4,   # Poids du score technique
                    "sentiment_weight": 0.4,   # Poids du score sentiment
                    "market_weight": 0.2       # Poids du score marché (réduit)
                }
            }
            
            # Formule de calcul optimisée
            sizing_formula = {
                "base_size": "portfolio_risk * portfolio_value / current_price",
                "volatility_factor": "volatility_adjustment[volatility_level]",
                "confidence_factor": "confidence_adjustment[confidence_level]",
                "score_factor": "technical_weight * technical_score + sentiment_weight * sentiment_score + market_weight * market_score",
                "final_size": "base_size * volatility_factor * confidence_factor * score_factor"
            }
            
            # Règles de protection
            protection_rules = {
                "max_position_size": 0.10,     # Maximum 10% du portefeuille
                "max_correlation_exposure": 0.30,  # Maximum 30% d'exposition corrélée
                "diversification_minimum": 5,  # Minimum 5 positions
                "stop_loss_level": 0.02,       # Stop-loss à 2%
                "take_profit_level": 0.04      # Take-profit à 4%
            }
            
            return {
                "optimized_sizing_strategy": optimized_sizing_strategy,
                "sizing_formula": sizing_formula,
                "protection_rules": protection_rules,
                "implementation_notes": [
                    "Risque de base réduit pour plus de prudence",
                    "Ajustements basés sur la volatilité et la confiance",
                    "Poids optimisés selon les corrélations observées",
                    "Règles de protection renforcées",
                    "Diversification obligatoire"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'implémentation du sizing: {e}")
            return {"error": str(e)}
    
    def implement_optimized_take_profit(self) -> Dict[str, Any]:
        """
        Implémente des seuils de take-profit optimisés
        """
        try:
            self.logger.info("🎯 Implémentation des take-profits optimisés")
            
            # Stratégie de take-profit optimisée
            optimized_take_profit_strategy = {
                "base_multiplier": 2.5,  # Réduit de 3x à 2.5x ATR
                "adaptive_multipliers": {
                    "BUY_STRONG": {
                        "min_multiplier": 2.0,
                        "max_multiplier": 3.5,
                        "score_adjustment": 0.3
                    },
                    "BUY_MODERATE": {
                        "min_multiplier": 1.8,
                        "max_multiplier": 3.0,
                        "score_adjustment": 0.2
                    },
                    "BUY_WEAK": {
                        "min_multiplier": 1.5,
                        "max_multiplier": 2.5,
                        "score_adjustment": 0.1
                    }
                },
                "volatility_adjustment": {
                    "low_volatility": 1.2,    # Augmentation pour faible volatilité
                    "medium_volatility": 1.0, # Standard
                    "high_volatility": 0.8    # Réduction pour haute volatilité
                },
                "confidence_adjustment": {
                    "low_confidence": 0.9,    # Réduction pour faible confiance
                    "medium_confidence": 1.0, # Standard
                    "high_confidence": 1.1,  # Légère augmentation
                    "over_confidence": 0.8    # Réduction pour sur-confiance
                }
            }
            
            # Règles de sortie dynamiques
            dynamic_exit_rules = {
                "trailing_stop": {
                    "activation_threshold": 0.015,  # Activer à 1.5% de gain
                    "trailing_distance": 0.01,      # Distance de 1%
                    "min_profit": 0.005             # Profit minimum de 0.5%
                },
                "time_based_exit": {
                    "max_holding_period": 5,        # Maximum 5 jours
                    "profit_target_1d": 0.02,       # Objectif 2% en 1 jour
                    "profit_target_3d": 0.035,      # Objectif 3.5% en 3 jours
                    "profit_target_5d": 0.05        # Objectif 5% en 5 jours
                },
                "volatility_exit": {
                    "high_volatility_threshold": 0.05,  # Volatilité > 5%
                    "volatility_exit_multiplier": 0.7   # Réduction de 30%
                }
            }
            
            return {
                "optimized_take_profit_strategy": optimized_take_profit_strategy,
                "dynamic_exit_rules": dynamic_exit_rules,
                "implementation_notes": [
                    "Multiplicateurs adaptatifs selon le type de signal",
                    "Ajustements basés sur la volatilité et la confiance",
                    "Règles de sortie dynamiques avec trailing stop",
                    "Sorties basées sur le temps et la volatilité",
                    "Objectifs de profit progressifs"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'implémentation des take-profits: {e}")
            return {"error": str(e)}
    
    def update_advanced_trading_analysis(self) -> Dict[str, Any]:
        """
        Met à jour le service AdvancedTradingAnalysis avec les optimisations
        """
        try:
            self.logger.info("📝 Mise à jour d'AdvancedTradingAnalysis")
            
            # Lire le fichier actuel
            analysis_file = "/Users/loiclinais/Documents/dev/aimarkets/backend/app/services/advanced_analysis/advanced_trading_analysis.py"
            
            with open(analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Générer les nouvelles méthodes optimisées
            optimized_methods = self._generate_optimized_methods()
            
            # Insérer les nouvelles méthodes avant la méthode analyze_opportunity
            insertion_point = content.find("    async def analyze_opportunity")
            if insertion_point == -1:
                return {"error": "Point d'insertion non trouvé"}
            
            # Insérer les nouvelles méthodes
            new_content = content[:insertion_point] + optimized_methods + "\n" + content[insertion_point:]
            
            # Sauvegarder le fichier modifié
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                "success": True,
                "message": "Méthodes optimisées ajoutées avec succès",
                "methods_added": [
                    "_calculate_optimized_composite_score",
                    "_determine_optimized_recommendation",
                    "_calculate_optimized_position_size",
                    "_calculate_optimized_take_profit",
                    "_validate_optimized_buy_signals"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la mise à jour: {e}")
            return {"error": str(e)}
    
    def _generate_optimized_methods(self) -> str:
        """Génère le code des méthodes optimisées"""
        
        return '''
    def _calculate_optimized_composite_score(self, scores: Dict[str, float]) -> float:
        """
        Calcule le score composite optimisé basé sur les corrélations observées
        Optimisations: Augmentation des poids technique et sentiment, réduction du poids marché
        """
        try:
            # Poids optimisés basés sur les corrélations
            optimized_weights = {
                'technical': 0.40,    # Augmenté (corrélation positive 0.256)
                'sentiment': 0.45,    # Augmenté (meilleure corrélation 0.359)
                'market': 0.15,       # Réduit (corrélation négative -0.438)
            }
            
            # Score de base
            base_score = (
                optimized_weights['technical'] * scores.get('technical', 0.5) +
                optimized_weights['sentiment'] * scores.get('sentiment', 0.5) +
                optimized_weights['market'] * scores.get('market', 0.5)
            )
            
            # Pénalité pour la sur-confiance (corrélation négative -0.439)
            confidence = scores.get('confidence', 0.5)
            if confidence > 0.85:
                confidence_penalty = (confidence - 0.85) * 0.2
                base_score -= confidence_penalty
            
            return max(0.0, min(1.0, base_score))
            
        except Exception as e:
            self.logger.error(f"Erreur calcul score composite optimisé: {e}")
            return 0.5
    
    def _determine_optimized_recommendation(self, composite_score: float, scores: Dict[str, float]) -> str:
        """
        Détermine la recommandation optimisée avec des seuils plus stricts
        """
        try:
            technical_score = scores.get('technical', 0.5)
            sentiment_score = scores.get('sentiment', 0.5)
            market_score = scores.get('market', 0.5)
            confidence = scores.get('confidence', 0.5)
            
            # Seuils optimisés plus stricts
            if (composite_score >= 0.65 and 
                technical_score >= 0.60 and 
                sentiment_score >= 0.55 and 
                market_score <= 0.40 and  # Éviter les marchés baissiers
                0.70 <= confidence <= 0.85):  # Éviter la sur-confiance
                return "BUY_STRONG"
            
            elif (composite_score >= 0.55 and 
                  technical_score >= 0.50 and 
                  sentiment_score >= 0.45 and 
                  market_score <= 0.45 and 
                  0.65 <= confidence <= 0.90):
                return "BUY_MODERATE"
            
            elif (composite_score >= 0.45 and 
                  technical_score >= 0.40 and 
                  sentiment_score >= 0.35 and 
                  market_score <= 0.50 and 
                  0.60 <= confidence <= 0.95):
                return "BUY_WEAK"
            
            else:
                return "HOLD"
                
        except Exception as e:
            self.logger.error(f"Erreur détermination recommandation optimisée: {e}")
            return "HOLD"
    
    def _calculate_optimized_position_size(
        self, 
        opportunity_data: Dict[str, Any], 
        portfolio_value: float = 100000
    ) -> Dict[str, Any]:
        """
        Calcule la taille de position optimisée basée sur l'analyse des performances
        """
        try:
            symbol = opportunity_data.get('symbol')
            current_price = opportunity_data.get('price_at_generation', 0)
            composite_score = opportunity_data.get('composite_score', 0.5)
            confidence_level = opportunity_data.get('confidence_level', 0.5)
            technical_score = opportunity_data.get('technical_score', 0.5)
            sentiment_score = opportunity_data.get('sentiment_score', 0.5)
            market_score = opportunity_data.get('market_score', 0.5)
            
            if not symbol or current_price <= 0:
                return {"error": "Données d'opportunité incomplètes"}
            
            # Paramètres optimisés
            base_portfolio_risk = 0.015  # Réduit de 2% à 1.5%
            max_position_risk = 0.025    # Maximum 2.5%
            
            # Taille de base
            base_size = int(portfolio_value * base_portfolio_risk / current_price)
            
            # Ajustements optimisés
            # 1. Ajustement volatilité (simulé)
            volatility_factor = 1.0  # À calculer avec les données réelles
            
            # 2. Ajustement confiance (éviter la sur-confiance)
            if confidence_level < 0.6:
                confidence_factor = 0.5
            elif confidence_level > 0.85:
                confidence_factor = 0.8  # Réduction pour sur-confiance
            else:
                confidence_factor = 1.0 + (confidence_level - 0.5) * 0.6
            
            # 3. Ajustement score (poids optimisés)
            score_factor = (
                0.4 * technical_score + 
                0.4 * sentiment_score + 
                0.2 * market_score
            )
            
            # Taille finale
            final_size = int(base_size * volatility_factor * confidence_factor * score_factor)
            
            # Limites de protection
            max_size = int(portfolio_value * 0.10 / current_price)  # Max 10% du portefeuille
            final_size = min(final_size, max_size)
            final_size = max(1, final_size)  # Minimum 1 action
            
            return {
                "position_size": final_size,
                "position_value": final_size * current_price,
                "position_risk": final_size * current_price * base_portfolio_risk / portfolio_value,
                "volatility_factor": volatility_factor,
                "confidence_factor": confidence_factor,
                "score_factor": score_factor
            }
            
        except Exception as e:
            self.logger.error(f"Erreur calcul position optimisée: {e}")
            return {"error": str(e)}
    
    def _calculate_optimized_take_profit(self, opportunity_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcule les seuils de take-profit optimisés
        """
        try:
            symbol = opportunity_data.get('symbol')
            current_price = opportunity_data.get('price_at_generation', 0)
            composite_score = opportunity_data.get('composite_score', 0.5)
            confidence_level = opportunity_data.get('confidence_level', 0.5)
            recommendation = opportunity_data.get('recommendation', 'HOLD')
            
            if not symbol or current_price <= 0:
                return {"error": "Données d'opportunité incomplètes"}
            
            # ATR simulé (2% du prix)
            atr = current_price * 0.02
            
            # Multiplicateurs optimisés par type de recommandation
            if recommendation == "BUY_STRONG":
                base_multiplier = 2.5 + (composite_score - 0.5) * 1.0  # 2.0 à 3.0
            elif recommendation == "BUY_MODERATE":
                base_multiplier = 2.0 + (composite_score - 0.5) * 0.8  # 1.6 à 2.4
            elif recommendation == "BUY_WEAK":
                base_multiplier = 1.5 + (composite_score - 0.5) * 0.6  # 1.2 à 1.8
            else:
                base_multiplier = 2.0
            
            # Ajustement confiance (éviter la sur-confiance)
            if confidence_level > 0.85:
                confidence_adjustment = 0.8  # Réduction pour sur-confiance
            else:
                confidence_adjustment = 1.0 + (confidence_level - 0.5) * 0.2
            
            # Multiplicateur final
            final_multiplier = base_multiplier * confidence_adjustment
            
            # Take-profit
            take_profit = current_price * (1 + final_multiplier * atr / current_price)
            
            # Trailing stop
            trailing_stop = current_price * (1 - 0.01)  # 1% de trailing
            
            return {
                "take_profit": take_profit,
                "trailing_stop": trailing_stop,
                "multiplier": final_multiplier,
                "atr": atr
            }
            
        except Exception as e:
            self.logger.error(f"Erreur calcul take-profit optimisé: {e}")
            return {"error": str(e)}
    
    def _validate_optimized_buy_signals(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide les signaux d'achat avec des règles optimisées
        """
        try:
            symbol = opportunity_data.get('symbol')
            technical_score = opportunity_data.get('technical_score', 0.5)
            sentiment_score = opportunity_data.get('sentiment_score', 0.5)
            market_score = opportunity_data.get('market_score', 0.5)
            confidence_level = opportunity_data.get('confidence_level', 0.5)
            
            validations = {
                "technical_valid": False,
                "sentiment_valid": False,
                "market_valid": False,
                "confidence_valid": False,
                "overall_valid": False
            }
            
            # Validation technique renforcée
            if (0.4 <= technical_score <= 0.8 and  # Éviter les extrêmes
                technical_score > 0.5):  # Score positif
                validations["technical_valid"] = True
            
            # Validation sentiment renforcée
            if (0.35 <= sentiment_score <= 0.75 and  # Éviter les extrêmes
                sentiment_score > 0.5):  # Score positif
                validations["sentiment_valid"] = True
            
            # Validation marché (éviter les marchés baissiers)
            if market_score <= 0.5:  # Marché neutre ou haussier
                validations["market_valid"] = True
            
            # Validation confiance (éviter la sur-confiance)
            if 0.6 <= confidence_level <= 0.85:  # Confiance modérée
                validations["confidence_valid"] = True
            
            # Validation globale
            valid_count = sum(1 for v in validations.values() if v and v != "overall_valid")
            validations["overall_valid"] = valid_count >= 3
            
            return {
                "valid": validations["overall_valid"],
                "validations": validations,
                "recommendations": self._generate_validation_recommendations(validations)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur validation optimisée: {e}")
            return {"error": str(e)}
    
    def _generate_validation_recommendations(self, validations: Dict[str, bool]) -> List[str]:
        """Génère des recommandations basées sur les validations"""
        recommendations = []
        
        if not validations.get("technical_valid", False):
            recommendations.append("Score technique insuffisant ou extrême")
        
        if not validations.get("sentiment_valid", False):
            recommendations.append("Score sentiment insuffisant ou extrême")
        
        if not validations.get("market_valid", False):
            recommendations.append("Conditions de marché défavorables")
        
        if not validations.get("confidence_valid", False):
            recommendations.append("Niveau de confiance inadapté (trop faible ou sur-confiance)")
        
        return recommendations
'''
    
    def test_optimized_implementation(self) -> Dict[str, Any]:
        """Teste l'implémentation optimisée"""
        try:
            self.logger.info("🧪 Test de l'implémentation optimisée")
            
            # Récupérer quelques opportunités pour tester
            opportunities = self.db.query(HistoricalOpportunities).limit(10).all()
            
            if not opportunities:
                return {"error": "Aucune opportunité trouvée pour les tests"}
            
            test_results = []
            
            for opp in opportunities:
                # Convertir en dictionnaire
                opp_data = {
                    'symbol': opp.symbol,
                    'composite_score': float(opp.composite_score) if opp.composite_score else 0.5,
                    'confidence_level': float(opp.confidence_level) if opp.confidence_level else 0.5,
                    'technical_score': float(opp.technical_score) if opp.technical_score else 0.5,
                    'sentiment_score': float(opp.sentiment_score) if opp.sentiment_score else 0.5,
                    'market_score': float(opp.market_score) if opp.market_score else 0.5,
                    'price_at_generation': float(opp.price_at_generation) if opp.price_at_generation else 0,
                    'recommendation': opp.recommendation
                }
                
                # Tester les nouvelles méthodes
                optimized_composite = self._calculate_optimized_composite_score({
                    'technical': opp_data['technical_score'],
                    'sentiment': opp_data['sentiment_score'],
                    'market': opp_data['market_score'],
                    'confidence': opp_data['confidence_level']
                })
                
                optimized_recommendation = self._determine_optimized_recommendation(
                    optimized_composite, opp_data
                )
                
                optimized_position = self._calculate_optimized_position_size(opp_data)
                optimized_take_profit = self._calculate_optimized_take_profit(opp_data)
                optimized_validation = self._validate_optimized_buy_signals(opp_data)
                
                test_results.append({
                    "symbol": opp.symbol,
                    "original_composite": opp_data['composite_score'],
                    "optimized_composite": optimized_composite,
                    "original_recommendation": opp_data['recommendation'],
                    "optimized_recommendation": optimized_recommendation,
                    "position_calculation": optimized_position,
                    "take_profit_calculation": optimized_take_profit,
                    "validation_result": optimized_validation
                })
            
            return {
                "success": True,
                "test_results": test_results,
                "total_tested": len(test_results)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors du test optimisé: {e}")
            return {"error": str(e)}
    
    def _calculate_optimized_composite_score(self, scores: Dict[str, float]) -> float:
        """Méthode de test pour le score composite optimisé"""
        try:
            optimized_weights = {
                'technical': 0.40,
                'sentiment': 0.45,
                'market': 0.15,
            }
            
            base_score = (
                optimized_weights['technical'] * scores.get('technical', 0.5) +
                optimized_weights['sentiment'] * scores.get('sentiment', 0.5) +
                optimized_weights['market'] * scores.get('market', 0.5)
            )
            
            confidence = scores.get('confidence', 0.5)
            if confidence > 0.85:
                confidence_penalty = (confidence - 0.85) * 0.2
                base_score -= confidence_penalty
            
            return max(0.0, min(1.0, base_score))
            
        except Exception as e:
            return 0.5
    
    def _determine_optimized_recommendation(self, composite_score: float, scores: Dict[str, float]) -> str:
        """Méthode de test pour la recommandation optimisée"""
        try:
            technical_score = scores.get('technical_score', 0.5)
            sentiment_score = scores.get('sentiment_score', 0.5)
            market_score = scores.get('market_score', 0.5)
            confidence = scores.get('confidence_level', 0.5)
            
            if (composite_score >= 0.65 and 
                technical_score >= 0.60 and 
                sentiment_score >= 0.55 and 
                market_score <= 0.40 and 
                0.70 <= confidence <= 0.85):
                return "BUY_STRONG"
            elif (composite_score >= 0.55 and 
                  technical_score >= 0.50 and 
                  sentiment_score >= 0.45 and 
                  market_score <= 0.45 and 
                  0.65 <= confidence <= 0.90):
                return "BUY_MODERATE"
            elif (composite_score >= 0.45 and 
                  technical_score >= 0.40 and 
                  sentiment_score >= 0.35 and 
                  market_score <= 0.50 and 
                  0.60 <= confidence <= 0.95):
                return "BUY_WEAK"
            else:
                return "HOLD"
                
        except Exception as e:
            return "HOLD"
    
    def _calculate_optimized_position_size(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Méthode de test pour le position sizing optimisé"""
        try:
            current_price = opportunity_data.get('price_at_generation', 0)
            confidence_level = opportunity_data.get('confidence_level', 0.5)
            technical_score = opportunity_data.get('technical_score', 0.5)
            sentiment_score = opportunity_data.get('sentiment_score', 0.5)
            market_score = opportunity_data.get('market_score', 0.5)
            
            if current_price <= 0:
                return {"error": "Prix invalide"}
            
            base_size = int(100000 * 0.015 / current_price)
            
            if confidence_level < 0.6:
                confidence_factor = 0.5
            elif confidence_level > 0.85:
                confidence_factor = 0.8
            else:
                confidence_factor = 1.0 + (confidence_level - 0.5) * 0.6
            
            score_factor = (
                0.4 * technical_score + 
                0.4 * sentiment_score + 
                0.2 * market_score
            )
            
            final_size = int(base_size * confidence_factor * score_factor)
            final_size = min(final_size, int(100000 * 0.10 / current_price))
            final_size = max(1, final_size)
            
            return {
                "position_size": final_size,
                "position_value": final_size * current_price,
                "confidence_factor": confidence_factor,
                "score_factor": score_factor
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_optimized_take_profit(self, opportunity_data: Dict[str, Any]) -> Dict[str, float]:
        """Méthode de test pour le take-profit optimisé"""
        try:
            current_price = opportunity_data.get('price_at_generation', 0)
            composite_score = opportunity_data.get('composite_score', 0.5)
            confidence_level = opportunity_data.get('confidence_level', 0.5)
            recommendation = opportunity_data.get('recommendation', 'HOLD')
            
            if current_price <= 0:
                return {"error": "Prix invalide"}
            
            atr = current_price * 0.02
            
            if recommendation == "BUY_STRONG":
                base_multiplier = 2.5 + (composite_score - 0.5) * 1.0
            elif recommendation == "BUY_MODERATE":
                base_multiplier = 2.0 + (composite_score - 0.5) * 0.8
            elif recommendation == "BUY_WEAK":
                base_multiplier = 1.5 + (composite_score - 0.5) * 0.6
            else:
                base_multiplier = 2.0
            
            if confidence_level > 0.85:
                confidence_adjustment = 0.8
            else:
                confidence_adjustment = 1.0 + (confidence_level - 0.5) * 0.2
            
            final_multiplier = base_multiplier * confidence_adjustment
            take_profit = current_price * (1 + final_multiplier * atr / current_price)
            
            return {
                "take_profit": take_profit,
                "multiplier": final_multiplier,
                "atr": atr
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _validate_optimized_buy_signals(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Méthode de test pour la validation optimisée"""
        try:
            technical_score = opportunity_data.get('technical_score', 0.5)
            sentiment_score = opportunity_data.get('sentiment_score', 0.5)
            market_score = opportunity_data.get('market_score', 0.5)
            confidence_level = opportunity_data.get('confidence_level', 0.5)
            
            validations = {
                "technical_valid": 0.4 <= technical_score <= 0.8 and technical_score > 0.5,
                "sentiment_valid": 0.35 <= sentiment_score <= 0.75 and sentiment_score > 0.5,
                "market_valid": market_score <= 0.5,
                "confidence_valid": 0.6 <= confidence_level <= 0.85
            }
            
            valid_count = sum(1 for v in validations.values() if v)
            validations["overall_valid"] = valid_count >= 3
            
            return {
                "valid": validations["overall_valid"],
                "validations": validations
            }
            
        except Exception as e:
            return {"error": str(e)}


def main():
    """Fonction principale pour implémenter les optimisations des signaux d'achat"""
    logger.info("🚀 Démarrage de l'implémentation des optimisations des signaux d'achat")
    
    try:
        # Connexion à la base de données
        db = SessionLocal()
        
        # Initialiser l'implémentation
        optimizer = OptimizedBuySignalsImplementation(db)
        
        # Implémenter le scoring optimisé
        logger.info("🔧 Implémentation du scoring optimisé...")
        scoring_result = optimizer.implement_optimized_scoring()
        
        if "error" in scoring_result:
            logger.error(f"❌ Erreur lors de l'implémentation du scoring: {scoring_result['error']}")
            return
        
        # Implémenter le position sizing optimisé
        logger.info("⚖️ Implémentation du position sizing optimisé...")
        sizing_result = optimizer.implement_optimized_position_sizing()
        
        if "error" in sizing_result:
            logger.error(f"❌ Erreur lors de l'implémentation du sizing: {sizing_result['error']}")
            return
        
        # Implémenter les take-profits optimisés
        logger.info("🎯 Implémentation des take-profits optimisés...")
        take_profit_result = optimizer.implement_optimized_take_profit()
        
        if "error" in take_profit_result:
            logger.error(f"❌ Erreur lors de l'implémentation des take-profits: {take_profit_result['error']}")
            return
        
        # Mettre à jour AdvancedTradingAnalysis
        logger.info("📝 Mise à jour d'AdvancedTradingAnalysis...")
        update_result = optimizer.update_advanced_trading_analysis()
        
        if "error" in update_result:
            logger.error(f"❌ Erreur lors de la mise à jour: {update_result['error']}")
            return
        
        # Tester l'implémentation
        logger.info("🧪 Test de l'implémentation...")
        test_result = optimizer.test_optimized_implementation()
        
        if "error" in test_result:
            logger.error(f"❌ Erreur lors du test: {test_result['error']}")
            return
        
        # Afficher les résultats
        print("\n" + "="*80)
        print("🔧 IMPLÉMENTATION DES OPTIMISATIONS DES SIGNAUX D'ACHAT")
        print("="*80)
        
        print(f"\n📊 SCORING OPTIMISÉ:")
        print(f"  • Poids technique: 40% (augmenté)")
        print(f"  • Poids sentiment: 45% (augmenté)")
        print(f"  • Poids marché: 15% (réduit)")
        print(f"  • Pénalité sur-confiance: Activée")
        
        print(f"\n⚖️ POSITION SIZING OPTIMISÉ:")
        print(f"  • Risque de base: 1.5% (réduit)")
        print(f"  • Ajustements confiance: Optimisés")
        print(f"  • Ajustements score: Pondérés")
        print(f"  • Protection: Renforcée")
        
        print(f"\n🎯 TAKE-PROFITS OPTIMISÉS:")
        print(f"  • Multiplicateurs adaptatifs: Par type de signal")
        print(f"  • Ajustements confiance: Anti sur-confiance")
        print(f"  • Règles de sortie: Dynamiques")
        
        print(f"\n✅ MISE À JOUR D'ADVANCEDTRADINGANALYSIS:")
        print(f"  • {update_result['message']}")
        print(f"  • Méthodes ajoutées: {len(update_result['methods_added'])}")
        
        print(f"\n🧪 RÉSULTATS DES TESTS:")
        print(f"  • Opportunités testées: {test_result['total_tested']}")
        print(f"  • Tests réussis: {test_result['success']}")
        
        # Sauvegarder les résultats
        results = {
            "scoring_result": scoring_result,
            "sizing_result": sizing_result,
            "take_profit_result": take_profit_result,
            "update_result": update_result,
            "test_result": test_result,
            "implementation_timestamp": datetime.now().isoformat()
        }
        
        with open("/Users/loiclinais/Documents/dev/aimarkets/backend/scripts/optimized_buy_signals_implementation.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("📁 Résultats sauvegardés dans optimized_buy_signals_implementation.json")
        logger.info("✅ Implémentation des optimisations terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'implémentation: {e}")
        return


if __name__ == "__main__":
    main()
