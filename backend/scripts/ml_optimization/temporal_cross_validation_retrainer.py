#!/usr/bin/env python3
"""
Système de réentraînement avec validation croisée temporelle
Utilise des données récentes et une stratégie de k-fold temporel
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
from dataclasses import dataclass
import warnings
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error
import pickle
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
class TemporalFold:
    """Représente un fold temporel"""
    train_start: datetime
    train_end: datetime
    validation_start: datetime
    validation_end: datetime
    fold_number: int

class TemporalCrossValidator:
    """Validateur croisé temporel pour données financières"""
    
    def __init__(self, n_splits: int = 5, test_size_days: int = 30):
        self.n_splits = n_splits
        self.test_size_days = test_size_days
        self.folds = []
    
    def create_temporal_folds(self, start_date: datetime, end_date: datetime) -> List[TemporalFold]:
        """Crée des folds temporels"""
        logger.info(f"📅 Création de {self.n_splits} folds temporels")
        
        total_days = (end_date - start_date).days
        fold_size = total_days // self.n_splits
        
        folds = []
        
        for i in range(self.n_splits):
            # Date de début du fold
            fold_start = start_date + timedelta(days=i * fold_size)
            
            # Date de fin d'entraînement (80% du fold)
            train_end = fold_start + timedelta(days=int(fold_size * 0.8))
            
            # Date de début de validation
            validation_start = train_end + timedelta(days=1)
            
            # Date de fin de validation
            validation_end = fold_start + timedelta(days=fold_size)
            
            fold = TemporalFold(
                train_start=fold_start,
                train_end=train_end,
                validation_start=validation_start,
                validation_end=validation_end,
                fold_number=i + 1
            )
            
            folds.append(fold)
            
            logger.info(f"   Fold {i+1}: Train {fold_start.date()} → {train_end.date()}, "
                       f"Validation {validation_start.date()} → {validation_end.date()}")
        
        self.folds = folds
        return folds

class AdvancedMLRetrainer:
    """Système de réentraînement avancé avec validation croisée temporelle"""
    
    def __init__(self):
        DATABASE_URL = settings.database_url
        self.engine = create_engine(DATABASE_URL)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = SessionLocal()
        
        # Configuration - Utiliser seulement les colonnes disponibles
        self.feature_columns = [
            'rsi_14', 'macd', 'bb_position', 'adx_14', 'sma_ratio_20_50',
            'momentum_composite', 'volatility_composite', 'trend_strength',
            'bb_squeeze', 'cci_14', 'willr_14', 'stoch_k', 'stoch_d',
            'obv', 'ultosc', 'roc_10', 'atr_14', 'natr_14'
        ]
        
        # Modèles
        self.models = {
            'classification': RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            ),
            'regression': RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
        }
        
        # Résultats de validation
        self.validation_results = {}
        
    def load_training_data(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Charge les données d'entraînement pour une période donnée"""
        logger.info(f"📊 Chargement des données d'entraînement: {start_date.date()} → {end_date.date()}")
        
        query = f"""
        SELECT 
            ati.symbol,
            ati.date,
            ati.rsi_14,
            ati.macd,
            ati.bb_position,
            ati.adx_14,
            ati.sma_ratio_20_50,
            ati.momentum_composite,
            ati.volatility_composite,
            ati.trend_strength,
            ati.bb_squeeze,
            ati.cci_14,
            ati.willr_14,
            ati.stoch_k,
            ati.stoch_d,
            ati.obv,
            ati.ultosc,
            ati.roc_10,
            ati.atr_14,
            ati.natr_14,
            hd.close,
            hd.volume
        FROM advanced_technical_indicators ati
        JOIN historical_data hd ON ati.symbol = hd.symbol AND ati.date = hd.date
        WHERE ati.date BETWEEN '{start_date.date()}' AND '{end_date.date()}'
            AND ati.rsi_14 IS NOT NULL
            AND ati.macd IS NOT NULL
            AND ati.bb_position IS NOT NULL
        ORDER BY ati.symbol, ati.date
        """
        
        df = pd.read_sql(query, self.db.connection())
        logger.info(f"✅ {len(df)} enregistrements chargés")
        
        return df
    
    def calculate_target_variables(self, df: pd.DataFrame, horizon_days: int = 7) -> pd.DataFrame:
        """Calcule les variables cibles pour l'entraînement"""
        logger.info(f"🎯 Calcul des variables cibles (horizon: {horizon_days}j)")
        
        df_with_targets = []
        
        for symbol in df['symbol'].unique():
            symbol_df = df[df['symbol'] == symbol].copy().sort_values('date')
            
            if len(symbol_df) < horizon_days + 1:
                continue
            
            # Calculer les retours futurs
            symbol_df['future_price'] = symbol_df['close'].shift(-horizon_days)
            symbol_df['future_return'] = (symbol_df['future_price'] - symbol_df['close']) / symbol_df['close']
            
            # Créer les variables cibles
            symbol_df['target_classification'] = pd.cut(
                symbol_df['future_return'],
                bins=[-np.inf, -0.02, 0.02, np.inf],
                labels=['SELL', 'HOLD', 'BUY']
            )
            
            symbol_df['target_regression'] = symbol_df['future_return']
            
            # Supprimer les lignes avec des valeurs manquantes
            symbol_df = symbol_df.dropna(subset=['future_return', 'target_classification'])
            
            if len(symbol_df) > 0:  # Vérifier qu'il y a des données
                df_with_targets.append(symbol_df)
        
        if len(df_with_targets) == 0:
            logger.warning("⚠️ Aucune donnée avec variables cibles trouvée")
            return pd.DataFrame()
        
        result_df = pd.concat(df_with_targets, ignore_index=True)
        logger.info(f"✅ {len(result_df)} enregistrements avec variables cibles")
        
        return result_df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Prépare les features pour l'entraînement"""
        logger.info("🔧 Préparation des features")
        
        # Sélectionner les features
        X = df[self.feature_columns].fillna(0).values
        
        # Variables cibles
        y_classification = df['target_classification'].values
        y_regression = df['target_regression'].values
        
        logger.info(f"✅ Features shape: {X.shape}")
        logger.info(f"✅ Classification targets: {len(y_classification)}")
        logger.info(f"✅ Regression targets: {len(y_regression)}")
        
        return X, y_classification, y_regression
    
    def train_fold(self, fold: TemporalFold, horizon_days: int = 7) -> Dict:
        """Entraîne les modèles sur un fold temporel"""
        logger.info(f"🚀 Entraînement du fold {fold.fold_number}")
        
        # Charger les données d'entraînement
        train_df = self.load_training_data(fold.train_start, fold.train_end)
        
        if train_df.empty:
            logger.warning(f"⚠️ Aucune donnée d'entraînement pour le fold {fold.fold_number}")
            return {}
        
        # Calculer les variables cibles
        train_df_with_targets = self.calculate_target_variables(train_df, horizon_days)
        
        if train_df_with_targets.empty:
            logger.warning(f"⚠️ Aucune donnée avec variables cibles pour le fold {fold.fold_number}")
            return {}
        
        # Préparer les features
        X_train, y_class_train, y_reg_train = self.prepare_features(train_df_with_targets)
        
        # Entraîner les modèles
        logger.info(f"   📊 Entraînement du modèle de classification...")
        self.models['classification'].fit(X_train, y_class_train)
        
        logger.info(f"   📈 Entraînement du modèle de régression...")
        self.models['regression'].fit(X_train, y_reg_train)
        
        # Charger les données de validation
        val_df = self.load_training_data(fold.validation_start, fold.validation_end)
        
        if val_df.empty:
            logger.warning(f"⚠️ Aucune donnée de validation pour le fold {fold.fold_number}")
            return {}
        
        val_df_with_targets = self.calculate_target_variables(val_df, horizon_days)
        
        if val_df_with_targets.empty:
            logger.warning(f"⚠️ Aucune donnée de validation avec variables cibles pour le fold {fold.fold_number}")
            return {}
        
        X_val, y_class_val, y_reg_val = self.prepare_features(val_df_with_targets)
        
        # Prédictions
        y_class_pred = self.models['classification'].predict(X_val)
        y_reg_pred = self.models['regression'].predict(X_val)
        
        # Métriques de validation
        classification_accuracy = accuracy_score(y_class_val, y_class_pred)
        regression_mse = mean_squared_error(y_reg_val, y_reg_pred)
        
        # Distribution des prédictions
        pred_distribution = pd.Series(y_class_pred).value_counts().to_dict()
        actual_distribution = pd.Series(y_class_val).value_counts().to_dict()
        
        fold_results = {
            'fold_number': fold.fold_number,
            'train_samples': len(X_train),
            'validation_samples': len(X_val),
            'classification_accuracy': classification_accuracy,
            'regression_mse': regression_mse,
            'prediction_distribution': pred_distribution,
            'actual_distribution': actual_distribution,
            'feature_importance': self.models['classification'].feature_importances_.tolist()
        }
        
        logger.info(f"✅ Fold {fold.fold_number} terminé:")
        logger.info(f"   Accuracy: {classification_accuracy:.4f}")
        logger.info(f"   MSE: {regression_mse:.6f}")
        logger.info(f"   Échantillons train: {len(X_train)}")
        logger.info(f"   Échantillons validation: {len(X_val)}")
        
        return fold_results
    
    def run_temporal_cross_validation(self, start_date: datetime, end_date: datetime, 
                                    horizon_days: int = 7) -> Dict:
        """Lance la validation croisée temporelle complète"""
        logger.info("🚀 Début de la validation croisée temporelle")
        
        # Créer les folds temporels
        validator = TemporalCrossValidator(n_splits=3, test_size_days=14)  # Réduire à 3 folds avec validation de 14 jours
        folds = validator.create_temporal_folds(start_date, end_date)
        
        # Résultats globaux
        all_results = []
        
        # Entraîner sur chaque fold
        for fold in folds:
            fold_results = self.train_fold(fold, horizon_days)
            if fold_results:
                all_results.append(fold_results)
        
        # Calculer les métriques moyennes
        if all_results:
            avg_accuracy = np.mean([r['classification_accuracy'] for r in all_results])
            avg_mse = np.mean([r['regression_mse'] for r in all_results])
            
            # Importance des features moyenne
            feature_importance_avg = np.mean([r['feature_importance'] for r in all_results], axis=0)
            
            # Distribution moyenne des prédictions
            all_pred_dist = {}
            all_actual_dist = {}
            
            for result in all_results:
                for key, value in result['prediction_distribution'].items():
                    all_pred_dist[key] = all_pred_dist.get(key, 0) + value
                for key, value in result['actual_distribution'].items():
                    all_actual_dist[key] = all_actual_dist.get(key, 0) + value
            
            # Normaliser les distributions
            total_pred = sum(all_pred_dist.values())
            total_actual = sum(all_actual_dist.values())
            
            pred_dist_normalized = {k: v/total_pred for k, v in all_pred_dist.items()}
            actual_dist_normalized = {k: v/total_actual for k, v in all_actual_dist.items()}
            
            # Résultats finaux
            final_results = {
                'cross_validation_results': all_results,
                'average_accuracy': avg_accuracy,
                'average_mse': avg_mse,
                'feature_importance': feature_importance_avg.tolist(),
                'feature_names': self.feature_columns,
                'prediction_distribution': pred_dist_normalized,
                'actual_distribution': actual_dist_normalized,
                'total_folds': len(all_results),
                'validation_period': f"{start_date.date()} → {end_date.date()}",
                'horizon_days': horizon_days
            }
            
            logger.info("\n📊 RÉSULTATS DE LA VALIDATION CROISÉE")
            logger.info("=" * 50)
            logger.info(f"📈 Accuracy moyenne: {avg_accuracy:.4f}")
            logger.info(f"📊 MSE moyenne: {avg_mse:.6f}")
            logger.info(f"📅 Période de validation: {start_date.date()} → {end_date.date()}")
            logger.info(f"⏰ Horizon: {horizon_days} jours")
            logger.info(f"📊 Nombre de folds: {len(all_results)}")
            
            logger.info(f"\n🎯 Distribution des prédictions:")
            for label, prob in pred_dist_normalized.items():
                logger.info(f"   {label}: {prob:.3f}")
            
            logger.info(f"\n📊 Distribution réelle:")
            for label, prob in actual_dist_normalized.items():
                logger.info(f"   {label}: {prob:.3f}")
            
            logger.info(f"\n🔧 Top 5 features les plus importantes:")
            feature_importance_pairs = list(zip(self.feature_columns, feature_importance_avg))
            feature_importance_pairs.sort(key=lambda x: x[1], reverse=True)
            
            for i, (feature, importance) in enumerate(feature_importance_pairs[:5]):
                logger.info(f"   {i+1}. {feature}: {importance:.4f}")
            
            return final_results
        
        else:
            logger.error("❌ Aucun résultat de validation obtenu")
            return {}
    
    def save_trained_models(self, results: Dict, model_version: str = "v2"):
        """Sauvegarde les modèles entraînés"""
        logger.info("💾 Sauvegarde des modèles entraînés")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Sauvegarder les modèles
        models_path = os.path.join(backend_path, f"trained_models_{model_version}_{timestamp}")
        os.makedirs(models_path, exist_ok=True)
        
        # Modèle de classification
        classification_path = os.path.join(models_path, "classification_model.pkl")
        with open(classification_path, 'wb') as f:
            pickle.dump(self.models['classification'], f)
        
        # Modèle de régression
        regression_path = os.path.join(models_path, "regression_model.pkl")
        with open(regression_path, 'wb') as f:
            pickle.dump(self.models['regression'], f)
        
        # Résultats de validation
        results_path = os.path.join(models_path, "validation_results.json")
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"✅ Modèles sauvegardés dans {models_path}")
        
        return models_path
    
    def generate_opportunities_with_new_models(self, models_path: str, 
                                              start_date: datetime, end_date: datetime):
        """Génère des opportunités avec les nouveaux modèles"""
        logger.info("🎯 Génération d'opportunités avec les nouveaux modèles")
        
        # Charger les modèles
        classification_path = os.path.join(models_path, "classification_model.pkl")
        regression_path = os.path.join(models_path, "regression_model.pkl")
        
        with open(classification_path, 'rb') as f:
            classification_model = pickle.load(f)
        
        with open(regression_path, 'rb') as f:
            regression_model = pickle.load(f)
        
        # Charger les données récentes
        recent_data = self.load_training_data(start_date, end_date)
        
        if recent_data.empty:
            logger.error("❌ Aucune donnée récente trouvée")
            return
        
        # Préparer les features
        X = recent_data[self.feature_columns].fillna(0).values
        
        # Prédictions
        predictions_class = classification_model.predict(X)
        predictions_reg = regression_model.predict(X)
        predictions_proba = classification_model.predict_proba(X)
        
        # Créer le DataFrame des opportunités
        opportunities_df = recent_data[['symbol', 'date']].copy()
        opportunities_df['predicted_recommendation'] = predictions_class
        opportunities_df['predicted_return'] = predictions_reg
        opportunities_df['confidence_level'] = np.max(predictions_proba, axis=1)
        
        # Ajouter les horizons (pour l'instant, on utilise 7 jours)
        opportunities_df['horizon_days'] = 7
        
        logger.info(f"✅ {len(opportunities_df)} opportunités générées")
        
        # Statistiques des prédictions
        pred_dist = pd.Series(predictions_class).value_counts()
        logger.info(f"📊 Distribution des prédictions:")
        for label, count in pred_dist.items():
            logger.info(f"   {label}: {count} ({count/len(predictions_class)*100:.1f}%)")
        
        return opportunities_df

