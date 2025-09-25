"""
Framework de Comparaison de Modèles ML pour le Trading
=====================================================

Ce module fournit un framework complet pour comparer différents modèles
d'apprentissage automatique dans le contexte du trading financier.

Fonctionnalités :
- Comparaison de multiples modèles ML
- Métriques de trading spécialisées
- Validation croisée temporelle
- Visualisation des performances
- Sélection automatique du meilleur modèle
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, date
from dataclasses import dataclass
from abc import ABC, abstractmethod
import joblib
import json
from pathlib import Path

# Imports pour les modèles ML
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_auc_score
)
from sklearn.preprocessing import StandardScaler, LabelEncoder

# Imports pour les modèles avancés (optionnels)
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("XGBoost non disponible. Installez avec: pip install xgboost")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("LightGBM non disponible. Installez avec: pip install lightgbm")

try:
    from sklearn.neural_network import MLPClassifier, MLPRegressor
    NEURAL_NETWORKS_AVAILABLE = True
except ImportError:
    NEURAL_NETWORKS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ModelMetrics:
    """Métriques de performance d'un modèle"""
    # Métriques ML classiques
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float
    
    # Métriques de trading
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    win_rate: float
    profit_factor: float
    
    # Métriques temporelles
    training_time: float
    prediction_time: float
    
    # Métadonnées
    model_name: str
    timestamp: datetime
    parameters: Dict[str, Any]

@dataclass
class TradingResults:
    """Résultats de backtesting pour un modèle"""
    trades: List[Dict[str, Any]]
    equity_curve: List[float]
    daily_returns: List[float]
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    win_rate: float
    profit_factor: float
    total_trades: int
    winning_trades: int
    losing_trades: int

class BaseModel(ABC):
    """Classe de base pour tous les modèles ML"""
    
    def __init__(self, name: str, **kwargs):
        self.name = name
        self.parameters = kwargs
        self.model = None
        self.is_trained = False
        self.scaler = StandardScaler()
        
    @abstractmethod
    def _create_model(self) -> Any:
        """Créer l'instance du modèle"""
        pass
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'BaseModel':
        """Entraîner le modèle"""
        start_time = datetime.now()
        
        # Normaliser les features
        X_scaled = self.scaler.fit_transform(X)
        
        # Créer et entraîner le modèle
        self.model = self._create_model()
        self.model.fit(X_scaled, y)
        
        self.is_trained = True
        self.training_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"Modèle {self.name} entraîné en {self.training_time:.2f}s")
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Faire des prédictions"""
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant de faire des prédictions")
        
        start_time = datetime.now()
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        self.prediction_time = (datetime.now() - start_time).total_seconds()
        
        return predictions
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Faire des prédictions probabilistes"""
        if not self.is_trained:
            raise ValueError("Le modèle doit être entraîné avant de faire des prédictions")
        
        X_scaled = self.scaler.transform(X)
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X_scaled)
        else:
            # Pour les modèles sans predict_proba, utiliser decision_function
            if hasattr(self.model, 'decision_function'):
                scores = self.model.decision_function(X_scaled)
                # Convertir en probabilités avec sigmoid
                probabilities = 1 / (1 + np.exp(-scores))
                return np.column_stack([1 - probabilities, probabilities])
            else:
                raise ValueError(f"Le modèle {self.name} ne supporte pas les prédictions probabilistes")

class RandomForestModel(BaseModel):
    """Modèle Random Forest"""
    
    def _create_model(self):
        return RandomForestClassifier(
            n_estimators=self.parameters.get('n_estimators', 100),
            max_depth=self.parameters.get('max_depth', None),
            min_samples_split=self.parameters.get('min_samples_split', 2),
            min_samples_leaf=self.parameters.get('min_samples_leaf', 1),
            random_state=self.parameters.get('random_state', 42),
            n_jobs=self.parameters.get('n_jobs', -1)
        )

class XGBoostModel(BaseModel):
    """Modèle XGBoost"""
    
    def _create_model(self):
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost n'est pas installé")
        
        return xgb.XGBClassifier(
            n_estimators=self.parameters.get('n_estimators', 100),
            max_depth=self.parameters.get('max_depth', 6),
            learning_rate=self.parameters.get('learning_rate', 0.1),
            subsample=self.parameters.get('subsample', 1.0),
            colsample_bytree=self.parameters.get('colsample_bytree', 1.0),
            random_state=self.parameters.get('random_state', 42),
            n_jobs=self.parameters.get('n_jobs', -1)
        )

