#!/usr/bin/env python3
"""
Script d'analyse des performances des recommandations
Fournit des insights pour l'implémentation des outils ML futurs
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case
from app.core.database import get_db
from app.models.historical_opportunities import HistoricalOpportunities, HistoricalOpportunityValidation
from app.models.database import HistoricalData
import logging
from datetime import datetime, date
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple, Optional
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecommendationPerformanceAnalyzer:
    """Analyseur de performance des recommandations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.results = {}
    
    def analyze_overall_performance(self) -> Dict:
        """Analyse globale des performances"""
        logger.info("📊 Analyse globale des performances")
        
        # Statistiques générales
        total_opportunities = self.db.query(HistoricalOpportunities).count()
        
        # Opportunités avec validation
        validated_1d = self.db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.price_1_day_later.isnot(None))\
            .count()
        
        validated_7d = self.db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.price_7_days_later.isnot(None))\
            .count()
        
        validated_30d = self.db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.price_30_days_later.isnot(None))\
            .count()
        
        # Distribution des recommandations
        rec_distribution = self.db.query(
            HistoricalOpportunities.recommendation,
            func.count(HistoricalOpportunities.id)
        ).group_by(HistoricalOpportunities.recommendation).all()
        
        # Distribution des niveaux de risque
        risk_distribution = self.db.query(
            HistoricalOpportunities.risk_level,
            func.count(HistoricalOpportunities.id)
        ).group_by(HistoricalOpportunities.risk_level).all()
        
        return {
            "total_opportunities": total_opportunities,
            "validated_1d": validated_1d,
            "validated_7d": validated_7d,
            "validated_30d": validated_30d,
            "recommendation_distribution": dict(rec_distribution),
            "risk_distribution": dict(risk_distribution),
            "validation_coverage": {
                "1d": (validated_1d / total_opportunities) * 100,
                "7d": (validated_7d / total_opportunities) * 100,
                "30d": (validated_30d / total_opportunities) * 100
            }
        }
    
    def analyze_accuracy_by_recommendation(self) -> Dict:
        """Analyse de la précision par type de recommandation"""
        logger.info("🎯 Analyse de la précision par recommandation")
        
        results = {}
        
        for period in [1, 7, 30]:
            period_key = f"{period}d"
            results[period_key] = {}
            
            # Requête pour chaque type de recommandation
            for rec_type in ["BUY", "SELL", "HOLD"]:
                # Opportunités avec validation
                if period == 1:
                    price_col = HistoricalOpportunities.price_1_day_later
                elif period == 7:
                    price_col = HistoricalOpportunities.price_7_days_later
                else:  # period == 30
                    price_col = HistoricalOpportunities.price_30_days_later
                
                opportunities = self.db.query(HistoricalOpportunities)\
                    .filter(
                        and_(
                            HistoricalOpportunities.recommendation == rec_type,
                            price_col.isnot(None)
                        )
                    ).all()
                
                if not opportunities:
                    results[period_key][rec_type] = {
                        "count": 0,
                        "accuracy": 0,
                        "avg_return": 0,
                        "success_rate": 0
                    }
                    continue
                
                # Calculer la précision
                if period == 1:
                    correct_col = "recommendation_correct_1_day"
                elif period == 7:
                    correct_col = "recommendation_correct_7_days"
                else:  # period == 30
                    correct_col = "recommendation_correct_30_days"
                
                correct_predictions = sum(
                    1 for opp in opportunities 
                    if getattr(opp, correct_col) is True
                )
                
                # Calculer les retours moyens
                if period == 1:
                    return_col = "return_1_day"
                elif period == 7:
                    return_col = "return_7_days"
                else:  # period == 30
                    return_col = "return_30_days"
                
                returns = [
                    getattr(opp, return_col) 
                    for opp in opportunities 
                    if getattr(opp, return_col) is not None
                ]
                
                avg_return = np.mean(returns) if returns else 0
                
                # Taux de succès (retour positif)
                success_rate = sum(1 for r in returns if r > 0) / len(returns) if returns else 0
                
                results[period_key][rec_type] = {
                    "count": len(opportunities),
                    "accuracy": (correct_predictions / len(opportunities)) * 100,
                    "avg_return": avg_return * 100,  # En pourcentage
                    "success_rate": success_rate * 100,
                    "total_return": sum(returns) * 100 if returns else 0
                }
        
        return results
    
    def analyze_accuracy_by_risk_level(self) -> Dict:
        """Analyse de la précision par niveau de risque"""
        logger.info("⚠️ Analyse de la précision par niveau de risque")
        
        results = {}
        
        for period in [1, 7, 30]:
            period_key = f"{period}d"
            results[period_key] = {}
            
            for risk_level in ["LOW", "MEDIUM", "HIGH"]:
                # Sélectionner la colonne de prix appropriée
                if period == 1:
                    price_col = HistoricalOpportunities.price_1_day_later
                elif period == 7:
                    price_col = HistoricalOpportunities.price_7_days_later
                else:  # period == 30
                    price_col = HistoricalOpportunities.price_30_days_later
                
                opportunities = self.db.query(HistoricalOpportunities)\
                    .filter(
                        and_(
                            HistoricalOpportunities.risk_level == risk_level,
                            price_col.isnot(None)
                        )
                    ).all()
                
                if not opportunities:
                    results[period_key][risk_level] = {
                        "count": 0,
                        "accuracy": 0,
                        "avg_return": 0,
                        "volatility": 0
                    }
                    continue
                
                # Calculer la précision
                if period == 1:
                    correct_col = "recommendation_correct_1_day"
                    return_col = "return_1_day"
                elif period == 7:
                    correct_col = "recommendation_correct_7_days"
                    return_col = "return_7_days"
                else:  # period == 30
                    correct_col = "recommendation_correct_30_days"
                    return_col = "return_30_days"
                
                correct_predictions = sum(
                    1 for opp in opportunities 
                    if getattr(opp, correct_col) is True
                )
                
                # Calculer les retours
                returns = [
                    getattr(opp, return_col) 
                    for opp in opportunities 
                    if getattr(opp, return_col) is not None
                ]
                
                avg_return = np.mean(returns) if returns else 0
                volatility = np.std(returns) if len(returns) > 1 else 0
                
                results[period_key][risk_level] = {
                    "count": len(opportunities),
                    "accuracy": (correct_predictions / len(opportunities)) * 100,
                    "avg_return": avg_return * 100,
                    "volatility": volatility * 100,
                    "sharpe_ratio": (avg_return / volatility) if volatility > 0 else 0
                }
        
        return results
    
    def analyze_score_correlation(self) -> Dict:
        """Analyse de la corrélation entre les scores et les performances"""
        logger.info("📈 Analyse de la corrélation scores-performance")
        
        # Récupérer les données avec validation
        opportunities = self.db.query(HistoricalOpportunities)\
            .filter(
                and_(
                    HistoricalOpportunities.price_1_day_later.isnot(None),
                    HistoricalOpportunities.return_1_day.isnot(None)
                )
            ).all()
        
        if not opportunities:
            return {"error": "Pas de données de validation disponibles"}
        
        # Préparer les données
        data = []
        for opp in opportunities:
            data.append({
                "technical_score": float(opp.technical_score) if opp.technical_score else None,
                "sentiment_score": float(opp.sentiment_score) if opp.sentiment_score else None,
                "market_score": float(opp.market_score) if opp.market_score else None,
                "composite_score": float(opp.composite_score) if opp.composite_score else None,
                "return_1d": float(opp.return_1_day) if opp.return_1_day else None,
                "return_7d": float(opp.return_7_days) if opp.return_7_days else None,
                "return_30d": float(opp.return_30_days) if opp.return_30_days else None,
                "recommendation": opp.recommendation,
                "risk_level": opp.risk_level
            })
        
        df = pd.DataFrame(data)
        
        # Calculer les corrélations
        score_columns = ["technical_score", "sentiment_score", "market_score", "composite_score"]
        return_columns = ["return_1d", "return_7d", "return_30d"]
        
        correlations = {}
        for return_col in return_columns:
            if return_col in df.columns:
                correlations[return_col] = {}
                for score_col in score_columns:
                    if score_col in df.columns:
                        corr = df[score_col].corr(df[return_col])
                        correlations[return_col][score_col] = corr if not pd.isna(corr) else 0
        
        # Analyse par déciles de score composite
        df['composite_decile'] = pd.qcut(df['composite_score'], 10, labels=False, duplicates='drop')
        decile_analysis = df.groupby('composite_decile').agg({
            'return_1d': ['mean', 'std', 'count'],
            'return_7d': ['mean', 'std', 'count'],
            'return_30d': ['mean', 'std', 'count']
        }).round(4)
        
        # Convertir les tuples en strings pour JSON
        decile_dict = {}
        for col in decile_analysis.columns:
            col_name = f"{col[0]}_{col[1]}" if isinstance(col, tuple) else str(col)
            decile_dict[col_name] = decile_analysis[col].to_dict()
        
        return {
            "correlations": correlations,
            "decile_analysis": decile_dict,
            "sample_size": len(df)
        }
    
    def analyze_temporal_performance(self) -> Dict:
        """Analyse des performances dans le temps"""
        logger.info("📅 Analyse des performances temporelles")
        
        # Récupérer les données par mois
        monthly_data = self.db.query(
            func.date_trunc('month', HistoricalOpportunities.opportunity_date).label('month'),
            HistoricalOpportunities.recommendation,
            func.count(HistoricalOpportunities.id).label('count'),
            func.avg(
                case(
                    (HistoricalOpportunities.recommendation_correct_1_day == True, 1),
                    else_=0
                )
            ).label('accuracy_1d'),
            func.avg(HistoricalOpportunities.return_1_day).label('avg_return_1d')
        ).filter(
            HistoricalOpportunities.price_1_day_later.isnot(None)
        ).group_by(
            func.date_trunc('month', HistoricalOpportunities.opportunity_date),
            HistoricalOpportunities.recommendation
        ).order_by('month').all()
        
        # Organiser les données
        results = {}
        for row in monthly_data:
            month_str = row.month.strftime('%Y-%m')
            if month_str not in results:
                results[month_str] = {}
            
            results[month_str][row.recommendation] = {
                "count": row.count,
                "accuracy_1d": (row.accuracy_1d or 0) * 100,
                "avg_return_1d": (row.avg_return_1d or 0) * 100
            }
        
        return results
    
    def analyze_symbol_performance(self) -> Dict:
        """Analyse des performances par symbole"""
        logger.info("🏢 Analyse des performances par symbole")
        
        # Top 20 symboles par nombre d'opportunités
        symbol_stats = self.db.query(
            HistoricalOpportunities.symbol,
            func.count(HistoricalOpportunities.id).label('total_opportunities'),
            func.avg(
                case(
                    (HistoricalOpportunities.recommendation_correct_1_day == True, 1),
                    else_=0
                )
            ).label('accuracy_1d'),
            func.avg(HistoricalOpportunities.return_1_day).label('avg_return_1d'),
            func.avg(HistoricalOpportunities.composite_score).label('avg_composite_score')
        ).filter(
            HistoricalOpportunities.price_1_day_later.isnot(None)
        ).group_by(
            HistoricalOpportunities.symbol
        ).having(
            func.count(HistoricalOpportunities.id) >= 10  # Au moins 10 opportunités
        ).order_by(
            func.count(HistoricalOpportunities.id).desc()
        ).limit(20).all()
        
        results = []
        for row in symbol_stats:
            results.append({
                "symbol": row.symbol,
                "total_opportunities": row.total_opportunities,
                "accuracy_1d": (row.accuracy_1d or 0) * 100,
                "avg_return_1d": (row.avg_return_1d or 0) * 100,
                "avg_composite_score": row.avg_composite_score or 0
            })
        
        return {"top_symbols": results}
    
    def generate_ml_insights(self) -> Dict:
        """Génère des insights pour l'implémentation ML"""
        logger.info("🤖 Génération d'insights ML")
        
        # Récupérer les données complètes
        opportunities = self.db.query(HistoricalOpportunities)\
            .filter(
                and_(
                    HistoricalOpportunities.price_1_day_later.isnot(None),
                    HistoricalOpportunities.return_1_day.isnot(None)
                )
            ).all()
        
        if not opportunities:
            return {"error": "Pas de données disponibles"}
        
        # Préparer les données
        data = []
        for opp in opportunities:
            data.append({
                "technical_score": float(opp.technical_score) if opp.technical_score else None,
                "sentiment_score": float(opp.sentiment_score) if opp.sentiment_score else None,
                "market_score": float(opp.market_score) if opp.market_score else None,
                "composite_score": float(opp.composite_score) if opp.composite_score else None,
                "return_1d": float(opp.return_1_day) if opp.return_1_day else None,
                "return_7d": float(opp.return_7_days) if opp.return_7_days else None,
                "return_30d": float(opp.return_30_days) if opp.return_30_days else None,
                "recommendation": opp.recommendation,
                "risk_level": opp.risk_level,
                "confidence_level": opp.confidence_level
            })
        
        df = pd.DataFrame(data)
        
        # Insights pour ML
        insights = {
            "dataset_size": len(df),
            "feature_importance": {},
            "performance_by_score_ranges": {},
            "recommendations_for_ml": []
        }
        
        # Analyse des plages de scores
        score_ranges = {
            "low": (0, 0.4),
            "medium": (0.4, 0.6),
            "high": (0.6, 1.0)
        }
        
        for range_name, (min_val, max_val) in score_ranges.items():
            mask = (df['composite_score'] >= min_val) & (df['composite_score'] < max_val)
            range_data = df[mask]
            
            if len(range_data) > 0:
                insights["performance_by_score_ranges"][range_name] = {
                    "count": len(range_data),
                    "avg_return_1d": range_data['return_1d'].mean() * 100,
                    "accuracy": (range_data['return_1d'] > 0).mean() * 100,
                    "volatility": range_data['return_1d'].std() * 100
                }
        
        # Recommandations pour ML
        insights["recommendations_for_ml"] = [
            "Utiliser les scores techniques comme features principales",
            "Intégrer la volatilité historique comme feature",
            "Considérer les patterns temporels (mois, saisons)",
            "Implémenter un système de confiance basé sur la précision historique",
            "Utiliser l'ensemble des 3 horizons (1d, 7d, 30d) pour l'entraînement",
            "Considérer les interactions entre scores techniques et sentiment",
            "Implémenter un système de récompense basé sur le Sharpe ratio"
        ]
        
        return insights
    
    def run_complete_analysis(self) -> Dict:
        """Exécute l'analyse complète"""
        logger.info("🚀 Démarrage de l'analyse complète des performances")
        
        try:
            self.results = {
                "overall_performance": self.analyze_overall_performance(),
                "accuracy_by_recommendation": self.analyze_accuracy_by_recommendation(),
                "accuracy_by_risk_level": self.analyze_accuracy_by_risk_level(),
                "score_correlation": self.analyze_score_correlation(),
                "temporal_performance": self.analyze_temporal_performance(),
                "symbol_performance": self.analyze_symbol_performance(),
                "ml_insights": self.generate_ml_insights(),
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse: {e}")
            raise
    
    def save_results(self, filename: str = "recommendation_performance_analysis.json"):
        """Sauvegarde les résultats"""
        if not self.results:
            logger.warning("Aucun résultat à sauvegarder")
            return
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📁 Résultats sauvegardés dans {filepath}")
    
    def print_summary(self):
        """Affiche un résumé des résultats"""
        if not self.results:
            logger.warning("Aucun résultat à afficher")
            return
        
        overall = self.results["overall_performance"]
        accuracy = self.results["accuracy_by_recommendation"]
        
        print("\n" + "="*80)
        print("📊 RÉSUMÉ DE L'ANALYSE DES PERFORMANCES")
        print("="*80)
        
        print(f"\n📈 STATISTIQUES GÉNÉRALES:")
        print(f"  • Total d'opportunités: {overall['total_opportunities']:,}")
        print(f"  • Validées 1 jour: {overall['validated_1d']:,} ({overall['validation_coverage']['1d']:.1f}%)")
        print(f"  • Validées 7 jours: {overall['validated_7d']:,} ({overall['validation_coverage']['7d']:.1f}%)")
        print(f"  • Validées 30 jours: {overall['validated_30d']:,} ({overall['validation_coverage']['30d']:.1f}%)")
        
        print(f"\n🎯 DISTRIBUTION DES RECOMMANDATIONS:")
        for rec, count in overall['recommendation_distribution'].items():
            percentage = (count / overall['total_opportunities']) * 100
            print(f"  • {rec}: {count:,} ({percentage:.1f}%)")
        
        print(f"\n⚠️ DISTRIBUTION DES RISQUES:")
        for risk, count in overall['risk_distribution'].items():
            percentage = (count / overall['total_opportunities']) * 100
            print(f"  • {risk}: {count:,} ({percentage:.1f}%)")
        
        print(f"\n🎯 PRÉCISION PAR RECOMMANDATION (1 jour):")
        for rec_type in ["BUY", "SELL", "HOLD"]:
            if rec_type in accuracy["1d"]:
                data = accuracy["1d"][rec_type]
                print(f"  • {rec_type}: {data['accuracy']:.1f}% (n={data['count']}, retour moyen: {data['avg_return']:.2f}%)")
        
        print(f"\n🤖 INSIGHTS POUR ML:")
        ml_insights = self.results["ml_insights"]
        if "recommendations_for_ml" in ml_insights:
            for i, rec in enumerate(ml_insights["recommendations_for_ml"], 1):
                print(f"  {i}. {rec}")
        
        print("\n" + "="*80)


async def main():
    """Fonction principale"""
    
    logger.info("🚀 Démarrage de l'analyse des performances des recommandations")
    
    db = next(get_db())
    
    try:
        # Créer l'analyseur
        analyzer = RecommendationPerformanceAnalyzer(db)
        
        # Exécuter l'analyse complète
        results = analyzer.run_complete_analysis()
        
        # Afficher le résumé
        analyzer.print_summary()
        
        # Sauvegarder les résultats
        analyzer.save_results()
        
        logger.info("✅ Analyse terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
