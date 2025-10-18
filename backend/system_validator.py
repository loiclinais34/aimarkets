#!/usr/bin/env python3
"""
Système de test et validation complet pour le nouveau système ML sophistiqué.
Compare les performances avec l'ancien système et valide les améliorations.
"""

import os
import sys
import pandas as pd
import numpy as np
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
import json
import warnings
warnings.filterwarnings('ignore')

# Ajouter le chemin du projet
sys.path.append('/Users/loiclinais/Documents/dev/aimarkets/backend')

load_dotenv()

class SystemValidator:
    """Classe pour valider et tester le nouveau système ML"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'aimarkets'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password')
        )
    
    def analyze_old_system_performance(self) -> Dict[str, Any]:
        """Analyse les performances de l'ancien système"""
        
        print("📊 Analyse des performances de l'ancien système...")
        
        cur = self.conn.cursor()
        
        # Analyser les opportunités historiques existantes
        cur.execute("""
            SELECT 
                recommendation,
                COUNT(*) as count,
                AVG(CASE 
                    WHEN confidence_level ~ '^[0-9]+\\.?[0-9]*$' 
                    THEN CAST(confidence_level AS FLOAT)
                    ELSE CASE confidence_level
                        WHEN 'LOW' THEN 0.3
                        WHEN 'MEDIUM' THEN 0.6
                        WHEN 'HIGH' THEN 0.8
                        WHEN 'VERY_HIGH' THEN 0.9
                        ELSE 0.5
                    END
                END) as avg_confidence
            FROM historical_opportunities 
            WHERE opportunity_date >= '2025-01-01'
            GROUP BY recommendation 
            ORDER BY count DESC
        """)
        
        old_performance = {}
        for row in cur.fetchall():
            recommendation, count, avg_confidence = row
            old_performance[recommendation] = {
                'count': count,
                'avg_confidence': avg_confidence or 0
            }
        
        cur.close()
        
        print(f"    ✅ {len(old_performance)} types de recommandations analysés")
        
        return old_performance
    
    def analyze_new_system_performance(self) -> Dict[str, Any]:
        """Analyse les performances du nouveau système ML"""
        
        print("🤖 Analyse des performances du nouveau système ML...")
        
        cur = self.conn.cursor()
        
        # Analyser les modèles ML entraînés
        cur.execute("""
            SELECT 
                model_name,
                model_type,
                training_score,
                test_score,
                feature_importance,
                created_at
            FROM ml_models_v2 
            WHERE is_active = true
            ORDER BY created_at DESC
        """)
        
        ml_models = []
        for row in cur.fetchall():
            model_name, model_type, training_score, test_score, feature_importance, created_at = row
            ml_models.append({
                'model_name': model_name,
                'model_type': model_type,
                'training_score': training_score,
                'test_score': test_score,
                'feature_importance': json.loads(feature_importance) if isinstance(feature_importance, str) else feature_importance,
                'created_at': created_at
            })
        
        # Analyser les simulations Monte Carlo
        cur.execute("""
            SELECT 
                symbol,
                COUNT(*) as simulation_count,
                AVG(sharpe_ratio) as avg_sharpe,
                AVG(max_drawdown) as avg_max_drawdown,
                AVG(var_95) as avg_var_95
            FROM monte_carlo_simulations_v2 
            WHERE status = 'COMPLETED'
            GROUP BY symbol
            ORDER BY avg_sharpe DESC
        """)
        
        monte_carlo_results = {}
        for row in cur.fetchall():
            symbol, sim_count, avg_sharpe, avg_drawdown, avg_var = row
            monte_carlo_results[symbol] = {
                'simulation_count': sim_count,
                'avg_sharpe': avg_sharpe or 0,
                'avg_max_drawdown': avg_drawdown or 0,
                'avg_var_95': avg_var or 0
            }
        
        # Analyser les indicateurs techniques
        cur.execute("""
            SELECT 
                COUNT(*) as total_indicators,
                COUNT(DISTINCT symbol) as symbols_with_indicators,
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM advanced_technical_indicators
        """)
        
        indicators_stats = cur.fetchone()
        
        cur.close()
        
        new_performance = {
            'ml_models': ml_models,
            'monte_carlo_results': monte_carlo_results,
            'indicators_stats': {
                'total_indicators': indicators_stats[0],
                'symbols_with_indicators': indicators_stats[1],
                'earliest_date': indicators_stats[2],
                'latest_date': indicators_stats[3]
            }
        }
        
        print(f"    ✅ {len(ml_models)} modèles ML analysés")
        print(f"    ✅ {len(monte_carlo_results)} simulations Monte Carlo analysées")
        print(f"    ✅ {indicators_stats[0]} indicateurs techniques calculés")
        
        return new_performance
    
    def compare_systems(self, old_performance: Dict[str, Any], new_performance: Dict[str, Any]) -> Dict[str, Any]:
        """Compare les performances des deux systèmes"""
        
        print("⚖️ Comparaison des systèmes...")
        
        comparison = {
            'old_system': {
                'recommendation_types': len(old_performance),
                'total_opportunities': sum(data['count'] for data in old_performance.values()),
                'avg_confidence': np.mean([data['avg_confidence'] for data in old_performance.values()]),
                'recommendation_distribution': old_performance
            },
            'new_system': {
                'ml_models_count': len(new_performance['ml_models']),
                'monte_carlo_simulations': len(new_performance['monte_carlo_results']),
                'technical_indicators': new_performance['indicators_stats']['total_indicators'],
                'symbols_covered': new_performance['indicators_stats']['symbols_with_indicators'],
                'best_ml_accuracy': max([model['training_score'] for model in new_performance['ml_models']], default=0),
                'best_sharpe_ratio': max([data['avg_sharpe'] for data in new_performance['monte_carlo_results'].values()], default=0)
            },
            'improvements': {}
        }
        
        # Calculer les améliorations
        if new_performance['ml_models']:
            best_ml_score = max([model['training_score'] for model in new_performance['ml_models']])
            comparison['improvements']['ml_accuracy'] = best_ml_score
        
        if new_performance['monte_carlo_results']:
            best_sharpe = max([data['avg_sharpe'] for data in new_performance['monte_carlo_results'].values()])
            comparison['improvements']['best_sharpe_ratio'] = best_sharpe
        
        comparison['improvements']['technical_coverage'] = new_performance['indicators_stats']['symbols_with_indicators']
        comparison['improvements']['data_points'] = new_performance['indicators_stats']['total_indicators']
        
        print(f"    ✅ Comparaison terminée")
        
        return comparison
    
    def generate_recommendations_with_new_system(self, symbols: List[str], date: str = '2025-10-17') -> Dict[str, Any]:
        """Génère des recommandations avec le nouveau système ML"""
        
        print(f"🎯 Génération de recommandations pour {len(symbols)} symboles...")
        
        recommendations = {}
        
        for symbol in symbols:
            try:
                # Simuler une recommandation basée sur les données ML disponibles
                recommendation = self.simulate_ml_recommendation(symbol, date)
                recommendations[symbol] = recommendation
                
            except Exception as e:
                recommendations[symbol] = {
                    'symbol': symbol,
                    'error': str(e)
                }
        
        print(f"    ✅ {len(recommendations)} recommandations générées")
        
        return recommendations
    
    def simulate_ml_recommendation(self, symbol: str, date: str) -> Dict[str, Any]:
        """Simule une recommandation ML basée sur les données disponibles"""
        
        cur = self.conn.cursor()
        
        # Récupérer les données techniques pour le symbole
        cur.execute("""
            SELECT 
                symbol, date, rsi_14, macd_line, macd_signal,
                bollinger_upper, bollinger_middle, bollinger_lower,
                stochastic_k, stochastic_d, atr_14, volatility_20
            FROM advanced_technical_indicators 
            WHERE symbol = %s AND date = %s
        """, (symbol, date))
        
        tech_data = cur.fetchone()
        
        if not tech_data:
            return {
                'symbol': symbol,
                'date': date,
                'recommendation': 'HOLD',
                'confidence_level': 0.5,
                'reasoning': 'Données techniques insuffisantes'
            }
        
        # Récupérer les résultats Monte Carlo
        cur.execute("""
            SELECT 
                avg_sharpe, avg_max_drawdown, avg_var_95
            FROM monte_carlo_simulations_v2 
            WHERE symbol = %s AND status = 'COMPLETED'
            ORDER BY created_at DESC
            LIMIT 1
        """, (symbol,))
        
        mc_data = cur.fetchone()
        
        cur.close()
        
        # Logique de recommandation simplifiée basée sur les indicateurs
        rsi_14, macd_line, macd_signal, bb_upper, bb_middle, bb_lower, stoch_k, stoch_d, atr_14, vol_20 = tech_data[2:]
        
        # Calculer un score composite
        score = 0
        confidence = 0.5
        
        # RSI
        if rsi_14 and not pd.isna(rsi_14):
            if rsi_14 < 30:
                score += 2  # Survente
                confidence += 0.1
            elif rsi_14 > 70:
                score -= 2  # Surachat
                confidence += 0.1
        
        # MACD
        if macd_line and macd_signal and not pd.isna(macd_line) and not pd.isna(macd_signal):
            if macd_line > macd_signal:
                score += 1
                confidence += 0.05
            else:
                score -= 1
                confidence += 0.05
        
        # Bollinger Bands
        if bb_upper and bb_middle and bb_lower and not pd.isna(bb_upper):
            # Position dans les bandes (approximation)
            bb_position = (bb_upper - bb_lower) / bb_middle if bb_middle > 0 else 0
            if bb_position > 0.1:  # Volatilité élevée
                confidence += 0.05
        
        # Stochastic
        if stoch_k and stoch_d and not pd.isna(stoch_k) and not pd.isna(stoch_d):
            if stoch_k < 20 and stoch_d < 20:
                score += 1
                confidence += 0.05
            elif stoch_k > 80 and stoch_d > 80:
                score -= 1
                confidence += 0.05
        
        # Monte Carlo
        if mc_data and mc_data[0]:
            sharpe_ratio = mc_data[0]
            if sharpe_ratio > 1.0:
                score += 1
                confidence += 0.1
            elif sharpe_ratio < 0:
                score -= 1
                confidence += 0.05
        
        # Déterminer la recommandation
        if score >= 3 and confidence >= 0.7:
            recommendation = 'BUY_STRONG'
        elif score >= 2 and confidence >= 0.6:
            recommendation = 'BUY_MODERATE'
        elif score >= 1 and confidence >= 0.5:
            recommendation = 'BUY_WEAK'
        elif score <= -3 and confidence >= 0.7:
            recommendation = 'SELL_STRONG'
        elif score <= -2 and confidence >= 0.6:
            recommendation = 'SELL_WEAK'
        else:
            recommendation = 'HOLD'
        
        return {
            'symbol': symbol,
            'date': date,
            'recommendation': recommendation,
            'confidence_level': min(confidence, 1.0),
            'composite_score': score,
            'reasoning': f'Score composite: {score}, Confiance: {confidence:.3f}',
            'technical_indicators': {
                'rsi_14': rsi_14,
                'macd_line': macd_line,
                'macd_signal': macd_signal,
                'stochastic_k': stoch_k,
                'stochastic_d': stoch_d
            },
            'monte_carlo_sharpe': mc_data[0] if mc_data else None
        }
    
    def validate_system_improvements(self) -> Dict[str, Any]:
        """Valide les améliorations du système"""
        
        print("🔍 Validation des améliorations du système...")
        
        validation_results = {
            'data_quality': {},
            'model_performance': {},
            'system_reliability': {},
            'recommendations': []
        }
        
        # Validation de la qualité des données
        cur = self.conn.cursor()
        
        # Vérifier la couverture des indicateurs techniques
        cur.execute("""
            SELECT 
                COUNT(DISTINCT symbol) as symbols_with_indicators,
                COUNT(*) as total_indicators,
                AVG(CASE WHEN rsi_14 IS NOT NULL THEN 1 ELSE 0 END) as rsi_coverage,
                AVG(CASE WHEN macd_line IS NOT NULL THEN 1 ELSE 0 END) as macd_coverage,
                AVG(CASE WHEN bollinger_upper IS NOT NULL THEN 1 ELSE 0 END) as bb_coverage
            FROM advanced_technical_indicators
        """)
        
        data_quality = cur.fetchone()
        validation_results['data_quality'] = {
            'symbols_with_indicators': data_quality[0],
            'total_indicators': data_quality[1],
            'rsi_coverage': data_quality[2] or 0,
            'macd_coverage': data_quality[3] or 0,
            'bb_coverage': data_quality[4] or 0
        }
        
        # Validation des performances des modèles
        cur.execute("""
            SELECT 
                model_type,
                AVG(training_score) as avg_training_score,
                AVG(test_score) as avg_test_score,
                COUNT(*) as model_count
            FROM ml_models_v2 
            WHERE is_active = true
            GROUP BY model_type
        """)
        
        model_performance = {}
        for row in cur.fetchall():
            model_type, avg_training, avg_test, count = row
            model_performance[model_type] = {
                'avg_training_score': avg_training or 0,
                'avg_test_score': avg_test or 0,
                'model_count': count
            }
        
        validation_results['model_performance'] = model_performance
        
        # Validation de la fiabilité du système
        cur.execute("""
            SELECT 
                COUNT(*) as total_simulations,
                AVG(sharpe_ratio) as avg_sharpe,
                AVG(max_drawdown) as avg_drawdown,
                COUNT(DISTINCT symbol) as symbols_simulated
            FROM monte_carlo_simulations_v2 
            WHERE status = 'COMPLETED'
        """)
        
        reliability = cur.fetchone()
        validation_results['system_reliability'] = {
            'total_simulations': reliability[0],
            'avg_sharpe_ratio': reliability[1] or 0,
            'avg_max_drawdown': reliability[2] or 0,
            'symbols_simulated': reliability[3]
        }
        
        cur.close()
        
        # Générer des recommandations de validation
        recommendations = []
        
        if validation_results['data_quality']['rsi_coverage'] < 0.8:
            recommendations.append("Améliorer la couverture des indicateurs RSI")
        
        if validation_results['model_performance']:
            best_model_score = max([data['avg_training_score'] for data in validation_results['model_performance'].values()])
            if best_model_score < 0.7:
                recommendations.append("Améliorer la précision des modèles ML")
        
        if validation_results['system_reliability']['avg_sharpe_ratio'] < 0.5:
            recommendations.append("Optimiser les stratégies Monte Carlo")
        
        validation_results['recommendations'] = recommendations
        
        print(f"    ✅ Validation terminée - {len(recommendations)} recommandations générées")
        
        return validation_results
    
    def generate_final_report(self) -> Dict[str, Any]:
        """Génère le rapport final de validation"""
        
        print("📋 Génération du rapport final...")
        
        # Analyser les deux systèmes
        old_performance = self.analyze_old_system_performance()
        new_performance = self.analyze_new_system_performance()
        
        # Comparer les systèmes
        comparison = self.compare_systems(old_performance, new_performance)
        
        # Valider les améliorations
        validation = self.validate_system_improvements()
        
        # Générer des recommandations de test
        test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMZN', 'META', 'NFLX', 'AMD', 'INTC']
        ml_recommendations = self.generate_recommendations_with_new_system(test_symbols)
        
        # Rapport final
        final_report = {
            'timestamp': datetime.now().isoformat(),
            'system_comparison': comparison,
            'validation_results': validation,
            'test_recommendations': ml_recommendations,
            'summary': {
                'old_system_opportunities': comparison['old_system']['total_opportunities'],
                'new_system_indicators': comparison['new_system']['technical_indicators'],
                'ml_models_trained': comparison['new_system']['ml_models_count'],
                'monte_carlo_simulations': comparison['new_system']['monte_carlo_simulations'],
                'best_ml_accuracy': comparison['new_system']['best_ml_accuracy'],
                'best_sharpe_ratio': comparison['new_system']['best_sharpe_ratio']
            }
        }
        
        print("    ✅ Rapport final généré")
        
        return final_report
    
    def close(self):
        """Ferme la connexion à la base de données"""
        self.conn.close()

