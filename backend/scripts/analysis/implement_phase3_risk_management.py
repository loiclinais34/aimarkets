#!/usr/bin/env python3
"""
Script pour implémenter la Phase 3 : Gestion du risque
Optimise les performances en intégrant la gestion du risque dans AdvancedTradingAnalysis
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import des modèles et services
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration de la base de données
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configuration de la base de données
from app.core.config import settings
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Import des modèles
from app.models.historical_opportunities import HistoricalOpportunities
from app.models.database import HistoricalData


class Phase3RiskManager:
    """
    Gestionnaire de risque pour la Phase 3
    Implémente le position sizing, les stops et la gestion du portefeuille
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        
        # Paramètres de risque
        self.risk_parameters = {
            "max_portfolio_risk": 0.02,  # 2% de risque maximum par position
            "volatility_lookback": 20,   # Période pour calculer la volatilité
            "correlation_threshold": 0.7, # Seuil de corrélation élevée
            "max_correlation_exposure": 0.3, # Exposition max aux corrélations
            "stop_loss_multiplier": 2.0,  # Multiplicateur ATR pour stop-loss
            "take_profit_multiplier": 3.0, # Multiplicateur ATR pour take-profit
        }
    
    def calculate_position_size(
        self, 
        opportunity: Dict[str, Any], 
        portfolio_value: float = 100000,
        current_positions: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Calcule la taille de position optimale basée sur le risque
        
        Args:
            opportunity: Dictionnaire contenant les données de l'opportunité
            portfolio_value: Valeur totale du portefeuille
            current_positions: Positions actuelles du portefeuille
            
        Returns:
            Dict contenant la taille de position et les paramètres de risque
        """
        try:
            # Récupérer les données nécessaires
            symbol = opportunity.get('symbol')
            current_price = opportunity.get('price_at_generation', 0)
            composite_score = opportunity.get('composite_score', 0.5)
            confidence_level = opportunity.get('confidence_level', 0.5)
            risk_level = opportunity.get('risk_level', 'MEDIUM')
            
            if not symbol or current_price <= 0:
                return {"error": "Données d'opportunité incomplètes"}
            
            # Calculer la volatilité historique
            volatility = self._calculate_historical_volatility(symbol)
            if volatility is None:
                volatility = 0.02  # Volatilité par défaut de 2%
            
            # Calculer le risque de position
            position_risk = self._calculate_position_risk(
                composite_score, confidence_level, risk_level, volatility
            )
            
            # Calculer la taille de position
            position_size = self._calculate_optimal_position_size(
                position_risk, current_price, portfolio_value, current_positions
            )
            
            # Calculer les niveaux de stop et take-profit
            stop_loss, take_profit = self._calculate_stop_take_levels(
                current_price, volatility, opportunity
            )
            
            return {
                "position_size": position_size,
                "position_value": position_size * current_price,
                "position_risk": position_risk,
                "volatility": volatility,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_reward_ratio": (take_profit - current_price) / (current_price - stop_loss) if stop_loss < current_price else 0,
                "max_loss": (current_price - stop_loss) * position_size,
                "max_gain": (take_profit - current_price) * position_size
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul de la taille de position: {e}")
            return {"error": str(e)}
    
    def _calculate_historical_volatility(self, symbol: str) -> Optional[float]:
        """Calcule la volatilité historique sur 20 jours"""
        try:
            # Récupérer les données de prix récentes
            
            recent_data = self.db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol
            ).order_by(HistoricalData.date.desc()).limit(21).all()
            
            if len(recent_data) < 20:
                return None
            
            # Calculer les rendements quotidiens
            prices = [float(d.close) for d in reversed(recent_data)]
            returns = [np.log(prices[i] / prices[i-1]) for i in range(1, len(prices))]
            
            # Volatilité annualisée
            volatility = np.std(returns) * np.sqrt(252)
            return volatility
            
        except Exception as e:
            self.logger.error(f"Erreur calcul volatilité {symbol}: {e}")
            return None
    
    def _calculate_position_risk(
        self, 
        composite_score: float, 
        confidence_level: float, 
        risk_level: str, 
        volatility: float
    ) -> float:
        """Calcule le risque de position basé sur les scores et la volatilité"""
        
        # Score de qualité (0-1)
        quality_score = (composite_score + confidence_level) / 2
        
        # Ajustement selon le niveau de risque
        risk_multiplier = {
            'LOW': 0.5,
            'MEDIUM': 1.0,
            'HIGH': 1.5,
            'VERY_HIGH': 2.0
        }.get(risk_level, 1.0)
        
        # Risque de base ajusté par la qualité
        base_risk = self.risk_parameters["max_portfolio_risk"] * quality_score
        
        # Ajustement par la volatilité
        volatility_adjustment = min(volatility / 0.02, 2.0)  # Normaliser sur 2%
        
        # Risque final
        position_risk = base_risk * risk_multiplier / volatility_adjustment
        
        return min(position_risk, self.risk_parameters["max_portfolio_risk"])
    
    def _calculate_optimal_position_size(
        self, 
        position_risk: float, 
        current_price: float, 
        portfolio_value: float,
        current_positions: List[Dict] = None
    ) -> int:
        """Calcule la taille de position optimale"""
        
        # Taille de position basée sur le risque
        risk_based_size = (portfolio_value * position_risk) / current_price
        
        # Limiter la taille de position
        max_position_size = portfolio_value * 0.1 / current_price  # Max 10% du portefeuille
        
        # Ajuster selon les positions existantes
        if current_positions:
            total_exposure = sum(pos.get('value', 0) for pos in current_positions)
            available_capital = portfolio_value - total_exposure
            max_available_size = available_capital / current_price
            risk_based_size = min(risk_based_size, max_available_size)
        
        return int(min(risk_based_size, max_position_size))
    
    def _calculate_stop_take_levels(
        self, 
        current_price: float, 
        volatility: float, 
        opportunity: Dict[str, Any]
    ) -> tuple:
        """Calcule les niveaux de stop-loss et take-profit"""
        
        # Récupérer l'ATR si disponible
        atr = opportunity.get('atr', volatility * current_price / 100)
        
        # Calculer les niveaux
        stop_loss = current_price * (1 - self.risk_parameters["stop_loss_multiplier"] * atr / current_price)
        take_profit = current_price * (1 + self.risk_parameters["take_profit_multiplier"] * atr / current_price)
        
        return stop_loss, take_profit
    
    def calculate_portfolio_risk_metrics(
        self, 
        positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calcule les métriques de risque du portefeuille"""
        
        if not positions:
            return {"error": "Aucune position"}
        
        total_value = sum(pos.get('value', 0) for pos in positions)
        total_risk = sum(pos.get('risk', 0) for pos in positions)
        
        # Calculer la corrélation moyenne
        correlations = [pos.get('correlation', 0) for pos in positions if pos.get('correlation') is not None]
        avg_correlation = np.mean(correlations) if correlations else 0
        
        # Calculer la diversification
        diversification = 1 - avg_correlation if avg_correlation > 0 else 1
        
        return {
            "total_value": total_value,
            "total_risk": total_risk,
            "portfolio_risk": total_risk / total_value if total_value > 0 else 0,
            "avg_correlation": avg_correlation,
            "diversification": diversification,
            "position_count": len(positions),
            "risk_concentration": max(pos.get('risk', 0) for pos in positions) / total_risk if total_risk > 0 else 0
        }


class Phase3Implementation:
    """
    Implémentation de la Phase 3 dans AdvancedTradingAnalysis
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.risk_manager = Phase3RiskManager(db)
    
    def enhance_advanced_trading_analysis(self) -> Dict[str, Any]:
        """
        Améliore le service AdvancedTradingAnalysis avec la gestion du risque
        """
        try:
            # Lire le fichier actuel
            analysis_file = "/Users/loiclinais/Documents/dev/aimarkets/backend/app/services/advanced_analysis/advanced_trading_analysis.py"
            
            with open(analysis_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Ajouter les nouvelles méthodes de gestion du risque
            risk_management_methods = self._generate_risk_management_methods()
            
            # Insérer les nouvelles méthodes avant la méthode analyze_opportunity
            insertion_point = content.find("    async def analyze_opportunity")
            if insertion_point == -1:
                return {"error": "Point d'insertion non trouvé"}
            
            # Insérer les nouvelles méthodes
            new_content = content[:insertion_point] + risk_management_methods + "\n" + content[insertion_point:]
            
            # Sauvegarder le fichier modifié
            with open(analysis_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return {
                "success": True,
                "message": "Méthodes de gestion du risque ajoutées avec succès",
                "methods_added": [
                    "_calculate_position_size",
                    "_calculate_portfolio_risk",
                    "_calculate_stop_loss_levels",
                    "_calculate_take_profit_levels",
                    "_validate_risk_parameters"
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'amélioration d'AdvancedTradingAnalysis: {e}")
            return {"error": str(e)}
    
    def _generate_risk_management_methods(self) -> str:
        """Génère le code des méthodes de gestion du risque"""
        
        return '''
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
'''
    
    def test_phase3_implementation(self) -> Dict[str, Any]:
        """Teste l'implémentation de la Phase 3"""
        try:
            self.logger.info("🧪 Test de l'implémentation Phase 3")
            
            # Récupérer quelques opportunités pour tester
            opportunities = self.db.query(HistoricalOpportunities).limit(5).all()
            
            if not opportunities:
                return {"error": "Aucune opportunité trouvée pour les tests"}
            
            test_results = []
            
            for opp in opportunities:
                # Convertir en dictionnaire
                opp_data = {
                    'symbol': opp.symbol,
                    'composite_score': float(opp.composite_score),
                    'confidence_level': float(opp.confidence_level),
                    'risk_level': opp.risk_level,
                    'price_at_generation': float(opp.price_at_generation) if opp.price_at_generation else 0
                }
                
                # Tester le calcul de position
                position_result = self.risk_manager.calculate_position_size(opp_data)
                
                # Tester les niveaux de stop/take
                stop_result = self._calculate_stop_loss_levels(opp_data)
                take_result = self._calculate_take_profit_levels(opp_data)
                
                test_results.append({
                    "symbol": opp.symbol,
                    "position_calculation": position_result,
                    "stop_loss_levels": stop_result,
                    "take_profit_levels": take_result
                })
            
            return {
                "success": True,
                "test_results": test_results,
                "total_tested": len(test_results)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors du test Phase 3: {e}")
            return {"error": str(e)}
    
    def _calculate_stop_loss_levels(self, opportunity_data: Dict[str, Any]) -> Dict[str, float]:
        """Méthode de test pour les niveaux de stop-loss"""
        try:
            current_price = opportunity_data.get('price_at_generation', 0)
            atr = 0.02 * current_price  # 2% par défaut
            
            stop_loss = current_price * (1 - 2.0 * atr / current_price)
            trailing_stop = current_price * (1 - 1.5 * atr / current_price)
            
            return {
                "stop_loss": stop_loss,
                "trailing_stop": trailing_stop,
                "atr": atr
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def _calculate_take_profit_levels(self, opportunity_data: Dict[str, Any]) -> Dict[str, float]:
        """Méthode de test pour les niveaux de take-profit"""
        try:
            current_price = opportunity_data.get('price_at_generation', 0)
            composite_score = opportunity_data.get('composite_score', 0.5)
            atr = 0.02 * current_price
            
            multiplier = 2.0 + (composite_score - 0.5) * 2.0
            take_profit = current_price * (1 + multiplier * atr / current_price)
            
            return {
                "take_profit": take_profit,
                "multiplier": multiplier,
                "atr": atr
            }
            
        except Exception as e:
            return {"error": str(e)}


def main():
    """Fonction principale pour implémenter la Phase 3"""
    logger.info("🚀 Démarrage de l'implémentation Phase 3 : Gestion du risque")
    
    try:
        # Connexion à la base de données
        db = SessionLocal()
        
        # Initialiser l'implémentation
        phase3 = Phase3Implementation(db)
        
        # Améliorer AdvancedTradingAnalysis
        logger.info("📝 Amélioration d'AdvancedTradingAnalysis...")
        enhancement_result = phase3.enhance_advanced_trading_analysis()
        
        if "error" in enhancement_result:
            logger.error(f"❌ Erreur lors de l'amélioration: {enhancement_result['error']}")
            return
        
        logger.info(f"✅ {enhancement_result['message']}")
        
        # Tester l'implémentation
        logger.info("🧪 Test de l'implémentation...")
        test_result = phase3.test_phase3_implementation()
        
        if "error" in test_result:
            logger.error(f"❌ Erreur lors du test: {test_result['error']}")
            return
        
        logger.info(f"✅ Test réussi - {test_result['total_tested']} opportunités testées")
        
        # Sauvegarder les résultats
        results = {
            "enhancement_result": enhancement_result,
            "test_result": test_result,
            "implementation_timestamp": datetime.now().isoformat()
        }
        
        with open("/Users/loiclinais/Documents/dev/aimarkets/backend/scripts/phase3_implementation_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("📁 Résultats sauvegardés dans phase3_implementation_results.json")
        logger.info("✅ Implémentation Phase 3 terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'implémentation Phase 3: {e}")
        return


if __name__ == "__main__":
    main()
