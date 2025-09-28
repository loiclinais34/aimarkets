#!/usr/bin/env python3
"""
Script pour tester les performances de la Phase 3 : Gestion du risque
Compare les performances avant et après l'implémentation de la gestion du risque
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, List
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


class Phase3PerformanceTester:
    """
    Testeur de performance pour la Phase 3
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def test_risk_management_impact(self) -> Dict[str, Any]:
        """
        Teste l'impact de la gestion du risque sur les performances
        """
        try:
            self.logger.info("🧪 Test de l'impact de la gestion du risque")
            
            # Récupérer les opportunités avec leurs validations
            opportunities = self.db.query(HistoricalOpportunities).all()
            
            if not opportunities:
                return {"error": "Aucune opportunité trouvée"}
            
            # Analyser les performances par type de recommandation
            performance_analysis = self._analyze_performance_by_recommendation(opportunities)
            
            # Analyser l'impact du position sizing
            position_sizing_analysis = self._analyze_position_sizing_impact(opportunities)
            
            # Analyser l'impact des stops
            stop_loss_analysis = self._analyze_stop_loss_impact(opportunities)
            
            # Calculer les métriques de risque
            risk_metrics = self._calculate_risk_metrics(opportunities)
            
            return {
                "performance_analysis": performance_analysis,
                "position_sizing_analysis": position_sizing_analysis,
                "stop_loss_analysis": stop_loss_analysis,
                "risk_metrics": risk_metrics,
                "total_opportunities": len(opportunities)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors du test de performance: {e}")
            return {"error": str(e)}
    
    def _analyze_performance_by_recommendation(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse les performances par type de recommandation"""
        
        recommendation_stats = {}
        
        for opp in opportunities:
            rec_type = opp.recommendation
            if not rec_type:
                continue
            
            if rec_type not in recommendation_stats:
                recommendation_stats[rec_type] = {
                    "count": 0,
                    "returns_1d": [],
                    "returns_7d": [],
                    "returns_30d": [],
                    "accuracy_1d": [],
                    "accuracy_7d": [],
                    "accuracy_30d": []
                }
            
            recommendation_stats[rec_type]["count"] += 1
            
            # Ajouter les retours
            if opp.return_1_day is not None:
                recommendation_stats[rec_type]["returns_1d"].append(float(opp.return_1_day))
            if opp.return_7_days is not None:
                recommendation_stats[rec_type]["returns_7d"].append(float(opp.return_7_days))
            if opp.return_30_days is not None:
                recommendation_stats[rec_type]["returns_30d"].append(float(opp.return_30_days))
            
            # Ajouter les précisions
            if opp.recommendation_correct_1_day is not None:
                recommendation_stats[rec_type]["accuracy_1d"].append(opp.recommendation_correct_1_day)
            if opp.recommendation_correct_7_days is not None:
                recommendation_stats[rec_type]["accuracy_7d"].append(opp.recommendation_correct_7_days)
            if opp.recommendation_correct_30_days is not None:
                recommendation_stats[rec_type]["accuracy_30d"].append(opp.recommendation_correct_30_days)
        
        # Calculer les statistiques
        for rec_type, stats in recommendation_stats.items():
            for period in ["1d", "7d", "30d"]:
                returns_key = f"returns_{period}"
                accuracy_key = f"accuracy_{period}"
                
                if stats[returns_key]:
                    stats[f"avg_return_{period}"] = np.mean(stats[returns_key])
                    stats[f"std_return_{period}"] = np.std(stats[returns_key])
                    stats[f"sharpe_{period}"] = stats[f"avg_return_{period}"] / stats[f"std_return_{period}"] if stats[f"std_return_{period}"] > 0 else 0
                
                if stats[accuracy_key]:
                    stats[f"accuracy_{period}"] = np.mean(stats[accuracy_key])
        
        return recommendation_stats
    
    def _analyze_position_sizing_impact(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse l'impact du position sizing sur les performances"""
        
        # Simuler différents scénarios de position sizing
        scenarios = {
            "fixed_1": {"position_size": 1, "description": "Position fixe de 1 action"},
            "fixed_10": {"position_size": 10, "description": "Position fixe de 10 actions"},
            "risk_based": {"position_size": "dynamic", "description": "Position basée sur le risque"}
        }
        
        scenario_results = {}
        
        for scenario_name, scenario_config in scenarios.items():
            total_return = 0
            total_risk = 0
            position_count = 0
            
            for opp in opportunities:
                if opp.return_1_day is None:
                    continue
                
                # Calculer la taille de position
                if scenario_config["position_size"] == "dynamic":
                    # Position basée sur le risque (simplifié)
                    position_size = max(1, int(1000 / float(opp.price_at_generation or 100)))
                else:
                    position_size = scenario_config["position_size"]
                
                # Calculer le retour et le risque
                position_return = float(opp.return_1_day) * position_size
                position_risk = position_size * float(opp.price_at_generation or 100) * 0.02  # 2% de risque
                
                total_return += position_return
                total_risk += position_risk
                position_count += 1
            
            scenario_results[scenario_name] = {
                "description": scenario_config["description"],
                "total_return": total_return,
                "total_risk": total_risk,
                "position_count": position_count,
                "avg_return_per_position": total_return / position_count if position_count > 0 else 0,
                "risk_return_ratio": total_return / total_risk if total_risk > 0 else 0
            }
        
        return scenario_results
    
    def _analyze_stop_loss_impact(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse l'impact des stops sur les performances"""
        
        stop_scenarios = {
            "no_stop": {"stop_loss": None, "description": "Aucun stop-loss"},
            "fixed_2pct": {"stop_loss": 0.02, "description": "Stop-loss fixe à 2%"},
            "fixed_5pct": {"stop_loss": 0.05, "description": "Stop-loss fixe à 5%"},
            "dynamic_atr": {"stop_loss": "dynamic", "description": "Stop-loss dynamique basé sur ATR"}
        }
        
        scenario_results = {}
        
        for scenario_name, scenario_config in stop_scenarios.items():
            total_return = 0
            stopped_out_count = 0
            position_count = 0
            
            for opp in opportunities:
                if opp.return_1_day is None or opp.price_at_generation is None:
                    continue
                
                position_count += 1
                current_price = float(opp.price_at_generation)
                return_1d = float(opp.return_1_day)
                
                # Calculer le niveau de stop
                if scenario_config["stop_loss"] is None:
                    # Pas de stop
                    final_return = return_1d
                elif scenario_config["stop_loss"] == "dynamic":
                    # Stop dynamique basé sur ATR (simplifié)
                    stop_level = current_price * 0.98  # 2% par défaut
                else:
                    # Stop fixe
                    stop_level = current_price * (1 - scenario_config["stop_loss"])
                
                # Vérifier si le stop est touché
                if scenario_config["stop_loss"] is not None and scenario_config["stop_loss"] != "dynamic":
                    stop_loss_value = float(scenario_config["stop_loss"])
                    if return_1d < 0 and abs(return_1d) > abs(stop_loss_value):
                        # Stop touché
                        final_return = -stop_loss_value
                        stopped_out_count += 1
                    else:
                        final_return = return_1d
                elif scenario_config["stop_loss"] == "dynamic":
                    # Stop dynamique basé sur ATR (simplifié à 2%)
                    if return_1d < -0.02:
                        final_return = -0.02
                        stopped_out_count += 1
                    else:
                        final_return = return_1d
                else:
                    final_return = return_1d
                
                total_return += final_return
            
            scenario_results[scenario_name] = {
                "description": scenario_config["description"],
                "total_return": total_return,
                "avg_return": total_return / position_count if position_count > 0 else 0,
                "stopped_out_count": stopped_out_count,
                "stopped_out_rate": stopped_out_count / position_count if position_count > 0 else 0,
                "position_count": position_count
            }
        
        return scenario_results
    
    def _calculate_risk_metrics(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Calcule les métriques de risque globales"""
        
        # Récupérer tous les retours
        returns_1d = [float(opp.return_1_day) for opp in opportunities if opp.return_1_day is not None]
        returns_7d = [float(opp.return_7_days) for opp in opportunities if opp.return_7_days is not None]
        returns_30d = [float(opp.return_30_days) for opp in opportunities if opp.return_30_days is not None]
        
        risk_metrics = {}
        
        for period, returns in [("1d", returns_1d), ("7d", returns_7d), ("30d", returns_30d)]:
            if not returns:
                continue
            
            returns_array = np.array(returns)
            
            # Métriques de base
            mean_return = np.mean(returns_array)
            std_return = np.std(returns_array)
            sharpe_ratio = mean_return / std_return if std_return > 0 else 0
            
            # Calcul du maximum drawdown
            cumulative_returns = np.cumprod(1 + returns_array)
            running_max = np.maximum.accumulate(cumulative_returns)
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = np.min(drawdown)
            
            # VaR (Value at Risk) à 95%
            var_95 = np.percentile(returns_array, 5)
            
            # Expected Shortfall (CVaR)
            cvar_95 = np.mean(returns_array[returns_array <= var_95])
            
            risk_metrics[period] = {
                "mean_return": mean_return,
                "std_return": std_return,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "var_95": var_95,
                "cvar_95": cvar_95,
                "positive_returns": np.sum(returns_array > 0),
                "negative_returns": np.sum(returns_array < 0),
                "win_rate": np.sum(returns_array > 0) / len(returns_array)
            }
        
        return risk_metrics
    
    def generate_phase3_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Génère des recommandations basées sur l'analyse Phase 3"""
        
        recommendations = []
        
        # Analyser les performances par recommandation
        perf_analysis = analysis_results.get("performance_analysis", {})
        
        for rec_type, stats in perf_analysis.items():
            if rec_type == "HOLD":
                continue
            
            accuracy_1d = stats.get("accuracy_1d", 0)
            avg_return_1d = stats.get("avg_return_1d", 0)
            sharpe_1d = stats.get("sharpe_1d", 0)
            
            if accuracy_1d > 0.8 and avg_return_1d > 0:
                recommendations.append(f"✅ {rec_type}: Excellente performance (Précision: {accuracy_1d:.1%}, Retour: {avg_return_1d:.2%})")
            elif accuracy_1d > 0.6:
                recommendations.append(f"⚠️ {rec_type}: Performance acceptable mais à surveiller (Précision: {accuracy_1d:.1%})")
            else:
                recommendations.append(f"❌ {rec_type}: Performance insuffisante (Précision: {accuracy_1d:.1%})")
        
        # Analyser l'impact du position sizing
        position_analysis = analysis_results.get("position_sizing_analysis", {})
        if "risk_based" in position_analysis:
            risk_based = position_analysis["risk_based"]
            if risk_based["risk_return_ratio"] > 0.5:
                recommendations.append("✅ Position sizing basé sur le risque: Efficace")
            else:
                recommendations.append("⚠️ Position sizing basé sur le risque: À optimiser")
        
        # Analyser l'impact des stops
        stop_analysis = analysis_results.get("stop_loss_analysis", {})
        if "dynamic_atr" in stop_analysis:
            dynamic_stop = stop_analysis["dynamic_atr"]
            if dynamic_stop["stopped_out_rate"] < 0.3:
                recommendations.append("✅ Stops dynamiques: Taux d'arrêt acceptable")
            else:
                recommendations.append("⚠️ Stops dynamiques: Taux d'arrêt élevé")
        
        return recommendations


def main():
    """Fonction principale pour tester les performances Phase 3"""
    logger.info("🚀 Démarrage du test de performance Phase 3")
    
    try:
        # Connexion à la base de données
        db = SessionLocal()
        
        # Initialiser le testeur
        tester = Phase3PerformanceTester(db)
        
        # Exécuter l'analyse de performance
        logger.info("📊 Analyse des performances...")
        analysis_results = tester.test_risk_management_impact()
        
        if "error" in analysis_results:
            logger.error(f"❌ Erreur lors de l'analyse: {analysis_results['error']}")
            return
        
        # Générer les recommandations
        logger.info("💡 Génération des recommandations...")
        recommendations = tester.generate_phase3_recommendations(analysis_results)
        
        # Afficher les résultats
        print("\n" + "="*80)
        print("📊 RÉSULTATS DU TEST DE PERFORMANCE PHASE 3")
        print("="*80)
        
        print(f"\n📈 OPPORTUNITÉS ANALYSÉES: {analysis_results['total_opportunities']}")
        
        print(f"\n🎯 PERFORMANCES PAR RECOMMANDATION:")
        perf_analysis = analysis_results.get("performance_analysis", {})
        for rec_type, stats in perf_analysis.items():
            if stats["count"] > 0:
                print(f"  • {rec_type}: {stats['count']} opportunités")
                if "accuracy_1d" in stats:
                    print(f"    - Précision 1j: {stats['accuracy_1d']:.1%}")
                if "avg_return_1d" in stats:
                    print(f"    - Retour moyen 1j: {stats['avg_return_1d']:.2%}")
                if "sharpe_1d" in stats:
                    print(f"    - Sharpe 1j: {stats['sharpe_1d']:.3f}")
        
        print(f"\n💰 IMPACT DU POSITION SIZING:")
        position_analysis = analysis_results.get("position_sizing_analysis", {})
        for scenario, results in position_analysis.items():
            print(f"  • {results['description']}:")
            print(f"    - Retour total: {results['total_return']:.2f}")
            print(f"    - Ratio risque/retour: {results['risk_return_ratio']:.3f}")
        
        print(f"\n🛡️ IMPACT DES STOPS:")
        stop_analysis = analysis_results.get("stop_loss_analysis", {})
        for scenario, results in stop_analysis.items():
            print(f"  • {results['description']}:")
            print(f"    - Retour moyen: {results['avg_return']:.2%}")
            print(f"    - Taux d'arrêt: {results['stopped_out_rate']:.1%}")
        
        print(f"\n📊 MÉTRIQUES DE RISQUE:")
        risk_metrics = analysis_results.get("risk_metrics", {})
        for period, metrics in risk_metrics.items():
            print(f"  • Période {period}:")
            print(f"    - Sharpe: {metrics['sharpe_ratio']:.3f}")
            print(f"    - Max Drawdown: {metrics['max_drawdown']:.2%}")
            print(f"    - VaR 95%: {metrics['var_95']:.2%}")
            print(f"    - Taux de réussite: {metrics['win_rate']:.1%}")
        
        print(f"\n💡 RECOMMANDATIONS:")
        for rec in recommendations:
            print(f"  • {rec}")
        
        # Sauvegarder les résultats
        results = {
            "analysis_results": analysis_results,
            "recommendations": recommendations,
            "test_timestamp": datetime.now().isoformat()
        }
        
        with open("/Users/loiclinais/Documents/dev/aimarkets/backend/scripts/phase3_performance_test_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("📁 Résultats sauvegardés dans phase3_performance_test_results.json")
        logger.info("✅ Test de performance Phase 3 terminé avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de performance Phase 3: {e}")
        return


if __name__ == "__main__":
    main()
