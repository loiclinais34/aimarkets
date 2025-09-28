#!/usr/bin/env python3
"""
Script pour tester les performances des signaux d'achat optimisés
Compare les performances avant et après les optimisations
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


class OptimizedBuySignalsPerformanceTester:
    """
    Testeur de performance pour les signaux d'achat optimisés
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def test_optimized_vs_original_performance(self) -> Dict[str, Any]:
        """
        Compare les performances des signaux optimisés vs originaux
        """
        try:
            self.logger.info("🧪 Test de performance optimisé vs original")
            
            # Récupérer tous les signaux d'achat
            buy_opportunities = self.db.query(HistoricalOpportunities).filter(
                HistoricalOpportunities.recommendation.in_(['BUY_WEAK', 'BUY_MODERATE', 'BUY_STRONG'])
            ).all()
            
            if not buy_opportunities:
                return {"error": "Aucun signal d'achat trouvé"}
            
            # Analyser les performances originales
            original_performance = self._analyze_original_performance(buy_opportunities)
            
            # Simuler les performances optimisées
            optimized_performance = self._simulate_optimized_performance(buy_opportunities)
            
            # Comparer les performances
            comparison = self._compare_performances(original_performance, optimized_performance)
            
            # Analyser l'impact des optimisations
            impact_analysis = self._analyze_optimization_impact(buy_opportunities)
            
            return {
                "original_performance": original_performance,
                "optimized_performance": optimized_performance,
                "comparison": comparison,
                "impact_analysis": impact_analysis,
                "total_signals": len(buy_opportunities)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors du test de performance: {e}")
            return {"error": str(e)}
    
    def _analyze_original_performance(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse les performances originales des signaux d'achat"""
        
        performance = {
            "by_recommendation": {},
            "overall": {
                "total_signals": 0,
                "positive_returns": 0,
                "negative_returns": 0,
                "zero_returns": 0,
                "total_return": 0,
                "avg_return": 0,
                "win_rate": 0,
                "sharpe_ratio": 0
            }
        }
        
        all_returns = []
        
        for opp in opportunities:
            if opp.return_1_day is None:
                continue
            
            rec_type = opp.recommendation
            return_1d = float(opp.return_1_day)
            
            # Statistiques globales
            performance["overall"]["total_signals"] += 1
            all_returns.append(return_1d)
            
            if return_1d > 0:
                performance["overall"]["positive_returns"] += 1
            elif return_1d < 0:
                performance["overall"]["negative_returns"] += 1
            else:
                performance["overall"]["zero_returns"] += 1
            
            performance["overall"]["total_return"] += return_1d
            
            # Par type de recommandation
            if rec_type not in performance["by_recommendation"]:
                performance["by_recommendation"][rec_type] = {
                    "count": 0,
                    "positive_returns": 0,
                    "negative_returns": 0,
                    "total_return": 0,
                    "returns": []
                }
            
            performance["by_recommendation"][rec_type]["count"] += 1
            performance["by_recommendation"][rec_type]["returns"].append(return_1d)
            performance["by_recommendation"][rec_type]["total_return"] += return_1d
            
            if return_1d > 0:
                performance["by_recommendation"][rec_type]["positive_returns"] += 1
            else:
                performance["by_recommendation"][rec_type]["negative_returns"] += 1
        
        # Calculer les statistiques globales
        if all_returns:
            performance["overall"]["avg_return"] = np.mean(all_returns)
            performance["overall"]["win_rate"] = performance["overall"]["positive_returns"] / performance["overall"]["total_signals"]
            performance["overall"]["sharpe_ratio"] = np.mean(all_returns) / np.std(all_returns) if np.std(all_returns) > 0 else 0
        
        # Calculer les statistiques par recommandation
        for rec_type, data in performance["by_recommendation"].items():
            if data["returns"]:
                data["avg_return"] = np.mean(data["returns"])
                data["win_rate"] = data["positive_returns"] / data["count"]
                data["sharpe_ratio"] = np.mean(data["returns"]) / np.std(data["returns"]) if np.std(data["returns"]) > 0 else 0
        
        return performance
    
    def _simulate_optimized_performance(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Simule les performances avec les optimisations appliquées"""
        
        performance = {
            "by_recommendation": {},
            "overall": {
                "total_signals": 0,
                "positive_returns": 0,
                "negative_returns": 0,
                "zero_returns": 0,
                "total_return": 0,
                "avg_return": 0,
                "win_rate": 0,
                "sharpe_ratio": 0
            }
        }
        
        all_returns = []
        
        for opp in opportunities:
            if opp.return_1_day is None:
                continue
            
            # Appliquer les optimisations
            optimized_result = self._apply_optimizations(opp)
            
            if not optimized_result["signal_generated"]:
                continue  # Signal filtré par les optimisations
            
            rec_type = optimized_result["recommendation"]
            return_1d = float(opp.return_1_day)
            
            # Ajuster le retour avec le position sizing optimisé
            adjusted_return = return_1d * optimized_result["position_multiplier"]
            
            # Statistiques globales
            performance["overall"]["total_signals"] += 1
            all_returns.append(adjusted_return)
            
            if adjusted_return > 0:
                performance["overall"]["positive_returns"] += 1
            elif adjusted_return < 0:
                performance["overall"]["negative_returns"] += 1
            else:
                performance["overall"]["zero_returns"] += 1
            
            performance["overall"]["total_return"] += adjusted_return
            
            # Par type de recommandation
            if rec_type not in performance["by_recommendation"]:
                performance["by_recommendation"][rec_type] = {
                    "count": 0,
                    "positive_returns": 0,
                    "negative_returns": 0,
                    "total_return": 0,
                    "returns": []
                }
            
            performance["by_recommendation"][rec_type]["count"] += 1
            performance["by_recommendation"][rec_type]["returns"].append(adjusted_return)
            performance["by_recommendation"][rec_type]["total_return"] += adjusted_return
            
            if adjusted_return > 0:
                performance["by_recommendation"][rec_type]["positive_returns"] += 1
            else:
                performance["by_recommendation"][rec_type]["negative_returns"] += 1
        
        # Calculer les statistiques globales
        if all_returns:
            performance["overall"]["avg_return"] = np.mean(all_returns)
            performance["overall"]["win_rate"] = performance["overall"]["positive_returns"] / performance["overall"]["total_signals"]
            performance["overall"]["sharpe_ratio"] = np.mean(all_returns) / np.std(all_returns) if np.std(all_returns) > 0 else 0
        
        # Calculer les statistiques par recommandation
        for rec_type, data in performance["by_recommendation"].items():
            if data["returns"]:
                data["avg_return"] = np.mean(data["returns"])
                data["win_rate"] = data["positive_returns"] / data["count"]
                data["sharpe_ratio"] = np.mean(data["returns"]) / np.std(data["returns"]) if np.std(data["returns"]) > 0 else 0
        
        return performance
    
    def _apply_optimizations(self, opportunity: HistoricalOpportunities) -> Dict[str, Any]:
        """Applique les optimisations à une opportunité"""
        
        # Récupérer les scores
        composite_score = float(opportunity.composite_score) if opportunity.composite_score else 0.5
        technical_score = float(opportunity.technical_score) if opportunity.technical_score else 0.5
        sentiment_score = float(opportunity.sentiment_score) if opportunity.sentiment_score else 0.5
        market_score = float(opportunity.market_score) if opportunity.market_score else 0.5
        confidence_level = float(opportunity.confidence_level) if opportunity.confidence_level else 0.5
        
        # Calculer le score composite optimisé
        optimized_composite = (
            0.40 * technical_score +
            0.45 * sentiment_score +
            0.15 * market_score
        )
        
        # Pénalité pour la sur-confiance
        if confidence_level > 0.85:
            confidence_penalty = (confidence_level - 0.85) * 0.2
            optimized_composite -= confidence_penalty
        
        optimized_composite = max(0.0, min(1.0, optimized_composite))
        
        # Déterminer la recommandation optimisée
        if (optimized_composite >= 0.65 and 
            technical_score >= 0.60 and 
            sentiment_score >= 0.55 and 
            market_score <= 0.40 and 
            0.70 <= confidence_level <= 0.85):
            recommendation = "BUY_STRONG"
        elif (optimized_composite >= 0.55 and 
              technical_score >= 0.50 and 
              sentiment_score >= 0.45 and 
              market_score <= 0.45 and 
              0.65 <= confidence_level <= 0.90):
            recommendation = "BUY_MODERATE"
        elif (optimized_composite >= 0.45 and 
              technical_score >= 0.40 and 
              sentiment_score >= 0.35 and 
              market_score <= 0.50 and 
              0.60 <= confidence_level <= 0.95):
            recommendation = "BUY_WEAK"
        else:
            recommendation = "HOLD"
        
        # Vérifier si le signal est généré
        signal_generated = recommendation != "HOLD"
        
        # Calculer le multiplicateur de position
        if signal_generated:
            # Ajustement confiance
            if confidence_level < 0.6:
                confidence_factor = 0.5
            elif confidence_level > 0.85:
                confidence_factor = 0.8
            else:
                confidence_factor = 1.0 + (confidence_level - 0.5) * 0.6
            
            # Ajustement score
            score_factor = (
                0.4 * technical_score + 
                0.4 * sentiment_score + 
                0.2 * market_score
            )
            
            position_multiplier = confidence_factor * score_factor
        else:
            position_multiplier = 0
        
        return {
            "signal_generated": signal_generated,
            "recommendation": recommendation,
            "original_composite": composite_score,
            "optimized_composite": optimized_composite,
            "position_multiplier": position_multiplier,
            "confidence_factor": confidence_factor if signal_generated else 0,
            "score_factor": score_factor if signal_generated else 0
        }
    
    def _compare_performances(self, original: Dict[str, Any], optimized: Dict[str, Any]) -> Dict[str, Any]:
        """Compare les performances originales et optimisées"""
        
        comparison = {
            "overall_improvement": {},
            "by_recommendation_improvement": {},
            "key_metrics": {}
        }
        
        # Comparaison globale
        orig_overall = original["overall"]
        opt_overall = optimized["overall"]
        
        comparison["overall_improvement"] = {
            "signal_count_change": opt_overall["total_signals"] - orig_overall["total_signals"],
            "signal_count_change_pct": (opt_overall["total_signals"] - orig_overall["total_signals"]) / orig_overall["total_signals"] * 100 if orig_overall["total_signals"] > 0 else 0,
            "win_rate_change": opt_overall["win_rate"] - orig_overall["win_rate"],
            "avg_return_change": opt_overall["avg_return"] - orig_overall["avg_return"],
            "sharpe_ratio_change": opt_overall["sharpe_ratio"] - orig_overall["sharpe_ratio"],
            "total_return_change": opt_overall["total_return"] - orig_overall["total_return"]
        }
        
        # Comparaison par recommandation
        for rec_type in set(list(original["by_recommendation"].keys()) + list(optimized["by_recommendation"].keys())):
            orig_data = original["by_recommendation"].get(rec_type, {"count": 0, "win_rate": 0, "avg_return": 0, "sharpe_ratio": 0})
            opt_data = optimized["by_recommendation"].get(rec_type, {"count": 0, "win_rate": 0, "avg_return": 0, "sharpe_ratio": 0})
            
            comparison["by_recommendation_improvement"][rec_type] = {
                "count_change": opt_data["count"] - orig_data["count"],
                "win_rate_change": opt_data["win_rate"] - orig_data["win_rate"],
                "avg_return_change": opt_data["avg_return"] - orig_data["avg_return"],
                "sharpe_ratio_change": opt_data["sharpe_ratio"] - orig_data["sharpe_ratio"]
            }
        
        # Métriques clés
        comparison["key_metrics"] = {
            "original_signals": orig_overall["total_signals"],
            "optimized_signals": opt_overall["total_signals"],
            "original_win_rate": orig_overall["win_rate"],
            "optimized_win_rate": opt_overall["win_rate"],
            "original_avg_return": orig_overall["avg_return"],
            "optimized_avg_return": opt_overall["avg_return"],
            "original_sharpe": orig_overall["sharpe_ratio"],
            "optimized_sharpe": opt_overall["sharpe_ratio"]
        }
        
        return comparison
    
    def _analyze_optimization_impact(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse l'impact des optimisations"""
        
        impact = {
            "signals_filtered": 0,
            "signals_kept": 0,
            "recommendation_changes": {},
            "quality_improvements": {}
        }
        
        for opp in opportunities:
            optimized_result = self._apply_optimizations(opp)
            
            if optimized_result["signal_generated"]:
                impact["signals_kept"] += 1
            else:
                impact["signals_filtered"] += 1
            
            # Changements de recommandation
            original_rec = opp.recommendation
            optimized_rec = optimized_result["recommendation"]
            
            if original_rec != optimized_rec:
                change_key = f"{original_rec} -> {optimized_rec}"
                if change_key not in impact["recommendation_changes"]:
                    impact["recommendation_changes"][change_key] = 0
                impact["recommendation_changes"][change_key] += 1
        
        # Améliorations de qualité
        impact["quality_improvements"] = {
            "signals_filtered_pct": impact["signals_filtered"] / len(opportunities) * 100,
            "signals_kept_pct": impact["signals_kept"] / len(opportunities) * 100,
            "total_recommendation_changes": sum(impact["recommendation_changes"].values())
        }
        
        return impact
    
    def generate_performance_recommendations(self, test_results: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur les résultats des tests"""
        
        recommendations = []
        
        comparison = test_results.get("comparison", {})
        overall_improvement = comparison.get("overall_improvement", {})
        
        # Analyser les améliorations
        win_rate_change = overall_improvement.get("win_rate_change", 0)
        avg_return_change = overall_improvement.get("avg_return_change", 0)
        sharpe_change = overall_improvement.get("sharpe_ratio_change", 0)
        signal_count_change = overall_improvement.get("signal_count_change", 0)
        
        if win_rate_change > 0.05:
            recommendations.append(f"✅ Amélioration significative du taux de réussite (+{win_rate_change:.1%})")
        elif win_rate_change > 0:
            recommendations.append(f"⚠️ Amélioration modérée du taux de réussite (+{win_rate_change:.1%})")
        else:
            recommendations.append(f"❌ Dégradation du taux de réussite ({win_rate_change:.1%})")
        
        if avg_return_change > 0.01:
            recommendations.append(f"✅ Amélioration significative du retour moyen (+{avg_return_change:.2%})")
        elif avg_return_change > 0:
            recommendations.append(f"⚠️ Amélioration modérée du retour moyen (+{avg_return_change:.2%})")
        else:
            recommendations.append(f"❌ Dégradation du retour moyen ({avg_return_change:.2%})")
        
        if sharpe_change > 0.1:
            recommendations.append(f"✅ Amélioration significative du ratio de Sharpe (+{sharpe_change:.3f})")
        elif sharpe_change > 0:
            recommendations.append(f"⚠️ Amélioration modérée du ratio de Sharpe (+{sharpe_change:.3f})")
        else:
            recommendations.append(f"❌ Dégradation du ratio de Sharpe ({sharpe_change:.3f})")
        
        if signal_count_change < 0:
            recommendations.append(f"📉 Réduction du nombre de signaux ({signal_count_change}) - Qualité vs quantité")
        elif signal_count_change > 0:
            recommendations.append(f"📈 Augmentation du nombre de signaux (+{signal_count_change})")
        
        # Recommandations spécifiques
        impact_analysis = test_results.get("impact_analysis", {})
        signals_filtered_pct = impact_analysis.get("quality_improvements", {}).get("signals_filtered_pct", 0)
        
        if signals_filtered_pct > 30:
            recommendations.append("🔧 Filtrage agressif - Vérifier les seuils de qualité")
        elif signals_filtered_pct > 15:
            recommendations.append("✅ Filtrage modéré - Bon équilibre qualité/quantité")
        else:
            recommendations.append("⚠️ Filtrage faible - Considérer des seuils plus stricts")
        
        return recommendations


def main():
    """Fonction principale pour tester les performances des signaux optimisés"""
    logger.info("🚀 Démarrage du test de performance des signaux optimisés")
    
    try:
        # Connexion à la base de données
        db = SessionLocal()
        
        # Initialiser le testeur
        tester = OptimizedBuySignalsPerformanceTester(db)
        
        # Exécuter le test de performance
        logger.info("🧪 Test de performance...")
        test_results = tester.test_optimized_vs_original_performance()
        
        if "error" in test_results:
            logger.error(f"❌ Erreur lors du test: {test_results['error']}")
            return
        
        # Générer les recommandations
        logger.info("💡 Génération des recommandations...")
        recommendations = tester.generate_performance_recommendations(test_results)
        
        # Afficher les résultats
        print("\n" + "="*80)
        print("🧪 TEST DE PERFORMANCE DES SIGNAUX D'ACHAT OPTIMISÉS")
        print("="*80)
        
        print(f"\n📊 SIGNAUX ANALYSÉS: {test_results['total_signals']}")
        
        # Comparaison globale
        comparison = test_results.get("comparison", {})
        key_metrics = comparison.get("key_metrics", {})
        
        print(f"\n📈 COMPARAISON GLOBALE:")
        print(f"  • Signaux originaux: {key_metrics.get('original_signals', 0)}")
        print(f"  • Signaux optimisés: {key_metrics.get('optimized_signals', 0)}")
        print(f"  • Taux de réussite original: {key_metrics.get('original_win_rate', 0):.1%}")
        print(f"  • Taux de réussite optimisé: {key_metrics.get('optimized_win_rate', 0):.1%}")
        print(f"  • Retour moyen original: {key_metrics.get('original_avg_return', 0):.2%}")
        print(f"  • Retour moyen optimisé: {key_metrics.get('optimized_avg_return', 0):.2%}")
        print(f"  • Sharpe original: {key_metrics.get('original_sharpe', 0):.3f}")
        print(f"  • Sharpe optimisé: {key_metrics.get('optimized_sharpe', 0):.3f}")
        
        # Améliorations
        overall_improvement = comparison.get("overall_improvement", {})
        print(f"\n🚀 AMÉLIORATIONS:")
        print(f"  • Changement taux de réussite: {overall_improvement.get('win_rate_change', 0):+.1%}")
        print(f"  • Changement retour moyen: {overall_improvement.get('avg_return_change', 0):+.2%}")
        print(f"  • Changement Sharpe: {overall_improvement.get('sharpe_ratio_change', 0):+.3f}")
        print(f"  • Changement nombre de signaux: {overall_improvement.get('signal_count_change', 0):+}")
        
        # Impact des optimisations
        impact_analysis = test_results.get("impact_analysis", {})
        quality_improvements = impact_analysis.get("quality_improvements", {})
        
        print(f"\n🔧 IMPACT DES OPTIMISATIONS:")
        print(f"  • Signaux filtrés: {quality_improvements.get('signals_filtered_pct', 0):.1f}%")
        print(f"  • Signaux conservés: {quality_improvements.get('signals_kept_pct', 0):.1f}%")
        print(f"  • Changements de recommandation: {quality_improvements.get('total_recommendation_changes', 0)}")
        
        print(f"\n💡 RECOMMANDATIONS:")
        for rec in recommendations:
            print(f"  • {rec}")
        
        # Sauvegarder les résultats
        results = {
            "test_results": test_results,
            "recommendations": recommendations,
            "test_timestamp": datetime.now().isoformat()
        }
        
        with open("/Users/loiclinais/Documents/dev/aimarkets/backend/scripts/optimized_buy_signals_performance_test.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("📁 Résultats sauvegardés dans optimized_buy_signals_performance_test.json")
        logger.info("✅ Test de performance terminé avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        return


if __name__ == "__main__":
    main()
