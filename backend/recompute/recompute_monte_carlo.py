#!/usr/bin/env python3
"""
Script de recalcul des simulations Monte Carlo
Calcule les simulations Monte Carlo pour l'analyse de risque
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging

from app.core.database import get_db
from app.models.database import HistoricalData
from app.models.sentiment_analysis import MonteCarloSimulations

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MonteCarloCalculator:
    """Calculateur de simulations Monte Carlo"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def calculate_monte_carlo_simulations(self, symbol: str, force_update: bool = False, 
                                        time_horizon: int = 30, simulations_count: int = 10000) -> dict:
        """
        Calcule les simulations Monte Carlo pour un symbole
        
        Args:
            symbol: Symbole à traiter
            force_update: Forcer le recalcul
            time_horizon: Horizon temporel en jours
            simulations_count: Nombre de simulations
        
        Returns:
            Dict contenant le résultat du calcul
        """
        try:
            logger.info(f"Calculating Monte Carlo simulations for {symbol}")
            
            # Vérifier si les simulations existent déjà et sont récents
            if not force_update:
                latest_simulation = self.db.query(MonteCarloSimulations)\
                    .filter(MonteCarloSimulations.symbol == symbol)\
                    .order_by(MonteCarloSimulations.created_at.desc())\
                    .first()
                
                if latest_simulation and latest_simulation.created_at >= datetime.now() - timedelta(days=1):
                    logger.info(f"Monte Carlo simulations for {symbol} are already up to date")
                    return {"status": "skipped", "reason": "already_up_to_date"}
            
            # Récupérer les données historiques (252 jours = 1 année de trading)
            historical_data = self.db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol
            ).order_by(HistoricalData.date.desc()).limit(252).all()
            
            if not historical_data:
                logger.warning(f"No historical data found for {symbol}")
                return {"status": "error", "symbol": symbol, "error": "No historical data"}
            
            # Convertir en DataFrame
            data = []
            for row in historical_data:
                data.append({
                    'date': row.date,
                    'close': float(row.close)
                })
            
            df = pd.DataFrame(data)
            df = df.sort_values('date').reset_index(drop=True)
            
            # Supprimer les anciennes simulations si force_update
            if force_update:
                self.db.query(MonteCarloSimulations).filter(MonteCarloSimulations.symbol == symbol).delete()
            
            # Calculer les rendements
            df['returns'] = np.log(df['close'] / df['close'].shift(1))
            df = df.dropna()
            
            if len(df) < 30:
                logger.warning(f"Insufficient data for Monte Carlo simulation for {symbol}")
                return {"status": "error", "symbol": symbol, "error": "Insufficient data"}
            
            # Calculer les paramètres
            current_price = df['close'].iloc[-1]
            volatility = df['returns'].std() * np.sqrt(252)
            drift = df['returns'].mean() * 252
            
            # Exécuter les simulations Monte Carlo
            simulation_results = self._run_monte_carlo_simulation(
                current_price, volatility, drift, time_horizon, simulations_count
            )
            
            # Créer l'enregistrement
            simulation = MonteCarloSimulations(
                symbol=symbol,
                analysis_date=datetime.now(),
                current_price=current_price,
                volatility=volatility,
                drift=drift,
                time_horizon=time_horizon,
                simulations_count=simulations_count,
                var_95=simulation_results['var_95'],
                var_99=simulation_results['var_99'],
                expected_shortfall_95=simulation_results['expected_shortfall_95'],
                expected_shortfall_99=simulation_results['expected_shortfall_99'],
                mean_return=simulation_results['mean_return'],
                std_return=simulation_results['std_return'],
                min_return=simulation_results['min_return'],
                max_return=simulation_results['max_return'],
                probability_positive_return=simulation_results['probability_positive_return'],
                stress_test_results=simulation_results['stress_test_results'],
                tail_risk_analysis=simulation_results['tail_risk_analysis']
            )
            
            self.db.add(simulation)
            self.db.commit()
            
            logger.info(f"Monte Carlo simulations calculated for {symbol}")
            return {
                "status": "success", 
                "symbol": symbol, 
                "simulations_created": 1
            }
            
        except Exception as e:
            logger.error(f"Error calculating Monte Carlo simulations for {symbol}: {e}")
            self.db.rollback()
            return {"status": "error", "symbol": symbol, "error": str(e)}
    
    def _run_monte_carlo_simulation(self, current_price: float, volatility: float, 
                                  drift: float, time_horizon: int, simulations_count: int) -> dict:
        """Exécuter les simulations Monte Carlo"""
        
        # Paramètres pour le modèle de Black-Scholes-Merton
        dt = 1/252  # Pas de temps quotidien
        sqrt_dt = np.sqrt(dt)
        
        # Initialiser les résultats
        final_prices = np.zeros(simulations_count)
        returns = np.zeros(simulations_count)
        
        # Exécuter les simulations
        for i in range(simulations_count):
            # Générer un chemin de prix aléatoire
            price_path = np.zeros(time_horizon + 1)
            price_path[0] = current_price
            
            for t in range(1, time_horizon + 1):
                # Mouvement brownien géométrique
                random_shock = np.random.normal(0, 1)
                price_path[t] = price_path[t-1] * np.exp(
                    (drift - 0.5 * volatility**2) * dt + volatility * sqrt_dt * random_shock
                )
            
            final_prices[i] = price_path[-1]
            returns[i] = (price_path[-1] - current_price) / current_price
        
        # Calculer les métriques de risque
        var_95 = np.percentile(returns, 5)  # VaR 95%
        var_99 = np.percentile(returns, 1)  # VaR 99%
        
        # Expected Shortfall (Conditional VaR)
        expected_shortfall_95 = np.mean(returns[returns <= var_95])
        expected_shortfall_99 = np.mean(returns[returns <= var_99])
        
        # Statistiques descriptives
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        min_return = np.min(returns)
        max_return = np.max(returns)
        probability_positive_return = np.mean(returns > 0)
        
        # Tests de stress
        stress_test_results = self._perform_stress_tests(returns)
        
        # Analyse des risques de queue
        tail_risk_analysis = self._analyze_tail_risk(returns)
        
        return {
            'var_95': float(var_95),
            'var_99': float(var_99),
            'expected_shortfall_95': float(expected_shortfall_95),
            'expected_shortfall_99': float(expected_shortfall_99),
            'mean_return': float(mean_return),
            'std_return': float(std_return),
            'min_return': float(min_return),
            'max_return': float(max_return),
            'probability_positive_return': float(probability_positive_return),
            'stress_test_results': stress_test_results,
            'tail_risk_analysis': tail_risk_analysis
        }
    
    def _perform_stress_tests(self, returns: np.ndarray) -> dict:
        """Effectuer des tests de stress"""
        return {
            'worst_case_1pct': float(np.percentile(returns, 1)),
            'worst_case_5pct': float(np.percentile(returns, 5)),
            'worst_case_10pct': float(np.percentile(returns, 10)),
            'extreme_loss_probability': float(np.mean(returns < -0.2)),  # Probabilité de perte > 20%
            'tail_expectation': float(np.mean(returns[returns < np.percentile(returns, 5)]))
        }
    
    def _analyze_tail_risk(self, returns: np.ndarray) -> dict:
        """Analyser les risques de queue"""
        # Calculer l'excès de kurtosis
        kurtosis = self._calculate_kurtosis(returns)
        
        # Calculer le skewness
        skewness = self._calculate_skewness(returns)
        
        # Calculer les moments d'ordre supérieur
        fourth_moment = np.mean((returns - np.mean(returns))**4)
        
        return {
            'kurtosis': float(kurtosis),
            'skewness': float(skewness),
            'fourth_moment': float(fourth_moment),
            'tail_thickness': 'heavy' if kurtosis > 3 else 'normal',
            'tail_asymmetry': 'left' if skewness < -0.5 else 'right' if skewness > 0.5 else 'symmetric'
        }
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculer l'excès de kurtosis"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return np.mean(((data - mean) / std)**4) - 3
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculer le skewness"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return np.mean(((data - mean) / std)**3)

