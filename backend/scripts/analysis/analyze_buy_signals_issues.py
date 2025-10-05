#!/usr/bin/env python3
"""
Script pour analyser les problèmes des signaux d'achat
Identifie les causes des retours négatifs et propose des solutions
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


class BuySignalsAnalyzer:
    """
    Analyseur des problèmes des signaux d'achat
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger(__name__)
    
    def analyze_buy_signals_issues(self) -> Dict[str, Any]:
        """
        Analyse en profondeur les problèmes des signaux d'achat
        """
        try:
            self.logger.info("🔍 Analyse approfondie des problèmes des signaux d'achat")
            
            # Récupérer tous les signaux d'achat
            buy_opportunities = self.db.query(HistoricalOpportunities).filter(
                HistoricalOpportunities.recommendation.in_(['BUY_WEAK', 'BUY_MODERATE', 'BUY_STRONG'])
            ).all()
            
            if not buy_opportunities:
                return {"error": "Aucun signal d'achat trouvé"}
            
            # Analyser les patterns de performance
            performance_analysis = self._analyze_performance_patterns(buy_opportunities)
            
            # Analyser les corrélations avec les scores
            correlation_analysis = self._analyze_score_correlations(buy_opportunities)
            
            # Analyser les patterns temporels
            temporal_analysis = self._analyze_temporal_patterns(buy_opportunities)
            
            # Analyser les patterns de volatilité
            volatility_analysis = self._analyze_volatility_patterns(buy_opportunities)
            
            # Identifier les opportunités manquées
            missed_opportunities = self._identify_missed_opportunities(buy_opportunities)
            
            return {
                "performance_analysis": performance_analysis,
                "correlation_analysis": correlation_analysis,
                "temporal_analysis": temporal_analysis,
                "volatility_analysis": volatility_analysis,
                "missed_opportunities": missed_opportunities,
                "total_buy_signals": len(buy_opportunities)
            }
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse des problèmes: {e}")
            return {"error": str(e)}
    
    def _analyze_performance_patterns(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse les patterns de performance des signaux d'achat"""
        
        patterns = {
            "positive_returns": [],
            "negative_returns": [],
            "zero_returns": [],
            "extreme_positive": [],
            "extreme_negative": [],
            "by_recommendation_type": {}
        }
        
        for opp in opportunities:
            if opp.return_1_day is None:
                continue
            
            return_1d = float(opp.return_1_day)
            rec_type = opp.recommendation
            
            # Catégoriser les retours
            if return_1d > 0:
                patterns["positive_returns"].append(return_1d)
            elif return_1d < 0:
                patterns["negative_returns"].append(return_1d)
            else:
                patterns["zero_returns"].append(return_1d)
            
            # Retours extrêmes
            if return_1d > 0.05:  # > 5%
                patterns["extreme_positive"].append(return_1d)
            elif return_1d < -0.05:  # < -5%
                patterns["extreme_negative"].append(return_1d)
            
            # Par type de recommandation
            if rec_type not in patterns["by_recommendation_type"]:
                patterns["by_recommendation_type"][rec_type] = {
                    "positive": [],
                    "negative": [],
                    "count": 0
                }
            
            patterns["by_recommendation_type"][rec_type]["count"] += 1
            
            if return_1d > 0:
                patterns["by_recommendation_type"][rec_type]["positive"].append(return_1d)
            else:
                patterns["by_recommendation_type"][rec_type]["negative"].append(return_1d)
        
        # Calculer les statistiques
        if patterns["positive_returns"]:
            patterns["avg_positive_return"] = np.mean(patterns["positive_returns"])
            patterns["std_positive_return"] = np.std(patterns["positive_returns"])
        
        if patterns["negative_returns"]:
            patterns["avg_negative_return"] = np.mean(patterns["negative_returns"])
            patterns["std_negative_return"] = np.std(patterns["negative_returns"])
        
        patterns["positive_rate"] = len(patterns["positive_returns"]) / (len(patterns["positive_returns"]) + len(patterns["negative_returns"])) if (patterns["positive_returns"] or patterns["negative_returns"]) else 0
        
        return patterns
    
    def _analyze_score_correlations(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse les corrélations entre les scores et les performances"""
        
        correlations = {
            "composite_score_vs_return": [],
            "confidence_vs_return": [],
            "technical_score_vs_return": [],
            "sentiment_score_vs_return": [],
            "market_score_vs_return": []
        }
        
        for opp in opportunities:
            if opp.return_1_day is None:
                continue
            
            return_1d = float(opp.return_1_day)
            
            # Corrélations avec les scores
            if opp.composite_score is not None:
                correlations["composite_score_vs_return"].append((float(opp.composite_score), return_1d))
            
            if opp.confidence_level is not None:
                correlations["confidence_vs_return"].append((float(opp.confidence_level), return_1d))
            
            if opp.technical_score is not None:
                correlations["technical_score_vs_return"].append((float(opp.technical_score), return_1d))
            
            if opp.sentiment_score is not None:
                correlations["sentiment_score_vs_return"].append((float(opp.sentiment_score), return_1d))
            
            if opp.market_score is not None:
                correlations["market_score_vs_return"].append((float(opp.market_score), return_1d))
        
        # Calculer les corrélations
        for key, data in correlations.items():
            if len(data) > 1:
                scores, returns = zip(*data)
                correlation = np.corrcoef(scores, returns)[0, 1]
                correlations[key] = {
                    "correlation": correlation,
                    "data_points": len(data),
                    "avg_score": np.mean(scores),
                    "avg_return": np.mean(returns)
                }
            else:
                correlations[key] = {"correlation": 0, "data_points": 0}
        
        return correlations
    
    def _analyze_temporal_patterns(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse les patterns temporels des signaux d'achat"""
        
        temporal = {
            "by_month": {},
            "by_weekday": {},
            "by_hour": {},
            "trend_analysis": {}
        }
        
        for opp in opportunities:
            if opp.return_1_day is None or opp.opportunity_date is None:
                continue
            
            return_1d = float(opp.return_1_day)
            date = opp.opportunity_date
            
            # Par mois
            month_key = f"{date.year}-{date.month:02d}"
            if month_key not in temporal["by_month"]:
                temporal["by_month"][month_key] = []
            temporal["by_month"][month_key].append(return_1d)
            
            # Par jour de la semaine
            weekday = date.weekday()
            if weekday not in temporal["by_weekday"]:
                temporal["by_weekday"][weekday] = []
            temporal["by_weekday"][weekday].append(return_1d)
        
        # Calculer les statistiques temporelles
        for period, data in temporal.items():
            if period != "trend_analysis" and data:
                for key, returns in data.items():
                    if returns:
                        temporal[period][key] = {
                            "avg_return": np.mean(returns),
                            "std_return": np.std(returns),
                            "count": len(returns),
                            "positive_rate": np.sum(np.array(returns) > 0) / len(returns)
                        }
        
        return temporal
    
    def _analyze_volatility_patterns(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse les patterns de volatilité des signaux d'achat"""
        
        volatility = {
            "high_volatility": [],
            "low_volatility": [],
            "volatility_vs_return": []
        }
        
        for opp in opportunities:
            if opp.return_1_day is None or opp.price_at_generation is None:
                continue
            
            return_1d = float(opp.return_1_day)
            price = float(opp.price_at_generation)
            
            # Simuler la volatilité (en réalité, on devrait la calculer)
            # Pour l'instant, on utilise une approximation basée sur le prix
            estimated_volatility = price * 0.02  # 2% du prix
            
            volatility["volatility_vs_return"].append((estimated_volatility, return_1d))
            
            # Catégoriser par volatilité
            if estimated_volatility > price * 0.03:  # > 3%
                volatility["high_volatility"].append(return_1d)
            else:
                volatility["low_volatility"].append(return_1d)
        
        # Calculer les statistiques de volatilité
        if volatility["high_volatility"]:
            volatility["high_vol_avg_return"] = np.mean(volatility["high_volatility"])
            volatility["high_vol_positive_rate"] = np.sum(np.array(volatility["high_volatility"]) > 0) / len(volatility["high_volatility"])
        
        if volatility["low_volatility"]:
            volatility["low_vol_avg_return"] = np.mean(volatility["low_volatility"])
            volatility["low_vol_positive_rate"] = np.sum(np.array(volatility["low_volatility"]) > 0) / len(volatility["low_volatility"])
        
        return volatility
    
    def _identify_missed_opportunities(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Identifie les opportunités manquées (signaux non générés)"""
        
        missed = {
            "high_return_opportunities": [],
            "strong_signals_missed": [],
            "timing_issues": []
        }
        
        # Analyser les opportunités avec de forts retours positifs
        for opp in opportunities:
            if opp.return_1_day is not None:
                return_1d = float(opp.return_1_day)
                
                # Opportunités avec de forts retours positifs
                if return_1d > 0.03:  # > 3%
                    missed["high_return_opportunities"].append({
                        "symbol": opp.symbol,
                        "date": opp.opportunity_date.isoformat() if opp.opportunity_date else None,
                        "return_1d": return_1d,
                        "composite_score": float(opp.composite_score) if opp.composite_score else None,
                        "confidence": float(opp.confidence_level) if opp.confidence_level else None
                    })
        
        return missed
    
    def generate_improvement_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Génère des recommandations d'amélioration basées sur l'analyse"""
        
        recommendations = []
        
        # Analyser les patterns de performance
        perf_analysis = analysis_results.get("performance_analysis", {})
        positive_rate = perf_analysis.get("positive_rate", 0)
        
        if positive_rate < 0.4:
            recommendations.append("❌ Taux de réussite très faible (< 40%) - Revoir les critères de sélection")
        elif positive_rate < 0.5:
            recommendations.append("⚠️ Taux de réussite faible (< 50%) - Optimiser les seuils de décision")
        else:
            recommendations.append("✅ Taux de réussite acceptable")
        
        # Analyser les corrélations
        corr_analysis = analysis_results.get("correlation_analysis", {})
        composite_corr = corr_analysis.get("composite_score_vs_return", {}).get("correlation", 0)
        
        if composite_corr < 0.1:
            recommendations.append("❌ Corrélation faible entre score composite et performance - Revoir la formule de scoring")
        elif composite_corr < 0.3:
            recommendations.append("⚠️ Corrélation modérée - Améliorer la pondération des indicateurs")
        else:
            recommendations.append("✅ Bonne corrélation entre score et performance")
        
        # Analyser les opportunités manquées
        missed_opps = analysis_results.get("missed_opportunities", {})
        high_return_count = len(missed_opps.get("high_return_opportunities", []))
        
        if high_return_count > 0:
            recommendations.append(f"💡 {high_return_count} opportunités à fort retour identifiées - Analyser les patterns")
        
        # Recommandations spécifiques
        recommendations.extend([
            "🔧 Implémenter des filtres de qualité plus stricts",
            "📊 Ajuster les poids des indicateurs techniques",
            "⏰ Optimiser le timing des signaux",
            "🛡️ Améliorer la gestion du risque",
            "🎯 Réduire les faux positifs avec des validations supplémentaires"
        ])
        
        return recommendations


def main():
    """Fonction principale pour analyser les problèmes des signaux d'achat"""
    logger.info("🚀 Démarrage de l'analyse des problèmes des signaux d'achat")
    
    try:
        # Connexion à la base de données
        db = SessionLocal()
        
        # Initialiser l'analyseur
        analyzer = BuySignalsAnalyzer(db)
        
        # Exécuter l'analyse
        logger.info("🔍 Analyse des problèmes...")
        analysis_results = analyzer.analyze_buy_signals_issues()
        
        if "error" in analysis_results:
            logger.error(f"❌ Erreur lors de l'analyse: {analysis_results['error']}")
            return
        
        # Générer les recommandations
        logger.info("💡 Génération des recommandations...")
        recommendations = analyzer.generate_improvement_recommendations(analysis_results)
        
        # Afficher les résultats
        print("\n" + "="*80)
        print("🔍 ANALYSE DES PROBLÈMES DES SIGNAUX D'ACHAT")
        print("="*80)
        
        print(f"\n📊 SIGNAUX D'ACHAT ANALYSÉS: {analysis_results['total_buy_signals']}")
        
        # Patterns de performance
        perf_analysis = analysis_results.get("performance_analysis", {})
        print(f"\n📈 PATTERNS DE PERFORMANCE:")
        print(f"  • Taux de réussite: {perf_analysis.get('positive_rate', 0):.1%}")
        print(f"  • Retour moyen positif: {perf_analysis.get('avg_positive_return', 0):.2%}")
        print(f"  • Retour moyen négatif: {perf_analysis.get('avg_negative_return', 0):.2%}")
        
        # Corrélations
        corr_analysis = analysis_results.get("correlation_analysis", {})
        print(f"\n🔗 CORRÉLATIONS:")
        for key, data in corr_analysis.items():
            if isinstance(data, dict) and "correlation" in data:
                print(f"  • {key}: {data['correlation']:.3f} ({data['data_points']} points)")
        
        # Opportunités manquées
        missed_opps = analysis_results.get("missed_opportunities", {})
        high_return_count = len(missed_opps.get("high_return_opportunities", []))
        print(f"\n💎 OPPORTUNITÉS À FORT RETOUR: {high_return_count}")
        
        print(f"\n💡 RECOMMANDATIONS D'AMÉLIORATION:")
        for rec in recommendations:
            print(f"  • {rec}")
        
        # Sauvegarder les résultats
        results = {
            "analysis_results": analysis_results,
            "recommendations": recommendations,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        with open("/Users/loiclinais/Documents/dev/aimarkets/backend/scripts/buy_signals_issues_analysis.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("📁 Résultats sauvegardés dans buy_signals_issues_analysis.json")
        logger.info("✅ Analyse des problèmes terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse: {e}")
        return


if __name__ == "__main__":
    main()
