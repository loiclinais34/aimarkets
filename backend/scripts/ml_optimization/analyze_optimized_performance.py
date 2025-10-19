#!/usr/bin/env python3
"""
Analyse des performances des nouvelles opportunités optimisées
Compare les KPIs avant/après optimisation des seuils
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
import sys
import os
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# Ajouter le chemin du backend
backend_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(backend_path)

from app.core.config import settings

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OptimizedPerformanceAnalyzer:
    """Analyseur de performance des opportunités optimisées"""
    
    def __init__(self):
        DATABASE_URL = settings.database_url
        self.engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = SessionLocal()
        
        # Métriques de performance
        self.metrics = {
            'total_opportunities': 0,
            'by_recommendation': {},
            'by_horizon': {},
            'performance_metrics': {},
            'comparison_results': {}
        }
    
    def calculate_actual_returns(self, opportunities_df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les retours réels pour chaque opportunité"""
        logger.info("📊 Calcul des retours réels...")
        
        opportunities_with_returns = []
        
        for _, opp in opportunities_df.iterrows():
            try:
                # Calculer la date future basée sur l'horizon
                future_date = opp['date'] + timedelta(days=opp['horizon_days'])
                
                # Récupérer le prix de clôture à la date de l'opportunité
                current_price_query = """
                SELECT close FROM historical_data 
                WHERE symbol = :symbol AND date = :date
                """
                current_price_result = self.db.execute(text(current_price_query), {
                    'symbol': opp['symbol'],
                    'date': opp['date']
                }).fetchone()
                
                if not current_price_result:
                    continue
                
                current_price = float(current_price_result[0])
                
                # Récupérer le prix de clôture à la date future
                future_price_query = """
                SELECT close FROM historical_data 
                WHERE symbol = :symbol AND date = :date
                """
                future_price_result = self.db.execute(text(future_price_query), {
                    'symbol': opp['symbol'],
                    'date': future_date
                }).fetchone()
                
                if not future_price_result:
                    continue
                
                future_price = float(future_price_result[0])
                
                # Calculer le retour réel
                actual_return = (future_price - current_price) / current_price
                
                # Ajouter à la liste
                opp_dict = opp.to_dict()
                opp_dict['actual_return'] = actual_return
                opp_dict['current_price'] = current_price
                opp_dict['future_price'] = future_price
                opp_dict['future_date'] = future_date
                
                opportunities_with_returns.append(opp_dict)
                
            except Exception as e:
                logger.warning(f"⚠️ Erreur pour {opp['symbol']} le {opp['date']}: {e}")
                continue
        
        logger.info(f"✅ {len(opportunities_with_returns)} opportunités avec retours calculés")
        return pd.DataFrame(opportunities_with_returns)
    
    def calculate_performance_metrics(self, df: pd.DataFrame) -> Dict:
        """Calcule les métriques de performance"""
        logger.info("📈 Calcul des métriques de performance...")
        
        if df.empty:
            return {}
        
        # Métriques générales
        total_opportunities = len(df)
        actual_returns = df['actual_return'].dropna()
        
        if actual_returns.empty:
            return {}
        
        # Métriques de base
        mean_return = actual_returns.mean()
        volatility = actual_returns.std()
        sharpe_ratio = mean_return / volatility if volatility > 0 else 0
        
        # Win rate
        winning_trades = (actual_returns > 0).sum()
        win_rate = winning_trades / len(actual_returns) if len(actual_returns) > 0 else 0
        
        # Profit factor
        profits = actual_returns[actual_returns > 0].sum()
        losses = abs(actual_returns[actual_returns < 0].sum())
        profit_factor = profits / losses if losses > 0 else float('inf')
        
        # Max drawdown
        cumulative_returns = (1 + actual_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Accuracy (pourcentage de prédictions correctes)
        correct_predictions = 0
        total_predictions = 0
        
        for _, row in df.iterrows():
            predicted_return = row['potential_return']
            actual_return = row['actual_return']
            
            if pd.notna(predicted_return) and pd.notna(actual_return):
                # Vérifier si la direction est correcte
                if (predicted_return > 0 and actual_return > 0) or (predicted_return < 0 and actual_return < 0):
                    correct_predictions += 1
                total_predictions += 1
        
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        # Distribution par recommandation
        recommendation_dist = df['recommendation'].value_counts().to_dict()
        
        # Distribution par horizon
        horizon_dist = df['horizon_days'].value_counts().to_dict()
        
        return {
            'total_opportunities': total_opportunities,
            'mean_return': mean_return,
            'volatility': volatility,
            'sharpe_ratio': sharpe_ratio,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown': max_drawdown,
            'accuracy': accuracy,
            'recommendation_distribution': recommendation_dist,
            'horizon_distribution': horizon_dist,
            'total_return': actual_returns.sum(),
            'positive_trades': winning_trades,
            'negative_trades': len(actual_returns) - winning_trades
        }
    
    def analyze_by_recommendation(self, df: pd.DataFrame) -> Dict:
        """Analyse les performances par type de recommandation"""
        logger.info("🎯 Analyse par type de recommandation...")
        
        results = {}
        
        for recommendation in df['recommendation'].unique():
            rec_df = df[df['recommendation'] == recommendation]
            if not rec_df.empty:
                metrics = self.calculate_performance_metrics(rec_df)
                results[recommendation] = metrics
        
        return results
    
    def analyze_by_horizon(self, df: pd.DataFrame) -> Dict:
        """Analyse les performances par horizon"""
        logger.info("⏰ Analyse par horizon...")
        
        results = {}
        
        for horizon in df['horizon_days'].unique():
            horizon_df = df[df['horizon_days'] == horizon]
            if not horizon_df.empty:
                metrics = self.calculate_performance_metrics(horizon_df)
                results[f"{horizon}d"] = metrics
        
        return results
    
    def load_optimized_opportunities(self) -> pd.DataFrame:
        """Charge les opportunités optimisées"""
        logger.info("📊 Chargement des opportunités optimisées...")
        
        query = """
        SELECT symbol, date, horizon_days, recommendation, confidence_level, 
               potential_return, risk_score, technical_indicators, ml_features
        FROM ml_opportunities_xgboost
        ORDER BY date DESC, symbol
        """
        
        df = pd.read_sql(query, self.db.connection())
        logger.info(f"✅ {len(df)} opportunités optimisées chargées")
        
        return df
    
    def compare_with_baseline(self) -> Dict:
        """Compare avec les métriques de référence (baseline)"""
        logger.info("📊 Comparaison avec les métriques de référence...")
        
        # Métriques de référence (estimées basées sur les résultats de la Phase 1)
        baseline_metrics = {
            'sharpe_ratio': 1.0,  # Baseline estimée
            'accuracy': 0.60,     # Baseline estimée
            'win_rate': 0.75,     # Baseline estimée
            'profit_factor': 2.0, # Baseline estimée
            'max_drawdown': -0.05 # Baseline estimée
        }
        
        return baseline_metrics
    
    def run_comprehensive_analysis(self):
        """Lance l'analyse complète des performances"""
        logger.info("🚀 Début de l'analyse des performances optimisées")
        
        try:
            # Charger les opportunités optimisées
            opportunities_df = self.load_optimized_opportunities()
            
            if opportunities_df.empty:
                logger.error("❌ Aucune opportunité optimisée trouvée")
                return
            
            # Calculer les retours réels
            opportunities_with_returns = self.calculate_actual_returns(opportunities_df)
            
            if opportunities_with_returns.empty:
                logger.error("❌ Aucun retour réel calculé")
                return
            
            # Métriques globales
            logger.info("\n📈 MÉTRIQUES GLOBALES")
            logger.info("=" * 50)
            
            global_metrics = self.calculate_performance_metrics(opportunities_with_returns)
            self.metrics['performance_metrics'] = global_metrics
            
            logger.info(f"📊 Total opportunités: {global_metrics['total_opportunities']:,}")
            logger.info(f"📈 Retour moyen: {global_metrics['mean_return']:.4f} ({global_metrics['mean_return']*100:.2f}%)")
            logger.info(f"📊 Volatilité: {global_metrics['volatility']:.4f}")
            logger.info(f"📈 Sharpe Ratio: {global_metrics['sharpe_ratio']:.4f}")
            logger.info(f"🎯 Win Rate: {global_metrics['win_rate']:.4f} ({global_metrics['win_rate']*100:.2f}%)")
            logger.info(f"💰 Profit Factor: {global_metrics['profit_factor']:.4f}")
            logger.info(f"📉 Max Drawdown: {global_metrics['max_drawdown']:.4f} ({global_metrics['max_drawdown']*100:.2f}%)")
            logger.info(f"🎯 Accuracy: {global_metrics['accuracy']:.4f} ({global_metrics['accuracy']*100:.2f}%)")
            logger.info(f"📊 Retour total: {global_metrics['total_return']:.4f} ({global_metrics['total_return']*100:.2f}%)")
            
            # Analyse par recommandation
            logger.info("\n🎯 PERFORMANCE PAR RECOMMANDATION")
            logger.info("=" * 50)
            
            rec_analysis = self.analyze_by_recommendation(opportunities_with_returns)
            
            for rec, metrics in rec_analysis.items():
                logger.info(f"\n📊 {rec}:")
                logger.info(f"   Opportunités: {metrics['total_opportunities']:,}")
                logger.info(f"   Retour moyen: {metrics['mean_return']:.4f} ({metrics['mean_return']*100:.2f}%)")
                logger.info(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.4f}")
                logger.info(f"   Win Rate: {metrics['win_rate']:.4f} ({metrics['win_rate']*100:.2f}%)")
                logger.info(f"   Accuracy: {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
                logger.info(f"   Profit Factor: {metrics['profit_factor']:.4f}")
            
            # Analyse par horizon
            logger.info("\n⏰ PERFORMANCE PAR HORIZON")
            logger.info("=" * 50)
            
            horizon_analysis = self.analyze_by_horizon(opportunities_with_returns)
            
            for horizon, metrics in horizon_analysis.items():
                logger.info(f"\n📊 {horizon}:")
                logger.info(f"   Opportunités: {metrics['total_opportunities']:,}")
                logger.info(f"   Retour moyen: {metrics['mean_return']:.4f} ({metrics['mean_return']*100:.2f}%)")
                logger.info(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.4f}")
                logger.info(f"   Win Rate: {metrics['win_rate']:.4f} ({metrics['win_rate']*100:.2f}%)")
                logger.info(f"   Accuracy: {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.2f}%)")
            
            # Comparaison avec baseline
            logger.info("\n📊 COMPARAISON AVEC BASELINE")
            logger.info("=" * 50)
            
            baseline = self.compare_with_baseline()
            
            logger.info(f"📈 Sharpe Ratio:")
            logger.info(f"   Baseline: {baseline['sharpe_ratio']:.4f}")
            logger.info(f"   Optimisé: {global_metrics['sharpe_ratio']:.4f}")
            logger.info(f"   Amélioration: {((global_metrics['sharpe_ratio'] / baseline['sharpe_ratio']) - 1) * 100:.1f}%")
            
            logger.info(f"🎯 Accuracy:")
            logger.info(f"   Baseline: {baseline['accuracy']:.4f}")
            logger.info(f"   Optimisé: {global_metrics['accuracy']:.4f}")
            logger.info(f"   Amélioration: {((global_metrics['accuracy'] / baseline['accuracy']) - 1) * 100:.1f}%")
            
            logger.info(f"🎯 Win Rate:")
            logger.info(f"   Baseline: {baseline['win_rate']:.4f}")
            logger.info(f"   Optimisé: {global_metrics['win_rate']:.4f}")
            logger.info(f"   Amélioration: {((global_metrics['win_rate'] / baseline['win_rate']) - 1) * 100:.1f}%")
            
            logger.info(f"💰 Profit Factor:")
            logger.info(f"   Baseline: {baseline['profit_factor']:.4f}")
            logger.info(f"   Optimisé: {global_metrics['profit_factor']:.4f}")
            logger.info(f"   Amélioration: {((global_metrics['profit_factor'] / baseline['profit_factor']) - 1) * 100:.1f}%")
            
            # Sauvegarder les résultats
            self.save_analysis_results(global_metrics, rec_analysis, horizon_analysis, baseline)
            
            logger.info("\n🎉 Analyse des performances terminée avec succès!")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse: {e}", exc_info=True)
            raise
        finally:
            self.db.close()
    
    def save_analysis_results(self, global_metrics: Dict, rec_analysis: Dict, horizon_analysis: Dict, baseline: Dict):
        """Sauvegarde les résultats de l'analyse"""
        logger.info("💾 Sauvegarde des résultats...")
        
        results = {
            'analysis_date': datetime.now().isoformat(),
            'global_metrics': global_metrics,
            'recommendation_analysis': rec_analysis,
            'horizon_analysis': horizon_analysis,
            'baseline_comparison': baseline,
            'improvements': {
                'sharpe_ratio_improvement': ((global_metrics['sharpe_ratio'] / baseline['sharpe_ratio']) - 1) * 100,
                'accuracy_improvement': ((global_metrics['accuracy'] / baseline['accuracy']) - 1) * 100,
                'win_rate_improvement': ((global_metrics['win_rate'] / baseline['win_rate']) - 1) * 100,
                'profit_factor_improvement': ((global_metrics['profit_factor'] / baseline['profit_factor']) - 1) * 100
            }
        }
        
        # Sauvegarder en JSON
        filename = f"optimized_performance_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = os.path.join(backend_path, filename)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"✅ Résultats sauvegardés dans {filepath}")

def main():
    """Fonction principale"""
    analyzer = OptimizedPerformanceAnalyzer()
    
    try:
        analyzer.run_comprehensive_analysis()
    except Exception as e:
        logger.error(f"❌ Erreur dans l'analyse: {e}")
        raise

if __name__ == "__main__":
    main()