class LightGBMModel(BaseModel):
    """Modèle LightGBM"""
    
    def _create_model(self):
        if not LIGHTGBM_AVAILABLE:
            raise ImportError("LightGBM n'est pas installé")
        
        return lgb.LGBMClassifier(
            n_estimators=self.parameters.get('n_estimators', 100),
            max_depth=self.parameters.get('max_depth', -1),
            learning_rate=self.parameters.get('learning_rate', 0.1),
            subsample=self.parameters.get('subsample', 1.0),
            colsample_bytree=self.parameters.get('colsample_bytree', 1.0),
            random_state=self.parameters.get('random_state', 42),
            n_jobs=self.parameters.get('n_jobs', -1),
            verbose=-1
        )

class NeuralNetworkModel(BaseModel):
    """Modèle Neural Network"""
    
    def _create_model(self):
        if not NEURAL_NETWORKS_AVAILABLE:
            raise ImportError("Neural Networks ne sont pas disponibles")
        
        return MLPClassifier(
            hidden_layer_sizes=self.parameters.get('hidden_layer_sizes', (100, 50)),
            activation=self.parameters.get('activation', 'relu'),
            solver=self.parameters.get('solver', 'adam'),
            alpha=self.parameters.get('alpha', 0.0001),
            learning_rate=self.parameters.get('learning_rate', 'constant'),
            max_iter=self.parameters.get('max_iter', 1000),
            random_state=self.parameters.get('random_state', 42)
        )

