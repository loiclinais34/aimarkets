"""
Service d'Analyse Combinée Avancée
Phase 4: Intégration et Optimisation

Ce service orchestre tous les services d'analyse développés dans les phases précédentes :
- Analyse technique (Phase 1)
- Indicateurs de marché (Phase 2) 
- Analyse de sentiment (Phase 3)
- Intégration ML existante
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, date
import logging
from dataclasses import dataclass
from sqlalchemy.orm import Session

# Import des modèles de base de données
from app.models.database import HistoricalData, SentimentData, TechnicalIndicators, SentimentIndicators
from app.models.market_indicators import MarketIndicators, MomentumIndicators, VolatilityIndicators
from app.models.technical_analysis import CandlestickPatterns
from app.models.sentiment_analysis import GARCHModels, MonteCarloSimulations, MarkovChainAnalysis
from app.models.advanced_opportunities import AdvancedOpportunity

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Résultat d'une analyse complète"""
    symbol: str
    analysis_date: datetime
    technical_score: float
    sentiment_score: float
    market_score: float
    ml_score: float
    candlestick_score: float
    garch_score: float
    monte_carlo_score: float
    markov_score: float
    volatility_score: float
    composite_score: float
    confidence_level: float
    recommendation: str
    risk_level: str
    technical_analysis: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    market_indicators: Dict[str, Any]
    ml_analysis: Dict[str, Any]
    candlestick_analysis: Dict[str, Any]
    garch_analysis: Dict[str, Any]
    monte_carlo_analysis: Dict[str, Any]
    markov_analysis: Dict[str, Any]
    volatility_analysis: Dict[str, Any]