def recompute_monte_carlo_simulations_for_symbol(symbol: str, force_update: bool = False, 
                                               time_horizon: int = 30, simulations_count: int = 10000) -> dict:
    """
    Recalculer les simulations Monte Carlo pour un symbole
    
    Args:
        symbol: Symbole à traiter
        force_update: Forcer le recalcul
        time_horizon: Horizon temporel en jours
        simulations_count: Nombre de simulations
    
    Returns:
        Dict contenant le résultat
    """
    try:
        db = next(get_db())
        calculator = MonteCarloCalculator(db)
        result = calculator.calculate_monte_carlo_simulations(symbol, force_update, time_horizon, simulations_count)
        return result
    except Exception as e:
        logger.error(f"Error in recompute_monte_carlo_simulations_for_symbol: {e}")
        return {"status": "error", "symbol": symbol, "error": str(e)}
    finally:
        db.close()

def recompute_monte_carlo_simulations_for_symbols(symbols: list, force_update: bool = False, 
                                                time_horizon: int = 30, simulations_count: int = 10000) -> dict:
    """
    Recalculer les simulations Monte Carlo pour plusieurs symboles
    
    Args:
        symbols: Liste des symboles à traiter
        force_update: Forcer le recalcul
        time_horizon: Horizon temporel en jours
        simulations_count: Nombre de simulations
    
    Returns:
        Dict contenant les résultats
    """
    results = {
        "total_symbols": len(symbols),
        "processed_symbols": 0,
        "successful_symbols": 0,
        "failed_symbols": 0,
        "total_simulations_created": 0,
        "errors": [],
        "start_time": datetime.now().isoformat()
    }
    
    logger.info(f"Starting Monte Carlo simulations recompute for {len(symbols)} symbols")
    
    for symbol in symbols:
        try:
            logger.info(f"Processing Monte Carlo simulations for {symbol}")
            result = recompute_monte_carlo_simulations_for_symbol(symbol, force_update, time_horizon, simulations_count)
            
            results["processed_symbols"] += 1
            
            if result["status"] == "success":
                results["successful_symbols"] += 1
                results["total_simulations_created"] += result.get("simulations_created", 0)
                logger.info(f"Monte Carlo simulations calculated successfully for {symbol}: {result.get('simulations_created', 0)} simulations")
            elif result["status"] == "skipped":
                results["successful_symbols"] += 1
                logger.info(f"Monte Carlo simulations skipped for {symbol}: {result.get('reason', 'Unknown')}")
            else:
                results["failed_symbols"] += 1
                results["errors"].append({
                    "symbol": symbol,
                    "error": result.get("error", "Unknown error")
                })
                logger.error(f"Failed to calculate Monte Carlo simulations for {symbol}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            results["processed_symbols"] += 1
            results["failed_symbols"] += 1
            results["errors"].append({
                "symbol": symbol,
                "error": str(e)
            })
            logger.error(f"Error processing {symbol}: {e}")
    
    results["end_time"] = datetime.now().isoformat()
    results["duration"] = (datetime.fromisoformat(results["end_time"]) - 
                          datetime.fromisoformat(results["start_time"])).total_seconds()
    
    logger.info(f"Monte Carlo simulations recompute completed: {results}")
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Recompute Monte Carlo simulations")
    parser.add_argument("--symbols", nargs="+", help="Symbols to recompute", default=["PLTR"])
    parser.add_argument("--force", action="store_true", help="Force recalculate")
    parser.add_argument("--time-horizon", type=int, default=30, help="Time horizon in days")
    parser.add_argument("--simulations", type=int, default=10000, help="Number of simulations")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Exécuter le recalcul
    results = recompute_monte_carlo_simulations_for_symbols(
        args.symbols, args.force, args.time_horizon, args.simulations
    )
    
    # Afficher les résultats
    print("\n" + "="*80)
    print("MONTE CARLO SIMULATIONS RECOMPUTE RESULTS")
    print("="*80)
    print(f"Total symbols: {results['total_symbols']}")
    print(f"Processed: {results['processed_symbols']}")
    print(f"Successful: {results['successful_symbols']}")
    print(f"Failed: {results['failed_symbols']}")
    print(f"Total simulations created: {results['total_simulations_created']}")
    print(f"Duration: {results['duration']:.2f} seconds")
    print(f"Success rate: {(results['successful_symbols']/results['processed_symbols']*100):.1f}%")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  {error['symbol']}: {error['error']}")
    
    print("="*80)
