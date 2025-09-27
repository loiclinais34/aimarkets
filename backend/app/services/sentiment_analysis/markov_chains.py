"""
Chaînes de Markov pour l'analyse des états de marché.

Ce module implémente des chaînes de Markov pour analyser
les transitions entre différents états de marché.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
import warnings

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class MarkovChainAnalysis:
    """
    Classe pour analyser les états de marché en utilisant les chaînes de Markov.
    
    Cette classe fournit des méthodes pour identifier les états de marché,
    calculer les matrices de transition et prédire les états futurs.
    """
    
    @staticmethod
    def identify_market_states(returns: pd.Series, n_states: int = 3, 
                             method: str = "gmm") -> Dict[str, Any]:
        """
        Identifie les états de marché à partir des rendements.
        
        Args:
            returns: Série des rendements
            n_states: Nombre d'états à identifier
            method: Méthode d'identification ("gmm" ou "kmeans")
            
        Returns:
            Dictionnaire contenant les états identifiés
        """
        try:
            # Préparer les données
            returns_clean = returns.dropna()
            
            if len(returns_clean) < 50:
                raise ValueError("Pas assez de données pour identifier les états de marché")
            
            # Reshape pour sklearn
            X = returns_clean.values.reshape(-1, 1)
            
            if method == "gmm":
                # Utiliser un modèle de mélange gaussien
                model = GaussianMixture(n_components=n_states, random_state=42)
                states = model.fit_predict(X)
                
                # Extraire les paramètres des composantes
                means = model.means_.flatten()
                covariances = model.covariances_.flatten()
                weights = model.weights_
                
                state_info = {
                    "means": means,
                    "covariances": covariances,
                    "weights": weights
                }
                
            else:  # kmeans
                # Utiliser K-means
                model = KMeans(n_clusters=n_states, random_state=42)
                states = model.fit_predict(X)
                
                # Extraire les centres des clusters
                means = model.cluster_centers_.flatten()
                state_info = {
                    "means": means,
                    "centers": means
                }
            
            # Créer une série des états
            states_series = pd.Series(states, index=returns_clean.index)
            
            # Analyser les états
            state_analysis = MarkovChainAnalysis._analyze_states(states_series, returns_clean)
            
            return {
                "states": states_series,
                "model": model,
                "state_info": state_info,
                "state_analysis": state_analysis,
                "method": method,
                "n_states": n_states,
                "state_labels": list(range(n_states))
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'identification des états de marché: {e}")
            return {
                "states": pd.Series(dtype=int),
                "model": None,
                "state_info": {},
                "state_analysis": {},
                "method": method,
                "n_states": n_states,
                "error": str(e)
            }
    
    @staticmethod
    def _analyze_states(states: pd.Series, returns: pd.Series) -> Dict[str, Any]:
        """
        Analyse les caractéristiques de chaque état.
        
        Args:
            states: Série des états
            returns: Série des rendements
            
        Returns:
            Dictionnaire contenant l'analyse des états
        """
        try:
            analysis = {}
            
            for state in states.unique():
                state_returns = returns[states == state]
                
                analysis[f"state_{state}"] = {
                    "count": len(state_returns),
                    "percentage": len(state_returns) / len(returns) * 100,
                    "mean_return": state_returns.mean(),
                    "std_return": state_returns.std(),
                    "min_return": state_returns.min(),
                    "max_return": state_returns.max(),
                    "skewness": state_returns.skew(),
                    "kurtosis": state_returns.kurtosis()
                }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des états: {e}")
            return {}
    
    @staticmethod
    def calculate_transition_matrix(states: pd.Series) -> Dict[str, Any]:
        """
        Calcule la matrice de transition entre les états.
        
        Args:
            states: Série des états
            
        Returns:
            Dictionnaire contenant la matrice de transition
        """
        try:
            # Créer la matrice de transition
            n_states = len(states.unique())
            transition_matrix = np.zeros((n_states, n_states))
            
            # Compter les transitions
            for i in range(len(states) - 1):
                current_state = states.iloc[i]
                next_state = states.iloc[i + 1]
                transition_matrix[current_state, next_state] += 1
            
            # Normaliser les lignes pour obtenir les probabilités
            row_sums = transition_matrix.sum(axis=1)
            transition_matrix = transition_matrix / row_sums[:, np.newaxis]
            
            # Remplacer les NaN par 0
            transition_matrix = np.nan_to_num(transition_matrix)
            
            # Calculer les probabilités stationnaires
            stationary_probs = MarkovChainAnalysis._calculate_stationary_probabilities(transition_matrix)
            
            return {
                "transition_matrix": transition_matrix,
                "stationary_probabilities": stationary_probs,
                "n_states": n_states,
                "state_labels": list(range(n_states))
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la matrice de transition: {e}")
            return {
                "transition_matrix": np.array([]),
                "stationary_probabilities": np.array([]),
                "n_states": 0,
                "state_labels": [],
                "error": str(e)
            }
    
    @staticmethod
    def _calculate_stationary_probabilities(transition_matrix: np.ndarray) -> np.ndarray:
        """
        Calcule les probabilités stationnaires de la chaîne de Markov.
        
        Args:
            transition_matrix: Matrice de transition
            
        Returns:
            Array des probabilités stationnaires
        """
        try:
            # Résoudre le système d'équations: π = πP
            # Où π est le vecteur des probabilités stationnaires
            # et P est la matrice de transition
            
            n = transition_matrix.shape[0]
            
            # Créer le système d'équations
            # π(I - P) = 0, avec Σπ = 1
            A = np.eye(n) - transition_matrix.T
            A[-1] = np.ones(n)  # Contrainte de normalisation
            
            # Vecteur de droite
            b = np.zeros(n)
            b[-1] = 1
            
            # Résoudre le système
            stationary_probs = np.linalg.solve(A, b)
            
            # S'assurer que les probabilités sont positives
            stationary_probs = np.maximum(stationary_probs, 0)
            stationary_probs = stationary_probs / stationary_probs.sum()
            
            return stationary_probs
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des probabilités stationnaires: {e}")
            return np.ones(transition_matrix.shape[0]) / transition_matrix.shape[0]
    
    @staticmethod
    def predict_future_states(transition_matrix: np.ndarray, current_state: int,
                            horizon: int = 5) -> Dict[str, Any]:
        """
        Prédit les états futurs basés sur la matrice de transition.
        
        Args:
            transition_matrix: Matrice de transition
            current_state: État actuel
            horizon: Horizon de prédiction
            
        Returns:
            Dictionnaire contenant les prédictions
        """
        try:
            n_states = transition_matrix.shape[0]
            
            # Vecteur d'état initial
            state_vector = np.zeros(n_states)
            state_vector[current_state] = 1
            
            # Prédictions pour chaque horizon
            predictions = []
            current_vector = state_vector.copy()
            
            for h in range(horizon):
                # Calculer la probabilité de chaque état
                state_probs = current_vector @ transition_matrix
                predictions.append(state_probs.copy())
                current_vector = state_probs
            
            # Convertir en DataFrame pour faciliter l'analyse
            predictions_df = pd.DataFrame(
                predictions,
                columns=[f"state_{i}" for i in range(n_states)],
                index=range(1, horizon + 1)
            )
            
            # Identifier l'état le plus probable à chaque horizon
            most_likely_states = predictions_df.idxmax(axis=1)
            max_probabilities = predictions_df.max(axis=1)
            
            return {
                "predictions": predictions_df,
                "most_likely_states": most_likely_states,
                "max_probabilities": max_probabilities,
                "horizon": horizon,
                "current_state": current_state
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la prédiction des états futurs: {e}")
            return {
                "predictions": pd.DataFrame(),
                "most_likely_states": pd.Series(),
                "max_probabilities": pd.Series(),
                "horizon": horizon,
                "current_state": current_state,
                "error": str(e)
            }
    
    @staticmethod
    def detect_regime_changes(states: pd.Series, min_duration: int = 5) -> Dict[str, Any]:
        """
        Détecte les changements de régime dans les états de marché.
        
        Args:
            states: Série des états
            min_duration: Durée minimale d'un régime
            
        Returns:
            Dictionnaire contenant les changements de régime détectés
        """
        try:
            # Identifier les changements d'état
            state_changes = states.diff().fillna(0) != 0
            change_indices = state_changes[state_changes].index.tolist()
            
            # Analyser les régimes
            regimes = []
            current_regime = states.iloc[0]
            start_index = states.index[0]
            
            for i, (idx, state) in enumerate(states.items()):
                if state != current_regime:
                    # Fin du régime précédent
                    end_index = states.index[i-1] if i > 0 else start_index
                    duration = (end_index - start_index).days if hasattr(end_index, 'days') else i
                    
                    if duration >= min_duration:
                        regimes.append({
                            "state": current_regime,
                            "start": start_index,
                            "end": end_index,
                            "duration": duration,
                            "start_index": i - duration if i > 0 else 0,
                            "end_index": i - 1 if i > 0 else 0
                        })
                    
                    # Nouveau régime
                    current_regime = state
                    start_index = idx
            
            # Ajouter le dernier régime
            if len(regimes) == 0 or regimes[-1]["end"] != states.index[-1]:
                end_index = states.index[-1]
                duration = (end_index - start_index).days if hasattr(end_index, 'days') else len(states) - regimes[-1]["end_index"] if regimes else len(states)
                
                if duration >= min_duration:
                    regimes.append({
                        "state": current_regime,
                        "start": start_index,
                        "end": end_index,
                        "duration": duration,
                        "start_index": regimes[-1]["end_index"] + 1 if regimes else 0,
                        "end_index": len(states) - 1
                    })
            
            # Analyser les caractéristiques des régimes
            regime_analysis = MarkovChainAnalysis._analyze_regimes(regimes, states)
            
            return {
                "regimes": regimes,
                "regime_analysis": regime_analysis,
                "total_regimes": len(regimes),
                "min_duration": min_duration
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la détection des changements de régime: {e}")
            return {
                "regimes": [],
                "regime_analysis": {},
                "total_regimes": 0,
                "min_duration": min_duration,
                "error": str(e)
            }
    
    @staticmethod
    def _analyze_regimes(regimes: List[Dict], states: pd.Series) -> Dict[str, Any]:
        """
        Analyse les caractéristiques des régimes détectés.
        
        Args:
            regimes: Liste des régimes
            states: Série des états
            
        Returns:
            Dictionnaire contenant l'analyse des régimes
        """
        try:
            analysis = {
                "regime_durations": [regime["duration"] for regime in regimes],
                "regime_states": [regime["state"] for regime in regimes],
                "average_duration": np.mean([regime["duration"] for regime in regimes]) if regimes else 0,
                "max_duration": max([regime["duration"] for regime in regimes]) if regimes else 0,
                "min_duration": min([regime["duration"] for regime in regimes]) if regimes else 0
            }
            
            # Analyser les transitions entre régimes
            if len(regimes) > 1:
                transitions = []
                for i in range(len(regimes) - 1):
                    transition = {
                        "from_state": regimes[i]["state"],
                        "to_state": regimes[i + 1]["state"],
                        "transition_time": regimes[i + 1]["start"]
                    }
                    transitions.append(transition)
                
                analysis["transitions"] = transitions
                analysis["unique_transitions"] = len(set((t["from_state"], t["to_state"]) for t in transitions))
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des régimes: {e}")
            return {}
    
    @staticmethod
    def calculate_state_probabilities(transition_matrix: np.ndarray, 
                                    initial_state: int, steps: int = 10) -> pd.DataFrame:
        """
        Calcule les probabilités d'être dans chaque état après un nombre de pas.
        
        Args:
            transition_matrix: Matrice de transition
            initial_state: État initial
            steps: Nombre de pas
            
        Returns:
            DataFrame contenant les probabilités
        """
        try:
            n_states = transition_matrix.shape[0]
            
            # Vecteur d'état initial
            state_vector = np.zeros(n_states)
            state_vector[initial_state] = 1
            
            # Calculer les probabilités pour chaque pas
            probabilities = []
            current_vector = state_vector.copy()
            
            for step in range(steps + 1):
                probabilities.append(current_vector.copy())
                current_vector = current_vector @ transition_matrix
            
            # Créer le DataFrame
            prob_df = pd.DataFrame(
                probabilities,
                columns=[f"state_{i}" for i in range(n_states)],
                index=range(steps + 1)
            )
            
            return prob_df
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des probabilités d'état: {e}")
            return pd.DataFrame()
    
    @staticmethod
    def comprehensive_markov_analysis(returns: pd.Series, n_states: int = 3) -> Dict[str, Any]:
        """
        Effectue une analyse complète des chaînes de Markov.
        
        Args:
            returns: Série des rendements
            n_states: Nombre d'états à identifier
            
        Returns:
            Dictionnaire contenant l'analyse complète
        """
        try:
            # Identifier les états
            state_identification = MarkovChainAnalysis.identify_market_states(returns, n_states)
            
            if state_identification["states"].empty:
                raise ValueError("Impossible d'identifier les états de marché")
            
            states = state_identification["states"]
            
            # Calculer la matrice de transition
            transition_analysis = MarkovChainAnalysis.calculate_transition_matrix(states)
            
            # Détecter les changements de régime
            regime_analysis = MarkovChainAnalysis.detect_regime_changes(states)
            
            # Prédire les états futurs
            current_state = states.iloc[-1]
            future_predictions = MarkovChainAnalysis.predict_future_states(
                transition_analysis["transition_matrix"], current_state
            )
            
            # Calculer les probabilités d'état
            state_probabilities = MarkovChainAnalysis.calculate_state_probabilities(
                transition_analysis["transition_matrix"], current_state
            )
            
            return {
                "state_identification": state_identification,
                "transition_analysis": transition_analysis,
                "regime_analysis": regime_analysis,
                "future_predictions": future_predictions,
                "state_probabilities": state_probabilities,
                "current_state": current_state,
                "analysis_timestamp": pd.Timestamp.now(),
                "data_period": {
                    "start": returns.index[0],
                    "end": returns.index[-1],
                    "duration_days": (returns.index[-1] - returns.index[0]).days
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse complète des chaînes de Markov: {e}")
            return {
                "state_identification": {},
                "transition_analysis": {},
                "regime_analysis": {},
                "future_predictions": {},
                "state_probabilities": pd.DataFrame(),
                "current_state": None,
                "analysis_timestamp": pd.Timestamp.now(),
                "data_period": {},
                "error": str(e)
            }
