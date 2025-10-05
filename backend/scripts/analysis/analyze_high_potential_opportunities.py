#!/usr/bin/env python3
"""
Script pour analyser les 128 opportunités à fort potentiel identifiées
et découvrir les marqueurs forts de performance
"""

import sys
import os
from datetime import datetime, date
from typing import List, Dict, Any, Tuple
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

class HighPotentialOpportunitiesAnalyzer:
    """Analyseur des opportunités à fort potentiel"""
    
    def __init__(self):
        """Initialise l'analyseur"""
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        
    def __del__(self):
        """Ferme la session de base de données"""
        if hasattr(self, 'db'):
            self.db.close()
    
    def identify_high_potential_opportunities(self, min_return_threshold: float = 0.05) -> List[HistoricalOpportunities]:
        """
        Identifie les opportunités à fort potentiel basées sur les retours réels
        
        Args:
            min_return_threshold: Seuil minimum de retour pour considérer une opportunité comme à fort potentiel
            
        Returns:
            Liste des opportunités à fort potentiel
        """
        print(f"🔍 Identification des opportunités à fort potentiel (retour > {min_return_threshold*100:.1f}%)")
        
        # Récupérer toutes les opportunités avec des retours validés
        opportunities = self.db.query(HistoricalOpportunities).filter(
            and_(
                HistoricalOpportunities.return_1_day.isnot(None),
                HistoricalOpportunities.return_1_day > min_return_threshold,
                HistoricalOpportunities.recommendation.in_(['BUY', 'BUY_WEAK', 'BUY_MODERATE', 'BUY_STRONG'])
            )
        ).all()
        
        print(f"📊 Trouvé {len(opportunities)} opportunités à fort potentiel")
        return opportunities
    
    def analyze_score_patterns(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse les patterns de scores des opportunités à fort potentiel"""
        print("📈 Analyse des patterns de scores...")
        
        if not opportunities:
            return {"error": "Aucune opportunité à analyser"}
        
        # Extraire les scores
        scores_data = []
        for opp in opportunities:
            scores_data.append({
                'composite_score': float(opp.composite_score) if opp.composite_score else 0,
                'technical_score': float(opp.technical_score) if opp.technical_score else 0,
                'sentiment_score': float(opp.sentiment_score) if opp.sentiment_score else 0,
                'market_score': float(opp.market_score) if opp.market_score else 0,
                'confidence_level': float(opp.confidence_level) if opp.confidence_level else 0,
                'return_1_day': float(opp.return_1_day) if opp.return_1_day else 0,
                'return_7_days': float(opp.return_7_days) if opp.return_7_days else 0,
                'return_30_days': float(opp.return_30_days) if opp.return_30_days else 0,
                'recommendation': opp.recommendation,
                'risk_level': opp.risk_level,
                'symbol': opp.symbol
            })
        
        df = pd.DataFrame(scores_data)
        
        # Statistiques descriptives
        score_stats = {}
        for score_type in ['composite_score', 'technical_score', 'sentiment_score', 'market_score', 'confidence_level']:
            if score_type in df.columns:
                score_stats[score_type] = {
                    'mean': float(df[score_type].mean()),
                    'median': float(df[score_type].median()),
                    'std': float(df[score_type].std()),
                    'min': float(df[score_type].min()),
                    'max': float(df[score_type].max()),
                    'q25': float(df[score_type].quantile(0.25)),
                    'q75': float(df[score_type].quantile(0.75))
                }
        
        # Corrélations avec les retours
        correlations = {}
        for return_type in ['return_1_day', 'return_7_days', 'return_30_days']:
            if return_type in df.columns:
                correlations[return_type] = {}
                for score_type in ['composite_score', 'technical_score', 'sentiment_score', 'market_score', 'confidence_level']:
                    if score_type in df.columns:
                        corr = df[score_type].corr(df[return_type])
                        correlations[return_type][score_type] = float(corr) if not np.isnan(corr) else 0.0
        
        return {
            'count': len(opportunities),
            'score_statistics': score_stats,
            'correlations': correlations,
            'data_sample': scores_data[:10]  # Échantillon pour inspection
        }
    
    def analyze_recommendation_patterns(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse les patterns de recommandations"""
        print("🎯 Analyse des patterns de recommandations...")
        
        if not opportunities:
            return {"error": "Aucune opportunité à analyser"}
        
        # Grouper par recommandation
        rec_groups = defaultdict(list)
        for opp in opportunities:
            rec_groups[opp.recommendation].append(opp)
        
        # Analyser chaque groupe
        rec_analysis = {}
        for rec, opps in rec_groups.items():
            returns_1d = [float(opp.return_1_day) for opp in opps if opp.return_1_day is not None]
            returns_7d = [float(opp.return_7_days) for opp in opps if opp.return_7_days is not None]
            returns_30d = [float(opp.return_30_days) for opp in opps if opp.return_30_days is not None]
            
            rec_analysis[rec] = {
                'count': len(opps),
                'avg_return_1d': float(np.mean(returns_1d)) if returns_1d else 0,
                'avg_return_7d': float(np.mean(returns_7d)) if returns_7d else 0,
                'avg_return_30d': float(np.mean(returns_30d)) if returns_30d else 0,
                'max_return_1d': float(np.max(returns_1d)) if returns_1d else 0,
                'min_return_1d': float(np.min(returns_1d)) if returns_1d else 0,
                'std_return_1d': float(np.std(returns_1d)) if returns_1d else 0
            }
        
        return rec_analysis
    
    def analyze_risk_patterns(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse les patterns de risque"""
        print("⚠️ Analyse des patterns de risque...")
        
        if not opportunities:
            return {"error": "Aucune opportunité à analyser"}
        
        # Grouper par niveau de risque
        risk_groups = defaultdict(list)
        for opp in opportunities:
            risk_groups[opp.risk_level].append(opp)
        
        # Analyser chaque groupe
        risk_analysis = {}
        for risk, opps in risk_groups.items():
            returns_1d = [float(opp.return_1_day) for opp in opps if opp.return_1_day is not None]
            confidences = [float(opp.confidence_level) for opp in opps if opp.confidence_level is not None]
            
            risk_analysis[risk] = {
                'count': len(opps),
                'avg_return_1d': float(np.mean(returns_1d)) if returns_1d else 0,
                'max_return_1d': float(np.max(returns_1d)) if returns_1d else 0,
                'min_return_1d': float(np.min(returns_1d)) if returns_1d else 0,
                'std_return_1d': float(np.std(returns_1d)) if returns_1d else 0,
                'avg_confidence': float(np.mean(confidences)) if confidences else 0,
                'success_rate': len([r for r in returns_1d if r > 0]) / len(returns_1d) if returns_1d else 0
            }
        
        return risk_analysis
    
    def analyze_symbol_patterns(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse les patterns par symbole"""
        print("🏢 Analyse des patterns par symbole...")
        
        if not opportunities:
            return {"error": "Aucune opportunité à analyser"}
        
        # Grouper par symbole
        symbol_groups = defaultdict(list)
        for opp in opportunities:
            symbol_groups[opp.symbol].append(opp)
        
        # Analyser les symboles avec le plus d'opportunités à fort potentiel
        symbol_analysis = {}
        for symbol, opps in symbol_groups.items():
            if len(opps) >= 2:  # Au moins 2 opportunités
                returns_1d = [float(opp.return_1_day) for opp in opps if opp.return_1_day is not None]
                avg_scores = {
                    'composite': np.mean([float(opp.composite_score) for opp in opps if opp.composite_score]),
                    'technical': np.mean([float(opp.technical_score) for opp in opps if opp.technical_score]),
                    'sentiment': np.mean([float(opp.sentiment_score) for opp in opps if opp.sentiment_score]),
                    'market': np.mean([float(opp.market_score) for opp in opps if opp.market_score])
                }
                
                symbol_analysis[symbol] = {
                    'count': len(opps),
                    'avg_return_1d': float(np.mean(returns_1d)) if returns_1d else 0,
                    'max_return_1d': float(np.max(returns_1d)) if returns_1d else 0,
                    'min_return_1d': float(np.min(returns_1d)) if returns_1d else 0,
                    'success_rate': len([r for r in returns_1d if r > 0]) / len(returns_1d) if returns_1d else 0,
                    'avg_scores': {k: float(v) for k, v in avg_scores.items() if not np.isnan(v)}
                }
        
        # Trier par nombre d'opportunités
        sorted_symbols = sorted(symbol_analysis.items(), key=lambda x: x[1]['count'], reverse=True)
        
        return {
            'top_symbols': dict(sorted_symbols[:20]),  # Top 20
            'total_symbols': len(symbol_analysis)
        }
    
    def analyze_temporal_patterns(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Analyse les patterns temporels"""
        print("📅 Analyse des patterns temporels...")
        
        if not opportunities:
            return {"error": "Aucune opportunité à analyser"}
        
        # Grouper par mois
        monthly_groups = defaultdict(list)
        for opp in opportunities:
            if opp.opportunity_date:
                month_key = opp.opportunity_date.strftime('%Y-%m')
                monthly_groups[month_key].append(opp)
        
        # Analyser chaque mois
        monthly_analysis = {}
        for month, opps in monthly_groups.items():
            returns_1d = [float(opp.return_1_day) for opp in opps if opp.return_1_day is not None]
            
            monthly_analysis[month] = {
                'count': len(opps),
                'avg_return_1d': float(np.mean(returns_1d)) if returns_1d else 0,
                'max_return_1d': float(np.max(returns_1d)) if returns_1d else 0,
                'success_rate': len([r for r in returns_1d if r > 0]) / len(returns_1d) if returns_1d else 0
            }
        
        return monthly_analysis
    
    def identify_strong_markers(self, opportunities: List[HistoricalOpportunities]) -> Dict[str, Any]:
        """Identifie les marqueurs forts de performance"""
        print("💎 Identification des marqueurs forts...")
        
        if not opportunities:
            return {"error": "Aucune opportunité à analyser"}
        
        # Extraire les données
        data = []
        for opp in opportunities:
            data.append({
                'composite_score': float(opp.composite_score) if opp.composite_score else 0,
                'technical_score': float(opp.technical_score) if opp.technical_score else 0,
                'sentiment_score': float(opp.sentiment_score) if opp.sentiment_score else 0,
                'market_score': float(opp.market_score) if opp.market_score else 0,
                'confidence_level': float(opp.confidence_level) if opp.confidence_level else 0,
                'return_1_day': float(opp.return_1_day) if opp.return_1_day else 0,
                'recommendation': opp.recommendation,
                'risk_level': opp.risk_level
            })
        
        df = pd.DataFrame(data)
        
        # Identifier les seuils optimaux pour chaque score
        markers = {}
        
        for score_type in ['composite_score', 'technical_score', 'sentiment_score', 'market_score', 'confidence_level']:
            if score_type in df.columns:
                # Calculer les percentiles
                percentiles = [10, 25, 50, 75, 90]
                percentile_values = {}
                for p in percentiles:
                    percentile_values[f'p{p}'] = float(df[score_type].quantile(p/100))
                
                # Analyser la performance par quartile
                try:
                    quartiles = pd.qcut(df[score_type], q=4, labels=['Q1', 'Q2', 'Q3', 'Q4'], duplicates='drop')
                    quartile_performance = {}
                    for q in ['Q1', 'Q2', 'Q3', 'Q4']:
                        q_data = df[quartiles == q]
                        if len(q_data) > 0:
                            quartile_performance[q] = {
                                'count': len(q_data),
                                'avg_return': float(q_data['return_1_day'].mean()),
                                'success_rate': float((q_data['return_1_day'] > 0).mean())
                            }
                except ValueError:
                    # Si les quartiles ne peuvent pas être calculés (valeurs identiques), utiliser des seuils fixes
                    quartile_performance = {}
                    score_values = df[score_type].values
                    if len(score_values) > 0:
                        q1_threshold = np.percentile(score_values, 25)
                        q2_threshold = np.percentile(score_values, 50)
                        q3_threshold = np.percentile(score_values, 75)
                        
                        for q, threshold in [('Q1', q1_threshold), ('Q2', q2_threshold), ('Q3', q3_threshold), ('Q4', float('inf'))]:
                            if q == 'Q1':
                                q_data = df[df[score_type] <= threshold]
                            elif q == 'Q2':
                                q_data = df[(df[score_type] > q1_threshold) & (df[score_type] <= threshold)]
                            elif q == 'Q3':
                                q_data = df[(df[score_type] > q2_threshold) & (df[score_type] <= threshold)]
                            else:  # Q4
                                q_data = df[df[score_type] > q3_threshold]
                            
                            if len(q_data) > 0:
                                quartile_performance[q] = {
                                    'count': len(q_data),
                                    'avg_return': float(q_data['return_1_day'].mean()),
                                    'success_rate': float((q_data['return_1_day'] > 0).mean())
                                }
                
                markers[score_type] = {
                    'percentiles': percentile_values,
                    'quartile_performance': quartile_performance,
                    'correlation_with_return': float(df[score_type].corr(df['return_1_day']))
                }
        
        # Identifier les combinaisons de scores les plus performantes
        # Top 20% des opportunités par retour
        top_20_percent = df.nlargest(int(len(df) * 0.2), 'return_1_day')
        
        combination_analysis = {
            'top_20_percent_avg_scores': {
                'composite_score': float(top_20_percent['composite_score'].mean()),
                'technical_score': float(top_20_percent['technical_score'].mean()),
                'sentiment_score': float(top_20_percent['sentiment_score'].mean()),
                'market_score': float(top_20_percent['market_score'].mean()),
                'confidence_level': float(top_20_percent['confidence_level'].mean())
            },
            'top_20_percent_count': len(top_20_percent)
        }
        
        return {
            'score_markers': markers,
            'combination_analysis': combination_analysis
        }
    
    def generate_insights(self, all_results: Dict[str, Any]) -> List[str]:
        """Génère des insights basés sur l'analyse"""
        print("💡 Génération des insights...")
        
        insights = []
        
        # Insights sur les scores
        if 'score_patterns' in all_results and 'score_statistics' in all_results['score_patterns']:
            score_stats = all_results['score_patterns']['score_statistics']
            
            # Identifier le score le plus élevé en moyenne
            avg_scores = {k: v['mean'] for k, v in score_stats.items()}
            highest_avg_score = max(avg_scores.items(), key=lambda x: x[1])
            insights.append(f"Score moyen le plus élevé: {highest_avg_score[0]} ({highest_avg_score[1]:.3f})")
            
            # Identifier le score avec la plus grande corrélation
            if 'correlations' in all_results['score_patterns']:
                corr_1d = all_results['score_patterns']['correlations'].get('return_1_day', {})
                if corr_1d:
                    best_corr = max(corr_1d.items(), key=lambda x: abs(x[1]))
                    insights.append(f"Meilleure corrélation avec retour 1j: {best_corr[0]} ({best_corr[1]:.3f})")
        
        # Insights sur les recommandations
        if 'recommendation_patterns' in all_results:
            rec_patterns = all_results['recommendation_patterns']
            if rec_patterns:
                best_rec = max(rec_patterns.items(), key=lambda x: x[1].get('avg_return_1d', 0))
                insights.append(f"Recommandation la plus performante: {best_rec[0]} (retour moyen: {best_rec[1]['avg_return_1d']:.2f}%)")
        
        # Insights sur les risques
        if 'risk_patterns' in all_results:
            risk_patterns = all_results['risk_patterns']
            if risk_patterns:
                best_risk = max(risk_patterns.items(), key=lambda x: x[1].get('avg_return_1d', 0))
                insights.append(f"Niveau de risque le plus performant: {best_risk[0]} (retour moyen: {best_risk[1]['avg_return_1d']:.2f}%)")
        
        # Insights sur les symboles
        if 'symbol_patterns' in all_results and 'top_symbols' in all_results['symbol_patterns']:
            top_symbols = all_results['symbol_patterns']['top_symbols']
            if top_symbols:
                best_symbol = max(top_symbols.items(), key=lambda x: x[1].get('avg_return_1d', 0))
                insights.append(f"Symbole le plus performant: {best_symbol[0]} (retour moyen: {best_symbol[1]['avg_return_1d']:.2f}%, {best_symbol[1]['count']} opportunités)")
        
        # Insights sur les marqueurs
        if 'strong_markers' in all_results and 'score_markers' in all_results['strong_markers']:
            markers = all_results['strong_markers']['score_markers']
            if markers:
                # Identifier le marqueur avec la meilleure corrélation
                best_marker = max(markers.items(), key=lambda x: abs(x[1].get('correlation_with_return', 0)))
                insights.append(f"Marqueur le plus corrélé: {best_marker[0]} (corrélation: {best_marker[1]['correlation_with_return']:.3f})")
        
        return insights
    
    def run_complete_analysis(self, min_return_threshold: float = 0.05) -> Dict[str, Any]:
        """Exécute l'analyse complète"""
        print("🚀 Démarrage de l'analyse des opportunités à fort potentiel")
        print("=" * 80)
        
        # Identifier les opportunités à fort potentiel
        opportunities = self.identify_high_potential_opportunities(min_return_threshold)
        
        if not opportunities:
            return {"error": "Aucune opportunité à fort potentiel trouvée"}
        
        # Exécuter toutes les analyses
        results = {
            "analysis_date": datetime.now().isoformat(),
            "min_return_threshold": min_return_threshold,
            "total_opportunities": len(opportunities),
            "score_patterns": self.analyze_score_patterns(opportunities),
            "recommendation_patterns": self.analyze_recommendation_patterns(opportunities),
            "risk_patterns": self.analyze_risk_patterns(opportunities),
            "symbol_patterns": self.analyze_symbol_patterns(opportunities),
            "temporal_patterns": self.analyze_temporal_patterns(opportunities),
            "strong_markers": self.identify_strong_markers(opportunities)
        }
        
        # Générer les insights
        results["insights"] = self.generate_insights(results)
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Affiche un résumé des résultats"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DE L'ANALYSE DES OPPORTUNITÉS À FORT POTENTIEL")
        print("=" * 80)
        
        if "error" in results:
            print(f"❌ Erreur: {results['error']}")
            return
        
        print(f"📈 OPPORTUNITÉS ANALYSÉES: {results['total_opportunities']}")
        print(f"🎯 Seuil de retour minimum: {results['min_return_threshold']*100:.1f}%")
        
        # Patterns de scores
        if "score_patterns" in results and "score_statistics" in results["score_patterns"]:
            print(f"\n📊 PATTERNS DE SCORES:")
            score_stats = results["score_patterns"]["score_statistics"]
            for score_type, stats in score_stats.items():
                print(f"  • {score_type}:")
                print(f"    - Moyenne: {stats['mean']:.3f}")
                print(f"    - Médiane: {stats['median']:.3f}")
                print(f"    - Écart-type: {stats['std']:.3f}")
                print(f"    - Min/Max: {stats['min']:.3f} / {stats['max']:.3f}")
        
        # Patterns de recommandations
        if "recommendation_patterns" in results:
            print(f"\n🎯 PATTERNS DE RECOMMANDATIONS:")
            rec_patterns = results["recommendation_patterns"]
            for rec, data in rec_patterns.items():
                print(f"  • {rec}: {data['count']} opportunités")
                print(f"    - Retour moyen 1j: {data['avg_return_1d']:.2f}%")
                print(f"    - Retour max 1j: {data['max_return_1d']:.2f}%")
        
        # Patterns de risque
        if "risk_patterns" in results:
            print(f"\n⚠️ PATTERNS DE RISQUE:")
            risk_patterns = results["risk_patterns"]
            for risk, data in risk_patterns.items():
                print(f"  • {risk}: {data['count']} opportunités")
                print(f"    - Retour moyen 1j: {data['avg_return_1d']:.2f}%")
                print(f"    - Taux de succès: {data['success_rate']:.1%}")
        
        # Top symboles
        if "symbol_patterns" in results and "top_symbols" in results["symbol_patterns"]:
            print(f"\n🏢 TOP SYMBOLES:")
            top_symbols = results["symbol_patterns"]["top_symbols"]
            for symbol, data in list(top_symbols.items())[:10]:
                print(f"  • {symbol}: {data['count']} opportunités, retour moyen: {data['avg_return_1d']:.2f}%")
        
        # Marqueurs forts
        if "strong_markers" in results and "score_markers" in results["strong_markers"]:
            print(f"\n💎 MARQUEURS FORTS:")
            markers = results["strong_markers"]["score_markers"]
            for score_type, marker_data in markers.items():
                corr = marker_data.get('correlation_with_return', 0)
                print(f"  • {score_type}: corrélation = {corr:.3f}")
        
        # Insights
        if "insights" in results:
            print(f"\n💡 INSIGHTS CLÉS:")
            for i, insight in enumerate(results["insights"], 1):
                print(f"  {i}. {insight}")

def main():
    """Fonction principale"""
    analyzer = HighPotentialOpportunitiesAnalyzer()
    
    try:
        # Exécuter l'analyse avec différents seuils
        thresholds = [0.03, 0.05, 0.07, 0.10]  # 3%, 5%, 7%, 10%
        
        for threshold in thresholds:
            print(f"\n🔍 Analyse avec seuil de {threshold*100:.1f}%")
            print("-" * 50)
            
            results = analyzer.run_complete_analysis(threshold)
            
            # Afficher le résumé
            analyzer.print_summary(results)
            
            # Sauvegarder les résultats
            filename = f"high_potential_opportunities_analysis_{int(threshold*100)}pct.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"\n📁 Résultats sauvegardés dans {filename}")
            
            # Arrêter après le premier seuil qui donne des résultats
            if "error" not in results and results["total_opportunities"] > 0:
                break
        
        print(f"\n✅ Analyse terminée avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        del analyzer

if __name__ == "__main__":
    main()
