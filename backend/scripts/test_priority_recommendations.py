#!/usr/bin/env python3
"""
Script pour tester les 3 recommandations prioritaires implémentées
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any
import numpy as np
import pandas as pd
from collections import defaultdict
import json

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.historical_opportunities import HistoricalOpportunities

class PriorityRecommendationsTester:
    """Testeur des recommandations prioritaires"""
    
    def __init__(self):
        """Initialise le testeur"""
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        
    def __del__(self):
        """Ferme la session de base de données"""
        if hasattr(self, 'db'):
            self.db.close()
    
    def get_all_buy_opportunities(self) -> List[HistoricalOpportunities]:
        """Récupère toutes les opportunités d'achat avec validation"""
        print("📊 Récupération de toutes les opportunités d'achat...")
        
        opportunities = self.db.query(HistoricalOpportunities).filter(
            and_(
                HistoricalOpportunities.recommendation.in_(['BUY', 'BUY_WEAK', 'BUY_MODERATE', 'BUY_STRONG']),
                HistoricalOpportunities.return_1_day.isnot(None),
                HistoricalOpportunities.technical_score.isnot(None),
                HistoricalOpportunities.composite_score.isnot(None),
                HistoricalOpportunities.confidence_level.isnot(None)
            )
        ).all()
        
        print(f"📈 Trouvé {len(opportunities)} opportunités d'achat avec validation")
        return opportunities
    
    def calculate_performance_metrics(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, float]:
        """Calcule les métriques de performance pour un ensemble d'opportunités"""
        if not opportunities:
            return {
                'count': 0,
                'success_rate': 0.0,
                'avg_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_return': 0.0,
                'min_return': 0.0,
                'std_return': 0.0
            }
        
        returns = [float(opp.return_1_day) for opp in opportunities if opp.return_1_day is not None]
        
        if not returns:
            return {
                'count': len(opportunities),
                'success_rate': 0.0,
                'avg_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_return': 0.0,
                'min_return': 0.0,
                'std_return': 0.0
            }
        
        success_rate = len([r for r in returns if r > 0]) / len(returns)
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        sharpe_ratio = avg_return / std_return if std_return > 0 else 0.0
        
        return {
            'count': len(opportunities),
            'success_rate': success_rate,
            'avg_return': avg_return,
            'sharpe_ratio': sharpe_ratio,
            'max_return': np.max(returns),
            'min_return': np.min(returns),
            'std_return': std_return
        }
    
    def test_priority_optimized_scoring(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Teste le scoring optimisé avec priorité au score technique"""
        print("⚖️ Test du scoring optimisé avec priorité technique...")
        
        if not opportunities:
            return {"error": "Aucune opportunité à analyser"}
        
        # Poids optimisés - priorité au score technique
        TECH_WEIGHT = 0.8
        SENTIMENT_WEIGHT = 0.1
        MARKET_WEIGHT = 0.1
        
        # Calculer les scores composites optimisés
        optimized_scores = []
        for opp in opportunities:
            if (opp.technical_score is not None and 
                opp.sentiment_score is not None and
                opp.market_score is not None and
                opp.return_1_day is not None):
                
                tech_score = float(opp.technical_score)
                sent_score = float(opp.sentiment_score)
                market_score = float(opp.market_score)
                return_1d = float(opp.return_1_day)
                
                # Score composite optimisé avec priorité technique
                optimized_composite = (
                    TECH_WEIGHT * tech_score +
                    SENTIMENT_WEIGHT * sent_score +
                    MARKET_WEIGHT * market_score
                )
                
                optimized_scores.append({
                    'optimized_composite': optimized_composite,
                    'original_composite': float(opp.composite_score) if opp.composite_score else 0,
                    'return_1_day': return_1d,
                    'technical_score': tech_score,
                    'sentiment_score': sent_score,
                    'market_score': market_score
                })
        
        if not optimized_scores:
            return {"error": "Aucune donnée valide"}
        
        df = pd.DataFrame(optimized_scores)
        
        # Calculer les corrélations
        optimized_correlation = df['optimized_composite'].corr(df['return_1_day'])
        original_correlation = df['original_composite'].corr(df['return_1_day'])
        
        # Analyser les performances par quartile
        optimized_quartiles = pd.qcut(df['optimized_composite'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
        original_quartiles = pd.qcut(df['original_composite'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
        
        optimized_quartile_performance = {}
        original_quartile_performance = {}
        
        for q in ['Q1', 'Q2', 'Q3', 'Q4']:
            # Performance avec score optimisé
            q_data_opt = df[optimized_quartiles == q]
            if len(q_data_opt) > 0:
                optimized_quartile_performance[q] = {
                    'count': len(q_data_opt),
                    'avg_return': float(q_data_opt['return_1_day'].mean()),
                    'success_rate': float((q_data_opt['return_1_day'] > 0).mean())
                }
            
            # Performance avec score original
            q_data_orig = df[original_quartiles == q]
            if len(q_data_orig) > 0:
                original_quartile_performance[q] = {
                    'count': len(q_data_orig),
                    'avg_return': float(q_data_orig['return_1_day'].mean()),
                    'success_rate': float((q_data_orig['return_1_day'] > 0).mean())
                }
        
        return {
            'optimized_weights': {
                'technical_weight': TECH_WEIGHT,
                'sentiment_weight': SENTIMENT_WEIGHT,
                'market_weight': MARKET_WEIGHT
            },
            'correlations': {
                'optimized_composite': float(optimized_correlation),
                'original_composite': float(original_correlation),
                'improvement': float(optimized_correlation - original_correlation)
            },
            'quartile_performance': {
                'optimized': optimized_quartile_performance,
                'original': original_quartile_performance
            }
        }
    
    def test_priority_optimized_thresholds(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Teste les seuils optimisés avec validation des signaux"""
        print("🔧 Test des seuils optimisés avec validation...")
        
        if not opportunities:
            return {"error": "Aucune opportunité à analyser"}
        
        # Seuils optimisés
        TECH_THRESHOLD = 0.533
        COMP_THRESHOLD = 0.651
        CONF_THRESHOLD = 0.6
        
        # Filtrer les opportunités selon les seuils optimisés
        optimized_opps = []
        validation_results = []
        
        for opp in opportunities:
            if (opp.technical_score is not None and 
                opp.composite_score is not None and
                opp.confidence_level is not None):
                
                tech_score = float(opp.technical_score)
                comp_score = float(opp.composite_score)
                conf_level = float(opp.confidence_level)
                
                # Validation des signaux optimisés
                tech_valid = tech_score >= TECH_THRESHOLD
                comp_valid = comp_score >= COMP_THRESHOLD
                conf_valid = conf_level >= CONF_THRESHOLD
                
                # Validation globale : au moins 2 critères sur 3
                overall_valid = sum([tech_valid, comp_valid, conf_valid]) >= 2
                
                validation_results.append({
                    'symbol': opp.symbol,
                    'technical_score': tech_score,
                    'composite_score': comp_score,
                    'confidence_level': conf_level,
                    'tech_valid': tech_valid,
                    'comp_valid': comp_valid,
                    'conf_valid': conf_valid,
                    'overall_valid': overall_valid,
                    'return_1_day': float(opp.return_1_day) if opp.return_1_day else 0
                })
                
                if overall_valid:
                    optimized_opps.append(opp)
        
        # Calculer les métriques pour les opportunités optimisées
        optimized_metrics = self.calculate_performance_metrics(optimized_opps)
        
        # Comparer avec toutes les opportunités
        all_metrics = self.calculate_performance_metrics(opportunities)
        
        # Analyser les résultats de validation
        validation_df = pd.DataFrame(validation_results)
        validation_stats = {
            'total_opportunities': len(validation_results),
            'tech_valid_count': validation_df['tech_valid'].sum(),
            'comp_valid_count': validation_df['comp_valid'].sum(),
            'conf_valid_count': validation_df['conf_valid'].sum(),
            'overall_valid_count': validation_df['overall_valid'].sum(),
            'tech_valid_rate': validation_df['tech_valid'].mean(),
            'comp_valid_rate': validation_df['comp_valid'].mean(),
            'conf_valid_rate': validation_df['conf_valid'].mean(),
            'overall_valid_rate': validation_df['overall_valid'].mean()
        }
        
        return {
            'optimized_thresholds': {
                'technical_threshold': TECH_THRESHOLD,
                'composite_threshold': COMP_THRESHOLD,
                'confidence_threshold': CONF_THRESHOLD
            },
            'optimized_opportunities': optimized_metrics,
            'all_opportunities': all_metrics,
            'validation_stats': validation_stats,
            'improvement': {
                'success_rate_improvement': optimized_metrics['success_rate'] - all_metrics['success_rate'],
                'avg_return_improvement': optimized_metrics['avg_return'] - all_metrics['avg_return'],
                'sharpe_ratio_improvement': optimized_metrics['sharpe_ratio'] - all_metrics['sharpe_ratio']
            }
        }
    
    def test_priority_optimized_filtering(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Teste le filtrage optimisé complet"""
        print("🔍 Test du filtrage optimisé complet...")
        
        if not opportunities:
            return {"error": "Aucune opportunité à analyser"}
        
        # Seuils optimisés
        TECH_THRESHOLD = 0.533
        COMP_THRESHOLD = 0.651
        CONF_THRESHOLD = 0.6
        
        # Poids optimisés
        TECH_WEIGHT = 0.8
        SENTIMENT_WEIGHT = 0.1
        MARKET_WEIGHT = 0.1
        
        # Appliquer le filtrage complet
        filtered_opps = []
        filtering_results = []
        
        for opp in opportunities:
            if (opp.technical_score is not None and 
                opp.sentiment_score is not None and
                opp.market_score is not None and
                opp.composite_score is not None and
                opp.confidence_level is not None):
                
                tech_score = float(opp.technical_score)
                sent_score = float(opp.sentiment_score)
                market_score = float(opp.market_score)
                comp_score = float(opp.composite_score)
                conf_level = float(opp.confidence_level)
                
                # Score composite optimisé
                optimized_composite = (
                    TECH_WEIGHT * tech_score +
                    SENTIMENT_WEIGHT * sent_score +
                    MARKET_WEIGHT * market_score
                )
                
                # Validation des seuils
                tech_valid = tech_score >= TECH_THRESHOLD
                comp_valid = optimized_composite >= COMP_THRESHOLD
                conf_valid = conf_level >= CONF_THRESHOLD
                
                # Validation globale
                overall_valid = sum([tech_valid, comp_valid, conf_valid]) >= 2
                
                filtering_results.append({
                    'symbol': opp.symbol,
                    'technical_score': tech_score,
                    'sentiment_score': sent_score,
                    'market_score': market_score,
                    'original_composite': comp_score,
                    'optimized_composite': optimized_composite,
                    'confidence_level': conf_level,
                    'tech_valid': tech_valid,
                    'comp_valid': comp_valid,
                    'conf_valid': conf_valid,
                    'overall_valid': overall_valid,
                    'return_1_day': float(opp.return_1_day) if opp.return_1_day else 0
                })
                
                if overall_valid:
                    filtered_opps.append(opp)
        
        # Calculer les métriques
        filtered_metrics = self.calculate_performance_metrics(filtered_opps)
        all_metrics = self.calculate_performance_metrics(opportunities)
        
        return {
            'filtering_results': filtering_results,
            'filtered_opportunities': filtered_metrics,
            'all_opportunities': all_metrics,
            'filtering_stats': {
                'total_opportunities': len(opportunities),
                'filtered_opportunities': len(filtered_opps),
                'filtering_rate': len(filtered_opps) / len(opportunities) if opportunities else 0
            },
            'improvement': {
                'success_rate_improvement': filtered_metrics['success_rate'] - all_metrics['success_rate'],
                'avg_return_improvement': filtered_metrics['avg_return'] - all_metrics['avg_return'],
                'sharpe_ratio_improvement': filtered_metrics['sharpe_ratio'] - all_metrics['sharpe_ratio']
            }
        }
    
    def run_complete_test(self) -> Dict[str, Any]:
        """Exécute le test complet des recommandations prioritaires"""
        print("🚀 Démarrage du test des recommandations prioritaires")
        print("=" * 80)
        
        # Récupérer toutes les opportunités d'achat
        opportunities = self.get_all_buy_opportunities()
        
        if not opportunities:
            return {"error": "Aucune opportunité d'achat trouvée"}
        
        # Exécuter tous les tests
        results = {
            "test_date": datetime.now().isoformat(),
            "total_opportunities": len(opportunities),
            "priority_optimized_scoring_test": self.test_priority_optimized_scoring(opportunities),
            "priority_optimized_thresholds_test": self.test_priority_optimized_thresholds(opportunities),
            "priority_optimized_filtering_test": self.test_priority_optimized_filtering(opportunities)
        }
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Affiche un résumé des résultats de test"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DU TEST DES RECOMMANDATIONS PRIORITAIRES")
        print("=" * 80)
        
        if "error" in results:
            print(f"❌ Erreur: {results['error']}")
            return
        
        print(f"📈 OPPORTUNITÉS TESTÉES: {results['total_opportunities']}")
        
        # Test du scoring optimisé
        if "priority_optimized_scoring_test" in results:
            scoring_test = results["priority_optimized_scoring_test"]
            if "error" not in scoring_test:
                print(f"\n⚖️ TEST DU SCORING OPTIMISÉ:")
                print(f"  • Poids technique: {scoring_test['optimized_weights']['technical_weight']:.1f}")
                print(f"  • Poids sentiment: {scoring_test['optimized_weights']['sentiment_weight']:.1f}")
                print(f"  • Poids marché: {scoring_test['optimized_weights']['market_weight']:.1f}")
                
                corr = scoring_test['correlations']
                print(f"  • Corrélation optimisée: {corr['optimized_composite']:.3f}")
                print(f"  • Corrélation originale: {corr['original_composite']:.3f}")
                print(f"  • Amélioration corrélation: {corr['improvement']:+.3f}")
        
        # Test des seuils optimisés
        if "priority_optimized_thresholds_test" in results:
            thresh_test = results["priority_optimized_thresholds_test"]
            if "error" not in thresh_test:
                print(f"\n🔧 TEST DES SEUILS OPTIMISÉS:")
                print(f"  • Seuil technique: {thresh_test['optimized_thresholds']['technical_threshold']:.3f}")
                print(f"  • Seuil composite: {thresh_test['optimized_thresholds']['composite_threshold']:.3f}")
                print(f"  • Seuil confiance: {thresh_test['optimized_thresholds']['confidence_threshold']:.3f}")
                
                opt_metrics = thresh_test['optimized_opportunities']
                all_metrics = thresh_test['all_opportunities']
                improvement = thresh_test['improvement']
                
                print(f"  • Opportunités filtrées: {opt_metrics['count']} / {all_metrics['count']}")
                print(f"  • Taux de succès: {opt_metrics['success_rate']:.1%} (vs {all_metrics['success_rate']:.1%})")
                print(f"  • Retour moyen: {opt_metrics['avg_return']:.3f} (vs {all_metrics['avg_return']:.3f})")
                print(f"  • Sharpe ratio: {opt_metrics['sharpe_ratio']:.3f} (vs {all_metrics['sharpe_ratio']:.3f})")
                print(f"  • Amélioration taux de succès: {improvement['success_rate_improvement']:+.1%}")
                print(f"  • Amélioration retour moyen: {improvement['avg_return_improvement']:+.3f}")
                print(f"  • Amélioration Sharpe ratio: {improvement['sharpe_ratio_improvement']:+.3f}")
        
        # Test du filtrage optimisé
        if "priority_optimized_filtering_test" in results:
            filter_test = results["priority_optimized_filtering_test"]
            if "error" not in filter_test:
                print(f"\n🔍 TEST DU FILTRAGE OPTIMISÉ:")
                filter_stats = filter_test['filtering_stats']
                print(f"  • Opportunités totales: {filter_stats['total_opportunities']}")
                print(f"  • Opportunités filtrées: {filter_stats['filtered_opportunities']}")
                print(f"  • Taux de filtrage: {filter_stats['filtering_rate']:.1%}")
                
                filtered_metrics = filter_test['filtered_opportunities']
                all_metrics = filter_test['all_opportunities']
                improvement = filter_test['improvement']
                
                print(f"  • Taux de succès filtré: {filtered_metrics['success_rate']:.1%} (vs {all_metrics['success_rate']:.1%})")
                print(f"  • Retour moyen filtré: {filtered_metrics['avg_return']:.3f} (vs {all_metrics['avg_return']:.3f})")
                print(f"  • Sharpe ratio filtré: {filtered_metrics['sharpe_ratio']:.3f} (vs {all_metrics['sharpe_ratio']:.3f})")
                print(f"  • Amélioration taux de succès: {improvement['success_rate_improvement']:+.1%}")
                print(f"  • Amélioration retour moyen: {improvement['avg_return_improvement']:+.3f}")
                print(f"  • Amélioration Sharpe ratio: {improvement['sharpe_ratio_improvement']:+.3f}")

def main():
    """Fonction principale"""
    tester = PriorityRecommendationsTester()
    
    try:
        # Exécuter le test complet
        results = tester.run_complete_test()
        
        # Afficher le résumé
        tester.print_summary(results)
        
        # Sauvegarder les résultats
        filename = "priority_recommendations_test.json"
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
