#!/usr/bin/env python3
"""
Système de simulation Monte Carlo pour tester les stratégies de trading.
Permet de tester différents paramètres et scénarios de marché.
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
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

# Ajouter le chemin du projet
sys.path.append('/Users/loiclinais/Documents/dev/aimarkets/backend')

load_dotenv()

class MonteCarloSimulator:
    """Classe pour les simulations Monte Carlo"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'aimarkets'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password')
        )
    
    def get_historical_returns(self, symbol: str, start_date: str = '2025-01-01') -> pd.Series:
        """Récupère les rendements historiques pour un symbole"""
        query = """
        SELECT date, close
        FROM historical_data 
        WHERE symbol = %s AND date >= %s
        ORDER BY date
        """
        df = pd.read_sql_query(query, self.conn, params=[symbol, start_date])
        
        if df.empty:
            return pd.Series()
        
        df['close'] = pd.to_numeric(df['close'])
        df['returns'] = df['close'].pct_change().dropna()
        
        return df['returns']
    
    def get_all_symbols_returns(self, start_date: str = '2025-01-01') -> Dict[str, pd.Series]:
        """Récupère les rendements pour tous les symboles"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT DISTINCT symbol 
            FROM historical_data 
            WHERE date >= %s
            ORDER BY symbol
        """, (start_date,))
        
        symbols = [row[0] for row in cur.fetchall()]
        cur.close()
        
        returns_data = {}
        for symbol in symbols:
            returns = self.get_historical_returns(symbol, start_date)
            if not returns.empty:
                returns_data[symbol] = returns
        
        return returns_data
    
    def calculate_market_statistics(self, returns_data: Dict[str, pd.Series]) -> Dict[str, Any]:
        """Calcule les statistiques du marché"""
        all_returns = []
        symbol_stats = {}
        
        for symbol, returns in returns_data.items():
            if len(returns) > 0:
                symbol_stats[symbol] = {
                    'mean_return': returns.mean(),
                    'std_return': returns.std(),
                    'skewness': returns.skew(),
                    'kurtosis': returns.kurtosis(),
                    'sharpe_ratio': returns.mean() / returns.std() if returns.std() > 0 else 0,
                    'max_drawdown': self.calculate_max_drawdown(returns),
                    'var_95': returns.quantile(0.05),
                    'cvar_95': returns[returns <= returns.quantile(0.05)].mean()
                }
                all_returns.extend(returns.tolist())
        
        # Statistiques globales du marché
        market_stats = {
            'overall_mean': np.mean(all_returns),
            'overall_std': np.std(all_returns),
            'overall_skewness': stats.skew(all_returns),
            'overall_kurtosis': stats.kurtosis(all_returns),
            'correlation_matrix': self.calculate_correlation_matrix(returns_data),
            'symbol_statistics': symbol_stats
        }
        
        return market_stats
    
    def calculate_max_drawdown(self, returns: pd.Series) -> float:
        """Calcule le drawdown maximum"""
        cumulative = (1 + returns).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown.min()
    
    def calculate_correlation_matrix(self, returns_data: Dict[str, pd.Series]) -> pd.DataFrame:
        """Calcule la matrice de corrélation entre les symboles"""
        # Créer un DataFrame avec tous les rendements alignés
        df = pd.DataFrame(returns_data)
        return df.corr()
    
    def generate_scenarios(self, 
                          base_returns: pd.Series, 
                          num_scenarios: int = 1000,
                          horizon_days: int = 30,
                          volatility_multiplier: float = 1.0,
                          drift_adjustment: float = 0.0) -> np.ndarray:
        """Génère des scénarios Monte Carlo"""
        
        if len(base_returns) == 0:
            return np.array([])
        
        # Paramètres statistiques
        mean_return = base_returns.mean()
        std_return = base_returns.std()
        
        # Ajustements
        adjusted_mean = mean_return + drift_adjustment
        adjusted_std = std_return * volatility_multiplier
        
        # Génération des scénarios
        scenarios = np.random.normal(
            loc=adjusted_mean,
            scale=adjusted_std,
            size=(num_scenarios, horizon_days)
        )
        
        return scenarios
    
    def simulate_portfolio_performance(self,
                                     scenarios: np.ndarray,
                                     initial_capital: float = 100000,
                                     position_size: float = 0.1,
                                     transaction_costs: float = 0.001) -> Dict[str, Any]:
        """Simule la performance d'un portefeuille"""
        
        if scenarios.size == 0:
            return {}
        
        num_scenarios, horizon_days = scenarios.shape
        portfolio_values = np.zeros((num_scenarios, horizon_days + 1))
        portfolio_values[:, 0] = initial_capital
        
        # Simulation de chaque scénario
        for i in range(num_scenarios):
            for j in range(horizon_days):
                # Calcul du rendement avec coûts de transaction
                gross_return = scenarios[i, j]
                net_return = gross_return - transaction_costs
                
                # Mise à jour de la valeur du portefeuille
                portfolio_values[i, j + 1] = portfolio_values[i, j] * (1 + net_return * position_size)
        
        # Calcul des métriques de performance
        final_values = portfolio_values[:, -1]
        returns = (final_values - initial_capital) / initial_capital
        
        performance_metrics = {
            'mean_return': np.mean(returns),
            'std_return': np.std(returns),
            'sharpe_ratio': np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0,
            'max_drawdown': self.calculate_max_drawdown_from_values(portfolio_values),
            'var_95': np.percentile(returns, 5),
            'cvar_95': np.mean(returns[returns <= np.percentile(returns, 5)]),
            'win_rate': np.mean(returns > 0),
            'profit_factor': self.calculate_profit_factor(returns),
            'scenarios': portfolio_values.tolist(),
            'final_values': final_values.tolist(),
            'returns': returns.tolist()
        }
        
        return performance_metrics
    
    def calculate_max_drawdown_from_values(self, portfolio_values: np.ndarray) -> float:
        """Calcule le drawdown maximum à partir des valeurs du portefeuille"""
        max_drawdowns = []
        
        for scenario in portfolio_values:
            running_max = np.maximum.accumulate(scenario)
            drawdown = (scenario - running_max) / running_max
            max_drawdowns.append(np.min(drawdown))
        
        return np.mean(max_drawdowns)
    
    def calculate_profit_factor(self, returns: np.ndarray) -> float:
        """Calcule le profit factor"""
        positive_returns = returns[returns > 0]
        negative_returns = returns[returns < 0]
        
        if len(negative_returns) == 0:
            return float('inf')
        
        gross_profit = np.sum(positive_returns)
        gross_loss = abs(np.sum(negative_returns))
        
        return gross_profit / gross_loss if gross_loss > 0 else 0
    
    def run_comprehensive_simulation(self,
                                   symbol: str,
                                   num_scenarios: int = 1000,
                                   horizon_days: int = 30,
                                   volatility_scenarios: List[float] = [0.5, 1.0, 1.5, 2.0],
                                   drift_scenarios: List[float] = [-0.001, 0.0, 0.001, 0.002]) -> Dict[str, Any]:
        """Exécute une simulation Monte Carlo complète"""
        
        print(f"🎲 Simulation Monte Carlo pour {symbol}...")
        
        # Récupérer les données historiques
        historical_returns = self.get_historical_returns(symbol)
        
        if historical_returns.empty:
            print(f"    ⚠️ Aucune donnée historique pour {symbol}")
            return {}
        
        print(f"    📊 {len(historical_returns)} jours de données historiques")
        
        # Statistiques historiques
        historical_stats = {
            'mean_return': historical_returns.mean(),
            'std_return': historical_returns.std(),
            'sharpe_ratio': historical_returns.mean() / historical_returns.std() if historical_returns.std() > 0 else 0,
            'max_drawdown': self.calculate_max_drawdown(historical_returns),
            'var_95': historical_returns.quantile(0.05),
            'cvar_95': historical_returns[historical_returns <= historical_returns.quantile(0.05)].mean()
        }
        
        # Simulations avec différents paramètres
        simulation_results = {}
        
        for vol_mult in volatility_scenarios:
            for drift_adj in drift_scenarios:
                scenario_name = f"vol_{vol_mult}_drift_{drift_adj}"
                
                # Générer les scénarios
                scenarios = self.generate_scenarios(
                    historical_returns,
                    num_scenarios=num_scenarios,
                    horizon_days=horizon_days,
                    volatility_multiplier=vol_mult,
                    drift_adjustment=drift_adj
                )
                
                # Simuler la performance
                performance = self.simulate_portfolio_performance(scenarios)
                
                if performance:
                    simulation_results[scenario_name] = {
                        'parameters': {
                            'volatility_multiplier': vol_mult,
                            'drift_adjustment': drift_adj,
                            'num_scenarios': num_scenarios,
                            'horizon_days': horizon_days
                        },
                        'performance': performance
                    }
        
        # Résultats complets
        comprehensive_results = {
            'symbol': symbol,
            'historical_statistics': historical_stats,
            'simulation_results': simulation_results,
            'best_scenario': self.find_best_scenario(simulation_results),
            'risk_analysis': self.analyze_risk_scenarios(simulation_results),
            'created_at': datetime.now().isoformat()
        }
        
        print(f"    ✅ Simulation terminée - {len(simulation_results)} scénarios testés")
        
        return comprehensive_results
    
    def find_best_scenario(self, simulation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Trouve le meilleur scénario basé sur le ratio de Sharpe"""
        best_scenario = None
        best_sharpe = -float('inf')
        
        for scenario_name, results in simulation_results.items():
            sharpe_ratio = results['performance'].get('sharpe_ratio', -float('inf'))
            if sharpe_ratio > best_sharpe:
                best_sharpe = sharpe_ratio
                best_scenario = {
                    'scenario_name': scenario_name,
                    'parameters': results['parameters'],
                    'performance': results['performance']
                }
        
        return best_scenario
    
    def analyze_risk_scenarios(self, simulation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse les scénarios de risque"""
        risk_analysis = {
            'high_risk_scenarios': [],
            'low_risk_scenarios': [],
            'extreme_scenarios': []
        }
        
        for scenario_name, results in simulation_results.items():
            performance = results['performance']
            var_95 = performance.get('var_95', 0)
            max_drawdown = performance.get('max_drawdown', 0)
            
            # Scénarios à haut risque
            if var_95 < -0.05 or max_drawdown < -0.1:
                risk_analysis['high_risk_scenarios'].append({
                    'scenario_name': scenario_name,
                    'var_95': var_95,
                    'max_drawdown': max_drawdown
                })
            
            # Scénarios à faible risque
            elif var_95 > -0.02 and max_drawdown > -0.05:
                risk_analysis['low_risk_scenarios'].append({
                    'scenario_name': scenario_name,
                    'var_95': var_95,
                    'max_drawdown': max_drawdown
                })
            
            # Scénarios extrêmes
            if var_95 < -0.1 or max_drawdown < -0.2:
                risk_analysis['extreme_scenarios'].append({
                    'scenario_name': scenario_name,
                    'var_95': var_95,
                    'max_drawdown': max_drawdown
                })
        
        return risk_analysis
    
    def save_simulation_to_db(self, simulation_results: Dict[str, Any]):
        """Sauvegarde les résultats de simulation dans la base de données"""
        cur = self.conn.cursor()
        
        simulation_name = f"monte_carlo_{simulation_results['symbol']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Créer la table si elle n'existe pas
        create_table_query = """
        CREATE TABLE IF NOT EXISTS monte_carlo_simulations_v2 (
            id SERIAL PRIMARY KEY,
            simulation_name VARCHAR(100) NOT NULL,
            symbol VARCHAR(10) NOT NULL,
            simulation_parameters JSONB,
            num_simulations INTEGER NOT NULL,
            simulation_horizon INTEGER NOT NULL,
            results JSONB,
            statistics JSONB,
            avg_return DECIMAL(8, 4),
            std_return DECIMAL(8, 4),
            sharpe_ratio DECIMAL(8, 4),
            max_drawdown DECIMAL(8, 4),
            var_95 DECIMAL(8, 4),
            cvar_95 DECIMAL(8, 4),
            status VARCHAR(20) DEFAULT 'COMPLETED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(simulation_name)
        )
        """
        cur.execute(create_table_query)
        
        # Insérer dans la nouvelle table
        insert_query = """
        INSERT INTO monte_carlo_simulations_v2 
        (simulation_name, symbol, simulation_parameters, num_simulations, simulation_horizon,
         results, statistics, avg_return, std_return, sharpe_ratio, max_drawdown, var_95, cvar_95, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Calculer les statistiques globales
        all_returns = []
        for scenario_results in simulation_results['simulation_results'].values():
            all_returns.extend(scenario_results['performance']['returns'])
        
        global_stats = {
            'avg_return': np.mean(all_returns),
            'std_return': np.std(all_returns),
            'sharpe_ratio': np.mean(all_returns) / np.std(all_returns) if np.std(all_returns) > 0 else 0,
            'max_drawdown': np.min(all_returns),
            'var_95': np.percentile(all_returns, 5),
            'cvar_95': np.mean([r for r in all_returns if r <= np.percentile(all_returns, 5)])
        }
        
        cur.execute(insert_query, (
            simulation_name,
            simulation_results['symbol'],
            json.dumps(simulation_results['simulation_results']),
            1000,  # num_simulations
            30,    # simulation_horizon
            json.dumps(simulation_results),
            json.dumps(global_stats),
            global_stats['avg_return'],
            global_stats['std_return'],
            global_stats['sharpe_ratio'],
            global_stats['max_drawdown'],
            global_stats['var_95'],
            global_stats['cvar_95'],
            'COMPLETED'
        ))
        
        self.conn.commit()
        cur.close()
        
        print(f"    💾 Simulation sauvegardée: {simulation_name}")
    
    def run_simulations_for_top_symbols(self, num_symbols: int = 10):
        """Exécute les simulations pour les symboles les plus performants"""
        
        # Récupérer les symboles avec les meilleures performances historiques
        returns_data = self.get_all_symbols_returns()
        
        # Calculer les statistiques de marché
        market_stats = self.calculate_market_statistics(returns_data)
        
        # Trier par ratio de Sharpe
        symbol_performance = []
        for symbol, stats in market_stats['symbol_statistics'].items():
            symbol_performance.append((symbol, stats['sharpe_ratio']))
        
        symbol_performance.sort(key=lambda x: x[1], reverse=True)
        top_symbols = [symbol for symbol, _ in symbol_performance[:num_symbols]]
        
        print(f"🎯 Simulation Monte Carlo pour les {num_symbols} meilleurs symboles:")
        for i, symbol in enumerate(top_symbols, 1):
            print(f"  [{i}/{num_symbols}] {symbol}")
        
        # Exécuter les simulations
        for symbol in top_symbols:
            try:
                simulation_results = self.run_comprehensive_simulation(symbol)
                if simulation_results:
                    self.save_simulation_to_db(simulation_results)
            except Exception as e:
                print(f"    ❌ Erreur pour {symbol}: {str(e)}")
        
        print("✅ Simulations Monte Carlo terminées!")
    
    def close(self):
        """Ferme la connexion à la base de données"""
        self.conn.close()

def main():
    """Fonction principale"""
    print("🎲 Démarrage des simulations Monte Carlo...")
    
    simulator = MonteCarloSimulator()
    
    try:
        # Exécuter les simulations pour les 10 meilleurs symboles
        simulator.run_simulations_for_top_symbols(10)
        
        # Vérifier les résultats
        cur = simulator.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM monte_carlo_simulations_v2")
        count = cur.fetchone()[0]
        print(f"\\n📊 Total de simulations sauvegardées: {count}")
        
        cur.close()
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
    finally:
        simulator.close()

if __name__ == "__main__":
    main()
