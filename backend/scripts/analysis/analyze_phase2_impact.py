#!/usr/bin/env python3
"""
Script pour analyser l'impact des modifications Phase 1 et 2 sur les performances
Compare les nouvelles opportunités avec les anciennes pour mesurer l'amélioration
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.historical_opportunities import HistoricalOpportunities, HistoricalOpportunityValidation
import logging
from typing import Dict, List
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase2ImpactAnalyzer:
    """Analyseur d'impact des modifications Phase 1 et 2"""
    
    def __init__(self, db: Session):
        self.db = db
        self.results = {}
    
    def analyze_opportunity_distribution(self) -> Dict:
        """Analyse la distribution des opportunités générées"""
        logger.info("📊 Analyse de la distribution des opportunités")
        
        # Récupérer toutes les opportunités
        opportunities = self.db.query(HistoricalOpportunities).all()
        
        if not opportunities:
            return {"error": "Aucune opportunité trouvée"}
        
        # Analyser les recommandations
        recommendations = [op.recommendation for op in opportunities if op.recommendation]
        rec_counts = pd.Series(recommendations).value_counts()
        
        # Analyser les niveaux de risque
        risk_levels = [op.risk_level for op in opportunities if op.risk_level]
        risk_counts = pd.Series(risk_levels).value_counts()
        
        # Analyser les scores composites
        composite_scores = [float(op.composite_score) for op in opportunities if op.composite_score is not None]
        
        # Analyser les niveaux de confiance
        confidence_levels = [float(op.confidence_level) for op in opportunities if op.confidence_level is not None]
        
        return {
            "total_opportunities": len(opportunities),
            "recommendation_distribution": rec_counts.to_dict(),
            "risk_level_distribution": risk_counts.to_dict(),
            "composite_score_stats": {
                "mean": np.mean(composite_scores),
                "median": np.median(composite_scores),
                "std": np.std(composite_scores),
                "min": np.min(composite_scores),
                "max": np.max(composite_scores)
            },
            "confidence_level_stats": {
                "mean": np.mean(confidence_levels),
                "median": np.median(confidence_levels),
                "std": np.std(confidence_levels),
                "min": np.min(confidence_levels),
                "max": np.max(confidence_levels)
            }
        }
    
    def analyze_validation_performance(self) -> Dict:
        """Analyse les performances de validation"""
        logger.info("🔍 Analyse des performances de validation")
        
        # Récupérer toutes les opportunités avec leurs données de validation
        opportunities = self.db.query(HistoricalOpportunities).all()
        
        if not opportunities:
            return {"error": "Aucune opportunité trouvée"}
        
        # Analyser les performances par période
        periods = [1, 7, 30]
        period_analysis = {}
        
        for period in periods:
            # Filtrer les opportunités qui ont des données pour cette période
            if period == 1:
                period_opportunities = [o for o in opportunities if o.return_1_day is not None]
                returns = [float(o.return_1_day) for o in period_opportunities]
                correct_recommendations = [o.recommendation_correct_1_day for o in period_opportunities if o.recommendation_correct_1_day is not None]
            elif period == 7:
                period_opportunities = [o for o in opportunities if o.return_7_days is not None]
                returns = [float(o.return_7_days) for o in period_opportunities]
                correct_recommendations = [o.recommendation_correct_7_days for o in period_opportunities if o.recommendation_correct_7_days is not None]
            elif period == 30:
                period_opportunities = [o for o in opportunities if o.return_30_days is not None]
                returns = [float(o.return_30_days) for o in period_opportunities]
                correct_recommendations = [o.recommendation_correct_30_days for o in period_opportunities if o.recommendation_correct_30_days is not None]
            
            if not period_opportunities:
                continue
            
            period_analysis[period] = {
                "total_opportunities": len(period_opportunities),
                "accuracy": np.mean(correct_recommendations) if correct_recommendations else 0,
                "avg_return": np.mean(returns) if returns else 0,
                "std_return": np.std(returns) if returns else 0,
                "min_return": np.min(returns) if returns else 0,
                "max_return": np.max(returns) if returns else 0,
                "positive_returns": sum(1 for r in returns if r > 0) if returns else 0,
                "negative_returns": sum(1 for r in returns if r < 0) if returns else 0
            }
        
        return period_analysis
    
    def analyze_recommendation_accuracy(self) -> Dict:
        """Analyse la précision des recommandations par type"""
        logger.info("🎯 Analyse de la précision des recommandations")
        
        # Récupérer les opportunités avec leurs validations
        opportunities = self.db.query(HistoricalOpportunities).all()
        
        if not opportunities:
            return {"error": "Aucune opportunité trouvée"}
        
        # Grouper par type de recommandation
        recommendation_analysis = {}
        
        for op in opportunities:
            if not op.recommendation:
                continue
            
            rec_type = op.recommendation
            if rec_type not in recommendation_analysis:
                recommendation_analysis[rec_type] = {
                    "count": 0,
                    "correct_1d": [],
                    "correct_7d": [],
                    "correct_30d": [],
                    "returns_1d": [],
                    "returns_7d": [],
                    "returns_30d": []
                }
            
            recommendation_analysis[rec_type]["count"] += 1
            
            # Utiliser directement les données de l'opportunité
            if op.recommendation_correct_1_day is not None:
                recommendation_analysis[rec_type]["correct_1d"].append(op.recommendation_correct_1_day)
            if op.recommendation_correct_7_days is not None:
                recommendation_analysis[rec_type]["correct_7d"].append(op.recommendation_correct_7_days)
            if op.recommendation_correct_30_days is not None:
                recommendation_analysis[rec_type]["correct_30d"].append(op.recommendation_correct_30_days)
            
            if op.return_1_day is not None:
                recommendation_analysis[rec_type]["returns_1d"].append(float(op.return_1_day))
            if op.return_7_days is not None:
                recommendation_analysis[rec_type]["returns_7d"].append(float(op.return_7_days))
            if op.return_30_days is not None:
                recommendation_analysis[rec_type]["returns_30d"].append(float(op.return_30_days))
        
        # Calculer les statistiques
        for rec_type, data in recommendation_analysis.items():
            data["accuracy_1d"] = np.mean(data["correct_1d"]) if data["correct_1d"] else 0
            data["accuracy_7d"] = np.mean(data["correct_7d"]) if data["correct_7d"] else 0
            data["accuracy_30d"] = np.mean(data["correct_30d"]) if data["correct_30d"] else 0
            data["avg_return_1d"] = np.mean(data["returns_1d"]) if data["returns_1d"] else 0
            data["avg_return_7d"] = np.mean(data["returns_7d"]) if data["returns_7d"] else 0
            data["avg_return_30d"] = np.mean(data["returns_30d"]) if data["returns_30d"] else 0
            data["std_return_1d"] = np.std(data["returns_1d"]) if data["returns_1d"] else 0
            data["std_return_7d"] = np.std(data["returns_7d"]) if data["returns_7d"] else 0
            data["std_return_30d"] = np.std(data["returns_30d"]) if data["returns_30d"] else 0
        
        return recommendation_analysis
    
    def analyze_confidence_impact(self) -> Dict:
        """Analyse l'impact des niveaux de confiance sur les performances"""
        logger.info("🎯 Analyse de l'impact de la confiance")
        
        # Récupérer les opportunités avec leurs validations
        opportunities = self.db.query(HistoricalOpportunities).all()
        
        if not opportunities:
            return {"error": "Aucune opportunité trouvée"}
        
        # Grouper par niveau de confiance
        confidence_analysis = {}
        
        for op in opportunities:
            if not op.confidence_level:
                continue
            
            conf_level = op.confidence_level
            if conf_level not in confidence_analysis:
                confidence_analysis[conf_level] = {
                    "count": 0,
                    "correct_1d": [],
                    "correct_7d": [],
                    "correct_30d": [],
                    "returns_1d": [],
                    "returns_7d": [],
                    "returns_30d": []
                }
            
            confidence_analysis[conf_level]["count"] += 1
            
            # Utiliser directement les données de l'opportunité
            if op.recommendation_correct_1_day is not None:
                confidence_analysis[conf_level]["correct_1d"].append(op.recommendation_correct_1_day)
            if op.recommendation_correct_7_days is not None:
                confidence_analysis[conf_level]["correct_7d"].append(op.recommendation_correct_7_days)
            if op.recommendation_correct_30_days is not None:
                confidence_analysis[conf_level]["correct_30d"].append(op.recommendation_correct_30_days)
            
            if op.return_1_day is not None:
                confidence_analysis[conf_level]["returns_1d"].append(float(op.return_1_day))
            if op.return_7_days is not None:
                confidence_analysis[conf_level]["returns_7d"].append(float(op.return_7_days))
            if op.return_30_days is not None:
                confidence_analysis[conf_level]["returns_30d"].append(float(op.return_30_days))
        
        # Calculer les statistiques
        for conf_level, data in confidence_analysis.items():
            data["accuracy_1d"] = np.mean(data["correct_1d"]) if data["correct_1d"] else 0
            data["accuracy_7d"] = np.mean(data["correct_7d"]) if data["correct_7d"] else 0
            data["accuracy_30d"] = np.mean(data["correct_30d"]) if data["correct_30d"] else 0
            data["avg_return_1d"] = np.mean(data["returns_1d"]) if data["returns_1d"] else 0
            data["avg_return_7d"] = np.mean(data["returns_7d"]) if data["returns_7d"] else 0
            data["avg_return_30d"] = np.mean(data["returns_30d"]) if data["returns_30d"] else 0
            data["std_return_1d"] = np.std(data["returns_1d"]) if data["returns_1d"] else 0
            data["std_return_7d"] = np.std(data["returns_7d"]) if data["returns_7d"] else 0
            data["std_return_30d"] = np.std(data["returns_30d"]) if data["returns_30d"] else 0
        
        return confidence_analysis
    
    def generate_insights(self) -> Dict:
        """Génère des insights sur l'impact des modifications"""
        logger.info("💡 Génération d'insights")
        
        insights = {
            "phase_2_improvements": [],
            "key_findings": [],
            "recommendations": []
        }
        
        # Analyser la distribution des opportunités
        distribution = self.analyze_opportunity_distribution()
        if "error" not in distribution:
            # Insight sur la distribution des recommandations
            rec_dist = distribution["recommendation_distribution"]
            total = sum(rec_dist.values())
            
            if "BUY_WEAK" in rec_dist and "BUY_MODERATE" in rec_dist:
                buy_opportunities = rec_dist.get("BUY_WEAK", 0) + rec_dist.get("BUY_MODERATE", 0)
                buy_percentage = (buy_opportunities / total) * 100
                insights["key_findings"].append(f"Phase 2 génère {buy_percentage:.1f}% d'opportunités d'achat (BUY_WEAK + BUY_MODERATE)")
            
            # Insight sur les niveaux de confiance
            conf_stats = distribution["confidence_level_stats"]
            if conf_stats["mean"] > 0.8:
                insights["key_findings"].append(f"Niveau de confiance moyen élevé: {conf_stats['mean']:.3f}")
        
        # Analyser les performances de validation
        validation_perf = self.analyze_validation_performance()
        if "error" not in validation_perf:
            for period, data in validation_perf.items():
                if data["accuracy"] > 0:
                    insights["key_findings"].append(f"Précision {period}j: {data['accuracy']:.1%}")
        
        # Analyser la précision des recommandations
        rec_accuracy = self.analyze_recommendation_accuracy()
        if "error" not in rec_accuracy:
            for rec_type, data in rec_accuracy.items():
                if data.get("accuracy_1d", 0) > 0:
                    insights["key_findings"].append(f"Précision {rec_type}: {data['accuracy_1d']:.1%}")
        
        # Recommandations
        insights["recommendations"].extend([
            "Continuer à affiner les seuils de validation pour améliorer la précision",
            "Implémenter la Phase 3 (gestion du risque) pour optimiser les performances",
            "Surveiller les performances des signaux BUY_WEAK et BUY_MODERATE",
            "Analyser l'impact des niveaux de confiance sur les décisions de trading"
        ])
        
        return insights
    
    def run_complete_analysis(self) -> Dict:
        """Exécute l'analyse complète de l'impact Phase 2"""
        logger.info("🚀 Démarrage de l'analyse complète de l'impact Phase 2")
        
        try:
            self.results = {
                "opportunity_distribution": self.analyze_opportunity_distribution(),
                "validation_performance": self.analyze_validation_performance(),
                "recommendation_accuracy": self.analyze_recommendation_accuracy(),
                "confidence_impact": self.analyze_confidence_impact(),
                "insights": self.generate_insights(),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse: {e}")
            return {
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def print_summary(self, results: Dict):
        """Affiche un résumé de l'analyse"""
        if "error" in results:
            logger.error(f"❌ Erreur dans l'analyse: {results['error']}")
            return
        
        distribution = results["opportunity_distribution"]
        validation = results["validation_performance"]
        rec_accuracy = results["recommendation_accuracy"]
        confidence = results["confidence_impact"]
        insights = results["insights"]
        
        print("\n" + "="*80)
        print("📊 ANALYSE DE L'IMPACT PHASE 2 - AMÉLIORATION DU SCORING")
        print("="*80)
        
        print(f"\n📈 DISTRIBUTION DES OPPORTUNITÉS:")
        if "error" not in distribution:
            print(f"  • Total: {distribution['total_opportunities']}")
            print(f"  • Recommandations:")
            for rec, count in distribution["recommendation_distribution"].items():
                percentage = (count / distribution["total_opportunities"]) * 100
                print(f"    - {rec}: {count} ({percentage:.1f}%)")
            print(f"  • Score composite moyen: {distribution['composite_score_stats']['mean']:.3f}")
            print(f"  • Confiance moyenne: {distribution['confidence_level_stats']['mean']:.3f}")
        
        print(f"\n🔍 PERFORMANCES DE VALIDATION:")
        if "error" not in validation:
            for period, data in validation.items():
                print(f"  • Période {period} jours:")
                print(f"    - Précision: {data['accuracy']:.1%}")
                print(f"    - Retour moyen: {data['avg_return']:.2%}")
                print(f"    - Volatilité: {data['std_return']:.2%}")
        
        print(f"\n🎯 PRÉCISION PAR TYPE DE RECOMMANDATION:")
        if "error" not in rec_accuracy:
            for rec_type, data in rec_accuracy.items():
                if data["count"] > 0:
                    print(f"  • {rec_type}: {data['count']} opportunités")
                    print(f"    - Précision 1j: {data.get('accuracy_1d', 0):.1%}")
                    print(f"    - Retour moyen 1j: {data.get('avg_return_1d', 0):.2%}")
        
        print(f"\n💡 INSIGHTS CLÉS:")
        for finding in insights["key_findings"]:
            print(f"  • {finding}")
        
        print(f"\n📋 RECOMMANDATIONS:")
        for rec in insights["recommendations"]:
            print(f"  • {rec}")
        
        print("\n" + "="*80)


def main():
    """Fonction principale"""
    
    logger.info("🚀 Démarrage de l'analyse de l'impact Phase 2")
    
    db = next(get_db())
    
    try:
        # Créer l'analyseur
        analyzer = Phase2ImpactAnalyzer(db)
        
        # Exécuter l'analyse complète
        results = analyzer.run_complete_analysis()
        
        # Afficher le résumé
        analyzer.print_summary(results)
        
        # Sauvegarder les résultats
        output_file = os.path.join(os.path.dirname(__file__), "phase2_impact_analysis.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📁 Résultats d'analyse sauvegardés dans {output_file}")
        logger.info("✅ Analyse de l'impact Phase 2 terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
