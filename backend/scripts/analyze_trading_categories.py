#!/usr/bin/env python3
"""
Script d'analyse des performances par catégories de trading
Évite le déséquilibre des classes en analysant les actions concrètes
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingCategoryAnalyzer:
    """Analyseur de performances par catégories de trading"""
    
    def __init__(self, db: Session):
        self.db = db
        self.results = {}
    
    def define_trading_categories(self) -> Dict:
        """Définit les catégories de trading basées sur les actions concrètes"""
        logger.info("📊 Définition des catégories de trading")
        
        # Catégories basées sur les actions concrètes
        categories = {
            "HOLD": {
                "description": "Maintenir la position actuelle",
                "action": "Ne rien faire",
                "context": "Portefeuille équilibré, pas de changement",
                "risk_level": "LOW",
                "expected_frequency": "70-80%"
            },
            "BUY_OPPORTUNITIES": {
                "description": "Opportunités d'achat (BUY + STRONG-BUY)",
                "action": "Acheter des actions",
                "context": "Peu de positions en portefeuille, recherche d'opportunités",
                "risk_level": "MEDIUM-HIGH",
                "expected_frequency": "15-25%"
            },
            "SELL_OPPORTUNITIES": {
                "description": "Opportunités de vente (SELL + STRONG-SELL)",
                "action": "Vendre des positions existantes",
                "context": "Gestion du portefeuille, prise de profits/limitation des pertes",
                "risk_level": "MEDIUM-HIGH", 
                "expected_frequency": "5-10%"
            }
        }
        
        return categories
    
    def analyze_category_performance(self) -> Dict:
        """Analyse les performances par catégorie de trading"""
        logger.info("🎯 Analyse des performances par catégorie")
        
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
        
        # Grouper par catégories
        categories_data = {
            "HOLD": [],
            "BUY_OPPORTUNITIES": [],
            "SELL_OPPORTUNITIES": []
        }
        
        for opp in opportunities:
            if opp.recommendation == "HOLD":
                categories_data["HOLD"].append(opp)
            elif opp.recommendation in ["BUY", "STRONG-BUY"]:
                categories_data["BUY_OPPORTUNITIES"].append(opp)
            elif opp.recommendation in ["SELL", "STRONG-SELL"]:
                categories_data["SELL_OPPORTUNITIES"].append(opp)
        
        # Analyser chaque catégorie
        results = {}
        for category, opps in categories_data.items():
            if not opps:
                results[category] = {
                    "count": 0,
                    "performance": "N/A"
                }
                continue
            
            # Calculer les métriques
            returns = [float(opp.return_1_day) for opp in opps if opp.return_1_day is not None]
            correct_predictions = sum(1 for opp in opps if opp.recommendation_correct_1_day is True)
            
            # Métriques de performance
            avg_return = np.mean(returns) if returns else 0
            std_return = np.std(returns) if len(returns) > 1 else 0
            sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
            accuracy = (correct_predictions / len(opps)) * 100
            
            # Taux de succès (retour positif)
            success_rate = sum(1 for r in returns if r > 0) / len(returns) * 100 if returns else 0
            
            # Analyse des retours
            positive_returns = [r for r in returns if r > 0]
            negative_returns = [r for r in returns if r < 0]
            
            results[category] = {
                "count": len(opps),
                "percentage": (len(opps) / len(opportunities)) * 100,
                "performance": {
                    "accuracy": accuracy,
                    "avg_return": avg_return * 100,
                    "std_return": std_return * 100,
                    "sharpe_ratio": sharpe_ratio,
                    "success_rate": success_rate,
                    "positive_returns": {
                        "count": len(positive_returns),
                        "avg": np.mean(positive_returns) * 100 if positive_returns else 0,
                        "max": np.max(positive_returns) * 100 if positive_returns else 0
                    },
                    "negative_returns": {
                        "count": len(negative_returns),
                        "avg": np.mean(negative_returns) * 100 if negative_returns else 0,
                        "min": np.min(negative_returns) * 100 if negative_returns else 0
                    }
                }
            }
        
        return results
    
    def analyze_category_risk_return(self) -> Dict:
        """Analyse risque/rendement par catégorie"""
        logger.info("⚠️ Analyse risque/rendement par catégorie")
        
        # Récupérer les données avec validation sur 3 horizons
        opportunities = self.db.query(HistoricalOpportunities)\
            .filter(
                and_(
                    HistoricalOpportunities.price_1_day_later.isnot(None),
                    HistoricalOpportunities.return_1_day.isnot(None)
                )
            ).all()
        
        if not opportunities:
            return {"error": "Pas de données disponibles"}
        
        # Grouper par catégories
        categories_data = {
            "HOLD": [],
            "BUY_OPPORTUNITIES": [],
            "SELL_OPPORTUNITIES": []
        }
        
        for opp in opportunities:
            if opp.recommendation == "HOLD":
                categories_data["HOLD"].append(opp)
            elif opp.recommendation in ["BUY", "STRONG-BUY"]:
                categories_data["BUY_OPPORTUNITIES"].append(opp)
            elif opp.recommendation in ["SELL", "STRONG-SELL"]:
                categories_data["SELL_OPPORTUNITIES"].append(opp)
        
        # Analyser sur 3 horizons
        results = {}
        for category, opps in categories_data.items():
            if not opps:
                results[category] = {"error": "Pas de données"}
                continue
            
            horizon_analysis = {}
            for period in [1, 7, 30]:
                period_key = f"{period}d"
                
                # Sélectionner les colonnes appropriées
                if period == 1:
                    return_col = "return_1_day"
                    correct_col = "recommendation_correct_1_day"
                elif period == 7:
                    return_col = "return_7_days"
                    correct_col = "recommendation_correct_7_days"
                else:  # period == 30
                    return_col = "return_30_days"
                    correct_col = "recommendation_correct_30_days"
                
                # Filtrer les opportunités avec données pour cette période
                valid_opps = [opp for opp in opps if getattr(opp, return_col) is not None]
                
                if not valid_opps:
                    horizon_analysis[period_key] = {"error": "Pas de données"}
                    continue
                
                # Calculer les métriques
                returns = [float(getattr(opp, return_col)) for opp in valid_opps]
                correct_predictions = sum(1 for opp in valid_opps if getattr(opp, correct_col) is True)
                
                avg_return = np.mean(returns)
                std_return = np.std(returns) if len(returns) > 1 else 0
                sharpe_ratio = (avg_return / std_return) if std_return > 0 else 0
                accuracy = (correct_predictions / len(valid_opps)) * 100
                
                # VaR (Value at Risk) - 5% percentile
                var_5 = np.percentile(returns, 5) * 100
                
                # Maximum drawdown
                cumulative_returns = np.cumprod(1 + np.array(returns))
                running_max = np.maximum.accumulate(cumulative_returns)
                drawdown = (cumulative_returns - running_max) / running_max
                max_drawdown = np.min(drawdown) * 100
                
                horizon_analysis[period_key] = {
                    "count": len(valid_opps),
                    "accuracy": accuracy,
                    "avg_return": avg_return * 100,
                    "std_return": std_return * 100,
                    "sharpe_ratio": sharpe_ratio,
                    "var_5_percent": var_5,
                    "max_drawdown": max_drawdown
                }
            
            results[category] = horizon_analysis
        
        return results
    
    def analyze_category_timing(self) -> Dict:
        """Analyse du timing des catégories"""
        logger.info("⏰ Analyse du timing des catégories")
        
        # Récupérer les données avec validation
        opportunities = self.db.query(HistoricalOpportunities)\
            .filter(
                and_(
                    HistoricalOpportunities.price_1_day_later.isnot(None),
                    HistoricalOpportunities.return_1_day.isnot(None)
                )
            ).all()
        
        if not opportunities:
            return {"error": "Pas de données disponibles"}
        
        # Grouper par catégories
        categories_data = {
            "HOLD": [],
            "BUY_OPPORTUNITIES": [],
            "SELL_OPPORTUNITIES": []
        }
        
        for opp in opportunities:
            if opp.recommendation == "HOLD":
                categories_data["HOLD"].append(opp)
            elif opp.recommendation in ["BUY", "STRONG-BUY"]:
                categories_data["BUY_OPPORTUNITIES"].append(opp)
            elif opp.recommendation in ["SELL", "STRONG-SELL"]:
                categories_data["SELL_OPPORTUNITIES"].append(opp)
        
        # Analyser le timing
        results = {}
        for category, opps in categories_data.items():
            if not opps:
                results[category] = {"error": "Pas de données"}
                continue
            
            # Analyser par mois
            monthly_data = {}
            for opp in opps:
                month = opp.opportunity_date.strftime('%Y-%m')
                if month not in monthly_data:
                    monthly_data[month] = []
                monthly_data[month].append(opp)
            
            # Calculer les performances mensuelles
            monthly_performance = {}
            for month, month_opps in monthly_data.items():
                returns = [float(opp.return_1_day) for opp in month_opps if opp.return_1_day is not None]
                if returns:
                    monthly_performance[month] = {
                        "count": len(month_opps),
                        "avg_return": np.mean(returns) * 100,
                        "success_rate": sum(1 for r in returns if r > 0) / len(returns) * 100
                    }
            
            results[category] = {
                "total_opportunities": len(opps),
                "monthly_distribution": monthly_performance,
                "best_month": max(monthly_performance.items(), key=lambda x: x[1]["avg_return"])[0] if monthly_performance else None,
                "worst_month": min(monthly_performance.items(), key=lambda x: x[1]["avg_return"])[0] if monthly_performance else None
            }
        
        return results
    
    def generate_trading_strategy_insights(self) -> Dict:
        """Génère des insights pour la stratégie de trading"""
        logger.info("💡 Génération d'insights stratégiques")
        
        # Récupérer les données
        opportunities = self.db.query(HistoricalOpportunities)\
            .filter(
                and_(
                    HistoricalOpportunities.price_1_day_later.isnot(None),
                    HistoricalOpportunities.return_1_day.isnot(None)
                )
            ).all()
        
        if not opportunities:
            return {"error": "Pas de données disponibles"}
        
        # Analyser les patterns
        buy_opps = [opp for opp in opportunities if opp.recommendation in ["BUY", "STRONG-BUY"]]
        sell_opps = [opp for opp in opportunities if opp.recommendation in ["SELL", "STRONG-SELL"]]
        hold_opps = [opp for opp in opportunities if opp.recommendation == "HOLD"]
        
        insights = {
            "portfolio_management": {
                "hold_strategy": {
                    "description": "Stratégie de maintien de position",
                    "frequency": len(hold_opps) / len(opportunities) * 100,
                    "recommendation": "Utiliser HOLD comme stratégie par défaut pour la stabilité du portefeuille"
                },
                "buy_strategy": {
                    "description": "Stratégie d'accumulation",
                    "frequency": len(buy_opps) / len(opportunities) * 100,
                    "recommendation": "Sélectionner rigoureusement les opportunités d'achat basées sur la qualité des signaux"
                },
                "sell_strategy": {
                    "description": "Stratégie de désinvestissement",
                    "frequency": len(sell_opps) / len(opportunities) * 100,
                    "recommendation": "Utiliser pour la gestion du risque et la prise de profits"
                }
            },
            "risk_management": {
                "position_sizing": "Ajuster la taille des positions selon la catégorie et la confiance",
                "diversification": "Maintenir la diversification même avec peu de positions",
                "stop_loss": "Implémenter des stops automatiques pour les positions BUY",
                "take_profit": "Utiliser les signaux SELL pour la prise de profits"
            },
            "execution_strategy": {
                "entry_timing": "Exécuter les ordres BUY sur confirmation des signaux",
                "exit_timing": "Exécuter les ordres SELL sur confirmation des signaux",
                "hold_period": "Maintenir les positions HOLD jusqu'à changement de signal",
                "rebalancing": "Rééquilibrer le portefeuille périodiquement"
            }
        }
        
        return insights
    
    def run_complete_analysis(self) -> Dict:
        """Exécute l'analyse complète par catégories"""
        logger.info("🚀 Démarrage de l'analyse complète par catégories")
        
        try:
            self.results = {
                "trading_categories": self.define_trading_categories(),
                "category_performance": self.analyze_category_performance(),
                "risk_return_analysis": self.analyze_category_risk_return(),
                "timing_analysis": self.analyze_category_timing(),
                "strategy_insights": self.generate_trading_strategy_insights()
            }
            
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse: {e}")
            raise
    
    def print_summary(self):
        """Affiche un résumé de l'analyse par catégories"""
        if not self.results:
            logger.warning("Aucun résultat à afficher")
            return
        
        categories = self.results["trading_categories"]
        performance = self.results["category_performance"]
        
        print("\n" + "="*80)
        print("📊 ANALYSE DES PERFORMANCES PAR CATÉGORIES DE TRADING")
        print("="*80)
        
        print(f"\n🎯 CATÉGORIES DE TRADING:")
        for category, info in categories.items():
            print(f"  • {category}: {info['description']}")
            print(f"    Action: {info['action']}")
            print(f"    Contexte: {info['context']}")
            print(f"    Fréquence attendue: {info['expected_frequency']}\n")
        
        print(f"📈 PERFORMANCES PAR CATÉGORIE:")
        for category, data in performance.items():
            if "error" in data:
                print(f"  • {category}: {data['error']}")
                continue
            
            perf = data["performance"]
            print(f"  • {category}:")
            print(f"    Nombre d'opportunités: {data['count']} ({data['percentage']:.1f}%)")
            print(f"    Précision: {perf['accuracy']:.1f}%")
            print(f"    Retour moyen: {perf['avg_return']:.2f}%")
            print(f"    Taux de succès: {perf['success_rate']:.1f}%")
            print(f"    Sharpe ratio: {perf['sharpe_ratio']:.3f}")
            print(f"    Retours positifs: {perf['positive_returns']['count']} (moy: {perf['positive_returns']['avg']:.2f}%)")
            print(f"    Retours négatifs: {perf['negative_returns']['count']} (moy: {perf['negative_returns']['avg']:.2f}%)\n")
        
        # Insights stratégiques
        insights = self.results["strategy_insights"]
        print(f"💡 INSIGHTS STRATÉGIQUES:")
        print(f"  • Gestion de portefeuille: {insights['portfolio_management']['hold_strategy']['recommendation']}")
        print(f"  • Stratégie d'achat: {insights['portfolio_management']['buy_strategy']['recommendation']}")
        print(f"  • Stratégie de vente: {insights['portfolio_management']['sell_strategy']['recommendation']}")
        print(f"  • Gestion du risque: {insights['risk_management']['position_sizing']}")
        
        print("\n" + "="*80)


def main():
    """Fonction principale"""
    
    logger.info("🚀 Démarrage de l'analyse par catégories de trading")
    
    db = next(get_db())
    
    try:
        # Créer l'analyseur
        analyzer = TradingCategoryAnalyzer(db)
        
        # Exécuter l'analyse
        results = analyzer.run_complete_analysis()
        
        # Afficher le résumé
        analyzer.print_summary()
        
        # Sauvegarder les résultats
        output_file = os.path.join(os.path.dirname(__file__), "trading_categories_analysis.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📁 Résultats sauvegardés dans {output_file}")
        logger.info("✅ Analyse par catégories terminée avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
