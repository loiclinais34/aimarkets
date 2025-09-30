#!/usr/bin/env python3
"""
Script pour tester si la recherche frontend utilise les nouvelles optimisations
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any
import json

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.advanced_opportunities import AdvancedOpportunity

class FrontendSearchOptimizationTester:
    """Testeur de la recherche frontend avec optimisations"""
    
    def __init__(self):
        """Initialise le testeur"""
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        
    def __del__(self):
        """Ferme la session de base de données"""
        if hasattr(self, 'db'):
            self.db.close()
    
    def check_recent_opportunities(self) -> Dict[str, Any]:
        """Vérifie les opportunités récentes dans la base"""
        print("🔍 Vérification des opportunités récentes...")
        
        # Récupérer les opportunités des 7 derniers jours
        from datetime import timedelta
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        recent_opportunities = self.db.query(AdvancedOpportunity).filter(
            AdvancedOpportunity.updated_at >= seven_days_ago
        ).order_by(AdvancedOpportunity.updated_at.desc()).limit(20).all()
        
        print(f"📊 Trouvé {len(recent_opportunities)} opportunités récentes")
        
        # Analyser les caractéristiques des opportunités récentes
        analysis = {
            "total_recent": len(recent_opportunities),
            "by_recommendation": {},
            "by_risk_level": {},
            "score_ranges": {
                "composite_score": {"min": None, "max": None, "avg": None},
                "technical_score": {"min": None, "max": None, "avg": None},
                "confidence_level": {"min": None, "max": None, "avg": None}
            },
            "optimization_indicators": {
                "high_technical_score_count": 0,  # >= 0.533
                "high_composite_score_count": 0,  # >= 0.651
                "high_confidence_count": 0,       # >= 0.6
                "optimized_opportunities": 0      # Toutes les conditions
            }
        }
        
        if recent_opportunities:
            # Analyser par recommandation
            for opp in recent_opportunities:
                rec = opp.recommendation
                if rec not in analysis["by_recommendation"]:
                    analysis["by_recommendation"][rec] = 0
                analysis["by_recommendation"][rec] += 1
            
            # Analyser par niveau de risque
            for opp in recent_opportunities:
                risk = opp.risk_level
                if risk not in analysis["by_risk_level"]:
                    analysis["by_risk_level"][risk] = 0
                analysis["by_risk_level"][risk] += 1
            
            # Analyser les scores
            composite_scores = [float(opp.composite_score) for opp in recent_opportunities if opp.composite_score]
            technical_scores = [float(opp.technical_score) for opp in recent_opportunities if opp.technical_score]
            confidence_scores = [float(opp.confidence_level) for opp in recent_opportunities if opp.confidence_level]
            
            if composite_scores:
                analysis["score_ranges"]["composite_score"] = {
                    "min": min(composite_scores),
                    "max": max(composite_scores),
                    "avg": sum(composite_scores) / len(composite_scores)
                }
            
            if technical_scores:
                analysis["score_ranges"]["technical_score"] = {
                    "min": min(technical_scores),
                    "max": max(technical_scores),
                    "avg": sum(technical_scores) / len(technical_scores)
                }
            
            if confidence_scores:
                analysis["score_ranges"]["confidence_level"] = {
                    "min": min(confidence_scores),
                    "max": max(confidence_scores),
                    "avg": sum(confidence_scores) / len(confidence_scores)
                }
            
            # Vérifier les indicateurs d'optimisation
            for opp in recent_opportunities:
                if opp.technical_score and float(opp.technical_score) >= 0.533:
                    analysis["optimization_indicators"]["high_technical_score_count"] += 1
                
                if opp.composite_score and float(opp.composite_score) >= 0.651:
                    analysis["optimization_indicators"]["high_composite_score_count"] += 1
                
                if opp.confidence_level and float(opp.confidence_level) >= 0.6:
                    analysis["optimization_indicators"]["high_confidence_count"] += 1
                
                # Vérifier si l'opportunité passe tous les seuils optimisés
                if (opp.technical_score and float(opp.technical_score) >= 0.533 and
                    opp.composite_score and float(opp.composite_score) >= 0.651 and
                    opp.confidence_level and float(opp.confidence_level) >= 0.6):
                    analysis["optimization_indicators"]["optimized_opportunities"] += 1
        
        return analysis
    
    def simulate_frontend_search(self) -> Dict[str, Any]:
        """Simule une recherche frontend typique"""
        print("🔍 Simulation d'une recherche frontend...")
        
        # Paramètres de recherche typiques du frontend
        search_params = {
            "min_score": 0.2,
            "max_risk": "HIGH",
            "limit": 20,
            "sort_by": "composite_score",
            "sort_order": "desc"
        }
        
        # Construire la requête comme dans l'API
        query = self.db.query(AdvancedOpportunity)
        
        # Filtrer par score composite minimum
        query = query.filter(AdvancedOpportunity.composite_score >= search_params["min_score"])
        
        # Filtrer par niveau de risque
        risk_levels = ["LOW", "MEDIUM", "HIGH"]
        max_risk = search_params["max_risk"]
        if max_risk in risk_levels:
            max_risk_index = risk_levels.index(max_risk)
            allowed_risks = risk_levels[:max_risk_index + 1]
            query = query.filter(AdvancedOpportunity.risk_level.in_(allowed_risks))
        
        # Trier par score composite décroissant
        query = query.order_by(AdvancedOpportunity.composite_score.desc())
        
        # Limiter les résultats
        opportunities = query.limit(search_params["limit"]).all()
        
        print(f"📊 Trouvé {len(opportunities)} opportunités avec les paramètres de recherche")
        
        # Analyser les résultats
        results_analysis = {
            "search_params": search_params,
            "total_found": len(opportunities),
            "by_recommendation": {},
            "by_risk_level": {},
            "score_analysis": {
                "composite_scores": [],
                "technical_scores": [],
                "confidence_scores": []
            },
            "optimization_compliance": {
                "meets_technical_threshold": 0,    # >= 0.533
                "meets_composite_threshold": 0,    # >= 0.651
                "meets_confidence_threshold": 0,   # >= 0.6
                "meets_all_thresholds": 0
            }
        }
        
        for opp in opportunities:
            # Analyser par recommandation
            rec = opp.recommendation
            if rec not in results_analysis["by_recommendation"]:
                results_analysis["by_recommendation"][rec] = 0
            results_analysis["by_recommendation"][rec] += 1
            
            # Analyser par niveau de risque
            risk = opp.risk_level
            if risk not in results_analysis["by_risk_level"]:
                results_analysis["by_risk_level"][risk] = 0
            results_analysis["by_risk_level"][risk] += 1
            
            # Collecter les scores
            if opp.composite_score:
                results_analysis["score_analysis"]["composite_scores"].append(float(opp.composite_score))
            if opp.technical_score:
                results_analysis["score_analysis"]["technical_scores"].append(float(opp.technical_score))
            if opp.confidence_level:
                results_analysis["score_analysis"]["confidence_scores"].append(float(opp.confidence_level))
            
            # Vérifier la conformité aux seuils optimisés
            if opp.technical_score and float(opp.technical_score) >= 0.533:
                results_analysis["optimization_compliance"]["meets_technical_threshold"] += 1
            
            if opp.composite_score and float(opp.composite_score) >= 0.651:
                results_analysis["optimization_compliance"]["meets_composite_threshold"] += 1
            
            if opp.confidence_level and float(opp.confidence_level) >= 0.6:
                results_analysis["optimization_compliance"]["meets_confidence_threshold"] += 1
            
            # Vérifier si toutes les conditions sont remplies
            if (opp.technical_score and float(opp.technical_score) >= 0.533 and
                opp.composite_score and float(opp.composite_score) >= 0.651 and
                opp.confidence_level and float(opp.confidence_level) >= 0.6):
                results_analysis["optimization_compliance"]["meets_all_thresholds"] += 1
        
        # Calculer les statistiques des scores
        for score_type in ["composite_scores", "technical_scores", "confidence_scores"]:
            scores = results_analysis["score_analysis"][score_type]
            if scores:
                results_analysis["score_analysis"][score_type] = {
                    "min": min(scores),
                    "max": max(scores),
                    "avg": sum(scores) / len(scores),
                    "count": len(scores)
                }
        
        return results_analysis
    
    def run_complete_test(self) -> Dict[str, Any]:
        """Exécute le test complet"""
        print("🚀 Démarrage du test de la recherche frontend avec optimisations")
        print("=" * 80)
        
        # Vérifier les opportunités récentes
        recent_analysis = self.check_recent_opportunities()
        
        # Simuler une recherche frontend
        search_analysis = self.simulate_frontend_search()
        
        # Analyser si les optimisations sont actives
        optimization_status = {
            "recent_opportunities_analysis": recent_analysis,
            "frontend_search_simulation": search_analysis,
            "optimization_active": False,
            "recommendations": []
        }
        
        # Vérifier si les optimisations sont actives
        if (recent_analysis["optimization_indicators"]["optimized_opportunities"] > 0 or
            search_analysis["optimization_compliance"]["meets_all_thresholds"] > 0):
            optimization_status["optimization_active"] = True
            optimization_status["recommendations"].append("✅ Les optimisations sont actives")
        else:
            optimization_status["recommendations"].append("⚠️ Les optimisations ne semblent pas actives")
        
        # Analyser la qualité des opportunités
        if search_analysis["optimization_compliance"]["meets_all_thresholds"] > 0:
            optimization_status["recommendations"].append(
                f"✅ {search_analysis['optimization_compliance']['meets_all_thresholds']} opportunités respectent tous les seuils optimisés"
            )
        
        if search_analysis["optimization_compliance"]["meets_technical_threshold"] > 0:
            optimization_status["recommendations"].append(
                f"✅ {search_analysis['optimization_compliance']['meets_technical_threshold']} opportunités respectent le seuil technique (≥0.533)"
            )
        
        return optimization_status
    
    def print_summary(self, results: Dict[str, Any]):
        """Affiche un résumé des résultats"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DU TEST DE LA RECHERCHE FRONTEND")
        print("=" * 80)
        
        # Analyse des opportunités récentes
        recent = results["recent_opportunities_analysis"]
        print(f"📈 OPPORTUNITÉS RÉCENTES (7 derniers jours): {recent['total_recent']}")
        
        if recent["total_recent"] > 0:
            print(f"  • Par recommandation: {recent['by_recommendation']}")
            print(f"  • Par niveau de risque: {recent['by_risk_level']}")
            
            # Scores moyens
            if recent["score_ranges"]["composite_score"]["avg"]:
                print(f"  • Score composite moyen: {recent['score_ranges']['composite_score']['avg']:.3f}")
            if recent["score_ranges"]["technical_score"]["avg"]:
                print(f"  • Score technique moyen: {recent['score_ranges']['technical_score']['avg']:.3f}")
            if recent["score_ranges"]["confidence_level"]["avg"]:
                print(f"  • Niveau de confiance moyen: {recent['score_ranges']['confidence_level']['avg']:.3f}")
            
            # Indicateurs d'optimisation
            opt_indicators = recent["optimization_indicators"]
            print(f"  • Opportunités avec score technique ≥0.533: {opt_indicators['high_technical_score_count']}")
            print(f"  • Opportunités avec score composite ≥0.651: {opt_indicators['high_composite_score_count']}")
            print(f"  • Opportunités avec confiance ≥0.6: {opt_indicators['high_confidence_count']}")
            print(f"  • Opportunités optimisées (tous seuils): {opt_indicators['optimized_opportunities']}")
        
        # Simulation de recherche frontend
        search = results["frontend_search_simulation"]
        print(f"\n🔍 SIMULATION RECHERCHE FRONTEND: {search['total_found']} opportunités")
        
        if search["total_found"] > 0:
            print(f"  • Par recommandation: {search['by_recommendation']}")
            print(f"  • Par niveau de risque: {search['by_risk_level']}")
            
            # Analyse des scores
            score_analysis = search["score_analysis"]
            if "composite_scores" in score_analysis and isinstance(score_analysis["composite_scores"], dict):
                print(f"  • Score composite: min={score_analysis['composite_scores']['min']:.3f}, max={score_analysis['composite_scores']['max']:.3f}, avg={score_analysis['composite_scores']['avg']:.3f}")
            if "technical_scores" in score_analysis and isinstance(score_analysis["technical_scores"], dict):
                print(f"  • Score technique: min={score_analysis['technical_scores']['min']:.3f}, max={score_analysis['technical_scores']['max']:.3f}, avg={score_analysis['technical_scores']['avg']:.3f}")
            if "confidence_scores" in score_analysis and isinstance(score_analysis["confidence_scores"], dict):
                print(f"  • Niveau de confiance: min={score_analysis['confidence_scores']['min']:.3f}, max={score_analysis['confidence_scores']['max']:.3f}, avg={score_analysis['confidence_scores']['avg']:.3f}")
            
            # Conformité aux optimisations
            compliance = search["optimization_compliance"]
            print(f"  • Respecte seuil technique (≥0.533): {compliance['meets_technical_threshold']}")
            print(f"  • Respecte seuil composite (≥0.651): {compliance['meets_composite_threshold']}")
            print(f"  • Respecte seuil confiance (≥0.6): {compliance['meets_confidence_threshold']}")
            print(f"  • Respecte tous les seuils: {compliance['meets_all_thresholds']}")
        
        # Statut des optimisations
        print(f"\n🎯 STATUT DES OPTIMISATIONS: {'ACTIVES' if results['optimization_active'] else 'INACTIVES'}")
        
        # Recommandations
        if results["recommendations"]:
            print(f"\n💡 RECOMMANDATIONS:")
            for rec in results["recommendations"]:
                print(f"  • {rec}")

def main():
    """Fonction principale"""
    tester = FrontendSearchOptimizationTester()
    
    try:
        # Exécuter le test complet
        results = tester.run_complete_test()
        
        # Afficher le résumé
        tester.print_summary(results)
        
        # Sauvegarder les résultats
        filename = "frontend_search_optimization_test.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📁 Résultats sauvegardés dans {filename}")
        print(f"\n✅ Test terminé avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        del tester

if __name__ == "__main__":
    main()
