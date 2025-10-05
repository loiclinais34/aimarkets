#!/usr/bin/env python3
"""
Script pour optimiser le position sizing et les seuils de take-profit
Analyse les performances des signaux d'achat et propose des optimisations
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


class PositionSizingOptimizer:
    """
    Optimiseur de position sizing et de take-profit
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def analyze_buy_signals_performance(self) -> Dict[str, Any]:
        """
        Analyse spécifiquement les performances des signaux d'achat
        """
        try:
            self.logger.info("🔍 Analyse des performances des signaux d'achat")
            
            # Récupérer tous les signaux d'achat
            buy_opportunities = self.db.query(HistoricalOpportunities).filter(
                HistoricalOpportunities.recommendation.in_(['BUY_WEAK', 'BUY_MODERATE', 'BUY_STRONG'])
            ).all()
            
            if not buy_opportunities:
                return {"error": "Aucun signal d'achat trouvé"}
            
            # Analyser par type de signal d'achat
            buy_analysis = {}
            
            for opp in buy_opportunities:
                rec_type = opp.recommendation
                if rec_type not in buy_analysis:
                    buy_analysis[rec_type] = {
                        "count": 0,
                        "returns_1d": [],
                        "returns_7d": [],
                        "returns_30d": [],
                        "composite_scores": [],
                        "confidence_levels": [],
                        "volatilities": [],
                        "prices": []
                    }
                
                buy_analysis[rec_type]["count"] += 1
                
                # Collecter les données
                if opp.return_1_day is not None:
                    buy_analysis[rec_type]["returns_1d"].append(float(opp.return_1_day))
                if opp.return_7_days is not None:
                    buy_analysis[rec_type]["returns_7d"].append(float(opp.return_7_days))
                if opp.return_30_days is not None:
                    buy_analysis[rec_type]["returns_30d"].append(float(opp.return_30_days))
                
                if opp.composite_score is not None:
                    buy_analysis[rec_type]["composite_scores"].append(float(opp.composite_score))
                if opp.confidence_level is not None:
                    buy_analysis[rec_type]["confidence_levels"].append(float(opp.confidence_level))
                if opp.price_at_generation is not None:
                    buy_analysis[rec_type]["prices"].append(float(opp.price_at_generation))
            
            # Calculer les statistiques
            for rec_type, data in buy_analysis.items():
                for period in ["1d", "7d", "30d"]:
                    returns_key = f"returns_{period}"
                    if data[returns_key]:
                        data[f"avg_return_{period}"] = np.mean(data[returns_key])
                        data[f"std_return_{period}"] = np.std(data[returns_key])
                        data[f"sharpe_{period}"] = data[f"avg_return_{period}"] / data[f"std_return_{period}"] if data[f"std_return_{period}"] > 0 else 0
                        data[f"win_rate_{period}"] = np.sum(np.array(data[returns_key]) > 0) / len(data[returns_key])
                
                # Statistiques des scores
                if data["composite_scores"]:
                    data["avg_composite_score"] = np.mean(data["composite_scores"])
                    data["std_composite_score"] = np.std(data["composite_scores"])
                
                if data["confidence_levels"]:
                    data["avg_confidence"] = np.mean(data["confidence_levels"])
                    data["std_confidence"] = np.std(data["confidence_levels"])
            
            return buy_analysis
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse des signaux d'achat: {e}")
            return {"error": str(e)}
    
    def optimize_position_sizing(self, buy_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimise le position sizing basé sur l'analyse des signaux d'achat
        """
        try:
            self.logger.info("⚖️ Optimisation du position sizing")
            
            # Paramètres d'optimisation
            base_portfolio_value = 100000
            max_position_risk = 0.02  # 2% max par position
            
            # Scénarios de position sizing à tester
            sizing_scenarios = {
                "current": {
                    "description": "Position sizing actuel",
                    "formula": "fixed_1"
                },
                "volatility_based": {
                    "description": "Basé sur la volatilité",
                    "formula": "volatility_adjusted"
                },
                "confidence_based": {
                    "description": "Basé sur la confiance",
                    "formula": "confidence_adjusted"
                },
                "composite_based": {
                    "description": "Basé sur le score composite",
                    "formula": "composite_adjusted"
                },
                "adaptive": {
                    "description": "Adaptatif (volatilité + confiance + score)",
                    "formula": "adaptive"
                }
            }
            
            scenario_results = {}
            
            for scenario_name, scenario_config in sizing_scenarios.items():
                total_return = 0
                total_risk = 0
                position_count = 0
                
                # Récupérer toutes les opportunités d'achat
                buy_opportunities = self.db.query(HistoricalOpportunities).filter(
                    HistoricalOpportunities.recommendation.in_(['BUY_WEAK', 'BUY_MODERATE', 'BUY_STRONG'])
                ).all()
                
                for opp in buy_opportunities:
                    if opp.return_1_day is None or opp.price_at_generation is None:
                        continue
                    
                    # Calculer la taille de position selon le scénario
                    position_size = self._calculate_position_size(
                        opp, scenario_config["formula"], base_portfolio_value, max_position_risk
                    )
                    
                    # Calculer le retour et le risque
                    position_return = float(opp.return_1_day) * position_size
                    position_risk = position_size * float(opp.price_at_generation) * 0.02
                    
                    total_return += position_return
                    total_risk += position_risk
                    position_count += 1
                
                scenario_results[scenario_name] = {
                    "description": scenario_config["description"],
                    "total_return": total_return,
                    "total_risk": total_risk,
                    "position_count": position_count,
                    "avg_return_per_position": total_return / position_count if position_count > 0 else 0,
                    "risk_return_ratio": total_return / total_risk if total_risk > 0 else 0,
                    "sharpe_ratio": total_return / total_risk if total_risk > 0 else 0
                }
            
            return scenario_results
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation du position sizing: {e}")
            return {"error": str(e)}
    
    def _calculate_position_size(
        self, 
        opportunity: HistoricalOpportunities, 
        formula: str, 
        portfolio_value: float, 
        max_risk: float
    ) -> int:
        """Calcule la taille de position selon la formule spécifiée"""
        
        current_price = float(opportunity.price_at_generation)
        composite_score = float(opportunity.composite_score) if opportunity.composite_score else 0.5
        confidence_level = float(opportunity.confidence_level) if opportunity.confidence_level else 0.5
        
        if formula == "fixed_1":
            return 1
        
        elif formula == "volatility_adjusted":
            # Basé sur la volatilité (inversement proportionnel)
            # Plus la volatilité est élevée, plus la position est petite
            base_size = int(portfolio_value * max_risk / current_price)
            volatility_factor = 0.5  # Facteur de volatilité (à calculer)
            return max(1, int(base_size * volatility_factor))
        
        elif formula == "confidence_adjusted":
            # Basé sur la confiance (proportionnel)
            base_size = int(portfolio_value * max_risk / current_price)
            confidence_factor = confidence_level
            return max(1, int(base_size * confidence_factor))
        
        elif formula == "composite_adjusted":
            # Basé sur le score composite (proportionnel)
            base_size = int(portfolio_value * max_risk / current_price)
            composite_factor = composite_score
            return max(1, int(base_size * composite_factor))
        
        elif formula == "adaptive":
            # Combinaison adaptative
            base_size = int(portfolio_value * max_risk / current_price)
            
            # Facteurs d'ajustement
            confidence_factor = confidence_level
            composite_factor = composite_score
            volatility_factor = 0.7  # Facteur de volatilité (à optimiser)
            
            # Formule adaptative
            adaptive_factor = (confidence_factor * 0.4 + composite_factor * 0.4 + volatility_factor * 0.2)
            
            return max(1, int(base_size * adaptive_factor))
        
        else:
            return 1
    
    def optimize_take_profit_levels(self, buy_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Optimise les seuils de take-profit basés sur l'analyse des signaux d'achat
        """
        try:
            self.logger.info("🎯 Optimisation des seuils de take-profit")
            
            # Scénarios de take-profit à tester
            take_profit_scenarios = {
                "current": {
                    "description": "Take-profit actuel (3x ATR)",
                    "multiplier": 3.0
                },
                "conservative": {
                    "description": "Conservateur (2x ATR)",
                    "multiplier": 2.0
                },
                "aggressive": {
                    "description": "Agressif (4x ATR)",
                    "multiplier": 4.0
                },
                "adaptive_score": {
                    "description": "Adaptatif basé sur le score",
                    "multiplier": "adaptive_score"
                },
                "adaptive_confidence": {
                    "description": "Adaptatif basé sur la confiance",
                    "multiplier": "adaptive_confidence"
                },
                "adaptive_combined": {
                    "description": "Adaptatif combiné",
                    "multiplier": "adaptive_combined"
                }
            }
            
            scenario_results = {}
            
            for scenario_name, scenario_config in take_profit_scenarios.items():
                total_return = 0
                take_profit_hit_count = 0
                position_count = 0
                
                # Récupérer toutes les opportunités d'achat
                buy_opportunities = self.db.query(HistoricalOpportunities).filter(
                    HistoricalOpportunities.recommendation.in_(['BUY_WEAK', 'BUY_MODERATE', 'BUY_STRONG'])
                ).all()
                
                for opp in buy_opportunities:
                    if opp.return_1_day is None or opp.price_at_generation is None:
                        continue
                    
                    current_price = float(opp.price_at_generation)
                    return_1d = float(opp.return_1_day)
                    composite_score = float(opp.composite_score) if opp.composite_score else 0.5
                    confidence_level = float(opp.confidence_level) if opp.confidence_level else 0.5
                    
                    # Calculer le seuil de take-profit
                    take_profit_threshold = self._calculate_take_profit_threshold(
                        current_price, scenario_config["multiplier"], composite_score, confidence_level
                    )
                    
                    # Vérifier si le take-profit est atteint
                    if return_1d > 0 and return_1d >= take_profit_threshold:
                        # Take-profit atteint
                        final_return = take_profit_threshold
                        take_profit_hit_count += 1
                    else:
                        # Pas de take-profit
                        final_return = return_1d
                    
                    total_return += final_return
                    position_count += 1
                
                scenario_results[scenario_name] = {
                    "description": scenario_config["description"],
                    "total_return": total_return,
                    "avg_return": total_return / position_count if position_count > 0 else 0,
                    "take_profit_hit_rate": take_profit_hit_count / position_count if position_count > 0 else 0,
                    "position_count": position_count
                }
            
            return scenario_results
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'optimisation des take-profits: {e}")
            return {"error": str(e)}
    
    def _calculate_take_profit_threshold(
        self, 
        current_price: float, 
        multiplier: Any, 
        composite_score: float, 
        confidence_level: float
    ) -> float:
        """Calcule le seuil de take-profit selon le multiplicateur spécifié"""
        
        # ATR simulé (2% du prix)
        atr = current_price * 0.02
        
        if isinstance(multiplier, (int, float)):
            return current_price * (1 + multiplier * atr / current_price)
        
        elif multiplier == "adaptive_score":
            # Adaptatif basé sur le score composite
            base_multiplier = 2.0 + (composite_score - 0.5) * 4.0  # 0x à 4x
            return current_price * (1 + base_multiplier * atr / current_price)
        
        elif multiplier == "adaptive_confidence":
            # Adaptatif basé sur la confiance
            base_multiplier = 2.0 + (confidence_level - 0.5) * 4.0  # 0x à 4x
            return current_price * (1 + base_multiplier * atr / current_price)
        
        elif multiplier == "adaptive_combined":
            # Adaptatif combiné
            score_factor = (composite_score - 0.5) * 2.0
            confidence_factor = (confidence_level - 0.5) * 2.0
            base_multiplier = 2.0 + score_factor + confidence_factor
            return current_price * (1 + base_multiplier * atr / current_price)
        
        else:
            return current_price * (1 + 3.0 * atr / current_price)
    
    def generate_optimization_recommendations(
        self, 
        buy_analysis: Dict[str, Any], 
        sizing_results: Dict[str, Any], 
        take_profit_results: Dict[str, Any]
    ) -> List[str]:
        """Génère des recommandations d'optimisation"""
        
        recommendations = []
        
        # Analyser les performances des signaux d'achat
        for rec_type, data in buy_analysis.items():
            if data["count"] > 0:
                avg_return_1d = data.get("avg_return_1d", 0)
                win_rate_1d = data.get("win_rate_1d", 0)
                avg_composite = data.get("avg_composite_score", 0)
                avg_confidence = data.get("avg_confidence", 0)
                
                if avg_return_1d > 0:
                    recommendations.append(f"✅ {rec_type}: Performance positive (Retour: {avg_return_1d:.2%}, Win rate: {win_rate_1d:.1%})")
                else:
                    recommendations.append(f"⚠️ {rec_type}: Performance négative (Retour: {avg_return_1d:.2%}, Win rate: {win_rate_1d:.1%})")
                
                recommendations.append(f"   - Score composite moyen: {avg_composite:.3f}")
                recommendations.append(f"   - Confiance moyenne: {avg_confidence:.3f}")
        
        # Analyser les résultats du position sizing
        best_sizing = max(sizing_results.items(), key=lambda x: x[1].get("risk_return_ratio", 0))
        recommendations.append(f"🏆 Meilleur position sizing: {best_sizing[0]} (Ratio: {best_sizing[1]['risk_return_ratio']:.3f})")
        
        # Analyser les résultats des take-profits
        best_take_profit = max(take_profit_results.items(), key=lambda x: x[1].get("avg_return", 0))
        recommendations.append(f"🎯 Meilleur take-profit: {best_take_profit[0]} (Retour: {best_take_profit[1]['avg_return']:.2%})")
        
        return recommendations


def main():
    """Fonction principale pour optimiser le position sizing et les take-profits"""
    logger.info("🚀 Démarrage de l'optimisation du position sizing et des take-profits")
    
    try:
        # Connexion à la base de données
        db = SessionLocal()
        
        # Initialiser l'optimiseur
        optimizer = PositionSizingOptimizer(db)
        
        # Analyser les performances des signaux d'achat
        logger.info("🔍 Analyse des signaux d'achat...")
        buy_analysis = optimizer.analyze_buy_signals_performance()
        
        if "error" in buy_analysis:
            logger.error(f"❌ Erreur lors de l'analyse: {buy_analysis['error']}")
            return
        
        # Optimiser le position sizing
        logger.info("⚖️ Optimisation du position sizing...")
        sizing_results = optimizer.optimize_position_sizing(buy_analysis)
        
        if "error" in sizing_results:
            logger.error(f"❌ Erreur lors de l'optimisation du sizing: {sizing_results['error']}")
            return
        
        # Optimiser les take-profits
        logger.info("🎯 Optimisation des take-profits...")
        take_profit_results = optimizer.optimize_take_profit_levels(buy_analysis)
        
        if "error" in take_profit_results:
            logger.error(f"❌ Erreur lors de l'optimisation des take-profits: {take_profit_results['error']}")
            return
        
        # Générer les recommandations
        logger.info("💡 Génération des recommandations...")
        recommendations = optimizer.generate_optimization_recommendations(
            buy_analysis, sizing_results, take_profit_results
        )
        
        # Afficher les résultats
        print("\n" + "="*80)
        print("⚖️ OPTIMISATION DU POSITION SIZING ET DES TAKE-PROFITS")
        print("="*80)
        
        print(f"\n🔍 ANALYSE DES SIGNAUX D'ACHAT:")
        for rec_type, data in buy_analysis.items():
            if data["count"] > 0:
                print(f"  • {rec_type}: {data['count']} opportunités")
                if "avg_return_1d" in data:
                    print(f"    - Retour moyen 1j: {data['avg_return_1d']:.2%}")
                if "win_rate_1d" in data:
                    print(f"    - Taux de réussite 1j: {data['win_rate_1d']:.1%}")
                if "sharpe_1d" in data:
                    print(f"    - Sharpe 1j: {data['sharpe_1d']:.3f}")
        
        print(f"\n⚖️ RÉSULTATS DU POSITION SIZING:")
        for scenario, results in sizing_results.items():
            print(f"  • {results['description']}:")
            print(f"    - Retour total: {results['total_return']:.2f}")
            print(f"    - Ratio risque/retour: {results['risk_return_ratio']:.3f}")
            print(f"    - Sharpe: {results['sharpe_ratio']:.3f}")
        
        print(f"\n🎯 RÉSULTATS DES TAKE-PROFITS:")
        for scenario, results in take_profit_results.items():
            print(f"  • {results['description']}:")
            print(f"    - Retour moyen: {results['avg_return']:.2%}")
            print(f"    - Taux de réussite: {results['take_profit_hit_rate']:.1%}")
        
        print(f"\n💡 RECOMMANDATIONS:")
        for rec in recommendations:
            print(f"  • {rec}")
        
        # Sauvegarder les résultats
        results = {
            "buy_analysis": buy_analysis,
            "sizing_results": sizing_results,
            "take_profit_results": take_profit_results,
            "recommendations": recommendations,
            "optimization_timestamp": datetime.now().isoformat()
        }
        
        with open("/Users/loiclinais/Documents/dev/aimarkets/backend/scripts/position_sizing_optimization_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("📁 Résultats sauvegardés dans position_sizing_optimization_results.json")
        logger.info("✅ Optimisation terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'optimisation: {e}")
        return


if __name__ == "__main__":
    main()