class ModelComparisonFramework:
    """Framework principal pour la comparaison de modèles"""
    
    def __init__(self, results_dir: str = "model_comparison_results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        self.models: Dict[str, BaseModel] = {}
        self.results: Dict[str, ModelMetrics] = {}
        self.trading_results: Dict[str, TradingResults] = {}
        
        # Configuration par défaut
        self.default_models = self._get_default_models()
        
    def _get_default_models(self) -> Dict[str, BaseModel]:
        """Obtenir les modèles par défaut"""
        models = {
            'RandomForest': RandomForestModel('RandomForest'),
            'RandomForest_Tuned': RandomForestModel(
                'RandomForest_Tuned',
                n_estimators=200,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2
            )
        }
        
        # Ajouter XGBoost si disponible
        if XGBOOST_AVAILABLE:
            models['XGBoost'] = XGBoostModel('XGBoost')
            models['XGBoost_Tuned'] = XGBoostModel(
                'XGBoost_Tuned',
                n_estimators=200,
                max_depth=8,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8
            )
        
        # Ajouter LightGBM si disponible
        if LIGHTGBM_AVAILABLE:
            models['LightGBM'] = LightGBMModel('LightGBM')
            models['LightGBM_Tuned'] = LightGBMModel(
                'LightGBM_Tuned',
                n_estimators=200,
                max_depth=8,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8
            )
        
        # Ajouter Neural Network si disponible
        if NEURAL_NETWORKS_AVAILABLE:
            models['NeuralNetwork'] = NeuralNetworkModel('NeuralNetwork')
            models['NeuralNetwork_Tuned'] = NeuralNetworkModel(
                'NeuralNetwork_Tuned',
                hidden_layer_sizes=(200, 100, 50),
                activation='relu',
                solver='adam',
                alpha=0.001,
                learning_rate='adaptive',
                max_iter=2000
            )
        
        return models
    
    def add_model(self, name: str, model: BaseModel):
        """Ajouter un modèle personnalisé"""
        self.models[name] = model
        logger.info(f"Modèle {name} ajouté au framework")
    
    def compare_models(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        prices: Optional[np.ndarray] = None,
        models_to_test: Optional[List[str]] = None
    ) -> Dict[str, ModelMetrics]:
        """
        Comparer les performances de plusieurs modèles
        
        Args:
            X_train: Features d'entraînement
            y_train: Labels d'entraînement
            X_test: Features de test
            y_test: Labels de test
            prices: Prix historiques pour le backtesting (optionnel)
            models_to_test: Liste des modèles à tester (optionnel)
        
        Returns:
            Dictionnaire des métriques pour chaque modèle
        """
        if models_to_test is None:
            models_to_test = list(self.default_models.keys())
        
        logger.info(f"Début de la comparaison de {len(models_to_test)} modèles")
        
        for model_name in models_to_test:
            try:
                logger.info(f"Entraînement du modèle: {model_name}")
                
                # Obtenir le modèle
                if model_name in self.models:
                    model = self.models[model_name]
                elif model_name in self.default_models:
                    model = self.default_models[model_name]
                else:
                    logger.warning(f"Modèle {model_name} non trouvé, ignoré")
                    continue
                
                # Entraîner le modèle
                model.fit(X_train, y_train)
                
                # Faire des prédictions
                y_pred = model.predict(X_test)
                y_pred_proba = model.predict_proba(X_test)
                
                # Calculer les métriques ML
                ml_metrics = self._calculate_ml_metrics(y_test, y_pred, y_pred_proba)
                
                # Calculer les métriques de trading si les prix sont fournis
                trading_metrics = None
                if prices is not None:
                    trading_metrics = self._calculate_trading_metrics(
                        y_pred, y_pred_proba, prices
                    )
                
                # Créer les métriques complètes
                metrics = ModelMetrics(
                    accuracy=ml_metrics['accuracy'],
                    precision=ml_metrics['precision'],
                    recall=ml_metrics['recall'],
                    f1_score=ml_metrics['f1_score'],
                    roc_auc=ml_metrics['roc_auc'],
                    sharpe_ratio=trading_metrics['sharpe_ratio'] if trading_metrics else 0.0,
                    max_drawdown=trading_metrics['max_drawdown'] if trading_metrics else 0.0,
                    total_return=trading_metrics['total_return'] if trading_metrics else 0.0,
                    win_rate=trading_metrics['win_rate'] if trading_metrics else 0.0,
                    profit_factor=trading_metrics['profit_factor'] if trading_metrics else 0.0,
                    training_time=getattr(model, 'training_time', 0.0),
                    prediction_time=getattr(model, 'prediction_time', 0.0),
                    model_name=model_name,
                    timestamp=datetime.now(),
                    parameters=model.parameters
                )
                
                self.results[model_name] = metrics
                
                logger.info(f"Modèle {model_name} terminé - Accuracy: {metrics.accuracy:.3f}")
                
            except Exception as e:
                logger.error(f"Erreur lors de l'entraînement de {model_name}: {e}")
                continue
        
        # Sauvegarder les résultats
        self._save_results()
        
        logger.info(f"Comparaison terminée. {len(self.results)} modèles évalués")
        return self.results
    
    def _calculate_ml_metrics(
        self, 
        y_true: np.ndarray, 
        y_pred: np.ndarray, 
        y_pred_proba: np.ndarray
    ) -> Dict[str, float]:
        """Calculer les métriques ML classiques"""
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, average='weighted'),
            'recall': recall_score(y_true, y_pred, average='weighted'),
            'f1_score': f1_score(y_true, y_pred, average='weighted'),
            'roc_auc': roc_auc_score(y_true, y_pred_proba[:, 1]) if y_pred_proba.shape[1] > 1 else 0.0
        }
    
    def _calculate_trading_metrics(
        self, 
        y_pred: np.ndarray, 
        y_pred_proba: np.ndarray, 
        prices: np.ndarray
    ) -> Dict[str, float]:
        """Calculer les métriques de trading"""
        # Simulation de trading simple
        trades = []
        position = 0
        entry_price = 0
        equity = [10000]  # Capital initial
        
        for i in range(1, len(prices)):
            current_price = prices[i]
            previous_price = prices[i-1]
            
            # Signal d'achat (prediction = 1)
            if y_pred[i] == 1 and position == 0:
                position = 1
                entry_price = current_price
                trades.append({
                    'type': 'buy',
                    'price': current_price,
                    'date': i,
                    'confidence': y_pred_proba[i, 1] if y_pred_proba.shape[1] > 1 else 0.5
                })
            
            # Signal de vente (prediction = 0) ou stop loss
            elif position == 1 and (y_pred[i] == 0 or current_price <= entry_price * 0.95):
                position = 0
                pnl = (current_price - entry_price) / entry_price
                trades.append({
                    'type': 'sell',
                    'price': current_price,
                    'date': i,
                    'pnl': pnl,
                    'entry_price': entry_price
                })
            
            # Mettre à jour l'equity
            if position == 1:
                current_equity = equity[-1] * (current_price / entry_price)
            else:
                current_equity = equity[-1]
            
            equity.append(current_equity)
        
        # Calculer les métriques
        if len(trades) > 0:
            sell_trades = [t for t in trades if t['type'] == 'sell']
            if sell_trades:
                returns = [t['pnl'] for t in sell_trades]
                winning_trades = [r for r in returns if r > 0]
                losing_trades = [r for r in returns if r < 0]
                
                total_return = (equity[-1] - equity[0]) / equity[0]
                win_rate = len(winning_trades) / len(returns) if returns else 0
                
                # Sharpe ratio (simplifié)
                if len(returns) > 1:
                    sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
                else:
                    sharpe_ratio = 0
                
                # Max drawdown
                peak = equity[0]
                max_dd = 0
                for value in equity:
                    if value > peak:
                        peak = value
                    dd = (peak - value) / peak
                    if dd > max_dd:
                        max_dd = dd
                
                # Profit factor
                gross_profit = sum(winning_trades) if winning_trades else 0
                gross_loss = abs(sum(losing_trades)) if losing_trades else 0
                profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
                
                return {
                    'sharpe_ratio': sharpe_ratio,
                    'max_drawdown': max_dd,
                    'total_return': total_return,
                    'win_rate': win_rate,
                    'profit_factor': profit_factor
                }
        
        return {
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'total_return': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0
        }
    
    def get_best_model(self, metric: str = 'f1_score') -> Tuple[str, ModelMetrics]:
        """Obtenir le meilleur modèle selon une métrique"""
        if not self.results:
            raise ValueError("Aucun résultat disponible. Exécutez compare_models() d'abord.")
        
        best_model_name = max(
            self.results.keys(),
            key=lambda x: getattr(self.results[x], metric)
        )
        
        return best_model_name, self.results[best_model_name]
    
    def _save_results(self):
        """Sauvegarder les résultats"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sauvegarder les métriques
        results_data = {}
        for model_name, metrics in self.results.items():
            results_data[model_name] = {
                'accuracy': metrics.accuracy,
                'precision': metrics.precision,
                'recall': metrics.recall,
                'f1_score': metrics.f1_score,
                'roc_auc': metrics.roc_auc,
                'sharpe_ratio': metrics.sharpe_ratio,
                'max_drawdown': metrics.max_drawdown,
                'total_return': metrics.total_return,
                'win_rate': metrics.win_rate,
                'profit_factor': metrics.profit_factor,
                'training_time': metrics.training_time,
                'prediction_time': metrics.prediction_time,
                'timestamp': metrics.timestamp.isoformat(),
                'parameters': metrics.parameters
            }
        
        results_file = self.results_dir / f"model_comparison_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        logger.info(f"Résultats sauvegardés dans {results_file}")
    
    def generate_report(self) -> str:
        """Générer un rapport de comparaison"""
        if not self.results:
            return "Aucun résultat disponible."
        
        report = []
        report.append("=" * 80)
        report.append("RAPPORT DE COMPARAISON DE MODÈLES")
        report.append("=" * 80)
        report.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Nombre de modèles comparés: {len(self.results)}")
        report.append("")
        
        # Tableau des résultats
        report.append("RÉSULTATS DÉTAILLÉS:")
        report.append("-" * 80)
        report.append(f"{'Modèle':<20} {'Accuracy':<10} {'F1-Score':<10} {'Sharpe':<10} {'Return':<10}")
        report.append("-" * 80)
        
        for model_name, metrics in self.results.items():
            report.append(
                f"{model_name:<20} "
                f"{metrics.accuracy:<10.3f} "
                f"{metrics.f1_score:<10.3f} "
                f"{metrics.sharpe_ratio:<10.3f} "
                f"{metrics.total_return:<10.3f}"
            )
        
        report.append("-" * 80)
        
        # Meilleur modèle par métrique
        report.append("\nMEILLEURS MODÈLES PAR MÉTRIQUE:")
        report.append("-" * 40)
        
        metrics_to_check = ['accuracy', 'f1_score', 'sharpe_ratio', 'total_return']
        for metric in metrics_to_check:
            try:
                best_name, best_metrics = self.get_best_model(metric)
                report.append(f"{metric.capitalize()}: {best_name} ({getattr(best_metrics, metric):.3f})")
            except:
                continue
        
        return "\n".join(report)

# Fonction utilitaire pour créer le framework
def create_model_comparison_framework() -> ModelComparisonFramework:
    """Créer une instance du framework avec les modèles par défaut"""
    return ModelComparisonFramework()

if __name__ == "__main__":
    # Exemple d'utilisation
    print("Framework de Comparaison de Modèles ML pour le Trading")
    print("=" * 60)
    
    # Créer le framework
    framework = create_model_comparison_framework()
    
    # Afficher les modèles disponibles
    print(f"Modèles disponibles: {list(framework.default_models.keys())}")
    
    # Exemple de données factices pour test
    np.random.seed(42)
    X_train = np.random.randn(1000, 10)
    y_train = np.random.randint(0, 2, 1000)
    X_test = np.random.randn(200, 10)
    y_test = np.random.randint(0, 2, 200)
    prices = np.random.randn(200) * 100 + 100  # Prix simulés
    
    # Comparer les modèles
    print("\nDébut de la comparaison...")
    results = framework.compare_models(X_train, y_train, X_test, y_test, prices)
    
    # Générer le rapport
    report = framework.generate_report()
    print("\n" + report)