def main():
    """Fonction principale"""
    retrainer = AdvancedMLRetrainer()
    
    try:
        # Définir les périodes d'entraînement et de validation
        # Utiliser des données récentes et représentatives (éviter avril 2025 volatil)
        end_date = datetime.now()
        start_date = datetime(2025, 5, 15)  # Début après les perturbations d'avril
        
        logger.info(f"📅 Période d'entraînement (marché normal): {start_date.date()} → {end_date.date()}")
        
        # Lancer la validation croisée temporelle
        results = retrainer.run_temporal_cross_validation(start_date, end_date, horizon_days=7)
        
        if results:
            # Sauvegarder les modèles
            models_path = retrainer.save_trained_models(results, model_version="temporal_cv")
            
            # Générer des opportunités avec les nouveaux modèles
            recent_start = end_date - timedelta(days=30)  # Derniers 30 jours
            opportunities = retrainer.generate_opportunities_with_new_models(
                models_path, recent_start, end_date
            )
            
            logger.info("\n🎉 Réentraînement terminé avec succès!")
            logger.info(f"📊 Accuracy moyenne: {results['average_accuracy']:.4f}")
            logger.info(f"📈 MSE moyenne: {results['average_mse']:.6f}")
            logger.info(f"💾 Modèles sauvegardés dans: {models_path}")
            
        else:
            logger.error("❌ Échec du réentraînement")
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du réentraînement: {e}", exc_info=True)
        raise
    finally:
        retrainer.db.close()

if __name__ == "__main__":
    main()