def main():
    """Fonction principale"""
    print("🧪 Démarrage de la validation du système ML sophistiqué...")
    
    validator = SystemValidator()
    
    try:
        # Générer le rapport final
        report = validator.generate_final_report()
        
        # Afficher le résumé
        print("\\n📊 RÉSUMÉ DE LA VALIDATION:")
        print(f"  Ancien système: {report['summary']['old_system_opportunities']} opportunités")
        print(f"  Nouveau système: {report['summary']['new_system_indicators']} indicateurs techniques")
        print(f"  Modèles ML: {report['summary']['ml_models_trained']} modèles entraînés")
        print(f"  Simulations Monte Carlo: {report['summary']['monte_carlo_simulations']} simulations")
        print(f"  Meilleure précision ML: {report['summary']['best_ml_accuracy']:.3f}")
        print(f"  Meilleur ratio Sharpe: {report['summary']['best_sharpe_ratio']:.3f}")
        
        # Afficher les recommandations de test
        print("\\n🎯 RECOMMANDATIONS DE TEST:")
        for symbol, rec in report['test_recommendations'].items():
            if 'error' not in rec:
                print(f"  {symbol}: {rec['recommendation']} (confiance: {rec['confidence_level']:.3f})")
        
        # Afficher les recommandations d'amélioration
        if report['validation_results']['recommendations']:
            print("\\n💡 RECOMMANDATIONS D'AMÉLIORATION:")
            for rec in report['validation_results']['recommendations']:
                print(f"  - {rec}")
        
        print("\\n✅ Validation terminée!")
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
    finally:
        validator.close()

if __name__ == "__main__":
    main()
