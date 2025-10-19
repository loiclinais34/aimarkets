#!/usr/bin/env python3
"""
Phase 1 : Optimisation des seuils actuels pour les recommandations ML (Version Simplifiée)
Grid Search sur les seuils RSI, MACD, BB pour améliorer les performances
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from itertools import product
import json
import sys
import os
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
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

@dataclass
class ThresholdConfig:
    """Configuration des seuils pour les recommandations"""
    # Seuils RSI
    rsi_oversold_strong: float = 30
    rsi_oversold_weak: float = 40
    rsi_overbought_weak: float = 60
    rsi_overbought_strong: float = 70
    
    # Seuils MACD
    macd_bullish: float = 0
    macd_bearish: float = 0
    
    # Seuils Bollinger Bands Position
    bb_oversold: float = 0.2
    bb_overbought: float = 0.8
    
    # Seuils ADX (force de tendance)
    adx_min_strength: float = 20
    
    # Confiance et retours potentiels
    confidence_strong: float = 0.85
    confidence_weak: float = 0.75
    confidence_hold: float = 0.6
    
    return_strong: float = 0.05
    return_weak: float = 0.03
    return_hold: float = 0.01

class SimpleThresholdOptimizer:
    """Optimiseur de seuils simplifié pour les recommandations ML"""
    
    def __init__(self):
        DATABASE_URL = settings.database_url
        self.engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = SessionLocal()
        
        # Configuration par défaut
        self.default_config = ThresholdConfig()
        
    def generate_recommendation(self, row: pd.Series, config: ThresholdConfig) -> Tuple[str, float, float]:
        """
        Génère une recommandation basée sur les indicateurs techniques et la configuration des seuils
        """
        rsi = row.get('rsi_14', 50)
        macd = row.get('macd', 0)
        bb_position = row.get('bb_position', 0.5)
        adx = row.get('adx_14', 20)
        
        # Logique de recommandation avec seuils configurables
        recommendation = "HOLD"
        confidence = config.confidence_hold
        potential_return = config.return_hold
        
        # BUY_STRONG : RSI très bas + MACD positif + BB très bas + ADX fort
        if (rsi < config.rsi_oversold_strong and 
            macd > config.macd_bullish and 
            bb_position < config.bb_oversold and
            adx > config.adx_min_strength):
            recommendation = "BUY_STRONG"
            confidence = config.confidence_strong
            potential_return = config.return_strong
            
        # BUY_WEAK : RSI bas + MACD positif
        elif (rsi < config.rsi_oversold_weak and 
              macd > config.macd_bullish):
            recommendation = "BUY_WEAK"
            confidence = config.confidence_weak
            potential_return = config.return_weak
            
        # SELL_STRONG : RSI très haut + MACD négatif + BB très haut + ADX fort
        elif (rsi > config.rsi_overbought_strong and 
              macd < config.macd_bearish and 
              bb_position > config.bb_overbought and
              adx > config.adx_min_strength):
            recommendation = "SELL_STRONG"
            confidence = config.confidence_strong
            potential_return = -config.return_strong
            
        # SELL_WEAK : RSI haut + MACD négatif
        elif (rsi > config.rsi_overbought_weak and 
              macd < config.macd_bearish):
            recommendation = "SELL_WEAK"
            confidence = config.confidence_weak
            potential_return = -config.return_weak
        
        return recommendation, confidence, potential_return
    
    def calculate_performance_metrics(self, df: pd.DataFrame, config: ThresholdConfig) -> Dict[str, float]:
        """
        Calcule les métriques de performance pour une configuration donnée
        """
        if df.empty:
            return {
                'accuracy': 0.0,
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_return': 0.0,
                'volatility': 0.0,
                'recommendation_distribution': {}
            }
        
        # Générer les recommandations
        recommendations = []
        confidences = []
        potential_returns = []
        
        for _, row in df.iterrows():
            rec, conf, ret = self.generate_recommendation(row, config)
            recommendations.append(rec)
            confidences.append(conf)
            potential_returns.append(ret)
        
        df['predicted_recommendation'] = recommendations
        df['predicted_confidence'] = confidences
        df['predicted_return'] = potential_returns
        
        # Calculer les métriques
        metrics = {}
        
        # Distribution des recommandations
        rec_counts = pd.Series(recommendations).value_counts()
        metrics['recommendation_distribution'] = rec_counts.to_dict()
        
        # Métriques de classification basées sur les retours prédits
        returns = df['predicted_return'].dropna()
        if len(returns) > 0:
            metrics['total_return'] = returns.sum()
            metrics['volatility'] = returns.std()
            metrics['sharpe_ratio'] = returns.mean() / returns.std() if returns.std() > 0 else 0.0
            
            # Win rate
            positive_returns = returns[returns > 0]
            metrics['win_rate'] = len(positive_returns) / len(returns) if len(returns) > 0 else 0.0
            
            # Profit factor
            gross_profit = positive_returns.sum() if len(positive_returns) > 0 else 0
            gross_loss = abs(returns[returns < 0].sum()) if len(returns[returns < 0]) > 0 else 0
            metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            
            # Max drawdown
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            metrics['max_drawdown'] = abs(drawdown.min())
            
            # Accuracy basée sur la cohérence des signaux
            buy_signals = df[df['predicted_recommendation'].isin(['BUY_STRONG', 'BUY_WEAK'])]
            sell_signals = df[df['predicted_recommendation'].isin(['SELL_STRONG', 'SELL_WEAK'])]
            
            # Calculer l'accuracy basée sur la cohérence interne
            total_signals = len(buy_signals) + len(sell_signals)
            if total_signals > 0:
                # Pour les signaux d'achat, vérifier que RSI < 50 et MACD > 0
                buy_coherent = 0
                for _, row in buy_signals.iterrows():
                    if row['rsi_14'] < 50 and row['macd'] > 0:
                        buy_coherent += 1
                
                # Pour les signaux de vente, vérifier que RSI > 50 et MACD < 0
                sell_coherent = 0
                for _, row in sell_signals.iterrows():
                    if row['rsi_14'] > 50 and row['macd'] < 0:
                        sell_coherent += 1
                
                metrics['accuracy'] = (buy_coherent + sell_coherent) / total_signals
            else:
                metrics['accuracy'] = 0.0
        else:
            metrics.update({
                'total_return': 0.0,
                'volatility': 0.0,
                'sharpe_ratio': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'max_drawdown': 0.0,
                'accuracy': 0.0
            })
        
        return metrics
    
    def load_training_data(self, symbol: str = None, limit: int = 2000) -> pd.DataFrame:
        """
        Charge les données d'entraînement depuis la base de données
        """
        logger.info(f"📊 Chargement des données d'entraînement...")
        
        # Requête pour récupérer les données avec les indicateurs techniques
        query = """
        SELECT 
            ati.symbol,
            ati.date,
            ati.rsi_14,
            ati.macd,
            ati.bb_position,
            ati.adx_14,
            hd.close,
            hd.volume
        FROM advanced_technical_indicators ati
        JOIN historical_data hd ON ati.symbol = hd.symbol AND ati.date = hd.date
        WHERE ati.rsi_14 IS NOT NULL 
            AND ati.macd IS NOT NULL 
            AND ati.bb_position IS NOT NULL
            AND ati.adx_14 IS NOT NULL
        """
        
        if symbol:
            query += f" AND ati.symbol = '{symbol}'"
        
        query += f" ORDER BY ati.date DESC LIMIT {limit}"
        
        df = pd.read_sql(query, self.db.connection())
        logger.info(f"   ✅ {len(df):,} enregistrements chargés")
        
        return df
    
    def simple_grid_search(self) -> Dict:
        """
        Effectue une recherche par grille simplifiée pour optimiser les seuils
        """
        logger.info("🔍 Début de l'optimisation par Grid Search simplifiée")
        
        # Charger les données d'entraînement
        training_data = self.load_training_data(limit=2000)
        
        if training_data.empty:
            logger.error("❌ Aucune donnée d'entraînement disponible")
            return {}
        
        # Plages réduites pour la démonstration
        rsi_oversold_strong_values = [25, 30, 35]
        rsi_oversold_weak_values = [35, 40, 45]
        rsi_overbought_weak_values = [55, 60, 65]
        rsi_overbought_strong_values = [65, 70, 75]
        
        bb_oversold_values = [0.1, 0.2, 0.3]
        bb_overbought_values = [0.7, 0.8, 0.9]
        
        confidence_strong_values = [0.8, 0.85, 0.9]
        confidence_weak_values = [0.7, 0.75, 0.8]
        
        return_strong_values = [0.03, 0.05, 0.07]
        return_weak_values = [0.02, 0.03, 0.04]
        
        # Calculer le nombre total de combinaisons
        total_combinations = (len(rsi_oversold_strong_values) * 
                            len(rsi_oversold_weak_values) * 
                            len(rsi_overbought_weak_values) * 
                            len(rsi_overbought_strong_values) * 
                            len(bb_oversold_values) * 
                            len(bb_overbought_values) * 
                            len(confidence_strong_values) * 
                            len(confidence_weak_values) * 
                            len(return_strong_values) * 
                            len(return_weak_values))
        
        logger.info(f"📊 {total_combinations:,} combinaisons à tester")
        
        best_configs = {
            'by_sharpe_ratio': {'config': None, 'score': -float('inf')},
            'by_accuracy': {'config': None, 'score': -float('inf')},
            'by_win_rate': {'config': None, 'score': -float('inf')},
            'by_profit_factor': {'config': None, 'score': -float('inf')}
        }
        
        tested_count = 0
        
        # Tester toutes les combinaisons
        for rsi_os_s in rsi_oversold_strong_values:
            for rsi_os_w in rsi_oversold_weak_values:
                for rsi_ob_w in rsi_overbought_weak_values:
                    for rsi_ob_s in rsi_overbought_strong_values:
                        for bb_os in bb_oversold_values:
                            for bb_ob in bb_overbought_values:
                                for conf_s in confidence_strong_values:
                                    for conf_w in confidence_weak_values:
                                        for ret_s in return_strong_values:
                                            for ret_w in return_weak_values:
                                                
                                                # Créer la configuration
                                                config = ThresholdConfig(
                                                    rsi_oversold_strong=rsi_os_s,
                                                    rsi_oversold_weak=rsi_os_w,
                                                    rsi_overbought_weak=rsi_ob_w,
                                                    rsi_overbought_strong=rsi_ob_s,
                                                    bb_oversold=bb_os,
                                                    bb_overbought=bb_ob,
                                                    confidence_strong=conf_s,
                                                    confidence_weak=conf_w,
                                                    return_strong=ret_s,
                                                    return_weak=ret_w
                                                )
                                                
                                                # Calculer les métriques
                                                metrics = self.calculate_performance_metrics(training_data, config)
                                                
                                                # Mettre à jour les meilleures configurations
                                                if metrics.get('sharpe_ratio', 0) > best_configs['by_sharpe_ratio']['score']:
                                                    best_configs['by_sharpe_ratio'] = {
                                                        'config': config,
                                                        'score': metrics.get('sharpe_ratio', 0),
                                                        'metrics': metrics
                                                    }
                                                
                                                if metrics.get('accuracy', 0) > best_configs['by_accuracy']['score']:
                                                    best_configs['by_accuracy'] = {
                                                        'config': config,
                                                        'score': metrics.get('accuracy', 0),
                                                        'metrics': metrics
                                                    }
                                                
                                                if metrics.get('win_rate', 0) > best_configs['by_win_rate']['score']:
                                                    best_configs['by_win_rate'] = {
                                                        'config': config,
                                                        'score': metrics.get('win_rate', 0),
                                                        'metrics': metrics
                                                    }
                                                
                                                if metrics.get('profit_factor', 0) > best_configs['by_profit_factor']['score']:
                                                    best_configs['by_profit_factor'] = {
                                                        'config': config,
                                                        'score': metrics.get('profit_factor', 0),
                                                        'metrics': metrics
                                                    }
                                                
                                                tested_count += 1
                                                
                                                if tested_count % 1000 == 0:
                                                    logger.info(f"   🔄 {tested_count:,}/{total_combinations:,} combinaisons testées")
        
        logger.info(f"✅ Optimisation terminée: {tested_count:,} combinaisons testées")
        
        return best_configs
    
    def save_results(self, results: Dict, filename: str = None):
        """
        Sauvegarde les résultats d'optimisation
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"threshold_optimization_results_{timestamp}.json"
        
        # Convertir les configurations en dictionnaires pour la sérialisation JSON
        serializable_results = {}
        
        for metric_name, result in results.items():
            if result['config'] is not None:
                config_dict = {
                    'rsi_oversold_strong': result['config'].rsi_oversold_strong,
                    'rsi_oversold_weak': result['config'].rsi_oversold_weak,
                    'rsi_overbought_weak': result['config'].rsi_overbought_weak,
                    'rsi_overbought_strong': result['config'].rsi_overbought_strong,
                    'macd_bullish': result['config'].macd_bullish,
                    'macd_bearish': result['config'].macd_bearish,
                    'bb_oversold': result['config'].bb_oversold,
                    'bb_overbought': result['config'].bb_overbought,
                    'confidence_strong': result['config'].confidence_strong,
                    'confidence_weak': result['config'].confidence_weak,
                    'confidence_hold': result['config'].confidence_hold,
                    'return_strong': result['config'].return_strong,
                    'return_weak': result['config'].return_weak,
                    'return_hold': result['config'].return_hold
                }
                
                serializable_results[metric_name] = {
                    'config': config_dict,
                    'score': result['score'],
                    'metrics': result['metrics']
                }
        
        filepath = os.path.join(backend_path, filename)
        
        with open(filepath, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"💾 Résultats sauvegardés dans {filepath}")
    
    def run_optimization(self):
        """Lance le processus d'optimisation complet"""
        logger.info("🚀 Début de la Phase 1 : Optimisation des seuils (Version Simplifiée)")
        
        try:
            # Phase 1 : Optimisation par Grid Search
            logger.info("\n📊 Phase 1 : Grid Search Optimization")
            
            optimization_results = self.simple_grid_search()
            
            # Afficher les résultats
            logger.info("\n📈 RÉSULTATS D'OPTIMISATION")
            logger.info("=" * 50)
            
            for metric_name, result in optimization_results.items():
                if result['config'] is not None:
                    logger.info(f"\n🏆 Meilleure configuration par {metric_name}:")
                    logger.info(f"   Score: {result['score']:.4f}")
                    logger.info(f"   Configuration:")
                    logger.info(f"     RSI Oversold Strong: {result['config'].rsi_oversold_strong}")
                    logger.info(f"     RSI Oversold Weak: {result['config'].rsi_oversold_weak}")
                    logger.info(f"     RSI Overbought Weak: {result['config'].rsi_overbought_weak}")
                    logger.info(f"     RSI Overbought Strong: {result['config'].rsi_overbought_strong}")
                    logger.info(f"     BB Oversold: {result['config'].bb_oversold}")
                    logger.info(f"     BB Overbought: {result['config'].bb_overbought}")
                    logger.info(f"     Confidence Strong: {result['config'].confidence_strong}")
                    logger.info(f"     Confidence Weak: {result['config'].confidence_weak}")
                    logger.info(f"     Return Strong: {result['config'].return_strong}")
                    logger.info(f"     Return Weak: {result['config'].return_weak}")
                    
                    if 'metrics' in result:
                        metrics = result['metrics']
                        logger.info(f"   Métriques:")
                        logger.info(f"     Accuracy: {metrics.get('accuracy', 0):.4f}")
                        logger.info(f"     Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.4f}")
                        logger.info(f"     Win Rate: {metrics.get('win_rate', 0):.4f}")
                        logger.info(f"     Profit Factor: {metrics.get('profit_factor', 0):.4f}")
                        logger.info(f"     Max Drawdown: {metrics.get('max_drawdown', 0):.4f}")
                        logger.info(f"     Total Return: {metrics.get('total_return', 0):.4f}")
                        logger.info(f"     Volatility: {metrics.get('volatility', 0):.4f}")
                        
                        if 'recommendation_distribution' in metrics:
                            logger.info(f"     Distribution des recommandations:")
                            for rec, count in metrics['recommendation_distribution'].items():
                                logger.info(f"       {rec}: {count}")
            
            # Sauvegarder les résultats
            self.save_results(optimization_results)
            
            logger.info("\n🎉 Phase 1 terminée avec succès!")
            logger.info("💡 Prochaines étapes:")
            logger.info("   1. Analyser les résultats d'optimisation")
            logger.info("   2. Implémenter les seuils optimisés dans le système")
            logger.info("   3. Tester sur de nouvelles données")
            logger.info("   4. Passer à la Phase 2 (Random Forest)")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'optimisation: {e}", exc_info=True)
        finally:
            self.db.close()

def main():
    """Fonction principale"""
    optimizer = SimpleThresholdOptimizer()
    optimizer.run_optimization()

if __name__ == "__main__":
    main()
