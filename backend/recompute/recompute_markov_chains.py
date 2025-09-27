#!/usr/bin/env python3
"""
Script de recalcul des chaînes de Markov
Calcule les modèles de chaînes de Markov pour l'analyse des régimes de marché
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
from app.models.sentiment_analysis import MarkovChainAnalysis

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MarkovChainCalculator:
    """Calculateur de chaînes de Markov"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def calculate_markov_chain_analysis(self, symbol: str, force_update: bool = False) -> dict:
        """
        Calcule l'analyse des chaînes de Markov pour un symbole
        
        Args:
            symbol: Symbole à traiter
            force_update: Forcer le recalcul
        
        Returns:
            Dict contenant le résultat du calcul
        """
        try:
            logger.info(f"Calculating Markov chain analysis for {symbol}")
            
            # Vérifier si l'analyse existe déjà et est récente
            if not force_update:
                latest_analysis = self.db.query(MarkovChainAnalysis)\
                    .filter(MarkovChainAnalysis.symbol == symbol)\
                    .order_by(MarkovChainAnalysis.created_at.desc())\
                    .first()
                
                if latest_analysis and latest_analysis.created_at >= datetime.now() - timedelta(days=1):
                    logger.info(f"Markov chain analysis for {symbol} is already up to date")
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
                    'close': float(row.close),
                    'volume': int(row.volume)
                })
            
            df = pd.DataFrame(data)
            df = df.sort_values('date').reset_index(drop=True)
            
            # Supprimer les anciennes analyses si force_update
            if force_update:
                self.db.query(MarkovChainAnalysis).filter(MarkovChainAnalysis.symbol == symbol).delete()
            
            # Calculer les rendements et volumes
            df['returns'] = np.log(df['close'] / df['close'].shift(1))
            df['volume_change'] = df['volume'].pct_change()
            df = df.dropna()
            
            if len(df) < 50:
                logger.warning(f"Insufficient data for Markov chain analysis for {symbol}")
                return {"status": "error", "symbol": symbol, "error": "Insufficient data"}
            
            # Effectuer l'analyse des chaînes de Markov
            analysis_results = self._perform_markov_analysis(df, symbol)
            
            # Créer l'enregistrement
            analysis = MarkovChainAnalysis(
                symbol=symbol,
                analysis_date=datetime.now(),
                n_states=3,  # BULL, BEAR, SIDEWAYS
                current_state=0 if analysis_results['current_state'] == 'BULL' else 1 if analysis_results['current_state'] == 'BEAR' else 2,
                state_probabilities=analysis_results['state_probabilities'],
                transition_matrix=analysis_results['transition_matrix'],
                stationary_probabilities=analysis_results['steady_state_probabilities'],
                regime_changes=analysis_results['state_history'],
                future_state_predictions=analysis_results['expected_duration'],
                state_analysis=analysis_results['regime_characteristics'],
                model_parameters=analysis_results['model_metrics']
            )
            
            self.db.add(analysis)
            self.db.commit()
            
            logger.info(f"Markov chain analysis calculated for {symbol}")
            return {
                "status": "success", 
                "symbol": symbol, 
                "analyses_created": 1
            }
            
        except Exception as e:
            logger.error(f"Error calculating Markov chain analysis for {symbol}: {e}")
            self.db.rollback()
            return {"status": "error", "symbol": symbol, "error": str(e)}
    
    def _perform_markov_analysis(self, df: pd.DataFrame, symbol: str) -> dict:
        """Effectuer l'analyse des chaînes de Markov"""
        
        # Définir les états basés sur les rendements
        returns = df['returns'].values
        volatility = np.std(returns) * np.sqrt(252)
        
        # Définir les seuils pour les états
        high_threshold = 0.02  # 2% de rendement
        low_threshold = -0.02  # -2% de rendement
        
        # Classifier les états
        states = []
        for ret in returns:
            if ret > high_threshold:
                states.append('BULL')
            elif ret < low_threshold:
                states.append('BEAR')
            else:
                states.append('SIDEWAYS')
        
        # Calculer la matrice de transition
        transition_matrix = self._calculate_transition_matrix(states)
        
        # Calculer les probabilités d'état actuelles
        current_state = states[-1]
        state_probabilities = self._calculate_state_probabilities(states)
        
        # Calculer les probabilités d'état stationnaire
        steady_state_probabilities = self._calculate_steady_state(transition_matrix)
        
        # Calculer la durée attendue dans chaque état
        expected_duration = self._calculate_expected_duration(transition_matrix)
        
        # Analyser les caractéristiques des régimes
        regime_characteristics = self._analyze_regime_characteristics(df, states)
        
        # Analyser les régimes de volatilité
        volatility_regimes = self._analyze_volatility_regimes(df, states)
        
        # Analyser les régimes de tendance
        trend_regimes = self._analyze_trend_regimes(df, states)
        
        # Analyser les régimes de volume
        volume_regimes = self._analyze_volume_regimes(df, states)
        
        # Historique des états
        state_history = states[-20:]  # 20 derniers états
        
        # Métriques du modèle
        model_metrics = self._calculate_model_metrics(states, transition_matrix)
        
        return {
            'current_state': current_state,
            'state_probabilities': state_probabilities,
            'transition_matrix': transition_matrix,
            'steady_state_probabilities': steady_state_probabilities,
            'expected_duration': expected_duration,
            'regime_characteristics': regime_characteristics,
            'volatility_regimes': volatility_regimes,
            'trend_regimes': trend_regimes,
            'volume_regimes': volume_regimes,
            'state_history': state_history,
            'model_metrics': model_metrics
        }
    
    def _calculate_transition_matrix(self, states: list) -> dict:
        """Calculer la matrice de transition"""
        states_unique = ['BULL', 'BEAR', 'SIDEWAYS']
        n_states = len(states_unique)
        
        # Initialiser la matrice de comptage
        count_matrix = np.zeros((n_states, n_states))
        
        # Compter les transitions
        for i in range(len(states) - 1):
            current_state_idx = states_unique.index(states[i])
            next_state_idx = states_unique.index(states[i + 1])
            count_matrix[current_state_idx][next_state_idx] += 1
        
        # Normaliser pour obtenir les probabilités
        transition_matrix = {}
        for i, from_state in enumerate(states_unique):
            row_sum = np.sum(count_matrix[i])
            if row_sum > 0:
                transition_matrix[from_state] = {
                    'BULL': float(count_matrix[i][0] / row_sum),
                    'BEAR': float(count_matrix[i][1] / row_sum),
                    'SIDEWAYS': float(count_matrix[i][2] / row_sum)
                }
            else:
                transition_matrix[from_state] = {
                    'BULL': 1/3,
                    'BEAR': 1/3,
                    'SIDEWAYS': 1/3
                }
        
        return transition_matrix
    
    def _calculate_state_probabilities(self, states: list) -> dict:
        """Calculer les probabilités d'état actuelles"""
        total_states = len(states)
        state_counts = {'BULL': 0, 'BEAR': 0, 'SIDEWAYS': 0}
        
        for state in states:
            state_counts[state] += 1
        
        return {
            'BULL': state_counts['BULL'] / total_states,
            'BEAR': state_counts['BEAR'] / total_states,
            'SIDEWAYS': state_counts['SIDEWAYS'] / total_states
        }
    
    def _calculate_steady_state(self, transition_matrix: dict) -> dict:
        """Calculer les probabilités d'état stationnaire"""
        # Méthode simplifiée : utiliser les probabilités moyennes
        bull_prob = np.mean([transition_matrix[state]['BULL'] for state in transition_matrix])
        bear_prob = np.mean([transition_matrix[state]['BEAR'] for state in transition_matrix])
        sideways_prob = np.mean([transition_matrix[state]['SIDEWAYS'] for state in transition_matrix])
        
        # Normaliser
        total = bull_prob + bear_prob + sideways_prob
        
        return {
            'BULL': bull_prob / total,
            'BEAR': bear_prob / total,
            'SIDEWAYS': sideways_prob / total
        }
    
    def _calculate_expected_duration(self, transition_matrix: dict) -> dict:
        """Calculer la durée attendue dans chaque état"""
        expected_duration = {}
        
        for state in transition_matrix:
            # Probabilité de rester dans le même état
            stay_prob = transition_matrix[state][state]
            if stay_prob < 1:
                expected_duration[state] = 1 / (1 - stay_prob)
            else:
                expected_duration[state] = float('inf')
        
        return expected_duration
    
    def _analyze_regime_characteristics(self, df: pd.DataFrame, states: list) -> dict:
        """Analyser les caractéristiques des régimes"""
        characteristics = {}
        
        for state in ['BULL', 'BEAR', 'SIDEWAYS']:
            state_indices = [i for i, s in enumerate(states) if s == state]
            if state_indices:
                state_returns = df['returns'].iloc[state_indices]
                characteristics[state] = {
                    'mean_return': float(np.mean(state_returns)),
                    'volatility': float(np.std(state_returns)),
                    'frequency': len(state_indices),
                    'avg_duration': len(state_indices) / len(states)
                }
            else:
                characteristics[state] = {
                    'mean_return': 0.0,
                    'volatility': 0.0,
                    'frequency': 0,
                    'avg_duration': 0.0
                }
        
        return characteristics
    
    def _analyze_volatility_regimes(self, df: pd.DataFrame, states: list) -> dict:
        """Analyser les régimes de volatilité"""
        volatility_regimes = {}
        
        for state in ['BULL', 'BEAR', 'SIDEWAYS']:
            state_indices = [i for i, s in enumerate(states) if s == state]
            if state_indices:
                state_volatility = df['returns'].iloc[state_indices].rolling(window=5).std().mean()
                volatility_regimes[state] = {
                    'avg_volatility': float(state_volatility),
                    'volatility_trend': 'increasing' if len(state_indices) > 1 else 'stable'
                }
            else:
                volatility_regimes[state] = {
                    'avg_volatility': 0.0,
                    'volatility_trend': 'stable'
                }
        
        return volatility_regimes
    
    def _analyze_trend_regimes(self, df: pd.DataFrame, states: list) -> dict:
        """Analyser les régimes de tendance"""
        trend_regimes = {}
        
        for state in ['BULL', 'BEAR', 'SIDEWAYS']:
            state_indices = [i for i, s in enumerate(states) if s == state]
            if state_indices:
                state_prices = df['close'].iloc[state_indices]
                if len(state_prices) > 1:
                    trend_slope = np.polyfit(range(len(state_prices)), state_prices, 1)[0]
                    trend_regimes[state] = {
                        'trend_slope': float(trend_slope),
                        'trend_strength': abs(float(trend_slope))
                    }
                else:
                    trend_regimes[state] = {
                        'trend_slope': 0.0,
                        'trend_strength': 0.0
                    }
            else:
                trend_regimes[state] = {
                    'trend_slope': 0.0,
                    'trend_strength': 0.0
                }
        
        return trend_regimes
    
    def _analyze_volume_regimes(self, df: pd.DataFrame, states: list) -> dict:
        """Analyser les régimes de volume"""
        volume_regimes = {}
        
        for state in ['BULL', 'BEAR', 'SIDEWAYS']:
            state_indices = [i for i, s in enumerate(states) if s == state]
            if state_indices:
                state_volumes = df['volume'].iloc[state_indices]
                volume_regimes[state] = {
                    'avg_volume': float(np.mean(state_volumes)),
                    'volume_volatility': float(np.std(state_volumes))
                }
            else:
                volume_regimes[state] = {
                    'avg_volume': 0.0,
                    'volume_volatility': 0.0
                }
        
        return volume_regimes
    
    def _calculate_model_metrics(self, states: list, transition_matrix: dict) -> dict:
        """Calculer les métriques du modèle"""
        # Calculer l'entropie de la chaîne
        entropy = 0
        for state in transition_matrix:
            state_probs = transition_matrix[state]
            for next_state in state_probs:
                prob = state_probs[next_state]
                if prob > 0:
                    entropy -= prob * np.log2(prob)
        
        # Calculer la persistance moyenne
        persistence = np.mean([transition_matrix[state][state] for state in transition_matrix])
        
        return {
            'entropy': float(entropy),
            'persistence': float(persistence),
            'states_count': len(set(states)),
            'transitions_count': len(states) - 1
        }

