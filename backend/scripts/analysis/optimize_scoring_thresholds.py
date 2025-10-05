#!/usr/bin/env python3
"""
Script pour optimiser les seuils du score technique et du score composite
pour améliorer les performances des opportunités
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from collections import defaultdict
import json
from itertools import product

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.historical_opportunities import HistoricalOpportunities

class ScoringThresholdsOptimizer:
    """Optimiseur des seuils de scoring"""
    
    def __init__(self):
        """Initialise l'optimiseur"""
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
                HistoricalOpportunities.composite_score.isnot(None)
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
    
    def optimize_technical_score_threshold(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Optimise le seuil du score technique"""
        print("🔧 Optimisation du seuil du score technique...")
        
        if not opportunities:
            return {"error": "Aucune opportunité à analyser"}
        
        # Extraire les scores techniques et retours
        data = []
        for opp in opportunities:
            if opp.technical_score is not None and opp.return_1_day is not None:
                data.append({
                    'technical_score': float(opp.technical_score),
                    'return_1_day': float(opp.return_1_day)
                })
        
        if not data:
            return {"error": "Aucune donnée valide"}
        
        df = pd.DataFrame(data)
        
        # Générer des seuils de test
        min_score = df['technical_score'].min()
        max_score = df['technical_score'].max()
        thresholds = np.linspace(min_score, max_score, 20)
        
        results = []
        for threshold in thresholds:
            # Filtrer les opportunités au-dessus du seuil
            filtered_opps = [opp for opp in opportunities 
                           if opp.technical_score is not None and float(opp.technical_score) >= threshold]
            
            # Calculer les métriques
            metrics = self.calculate_performance_metrics(filtered_opps)
            
            results.append({
                'threshold': float(threshold),
                'metrics': metrics
            })
        
        # Trouver le seuil optimal basé sur le Sharpe ratio
        best_sharpe = max(results, key=lambda x: x['metrics']['sharpe_ratio'])
        best_success_rate = max(results, key=lambda x: x['metrics']['success_rate'])
        best_avg_return = max(results, key=lambda x: x['metrics']['avg_return'])
        
        return {
            'thresholds_tested': len(thresholds),
            'score_range': {'min': float(min_score), 'max': float(max_score)},
            'best_sharpe_ratio': best_sharpe,
            'best_success_rate': best_success_rate,
            'best_avg_return': best_avg_return,
            'all_results': results
        }
    
    def optimize_composite_score_threshold(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Optimise le seuil du score composite"""
        print("🔧 Optimisation du seuil du score composite...")
        
        if not opportunities:
            return {"error": "Aucune opportunité à analyser"}
        
        # Extraire les scores composites et retours
        data = []
        for opp in opportunities:
            if opp.composite_score is not None and opp.return_1_day is not None:
                data.append({
                    'composite_score': float(opp.composite_score),
                    'return_1_day': float(opp.return_1_day)
                })
        
        if not data:
            return {"error": "Aucune donnée valide"}
        
        df = pd.DataFrame(data)
        
        # Générer des seuils de test
        min_score = df['composite_score'].min()
        max_score = df['composite_score'].max()
        thresholds = np.linspace(min_score, max_score, 20)
        
        results = []
        for threshold in thresholds:
            # Filtrer les opportunités au-dessus du seuil
            filtered_opps = [opp for opp in opportunities 
                           if opp.composite_score is not None and float(opp.composite_score) >= threshold]
            
            # Calculer les métriques
            metrics = self.calculate_performance_metrics(filtered_opps)
            
            results.append({
                'threshold': float(threshold),
                'metrics': metrics
            })
        
        # Trouver le seuil optimal basé sur le Sharpe ratio
        best_sharpe = max(results, key=lambda x: x['metrics']['sharpe_ratio'])
        best_success_rate = max(results, key=lambda x: x['metrics']['success_rate'])
        best_avg_return = max(results, key=lambda x: x['metrics']['avg_return'])
        
        return {
            'thresholds_tested': len(thresholds),
            'score_range': {'min': float(min_score), 'max': float(max_score)},
            'best_sharpe_ratio': best_sharpe,
            'best_success_rate': best_success_rate,
            'best_avg_return': best_avg_return,
            'all_results': results
        }
    
    def optimize_combined_thresholds(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Optimise les seuils combinés du score technique et composite"""
        print("🔧 Optimisation des seuils combinés...")
        
        if not opportunities:
            return {"error": "Aucune opportunité à analyser"}
        
        # Extraire les données
        data = []
        for opp in opportunities:
            if (opp.technical_score is not None and 
                opp.composite_score is not None and 
                opp.return_1_day is not None):
                data.append({
                    'technical_score': float(opp.technical_score),
                    'composite_score': float(opp.composite_score),
                    'return_1_day': float(opp.return_1_day)
                })
        
        if not data:
            return {"error": "Aucune donnée valide"}
        
        df = pd.DataFrame(data)
        
        # Générer des seuils de test
        tech_min, tech_max = df['technical_score'].min(), df['technical_score'].max()
        comp_min, comp_max = df['composite_score'].min(), df['composite_score'].max()
        
        tech_thresholds = np.linspace(tech_min, tech_max, 10)
        comp_thresholds = np.linspace(comp_min, comp_max, 10)
        
        results = []
        for tech_thresh, comp_thresh in product(tech_thresholds, comp_thresholds):
            # Filtrer les opportunités
            filtered_opps = [opp for opp in opportunities 
                           if (opp.technical_score is not None and 
                               opp.composite_score is not None and
                               float(opp.technical_score) >= tech_thresh and
                               float(opp.composite_score) >= comp_thresh)]
            
            # Calculer les métriques
            metrics = self.calculate_performance_metrics(filtered_opps)
            
            results.append({
                'technical_threshold': float(tech_thresh),
                'composite_threshold': float(comp_thresh),
                'metrics': metrics
            })
        
        # Trouver les meilleures combinaisons
        best_sharpe = max(results, key=lambda x: x['metrics']['sharpe_ratio'])
        best_success_rate = max(results, key=lambda x: x['metrics']['success_rate'])
        best_avg_return = max(results, key=lambda x: x['metrics']['avg_return'])
        
        # Filtrer les résultats avec au moins 10 opportunités
        valid_results = [r for r in results if r['metrics']['count'] >= 10]
        
        if valid_results:
            best_sharpe_valid = max(valid_results, key=lambda x: x['metrics']['sharpe_ratio'])
            best_success_rate_valid = max(valid_results, key=lambda x: x['metrics']['success_rate'])
            best_avg_return_valid = max(valid_results, key=lambda x: x['metrics']['avg_return'])
        else:
            best_sharpe_valid = best_sharpe
            best_success_rate_valid = best_success_rate
            best_avg_return_valid = best_avg_return
        
        return {
            'total_combinations_tested': len(results),
            'valid_combinations': len(valid_results),
            'score_ranges': {
                'technical': {'min': float(tech_min), 'max': float(tech_max)},
                'composite': {'min': float(comp_min), 'max': float(comp_max)}
            },
            'best_sharpe_ratio': best_sharpe,
            'best_success_rate': best_success_rate,
            'best_avg_return': best_avg_return,
            'best_sharpe_ratio_valid': best_sharpe_valid,
            'best_success_rate_valid': best_success_rate_valid,
            'best_avg_return_valid': best_avg_return_valid,
            'top_10_combinations': sorted(results, key=lambda x: x['metrics']['sharpe_ratio'], reverse=True)[:10]
        }
    
    def analyze_score_weights(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse l'impact des poids des scores dans le score composite"""
        print("⚖️ Analyse de l'impact des poids des scores...")
        
        if not opportunities:
            return {"error": "Aucune opportunité à analyser"}
        
        # Extraire les données
        data = []
        for opp in opportunities:
            if (opp.technical_score is not None and 
                opp.sentiment_score is not None and
                opp.market_score is not None and
                opp.return_1_day is not None):
                data.append({
                    'technical_score': float(opp.technical_score),
                    'sentiment_score': float(opp.sentiment_score),
                    'market_score': float(opp.market_score),
                    'return_1_day': float(opp.return_1_day)
                })
        
        if not data:
            return {"error": "Aucune donnée valide"}
        
        df = pd.DataFrame(data)
        
        # Tester différentes combinaisons de poids
        weight_combinations = [
            {'technical': 0.6, 'sentiment': 0.2, 'market': 0.2},  # Priorité technique
            {'technical': 0.5, 'sentiment': 0.3, 'market': 0.2},  # Équilibré
            {'technical': 0.4, 'sentiment': 0.4, 'market': 0.2},  # Technique + Sentiment
            {'technical': 0.7, 'sentiment': 0.1, 'market': 0.2},  # Forte priorité technique
            {'technical': 0.8, 'sentiment': 0.1, 'market': 0.1},  # Très forte priorité technique
        ]
        
        results = []
        for weights in weight_combinations:
            # Calculer le score composite pondéré
            df['weighted_composite'] = (
                weights['technical'] * df['technical_score'] +
                weights['sentiment'] * df['sentiment_score'] +
                weights['market'] * df['market_score']
            )
            
            # Calculer la corrélation avec le retour
            correlation = df['weighted_composite'].corr(df['return_1_day'])
            
            # Analyser les performances par quartile
            quartiles = pd.qcut(df['weighted_composite'], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
            quartile_performance = {}
            for q in ['Q1', 'Q2', 'Q3', 'Q4']:
                q_data = df[quartiles == q]
                if len(q_data) > 0:
                    quartile_performance[q] = {
                        'count': len(q_data),
                        'avg_return': float(q_data['return_1_day'].mean()),
                        'success_rate': float((q_data['return_1_day'] > 0).mean())
                    }
            
            results.append({
                'weights': weights,
                'correlation_with_return': float(correlation),
                'quartile_performance': quartile_performance
            })
        
        # Trouver la meilleure combinaison
        best_correlation = max(results, key=lambda x: abs(x['correlation_with_return']))
        
        return {
            'weight_combinations_tested': len(weight_combinations),
            'best_correlation': best_correlation,
            'all_results': results
        }
    
    def run_complete_optimization(self) -> Dict[str, Any]:
        """Exécute l'optimisation complète"""
        print("🚀 Démarrage de l'optimisation des seuils de scoring")
        print("=" * 80)
        
        # Récupérer toutes les opportunités d'achat
        opportunities = self.get_all_buy_opportunities()
        
        if not opportunities:
            return {"error": "Aucune opportunité d'achat trouvée"}
        
        # Exécuter toutes les optimisations
        results = {
            "analysis_date": datetime.now().isoformat(),
            "total_opportunities": len(opportunities),
            "technical_score_optimization": self.optimize_technical_score_threshold(opportunities),
            "composite_score_optimization": self.optimize_composite_score_threshold(opportunities),
            "combined_thresholds_optimization": self.optimize_combined_thresholds(opportunities),
            "score_weights_analysis": self.analyze_score_weights(opportunities)
        }
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Affiche un résumé des résultats d'optimisation"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DE L'OPTIMISATION DES SEUILS DE SCORING")
        print("=" * 80)
        
        if "error" in results:
            print(f"❌ Erreur: {results['error']}")
            return
        
        print(f"📈 OPPORTUNITÉS ANALYSÉES: {results['total_opportunities']}")
        
        # Optimisation du score technique
        if "technical_score_optimization" in results:
            tech_opt = results["technical_score_optimization"]
            if "error" not in tech_opt:
                print(f"\n🔧 OPTIMISATION DU SCORE TECHNIQUE:")
                print(f"  • Seuils testés: {tech_opt['thresholds_tested']}")
                print(f"  • Range: {tech_opt['score_range']['min']:.3f} - {tech_opt['score_range']['max']:.3f}")
                
                best_sharpe = tech_opt['best_sharpe_ratio']
                print(f"  • Meilleur Sharpe ratio: seuil {best_sharpe['threshold']:.3f}")
                print(f"    - Opportunités: {best_sharpe['metrics']['count']}")
                print(f"    - Taux de succès: {best_sharpe['metrics']['success_rate']:.1%}")
                print(f"    - Retour moyen: {best_sharpe['metrics']['avg_return']:.3f}")
                print(f"    - Sharpe ratio: {best_sharpe['metrics']['sharpe_ratio']:.3f}")
        
        # Optimisation du score composite
        if "composite_score_optimization" in results:
            comp_opt = results["composite_score_optimization"]
            if "error" not in comp_opt:
                print(f"\n🔧 OPTIMISATION DU SCORE COMPOSITE:")
                print(f"  • Seuils testés: {comp_opt['thresholds_tested']}")
                print(f"  • Range: {comp_opt['score_range']['min']:.3f} - {comp_opt['score_range']['max']:.3f}")
                
                best_sharpe = comp_opt['best_sharpe_ratio']
                print(f"  • Meilleur Sharpe ratio: seuil {best_sharpe['threshold']:.3f}")
                print(f"    - Opportunités: {best_sharpe['metrics']['count']}")
                print(f"    - Taux de succès: {best_sharpe['metrics']['success_rate']:.1%}")
                print(f"    - Retour moyen: {best_sharpe['metrics']['avg_return']:.3f}")
                print(f"    - Sharpe ratio: {best_sharpe['metrics']['sharpe_ratio']:.3f}")
        
        # Optimisation combinée
        if "combined_thresholds_optimization" in results:
            comb_opt = results["combined_thresholds_optimization"]
            if "error" not in comb_opt:
                print(f"\n🔧 OPTIMISATION COMBINÉE:")
                print(f"  • Combinaisons testées: {comb_opt['total_combinations_tested']}")
                print(f"  • Combinaisons valides: {comb_opt['valid_combinations']}")
                
                best_sharpe = comb_opt['best_sharpe_ratio_valid']
                print(f"  • Meilleure combinaison (Sharpe):")
                print(f"    - Seuil technique: {best_sharpe['technical_threshold']:.3f}")
                print(f"    - Seuil composite: {best_sharpe['composite_threshold']:.3f}")
                print(f"    - Opportunités: {best_sharpe['metrics']['count']}")
                print(f"    - Taux de succès: {best_sharpe['metrics']['success_rate']:.1%}")
                print(f"    - Retour moyen: {best_sharpe['metrics']['avg_return']:.3f}")
                print(f"    - Sharpe ratio: {best_sharpe['metrics']['sharpe_ratio']:.3f}")
        
        # Analyse des poids
        if "score_weights_analysis" in results:
            weights_opt = results["score_weights_analysis"]
            if "error" not in weights_opt:
                print(f"\n⚖️ ANALYSE DES POIDS:")
                print(f"  • Combinaisons testées: {weights_opt['weight_combinations_tested']}")
                
                best_corr = weights_opt['best_correlation']
                print(f"  • Meilleure corrélation: {best_corr['correlation_with_return']:.3f}")
                print(f"    - Poids technique: {best_corr['weights']['technical']:.1f}")
                print(f"    - Poids sentiment: {best_corr['weights']['sentiment']:.1f}")
                print(f"    - Poids marché: {best_corr['weights']['market']:.1f}")

def main():
    """Fonction principale"""
    optimizer = ScoringThresholdsOptimizer()
    
    try:
        # Exécuter l'optimisation complète
        results = optimizer.run_complete_optimization()
        
        # Afficher le résumé
        optimizer.print_summary(results)
        
        # Sauvegarder les résultats
        filename = "scoring_thresholds_optimization.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📁 Résultats sauvegardés dans {filename}")
        print(f"\n✅ Optimisation terminée avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'optimisation: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        del optimizer

if __name__ == "__main__":
    main()
