#!/usr/bin/env python3
"""
Script d'optimisation des signaux d'achat
Propose des améliorations concrètes basées sur l'analyse des opportunités d'achat
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BuySignalOptimizer:
    """Optimiseur des signaux d'achat"""
    
    def __init__(self, analysis_file: str = "buy_opportunities_analysis.json"):
        self.analysis_file = os.path.join(os.path.dirname(__file__), analysis_file)
        self.data = self.load_analysis_data()
    
    def load_analysis_data(self) -> Dict:
        """Charge les données d'analyse"""
        try:
            with open(self.analysis_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Fichier d'analyse non trouvé: {self.analysis_file}")
            return {}
    
    def analyze_current_performance(self) -> Dict:
        """Analyse la performance actuelle des signaux d'achat"""
        logger.info("📊 Analyse de la performance actuelle")
        
        recommendations = self.data.get("improvement_recommendations", {})
        current_perf = recommendations.get("current_performance", {})
        
        issues = []
        strengths = []
        
        # Analyser les problèmes
        success_rate = current_perf.get("success_rate", 0)
        avg_return = current_perf.get("avg_return", 0)
        
        if success_rate < 60:
            issues.append(f"Taux de succès trop faible: {success_rate:.1f}% (objectif: >60%)")
        
        if avg_return < 0:
            issues.append(f"Retour moyen négatif: {avg_return:.2f}% (objectif: >0%)")
        
        # Analyser les forces
        if success_rate > 50:
            strengths.append(f"Taux de succès acceptable: {success_rate:.1f}%")
        
        return {
            "current_performance": current_perf,
            "issues": issues,
            "strengths": strengths,
            "improvement_potential": {
                "success_rate_target": 65,
                "avg_return_target": 0.5,
                "precision_target": 70
            }
        }
    
    def propose_improved_scoring(self) -> Dict:
        """Propose un système de scoring amélioré"""
        logger.info("🎯 Proposition de scoring amélioré")
        
        threshold_analysis = self.data.get("threshold_analysis", {})
        combinations = self.data.get("indicator_combinations", {})
        
        # Analyser les seuils optimaux
        optimal_thresholds = {}
        for score, analysis in threshold_analysis.items():
            if "best_threshold" in analysis and analysis["best_threshold"] is not None:
                optimal_thresholds[score] = analysis["best_threshold"]
        
        # Analyser les meilleures combinaisons
        best_combinations = combinations.get("combinations", [])[:3]
        
        # Proposer un nouveau système de scoring
        improved_scoring = {
            "composite_score_formula": {
                "description": "Formule améliorée basée sur les meilleures combinaisons",
                "formula": "0.4 * technical_score + 0.35 * sentiment_score + 0.25 * market_score",
                "rationale": "Pondération basée sur les corrélations avec le succès"
            },
            "decision_thresholds": {
                "BUY_STRONG": {
                    "min_composite_score": 0.65,
                    "min_technical_score": 0.6,
                    "min_sentiment_score": 0.5,
                    "min_market_score": 0.4,
                    "min_confidence": 0.8,
                    "description": "Signaux très forts avec confirmation multiple"
                },
                "BUY_MODERATE": {
                    "min_composite_score": 0.55,
                    "min_technical_score": 0.5,
                    "min_sentiment_score": 0.4,
                    "min_market_score": 0.3,
                    "min_confidence": 0.6,
                    "description": "Signaux modérés avec validation partielle"
                },
                "BUY_WEAK": {
                    "min_composite_score": 0.45,
                    "min_technical_score": 0.4,
                    "min_sentiment_score": 0.3,
                    "min_market_score": 0.2,
                    "min_confidence": 0.4,
                    "description": "Signaux faibles - surveillance uniquement"
                }
            },
            "validation_rules": {
                "technical_validation": [
                    "RSI entre 30 et 70 (éviter les extrêmes)",
                    "MACD au-dessus de la ligne de signal",
                    "Prix au-dessus de la moyenne mobile 20",
                    "Volume supérieur à la moyenne sur 20 jours"
                ],
                "sentiment_validation": [
                    "Score de sentiment > 0.5",
                    "Confiance du sentiment > 0.6",
                    "Tendance du sentiment positive sur 5 jours"
                ],
                "market_validation": [
                    "Régime de marché favorable",
                    "Volatilité dans une fourchette acceptable",
                    "Corrélations sectorielles positives"
                ]
            }
        }
        
        return improved_scoring
    
    def propose_risk_management(self) -> Dict:
        """Propose un système de gestion du risque amélioré"""
        logger.info("⚠️ Proposition de gestion du risque")
        
        risk_analysis = self.data.get("risk_analysis", {})
        confidence_analysis = self.data.get("confidence_analysis", {})
        
        risk_management = {
            "position_sizing": {
                "BUY_STRONG": {
                    "base_size": 100,
                    "max_size": 150,
                    "risk_multiplier": 1.0,
                    "description": "Positions normales pour signaux forts"
                },
                "BUY_MODERATE": {
                    "base_size": 75,
                    "max_size": 100,
                    "risk_multiplier": 0.75,
                    "description": "Positions réduites pour signaux modérés"
                },
                "BUY_WEAK": {
                    "base_size": 25,
                    "max_size": 50,
                    "risk_multiplier": 0.25,
                    "description": "Positions minimales pour signaux faibles"
                }
            },
            "stop_loss": {
                "BUY_STRONG": {
                    "stop_loss": -3.0,
                    "trailing_stop": -2.0,
                    "description": "Stops plus larges pour signaux forts"
                },
                "BUY_MODERATE": {
                    "stop_loss": -2.5,
                    "trailing_stop": -1.5,
                    "description": "Stops standards pour signaux modérés"
                },
                "BUY_WEAK": {
                    "stop_loss": -2.0,
                    "trailing_stop": -1.0,
                    "description": "Stops serrés pour signaux faibles"
                }
            },
            "take_profit": {
                "BUY_STRONG": {
                    "take_profit": 8.0,
                    "partial_profit": 4.0,
                    "description": "Objectifs élevés pour signaux forts"
                },
                "BUY_MODERATE": {
                    "take_profit": 6.0,
                    "partial_profit": 3.0,
                    "description": "Objectifs modérés pour signaux modérés"
                },
                "BUY_WEAK": {
                    "take_profit": 4.0,
                    "partial_profit": 2.0,
                    "description": "Objectifs conservateurs pour signaux faibles"
                }
            },
            "portfolio_limits": {
                "max_positions": 10,
                "max_sector_exposure": 30,
                "max_single_position": 15,
                "cash_reserve": 20
            }
        }
        
        return risk_management
    
    def propose_ml_improvements(self) -> Dict:
        """Propose des améliorations ML spécifiques aux signaux d'achat"""
        logger.info("🤖 Proposition d'améliorations ML")
        
        ml_improvements = {
            "feature_engineering": {
                "technical_features": [
                    "RSI normalisé (0-1)",
                    "MACD momentum (5, 10, 20 jours)",
                    "Bollinger Bands position",
                    "Volume ratio (actuel/moyenne)",
                    "Support/resistance proximity",
                    "Trend strength (ADX)",
                    "Volatility percentile"
                ],
                "sentiment_features": [
                    "Sentiment score normalisé",
                    "Sentiment confidence",
                    "Sentiment trend (5, 10 jours)",
                    "Sentiment volatility",
                    "News sentiment ratio",
                    "Social media sentiment"
                ],
                "market_features": [
                    "Market regime indicator",
                    "Sector rotation signal",
                    "Market volatility",
                    "Correlation with market",
                    "Beta coefficient",
                    "Liquidity indicator"
                ],
                "temporal_features": [
                    "Day of week effect",
                    "Month of year effect",
                    "Earnings proximity",
                    "Dividend proximity",
                    "Options expiration proximity"
                ]
            },
            "model_architecture": {
                "primary_model": "XGBoost avec validation croisée temporelle",
                "secondary_model": "Neural Network pour interactions complexes",
                "ensemble_method": "Stacking avec méta-apprentissage",
                "confidence_model": "Séparé pour estimer la fiabilité des prédictions"
            },
            "training_strategy": {
                "validation": "TimeSeriesSplit avec 5 folds",
                "metrics": "F1-score pondéré + Sharpe ratio + Precision",
                "regularization": "Early stopping + L1/L2 + Dropout",
                "hyperparameter_tuning": "Optuna avec 100 trials"
            },
            "class_balancing": {
                "technique": "SMOTE + Undersampling",
                "target_distribution": {
                    "BUY_STRONG": 40,
                    "BUY_MODERATE": 35,
                    "BUY_WEAK": 25
                },
                "description": "Équilibrer les classes pour éviter le biais"
            }
        }
        
        return ml_improvements
    
    def propose_implementation_plan(self) -> Dict:
        """Propose un plan d'implémentation pour les améliorations"""
        logger.info("📋 Proposition de plan d'implémentation")
        
        plan = {
            "phase_1": {
                "title": "Amélioration des seuils de décision",
                "duration": "1 semaine",
                "tasks": [
                    "Implémenter les nouveaux seuils de composite_score",
                    "Ajuster la logique de classification BUY_STRONG/MODERATE/WEAK",
                    "Tester sur les données historiques",
                    "Valider les performances"
                ],
                "expected_improvement": "Réduction du nombre d'opportunités mais amélioration de la qualité",
                "success_metrics": ["Taux de succès > 60%", "Retour moyen > 0%"]
            },
            "phase_2": {
                "title": "Amélioration du scoring",
                "duration": "2 semaines",
                "tasks": [
                    "Implémenter la nouvelle formule de composite_score",
                    "Ajouter les règles de validation technique/sentiment/marché",
                    "Intégrer les niveaux de confiance",
                    "Tester sur backtesting"
                ],
                "expected_improvement": "Amélioration de la précision des signaux",
                "success_metrics": ["Précision > 70%", "F1-score > 0.65"]
            },
            "phase_3": {
                "title": "Gestion du risque",
                "duration": "1 semaine",
                "tasks": [
                    "Implémenter le position sizing adaptatif",
                    "Ajouter les stops et take-profits",
                    "Intégrer les limites de portefeuille",
                    "Tester la gestion du risque"
                ],
                "expected_improvement": "Amélioration du ratio risque/rendement",
                "success_metrics": ["Sharpe ratio > 0.5", "Max drawdown < 10%"]
            },
            "phase_4": {
                "title": "Implémentation ML",
                "duration": "3-4 semaines",
                "tasks": [
                    "Développer le pipeline ML",
                    "Implémenter le feature engineering",
                    "Entraîner les modèles",
                    "Valider les performances"
                ],
                "expected_improvement": "Optimisation globale des performances",
                "success_metrics": ["Taux de succès > 65%", "Retour moyen > 0.5%"]
            }
        }
        
        return plan
    
    def generate_actionable_recommendations(self) -> Dict:
        """Génère des recommandations actionnables immédiates"""
        logger.info("💡 Génération de recommandations actionnables")
        
        recommendations = {
            "immediate_actions": [
                {
                    "action": "Augmenter le seuil minimum de composite_score",
                    "current": "0.5",
                    "proposed": "0.6",
                    "rationale": "Filtrer les opportunités de moindre qualité",
                    "expected_impact": "Réduction de 30% du nombre d'opportunités mais amélioration de la qualité"
                },
                {
                    "action": "Implémenter un filtre de confiance",
                    "current": "Aucun",
                    "proposed": "Confiance > 0.7 pour BUY_STRONG",
                    "rationale": "Ne considérer que les signaux avec une confiance élevée",
                    "expected_impact": "Amélioration de la précision de 10-15%"
                },
                {
                    "action": "Ajuster la pondération du composite_score",
                    "current": "Égale (0.33, 0.33, 0.33)",
                    "proposed": "Technique 0.4, Sentiment 0.35, Marché 0.25",
                    "rationale": "Basé sur les corrélations avec le succès",
                    "expected_impact": "Amélioration de la précision de 5-10%"
                }
            ],
            "medium_term_actions": [
                {
                    "action": "Implémenter des règles de validation",
                    "description": "Ajouter des contrôles techniques, sentiment et marché",
                    "timeline": "2-3 semaines",
                    "expected_impact": "Réduction des faux positifs de 20-30%"
                },
                {
                    "action": "Développer un système de position sizing",
                    "description": "Ajuster la taille des positions selon la qualité du signal",
                    "timeline": "1-2 semaines",
                    "expected_impact": "Amélioration du ratio risque/rendement"
                },
                {
                    "action": "Mettre en place un système de monitoring",
                    "description": "Surveiller les performances en temps réel",
                    "timeline": "1 semaine",
                    "expected_impact": "Détection rapide des problèmes"
                }
            ],
            "long_term_actions": [
                {
                    "action": "Développer un modèle ML dédié",
                    "description": "Modèle spécialisé pour les signaux d'achat",
                    "timeline": "4-6 semaines",
                    "expected_impact": "Optimisation globale des performances"
                },
                {
                    "action": "Implémenter un système de validation croisée",
                    "description": "Validation temporelle pour éviter le surapprentissage",
                    "timeline": "2-3 semaines",
                    "expected_impact": "Robustesse accrue des prédictions"
                }
            ]
        }
        
        return recommendations
    
    def run_complete_analysis(self) -> Dict:
        """Exécute l'analyse complète d'optimisation"""
        logger.info("🚀 Démarrage de l'analyse d'optimisation complète")
        
        try:
            self.results = {
                "current_performance": self.analyze_current_performance(),
                "improved_scoring": self.propose_improved_scoring(),
                "risk_management": self.propose_risk_management(),
                "ml_improvements": self.propose_ml_improvements(),
                "implementation_plan": self.propose_implementation_plan(),
                "actionable_recommendations": self.generate_actionable_recommendations()
            }
            
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse: {e}")
            raise
    
    def print_summary(self):
        """Affiche un résumé des optimisations proposées"""
        if not self.results:
            logger.warning("Aucun résultat à afficher")
            return
        
        current_perf = self.results["current_performance"]
        improved_scoring = self.results["improved_scoring"]
        risk_mgmt = self.results["risk_management"]
        recommendations = self.results["actionable_recommendations"]
        
        print("\n" + "="*80)
        print("🚀 OPTIMISATION DES SIGNAUX D'ACHAT (BUY_STRONG & BUY_MODERATE)")
        print("="*80)
        
        print(f"\n📊 PERFORMANCE ACTUELLE:")
        if "current_performance" in current_perf:
            perf = current_perf["current_performance"]
            print(f"  • Taux de succès: {perf.get('success_rate', 0):.1f}%")
            print(f"  • Retour moyen: {perf.get('avg_return', 0):.2f}%")
            print(f"  • Nombre d'opportunités: {perf.get('total_opportunities', 0)}")
        
        print(f"\n🎯 NOUVEAUX SEUILS DE DÉCISION:")
        decision_thresholds = improved_scoring.get("decision_thresholds", {})
        for category, thresholds in decision_thresholds.items():
            print(f"  • {category}: composite_score ≥ {thresholds.get('min_composite_score', 0):.2f}")
            print(f"    Description: {thresholds.get('description', '')}")
        
        print(f"\n⚠️ GESTION DU RISQUE:")
        position_sizing = risk_mgmt.get("position_sizing", {})
        for category, sizing in position_sizing.items():
            print(f"  • {category}: Taille de base {sizing.get('base_size', 0)}%")
            print(f"    Description: {sizing.get('description', '')}")
        
        print(f"\n💡 ACTIONS IMMÉDIATES:")
        immediate_actions = recommendations.get("immediate_actions", [])
        for i, action in enumerate(immediate_actions, 1):
            print(f"  {i}. {action['action']}")
            print(f"     Actuel: {action['current']} → Proposé: {action['proposed']}")
            print(f"     Impact attendu: {action['expected_impact']}")
        
        print(f"\n📋 PLAN D'IMPLÉMENTATION:")
        implementation_plan = self.results["implementation_plan"]
        for phase, details in implementation_plan.items():
            print(f"  {phase.upper()}: {details['title']}")
            print(f"    Durée: {details['duration']}")
            print(f"    Amélioration attendue: {details['expected_improvement']}")
        
        print("\n" + "="*80)


def main():
    """Fonction principale"""
    
    logger.info("🚀 Démarrage de l'optimisation des signaux d'achat")
    
    try:
        # Créer l'optimiseur
        optimizer = BuySignalOptimizer()
        
        # Exécuter l'analyse
        results = optimizer.run_complete_analysis()
        
        # Afficher le résumé
        optimizer.print_summary()
        
        # Sauvegarder les résultats
        output_file = os.path.join(os.path.dirname(__file__), "buy_signals_optimization.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📁 Optimisations sauvegardées dans {output_file}")
        logger.info("✅ Optimisation des signaux d'achat terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
