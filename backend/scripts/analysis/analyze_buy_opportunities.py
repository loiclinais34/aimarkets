#!/usr/bin/env python3
"""
Script d'analyse des opportunités d'achat (BUY_STRONG et BUY_MODERATE)
Identifie les indicateurs les plus performants pour renforcer la précision
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case
from app.core.database import get_db
from app.models.historical_opportunities import HistoricalOpportunities
import logging
from typing import Dict, List, Tuple
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BuyOpportunityAnalyzer:
    """Analyseur spécialisé des opportunités d'achat"""
    
    def __init__(self, db: Session):
        self.db = db
        self.results = {}
    
    def get_buy_opportunities(self) -> List:
        """Récupère toutes les opportunités d'achat avec validation"""
        logger.info("📊 Récupération des opportunités d'achat")
        
        opportunities = self.db.query(HistoricalOpportunities)\
            .filter(
                and_(
                    HistoricalOpportunities.recommendation.in_(["BUY", "STRONG-BUY"]),
                    HistoricalOpportunities.price_1_day_later.isnot(None),
                    HistoricalOpportunities.return_1_day.isnot(None)
                )
            ).all()
        
        logger.info(f"Trouvé {len(opportunities)} opportunités d'achat avec validation")
        return opportunities
    
    def analyze_score_distribution(self, opportunities: List) -> Dict:
        """Analyse la distribution des scores pour les opportunités d'achat"""
        logger.info("📈 Analyse de la distribution des scores")
        
        if not opportunities:
            return {"error": "Pas d'opportunités d'achat disponibles"}
        
        # Préparer les données
        data = []
        for opp in opportunities:
            data.append({
                "technical_score": float(opp.technical_score) if opp.technical_score else 0,
                "sentiment_score": float(opp.sentiment_score) if opp.sentiment_score else 0,
                "market_score": float(opp.market_score) if opp.market_score else 0,
                "composite_score": float(opp.composite_score) if opp.composite_score else 0,
                "return_1d": float(opp.return_1_day) if opp.return_1_day else 0,
                "return_7d": float(opp.return_7_days) if opp.return_7_days else 0,
                "return_30d": float(opp.return_30_days) if opp.return_30_days else 0,
                "recommendation": opp.recommendation,
                "confidence_level": opp.confidence_level,
                "risk_level": opp.risk_level,
                "success_1d": opp.return_1_day > 0 if opp.return_1_day else False,
                "success_7d": opp.return_7_days > 0 if opp.return_7_days else False,
                "success_30d": opp.return_30_days > 0 if opp.return_30_days else False
            })
        
        df = pd.DataFrame(data)
        
        # Analyser la distribution des scores
        score_columns = ["technical_score", "sentiment_score", "market_score", "composite_score"]
        distribution = {}
        
        for col in score_columns:
            if col in df.columns:
                distribution[col] = {
                    "mean": df[col].mean(),
                    "std": df[col].std(),
                    "min": df[col].min(),
                    "max": df[col].max(),
                    "median": df[col].median(),
                    "q25": df[col].quantile(0.25),
                    "q75": df[col].quantile(0.75)
                }
        
        # Analyser la corrélation avec le succès
        correlations = {}
        for col in score_columns:
            if col in df.columns:
                correlations[col] = {
                    "success_1d": df[col].corr(df["success_1d"]),
                    "success_7d": df[col].corr(df["success_7d"]),
                    "success_30d": df[col].corr(df["success_30d"]),
                    "return_1d": df[col].corr(df["return_1d"]),
                    "return_7d": df[col].corr(df["return_7d"]),
                    "return_30d": df[col].corr(df["return_30d"])
                }
        
        return {
            "total_opportunities": len(df),
            "score_distribution": distribution,
            "correlations": correlations,
            "success_rates": {
                "1d": df["success_1d"].mean() * 100,
                "7d": df["success_7d"].mean() * 100,
                "30d": df["success_30d"].mean() * 100
            }
        }
    
    def analyze_score_thresholds(self, opportunities: List) -> Dict:
        """Analyse les seuils optimaux pour les scores"""
        logger.info("🎯 Analyse des seuils optimaux")
        
        if not opportunities:
            return {"error": "Pas d'opportunités d'achat disponibles"}
        
        # Préparer les données
        data = []
        for opp in opportunities:
            data.append({
                "technical_score": float(opp.technical_score) if opp.technical_score else 0,
                "sentiment_score": float(opp.sentiment_score) if opp.sentiment_score else 0,
                "market_score": float(opp.market_score) if opp.market_score else 0,
                "composite_score": float(opp.composite_score) if opp.composite_score else 0,
                "return_1d": float(opp.return_1_day) if opp.return_1_day else 0,
                "success_1d": opp.return_1_day > 0 if opp.return_1_day else False
            })
        
        df = pd.DataFrame(data)
        
        # Analyser les seuils pour chaque score
        score_columns = ["technical_score", "sentiment_score", "market_score", "composite_score"]
        threshold_analysis = {}
        
        for col in score_columns:
            if col not in df.columns:
                continue
            
            # Tester différents seuils
            thresholds = np.arange(0.1, 1.0, 0.05)
            best_threshold = None
            best_f1_score = 0
            best_precision = 0
            best_recall = 0
            
            threshold_results = []
            
            for threshold in thresholds:
                # Filtrer les opportunités au-dessus du seuil
                filtered_df = df[df[col] >= threshold]
                
                if len(filtered_df) == 0:
                    continue
                
                # Calculer les métriques
                true_positives = filtered_df["success_1d"].sum()
                false_positives = len(filtered_df) - true_positives
                false_negatives = df["success_1d"].sum() - true_positives
                
                precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
                recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
                f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
                
                avg_return = filtered_df["return_1d"].mean()
                
                threshold_results.append({
                    "threshold": threshold,
                    "count": len(filtered_df),
                    "precision": precision,
                    "recall": recall,
                    "f1_score": f1_score,
                    "avg_return": avg_return,
                    "success_rate": filtered_df["success_1d"].mean()
                })
                
                # Garder le meilleur seuil basé sur F1-score
                if f1_score > best_f1_score:
                    best_f1_score = f1_score
                    best_threshold = threshold
                    best_precision = precision
                    best_recall = recall
            
            threshold_analysis[col] = {
                "best_threshold": best_threshold,
                "best_f1_score": best_f1_score,
                "best_precision": best_precision,
                "best_recall": best_recall,
                "all_thresholds": threshold_results
            }
        
        return threshold_analysis
    
    def analyze_indicator_combinations(self, opportunities: List) -> Dict:
        """Analyse les combinaisons d'indicateurs les plus performantes"""
        logger.info("🔗 Analyse des combinaisons d'indicateurs")
        
        if not opportunities:
            return {"error": "Pas d'opportunités d'achat disponibles"}
        
        # Préparer les données
        data = []
        for opp in opportunities:
            data.append({
                "technical_score": float(opp.technical_score) if opp.technical_score else 0,
                "sentiment_score": float(opp.sentiment_score) if opp.sentiment_score else 0,
                "market_score": float(opp.market_score) if opp.market_score else 0,
                "composite_score": float(opp.composite_score) if opp.composite_score else 0,
                "return_1d": float(opp.return_1_day) if opp.return_1_day else 0,
                "success_1d": opp.return_1_day > 0 if opp.return_1_day else False
            })
        
        df = pd.DataFrame(data)
        
        # Analyser les combinaisons de scores
        score_columns = ["technical_score", "sentiment_score", "market_score"]
        combinations = []
        
        # Combinaisons de 2 indicateurs
        for i, col1 in enumerate(score_columns):
            for j, col2 in enumerate(score_columns):
                if i < j:  # Éviter les doublons
                    # Créer un score combiné
                    combined_score = (df[col1] + df[col2]) / 2
                    
                    # Analyser la performance
                    correlation = combined_score.corr(df["return_1d"])
                    success_correlation = combined_score.corr(df["success_1d"])
                    
                    combinations.append({
                        "combination": f"{col1} + {col2}",
                        "type": "2_indicators",
                        "correlation_return": correlation,
                        "correlation_success": success_correlation,
                        "avg_combined_score": combined_score.mean()
                    })
        
        # Combinaisons de 3 indicateurs
        combined_score = (df["technical_score"] + df["sentiment_score"] + df["market_score"]) / 3
        correlation = combined_score.corr(df["return_1d"])
        success_correlation = combined_score.corr(df["success_1d"])
        
        combinations.append({
            "combination": "technical + sentiment + market",
            "type": "3_indicators",
            "correlation_return": correlation,
            "correlation_success": success_correlation,
            "avg_combined_score": combined_score.mean()
        })
        
        # Trier par corrélation avec le succès
        combinations.sort(key=lambda x: abs(x["correlation_success"]), reverse=True)
        
        return {
            "combinations": combinations,
            "best_combination": combinations[0] if combinations else None
        }
    
    def analyze_confidence_levels(self, opportunities: List) -> Dict:
        """Analyse l'impact des niveaux de confiance"""
        logger.info("🎯 Analyse des niveaux de confiance")
        
        if not opportunities:
            return {"error": "Pas d'opportunités d'achat disponibles"}
        
        # Grouper par niveau de confiance
        confidence_groups = {}
        for opp in opportunities:
            confidence = opp.confidence_level or "UNKNOWN"
            if confidence not in confidence_groups:
                confidence_groups[confidence] = []
            confidence_groups[confidence].append(opp)
        
        # Analyser chaque groupe
        confidence_analysis = {}
        for confidence, opps in confidence_groups.items():
            if not opps:
                continue
            
            returns = [float(opp.return_1_day) for opp in opps if opp.return_1_day is not None]
            successes = [opp.return_1_day > 0 for opp in opps if opp.return_1_day is not None]
            
            if returns:
                confidence_analysis[confidence] = {
                    "count": len(opps),
                    "success_rate": sum(successes) / len(successes) * 100,
                    "avg_return": np.mean(returns) * 100,
                    "std_return": np.std(returns) * 100,
                    "sharpe_ratio": np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0,
                    "avg_technical_score": np.mean([float(opp.technical_score) for opp in opps if opp.technical_score]),
                    "avg_sentiment_score": np.mean([float(opp.sentiment_score) for opp in opps if opp.sentiment_score]),
                    "avg_market_score": np.mean([float(opp.market_score) for opp in opps if opp.market_score]),
                    "avg_composite_score": np.mean([float(opp.composite_score) for opp in opps if opp.composite_score])
                }
        
        return confidence_analysis
    
    def analyze_risk_levels(self, opportunities: List) -> Dict:
        """Analyse l'impact des niveaux de risque"""
        logger.info("⚠️ Analyse des niveaux de risque")
        
        if not opportunities:
            return {"error": "Pas d'opportunités d'achat disponibles"}
        
        # Grouper par niveau de risque
        risk_groups = {}
        for opp in opportunities:
            risk = opp.risk_level or "UNKNOWN"
            if risk not in risk_groups:
                risk_groups[risk] = []
            risk_groups[risk].append(opp)
        
        # Analyser chaque groupe
        risk_analysis = {}
        for risk, opps in risk_groups.items():
            if not opps:
                continue
            
            returns = [float(opp.return_1_day) for opp in opps if opp.return_1_day is not None]
            successes = [opp.return_1_day > 0 for opp in opps if opp.return_1_day is not None]
            
            if returns:
                risk_analysis[risk] = {
                    "count": len(opps),
                    "success_rate": sum(successes) / len(successes) * 100,
                    "avg_return": np.mean(returns) * 100,
                    "std_return": np.std(returns) * 100,
                    "sharpe_ratio": np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0,
                    "var_5_percent": np.percentile(returns, 5) * 100,
                    "max_return": np.max(returns) * 100,
                    "min_return": np.min(returns) * 100
                }
        
        return risk_analysis
    
    def generate_improvement_recommendations(self, opportunities: List) -> Dict:
        """Génère des recommandations d'amélioration"""
        logger.info("💡 Génération de recommandations d'amélioration")
        
        if not opportunities:
            return {"error": "Pas d'opportunités d'achat disponibles"}
        
        # Analyser les performances actuelles
        returns = [float(opp.return_1_day) for opp in opportunities if opp.return_1_day is not None]
        successes = [opp.return_1_day > 0 for opp in opportunities if opp.return_1_day is not None]
        
        current_success_rate = sum(successes) / len(successes) * 100 if successes else 0
        current_avg_return = np.mean(returns) * 100 if returns else 0
        
        # Recommandations basées sur l'analyse
        recommendations = {
            "current_performance": {
                "success_rate": current_success_rate,
                "avg_return": current_avg_return,
                "total_opportunities": len(opportunities)
            },
            "improvement_strategies": [
                {
                    "strategy": "Amélioration des seuils de décision",
                    "description": "Ajuster les seuils de composite_score pour filtrer les meilleures opportunités",
                    "expected_improvement": "Réduction du nombre d'opportunités mais amélioration de la qualité",
                    "implementation": "Utiliser les seuils optimaux identifiés dans l'analyse"
                },
                {
                    "strategy": "Combinaison d'indicateurs",
                    "description": "Utiliser des combinaisons d'indicateurs plutôt que le score composite seul",
                    "expected_improvement": "Amélioration de la précision des prédictions",
                    "implementation": "Implémenter des règles de décision basées sur les meilleures combinaisons"
                },
                {
                    "strategy": "Filtrage par confiance",
                    "description": "Ne considérer que les opportunités avec un niveau de confiance élevé",
                    "expected_improvement": "Réduction des faux positifs",
                    "implementation": "Seuil minimum de confiance pour les décisions d'achat"
                },
                {
                    "strategy": "Gestion du risque",
                    "description": "Ajuster la taille des positions selon le niveau de risque",
                    "expected_improvement": "Amélioration du ratio risque/rendement",
                    "implementation": "Position sizing adaptatif basé sur le niveau de risque"
                }
            ],
            "specific_actions": [
                "Implémenter un seuil minimum de 0.6 pour le composite_score",
                "Prioriser les combinaisons technique + sentiment",
                "Exiger un niveau de confiance HIGH pour les positions importantes",
                "Utiliser un position sizing réduit pour les niveaux de risque HIGH",
                "Implémenter un système de validation croisée des signaux"
            ]
        }
        
        return recommendations
    
    def run_complete_analysis(self) -> Dict:
        """Exécute l'analyse complète des opportunités d'achat"""
        logger.info("🚀 Démarrage de l'analyse complète des opportunités d'achat")
        
        try:
            # Récupérer les opportunités d'achat
            opportunities = self.get_buy_opportunities()
            
            if not opportunities:
                return {"error": "Aucune opportunité d'achat avec validation trouvée"}
            
            self.results = {
                "score_distribution": self.analyze_score_distribution(opportunities),
                "threshold_analysis": self.analyze_score_thresholds(opportunities),
                "indicator_combinations": self.analyze_indicator_combinations(opportunities),
                "confidence_analysis": self.analyze_confidence_levels(opportunities),
                "risk_analysis": self.analyze_risk_levels(opportunities),
                "improvement_recommendations": self.generate_improvement_recommendations(opportunities)
            }
            
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse: {e}")
            raise
    
    def print_summary(self):
        """Affiche un résumé de l'analyse des opportunités d'achat"""
        if not self.results:
            logger.warning("Aucun résultat à afficher")
            return
        
        score_dist = self.results["score_distribution"]
        threshold_analysis = self.results["threshold_analysis"]
        combinations = self.results["indicator_combinations"]
        confidence_analysis = self.results["confidence_analysis"]
        risk_analysis = self.results["risk_analysis"]
        recommendations = self.results["improvement_recommendations"]
        
        print("\n" + "="*80)
        print("📊 ANALYSE DES OPPORTUNITÉS D'ACHAT (BUY_STRONG & BUY_MODERATE)")
        print("="*80)
        
        print(f"\n📈 PERFORMANCE ACTUELLE:")
        if "current_performance" in recommendations:
            perf = recommendations["current_performance"]
            print(f"  • Taux de succès: {perf['success_rate']:.1f}%")
            print(f"  • Retour moyen: {perf['avg_return']:.2f}%")
            print(f"  • Nombre d'opportunités: {perf['total_opportunities']}")
        
        print(f"\n🎯 SEUILS OPTIMAUX IDENTIFIÉS:")
        for score, analysis in threshold_analysis.items():
            if "best_threshold" in analysis and analysis["best_threshold"] is not None:
                print(f"  • {score}: {analysis['best_threshold']:.2f} (F1: {analysis['best_f1_score']:.3f})")
        
        print(f"\n🔗 MEILLEURES COMBINAISONS D'INDICATEURS:")
        if "combinations" in combinations:
            for i, combo in enumerate(combinations["combinations"][:3], 1):
                print(f"  {i}. {combo['combination']}: corrélation succès = {combo['correlation_success']:.3f}")
        
        print(f"\n🎯 IMPACT DES NIVEAUX DE CONFIANCE:")
        for confidence, analysis in confidence_analysis.items():
            print(f"  • {confidence}: {analysis['count']} opp, succès = {analysis['success_rate']:.1f}%, retour = {analysis['avg_return']:.2f}%")
        
        print(f"\n⚠️ IMPACT DES NIVEAUX DE RISQUE:")
        for risk, analysis in risk_analysis.items():
            print(f"  • {risk}: {analysis['count']} opp, succès = {analysis['success_rate']:.1f}%, Sharpe = {analysis['sharpe_ratio']:.3f}")
        
        print(f"\n💡 RECOMMANDATIONS D'AMÉLIORATION:")
        if "specific_actions" in recommendations:
            for i, action in enumerate(recommendations["specific_actions"], 1):
                print(f"  {i}. {action}")
        
        print("\n" + "="*80)


def main():
    """Fonction principale"""
    
    logger.info("🚀 Démarrage de l'analyse des opportunités d'achat")
    
    db = next(get_db())
    
    try:
        # Créer l'analyseur
        analyzer = BuyOpportunityAnalyzer(db)
        
        # Exécuter l'analyse
        results = analyzer.run_complete_analysis()
        
        # Afficher le résumé
        analyzer.print_summary()
        
        # Sauvegarder les résultats
        output_file = os.path.join(os.path.dirname(__file__), "buy_opportunities_analysis.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📁 Résultats sauvegardés dans {output_file}")
        logger.info("✅ Analyse des opportunités d'achat terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