def recompute_markov_chain_analysis_for_symbol(symbol: str, force_update: bool = False) -> dict:
    """
    Recalculer l'analyse des chaînes de Markov pour un symbole
    
    Args:
        symbol: Symbole à traiter
        force_update: Forcer le recalcul
    
    Returns:
        Dict contenant le résultat
    """
    try:
        db = next(get_db())
        calculator = MarkovChainCalculator(db)
        result = calculator.calculate_markov_chain_analysis(symbol, force_update)
        return result
    except Exception as e:
        logger.error(f"Error in recompute_markov_chain_analysis_for_symbol: {e}")
        return {"status": "error", "symbol": symbol, "error": str(e)}
    finally:
        db.close()

def recompute_markov_chain_analysis_for_symbols(symbols: list, force_update: bool = False) -> dict:
    """
    Recalculer l'analyse des chaînes de Markov pour plusieurs symboles
    
    Args:
        symbols: Liste des symboles à traiter
        force_update: Forcer le recalcul
    
    Returns:
        Dict contenant les résultats
    """
    results = {
        "total_symbols": len(symbols),
        "processed_symbols": 0,
        "successful_symbols": 0,
        "failed_symbols": 0,
        "total_analyses_created": 0,
        "errors": [],
        "start_time": datetime.now().isoformat()
    }
    
    logger.info(f"Starting Markov chain analysis recompute for {len(symbols)} symbols")
    
    for symbol in symbols:
        try:
            logger.info(f"Processing Markov chain analysis for {symbol}")
            result = recompute_markov_chain_analysis_for_symbol(symbol, force_update)
            
            results["processed_symbols"] += 1
            
            if result["status"] == "success":
                results["successful_symbols"] += 1
                results["total_analyses_created"] += result.get("analyses_created", 0)
                logger.info(f"Markov chain analysis calculated successfully for {symbol}: {result.get('analyses_created', 0)} analyses")
            elif result["status"] == "skipped":
                results["successful_symbols"] += 1
                logger.info(f"Markov chain analysis skipped for {symbol}: {result.get('reason', 'Unknown')}")
            else:
                results["failed_symbols"] += 1
                results["errors"].append({
                    "symbol": symbol,
                    "error": result.get("error", "Unknown error")
                })
                logger.error(f"Failed to calculate Markov chain analysis for {symbol}: {result.get('error', 'Unknown error')}")
                
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
    
    logger.info(f"Markov chain analysis recompute completed: {results}")
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Recompute Markov chain analysis")
    parser.add_argument("--symbols", nargs="+", help="Symbols to recompute", default=["PLTR"])
    parser.add_argument("--force", action="store_true", help="Force recalculate")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Exécuter le recalcul
    results = recompute_markov_chain_analysis_for_symbols(args.symbols, args.force)
    
    # Afficher les résultats
    print("\n" + "="*80)
    print("MARKOV CHAIN ANALYSIS RECOMPUTE RESULTS")
    print("="*80)
    print(f"Total symbols: {results['total_symbols']}")
    print(f"Processed: {results['processed_symbols']}")
    print(f"Successful: {results['successful_symbols']}")
    print(f"Failed: {results['failed_symbols']}")
    print(f"Total analyses created: {results['total_analyses_created']}")
    print(f"Duration: {results['duration']:.2f} seconds")
    print(f"Success rate: {(results['successful_symbols']/results['processed_symbols']*100):.1f}%")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  {error['symbol']}: {error['error']}")
    
    print("="*80)