class AdvancedTradingAnalysis:
    """
    Service d'analyse combinée avancée
    
    Orchestre tous les services d'analyse pour fournir une vue complète
    des opportunités d'investissement.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    

    def _calculate_position_size(self, opportunity_data: Dict[str, Any], portfolio_value: float = 100000) -> Dict[str, Any]:
        """
        Calcule la taille de position optimale basée sur le risque
        Phase 3: Gestion du risque
        """
        try:
            symbol = opportunity_data.get('symbol')
            current_price = opportunity_data.get('price_at_generation', 0)
            composite_score = opportunity_data.get('composite_score', 0.5)
            confidence_level = opportunity_data.get('confidence_level', 0.5)
            risk_level = opportunity_data.get('risk_level', 'MEDIUM')
            
            if not symbol or current_price <= 0:
                return {"error": "Données d'opportunité incomplètes"}
            
            # Utiliser le risk manager
            risk_manager = Phase3RiskManager(self.db)
            return risk_manager.calculate_position_size(opportunity_data, portfolio_value)
            
        except Exception as e:
            self.logger.error(f"Erreur calcul taille position: {e}")
            return {"error": str(e)}
    
    def _calculate_portfolio_risk(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule les métriques de risque du portefeuille
        Phase 3: Gestion du risque
        """
        try:
            risk_manager = Phase3RiskManager(self.db)
            return risk_manager.calculate_portfolio_risk_metrics(positions)
            
        except Exception as e:
            self.logger.error(f"Erreur calcul risque portefeuille: {e}")
            return {"error": str(e)}
    
    def _calculate_stop_loss_levels(self, opportunity_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcule les niveaux de stop-loss dynamiques
        Phase 3: Gestion du risque
        """
        try:
            symbol = opportunity_data.get('symbol')
            current_price = opportunity_data.get('price_at_generation', 0)
            
            # Récupérer l'ATR
            technical_data = self._get_technical_indicators(symbol)
            atr = technical_data.get('atr', 0.02 * current_price)  # 2% par défaut
            
            # Calculer les niveaux
            stop_loss = current_price * (1 - 2.0 * atr / current_price)  # 2x ATR
            trailing_stop = current_price * (1 - 1.5 * atr / current_price)  # 1.5x ATR
            
            return {
                "stop_loss": stop_loss,
                "trailing_stop": trailing_stop,
                "atr": atr
            }
            
        except Exception as e:
            self.logger.error(f"Erreur calcul stop-loss: {e}")
            return {"error": str(e)}
    
    def _calculate_take_profit_levels(self, opportunity_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcule les niveaux de take-profit dynamiques
        Phase 3: Gestion du risque
        """
        try:
            symbol = opportunity_data.get('symbol')
            current_price = opportunity_data.get('price_at_generation', 0)
            composite_score = opportunity_data.get('composite_score', 0.5)
            
            # Récupérer l'ATR
            technical_data = self._get_technical_indicators(symbol)
            atr = technical_data.get('atr', 0.02 * current_price)
            
            # Ajuster selon la qualité du signal
            multiplier = 2.0 + (composite_score - 0.5) * 2.0  # 1x à 3x ATR
            
            take_profit = current_price * (1 + multiplier * atr / current_price)
            
            return {
                "take_profit": take_profit,
                "multiplier": multiplier,
                "atr": atr
            }
            
        except Exception as e:
            self.logger.error(f"Erreur calcul take-profit: {e}")
            return {"error": str(e)}
    
    def _validate_risk_parameters(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide les paramètres de risque d'une opportunité
        Phase 3: Gestion du risque
        """
        try:
            symbol = opportunity_data.get('symbol')
            risk_level = opportunity_data.get('risk_level', 'MEDIUM')
            confidence_level = opportunity_data.get('confidence_level', 0.5)
            
            # Récupérer les données de volatilité
            volatility_data = self._get_volatility_indicators(symbol)
            current_volatility = volatility_data.get('current_volatility', 0.02)
            
            # Validation des paramètres
            validations = {
                "volatility_acceptable": current_volatility < 0.05,  # < 5%
                "confidence_sufficient": confidence_level > 0.6,
                "risk_level_appropriate": risk_level in ['LOW', 'MEDIUM'],
                "symbol_liquid": True  # À implémenter avec les données de volume
            }
            
            overall_valid = all(validations.values())
            
            return {
                "valid": overall_valid,
                "validations": validations,
                "current_volatility": current_volatility,
                "recommendations": self._generate_risk_recommendations(validations)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur validation paramètres risque: {e}")
            return {"error": str(e)}
    
    def _generate_risk_recommendations(self, validations: Dict[str, bool]) -> List[str]:
        """Génère des recommandations basées sur les validations de risque"""
        recommendations = []
        
        if not validations.get("volatility_acceptable", True):
            recommendations.append("Volatilité élevée - Réduire la taille de position")
        
        if not validations.get("confidence_sufficient", True):
            recommendations.append("Confiance faible - Attendre un signal plus fort")
        
        if not validations.get("risk_level_appropriate", True):
            recommendations.append("Niveau de risque élevé - Surveiller attentivement")
        
        return recommendations


    def _calculate_position_size(self, opportunity_data: Dict[str, Any], portfolio_value: float = 100000) -> Dict[str, Any]:
        """
        Calcule la taille de position optimale basée sur le risque
        Phase 3: Gestion du risque
        """
        try:
            symbol = opportunity_data.get('symbol')
            current_price = opportunity_data.get('price_at_generation', 0)
            composite_score = opportunity_data.get('composite_score', 0.5)
            confidence_level = opportunity_data.get('confidence_level', 0.5)
            risk_level = opportunity_data.get('risk_level', 'MEDIUM')
            
            if not symbol or current_price <= 0:
                return {"error": "Données d'opportunité incomplètes"}
            
            # Utiliser le risk manager
            risk_manager = Phase3RiskManager(self.db)
            return risk_manager.calculate_position_size(opportunity_data, portfolio_value)
            
        except Exception as e:
            self.logger.error(f"Erreur calcul taille position: {e}")
            return {"error": str(e)}
    
    def _calculate_portfolio_risk(self, positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule les métriques de risque du portefeuille
        Phase 3: Gestion du risque
        """
        try:
            risk_manager = Phase3RiskManager(self.db)
            return risk_manager.calculate_portfolio_risk_metrics(positions)
            
        except Exception as e:
            self.logger.error(f"Erreur calcul risque portefeuille: {e}")
            return {"error": str(e)}
    
    def _calculate_stop_loss_levels(self, opportunity_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcule les niveaux de stop-loss dynamiques
        Phase 3: Gestion du risque
        """
        try:
            symbol = opportunity_data.get('symbol')
            current_price = opportunity_data.get('price_at_generation', 0)
            
            # Récupérer l'ATR
            technical_data = self._get_technical_indicators(symbol)
            atr = technical_data.get('atr', 0.02 * current_price)  # 2% par défaut
            
            # Calculer les niveaux
            stop_loss = current_price * (1 - 2.0 * atr / current_price)  # 2x ATR
            trailing_stop = current_price * (1 - 1.5 * atr / current_price)  # 1.5x ATR
            
            return {
                "stop_loss": stop_loss,
                "trailing_stop": trailing_stop,
                "atr": atr
            }
            
        except Exception as e:
            self.logger.error(f"Erreur calcul stop-loss: {e}")
            return {"error": str(e)}
    
    def _calculate_take_profit_levels(self, opportunity_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calcule les niveaux de take-profit dynamiques
        Phase 3: Gestion du risque
        """
        try:
            symbol = opportunity_data.get('symbol')
            current_price = opportunity_data.get('price_at_generation', 0)
            composite_score = opportunity_data.get('composite_score', 0.5)
            
            # Récupérer l'ATR
            technical_data = self._get_technical_indicators(symbol)
            atr = technical_data.get('atr', 0.02 * current_price)
            
            # Ajuster selon la qualité du signal
            multiplier = 2.0 + (composite_score - 0.5) * 2.0  # 1x à 3x ATR
            
            take_profit = current_price * (1 + multiplier * atr / current_price)
            
            return {
                "take_profit": take_profit,
                "multiplier": multiplier,
                "atr": atr
            }
            
        except Exception as e:
            self.logger.error(f"Erreur calcul take-profit: {e}")
            return {"error": str(e)}
    
    def _validate_risk_parameters(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valide les paramètres de risque d'une opportunité
        Phase 3: Gestion du risque
        """
        try:
            symbol = opportunity_data.get('symbol')
            risk_level = opportunity_data.get('risk_level', 'MEDIUM')
            confidence_level = opportunity_data.get('confidence_level', 0.5)
            
            # Récupérer les données de volatilité
            volatility_data = self._get_volatility_indicators(symbol)
            current_volatility = volatility_data.get('current_volatility', 0.02)
            
            # Validation des paramètres
            validations = {
                "volatility_acceptable": current_volatility < 0.05,  # < 5%
                "confidence_sufficient": confidence_level > 0.6,
                "risk_level_appropriate": risk_level in ['LOW', 'MEDIUM'],
                "symbol_liquid": True  # À implémenter avec les données de volume
            }
            
            overall_valid = all(validations.values())
            
            return {
                "valid": overall_valid,
                "validations": validations,
                "current_volatility": current_volatility,
                "recommendations": self._generate_risk_recommendations(validations)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur validation paramètres risque: {e}")
            return {"error": str(e)}
    
    def _generate_risk_recommendations(self, validations: Dict[str, bool]) -> List[str]:
        """Génère des recommandations basées sur les validations de risque"""
        recommendations = []
        
        if not validations.get("volatility_acceptable", True):
            recommendations.append("Volatilité élevée - Réduire la taille de position")
        
        if not validations.get("confidence_sufficient", True):
            recommendations.append("Confiance faible - Attendre un signal plus fort")
        
        if not validations.get("risk_level_appropriate", True):
            recommendations.append("Niveau de risque élevé - Surveiller attentivement")
        
        return recommendations


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


    def _calculate_adjusted_optimized_composite_score(
        self, 
        technical_score: float, 
        sentiment_score: float, 
        market_score: float, 
        ml_score: float = 0.0,
        candlestick_score: float = 0.0,
        garch_score: float = 0.0,
        monte_carlo_score: float = 0.0,
        markov_score: float = 0.0,
        volatility_score: float = 0.0
    ) -> float:
        """
        Calcule le score composite avec priorité au score technique (80%)
        Recommandation 2: Prioriser le score technique dans la formule de scoring
        """
        try:
            # Poids optimisés - priorité forte au score technique
            priority_weights = {
                'technical': 0.8,      # 80% - priorité maximale
                'sentiment': 0.1,  # 10%
                'market': 0.1         # 10%
            }
            
            # Score composite avec priorité technique
            composite_score = (
                priority_weights['technical'] * technical_score +
                priority_weights['sentiment'] * sentiment_score +
                priority_weights['market'] * market_score
            )
            
            return round(composite_score, 4)
            
        except Exception as e:
            self.logger.error(f"Error calculating priority optimized composite score: {e}")
            return 0.5
    
    def _determine_adjusted_optimized_recommendation(
        self, 
        composite_score: float, 
        technical_score: float,
        confidence_level: float
    ) -> str:
        """
        Détermine la recommandation avec les seuils optimisés
        Recommandation 1: Utiliser les seuils optimisés pour la génération d'opportunités
        """
        try:
            # Seuils optimaux basés sur l'analyse de performance
            TECH_THRESHOLD = 0.533
            COMP_THRESHOLD = 0.651
            CONF_THRESHOLD = 0.6
            
            # Validation des seuils optimaux
            tech_valid = technical_score >= TECH_THRESHOLD
            comp_valid = composite_score >= COMP_THRESHOLD
            conf_valid = confidence_level >= CONF_THRESHOLD
            
            # Logique de recommandation avec seuils optimisés
            if comp_valid and tech_valid and conf_valid:
                return "BUY_STRONG"
            elif comp_valid and tech_valid:
                return "BUY_MODERATE"
            elif comp_valid or tech_valid:
                return "BUY_WEAK"
            elif composite_score >= 0.4:
                return "HOLD"
            else:
                return "SELL_MODERATE"
                
        except Exception as e:
            self.logger.error(f"Error determining priority optimized recommendation: {e}")
            return "HOLD"
    
    def _validate_adjusted_optimized_signals(
        self, 
        technical_score: float, 
        composite_score: float,
        confidence_level: float
    ) -> Dict[str, bool]:
        """
        Valide les signaux avec les seuils optimisés
        Recommandation 3: Appliquer la validation des signaux optimisés
        """
        validation = {
            "technical_threshold_met": False,
            "composite_threshold_met": False,
            "confidence_threshold_met": False,
            "overall_valid": False
        }
        
        try:
            # Seuils optimaux
            TECH_THRESHOLD = 0.533
            COMP_THRESHOLD = 0.651
            CONF_THRESHOLD = 0.6
            
            # Validation des seuils
            validation["technical_threshold_met"] = technical_score >= TECH_THRESHOLD
            validation["composite_threshold_met"] = composite_score >= COMP_THRESHOLD
            validation["confidence_threshold_met"] = confidence_level >= CONF_THRESHOLD
            
            # Validation globale : au moins 2 critères sur 3
            valid_criteria = sum(1 for k, v in validation.items() if k != "overall_valid" and v)
            validation["overall_valid"] = valid_criteria >= 2
            
        except Exception as e:
            self.logger.warning(f"Erreur lors de la validation optimisée: {e}")
        
        return validation
    
    def _apply_adjusted_optimized_filtering(
        self, 
        technical_score: float, 
        composite_score: float,
        confidence_level: float
    ) -> bool:
        """
        Applique le filtrage optimisé pour ne garder que les opportunités de haute qualité
        Combine les 3 recommandations prioritaires
        """
        try:
            # Seuils optimaux
            TECH_THRESHOLD = 0.533
            COMP_THRESHOLD = 0.651
            CONF_THRESHOLD = 0.6
            
            # Validation des signaux
            validation = self._validate_adjusted_optimized_signals(
                technical_score, composite_score, confidence_level
            )
            
            # Filtrage strict : au moins 2 critères sur 3
            return validation["overall_valid"]
            
        except Exception as e:
            self.logger.warning(f"Erreur lors du filtrage optimisé: {e}")
            return False


    def _calculate_adjusted_optimized_composite_score(
        self, 
        technical_score: float, 
        sentiment_score: float, 
        market_score: float, 
        ml_score: float = 0.0,
        candlestick_score: float = 0.0,
        garch_score: float = 0.0,
        monte_carlo_score: float = 0.0,
        markov_score: float = 0.0,
        volatility_score: float = 0.0
    ) -> float:
        """
        Calcule le score composite avec priorité au score technique (80%)
        Seuils ajustés pour être plus réalistes
        """
        try:
            # Poids optimisés - priorité forte au score technique
            priority_weights = {
                'technical': 0.8,      # 80% - priorité maximale
                'sentiment': 0.1,      # 10%
                'market': 0.1          # 10%
            }
            
            # Score composite avec priorité technique
            composite_score = (
                priority_weights['technical'] * technical_score +
                priority_weights['sentiment'] * sentiment_score +
                priority_weights['market'] * market_score
            )
            
            return round(composite_score, 4)
            
        except Exception as e:
            self.logger.error(f"Error calculating adjusted optimized composite score: {e}")
            return 0.5
    
    def _determine_adjusted_optimized_recommendation(
        self, 
        composite_score: float, 
        technical_score: float,
        confidence_level: float
    ) -> str:
        """
        Détermine la recommandation avec les seuils ajustés
        Seuils plus réalistes basés sur l'analyse des données
        """
        try:
            # Seuils ajustés plus réalistes
            TECH_THRESHOLD = 0.45
            COMP_THRESHOLD = 0.5
            CONF_THRESHOLD = 0.6
            
            # Validation des seuils ajustés
            tech_valid = technical_score >= TECH_THRESHOLD
            comp_valid = composite_score >= COMP_THRESHOLD
            conf_valid = confidence_level >= CONF_THRESHOLD
            
            # Logique de recommandation avec seuils ajustés
            if comp_valid and tech_valid and conf_valid:
                return "BUY_STRONG"
            elif comp_valid and tech_valid:
                return "BUY_MODERATE"
            elif comp_valid or tech_valid:
                return "BUY_WEAK"
            elif composite_score >= 0.4:
                return "HOLD"
            else:
                return "SELL_MODERATE"
                
        except Exception as e:
            self.logger.error(f"Error determining adjusted optimized recommendation: {e}")
            return "HOLD"
    
    def _validate_adjusted_optimized_signals(
        self, 
        technical_score: float, 
        composite_score: float,
        confidence_level: float
    ) -> Dict[str, bool]:
        """
        Valide les signaux avec les seuils ajustés
        Seuils plus réalistes pour une meilleure sélection
        """
        validation = {
            "technical_threshold_met": False,
            "composite_threshold_met": False,
            "confidence_threshold_met": False,
            "overall_valid": False
        }
        
        try:
            # Seuils ajustés
            TECH_THRESHOLD = 0.45
            COMP_THRESHOLD = 0.5
            CONF_THRESHOLD = 0.6
            
            # Validation des seuils
            validation["technical_threshold_met"] = technical_score >= TECH_THRESHOLD
            validation["composite_threshold_met"] = composite_score >= COMP_THRESHOLD
            validation["confidence_threshold_met"] = confidence_level >= CONF_THRESHOLD
            
            # Validation globale : au moins 2 critères sur 3
            valid_criteria = sum(1 for k, v in validation.items() if k != "overall_valid" and v)
            validation["overall_valid"] = valid_criteria >= 2
            
        except Exception as e:
            self.logger.warning(f"Erreur lors de la validation ajustée: {e}")
        
        return validation
    
    def _apply_adjusted_optimized_filtering(
        self, 
        technical_score: float, 
        composite_score: float,
        confidence_level: float
    ) -> bool:
        """
        Applique le filtrage ajusté pour ne garder que les opportunités de qualité
        Seuils plus réalistes pour une meilleure sélection
        """
        try:
            # Seuils ajustés
            TECH_THRESHOLD = 0.45
            COMP_THRESHOLD = 0.5
            CONF_THRESHOLD = 0.6
            
            # Validation des signaux
            validation = self._validate_adjusted_optimized_signals(
                technical_score, composite_score, confidence_level
            )
            
            # Filtrage ajusté : au moins 2 critères sur 3
            return validation["overall_valid"]
            
        except Exception as e:
            self.logger.warning(f"Erreur lors du filtrage ajusté: {e}")
            return False

    async def analyze_opportunity(
        self, 
        symbol: str, 
        time_horizon: int = 30,
        include_ml: bool = True,
        db: Session = None,
        target_date: date = None
    ) -> AnalysisResult:
        """
        Analyse complète d'une opportunité d'investissement
        
        Args:
            symbol: Symbole à analyser
            time_horizon: Horizon temporel en jours
            include_ml: Inclure l'analyse ML
            db: Session de base de données
            
        Returns:
            AnalysisResult: Résultat complet de l'analyse
        """
        try:
            self.logger.info(f"Starting comprehensive analysis for {symbol}")
            
            # Analyse technique simplifiée
            technical_score, technical_analysis = await self._analyze_technical(symbol, db, target_date)
            
            # Analyse de sentiment simplifiée
            sentiment_score, sentiment_analysis = await self._analyze_sentiment(symbol, db, target_date)
            
            # Analyse de marché simplifiée
            market_score, market_indicators = await self._analyze_market(symbol, db, target_date)
            
            # Analyse des patterns de candlesticks
            candlestick_score, candlestick_analysis = await self._analyze_candlestick_patterns(symbol, db)
            
            # Analyse des modèles GARCH
            garch_score, garch_analysis = await self._analyze_garch_models(symbol, db)
            
            # Analyse des simulations Monte Carlo
            monte_carlo_score, monte_carlo_analysis = await self._analyze_monte_carlo(symbol, db)
            
            # Analyse des chaînes de Markov
            markov_score, markov_analysis = await self._analyze_markov_chains(symbol, db)
            
            # Analyse de la volatilité
            volatility_score, volatility_analysis = await self._analyze_volatility(symbol, db)
            
            # Analyse ML (si demandée)
            ml_score = 0.5  # Score neutre par défaut
            ml_analysis = {}
            if include_ml:
                ml_score, ml_analysis = await self._analyze_ml(symbol, db)
            
            # Calcul du score composite
            composite_score = self._calculate_adjusted_optimized_composite_score(
                technical_score, sentiment_score, market_score, ml_score,
                candlestick_score, garch_score, monte_carlo_score, markov_score, volatility_score
            )
            
            # Calcul du niveau de confiance avec validation des indicateurs (Phase 2)
            confidence_level = self._calculate_confidence_level(
                technical_score, sentiment_score, market_score, ml_score,
                candlestick_score, garch_score, monte_carlo_score, markov_score, volatility_score,
                technical_indicators=technical_analysis,
                sentiment_indicators=sentiment_analysis,
                market_indicators=market_indicators
            )
            
            # Détermination de la recommandation avec les seuils optimisés
            recommendation = self._determine_adjusted_optimized_recommendation(
                composite_score, technical_score, confidence_level
            )
            
            # Validation des signaux optimisés (Recommandation 3)
            signal_validation = self._validate_adjusted_optimized_signals(
                technical_score, composite_score, confidence_level
            )
            
            # Filtrage optimisé - ne garder que les opportunités de haute qualité
            if not self._apply_adjusted_optimized_filtering(
                technical_score, composite_score, confidence_level
            ):
                # Si le signal ne passe pas le filtrage, retourner HOLD
                recommendation = "HOLD"
            
            # Détermination du niveau de risque basé sur la validation
            if signal_validation["overall_valid"]:
                if confidence_level >= 0.8:
                    risk_level = "LOW"
                elif confidence_level >= 0.6:
                    risk_level = "MEDIUM"
                else:
                    risk_level = "HIGH"
            else:
                risk_level = "HIGH"
            
            result = AnalysisResult(
                symbol=symbol,
                analysis_date=datetime.now(),
                technical_score=technical_score,
                sentiment_score=sentiment_score,
                market_score=market_score,
                ml_score=ml_score,
                candlestick_score=candlestick_score,
                garch_score=garch_score,
                monte_carlo_score=monte_carlo_score,
                markov_score=markov_score,
                volatility_score=volatility_score,
                composite_score=composite_score,
                confidence_level=confidence_level,
                recommendation=recommendation,
                risk_level=risk_level,
                technical_analysis=technical_analysis,
                sentiment_analysis=sentiment_analysis,
                market_indicators=market_indicators,
                ml_analysis=ml_analysis,
                candlestick_analysis=candlestick_analysis,
                garch_analysis=garch_analysis,
                monte_carlo_analysis=monte_carlo_analysis,
                markov_analysis=markov_analysis,
                volatility_analysis=volatility_analysis
            )
            
            self.logger.info(f"Analysis completed for {symbol}: {recommendation}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            raise
    
    async def _analyze_technical(self, symbol: str, db: Session, target_date: date = None) -> Tuple[float, Dict[str, Any]]:
        """Analyse technique robuste basée sur l'historique des indicateurs avec scoring multi-dimensionnel"""
        try:
            # Récupérer l'historique des indicateurs techniques (60 jours pour les Z-scores)
            # Pour les opportunités historiques, utiliser les données disponibles à la date cible
            from sqlalchemy import func
            
            if target_date:
                # Pour les opportunités historiques, récupérer les indicateurs disponibles à cette date
                indicators_history = db.query(TechnicalIndicators)\
                    .filter(TechnicalIndicators.symbol == symbol)\
                    .filter(TechnicalIndicators.date <= target_date)\
                    .order_by(TechnicalIndicators.date.desc())\
                    .limit(60)\
                    .all()
            else:
                # Pour les opportunités en temps réel, utiliser la logique existante
                # Récupérer la date de dernière mise à jour pour ce symbole
                max_updated_at = db.query(func.max(TechnicalIndicators.updated_at))\
                    .filter(TechnicalIndicators.symbol == symbol)\
                    .scalar()
                
                if not max_updated_at:
                    return 0.5, {"status": "no_data", "message": "No technical indicators found"}
                
                # Récupérer les indicateurs avec la dernière mise à jour
                indicators_history = db.query(TechnicalIndicators)\
                    .filter(TechnicalIndicators.symbol == symbol)\
                    .filter(TechnicalIndicators.updated_at == max_updated_at)\
                    .order_by(TechnicalIndicators.date.desc())\
                    .limit(60)\
                    .all()
            
            if not indicators_history:
                return 0.5, {"status": "no_data", "message": "No technical indicators found"}
            
            # Récupérer l'historique des prix (60 jours)
            if target_date:
                # Pour les opportunités historiques, récupérer les prix disponibles à cette date
                price_history = db.query(HistoricalData)\
                    .filter(HistoricalData.symbol == symbol)\
                    .filter(HistoricalData.date <= target_date)\
                    .order_by(HistoricalData.date.desc())\
                    .limit(60)\
                    .all()
            else:
                # Pour les opportunités en temps réel, utiliser la logique existante
                price_history = db.query(HistoricalData)\
                    .filter(HistoricalData.symbol == symbol)\
                    .order_by(HistoricalData.date.desc())\
                    .limit(60)\
                    .all()
            
            if not price_history:
                return 0.5, {"status": "no_price_data", "message": "No price history found"}
            
            # Convertir en DataFrame pour les calculs
            import pandas as pd
            
            # Créer DataFrame des indicateurs
            indicators_df = pd.DataFrame([{
                'date': ind.date,
                'rsi_14': float(ind.rsi_14) if ind.rsi_14 is not None else None,
                'macd': float(ind.macd) if ind.macd is not None else None,
                'macd_signal': float(ind.macd_signal) if ind.macd_signal is not None else None,
                'macd_histogram': float(ind.macd_histogram) if ind.macd_histogram is not None else None,
                'bb_upper': float(ind.bb_upper) if ind.bb_upper is not None else None,
                'bb_lower': float(ind.bb_lower) if ind.bb_lower is not None else None,
                'bb_middle': float(ind.bb_middle) if ind.bb_middle is not None else None,
                'sma_20': float(ind.sma_20) if ind.sma_20 is not None else None,
                'sma_50': float(ind.sma_50) if ind.sma_50 is not None else None,
                'sma_200': float(ind.sma_200) if ind.sma_200 is not None else None,
                'ema_20': float(ind.ema_20) if ind.ema_20 is not None else None,
                'ema_50': float(ind.ema_50) if ind.ema_50 is not None else None,
                'williams_r': float(ind.williams_r) if ind.williams_r is not None else None,
                'atr_14': float(ind.atr_14) if ind.atr_14 is not None else None,
                'obv': float(ind.obv) if ind.obv is not None else None,
                'volume_sma_20': float(ind.volume_sma_20) if ind.volume_sma_20 is not None else None,
                'stochastic_k': float(ind.stochastic_k) if ind.stochastic_k is not None else None,
                'stochastic_d': float(ind.stochastic_d) if ind.stochastic_d is not None else None,
                'roc': float(ind.roc) if ind.roc is not None else None,
                'bb_width': float(ind.bb_width) if ind.bb_width is not None else None
            } for ind in indicators_history])
            
            # Créer DataFrame des prix
            price_df = pd.DataFrame([{
                'date': price.date,
                'close': float(price.close),
                'volume': float(price.volume) if price.volume is not None else None
            } for price in price_history])
            
            # Trier par date (plus ancien en premier)
            indicators_df = indicators_df.sort_values('date').reset_index(drop=True)
            price_df = price_df.sort_values('date').reset_index(drop=True)
            
            # Calculer les scores avec l'historique
            trend_score = self._calculate_trend_score_with_history(indicators_df, price_df)
            momentum_score = self._calculate_momentum_score_with_history(indicators_df)
            obos_score = self._calculate_obos_score_with_history(indicators_df, price_df)
            volume_score = self._calculate_volume_score_with_history(indicators_df, price_df)
            volatility_score = self._calculate_volatility_structure_score_with_history(indicators_df, price_df)
            
            # Score composite technique (0-100)
            technical_score = (
                trend_score * 0.30 +      # 30% - Tendance
                momentum_score * 0.25 +   # 25% - Momentum
                obos_score * 0.20 +       # 20% - Overbought/Oversold
                volume_score * 0.15 +     # 15% - Volume
                volatility_score * 0.10   # 10% - Structure/Volatilité
            )
            
            # Normalisation (0-1)
            normalized_score = technical_score / 100.0
            
            # Données les plus récentes pour l'analyse
            latest_indicators = indicators_df.iloc[-1]
            latest_price = price_df.iloc[-1]
            
            # Analyse détaillée des indicateurs
            analysis = {
                "trend_score": trend_score,
                "momentum_score": momentum_score,
                "obos_score": obos_score,
                "volume_score": volume_score,
                "volatility_score": volatility_score,
                "composite_technical_score": technical_score,
                "rsi_14": latest_indicators['rsi_14'],
                "macd": latest_indicators['macd'],
                "macd_signal": latest_indicators['macd_signal'],
                "macd_histogram": latest_indicators['macd_histogram'],
                "bb_upper": latest_indicators['bb_upper'],
                "bb_lower": latest_indicators['bb_lower'],
                "bb_middle": latest_indicators['bb_middle'],
                "sma_20": latest_indicators['sma_20'],
                "sma_50": latest_indicators['sma_50'],
                "sma_200": latest_indicators['sma_200'],
                "ema_20": latest_indicators['ema_20'],
                "ema_50": latest_indicators['ema_50'],
                "williams_r": latest_indicators['williams_r'],
                "atr_14": latest_indicators['atr_14'],
                "obv": latest_indicators['obv'],
                "current_price": latest_price['close'],
                "current_volume": latest_price['volume'],
                "score": normalized_score
            }
            
            return normalized_score, analysis
                
        except Exception as e:
            self.logger.error(f"Error in technical analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_sentiment(self, symbol: str, db: Session, target_date: date = None) -> Tuple[float, Dict[str, Any]]:
        """Analyse de sentiment basée sur les vrais indicateurs"""
        try:
            if target_date:
                # Pour les opportunités historiques, récupérer les indicateurs disponibles à cette date
                indicators = db.query(SentimentIndicators)\
                    .filter(SentimentIndicators.symbol == symbol)\
                    .filter(SentimentIndicators.date <= target_date)\
                    .order_by(SentimentIndicators.date.desc())\
                    .limit(1)\
                    .first()
            else:
                # Pour les opportunités en temps réel, utiliser la logique existante
                from sqlalchemy import func
                max_updated_at = db.query(func.max(SentimentIndicators.updated_at))\
                    .filter(SentimentIndicators.symbol == symbol)\
                    .scalar()
                
                if not max_updated_at:
                    return 0.5, {"status": "no_data", "message": "No sentiment indicators found"}
                
                # Récupérer les indicateurs de sentiment depuis la base avec la dernière mise à jour
                # Chercher les données les plus récentes non-neutres (différentes de 50.0)
                indicators = db.query(SentimentIndicators)\
                    .filter(SentimentIndicators.symbol == symbol)\
                    .filter(SentimentIndicators.updated_at == max_updated_at)\
                    .filter(SentimentIndicators.sentiment_score_normalized != 50.0)\
                    .order_by(SentimentIndicators.date.desc())\
                    .limit(1)\
                    .first()
                
                # Si pas de données non-neutres, prendre les plus récentes avec la dernière mise à jour
                if not indicators:
                    indicators = db.query(SentimentIndicators)\
                        .filter(SentimentIndicators.symbol == symbol)\
                        .filter(SentimentIndicators.updated_at == max_updated_at)\
                        .order_by(SentimentIndicators.date.desc())\
                        .limit(1)\
                        .first()
            
            if not indicators:
                return 0.5, {"status": "no_data", "message": "No sentiment indicators found"}
            
            # Calculer un score basé sur les indicateurs réels
            score = 0.5  # Score neutre par défaut
            
            # Utiliser le score normalisé s'il existe
            if indicators.sentiment_score_normalized is not None:
                # Convertir de 0,100 vers 0,1
                normalized_score = float(indicators.sentiment_score_normalized) / 100.0
                score = normalized_score
            
            # Calculer la confiance basée sur la volatilité
            confidence = 0.5
            if indicators.sentiment_volatility_7d is not None:
                # Plus la volatilité est faible, plus la confiance est élevée
                volatility = abs(float(indicators.sentiment_volatility_7d))
                confidence = max(0.1, min(1.0, 1.0 - volatility))
            
            # Analyse détaillée des indicateurs
            analysis = {
                "sentiment_score": float(indicators.sentiment_score_normalized) if indicators.sentiment_score_normalized is not None else None,
                "sentiment_momentum_1d": float(indicators.sentiment_momentum_1d) if indicators.sentiment_momentum_1d is not None else None,
                "sentiment_momentum_7d": float(indicators.sentiment_momentum_7d) if indicators.sentiment_momentum_7d is not None else None,
                "sentiment_volatility_7d": float(indicators.sentiment_volatility_7d) if indicators.sentiment_volatility_7d is not None else None,
                "confidence": confidence,
                "score": score,
                "data_date": indicators.date.isoformat()
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in sentiment analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_market(self, symbol: str, db: Session, target_date: date = None) -> Tuple[float, Dict[str, Any]]:
        """Analyse de marché basée sur les vrais indicateurs"""
        try:
            if target_date:
                # Pour les opportunités historiques, récupérer les indicateurs disponibles à cette date
                indicators = db.query(MarketIndicators)\
                    .filter(MarketIndicators.symbol == symbol)\
                    .filter(MarketIndicators.analysis_date <= target_date)\
                    .order_by(MarketIndicators.analysis_date.desc())\
                    .limit(10)\
                    .all()
            else:
                # Pour les opportunités en temps réel, utiliser la logique existante
                from sqlalchemy import func
                max_created_at = db.query(func.max(MarketIndicators.created_at))\
                    .filter(MarketIndicators.symbol == symbol)\
                    .scalar()
                
                if not max_created_at:
                    return 0.5, {"status": "no_data", "message": "No market indicators found"}
                
                # Récupérer les indicateurs de marché depuis la base avec la dernière création
                indicators = db.query(MarketIndicators)\
                    .filter(MarketIndicators.symbol == symbol)\
                    .filter(MarketIndicators.created_at == max_created_at)\
                    .order_by(MarketIndicators.analysis_date.desc())\
                    .limit(10)\
                    .all()
            
            if not indicators:
                return 0.5, {"status": "no_data", "message": "No market indicators found"}
            
            # Calculer un score basé sur les indicateurs réels
            score = 0.5  # Score neutre par défaut
            market_data = {}
            signals = []
            
            # Analyser les différents types d'indicateurs
            for indicator in indicators:
                indicator_type = indicator.indicator_type
                value = float(indicator.indicator_value)
                market_data[indicator_type] = value
                
                # Analyser RSI (indicateur technique de marché)
                if indicator_type == "RSI_14D":
                    if value < 30:
                        signals.append("RSI oversold (bullish)")
                        score += 0.15
                    elif value > 70:
                        signals.append("RSI overbought (bearish)")
                        score -= 0.15
                    elif 40 <= value <= 60:
                        signals.append("RSI neutral")
                        score += 0.05
                
                # Analyser le ratio de volume
                elif indicator_type == "VOLUME_RATIO":
                    if value > 1.5:
                        signals.append("High volume activity")
                        score += 0.1
                    elif value < 0.5:
                        signals.append("Low volume activity")
                        score -= 0.05
                
                # Analyser le momentum
                elif indicator_type == "MOMENTUM_20D":
                    if value > 0.05:
                        signals.append("Strong positive momentum")
                        score += 0.1
                    elif value < -0.05:
                        signals.append("Strong negative momentum")
                        score -= 0.1
                
                # Analyser la volatilité
                elif indicator_type == "VOLATILITY_20D":
                    if value < 0.15:
                        signals.append("Low volatility (stable)")
                        score += 0.05
                    elif value > 0.3:
                        signals.append("High volatility (risky)")
                        score -= 0.1
            
            # Normaliser le score entre 0 et 1
            score = max(0.0, min(1.0, score))
            
            # Analyse détaillée des indicateurs
            analysis = {
                "indicators": market_data,
                "indicator_count": len(indicators),
                "latest_date": indicators[0].analysis_date.isoformat() if indicators else None,
                "signals": signals,
                "score": score
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in market analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_ml(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse ML simplifiée"""
        try:
            # Pour l'instant, retourner un score neutre
            # TODO: Intégrer avec le service ML existant
            score = 0.5
            analysis = {
                "ml_score": score,
                "note": "ML analysis not yet implemented"
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in ML analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_candlestick_patterns(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse des patterns de candlesticks"""
        try:
            # Récupérer la date de dernière création pour ce symbole
            from sqlalchemy import func
            max_created_at = db.query(func.max(CandlestickPatterns.created_at))\
                .filter(CandlestickPatterns.symbol == symbol)\
                .scalar()
            
            if not max_created_at:
                return 0.5, {"status": "no_data", "message": "No candlestick patterns found"}
            
            # Récupérer les patterns de candlesticks depuis la base avec la dernière création
            patterns = db.query(CandlestickPatterns)\
                .filter(CandlestickPatterns.symbol == symbol)\
                .filter(CandlestickPatterns.created_at == max_created_at)\
                .order_by(CandlestickPatterns.created_at.desc())\
                .limit(10)\
                .all()
            
            if not patterns:
                return 0.5, {"status": "no_data", "message": "No candlestick patterns found"}
            
            # Calculer le score basé sur les patterns
            bullish_patterns = sum(1 for p in patterns if p.pattern_direction == 'BULLISH')
            bearish_patterns = sum(1 for p in patterns if p.pattern_direction == 'BEARISH')
            neutral_patterns = sum(1 for p in patterns if p.pattern_direction == 'NEUTRAL')
            
            total_patterns = len(patterns)
            if total_patterns == 0:
                score = 0.5
            else:
                # Score basé sur la proportion de patterns haussiers vs baissiers
                bullish_ratio = bullish_patterns / total_patterns
                bearish_ratio = bearish_patterns / total_patterns
                score = 0.5 + (bullish_ratio - bearish_ratio) * 0.3  # Score entre 0.2 et 0.8
            
            analysis = {
                "total_patterns": total_patterns,
                "bullish_patterns": bullish_patterns,
                "bearish_patterns": bearish_patterns,
                "neutral_patterns": neutral_patterns,
                "latest_patterns": [
                    {
                        "type": p.pattern_type,
                        "direction": p.pattern_direction,
                        "strength": float(p.pattern_strength)
                    } for p in patterns[:3]
                ],
                "score": score
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in candlestick analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_garch_models(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse des modèles GARCH"""
        try:
            # Récupérer la date de dernière création pour ce symbole
            from sqlalchemy import func
            max_created_at = db.query(func.max(GARCHModels.created_at))\
                .filter(GARCHModels.symbol == symbol)\
                .scalar()
            
            if not max_created_at:
                return 0.5, {"status": "no_data", "message": "No GARCH models found"}
            
            # Récupérer les modèles GARCH depuis la base avec la dernière création
            models = db.query(GARCHModels)\
                .filter(GARCHModels.symbol == symbol)\
                .filter(GARCHModels.created_at == max_created_at)\
                .order_by(GARCHModels.created_at.desc())\
                .limit(5)\
                .all()
            
            if not models:
                return 0.5, {"status": "no_data", "message": "No GARCH models found"}
            
            # Calculer le score basé sur la volatilité prévue
            best_model = next((m for m in models if m.is_best_model), models[0])
            volatility_forecast = float(best_model.volatility_forecast)
            
            # Score basé sur la volatilité (plus la volatilité est élevée, plus le risque est élevé)
            if volatility_forecast < 0.2:
                score = 0.8  # Faible volatilité = bon score
            elif volatility_forecast < 0.4:
                score = 0.6  # Volatilité modérée
            elif volatility_forecast < 0.6:
                score = 0.4  # Volatilité élevée
            else:
                score = 0.2  # Très haute volatilité
            
            analysis = {
                "volatility_forecast": volatility_forecast,
                "var_95": float(best_model.var_95),
                "var_99": float(best_model.var_99),
                "model_type": best_model.model_type,
                "aic": float(best_model.aic) if best_model.aic else None,
                "bic": float(best_model.bic) if best_model.bic else None,
                "total_models": len(models),
                "score": score
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in GARCH analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_monte_carlo(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse des simulations Monte Carlo"""
        try:
            # Récupérer la date de dernière création pour ce symbole
            from sqlalchemy import func
            max_created_at = db.query(func.max(MonteCarloSimulations.created_at))\
                .filter(MonteCarloSimulations.symbol == symbol)\
                .scalar()
            
            if not max_created_at:
                return 0.5, {"status": "no_data", "message": "No Monte Carlo simulations found"}
            
            # Récupérer les simulations Monte Carlo depuis la base avec la dernière création
            simulations = db.query(MonteCarloSimulations)\
                .filter(MonteCarloSimulations.symbol == symbol)\
                .filter(MonteCarloSimulations.created_at == max_created_at)\
                .order_by(MonteCarloSimulations.created_at.desc())\
                .limit(1)\
                .first()
            
            if not simulations:
                return 0.5, {"status": "no_data", "message": "No Monte Carlo simulations found"}
            
            # Calculer le score basé sur la probabilité de rendement positif
            prob_positive = float(simulations.probability_positive_return)
            score = prob_positive  # Score direct basé sur la probabilité
            
            analysis = {
                "probability_positive_return": prob_positive,
                "var_95": float(simulations.var_95),
                "var_99": float(simulations.var_99),
                "expected_shortfall_95": float(simulations.expected_shortfall_95),
                "expected_shortfall_99": float(simulations.expected_shortfall_99),
                "mean_return": float(simulations.mean_return),
                "std_return": float(simulations.std_return),
                "simulations_count": simulations.simulations_count,
                "time_horizon": simulations.time_horizon,
                "score": score
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in Monte Carlo analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_markov_chains(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse des chaînes de Markov"""
        try:
            # Récupérer la date de dernière création pour ce symbole
            from sqlalchemy import func
            max_created_at = db.query(func.max(MarkovChainAnalysis.created_at))\
                .filter(MarkovChainAnalysis.symbol == symbol)\
                .scalar()
            
            if not max_created_at:
                return 0.5, {"status": "no_data", "message": "No Markov chain analysis found"}
            
            # Récupérer l'analyse Markov depuis la base avec la dernière création
            analysis = db.query(MarkovChainAnalysis)\
                .filter(MarkovChainAnalysis.symbol == symbol)\
                .filter(MarkovChainAnalysis.created_at == max_created_at)\
                .order_by(MarkovChainAnalysis.created_at.desc())\
                .first()
            
            if not analysis:
                return 0.5, {"status": "no_data", "message": "No Markov chain analysis found"}
            
            # Calculer le score basé sur l'état actuel
            current_state = analysis.current_state
            if current_state == 0:  # BULL
                score = 0.8
            elif current_state == 1:  # BEAR
                score = 0.2
            else:  # SIDEWAYS
                score = 0.5
            
            analysis_data = {
                "current_state": current_state,
                "state_probabilities": analysis.state_probabilities,
                "transition_matrix": analysis.transition_matrix,
                "stationary_probabilities": analysis.stationary_probabilities,
                "n_states": analysis.n_states,
                "score": score
            }
            
            return score, analysis_data
            
        except Exception as e:
            self.logger.error(f"Error in Markov analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_volatility(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse de la volatilité"""
        try:
            # Récupérer la date de dernière mise à jour pour ce symbole
            from sqlalchemy import func
            max_updated_at = db.query(func.max(VolatilityIndicators.updated_at))\
                .filter(VolatilityIndicators.symbol == symbol)\
                .scalar()
            
            if not max_updated_at:
                return 0.5, {"status": "no_data", "message": "No volatility indicators found"}
            
            # Récupérer les indicateurs de volatilité depuis la base avec la dernière mise à jour
            volatility = db.query(VolatilityIndicators)\
                .filter(VolatilityIndicators.symbol == symbol)\
                .filter(VolatilityIndicators.updated_at == max_updated_at)\
                .order_by(VolatilityIndicators.created_at.desc())\
                .first()
            
            if not volatility:
                return 0.5, {"status": "no_data", "message": "No volatility indicators found"}
            
            # Calculer le score basé sur le niveau de risque
            risk_level = volatility.risk_level
            if risk_level == "LOW":
                score = 0.8
            elif risk_level == "MEDIUM":
                score = 0.6
            elif risk_level == "HIGH":
                score = 0.4
            else:  # VERY_HIGH
                score = 0.2
            
            analysis = {
                "current_volatility": float(volatility.current_volatility),
                "historical_volatility": float(volatility.historical_volatility),
                "volatility_ratio": float(volatility.volatility_ratio),
                "volatility_percentile": float(volatility.volatility_percentile),
                "risk_level": risk_level,
                "vix_value": float(volatility.vix_value),
                "regime_analysis": volatility.regime_analysis,
                "score": score
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in volatility analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    def _calculate_composite_score(
        self, 
        technical_score: float, 
        sentiment_score: float, 
        market_score: float, 
        ml_score: float,
        candlestick_score: float,
        garch_score: float,
        monte_carlo_score: float,
        markov_score: float,
        volatility_score: float
    ) -> float:
        """Calcule le score composite avec méthode robuste multi-dimensionnelle"""
        
        # Scores normalisés (0-100)
        scores = {
            'technical': technical_score * 100,
            'sentiment': sentiment_score * 100,
            'market': market_score * 100,
            'ml': ml_score * 100,
            'candlestick': candlestick_score * 100,
            'garch': garch_score * 100,
            'monte_carlo': monte_carlo_score * 100,
            'markov': markov_score * 100,
            'volatility': volatility_score * 100
        }
        
        # Nouveaux poids optimisés basés sur l'analyse des corrélations avec le succès
        # Phase 1: Amélioration des seuils de décision
        base_weights = {
            'technical': 0.40,      # Corrélation la plus forte avec le succès
            'sentiment': 0.35,      # Deuxième meilleure corrélation
            'market': 0.25,         # Corrélation modérée mais importante
            'ml': 0.0,              # Désactivé temporairement pour la phase 1
            'candlestick': 0.0,     # Intégré dans l'analyse technique
            'garch': 0.0,           # Intégré dans l'analyse de marché
            'monte_carlo': 0.0,     # Intégré dans l'analyse de marché
            'markov': 0.0,          # Intégré dans l'analyse de marché
            'volatility': 0.0       # Intégré dans l'analyse de marché
        }
        
        # Phase 2: Amélioration du scoring - Formule simplifiée et optimisée
        # Utilisation directe des poids de base sans ajustements complexes
        # Seuls les scores principaux sont utilisés (les autres sont à 0)
        composite_score = (
            base_weights['technical'] * scores['technical'] +
            base_weights['sentiment'] * scores['sentiment'] +
            base_weights['market'] * scores['market']
        )
        
        # Application de règles de prudence (overrides)
        composite_score = self._apply_safety_overrides(composite_score, scores)
        
        # Normalisation finale (0-1)
        return round(composite_score / 100.0, 3)
    
    def _apply_safety_overrides(self, composite_score: float, scores: Dict[str, float]) -> float:
        """Applique des règles de prudence pour éviter les signaux extrêmes non justifiés"""
        
        # Règle 1: Si volatilité très élevée ET sentiment négatif, réduire le score
        if scores['volatility'] < 30 and scores['sentiment'] < 40:
            composite_score *= 0.8  # Réduction de 20%
        
        # Règle 2: Si Monte Carlo très négatif ET GARCH très volatil, réduire le score
        if scores['monte_carlo'] < 30 and scores['garch'] < 30:
            composite_score *= 0.85  # Réduction de 15%
        
        # Règle 3: Si technique très positive mais marché très négatif, modérer
        if scores['technical'] > 70 and scores['market'] < 30:
            composite_score = (composite_score + 50) / 2  # Moyenne avec neutre
        
        # Règle 4: Si tous les signaux sont extrêmes dans le même sens, renforcer
        positive_signals = sum(1 for s in scores.values() if s > 60)
        negative_signals = sum(1 for s in scores.values() if s < 40)
        
        if positive_signals >= 6:  # 6+ signaux positifs
            composite_score = min(95, composite_score * 1.1)  # Boost de 10%, max 95
        elif negative_signals >= 6:  # 6+ signaux négatifs
            composite_score = max(5, composite_score * 0.9)   # Réduction de 10%, min 5
        
        return composite_score
    
    def _calculate_trend_score(self, indicators, current_price: float) -> float:
        """Calcule le score de tendance (0-100)"""
        points = 0
        
        # Prix vs SMA 200 (20 points)
        if indicators.sma_200 and current_price > float(indicators.sma_200):
            points += 20
        
        # SMA 50 vs SMA 200 (15 points)
        if indicators.sma_50 and indicators.sma_200 and float(indicators.sma_50) > float(indicators.sma_200):
            points += 15
        
        # SMA 20 vs SMA 50 (10 points)
        if indicators.sma_20 and indicators.sma_50 and float(indicators.sma_20) > float(indicators.sma_50):
            points += 10
        
        # EMA 20 vs EMA 50 (5 points)
        if indicators.ema_20 and indicators.ema_50 and float(indicators.ema_20) > float(indicators.ema_50):
            points += 5
        
        # MACD positif (10 points)
        if indicators.macd and float(indicators.macd) > 0:
            points += 10
        
        # MACD histogram positif (10 points)
        if indicators.macd_histogram and float(indicators.macd_histogram) > 0:
            points += 10
        
        # Position dans les Bollinger Bands (10 points)
        if (indicators.bb_upper and indicators.bb_lower and 
            indicators.bb_middle and current_price > float(indicators.bb_middle)):
            bb_position = (current_price - float(indicators.bb_lower)) / (float(indicators.bb_upper) - float(indicators.bb_lower))
            if bb_position > 0.5:
                points += 10
        
        return min(100, points)
    
    def _calculate_momentum_score(self, indicators) -> float:
        """Calcule le score de momentum (0-100)"""
        points = 0
        
        # RSI (30 points max)
        if indicators.rsi_14:
            rsi = float(indicators.rsi_14)
            if 50 < rsi < 70:
                points += 30
            elif rsi >= 70:
                points += 20
            elif 45 < rsi <= 50:
                points += 10
        
        # MACD slope (20 points max)
        if indicators.macd_histogram:
            histogram = float(indicators.macd_histogram)
            if histogram > 0:
                points += 20
            elif abs(histogram) < 0.001:  # Proche de zéro
                points += 10
        
        # ROC (20 points max) - Approximation basée sur RSI
        if indicators.rsi_14:
            rsi = float(indicators.rsi_14)
            if rsi > 55:  # Momentum positif
                points += 20
            elif rsi > 50:
                points += 10
        
        # Stochastic (10 points max) - Approximation
        if indicators.rsi_14:
            rsi = float(indicators.rsi_14)
            if 50 < rsi < 70:  # Momentum modéré
                points += 10
        
        return min(100, points)
    
    def _calculate_obos_score(self, indicators, current_price: float) -> float:
        """Calcule le score Overbought/Oversold (0-100)"""
        points = 0
        
        # RSI (40 points max)
        if indicators.rsi_14:
            rsi = float(indicators.rsi_14)
            if rsi < 30:
                points += 40
            elif 30 <= rsi < 40:
                points += 25
            elif 40 <= rsi < 50:
                points += 10
        
        # Williams %R (30 points max)
        if indicators.williams_r:
            wr = float(indicators.williams_r)
            if wr < -80:
                points += 30
            elif -80 <= wr < -60:
                points += 15
        
        # Position Bollinger Bands (30 points max)
        if (indicators.bb_upper and indicators.bb_lower and 
            indicators.bb_middle):
            bb_position = (current_price - float(indicators.bb_lower)) / (float(indicators.bb_upper) - float(indicators.bb_lower))
            if bb_position < 0.1:
                points += 30
            elif 0.1 <= bb_position < 0.3:
                points += 15
        
        return min(100, points)
    
    def _calculate_volume_score(self, indicators, current_price_data) -> float:
        """Calcule le score de volume (0-100)"""
        points = 0
        
        # OBV direction (40 points max)
        if indicators.obv:
            # Approximation basée sur le volume actuel
            if current_price_data.volume and indicators.volume_sma_20:
                if float(current_price_data.volume) > float(indicators.volume_sma_20):
                    points += 40
            else:
                    points += 20
        
        # Volume momentum (40 points max)
        if (current_price_data.volume and indicators.volume_sma_20 and 
            indicators.bb_middle and float(current_price_data.close) > float(indicators.bb_middle)):
            volume_ratio = float(current_price_data.volume) / float(indicators.volume_sma_20)
            if volume_ratio > 1.2:
                points += 40
            elif volume_ratio > 1.1:
                points += 20
        
        # Volume vs moyenne (20 points max)
        if current_price_data.volume and indicators.volume_sma_20:
            if float(current_price_data.volume) > float(indicators.volume_sma_20):
                points += 20
        
        return min(100, points)
    
    def _calculate_volatility_structure_score(self, indicators, current_price: float) -> float:
        """Calcule le score de structure/volatilité (0-100)"""
        points = 0
        
        # Breakout (50 points max)
        if (indicators.bb_upper and indicators.bb_lower and 
            indicators.bb_middle and indicators.atr_14):
            bb_width = (float(indicators.bb_upper) - float(indicators.bb_lower)) / float(indicators.bb_middle)
            atr_ratio = float(indicators.atr_14) / float(indicators.bb_middle)
            
            # Breakout avec volatilité élevée
            if bb_width > 0.1 and current_price > float(indicators.bb_upper):
                points += 50
            elif bb_width > 0.1 and current_price > float(indicators.bb_middle):
                points += 30
        
        # Range trading (30 points max)
        if (indicators.bb_upper and indicators.bb_lower and 
            indicators.bb_middle):
            bb_width = (float(indicators.bb_upper) - float(indicators.bb_lower)) / float(indicators.bb_middle)
            bb_position = (current_price - float(indicators.bb_lower)) / (float(indicators.bb_upper) - float(indicators.bb_lower))
            
            if bb_width < 0.05 and bb_position < 0.3:  # Range étroit, position basse
                points += 30
        
        # Risk premium (pénalité)
        if indicators.atr_14 and indicators.rsi_14:
            atr_ratio = float(indicators.atr_14) / current_price
            if atr_ratio > 0.02 and float(indicators.rsi_14) > 70:  # Haute volatilité + survente
                points -= 20
        
        return max(0, min(100, points))
    
    def _calculate_trend_score_with_history(self, indicators_df, price_df) -> float:
        """Calcule le score de tendance avec historique (0-100)"""
        if len(indicators_df) == 0 or len(price_df) == 0:
            return 50.0
        
        # Utiliser les données les plus récentes
        latest_indicators = indicators_df.iloc[-1]
        latest_price = price_df.iloc[-1]
        
        points = 0
        
        # Prix vs SMA 200 (20 points)
        if pd.notna(latest_indicators['sma_200']) and latest_price['close'] > latest_indicators['sma_200']:
            points += 20
        
        # SMA 50 vs SMA 200 (15 points)
        if (pd.notna(latest_indicators['sma_50']) and pd.notna(latest_indicators['sma_200']) and 
            latest_indicators['sma_50'] > latest_indicators['sma_200']):
            points += 15
        
        # SMA 20 vs SMA 50 (10 points)
        if (pd.notna(latest_indicators['sma_20']) and pd.notna(latest_indicators['sma_50']) and 
            latest_indicators['sma_20'] > latest_indicators['sma_50']):
            points += 10
        
        # EMA 20 vs EMA 50 (5 points)
        if (pd.notna(latest_indicators['ema_20']) and pd.notna(latest_indicators['ema_50']) and 
            latest_indicators['ema_20'] > latest_indicators['ema_50']):
            points += 5
        
        # MACD positif (10 points)
        if pd.notna(latest_indicators['macd']) and latest_indicators['macd'] > 0:
            points += 10
        
        # MACD histogram positif (10 points)
        if pd.notna(latest_indicators['macd_histogram']) and latest_indicators['macd_histogram'] > 0:
            points += 10
        
        # Position dans les Bollinger Bands (10 points)
        if (pd.notna(latest_indicators['bb_upper']) and pd.notna(latest_indicators['bb_lower']) and 
            pd.notna(latest_indicators['bb_middle']) and latest_price['close'] > latest_indicators['bb_middle']):
            bb_position = (latest_price['close'] - latest_indicators['bb_lower']) / (latest_indicators['bb_upper'] - latest_indicators['bb_lower'])
            if bb_position > 0.5:
                points += 10
        
        return min(100, points)
    
    def _calculate_momentum_score_with_history(self, indicators_df) -> float:
        """Calcule le score de momentum avec historique (0-100)"""
        if len(indicators_df) == 0:
            return 50.0
        
        latest_indicators = indicators_df.iloc[-1]
        points = 0
        
        # RSI (30 points max)
        if pd.notna(latest_indicators['rsi_14']):
            rsi = latest_indicators['rsi_14']
            if 50 < rsi < 70:
                points += 30
            elif rsi >= 70:
                points += 20
            elif 45 < rsi <= 50:
                points += 10
        
        # MACD slope (20 points max) - calculer la pente
        if len(indicators_df) >= 2 and pd.notna(latest_indicators['macd_histogram']):
            prev_histogram = indicators_df.iloc[-2]['macd_histogram']
            if pd.notna(prev_histogram):
                macd_slope = latest_indicators['macd_histogram'] - prev_histogram
                if macd_slope > 0:
                    points += 20
                elif abs(macd_slope) < 0.001:
                    points += 10
        
        # ROC (20 points max) - utiliser le ROC calculé
        if pd.notna(latest_indicators['roc']):
            roc = latest_indicators['roc']
            if roc > 0.5:
                points += 20
            elif roc > 0:
                points += 10
        
        # Stochastic (10 points max)
        if (pd.notna(latest_indicators['stochastic_k']) and pd.notna(latest_indicators['stochastic_d'])):
            if latest_indicators['stochastic_k'] > latest_indicators['stochastic_d']:
                points += 10
        
        return min(100, points)
    
    def _calculate_obos_score_with_history(self, indicators_df, price_df) -> float:
        """Calcule le score Overbought/Oversold avec historique (0-100)"""
        if len(indicators_df) == 0 or len(price_df) == 0:
            return 50.0
        
        latest_indicators = indicators_df.iloc[-1]
        latest_price = price_df.iloc[-1]
        points = 0
        
        # RSI (40 points max)
        if pd.notna(latest_indicators['rsi_14']):
            rsi = latest_indicators['rsi_14']
            if rsi < 30:
                points += 40
            elif 30 <= rsi < 40:
                points += 25
            elif 40 <= rsi < 50:
                points += 10
        
        # Williams %R (30 points max)
        if pd.notna(latest_indicators['williams_r']):
            wr = latest_indicators['williams_r']
            if wr < -80:
                points += 30
            elif -80 <= wr < -60:
                points += 15
        
        # Position Bollinger Bands (30 points max)
        if (pd.notna(latest_indicators['bb_upper']) and pd.notna(latest_indicators['bb_lower']) and 
            pd.notna(latest_indicators['bb_middle'])):
            bb_position = (latest_price['close'] - latest_indicators['bb_lower']) / (latest_indicators['bb_upper'] - latest_indicators['bb_lower'])
            if bb_position < 0.1:
                points += 30
            elif 0.1 <= bb_position < 0.3:
                points += 15
        
        return min(100, points)
    
    def _calculate_volume_score_with_history(self, indicators_df, price_df) -> float:
        """Calcule le score de volume avec historique (0-100)"""
        if len(indicators_df) == 0 or len(price_df) == 0:
            return 50.0
        
        latest_indicators = indicators_df.iloc[-1]
        latest_price = price_df.iloc[-1]
        points = 0
        
        # OBV direction (40 points max)
        if pd.notna(latest_indicators['obv']) and len(indicators_df) >= 20:
            obv_sma20 = indicators_df['obv'].rolling(20, min_periods=1).mean().iloc[-1]
            if pd.notna(obv_sma20):
                if latest_indicators['obv'] > obv_sma20:
                    points += 40
                else:
                    points += 20
        
        # Volume momentum (40 points max)
        if (pd.notna(latest_price['volume']) and pd.notna(latest_indicators['volume_sma_20']) and 
            pd.notna(latest_indicators['bb_middle']) and latest_price['close'] > latest_indicators['bb_middle']):
            volume_ratio = latest_price['volume'] / latest_indicators['volume_sma_20']
            if volume_ratio > 1.2:
                points += 40
            elif volume_ratio > 1.1:
                points += 20
        
        # Volume vs moyenne (20 points max)
        if pd.notna(latest_price['volume']) and pd.notna(latest_indicators['volume_sma_20']):
            if latest_price['volume'] > latest_indicators['volume_sma_20']:
                points += 20
        
        return min(100, points)
    
    def _calculate_volatility_structure_score_with_history(self, indicators_df, price_df) -> float:
        """Calcule le score de structure/volatilité avec historique (0-100)"""
        if len(indicators_df) == 0 or len(price_df) == 0:
            return 50.0
        
        latest_indicators = indicators_df.iloc[-1]
        latest_price = price_df.iloc[-1]
        points = 0
        
        # Breakout (50 points max)
        if (pd.notna(latest_indicators['bb_upper']) and pd.notna(latest_indicators['bb_lower']) and 
            pd.notna(latest_indicators['bb_middle']) and pd.notna(latest_indicators['atr_14'])):
            bb_width = (latest_indicators['bb_upper'] - latest_indicators['bb_lower']) / latest_indicators['bb_middle']
            
            # Breakout avec volatilité élevée
            if bb_width > 0.1 and latest_price['close'] > latest_indicators['bb_upper']:
                points += 50
            elif bb_width > 0.1 and latest_price['close'] > latest_indicators['bb_middle']:
                points += 30
        
        # Range trading (30 points max)
        if (pd.notna(latest_indicators['bb_upper']) and pd.notna(latest_indicators['bb_lower']) and 
            pd.notna(latest_indicators['bb_middle'])):
            bb_width = (latest_indicators['bb_upper'] - latest_indicators['bb_lower']) / latest_indicators['bb_middle']
            bb_position = (latest_price['close'] - latest_indicators['bb_lower']) / (latest_indicators['bb_upper'] - latest_indicators['bb_lower'])
            
            if bb_width < 0.05 and bb_position < 0.3:  # Range étroit, position basse
                points += 30
        
        # Risk premium (pénalité)
        if pd.notna(latest_indicators['atr_14']) and pd.notna(latest_indicators['rsi_14']):
            atr_ratio = latest_indicators['atr_14'] / latest_price['close']
            if atr_ratio > 0.02 and latest_indicators['rsi_14'] > 70:  # Haute volatilité + survente
                points -= 20
        
        return max(0, min(100, points))
    
    def _validate_buy_signals(self, composite_score: float, technical_score: float, 
                            sentiment_score: float, market_score: float, 
                            confidence_level: float) -> Dict[str, bool]:
        """
        Valide les signaux d'achat selon les règles définies dans buy_signals_optimization.json
        Phase 1: Implémentation des règles de validation
        """
        validation_results = {
            "BUY_STRONG": False,
            "BUY_MODERATE": False,
            "BUY_WEAK": False
        }
        
        # Règles de validation pour BUY_STRONG
        if (composite_score >= 0.65 and 
            technical_score >= 0.6 and 
            sentiment_score >= 0.5 and 
            market_score >= 0.4 and 
            confidence_level >= 0.8):
            validation_results["BUY_STRONG"] = True
        
        # Règles de validation pour BUY_MODERATE
        if (composite_score >= 0.55 and 
            technical_score >= 0.5 and 
            sentiment_score >= 0.4 and 
            market_score >= 0.3 and 
            confidence_level >= 0.6):
            validation_results["BUY_MODERATE"] = True
        
        # Règles de validation pour BUY_WEAK
        if (composite_score >= 0.45 and 
            technical_score >= 0.4 and 
            sentiment_score >= 0.3 and 
            market_score >= 0.2 and 
            confidence_level >= 0.4):
            validation_results["BUY_WEAK"] = True
        
        return validation_results
    
    def _validate_technical_indicators(self, technical_indicators: Dict[str, Any]) -> Dict[str, bool]:
        """
        Valide les indicateurs techniques selon les règles définies
        Phase 2: Règles de validation technique détaillées
        """
        validation = {
            "rsi_valid": False,
            "macd_valid": False,
            "price_above_sma": False,
            "volume_above_average": False,
            "overall_valid": False
        }
        
        try:
            # RSI entre 30 et 70 (éviter les extrêmes)
            if 'rsi_14' in technical_indicators and technical_indicators['rsi_14'] is not None:
                rsi = float(technical_indicators['rsi_14'])
                validation["rsi_valid"] = 30 <= rsi <= 70
            
            # MACD au-dessus de la ligne de signal
            if 'macd' in technical_indicators and technical_indicators['macd'] is not None:
                macd = float(technical_indicators['macd'])
                if 'macd_signal' in technical_indicators and technical_indicators['macd_signal'] is not None:
                    macd_signal = float(technical_indicators['macd_signal'])
                    validation["macd_valid"] = macd > macd_signal
            
            # Prix au-dessus de la moyenne mobile 20
            if 'sma_20' in technical_indicators and technical_indicators['sma_20'] is not None:
                sma_20 = float(technical_indicators['sma_20'])
                if 'close' in technical_indicators and technical_indicators['close'] is not None:
                    close = float(technical_indicators['close'])
                    validation["price_above_sma"] = close > sma_20
            
            # Volume supérieur à la moyenne sur 20 jours
            if 'volume' in technical_indicators and technical_indicators['volume'] is not None:
                volume = float(technical_indicators['volume'])
                if 'volume_sma_20' in technical_indicators and technical_indicators['volume_sma_20'] is not None:
                    volume_sma_20 = float(technical_indicators['volume_sma_20'])
                    validation["volume_above_average"] = volume > volume_sma_20
            
            # Validation globale : au moins 3 critères sur 4
            valid_criteria = sum(1 for k, v in validation.items() if k != "overall_valid" and v)
            validation["overall_valid"] = valid_criteria >= 3
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Erreur lors de la validation technique: {e}")
        
        return validation
    
    def _validate_sentiment_indicators(self, sentiment_indicators: Dict[str, Any]) -> Dict[str, bool]:
        """
        Valide les indicateurs de sentiment selon les règles définies
        Phase 2: Règles de validation sentiment détaillées
        """
        validation = {
            "score_positive": False,
            "confidence_high": False,
            "trend_positive": False,
            "overall_valid": False
        }
        
        try:
            # Score de sentiment > 0.5
            if 'sentiment_score_normalized' in sentiment_indicators and sentiment_indicators['sentiment_score_normalized'] is not None:
                score = float(sentiment_indicators['sentiment_score_normalized'])
                validation["score_positive"] = score > 0.5
            
            # Confiance du sentiment > 0.6
            if 'confidence' in sentiment_indicators and sentiment_indicators['confidence'] is not None:
                confidence = float(sentiment_indicators['confidence'])
                validation["confidence_high"] = confidence > 0.6
            
            # Tendance du sentiment positive sur 5 jours (simplifié)
            if 'sentiment_score_normalized' in sentiment_indicators and sentiment_indicators['sentiment_score_normalized'] is not None:
                score = float(sentiment_indicators['sentiment_score_normalized'])
                validation["trend_positive"] = score > 0.5  # Simplification pour la Phase 2
            
            # Validation globale : au moins 2 critères sur 3
            valid_criteria = sum(1 for k, v in validation.items() if k != "overall_valid" and v)
            validation["overall_valid"] = valid_criteria >= 2
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Erreur lors de la validation sentiment: {e}")
        
        return validation
    
    def _validate_market_indicators(self, market_indicators: Dict[str, Any]) -> Dict[str, bool]:
        """
        Valide les indicateurs de marché selon les règles définies
        Phase 2: Règles de validation marché détaillées
        """
        validation = {
            "regime_favorable": False,
            "volatility_acceptable": False,
            "correlations_positive": False,
            "overall_valid": False
        }
        
        try:
            # Régime de marché favorable (simplifié)
            if 'market_regime' in market_indicators and market_indicators['market_regime'] is not None:
                regime = str(market_indicators['market_regime']).lower()
                validation["regime_favorable"] = regime in ['bullish', 'sideways']
            
            # Volatilité dans une fourchette acceptable
            if 'volatility_percentile' in market_indicators and market_indicators['volatility_percentile'] is not None:
                volatility = float(market_indicators['volatility_percentile'])
                validation["volatility_acceptable"] = 20 <= volatility <= 80
            
            # Corrélations sectorielles positives (simplifié)
            if 'correlation_strength' in market_indicators and market_indicators['correlation_strength'] is not None:
                correlation = str(market_indicators['correlation_strength']).lower()
                validation["correlations_positive"] = correlation in ['strong', 'medium']
            
            # Validation globale : au moins 2 critères sur 3
            valid_criteria = sum(1 for k, v in validation.items() if k != "overall_valid" and v)
            validation["overall_valid"] = valid_criteria >= 2
            
        except (ValueError, TypeError) as e:
            self.logger.warning(f"Erreur lors de la validation marché: {e}")
        
        return validation
    
    def _determine_recommendation(self, composite_score: float, technical_score: float = 0.0, 
                                sentiment_score: float = 0.0, market_score: float = 0.0, 
                                confidence_level: float = 0.0) -> Tuple[str, str]:
        """
        Détermine la recommandation et le niveau de risque avec les nouveaux seuils optimisés
        Phase 1: Amélioration des seuils de décision avec règles de validation
        """
        # Appliquer les règles de validation améliorées (Phase 2)
        validation_passed = self._validate_buy_signals(
            composite_score, technical_score, sentiment_score, market_score, confidence_level
        )
        
        # Nouveaux seuils basés sur l'analyse des performances
        if composite_score >= 0.65 and validation_passed["BUY_STRONG"]:
            return "BUY_STRONG", "LOW"
        elif composite_score >= 0.55 and validation_passed["BUY_MODERATE"]:
            return "BUY_MODERATE", "MEDIUM"
        elif composite_score >= 0.45 and validation_passed["BUY_WEAK"]:
            return "BUY_WEAK", "MEDIUM"
        elif composite_score >= 0.35:
            return "HOLD", "LOW"
        elif composite_score >= 0.25:
            return "SELL_MODERATE", "HIGH"
        else:
            return "SELL_STRONG", "VERY_HIGH"
    
    def _calculate_confidence_level(
        self, 
        technical_score: float, 
        sentiment_score: float, 
        market_score: float, 
        ml_score: float,
        candlestick_score: float,
        garch_score: float,
        monte_carlo_score: float,
        markov_score: float,
        volatility_score: float,
        technical_indicators: Dict[str, Any] = None,
        sentiment_indicators: Dict[str, Any] = None,
        market_indicators: Dict[str, Any] = None
    ) -> float:
        """
        Calcule le niveau de confiance basé sur la qualité des données et les validations
        Phase 2: Intégration des niveaux de confiance améliorés
        """
        try:
            # Confiance de base basée sur la cohérence des scores principaux
            main_scores = [technical_score, sentiment_score, market_score]
            score_std = np.std(main_scores)
            base_confidence = max(0.1, 1.0 - score_std)
            
            # Bonus pour les scores élevés (indique une forte conviction)
            high_scores = sum(1 for score in main_scores if score > 0.7)
            conviction_bonus = high_scores * 0.05
            
            # Bonus pour les scores faibles (indique une forte conviction négative)
            low_scores = sum(1 for score in main_scores if score < 0.3)
            conviction_bonus += low_scores * 0.05
            
            # Bonus pour la validation des indicateurs (Phase 2)
            validation_bonus = 0.0
            if technical_indicators:
                tech_validation = self._validate_technical_indicators(technical_indicators)
                if tech_validation["overall_valid"]:
                    validation_bonus += 0.05  # Réduit pour éviter la sur-confiance
            
            if sentiment_indicators:
                sent_validation = self._validate_sentiment_indicators(sentiment_indicators)
                if sent_validation["overall_valid"]:
                    validation_bonus += 0.05  # Réduit pour éviter la sur-confiance
            
            if market_indicators:
                market_validation = self._validate_market_indicators(market_indicators)
                if market_validation["overall_valid"]:
                    validation_bonus += 0.05  # Réduit pour éviter la sur-confiance
            
            # Confiance finale
            confidence = min(1.0, base_confidence + conviction_bonus + validation_bonus)
            
            return round(confidence, 3)
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence level: {e}")
            return 0.5
    
    def get_analysis_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """Retourne un résumé de l'analyse"""
        return {
            "symbol": result.symbol,
            "composite_score": result.composite_score,
            "confidence_level": result.confidence_level,
            "recommendation": result.recommendation,
            "risk_level": result.risk_level,
            "score_breakdown": {
                "technical": result.technical_score,
                "sentiment": result.sentiment_score,
                "market": result.market_score,
                "ml": result.ml_score,
                "candlestick": result.candlestick_score,
                "garch": result.garch_score,
                "monte_carlo": result.monte_carlo_score,
                "markov": result.markov_score,
                "volatility": result.volatility_score
            }
        }