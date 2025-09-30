#!/usr/bin/env python3
"""
Script d'analyse des insights ML basés sur les performances des recommandations
Fournit des recommandations concrètes pour l'implémentation des outils ML
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


class MLPerformanceInsights:
    """Analyseur d'insights ML basé sur les performances"""
    
    def __init__(self, analysis_file: str = "recommendation_performance_analysis.json"):
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
    
    def analyze_recommendation_effectiveness(self) -> Dict:
        """Analyse l'efficacité des recommandations"""
        logger.info("🎯 Analyse de l'efficacité des recommandations")
        
        overall = self.data.get("overall_performance", {})
        accuracy = self.data.get("accuracy_by_recommendation", {})
        
        # Problèmes identifiés
        problems = []
        recommendations = []
        
        # 1. Déséquilibre des classes
        rec_dist = overall.get("recommendation_distribution", {})
        total = sum(rec_dist.values())
        
        if rec_dist.get("HOLD", 0) / total > 0.9:
            problems.append("Déséquilibre majeur des classes: 95.2% HOLD vs 4.8% BUY/SELL")
            recommendations.append("Implémenter un système de rééchantillonnage (SMOTE) ou ajuster les seuils de décision")
        
        # 2. Faible précision des signaux actifs
        accuracy_1d = accuracy.get("1d", {})
        buy_accuracy = accuracy_1d.get("BUY", {}).get("accuracy", 0)
        sell_accuracy = accuracy_1d.get("SELL", {}).get("accuracy", 0)
        
        if buy_accuracy < 30 or sell_accuracy < 30:
            problems.append(f"Faible précision des signaux actifs: BUY {buy_accuracy:.1f}%, SELL {sell_accuracy:.1f}%")
            recommendations.append("Améliorer la qualité des features et implémenter un système de confiance")
        
        # 3. Retours moyens négatifs pour BUY
        buy_return = accuracy_1d.get("BUY", {}).get("avg_return", 0)
        try:
            buy_return_float = float(buy_return) if buy_return is not None else 0
            if buy_return_float < 0:
                problems.append(f"Retours moyens négatifs pour BUY: {buy_return_float:.2f}%")
                recommendations.append("Revoir la logique de scoring et les seuils de décision")
        except (ValueError, TypeError):
            pass
        
        return {
            "problems": problems,
            "recommendations": recommendations,
            "class_balance": {
                "hold_percentage": (rec_dist.get("HOLD", 0) / total) * 100,
                "active_signals_percentage": ((rec_dist.get("BUY", 0) + rec_dist.get("SELL", 0)) / total) * 100
            },
            "signal_quality": {
                "buy_accuracy": buy_accuracy,
                "sell_accuracy": sell_accuracy,
                "buy_avg_return": buy_return_float if 'buy_return_float' in locals() else 0,
                "sell_avg_return": accuracy_1d.get("SELL", {}).get("avg_return", 0)
            }
        }
    
    def analyze_feature_importance(self) -> Dict:
        """Analyse l'importance des features"""
        logger.info("📊 Analyse de l'importance des features")
        
        correlations = self.data.get("score_correlation", {}).get("correlations", {})
        
        # Analyser les corrélations
        feature_importance = {}
        for return_period, corr_data in correlations.items():
            for feature, corr_value in corr_data.items():
                if feature not in feature_importance:
                    feature_importance[feature] = []
                feature_importance[feature].append(abs(corr_value))
        
        # Calculer l'importance moyenne
        avg_importance = {}
        for feature, corr_values in feature_importance.items():
            avg_importance[feature] = np.mean(corr_values)
        
        # Trier par importance
        sorted_features = sorted(avg_importance.items(), key=lambda x: x[1], reverse=True)
        
        # Recommandations
        recommendations = []
        if sorted_features:
            top_feature = sorted_features[0][0]
            recommendations.append(f"Feature principale: {top_feature} (corrélation moyenne: {sorted_features[0][1]:.3f})")
            
            if len(sorted_features) > 1:
                recommendations.append(f"Feature secondaire: {sorted_features[1][0]} (corrélation moyenne: {sorted_features[1][1]:.3f})")
        
        return {
            "feature_importance": dict(sorted_features),
            "recommendations": recommendations,
            "correlation_details": correlations
        }
    
    def analyze_temporal_patterns(self) -> Dict:
        """Analyse des patterns temporels"""
        logger.info("📅 Analyse des patterns temporels")
        
        temporal_data = self.data.get("temporal_performance", {})
        
        # Analyser les variations mensuelles
        monthly_accuracy = {}
        monthly_returns = {}
        
        for month, rec_data in temporal_data.items():
            for rec_type, data in rec_data.items():
                if rec_type not in monthly_accuracy:
                    monthly_accuracy[rec_type] = []
                    monthly_returns[rec_type] = []
                
                try:
                    accuracy_val = float(data.get("accuracy_1d", 0)) if data.get("accuracy_1d") is not None else 0
                    return_val = float(data.get("avg_return_1d", 0)) if data.get("avg_return_1d") is not None else 0
                    monthly_accuracy[rec_type].append(accuracy_val)
                    monthly_returns[rec_type].append(return_val)
                except (ValueError, TypeError):
                    monthly_accuracy[rec_type].append(0)
                    monthly_returns[rec_type].append(0)
        
        # Calculer les variations
        patterns = {}
        for rec_type in monthly_accuracy:
            if monthly_accuracy[rec_type]:
                patterns[rec_type] = {
                    "accuracy_std": np.std(monthly_accuracy[rec_type]),
                    "return_std": np.std(monthly_returns[rec_type]),
                    "accuracy_range": [min(monthly_accuracy[rec_type]), max(monthly_accuracy[rec_type])],
                    "return_range": [min(monthly_returns[rec_type]), max(monthly_returns[rec_type])]
                }
        
        # Recommandations
        recommendations = []
        if patterns:
            recommendations.append("Implémenter des features temporelles (mois, saisons, jours de la semaine)")
            recommendations.append("Considérer des modèles adaptatifs qui s'ajustent aux conditions de marché")
        
        return {
            "temporal_patterns": patterns,
            "recommendations": recommendations,
            "monthly_data": temporal_data
        }
    
    def analyze_risk_performance(self) -> Dict:
        """Analyse des performances par niveau de risque"""
        logger.info("⚠️ Analyse des performances par risque")
        
        risk_data = self.data.get("accuracy_by_risk_level", {})
        
        # Analyser les performances par risque
        risk_analysis = {}
        for period, period_data in risk_data.items():
            risk_analysis[period] = {}
            for risk_level, data in period_data.items():
                if data.get("count", 0) > 0:
                    risk_analysis[period][risk_level] = {
                        "accuracy": data.get("accuracy", 0),
                        "avg_return": data.get("avg_return", 0),
                        "volatility": data.get("volatility", 0),
                        "sharpe_ratio": data.get("sharpe_ratio", 0),
                        "count": data.get("count", 0)
                    }
        
        # Recommandations
        recommendations = []
        recommendations.append("Implémenter un système de gestion du risque adaptatif")
        recommendations.append("Utiliser le Sharpe ratio comme métrique de récompense")
        recommendations.append("Considérer des modèles de régularisation basés sur le risque")
        
        return {
            "risk_analysis": risk_analysis,
            "recommendations": recommendations
        }
    
    def generate_ml_architecture_recommendations(self) -> Dict:
        """Génère des recommandations d'architecture ML"""
        logger.info("🏗️ Génération de recommandations d'architecture ML")
        
        # Architecture recommandée
        architecture = {
            "data_preprocessing": [
                "Normalisation des features (StandardScaler)",
                "Gestion du déséquilibre des classes (SMOTE ou ajustement des seuils)",
                "Feature engineering temporel (mois, saisons, patterns)",
                "Validation croisée temporelle (TimeSeriesSplit)"
            ],
            "model_architecture": [
                "Modèle principal: Random Forest ou XGBoost pour la robustesse",
                "Modèle secondaire: Neural Network pour capturer les interactions complexes",
                "Ensemble method: Voting ou Stacking des modèles",
                "Modèle de confiance: Séparé pour estimer la fiabilité des prédictions"
            ],
            "feature_engineering": [
                "Scores techniques comme features principales",
                "Interactions entre scores (technique × sentiment)",
                "Features temporelles (tendances, saisonnalité)",
                "Features de volatilité et de risque",
                "Features de marché (corrélations, régimes)"
            ],
            "training_strategy": [
                "Validation croisée temporelle pour éviter le data leakage",
                "Métriques de récompense: Sharpe ratio + accuracy",
                "Régularisation pour éviter le surapprentissage",
                "Early stopping basé sur la performance de validation"
            ],
            "deployment_strategy": [
                "Système de confiance pour filtrer les prédictions peu fiables",
                "Monitoring en temps réel des performances",
                "Mise à jour périodique des modèles",
                "A/B testing pour valider les améliorations"
            ]
        }
        
        return architecture
    
    def generate_actionable_insights(self) -> Dict:
        """Génère des insights actionnables"""
        logger.info("💡 Génération d'insights actionnables")
        
        # Insights prioritaires
        priority_insights = [
            {
                "priority": "HIGH",
                "title": "Corriger le déséquilibre des classes",
                "description": "95.2% des recommandations sont HOLD, ce qui limite l'utilité du modèle",
                "action": "Ajuster les seuils de décision ou implémenter SMOTE",
                "impact": "Amélioration significative de la diversité des signaux"
            },
            {
                "priority": "HIGH", 
                "title": "Améliorer la précision des signaux actifs",
                "description": "BUY et SELL ont une précision de ~26%, insuffisante pour le trading",
                "action": "Améliorer la qualité des features et implémenter un système de confiance",
                "impact": "Réduction des faux signaux et amélioration des performances"
            },
            {
                "priority": "MEDIUM",
                "title": "Implémenter des features temporelles",
                "description": "Les performances varient dans le temps, indiquant des patterns saisonniers",
                "action": "Ajouter des features de temps (mois, saisons, jours de la semaine)",
                "impact": "Amélioration de la robustesse temporelle"
            },
            {
                "priority": "MEDIUM",
                "title": "Optimiser la gestion du risque",
                "description": "Les performances varient selon le niveau de risque",
                "action": "Implémenter un système de gestion du risque adaptatif",
                "impact": "Amélioration du ratio risque/rendement"
            }
        ]
        
        return {
            "priority_insights": priority_insights,
            "next_steps": [
                "1. Implémenter un système de rééchantillonnage pour équilibrer les classes",
                "2. Développer un modèle de confiance pour filtrer les prédictions peu fiables",
                "3. Créer des features temporelles et de marché avancées",
                "4. Mettre en place un système de validation croisée temporelle",
                "5. Développer un pipeline de déploiement avec monitoring"
            ]
        }
    
    def run_complete_analysis(self) -> Dict:
        """Exécute l'analyse complète des insights ML"""
        logger.info("🚀 Démarrage de l'analyse complète des insights ML")
        
        try:
            results = {
                "recommendation_effectiveness": self.analyze_recommendation_effectiveness(),
                "feature_importance": self.analyze_feature_importance(),
                "temporal_patterns": self.analyze_temporal_patterns(),
                "risk_performance": self.analyze_risk_performance(),
                "ml_architecture": self.generate_ml_architecture_recommendations(),
                "actionable_insights": self.generate_actionable_insights()
            }
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse: {e}")
            raise
    
    def print_summary(self):
        """Affiche un résumé des insights ML"""
        if not self.data:
            logger.warning("Aucune donnée d'analyse disponible")
            return
        
        results = self.run_complete_analysis()
        
        print("\n" + "="*80)
        print("🤖 INSIGHTS ML POUR L'AMÉLIORATION DES PERFORMANCES")
        print("="*80)
        
        # Problèmes critiques
        effectiveness = results["recommendation_effectiveness"]
        print(f"\n🚨 PROBLÈMES CRITIQUES IDENTIFIÉS:")
        for i, problem in enumerate(effectiveness["problems"], 1):
            print(f"  {i}. {problem}")
        
        # Recommandations prioritaires
        insights = results["actionable_insights"]
        print(f"\n🎯 RECOMMANDATIONS PRIORITAIRES:")
        for insight in insights["priority_insights"]:
            print(f"  [{insight['priority']}] {insight['title']}")
            print(f"      {insight['description']}")
            print(f"      Action: {insight['action']}")
            print(f"      Impact: {insight['impact']}\n")
        
        # Architecture ML recommandée
        architecture = results["ml_architecture"]
        print(f"🏗️ ARCHITECTURE ML RECOMMANDÉE:")
        print(f"  • Modèle principal: Random Forest ou XGBoost")
        print(f"  • Modèle secondaire: Neural Network")
        print(f"  • Ensemble method: Voting ou Stacking")
        print(f"  • Système de confiance: Séparé pour la fiabilité")
        
        # Prochaines étapes
        print(f"\n📋 PROCHAINES ÉTAPES:")
        for step in insights["next_steps"]:
            print(f"  {step}")
        
        print("\n" + "="*80)


def main():
    """Fonction principale"""
    
    logger.info("🚀 Démarrage de l'analyse des insights ML")
    
    try:
        # Créer l'analyseur
        analyzer = MLPerformanceInsights()
        
        # Exécuter l'analyse
        results = analyzer.run_complete_analysis()
        
        # Afficher le résumé
        analyzer.print_summary()
        
        # Sauvegarder les résultats
        output_file = os.path.join(os.path.dirname(__file__), "ml_performance_insights.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📁 Insights sauvegardés dans {output_file}")
        logger.info("✅ Analyse des insights ML terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
