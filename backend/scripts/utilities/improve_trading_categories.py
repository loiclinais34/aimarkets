#!/usr/bin/env python3
"""
Script d'amélioration des catégories de trading
Propose des améliorations concrètes basées sur l'analyse des performances
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


class TradingCategoryImprover:
    """Améliorateur des catégories de trading"""
    
    def __init__(self, analysis_file: str = "trading_categories_analysis.json"):
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
    
    def analyze_current_issues(self) -> Dict:
        """Analyse les problèmes actuels"""
        logger.info("🔍 Analyse des problèmes actuels")
        
        performance = self.data.get("category_performance", {})
        
        issues = []
        recommendations = []
        
        # 1. Problème de précision des signaux actifs
        buy_perf = performance.get("BUY_OPPORTUNITIES", {}).get("performance", {})
        sell_perf = performance.get("SELL_OPPORTUNITIES", {}).get("performance", {})
        
        if buy_perf.get("accuracy", 0) < 30:
            issues.append(f"Précision BUY trop faible: {buy_perf.get('accuracy', 0):.1f}%")
            recommendations.append("Améliorer la qualité des signaux d'achat")
        
        if sell_perf.get("accuracy", 0) < 30:
            issues.append(f"Précision SELL trop faible: {sell_perf.get('accuracy', 0):.1f}%")
            recommendations.append("Améliorer la qualité des signaux de vente")
        
        # 2. Problème de retours négatifs pour BUY
        if buy_perf.get("avg_return", 0) < 0:
            issues.append(f"Retours moyens négatifs pour BUY: {buy_perf.get('avg_return', 0):.2f}%")
            recommendations.append("Revoir la logique de scoring pour les opportunités d'achat")
        
        # 3. Déséquilibre des classes
        buy_count = performance.get("BUY_OPPORTUNITIES", {}).get("count", 0)
        sell_count = performance.get("SELL_OPPORTUNITIES", {}).get("count", 0)
        hold_count = performance.get("HOLD", {}).get("count", 0)
        total = buy_count + sell_count + hold_count
        
        if total > 0:
            buy_pct = (buy_count / total) * 100
            sell_pct = (sell_count / total) * 100
            hold_pct = (hold_count / total) * 100
            
            if hold_pct > 90:
                issues.append(f"Déséquilibre majeur: {hold_pct:.1f}% HOLD vs {buy_pct:.1f}% BUY + {sell_pct:.1f}% SELL")
                recommendations.append("Ajuster les seuils de décision pour équilibrer les catégories")
        
        return {
            "issues": issues,
            "recommendations": recommendations,
            "current_distribution": {
                "HOLD": hold_pct if total > 0 else 0,
                "BUY_OPPORTUNITIES": buy_pct if total > 0 else 0,
                "SELL_OPPORTUNITIES": sell_pct if total > 0 else 0
            }
        }
    
    def propose_improved_categories(self) -> Dict:
        """Propose des catégories améliorées"""
        logger.info("💡 Proposition de catégories améliorées")
        
        # Catégories améliorées basées sur l'analyse
        improved_categories = {
            "HOLD_STABLE": {
                "description": "Maintenir la position - marché stable",
                "action": "Ne rien faire",
                "context": "Portefeuille équilibré, conditions de marché stables",
                "expected_frequency": "60-70%",
                "risk_level": "LOW",
                "improvement": "Séparer HOLD stable de HOLD temporaire"
            },
            "HOLD_TEMPORARY": {
                "description": "Maintenir la position - attente de signal",
                "action": "Surveiller et attendre",
                "context": "Conditions incertaines, attente de clarification",
                "expected_frequency": "15-20%",
                "risk_level": "LOW-MEDIUM",
                "improvement": "Catégorie intermédiaire pour les cas ambigus"
            },
            "BUY_STRONG": {
                "description": "Opportunité d'achat forte",
                "action": "Acheter avec conviction",
                "context": "Signaux techniques et fondamentaux alignés",
                "expected_frequency": "8-12%",
                "risk_level": "MEDIUM",
                "improvement": "Filtrer les meilleures opportunités d'achat"
            },
            "BUY_MODERATE": {
                "description": "Opportunité d'achat modérée",
                "action": "Acheter avec prudence",
                "context": "Signaux positifs mais avec réserves",
                "expected_frequency": "5-8%",
                "risk_level": "MEDIUM-HIGH",
                "improvement": "Position sizing réduit pour ces opportunités"
            },
            "SELL_PROFIT": {
                "description": "Vente pour prise de profits",
                "action": "Vendre partiellement ou totalement",
                "context": "Objectifs de profit atteints",
                "expected_frequency": "3-5%",
                "risk_level": "LOW",
                "improvement": "Stratégie de sortie basée sur les objectifs"
            },
            "SELL_RISK": {
                "description": "Vente pour gestion du risque",
                "action": "Vendre pour limiter les pertes",
                "context": "Signaux de risque détectés",
                "expected_frequency": "2-4%",
                "risk_level": "HIGH",
                "improvement": "Stop-loss automatique basé sur les signaux"
            }
        }
        
        return improved_categories
    
    def propose_scoring_improvements(self) -> Dict:
        """Propose des améliorations du scoring"""
        logger.info("📊 Proposition d'améliorations du scoring")
        
        improvements = {
            "composite_score_thresholds": {
                "HOLD_STABLE": {
                    "min_score": 0.45,
                    "max_score": 0.55,
                    "description": "Zone de stabilité - pas d'action requise"
                },
                "HOLD_TEMPORARY": {
                    "min_score": 0.40,
                    "max_score": 0.60,
                    "description": "Zone d'incertitude - surveillance accrue"
                },
                "BUY_STRONG": {
                    "min_score": 0.70,
                    "max_score": 1.00,
                    "description": "Signaux forts - action recommandée"
                },
                "BUY_MODERATE": {
                    "min_score": 0.60,
                    "max_score": 0.70,
                    "description": "Signaux modérés - action prudente"
                },
                "SELL_PROFIT": {
                    "min_score": 0.00,
                    "max_score": 0.30,
                    "description": "Signaux de vente pour profits"
                },
                "SELL_RISK": {
                    "min_score": 0.00,
                    "max_score": 0.25,
                    "description": "Signaux de vente pour risque"
                }
            },
            "confidence_levels": {
                "HIGH": {
                    "min_confidence": 0.8,
                    "action": "Exécution immédiate",
                    "position_sizing": "Taille normale"
                },
                "MEDIUM": {
                    "min_confidence": 0.6,
                    "action": "Exécution avec prudence",
                    "position_sizing": "Taille réduite"
                },
                "LOW": {
                    "min_confidence": 0.4,
                    "action": "Surveillance uniquement",
                    "position_sizing": "Pas d'action"
                }
            },
            "risk_adjustments": {
                "volatility_factor": "Ajuster les scores selon la volatilité historique",
                "market_regime": "Modifier les seuils selon le régime de marché",
                "sector_rotation": "Considérer les rotations sectorielles",
                "macro_conditions": "Intégrer les conditions macroéconomiques"
            }
        }
        
        return improvements
    
    def propose_ml_improvements(self) -> Dict:
        """Propose des améliorations ML spécifiques"""
        logger.info("🤖 Proposition d'améliorations ML")
        
        ml_improvements = {
            "class_balancing": {
                "technique": "SMOTE + Undersampling",
                "target_distribution": {
                    "HOLD_STABLE": 60,
                    "HOLD_TEMPORARY": 15,
                    "BUY_STRONG": 10,
                    "BUY_MODERATE": 8,
                    "SELL_PROFIT": 4,
                    "SELL_RISK": 3
                },
                "description": "Équilibrer les classes pour éviter le biais HOLD"
            },
            "feature_engineering": {
                "technical_features": [
                    "Scores techniques normalisés",
                    "Momentum sur différentes périodes",
                    "Volatilité relative",
                    "Support/résistance proximity"
                ],
                "sentiment_features": [
                    "Sentiment score normalisé",
                    "Confidence du sentiment",
                    "Trend du sentiment",
                    "Volatilité du sentiment"
                ],
                "market_features": [
                    "Régime de marché",
                    "Corrélations sectorielles",
                    "Volatilité du marché",
                    "Liquidité relative"
                ],
                "temporal_features": [
                    "Jour de la semaine",
                    "Mois de l'année",
                    "Proximité des événements",
                    "Saisonnalité historique"
                ]
            },
            "model_architecture": {
                "primary_model": "XGBoost avec validation croisée temporelle",
                "secondary_model": "Neural Network pour capturer les interactions",
                "ensemble_method": "Stacking avec méta-apprentissage",
                "confidence_model": "Séparé pour estimer la fiabilité"
            },
            "training_strategy": {
                "validation": "TimeSeriesSplit pour éviter le data leakage",
                "metrics": "F1-score pondéré + Sharpe ratio",
                "regularization": "Early stopping + L1/L2 regularization",
                "hyperparameter_tuning": "Optuna avec validation croisée"
            }
        }
        
        return ml_improvements
    
    def propose_implementation_plan(self) -> Dict:
        """Propose un plan d'implémentation"""
        logger.info("📋 Proposition de plan d'implémentation")
        
        plan = {
            "phase_1": {
                "title": "Amélioration des seuils de décision",
                "duration": "1-2 semaines",
                "tasks": [
                    "Ajuster les seuils de composite_score",
                    "Implémenter les nouvelles catégories",
                    "Tester sur les données historiques",
                    "Valider les performances"
                ],
                "expected_improvement": "Réduction du déséquilibre des classes"
            },
            "phase_2": {
                "title": "Amélioration du scoring",
                "duration": "2-3 semaines",
                "tasks": [
                    "Intégrer les facteurs de risque",
                    "Améliorer la logique de confiance",
                    "Implémenter les ajustements temporels",
                    "Valider sur backtesting"
                ],
                "expected_improvement": "Amélioration de la précision des signaux"
            },
            "phase_3": {
                "title": "Implémentation ML",
                "duration": "4-6 semaines",
                "tasks": [
                    "Développer le pipeline ML",
                    "Implémenter le rééchantillonnage",
                    "Entraîner les modèles",
                    "Valider les performances"
                ],
                "expected_improvement": "Optimisation globale des performances"
            },
            "phase_4": {
                "title": "Déploiement et monitoring",
                "duration": "2-3 semaines",
                "tasks": [
                    "Déployer en production",
                    "Mettre en place le monitoring",
                    "Implémenter l'A/B testing",
                    "Optimiser en continu"
                ],
                "expected_improvement": "Stabilité et amélioration continue"
            }
        }
        
        return plan
    
    def run_complete_analysis(self) -> Dict:
        """Exécute l'analyse complète d'amélioration"""
        logger.info("🚀 Démarrage de l'analyse d'amélioration complète")
        
        try:
            self.results = {
                "current_issues": self.analyze_current_issues(),
                "improved_categories": self.propose_improved_categories(),
                "scoring_improvements": self.propose_scoring_improvements(),
                "ml_improvements": self.propose_ml_improvements(),
                "implementation_plan": self.propose_implementation_plan()
            }
            
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse: {e}")
            raise
    
    def print_summary(self):
        """Affiche un résumé des améliorations proposées"""
        if not self.results:
            logger.warning("Aucun résultat à afficher")
            return
        
        issues = self.results["current_issues"]
        categories = self.results["improved_categories"]
        plan = self.results["implementation_plan"]
        
        print("\n" + "="*80)
        print("🚀 AMÉLIORATIONS PROPOSÉES POUR LES CATÉGORIES DE TRADING")
        print("="*80)
        
        print(f"\n🔍 PROBLÈMES IDENTIFIÉS:")
        for i, issue in enumerate(issues["issues"], 1):
            print(f"  {i}. {issue}")
        
        print(f"\n💡 CATÉGORIES AMÉLIORÉES:")
        for category, info in categories.items():
            print(f"  • {category}: {info['description']}")
            print(f"    Action: {info['action']}")
            print(f"    Fréquence: {info['expected_frequency']}")
            print(f"    Amélioration: {info['improvement']}\n")
        
        print(f"📋 PLAN D'IMPLÉMENTATION:")
        for phase, details in plan.items():
            print(f"  {phase.upper()}: {details['title']}")
            print(f"    Durée: {details['duration']}")
            print(f"    Amélioration attendue: {details['expected_improvement']}")
            print(f"    Tâches principales:")
            for task in details['tasks']:
                print(f"      - {task}")
            print()
        
        print("="*80)


def main():
    """Fonction principale"""
    
    logger.info("🚀 Démarrage de l'analyse d'amélioration des catégories")
    
    try:
        # Créer l'analyseur
        improver = TradingCategoryImprover()
        
        # Exécuter l'analyse
        results = improver.run_complete_analysis()
        
        # Afficher le résumé
        improver.print_summary()
        
        # Sauvegarder les résultats
        output_file = os.path.join(os.path.dirname(__file__), "trading_categories_improvements.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📁 Améliorations sauvegardées dans {output_file}")
        logger.info("✅ Analyse d'amélioration terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
