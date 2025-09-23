"""
Service LightGBM pour l'analyse de tendance financière
"""
import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, date
from sqlalchemy.orm import Session
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')

from app.models.database import (
    HistoricalData, TechnicalIndicators, SentimentIndicators, 
    TargetParameters, MLModels, MLPredictions
)
from app.core.config import settings


class LightGBMService:
    """Service pour les modèles LightGBM spécialisés dans l'analyse de tendance financière"""
    
    def __init__(self, db: Session = None):
        self.db = db
        self.models_path = settings.ml_models_path
        self.ensure_models_directory()
        
        # Paramètres par défaut pour LightGBM
        self.default_params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': 42
        }
        
        # Paramètres pour la régression
        self.regression_params = {
            'objective': 'regression',
            'metric': 'rmse',
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': 42
        }
        
        # Paramètres pour la classification multi-classe
        self.multiclass_params = {
            'objective': 'multiclass',
            'metric': 'multi_logloss',
            'num_class': 5,  # 5 classes : forte baisse, baisse, stable, hausse, forte hausse
            'boosting_type': 'gbdt',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'feature_fraction': 0.9,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': 42
        }
    
    def ensure_models_directory(self):
        """Crée le répertoire des modèles s'il n'existe pas"""
        if not os.path.exists(self.models_path):
            os.makedirs(self.models_path)
    
    def get_feature_columns(self) -> List[str]:
        """Retourne la liste des colonnes de features pour l'entraînement"""
        return [
            # Indicateurs techniques
            'sma_5', 'sma_10', 'sma_20', 'sma_50', 'sma_200',
            'ema_5', 'ema_10', 'ema_20', 'ema_50', 'ema_200',
            'rsi_14', 'macd', 'macd_signal', 'macd_histogram',
            'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_position',
            'atr_14', 'obv', 'volume_roc', 'volume_sma_20',
            'stochastic_k', 'stochastic_d', 'williams_r',
            'roc', 'cci',
            
            # Indicateurs de sentiment
            'sentiment_score_normalized',
            'sentiment_momentum_1d', 'sentiment_momentum_3d', 'sentiment_momentum_7d', 'sentiment_momentum_14d',
            'sentiment_volatility_3d', 'sentiment_volatility_7d', 'sentiment_volatility_14d', 'sentiment_volatility_30d',
            'sentiment_sma_3', 'sentiment_sma_7', 'sentiment_sma_14', 'sentiment_sma_30',
            'sentiment_ema_3', 'sentiment_ema_7', 'sentiment_ema_14', 'sentiment_ema_30',
            'sentiment_rsi_14', 'sentiment_macd', 'sentiment_macd_signal', 'sentiment_macd_histogram',
            'news_volume_sma_7', 'news_volume_sma_14', 'news_volume_sma_30',
            'news_volume_roc_7d', 'news_volume_roc_14d',
            'news_positive_ratio', 'news_negative_ratio', 'news_neutral_ratio', 'news_sentiment_quality'
        ]
    
    def create_advanced_labels(self, df: pd.DataFrame, target_param: TargetParameters) -> pd.DataFrame:
        """Crée des labels avancés pour l'entraînement LightGBM"""
        df = df.copy()
        
        # Calcul du rendement futur
        df['future_return'] = df['close'].pct_change(periods=target_param.time_horizon_days).shift(-target_param.time_horizon_days)
        
        # Labels de classification binaire
        target_return_float = float(target_param.target_return_percentage)
        df['target_achieved'] = (df['future_return'] >= target_return_float).astype(int)
        
        # Labels de classification multi-classe (5 classes)
        df['return_class'] = 0  # Par défaut : stable
        df.loc[df['future_return'] < -0.05, 'return_class'] = 0  # Forte baisse
        df.loc[(df['future_return'] >= -0.05) & (df['future_return'] < -0.01), 'return_class'] = 1  # Baisse
        df.loc[(df['future_return'] >= -0.01) & (df['future_return'] < 0.01), 'return_class'] = 2  # Stable
        df.loc[(df['future_return'] >= 0.01) & (df['future_return'] < 0.05), 'return_class'] = 3  # Hausse
        df.loc[df['future_return'] >= 0.05, 'return_class'] = 4  # Forte hausse
        
        # Labels de régression (rendement exact)
        df['target_return'] = df['future_return']
        
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Prépare les features pour l'entraînement LightGBM"""
        feature_columns = self.get_feature_columns()
        
        # Sélection des colonnes disponibles
        available_features = [col for col in feature_columns if col in df.columns]
        
        # Remplissage des valeurs manquantes
        df_features = df[available_features].fillna(method='ffill').fillna(0)
        
        # Suppression des lignes avec des valeurs infinies
        df_features = df_features.replace([np.inf, -np.inf], np.nan).fillna(0)
        
        return df_features, available_features
    
    def train_binary_classification_model(self, symbol: str, target_param: TargetParameters, 
                                        db: Session = None) -> Dict[str, Any]:
        """Entraîne un modèle LightGBM de classification binaire"""
        if db is None:
            db = self.db
            
        # Récupération des données
        query = db.query(HistoricalData, TechnicalIndicators, SentimentIndicators).join(
            TechnicalIndicators, HistoricalData.symbol == TechnicalIndicators.symbol
        ).join(
            SentimentIndicators, HistoricalData.symbol == SentimentIndicators.symbol
        ).filter(
            HistoricalData.symbol == symbol
        ).order_by(HistoricalData.date)
        
        results = query.all()
        
        if not results:
            raise ValueError(f"Aucune donnée trouvée pour le symbole {symbol}")
        
        # Conversion en DataFrame
        data = []
        for hist, tech, sent in results:
            row = {
                'date': hist.date,
                'symbol': hist.symbol,
                'open': float(hist.open),
                'high': float(hist.high),
                'low': float(hist.low),
                'close': float(hist.close),
                'volume': float(hist.volume),
                'vwap': float(hist.vwap),
                
                # Indicateurs techniques
                'sma_5': float(tech.sma_5) if tech.sma_5 else 0,
                'sma_10': float(tech.sma_10) if tech.sma_10 else 0,
                'sma_20': float(tech.sma_20) if tech.sma_20 else 0,
                'sma_50': float(tech.sma_50) if tech.sma_50 else 0,
                'ema_5': float(tech.ema_5) if tech.ema_5 else 0,
                'ema_10': float(tech.ema_10) if tech.ema_10 else 0,
                'ema_20': float(tech.ema_20) if tech.ema_20 else 0,
                'ema_50': float(tech.ema_50) if tech.ema_50 else 0,
                'rsi': float(tech.rsi) if tech.rsi else 0,
                'macd': float(tech.macd) if tech.macd else 0,
                'macd_signal': float(tech.macd_signal) if tech.macd_signal else 0,
                'macd_histogram': float(tech.macd_histogram) if tech.macd_histogram else 0,
                'bb_upper': float(tech.bb_upper) if tech.bb_upper else 0,
                'bb_middle': float(tech.bb_middle) if tech.bb_middle else 0,
                'bb_lower': float(tech.bb_lower) if tech.bb_lower else 0,
                'bb_width': float(tech.bb_width) if tech.bb_width else 0,
                'atr': float(tech.atr) if tech.atr else 0,
                'obv': float(tech.obv) if tech.obv else 0,
                'vwap': float(tech.vwap) if tech.vwap else 0,
                'volume_roc': float(tech.volume_roc) if tech.volume_roc else 0,
                'stochastic_k': float(tech.stochastic_k) if tech.stochastic_k else 0,
                'stochastic_d': float(tech.stochastic_d) if tech.stochastic_d else 0,
                'williams_r': float(tech.williams_r) if tech.williams_r else 0,
                'roc': float(tech.roc) if tech.roc else 0,
                'cci': float(tech.cci) if tech.cci else 0,
                'volume_sma': float(tech.volume_sma) if tech.volume_sma else 0,
                
                # Indicateurs de sentiment
                'news_sentiment_score': float(sent.news_sentiment_score) if sent.news_sentiment_score else 0,
                'short_interest_ratio': float(sent.short_interest_ratio) if sent.short_interest_ratio else 0,
                'sentiment_momentum': float(sent.sentiment_momentum) if sent.sentiment_momentum else 0,
                'sentiment_volatility': float(sent.sentiment_volatility) if sent.sentiment_volatility else 0,
                'sentiment_sma': float(sent.sentiment_sma) if sent.sentiment_sma else 0,
                'sentiment_ema': float(sent.sentiment_ema) if sent.sentiment_ema else 0,
                'sentiment_rsi': float(sent.sentiment_rsi) if sent.sentiment_rsi else 0,
                'sentiment_macd': float(sent.sentiment_macd) if sent.sentiment_macd else 0,
                'news_volume': float(sent.news_volume) if sent.news_volume else 0,
                'sentiment_distribution': float(sent.sentiment_distribution) if sent.sentiment_distribution else 0,
                'composite_sentiment': float(sent.composite_sentiment) if sent.composite_sentiment else 0,
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Création des labels
        df = self.create_advanced_labels(df, target_param)
        
        # Préparation des features
        X, feature_names = self.prepare_features(df)
        y = df['target_achieved']
        
        # Suppression des lignes avec des labels manquants
        valid_indices = ~(y.isna() | X.isna().any(axis=1))
        X = X[valid_indices]
        y = y[valid_indices]
        
        if len(X) < 100:
            raise ValueError(f"Pas assez de données pour l'entraînement: {len(X)} échantillons")
        
        # Division train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Création du dataset LightGBM
        train_data = lgb.Dataset(X_train, label=y_train)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
        
        # Entraînement du modèle
        model = lgb.train(
            self.default_params,
            train_data,
            valid_sets=[test_data],
            num_boost_round=1000,
            callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(0)]
        )
        
        # Prédictions
        y_pred = model.predict(X_test, num_iteration=model.best_iteration)
        y_pred_binary = (y_pred > 0.5).astype(int)
        
        # Métriques
        accuracy = accuracy_score(y_test, y_pred_binary)
        precision = precision_score(y_test, y_pred_binary, zero_division=0)
        recall = recall_score(y_test, y_pred_binary, zero_division=0)
        f1 = f1_score(y_test, y_pred_binary, zero_division=0)
        
        # Importance des features
        feature_importance = dict(zip(feature_names, model.feature_importance()))
        
        # Sauvegarde du modèle
        model_name = f"lightgbm_binary_{symbol}_{target_param.parameter_name}_v1"
        model_path = os.path.join(self.models_path, f"{model_name}.joblib")
        joblib.dump(model, model_path)
        
        # Sauvegarde en base de données
        model_record = MLModels(
            name=model_name,
            model_type="lightgbm_binary_classification",
            symbol=symbol,
            target_parameter_id=target_param.id,
            model_parameters={
                "algorithm": "LightGBM",
                "objective": "binary_classification",
                "target_return": float(target_param.target_return_percentage),
                "time_horizon": int(target_param.time_horizon_days),
                "features": feature_names,
                "feature_importance": feature_importance,
                "best_iteration": int(model.best_iteration),
                "num_boost_round": 1000
            },
            performance_metrics={
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
                "test_samples": len(X_test),
                "train_samples": len(X_train)
            },
            model_path=model_path,
            is_active=True,
            created_by="lightgbm_service"
        )
        
        db.add(model_record)
        db.commit()
        db.refresh(model_record)
        
        return {
            "model_id": model_record.id,
            "model_name": model_name,
            "model_path": model_path,
            "performance": {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1
            },
            "feature_importance": feature_importance,
            "best_iteration": model.best_iteration,
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }
    
    def train_multiclass_classification_model(self, symbol: str, target_param: TargetParameters, 
                                            db: Session = None) -> Dict[str, Any]:
        """Entraîne un modèle LightGBM de classification multi-classe"""
        if db is None:
            db = self.db
            
        # Récupération des données (même logique que pour la classification binaire)
        query = db.query(HistoricalData, TechnicalIndicators, SentimentIndicators).join(
            TechnicalIndicators, HistoricalData.symbol == TechnicalIndicators.symbol
        ).join(
            SentimentIndicators, HistoricalData.symbol == SentimentIndicators.symbol
        ).filter(
            HistoricalData.symbol == symbol
        ).order_by(HistoricalData.date)
        
        results = query.all()
        
        if not results:
            raise ValueError(f"Aucune donnée trouvée pour le symbole {symbol}")
        
        # Conversion en DataFrame (même logique que pour la classification binaire)
        data = []
        for hist, tech, sent in results:
            row = {
                'date': hist.date,
                'symbol': hist.symbol,
                'open': float(hist.open),
                'high': float(hist.high),
                'low': float(hist.low),
                'close': float(hist.close),
                'volume': float(hist.volume),
                'vwap': float(hist.vwap),
                
                # Indicateurs techniques
                'sma_5': float(tech.sma_5) if tech.sma_5 else 0,
                'sma_10': float(tech.sma_10) if tech.sma_10 else 0,
                'sma_20': float(tech.sma_20) if tech.sma_20 else 0,
                'sma_50': float(tech.sma_50) if tech.sma_50 else 0,
                'ema_5': float(tech.ema_5) if tech.ema_5 else 0,
                'ema_10': float(tech.ema_10) if tech.ema_10 else 0,
                'ema_20': float(tech.ema_20) if tech.ema_20 else 0,
                'ema_50': float(tech.ema_50) if tech.ema_50 else 0,
                'rsi': float(tech.rsi) if tech.rsi else 0,
                'macd': float(tech.macd) if tech.macd else 0,
                'macd_signal': float(tech.macd_signal) if tech.macd_signal else 0,
                'macd_histogram': float(tech.macd_histogram) if tech.macd_histogram else 0,
                'bb_upper': float(tech.bb_upper) if tech.bb_upper else 0,
                'bb_middle': float(tech.bb_middle) if tech.bb_middle else 0,
                'bb_lower': float(tech.bb_lower) if tech.bb_lower else 0,
                'bb_width': float(tech.bb_width) if tech.bb_width else 0,
                'atr': float(tech.atr) if tech.atr else 0,
                'obv': float(tech.obv) if tech.obv else 0,
                'vwap': float(tech.vwap) if tech.vwap else 0,
                'volume_roc': float(tech.volume_roc) if tech.volume_roc else 0,
                'stochastic_k': float(tech.stochastic_k) if tech.stochastic_k else 0,
                'stochastic_d': float(tech.stochastic_d) if tech.stochastic_d else 0,
                'williams_r': float(tech.williams_r) if tech.williams_r else 0,
                'roc': float(tech.roc) if tech.roc else 0,
                'cci': float(tech.cci) if tech.cci else 0,
                'volume_sma': float(tech.volume_sma) if tech.volume_sma else 0,
                
                # Indicateurs de sentiment
                'news_sentiment_score': float(sent.news_sentiment_score) if sent.news_sentiment_score else 0,
                'short_interest_ratio': float(sent.short_interest_ratio) if sent.short_interest_ratio else 0,
                'sentiment_momentum': float(sent.sentiment_momentum) if sent.sentiment_momentum else 0,
                'sentiment_volatility': float(sent.sentiment_volatility) if sent.sentiment_volatility else 0,
                'sentiment_sma': float(sent.sentiment_sma) if sent.sentiment_sma else 0,
                'sentiment_ema': float(sent.sentiment_ema) if sent.sentiment_ema else 0,
                'sentiment_rsi': float(sent.sentiment_rsi) if sent.sentiment_rsi else 0,
                'sentiment_macd': float(sent.sentiment_macd) if sent.sentiment_macd else 0,
                'news_volume': float(sent.news_volume) if sent.news_volume else 0,
                'sentiment_distribution': float(sent.sentiment_distribution) if sent.sentiment_distribution else 0,
                'composite_sentiment': float(sent.composite_sentiment) if sent.composite_sentiment else 0,
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Création des labels
        df = self.create_advanced_labels(df, target_param)
        
        # Préparation des features
        X, feature_names = self.prepare_features(df)
        y = df['return_class']
        
        # Suppression des lignes avec des labels manquants
        valid_indices = ~(y.isna() | X.isna().any(axis=1))
        X = X[valid_indices]
        y = y[valid_indices]
        
        if len(X) < 100:
            raise ValueError(f"Pas assez de données pour l'entraînement: {len(X)} échantillons")
        
        # Division train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Création du dataset LightGBM
        train_data = lgb.Dataset(X_train, label=y_train)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
        
        # Entraînement du modèle
        model = lgb.train(
            self.multiclass_params,
            train_data,
            valid_sets=[test_data],
            num_boost_round=1000,
            callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(0)]
        )
        
        # Prédictions
        y_pred = model.predict(X_test, num_iteration=model.best_iteration)
        y_pred_class = np.argmax(y_pred, axis=1)
        
        # Métriques
        accuracy = accuracy_score(y_test, y_pred_class)
        precision = precision_score(y_test, y_pred_class, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred_class, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred_class, average='weighted', zero_division=0)
        
        # Importance des features
        feature_importance = dict(zip(feature_names, model.feature_importance()))
        
        # Sauvegarde du modèle
        model_name = f"lightgbm_multiclass_{symbol}_{target_param.parameter_name}_v1"
        model_path = os.path.join(self.models_path, f"{model_name}.joblib")
        joblib.dump(model, model_path)
        
        # Sauvegarde en base de données
        model_record = MLModels(
            name=model_name,
            model_type="lightgbm_multiclass_classification",
            symbol=symbol,
            target_parameter_id=target_param.id,
            model_parameters={
                "algorithm": "LightGBM",
                "objective": "multiclass_classification",
                "num_classes": 5,
                "class_names": ["Forte baisse", "Baisse", "Stable", "Hausse", "Forte hausse"],
                "target_return": float(target_param.target_return_percentage),
                "time_horizon": int(target_param.time_horizon_days),
                "features": feature_names,
                "feature_importance": feature_importance,
                "best_iteration": int(model.best_iteration),
                "num_boost_round": 1000
            },
            performance_metrics={
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
                "test_samples": len(X_test),
                "train_samples": len(X_train)
            },
            model_path=model_path,
            is_active=True,
            created_by="lightgbm_service"
        )
        
        db.add(model_record)
        db.commit()
        db.refresh(model_record)
        
        return {
            "model_id": model_record.id,
            "model_name": model_name,
            "model_path": model_path,
            "performance": {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1
            },
            "feature_importance": feature_importance,
            "best_iteration": model.best_iteration,
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }
    
    def train_regression_model(self, symbol: str, target_param: TargetParameters, 
                             db: Session = None) -> Dict[str, Any]:
        """Entraîne un modèle LightGBM de régression"""
        if db is None:
            db = self.db
            
        # Récupération des données (même logique que pour la classification)
        query = db.query(HistoricalData, TechnicalIndicators, SentimentIndicators).join(
            TechnicalIndicators, HistoricalData.symbol == TechnicalIndicators.symbol
        ).join(
            SentimentIndicators, HistoricalData.symbol == SentimentIndicators.symbol
        ).filter(
            HistoricalData.symbol == symbol
        ).order_by(HistoricalData.date)
        
        results = query.all()
        
        if not results:
            raise ValueError(f"Aucune donnée trouvée pour le symbole {symbol}")
        
        # Conversion en DataFrame (même logique que pour la classification)
        data = []
        for hist, tech, sent in results:
            row = {
                'date': hist.date,
                'symbol': hist.symbol,
                'open': float(hist.open),
                'high': float(hist.high),
                'low': float(hist.low),
                'close': float(hist.close),
                'volume': float(hist.volume),
                'vwap': float(hist.vwap),
                
                # Indicateurs techniques
                'sma_5': float(tech.sma_5) if tech.sma_5 else 0,
                'sma_10': float(tech.sma_10) if tech.sma_10 else 0,
                'sma_20': float(tech.sma_20) if tech.sma_20 else 0,
                'sma_50': float(tech.sma_50) if tech.sma_50 else 0,
                'ema_5': float(tech.ema_5) if tech.ema_5 else 0,
                'ema_10': float(tech.ema_10) if tech.ema_10 else 0,
                'ema_20': float(tech.ema_20) if tech.ema_20 else 0,
                'ema_50': float(tech.ema_50) if tech.ema_50 else 0,
                'rsi': float(tech.rsi) if tech.rsi else 0,
                'macd': float(tech.macd) if tech.macd else 0,
                'macd_signal': float(tech.macd_signal) if tech.macd_signal else 0,
                'macd_histogram': float(tech.macd_histogram) if tech.macd_histogram else 0,
                'bb_upper': float(tech.bb_upper) if tech.bb_upper else 0,
                'bb_middle': float(tech.bb_middle) if tech.bb_middle else 0,
                'bb_lower': float(tech.bb_lower) if tech.bb_lower else 0,
                'bb_width': float(tech.bb_width) if tech.bb_width else 0,
                'atr': float(tech.atr) if tech.atr else 0,
                'obv': float(tech.obv) if tech.obv else 0,
                'vwap': float(tech.vwap) if tech.vwap else 0,
                'volume_roc': float(tech.volume_roc) if tech.volume_roc else 0,
                'stochastic_k': float(tech.stochastic_k) if tech.stochastic_k else 0,
                'stochastic_d': float(tech.stochastic_d) if tech.stochastic_d else 0,
                'williams_r': float(tech.williams_r) if tech.williams_r else 0,
                'roc': float(tech.roc) if tech.roc else 0,
                'cci': float(tech.cci) if tech.cci else 0,
                'volume_sma': float(tech.volume_sma) if tech.volume_sma else 0,
                
                # Indicateurs de sentiment
                'news_sentiment_score': float(sent.news_sentiment_score) if sent.news_sentiment_score else 0,
                'short_interest_ratio': float(sent.short_interest_ratio) if sent.short_interest_ratio else 0,
                'sentiment_momentum': float(sent.sentiment_momentum) if sent.sentiment_momentum else 0,
                'sentiment_volatility': float(sent.sentiment_volatility) if sent.sentiment_volatility else 0,
                'sentiment_sma': float(sent.sentiment_sma) if sent.sentiment_sma else 0,
                'sentiment_ema': float(sent.sentiment_ema) if sent.sentiment_ema else 0,
                'sentiment_rsi': float(sent.sentiment_rsi) if sent.sentiment_rsi else 0,
                'sentiment_macd': float(sent.sentiment_macd) if sent.sentiment_macd else 0,
                'news_volume': float(sent.news_volume) if sent.news_volume else 0,
                'sentiment_distribution': float(sent.sentiment_distribution) if sent.sentiment_distribution else 0,
                'composite_sentiment': float(sent.composite_sentiment) if sent.composite_sentiment else 0,
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Création des labels
        df = self.create_advanced_labels(df, target_param)
        
        # Préparation des features
        X, feature_names = self.prepare_features(df)
        y = df['target_return']
        
        # Suppression des lignes avec des labels manquants
        valid_indices = ~(y.isna() | X.isna().any(axis=1))
        X = X[valid_indices]
        y = y[valid_indices]
        
        if len(X) < 100:
            raise ValueError(f"Pas assez de données pour l'entraînement: {len(X)} échantillons")
        
        # Division train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Création du dataset LightGBM
        train_data = lgb.Dataset(X_train, label=y_train)
        test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)
        
        # Entraînement du modèle
        model = lgb.train(
            self.regression_params,
            train_data,
            valid_sets=[test_data],
            num_boost_round=1000,
            callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(0)]
        )
        
        # Prédictions
        y_pred = model.predict(X_test, num_iteration=model.best_iteration)
        
        # Métriques
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred)
        
        # Importance des features
        feature_importance = dict(zip(feature_names, model.feature_importance()))
        
        # Sauvegarde du modèle
        model_name = f"lightgbm_regression_{symbol}_{target_param.parameter_name}_v1"
        model_path = os.path.join(self.models_path, f"{model_name}.joblib")
        joblib.dump(model, model_path)
        
        # Sauvegarde en base de données
        model_record = MLModels(
            name=model_name,
            model_type="lightgbm_regression",
            symbol=symbol,
            target_parameter_id=target_param.id,
            model_parameters={
                "algorithm": "LightGBM",
                "objective": "regression",
                "target_return": float(target_param.target_return_percentage),
                "time_horizon": int(target_param.time_horizon_days),
                "features": feature_names,
                "feature_importance": feature_importance,
                "best_iteration": int(model.best_iteration),
                "num_boost_round": 1000
            },
            performance_metrics={
                "mse": float(mse),
                "rmse": float(rmse),
                "r2_score": float(r2),
                "test_samples": len(X_test),
                "train_samples": len(X_train)
            },
            model_path=model_path,
            is_active=True,
            created_by="lightgbm_service"
        )
        
        db.add(model_record)
        db.commit()
        db.refresh(model_record)
        
        return {
            "model_id": model_record.id,
            "model_name": model_name,
            "model_path": model_path,
            "performance": {
                "mse": mse,
                "rmse": rmse,
                "r2_score": r2
            },
            "feature_importance": feature_importance,
            "best_iteration": model.best_iteration,
            "training_samples": len(X_train),
            "test_samples": len(X_test)
        }
    
    def predict(self, model_id: int, symbol: str, prediction_date: date, 
                db: Session = None) -> Dict[str, Any]:
        """Effectue une prédiction avec un modèle LightGBM"""
        if db is None:
            db = self.db
            
        # Récupération du modèle
        model_record = db.query(MLModels).filter(MLModels.id == model_id).first()
        if not model_record:
            raise ValueError(f"Modèle {model_id} non trouvé")
        
        # Chargement du modèle
        model = joblib.load(model_record.model_path)
        
        # Récupération des données pour la prédiction
        query = db.query(HistoricalData, TechnicalIndicators, SentimentIndicators).join(
            TechnicalIndicators, HistoricalData.symbol == TechnicalIndicators.symbol
        ).join(
            SentimentIndicators, HistoricalData.symbol == SentimentIndicators.symbol
        ).filter(
            HistoricalData.symbol == symbol,
            HistoricalData.date == prediction_date
        )
        
        result = query.first()
        
        if not result:
            # Fallback: récupérer les données les plus récentes
            query = db.query(HistoricalData, TechnicalIndicators, SentimentIndicators).join(
                TechnicalIndicators, HistoricalData.symbol == TechnicalIndicators.symbol
            ).join(
                SentimentIndicators, HistoricalData.symbol == SentimentIndicators.symbol
            ).filter(
                HistoricalData.symbol == symbol
            ).order_by(HistoricalData.date.desc()).limit(1)
            
            result = query.first()
            
            if not result:
                raise ValueError(f"Aucune donnée trouvée pour le symbole {symbol}")
        
        hist, tech, sent = result
        data_date_used = hist.date
        
        # Préparation des features
        features = {
            'sma_5': float(tech.sma_5) if tech.sma_5 else 0,
            'sma_10': float(tech.sma_10) if tech.sma_10 else 0,
            'sma_20': float(tech.sma_20) if tech.sma_20 else 0,
            'sma_50': float(tech.sma_50) if tech.sma_50 else 0,
            'ema_5': float(tech.ema_5) if tech.ema_5 else 0,
            'ema_10': float(tech.ema_10) if tech.ema_10 else 0,
            'ema_20': float(tech.ema_20) if tech.ema_20 else 0,
            'ema_50': float(tech.ema_50) if tech.ema_50 else 0,
            'rsi': float(tech.rsi) if tech.rsi else 0,
            'macd': float(tech.macd) if tech.macd else 0,
            'macd_signal': float(tech.macd_signal) if tech.macd_signal else 0,
            'macd_histogram': float(tech.macd_histogram) if tech.macd_histogram else 0,
            'bb_upper': float(tech.bb_upper) if tech.bb_upper else 0,
            'bb_middle': float(tech.bb_middle) if tech.bb_middle else 0,
            'bb_lower': float(tech.bb_lower) if tech.bb_lower else 0,
            'bb_width': float(tech.bb_width) if tech.bb_width else 0,
            'atr': float(tech.atr) if tech.atr else 0,
            'obv': float(tech.obv) if tech.obv else 0,
            'vwap': float(tech.vwap) if tech.vwap else 0,
            'volume_roc': float(tech.volume_roc) if tech.volume_roc else 0,
            'stochastic_k': float(tech.stochastic_k) if tech.stochastic_k else 0,
            'stochastic_d': float(tech.stochastic_d) if tech.stochastic_d else 0,
            'williams_r': float(tech.williams_r) if tech.williams_r else 0,
            'roc': float(tech.roc) if tech.roc else 0,
            'cci': float(tech.cci) if tech.cci else 0,
            'volume_sma': float(tech.volume_sma) if tech.volume_sma else 0,
            'news_sentiment_score': float(sent.news_sentiment_score) if sent.news_sentiment_score else 0,
            'short_interest_ratio': float(sent.short_interest_ratio) if sent.short_interest_ratio else 0,
            'sentiment_momentum': float(sent.sentiment_momentum) if sent.sentiment_momentum else 0,
            'sentiment_volatility': float(sent.sentiment_volatility) if sent.sentiment_volatility else 0,
            'sentiment_sma': float(sent.sentiment_sma) if sent.sentiment_sma else 0,
            'sentiment_ema': float(sent.sentiment_ema) if sent.sentiment_ema else 0,
            'sentiment_rsi': float(sent.sentiment_rsi) if sent.sentiment_rsi else 0,
            'sentiment_macd': float(sent.sentiment_macd) if sent.sentiment_macd else 0,
            'news_volume': float(sent.news_volume) if sent.news_volume else 0,
            'sentiment_distribution': float(sent.sentiment_distribution) if sent.sentiment_distribution else 0,
            'composite_sentiment': float(sent.composite_sentiment) if sent.composite_sentiment else 0,
        }
        
        # Création du DataFrame pour la prédiction
        X_pred = pd.DataFrame([features])
        
        # Prédiction
        prediction = model.predict(X_pred, num_iteration=model.best_iteration)
        
        # Interprétation selon le type de modèle
        if model_record.model_type == "lightgbm_binary_classification":
            prediction_value = float(prediction[0])
            prediction_class = "Hausse" if prediction_value > 0.5 else "Baisse"
            confidence = abs(prediction_value - 0.5) * 2  # Confiance entre 0 et 1
            
        elif model_record.model_type == "lightgbm_multiclass_classification":
            prediction_probs = prediction[0]
            prediction_class_idx = np.argmax(prediction_probs)
            prediction_value = float(prediction_probs[prediction_class_idx])
            confidence = float(prediction_value)
            
            class_names = ["Forte baisse", "Baisse", "Stable", "Hausse", "Forte hausse"]
            prediction_class = class_names[prediction_class_idx]
            
        elif model_record.model_type == "lightgbm_regression":
            prediction_value = float(prediction[0])
            prediction_class = "Hausse" if prediction_value > 0 else "Baisse"
            confidence = min(abs(prediction_value) * 10, 1.0)  # Confiance basée sur l'amplitude
            
        else:
            raise ValueError(f"Type de modèle non supporté: {model_record.model_type}")
        
        # Sauvegarde de la prédiction
        prediction_record = MLPredictions(
            model_id=model_id,
            symbol=symbol,
            prediction_date=prediction_date,
            prediction_value=prediction_value,
            prediction_class=prediction_class,
            confidence=confidence,
            data_date_used=data_date_used,
            created_by="lightgbm_service"
        )
        
        db.add(prediction_record)
        db.commit()
        db.refresh(prediction_record)
        
        return {
            "prediction_id": prediction_record.id,
            "model_id": model_id,
            "symbol": symbol,
            "prediction_date": prediction_date,
            "prediction_value": prediction_value,
            "prediction_class": prediction_class,
            "confidence": confidence,
            "data_date_used": data_date_used,
            "model_type": model_record.model_type
        }
