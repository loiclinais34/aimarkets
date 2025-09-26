import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, date
import joblib
import os
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')
# SHAP réactivé pour les explications de modèles
import shap

# Imports pour XGBoost et LightGBM
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("⚠️ XGBoost non disponible")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("⚠️ LightGBM non disponible")

from app.models.database import (
    HistoricalData, TechnicalIndicators, SentimentIndicators, 
    TargetParameters, MLModels, MLPredictions
)
from app.core.config import settings


class MLService:
    def __init__(self, db: Session = None):
        self.db = db
        self.models_path = settings.ml_models_path
        os.makedirs(self.models_path, exist_ok=True)
    
    def create_target_parameter(self, user_id: str, parameter_name: str, 
                              target_return_percentage: float, time_horizon_days: int,
                              risk_tolerance: str = 'medium', min_confidence_threshold: float = 0.7,
                              max_drawdown_percentage: float = 5.0) -> TargetParameters:
        """Créer un nouveau paramètre de cible de rentabilité"""
        target_param = TargetParameters(
            user_id=user_id,
            parameter_name=parameter_name,
            target_return_percentage=target_return_percentage,
            time_horizon_days=time_horizon_days,
            risk_tolerance=risk_tolerance,
            min_confidence_threshold=min_confidence_threshold,
            max_drawdown_percentage=max_drawdown_percentage
        )
        self.db.add(target_param)
        self.db.commit()
        self.db.refresh(target_param)
        return target_param
    
    def get_target_parameters(self, user_id: str) -> List[TargetParameters]:
        """Récupérer les paramètres de cible pour un utilisateur"""
        return self.db.query(TargetParameters).filter(
            TargetParameters.user_id == user_id,
            TargetParameters.is_active == True
        ).all()
    
    def calculate_target_price(self, current_price: float, target_return_percentage: float, 
                             time_horizon_days: int) -> float:
        """Calculer le prix cible basé sur le rendement attendu"""
        # Convertir en float pour éviter les problèmes de type
        current_price = float(current_price)
        target_return_percentage = float(target_return_percentage)
        time_horizon_days = int(time_horizon_days)
        
        # Calcul du rendement quotidien équivalent
        daily_return = (1 + target_return_percentage / 100) ** (1 / time_horizon_days) - 1
        # Calcul du prix cible
        target_price = current_price * (1 + daily_return * time_horizon_days)
        return target_price

    def create_target_labels_with_parameters(self, df: pd.DataFrame, target_return_percentage: float, time_horizon_days: int) -> pd.DataFrame:
        """
        Crée les labels de cible en utilisant les paramètres de rendement et d'horizon temporel.
        
        Args:
            df: DataFrame avec les données historiques
            target_return_percentage: Rendement attendu en pourcentage
            time_horizon_days: Horizon temporel en jours
            
        Returns:
            DataFrame avec les labels de cible ajoutés
        """
        if df.empty:
            return df
        
        # Calculer le prix cible pour chaque jour
        df['target_price'] = df['close'].apply(
            lambda x: self.calculate_target_price(x, target_return_percentage, time_horizon_days)
        )
        
        # Calculer le rendement réel sur l'horizon
        df['future_close'] = df['close'].shift(-time_horizon_days)
        df['actual_return'] = (df['future_close'] - df['close']) / df['close'] * 100
        
        # Créer les labels de classification
        df['target_achieved'] = (df['actual_return'] >= target_return_percentage).astype(int)
        
        # Créer les labels de régression (rendement réel)
        df['target_return'] = df['actual_return']
        
        # Ajouter des features basées sur les paramètres
        df['target_return_percentage'] = target_return_percentage
        df['time_horizon_days'] = time_horizon_days
        
        # Calculer des ratios basés sur les paramètres
        df['return_vs_target'] = df['actual_return'] / target_return_percentage
        df['days_to_target'] = time_horizon_days
        
        return df
    
    def create_labels_for_training(self, symbol: str, target_param: TargetParameters, db: Session = None) -> pd.DataFrame:
        """Créer les labels pour l'entraînement basés sur les paramètres de cible"""
        # Utiliser la session passée en paramètre ou celle de l'instance
        session = db or self.db
        
        # Récupérer le dernier cours connu pour ce symbole
        latest_data = session.query(HistoricalData).filter(
            HistoricalData.symbol == symbol
        ).order_by(HistoricalData.date.desc()).first()
        
        if not latest_data:
            return pd.DataFrame()
        
        latest_price = float(latest_data.close)
        latest_date = latest_data.date
        
        # Calculer le prix cible basé sur le rendement attendu
        target_price = latest_price * (1 + float(target_param.target_return_percentage) / 100)
        
        print(f"🎯 {symbol}: Dernier cours = ${latest_price:.2f}, Prix cible = ${target_price:.2f} (+{target_param.target_return_percentage}%)")
        
        # Récupérer les données historiques avec SQLAlchemy ORM
        historical_data = session.query(HistoricalData).filter(
            HistoricalData.symbol == symbol
        ).order_by(HistoricalData.date).all()
        
        if not historical_data:
            return pd.DataFrame()
        
        # Convertir en DataFrame
        data = []
        for h in historical_data:
            # Récupérer les indicateurs techniques
            tech = session.query(TechnicalIndicators).filter(
                TechnicalIndicators.symbol == symbol,
                TechnicalIndicators.date == h.date
            ).first()
            
            # Récupérer les indicateurs de sentiment
            sent = session.query(SentimentIndicators).filter(
                SentimentIndicators.symbol == symbol,
                SentimentIndicators.date == h.date
            ).first()
            
            # Préparer les données de base
            row_data = {
                'date': h.date,
                'close': float(h.close),
                'volume': h.volume,
                'vwap': float(h.vwap) if h.vwap else None,
            }
            
            # Ajouter tous les indicateurs techniques disponibles
            if tech:
                tech_indicators = {
                    # Moyennes mobiles
                    'sma_5': float(tech.sma_5) if tech.sma_5 else None,
                    'sma_10': float(tech.sma_10) if tech.sma_10 else None,
                    'sma_20': float(tech.sma_20) if tech.sma_20 else None,
                    'sma_50': float(tech.sma_50) if tech.sma_50 else None,
                    'sma_200': float(tech.sma_200) if tech.sma_200 else None,
                    'ema_5': float(tech.ema_5) if tech.ema_5 else None,
                    'ema_10': float(tech.ema_10) if tech.ema_10 else None,
                    'ema_20': float(tech.ema_20) if tech.ema_20 else None,
                    'ema_50': float(tech.ema_50) if tech.ema_50 else None,
                    'ema_200': float(tech.ema_200) if tech.ema_200 else None,
                    
                    # Indicateurs de momentum
                    'rsi_14': float(tech.rsi_14) if tech.rsi_14 else None,
                    'macd': float(tech.macd) if tech.macd else None,
                    'macd_signal': float(tech.macd_signal) if tech.macd_signal else None,
                    'macd_histogram': float(tech.macd_histogram) if tech.macd_histogram else None,
                    'stochastic_k': float(tech.stochastic_k) if tech.stochastic_k else None,
                    'stochastic_d': float(tech.stochastic_d) if tech.stochastic_d else None,
                    'williams_r': float(tech.williams_r) if tech.williams_r else None,
                    'roc': float(tech.roc) if tech.roc else None,
                    'cci': float(tech.cci) if tech.cci else None,
                    
                    # Bollinger Bands
                    'bb_middle': float(tech.bb_middle) if tech.bb_middle else None,
                    'bb_lower': float(tech.bb_lower) if tech.bb_lower else None,
                    'bb_width': float(tech.bb_width) if tech.bb_width else None,
                    'bb_position': float(tech.bb_position) if tech.bb_position else None,
                    
                    # Volume
                    'obv': float(tech.obv) if tech.obv else None,
                    'volume_roc': float(tech.volume_roc) if tech.volume_roc else None,
                    'volume_sma_20': float(tech.volume_sma_20) if tech.volume_sma_20 else None,
                    
                    # ATR
                    'atr_14': float(tech.atr_14) if tech.atr_14 else None,
                }
                row_data.update(tech_indicators)
            
            # Ajouter tous les indicateurs de sentiment disponibles
            if sent:
                sent_indicators = {
                    # Base Sentiment Indicators
                    'sentiment_score_normalized': float(sent.sentiment_score_normalized) if sent.sentiment_score_normalized else None,
                    
                    # Sentiment Momentum
                    'sentiment_momentum_1d': float(sent.sentiment_momentum_1d) if sent.sentiment_momentum_1d else None,
                    'sentiment_momentum_3d': float(sent.sentiment_momentum_3d) if sent.sentiment_momentum_3d else None,
                    'sentiment_momentum_7d': float(sent.sentiment_momentum_7d) if sent.sentiment_momentum_7d else None,
                    'sentiment_momentum_14d': float(sent.sentiment_momentum_14d) if sent.sentiment_momentum_14d else None,
                    
                    # Sentiment Volatility
                    'sentiment_volatility_3d': float(sent.sentiment_volatility_3d) if sent.sentiment_volatility_3d else None,
                    'sentiment_volatility_7d': float(sent.sentiment_volatility_7d) if sent.sentiment_volatility_7d else None,
                    'sentiment_volatility_14d': float(sent.sentiment_volatility_14d) if sent.sentiment_volatility_14d else None,
                    'sentiment_volatility_30d': float(sent.sentiment_volatility_30d) if sent.sentiment_volatility_30d else None,
                    
                    # Sentiment Moving Averages
                    'sentiment_sma_3': float(sent.sentiment_sma_3) if sent.sentiment_sma_3 else None,
                    'sentiment_sma_7': float(sent.sentiment_sma_7) if sent.sentiment_sma_7 else None,
                    'sentiment_sma_14': float(sent.sentiment_sma_14) if sent.sentiment_sma_14 else None,
                    'sentiment_sma_30': float(sent.sentiment_sma_30) if sent.sentiment_sma_30 else None,
                    'sentiment_ema_3': float(sent.sentiment_ema_3) if sent.sentiment_ema_3 else None,
                    'sentiment_ema_7': float(sent.sentiment_ema_7) if sent.sentiment_ema_7 else None,
                    'sentiment_ema_14': float(sent.sentiment_ema_14) if sent.sentiment_ema_14 else None,
                    'sentiment_ema_30': float(sent.sentiment_ema_30) if sent.sentiment_ema_30 else None,
                    
                    # Sentiment Oscillators
                    'sentiment_rsi_14': float(sent.sentiment_rsi_14) if sent.sentiment_rsi_14 else None,
                    'sentiment_macd': float(sent.sentiment_macd) if sent.sentiment_macd else None,
                    'sentiment_macd_signal': float(sent.sentiment_macd_signal) if sent.sentiment_macd_signal else None,
                    'sentiment_macd_histogram': float(sent.sentiment_macd_histogram) if sent.sentiment_macd_histogram else None,
                    
                    # News Volume Indicators
                    'news_volume_sma_7': float(sent.news_volume_sma_7) if sent.news_volume_sma_7 else None,
                    'news_volume_sma_14': float(sent.news_volume_sma_14) if sent.news_volume_sma_14 else None,
                    'news_volume_sma_30': float(sent.news_volume_sma_30) if sent.news_volume_sma_30 else None,
                    'news_volume_roc_7d': float(sent.news_volume_roc_7d) if sent.news_volume_roc_7d else None,
                    'news_volume_roc_14d': float(sent.news_volume_roc_14d) if sent.news_volume_roc_14d else None,
                    
                    # Sentiment Distribution Ratios
                    'news_positive_ratio': float(sent.news_positive_ratio) if sent.news_positive_ratio else None,
                    'news_negative_ratio': float(sent.news_negative_ratio) if sent.news_negative_ratio else None,
                    'news_neutral_ratio': float(sent.news_neutral_ratio) if sent.news_neutral_ratio else None,
                    'news_sentiment_quality': float(sent.news_sentiment_quality) if sent.news_sentiment_quality else None,
                    
                    
                    # Composite Sentiment Indicators
                    'sentiment_strength_index': float(sent.sentiment_strength_index) if sent.sentiment_strength_index else None,
                    'market_sentiment_index': float(sent.market_sentiment_index) if sent.market_sentiment_index else None,
                    'sentiment_divergence': float(sent.sentiment_divergence) if sent.sentiment_divergence else None,
                    'sentiment_acceleration': float(sent.sentiment_acceleration) if sent.sentiment_acceleration else None,
                    'sentiment_trend_strength': float(sent.sentiment_trend_strength) if sent.sentiment_trend_strength else None,
                    'sentiment_quality_index': float(sent.sentiment_quality_index) if sent.sentiment_quality_index else None,
                    'sentiment_risk_score': float(sent.sentiment_risk_score) if sent.sentiment_risk_score else None,
                }
                row_data.update(sent_indicators)
            
            data.append(row_data)
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return pd.DataFrame()
        
        # NOUVELLE LOGIQUE : Utiliser le prix cible calculé à partir du dernier cours
        # Pour chaque ligne, calculer si le prix futur atteint le prix cible
        df['future_close'] = df['close'].shift(-target_param.time_horizon_days)
        df['actual_return'] = (df['future_close'] - df['close']) / df['close'] * 100
        
        # Calculer le prix cible pour chaque jour basé sur le rendement attendu
        df['target_price'] = df['close'] * (1 + float(target_param.target_return_percentage) / 100)
        
        # Créer les labels de classification : le prix futur atteint-il le prix cible ?
        df['target_achieved'] = (df['future_close'] >= df['target_price']).astype(int)
        
        # Créer les labels de régression (rendement réel)
        df['target_return'] = df['actual_return']
        
        # Ajouter des informations de debug
        print(f"📊 {symbol}: {len(df)} échantillons d'entraînement")
        print(f"📊 {symbol}: {df['target_achieved'].sum()} échantillons positifs sur {len(df)} ({df['target_achieved'].mean()*100:.1f}%)")
        
        # Supprimer les lignes avec des valeurs NaN (futures manquantes)
        df = df.dropna(subset=['future_close', 'target_achieved'])
        
        print(f"📊 {symbol}: {len(df)} échantillons valides après nettoyage")
        
        # Remplacer les valeurs NaN par des valeurs par défaut au lieu de supprimer les lignes
        # Pour les features numériques, utiliser la médiane ou 0
        numeric_columns = [
            # Données de base
            'close', 'volume', 'vwap',
            
            # Moyennes mobiles techniques
            'sma_5', 'sma_10', 'sma_20', 'sma_50', 'sma_200',
            'ema_5', 'ema_10', 'ema_20', 'ema_50', 'ema_200',
            
            # Indicateurs de momentum techniques
            'rsi_14', 'macd', 'macd_signal', 'macd_histogram',
            'stochastic_k', 'stochastic_d', 'williams_r', 'roc', 'cci',
            
            # Bollinger Bands
            'bb_middle', 'bb_lower', 'bb_width', 'bb_position',
            
            # Volume techniques
            'obv', 'volume_roc', 'volume_sma_20',
            
            # ATR
            'atr_14',
            
            # Indicateurs de sentiment de base
            'sentiment_score_normalized',
            
            # Sentiment Momentum
            'sentiment_momentum_1d', 'sentiment_momentum_3d', 'sentiment_momentum_7d', 'sentiment_momentum_14d',
            
            # Sentiment Volatility
            'sentiment_volatility_3d', 'sentiment_volatility_7d', 'sentiment_volatility_14d', 'sentiment_volatility_30d',
            
            # Sentiment Moving Averages
            'sentiment_sma_3', 'sentiment_sma_7', 'sentiment_sma_14', 'sentiment_sma_30',
            'sentiment_ema_3', 'sentiment_ema_7', 'sentiment_ema_14', 'sentiment_ema_30',
            
            # Sentiment Oscillators
            'sentiment_rsi_14', 'sentiment_macd', 'sentiment_macd_signal', 'sentiment_macd_histogram',
            
            # News Volume Indicators
            'news_volume_sma_7', 'news_volume_sma_14', 'news_volume_sma_30',
            'news_volume_roc_7d', 'news_volume_roc_14d',
            
            # Sentiment Distribution Ratios
            'news_positive_ratio', 'news_negative_ratio', 'news_neutral_ratio', 'news_sentiment_quality',
            
            # Short Interest Indicators
            
            # Short Volume Indicators
            
            # Composite Sentiment Indicators
            'sentiment_strength_index', 'market_sentiment_index', 'sentiment_divergence',
            'sentiment_acceleration', 'sentiment_trend_strength', 'sentiment_quality_index', 'sentiment_risk_score'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                # Remplacer NaN par la médiane de la colonne, ou 0 si pas de données
                median_val = df[col].median() if not df[col].isna().all() else 0
                df[col] = df[col].fillna(median_val)
        
        # Supprimer seulement les lignes avec des valeurs manquantes critiques
        critical_columns = ['close', 'volume', 'target_price', 'future_close', 'actual_return']
        df = df.dropna(subset=critical_columns)
        
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Préparer les features pour l'entraînement avec toutes les dimensions enrichies"""
        
        # Définir toutes les features disponibles (toutes les colonnes sauf les colonnes de contrôle)
        exclude_columns = ['date', 'target_price', 'future_close', 'actual_return', 'target_achieved', 'target_return']
        feature_columns = [col for col in df.columns if col not in exclude_columns]
        
        # Sélectionner les features disponibles
        available_features = [col for col in feature_columns if col in df.columns]
        
        # Créer des features supplémentaires
        df_features = df[available_features].copy()
        
        # Features de momentum supplémentaires (si pas déjà présentes)
        if 'close' in df.columns:
            if 'price_momentum_5d' not in df_features.columns:
                df_features['price_momentum_5d'] = df['close'].pct_change(5)
            if 'price_momentum_10d' not in df_features.columns:
                df_features['price_momentum_10d'] = df['close'].pct_change(10)
            if 'price_momentum_20d' not in df_features.columns:
                df_features['price_momentum_20d'] = df['close'].pct_change(20)
        
        if 'volume' in df.columns:
            if 'volume_momentum_5d' not in df_features.columns:
                df_features['volume_momentum_5d'] = df['volume'].pct_change(5)
            if 'volume_momentum_10d' not in df_features.columns:
                df_features['volume_momentum_10d'] = df['volume'].pct_change(10)
        
        # Features de volatilité supplémentaires
        if 'close' in df.columns:
            if 'price_volatility_5d' not in df_features.columns:
                df_features['price_volatility_5d'] = df['close'].rolling(5).std()
            if 'price_volatility_10d' not in df_features.columns:
                df_features['price_volatility_10d'] = df['close'].rolling(10).std()
            if 'price_volatility_20d' not in df_features.columns:
                df_features['price_volatility_20d'] = df['close'].rolling(20).std()
        
        # Features de corrélation avancées
        if 'close' in df.columns and 'sentiment_score_normalized' in df.columns:
            if 'price_sentiment_corr' not in df_features.columns:
                df_features['price_sentiment_corr'] = df['close'].rolling(20).corr(df['sentiment_score_normalized'])
        
        if 'volume' in df.columns and 'sentiment_score_normalized' in df.columns:
            if 'volume_sentiment_corr' not in df_features.columns:
                df_features['volume_sentiment_corr'] = df['volume'].rolling(20).corr(df['sentiment_score_normalized'])
        
        # Features de ratio avancées
        if 'close' in df.columns and 'sma_20' in df.columns:
            if 'price_sma_ratio' not in df_features.columns:
                df_features['price_sma_ratio'] = df['close'] / df['sma_20']
        
        if 'close' in df.columns and 'ema_20' in df.columns:
            if 'price_ema_ratio' not in df_features.columns:
                df_features['price_ema_ratio'] = df['close'] / df['ema_20']
        
        # Features de divergence
        if 'rsi_14' in df.columns and 'sentiment_rsi_14' in df.columns:
            if 'rsi_sentiment_divergence' not in df_features.columns:
                df_features['rsi_sentiment_divergence'] = df['rsi_14'] - df['sentiment_rsi_14']
        
        # Features de momentum croisé
        if 'sentiment_momentum_7d' in df.columns and 'sentiment_momentum_14d' in df.columns:
            if 'sentiment_momentum_acceleration' not in df_features.columns:
                df_features['sentiment_momentum_acceleration'] = df['sentiment_momentum_7d'] - df['sentiment_momentum_14d']
        
        # Remplacer les valeurs infinies et NaN
        df_features = df_features.replace([np.inf, -np.inf], np.nan)
        df_features = df_features.fillna(0)
        
        return df_features, df_features.columns.tolist()
    
    def prepare_features_for_prediction(self, df: pd.DataFrame, feature_names: List[str]) -> pd.DataFrame:
        """Préparer les features pour la prédiction en utilisant exactement les mêmes features que l'entraînement"""
        
        # Créer un DataFrame avec toutes les features nécessaires
        df_features = pd.DataFrame(index=df.index)
        
        # Ajouter toutes les features de base disponibles
        for feature in feature_names:
            if feature in df.columns:
                df_features[feature] = df[feature]
            else:
                # Si la feature n'existe pas, la créer avec des valeurs par défaut
                if feature == 'price_momentum_5d' and 'close' in df.columns:
                    df_features[feature] = df['close'].pct_change(5)
                elif feature == 'price_momentum_10d' and 'close' in df.columns:
                    df_features[feature] = df['close'].pct_change(10)
                elif feature == 'price_momentum_20d' and 'close' in df.columns:
                    df_features[feature] = df['close'].pct_change(20)
                elif feature == 'volume_momentum_5d' and 'volume' in df.columns:
                    df_features[feature] = df['volume'].pct_change(5)
                elif feature == 'volume_momentum_10d' and 'volume' in df.columns:
                    df_features[feature] = df['volume'].pct_change(10)
                elif feature == 'price_volatility_5d' and 'close' in df.columns:
                    # Pour la prédiction, utiliser une valeur par défaut basée sur l'historique récent
                    # ou une estimation basée sur la volatilité des autres features
                    if 'atr_14' in df.columns and not pd.isna(df['atr_14'].iloc[0]):
                        df_features[feature] = df['atr_14'] * 0.1  # Estimation basée sur ATR
                    else:
                        df_features[feature] = df['close'].iloc[0] * 0.01  # 1% du prix comme estimation
                elif feature == 'price_volatility_10d' and 'close' in df.columns:
                    if 'atr_14' in df.columns and not pd.isna(df['atr_14'].iloc[0]):
                        df_features[feature] = df['atr_14'] * 0.15  # Estimation basée sur ATR
                    else:
                        df_features[feature] = df['close'].iloc[0] * 0.015  # 1.5% du prix comme estimation
                elif feature == 'price_volatility_20d' and 'close' in df.columns:
                    if 'atr_14' in df.columns and not pd.isna(df['atr_14'].iloc[0]):
                        df_features[feature] = df['atr_14'] * 0.2  # Estimation basée sur ATR
                    else:
                        df_features[feature] = df['close'].iloc[0] * 0.02  # 2% du prix comme estimation
                elif feature == 'price_sentiment_corr' and 'close' in df.columns and 'sentiment_score_normalized' in df.columns:
                    # Pour la corrélation, utiliser une valeur par défaut neutre
                    df_features[feature] = 0.0
                elif feature == 'volume_sentiment_corr' and 'volume' in df.columns and 'sentiment_score_normalized' in df.columns:
                    # Pour la corrélation, utiliser une valeur par défaut neutre
                    df_features[feature] = 0.0
                elif feature == 'price_sma_ratio' and 'close' in df.columns and 'sma_20' in df.columns:
                    df_features[feature] = df['close'] / df['sma_20']
                elif feature == 'price_ema_ratio' and 'close' in df.columns and 'ema_20' in df.columns:
                    df_features[feature] = df['close'] / df['ema_20']
                elif feature == 'rsi_sentiment_divergence' and 'rsi_14' in df.columns and 'sentiment_rsi_14' in df.columns:
                    df_features[feature] = df['rsi_14'] - df['sentiment_rsi_14']
                elif feature == 'sentiment_momentum_acceleration' and 'sentiment_momentum_7d' in df.columns and 'sentiment_momentum_14d' in df.columns:
                    df_features[feature] = df['sentiment_momentum_7d'] - df['sentiment_momentum_14d']
                else:
                    # Feature non reconnue, utiliser 0
                    df_features[feature] = 0
        
        # Remplacer les valeurs infinies et NaN
        df_features = df_features.replace([np.inf, -np.inf], np.nan)
        df_features = df_features.fillna(0)
        
        # S'assurer que l'ordre des colonnes correspond exactement à feature_names
        df_features = df_features[feature_names]
        
        return df_features
    
    def train_classification_model(self, symbol: str, target_param: TargetParameters, db: Session = None, search_id: str = None) -> Dict:
        """Entraîner un modèle de classification pour prédire si la cible sera atteinte"""
        # Utiliser la session passée en paramètre ou celle de l'instance
        session = db or self.db
        
        # Créer les données d'entraînement
        df = self.create_labels_for_training(symbol, target_param, session)
        
        if df.empty or len(df) < 100:
            return {"error": "Pas assez de données pour l'entraînement"}
        
        # Préparer les features
        X, feature_names = self.prepare_features(df)
        y = df['target_achieved']
        
        # Diviser les données
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Normaliser les features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Entraîner le modèle
        model = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )
        model.fit(X_train_scaled, y_train)
        
        # Évaluer le modèle
        y_pred = model.predict(X_test_scaled)
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        # Validation croisée
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='accuracy')
        
        # Générer un nom de modèle unique
        base_name = f"classification_{symbol}_{target_param.parameter_name}"
        model_name = base_name
        
        # Trouver la prochaine version disponible
        version_num = 1
        while True:
            version = f"v{version_num}"
            existing = session.query(MLModels).filter(
                MLModels.model_name == model_name,
                MLModels.model_version == version
            ).first()
            if not existing:
                break
            version_num += 1
        
        # Créer les chemins de fichiers avec la version
        model_path = os.path.join(self.models_path, f"{model_name}_{version}.joblib")
        scaler_path = os.path.join(self.models_path, f"{model_name}_{version}_scaler.joblib")
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        # Enregistrer le modèle en base
        ml_model = MLModels(
            model_name=model_name,
            model_type="classification",
            model_version=version,
            symbol=symbol,
            target_parameter_id=target_param.id,
            search_id=search_id,
            model_parameters={
                "target_return_percentage": float(target_param.target_return_percentage),
                "time_horizon_days": int(target_param.time_horizon_days),
                "risk_tolerance": str(target_param.risk_tolerance),
                "feature_names": feature_names,
                "training_data_start": str(df['date'].min()),
                "training_data_end": str(df['date'].max())
            },
            performance_metrics={
                "validation_score": float(cv_scores.mean()),
                "test_score": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "cv_mean": float(cv_scores.mean()),
                "cv_std": float(cv_scores.std())
            },
            model_path=model_path,
            is_active=True,
            created_by="ml_service"
        )
        session.add(ml_model)
        session.commit()
        
        return {
            "model_id": ml_model.id,
            "model_name": model_name,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "cv_mean": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
            "feature_importance": dict(zip(feature_names, model.feature_importances_))
        }

    def train_multiple_models(self, symbol: str, target_param: TargetParameters, algorithms: List[str] = None, db: Session = None, search_id: str = None) -> Dict:
        """Entraîner plusieurs types de modèles (RandomForest, XGBoost, LightGBM, NeuralNetwork) pour un symbole"""
        if algorithms is None:
            algorithms = ['RandomForest']
            if XGBOOST_AVAILABLE:
                algorithms.append('XGBoost')
            if LIGHTGBM_AVAILABLE:
                algorithms.append('LightGBM')
            algorithms.append('NeuralNetwork')
        
        results = {}
        
        for algorithm in algorithms:
            try:
                print(f"🤖 Entraînement {algorithm} pour {symbol}")
                
                if algorithm == 'RandomForest':
                    result = self.train_classification_model(symbol, target_param, db, search_id)
                elif algorithm == 'XGBoost' and XGBOOST_AVAILABLE:
                    result = self.train_xgboost_model(symbol, target_param, db, search_id)
                elif algorithm == 'LightGBM' and LIGHTGBM_AVAILABLE:
                    result = self.train_lightgbm_model(symbol, target_param, db, search_id)
                elif algorithm == 'NeuralNetwork':
                    result = self.train_neural_network_model(symbol, target_param, db, search_id)
                else:
                    print(f"⚠️ Algorithme {algorithm} non disponible")
                    continue
                
                if "error" not in result:
                    results[algorithm] = result
                    print(f"✅ {algorithm} entraîné avec succès - Accuracy: {result.get('accuracy', 0):.3f}")
                else:
                    print(f"❌ Erreur {algorithm}: {result['error']}")
                    
            except Exception as e:
                print(f"❌ Erreur lors de l'entraînement {algorithm} pour {symbol}: {str(e)}")
                continue
        
        # Filtrer les modèles par performance
        filtered_results = self.filter_models_by_performance(results)
        
        print(f"🎯 {symbol}: {len(filtered_results)}/{len(results)} modèles performants retenus")
        
        return filtered_results

    def filter_models_by_performance(self, results: Dict, min_accuracy: float = 0.55, min_f1_score: float = 0.8) -> Dict:
        """
        Filtre les modèles en fonction de leurs performances.
        
        Args:
            results: Dictionnaire des résultats d'entraînement
            min_accuracy: Précision minimale requise
            min_f1_score: Score F1 minimal requis
            
        Returns:
            Dictionnaire des modèles performants
        """
        filtered_results = {}
        
        for algorithm, result in results.items():
            if "error" in result:
                print(f"❌ {algorithm}: {result['error']}")
                continue
                
            accuracy = result.get('accuracy', 0)
            f1_score = result.get('f1_score', 0)
            
            if accuracy >= min_accuracy and f1_score >= min_f1_score:
                filtered_results[algorithm] = result
                print(f"✅ {algorithm}: Performance validée (Accuracy: {accuracy:.3f}, F1: {f1_score:.3f})")
            else:
                print(f"⚠️ {algorithm}: Performance insuffisante (Accuracy: {accuracy:.3f}, F1: {f1_score:.3f}) - Rejeté")
        
        return filtered_results

    def train_xgboost_model(self, symbol: str, target_param: TargetParameters, db: Session = None, search_id: str = None) -> Dict:
        """Entraîner un modèle XGBoost pour la classification"""
        if not XGBOOST_AVAILABLE:
            return {"error": "XGBoost non disponible"}
        
        # Utiliser la session passée en paramètre ou celle de l'instance
        session = db or self.db
        
        # Créer les données d'entraînement
        df = self.create_labels_for_training(symbol, target_param, session)
        
        if df.empty or len(df) < 100:
            return {"error": "Pas assez de données pour l'entraînement"}
        
        # Préparer les features
        X, feature_names = self.prepare_features(df)
        y = df['target_achieved'].astype(int)
        
        # Diviser les données
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Entraîner le modèle XGBoost
        model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )
        model.fit(X_train, y_train)
        
        # Évaluer le modèle
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        # Validation croisée
        cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
        
        # Sauvegarder le modèle
        model_name = f"classification_{symbol}_target_{symbol}_{float(target_param.target_return_percentage)}%_{target_param.time_horizon_days}d_xgboost"
        model_path = os.path.join(self.models_path, f"{model_name}.joblib")
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(model, model_path)
        
        # Sauvegarder le scaler
        scaler_path = model_path.replace('.joblib', '_scaler.joblib')
        scaler = StandardScaler()
        scaler.fit(X)
        joblib.dump(scaler, scaler_path)
        
        # Créer l'enregistrement en base
        ml_model = MLModels(
            model_name=model_name,
            model_type="classification",
            model_version="v1",
            symbol=symbol,
            target_parameter_id=target_param.id,
            search_id=search_id,
            model_parameters={
                "algorithm": "XGBoost",
                "target_return_percentage": str(target_param.target_return_percentage),
                "time_horizon_days": str(target_param.time_horizon_days),
                "risk_tolerance": str(target_param.risk_tolerance),
                "feature_names": feature_names,
                "training_data_start": str(df['date'].min()),
                "training_data_end": str(df['date'].max())
            },
            performance_metrics={
                "validation_score": float(cv_scores.mean()),
                "test_score": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "cv_mean": float(cv_scores.mean()),
                "cv_std": float(cv_scores.std())
            },
            model_path=model_path,
            is_active=True,
            created_by="ml_service"
        )
        session.add(ml_model)
        session.commit()
        
        return {
            "model_id": ml_model.id,
            "model_name": model_name,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "cv_mean": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
            "feature_importance": dict(zip(feature_names, model.feature_importances_))
        }

    def train_lightgbm_model(self, symbol: str, target_param: TargetParameters, db: Session = None, search_id: str = None) -> Dict:
        """Entraîner un modèle LightGBM pour la classification"""
        if not LIGHTGBM_AVAILABLE:
            return {"error": "LightGBM non disponible"}
        
        # Utiliser la session passée en paramètre ou celle de l'instance
        session = db or self.db
        
        # Créer les données d'entraînement
        df = self.create_labels_for_training(symbol, target_param, session)
        
        if df.empty or len(df) < 100:
            return {"error": "Pas assez de données pour l'entraînement"}
        
        # Préparer les features
        X, feature_names = self.prepare_features(df)
        y = df['target_achieved'].astype(int)
        
        # Diviser les données
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Entraîner le modèle LightGBM
        model = lgb.LGBMClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.08,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1
        )
        model.fit(X_train, y_train)
        
        # Évaluer le modèle
        y_pred = model.predict(X_test)
        y_pred_proba = model.predict_proba(X_test)[:, 1]
        
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred)
        recall = recall_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        # Validation croisée
        cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
        
        # Sauvegarder le modèle
        model_name = f"classification_{symbol}_target_{symbol}_{float(target_param.target_return_percentage)}%_{target_param.time_horizon_days}d_lightgbm"
        model_path = os.path.join(self.models_path, f"{model_name}.joblib")
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(model, model_path)
        
        # Sauvegarder le scaler
        scaler_path = model_path.replace('.joblib', '_scaler.joblib')
        scaler = StandardScaler()
        scaler.fit(X)
        joblib.dump(scaler, scaler_path)
        
        # Créer l'enregistrement en base
        ml_model = MLModels(
            model_name=model_name,
            model_type="classification",
            model_version="v1",
            symbol=symbol,
            target_parameter_id=target_param.id,
            search_id=search_id,
            model_parameters={
                "algorithm": "LightGBM",
                "target_return_percentage": str(target_param.target_return_percentage),
                "time_horizon_days": str(target_param.time_horizon_days),
                "risk_tolerance": str(target_param.risk_tolerance),
                "feature_names": feature_names,
                "training_data_start": str(df['date'].min()),
                "training_data_end": str(df['date'].max())
            },
            performance_metrics={
                "validation_score": float(cv_scores.mean()),
                "test_score": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "cv_mean": float(cv_scores.mean()),
                "cv_std": float(cv_scores.std())
            },
            model_path=model_path,
            is_active=True,
            created_by="ml_service"
        )
        session.add(ml_model)
        session.commit()
        
        return {
            "model_id": ml_model.id,
            "model_name": model_name,
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "cv_mean": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
            "feature_importance": dict(zip(feature_names, model.feature_importances_))
        }
    
    def train_regression_model(self, symbol: str, target_param: TargetParameters, db: Session = None) -> Dict:
        """Entraîner un modèle de régression pour prédire le rendement exact"""
        # Utiliser la session passée en paramètre ou celle de l'instance
        session = db or self.db
        
        # Créer les données d'entraînement
        df = self.create_labels_for_training(symbol, target_param, session)
        
        if df.empty or len(df) < 100:
            return {"error": "Pas assez de données pour l'entraînement"}
        
        # Préparer les features
        X, feature_names = self.prepare_features(df)
        y = df['target_return']
        
        # Diviser les données
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Normaliser les features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Entraîner le modèle
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        model.fit(X_train_scaled, y_train)
        
        # Évaluer le modèle
        y_pred = model.predict(X_test_scaled)
        
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        r2 = r2_score(y_test, y_pred)
        
        # Validation croisée
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
        
        # Générer un nom de modèle unique
        base_name = f"regression_{symbol}_{target_param.parameter_name}"
        model_name = base_name
        
        # Trouver la prochaine version disponible
        version_num = 1
        while True:
            version = f"v{version_num}"
            existing = session.query(MLModels).filter(
                MLModels.model_name == model_name,
                MLModels.model_version == version
            ).first()
            if not existing:
                break
            version_num += 1
        
        # Créer les chemins de fichiers avec la version
        model_path = os.path.join(self.models_path, f"{model_name}_{version}.joblib")
        scaler_path = os.path.join(self.models_path, f"{model_name}_{version}_scaler.joblib")
        
        joblib.dump(model, model_path)
        joblib.dump(scaler, scaler_path)
        
        # Enregistrer le modèle en base
        ml_model = MLModels(
            model_name=model_name,
            model_type="regression",
            model_version=version,
            symbol=symbol,
            target_parameter_id=target_param.id,
            search_id=search_id,
            model_parameters={
                "target_return_percentage": float(target_param.target_return_percentage),
                "time_horizon_days": int(target_param.time_horizon_days),
                "risk_tolerance": str(target_param.risk_tolerance),
                "feature_names": feature_names,
                "training_data_start": str(df['date'].min()),
                "training_data_end": str(df['date'].max())
            },
            performance_metrics={
                "validation_score": float(cv_scores.mean()),
                "test_score": r2,
                "r2_score": r2,
                "mse": mse,
                "rmse": rmse,
                "cv_mean": float(cv_scores.mean()),
                "cv_std": float(cv_scores.std())
            },
            model_path=model_path,
            is_active=True,
            created_by="ml_service"
        )
        session.add(ml_model)
        session.commit()
        
        return {
            "model_id": ml_model.id,
            "model_name": model_name,
            "mse": mse,
            "rmse": rmse,
            "r2_score": r2,
            "cv_mean": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
            "feature_importance": dict(zip(feature_names, model.feature_importances_))
        }
    
    def predict(self, symbol: str, model_id: int, date: datetime, db: Session = None, screener_run_id: int = None) -> Dict:
        """Faire une prédiction avec un modèle entraîné"""
        # Utiliser la session passée en paramètre ou celle de l'instance
        session = db or self.db
        
        # Récupérer le modèle
        ml_model = session.query(MLModels).filter(MLModels.id == model_id).first()
        if not ml_model:
            return {"error": "Modèle non trouvé"}
        
        # Vérifier que le chemin du modèle existe
        if not ml_model.model_path:
            return {"error": "Chemin du modèle non défini"}
        
        # Charger le modèle et le scaler
        try:
            model = joblib.load(ml_model.model_path)
            scaler_path = ml_model.model_path.replace('.joblib', '_scaler.joblib')
            scaler = joblib.load(scaler_path)
        except FileNotFoundError:
            return {"error": f"Fichier modèle non trouvé: {ml_model.model_path}"}
        except Exception as e:
            return {"error": f"Erreur lors du chargement du modèle: {str(e)}"}
        
        # Récupérer les données du jour avec SQLAlchemy ORM
        # D'abord essayer la date exacte
        historical_data = session.query(HistoricalData).filter(
            HistoricalData.symbol == symbol,
            HistoricalData.date == date
        ).first()
        
        # Si pas de données pour cette date, prendre la plus récente disponible
        if not historical_data:
            historical_data = session.query(HistoricalData).filter(
                HistoricalData.symbol == symbol
            ).order_by(HistoricalData.date.desc()).first()
            
            if not historical_data:
                return {"error": "Aucune donnée historique trouvée pour ce symbole"}
            
            # Utiliser la date la plus récente trouvée
            date = historical_data.date
        
        # Récupérer les indicateurs techniques
        tech = session.query(TechnicalIndicators).filter(
            TechnicalIndicators.symbol == symbol,
            TechnicalIndicators.date == date
        ).first()
        
        # Récupérer les indicateurs de sentiment
        sent = session.query(SentimentIndicators).filter(
            SentimentIndicators.symbol == symbol,
            SentimentIndicators.date == date
        ).first()
        
        # Créer le DataFrame avec toutes les dimensions enrichies
        row_data = {
            'close': float(historical_data.close),
            'volume': historical_data.volume,
            'vwap': float(historical_data.vwap) if historical_data.vwap else None,
        }
        
        # Ajouter tous les indicateurs techniques disponibles
        if tech:
            tech_indicators = {
                # Moyennes mobiles
                'sma_5': float(tech.sma_5) if tech.sma_5 else None,
                'sma_10': float(tech.sma_10) if tech.sma_10 else None,
                'sma_20': float(tech.sma_20) if tech.sma_20 else None,
                'sma_50': float(tech.sma_50) if tech.sma_50 else None,
                'sma_200': float(tech.sma_200) if tech.sma_200 else None,
                'ema_5': float(tech.ema_5) if tech.ema_5 else None,
                'ema_10': float(tech.ema_10) if tech.ema_10 else None,
                'ema_20': float(tech.ema_20) if tech.ema_20 else None,
                'ema_50': float(tech.ema_50) if tech.ema_50 else None,
                'ema_200': float(tech.ema_200) if tech.ema_200 else None,
                
                # Indicateurs de momentum
                'rsi_14': float(tech.rsi_14) if tech.rsi_14 else None,
                'macd': float(tech.macd) if tech.macd else None,
                'macd_signal': float(tech.macd_signal) if tech.macd_signal else None,
                'macd_histogram': float(tech.macd_histogram) if tech.macd_histogram else None,
                'stochastic_k': float(tech.stochastic_k) if tech.stochastic_k else None,
                'stochastic_d': float(tech.stochastic_d) if tech.stochastic_d else None,
                'williams_r': float(tech.williams_r) if tech.williams_r else None,
                'roc': float(tech.roc) if tech.roc else None,
                'cci': float(tech.cci) if tech.cci else None,
                
                # Bollinger Bands
                'bb_middle': float(tech.bb_middle) if tech.bb_middle else None,
                'bb_lower': float(tech.bb_lower) if tech.bb_lower else None,
                'bb_width': float(tech.bb_width) if tech.bb_width else None,
                'bb_position': float(tech.bb_position) if tech.bb_position else None,
                
                # Volume
                'obv': float(tech.obv) if tech.obv else None,
                'volume_roc': float(tech.volume_roc) if tech.volume_roc else None,
                'volume_sma_20': float(tech.volume_sma_20) if tech.volume_sma_20 else None,
                
                # ATR
                'atr_14': float(tech.atr_14) if tech.atr_14 else None,
            }
            row_data.update(tech_indicators)
        
        # Ajouter tous les indicateurs de sentiment disponibles
        if sent:
            sent_indicators = {
                # Base Sentiment Indicators
                'sentiment_score_normalized': float(sent.sentiment_score_normalized) if sent.sentiment_score_normalized else None,
                
                # Sentiment Momentum
                'sentiment_momentum_1d': float(sent.sentiment_momentum_1d) if sent.sentiment_momentum_1d else None,
                'sentiment_momentum_3d': float(sent.sentiment_momentum_3d) if sent.sentiment_momentum_3d else None,
                'sentiment_momentum_7d': float(sent.sentiment_momentum_7d) if sent.sentiment_momentum_7d else None,
                'sentiment_momentum_14d': float(sent.sentiment_momentum_14d) if sent.sentiment_momentum_14d else None,
                
                # Sentiment Volatility
                'sentiment_volatility_3d': float(sent.sentiment_volatility_3d) if sent.sentiment_volatility_3d else None,
                'sentiment_volatility_7d': float(sent.sentiment_volatility_7d) if sent.sentiment_volatility_7d else None,
                'sentiment_volatility_14d': float(sent.sentiment_volatility_14d) if sent.sentiment_volatility_14d else None,
                'sentiment_volatility_30d': float(sent.sentiment_volatility_30d) if sent.sentiment_volatility_30d else None,
                
                # Sentiment Moving Averages
                'sentiment_sma_3': float(sent.sentiment_sma_3) if sent.sentiment_sma_3 else None,
                'sentiment_sma_7': float(sent.sentiment_sma_7) if sent.sentiment_sma_7 else None,
                'sentiment_sma_14': float(sent.sentiment_sma_14) if sent.sentiment_sma_14 else None,
                'sentiment_sma_30': float(sent.sentiment_sma_30) if sent.sentiment_sma_30 else None,
                'sentiment_ema_3': float(sent.sentiment_ema_3) if sent.sentiment_ema_3 else None,
                'sentiment_ema_7': float(sent.sentiment_ema_7) if sent.sentiment_ema_7 else None,
                'sentiment_ema_14': float(sent.sentiment_ema_14) if sent.sentiment_ema_14 else None,
                'sentiment_ema_30': float(sent.sentiment_ema_30) if sent.sentiment_ema_30 else None,
                
                # Sentiment Oscillators
                'sentiment_rsi_14': float(sent.sentiment_rsi_14) if sent.sentiment_rsi_14 else None,
                'sentiment_macd': float(sent.sentiment_macd) if sent.sentiment_macd else None,
                'sentiment_macd_signal': float(sent.sentiment_macd_signal) if sent.sentiment_macd_signal else None,
                'sentiment_macd_histogram': float(sent.sentiment_macd_histogram) if sent.sentiment_macd_histogram else None,
                
                # News Volume Indicators
                'news_volume_sma_7': float(sent.news_volume_sma_7) if sent.news_volume_sma_7 else None,
                'news_volume_sma_14': float(sent.news_volume_sma_14) if sent.news_volume_sma_14 else None,
                'news_volume_sma_30': float(sent.news_volume_sma_30) if sent.news_volume_sma_30 else None,
                'news_volume_roc_7d': float(sent.news_volume_roc_7d) if sent.news_volume_roc_7d else None,
                'news_volume_roc_14d': float(sent.news_volume_roc_14d) if sent.news_volume_roc_14d else None,
                
                # Sentiment Distribution Ratios
                'news_positive_ratio': float(sent.news_positive_ratio) if sent.news_positive_ratio else None,
                'news_negative_ratio': float(sent.news_negative_ratio) if sent.news_negative_ratio else None,
                'news_neutral_ratio': float(sent.news_neutral_ratio) if sent.news_neutral_ratio else None,
                'news_sentiment_quality': float(sent.news_sentiment_quality) if sent.news_sentiment_quality else None,
                
                # Short Interest Indicators
                
                # Short Volume Indicators
                
                # Composite Sentiment Indicators
                'sentiment_strength_index': float(sent.sentiment_strength_index) if sent.sentiment_strength_index else None,
                'market_sentiment_index': float(sent.market_sentiment_index) if sent.market_sentiment_index else None,
                'sentiment_divergence': float(sent.sentiment_divergence) if sent.sentiment_divergence else None,
                'sentiment_acceleration': float(sent.sentiment_acceleration) if sent.sentiment_acceleration else None,
                'sentiment_trend_strength': float(sent.sentiment_trend_strength) if sent.sentiment_trend_strength else None,
                'sentiment_quality_index': float(sent.sentiment_quality_index) if sent.sentiment_quality_index else None,
                'sentiment_risk_score': float(sent.sentiment_risk_score) if sent.sentiment_risk_score else None,
            }
            row_data.update(sent_indicators)
        
        data = [row_data]
        
        df = pd.DataFrame(data)
        
        if df.empty:
            return {"error": "Données non trouvées pour cette date"}
        
        # Récupérer les noms des features utilisées lors de l'entraînement
        feature_names = ml_model.model_parameters.get('feature_names', [])
        if not feature_names:
            return {"error": "Noms des features non trouvés dans le modèle"}
        
        # Préparer les features en utilisant exactement les mêmes features que l'entraînement
        X = self.prepare_features_for_prediction(df, feature_names)
        
        # Normaliser et prédire
        X_scaled = scaler.transform(X)
        
        if ml_model.model_type == "classification":
            prediction = model.predict(X_scaled)[0]
            confidence = model.predict_proba(X_scaled)[0].max()
            prediction_type = "target_achieved"
        else:  # regression
            prediction = model.predict(X_scaled)[0]
            confidence = 0.8  # Placeholder pour la régression
            prediction_type = "target_return"
        
        # Enregistrer la prédiction
        ml_prediction = MLPredictions(
            symbol=symbol,
            prediction_date=date,
            model_id=model_id,
            prediction_class=prediction_type,
            prediction_value=float(prediction),
            confidence=float(confidence),
            data_date_used=date,
            screener_run_id=screener_run_id,
            created_by="ml_service"
        )
        session.add(ml_prediction)
        session.commit()
        
        return {
            "symbol": symbol,
            "date": date,
            "prediction": float(prediction),
            "confidence": float(confidence),
            "prediction_type": prediction_type,
            "model_name": ml_model.model_name,
            "data_date_used": date  # Indiquer la date réellement utilisée
        }
    
    def get_model_performance(self, model_id: int) -> Dict:
        """Récupérer les performances d'un modèle"""
        ml_model = self.db.query(MLModels).filter(MLModels.id == model_id).first()
        if not ml_model:
            return {"error": "Modèle non trouvé"}
        
        # Récupérer les prédictions récentes
        recent_predictions = self.db.query(MLPredictions).filter(
            MLPredictions.model_id == model_id
        ).order_by(MLPredictions.prediction_date.desc()).limit(100).all()
        
        return {
            "model_id": ml_model.id,
            "model_name": ml_model.model_name,
            "model_type": ml_model.model_type,
            "validation_score": float(ml_model.validation_score) if ml_model.validation_score else None,
            "test_score": float(ml_model.test_score) if ml_model.test_score else None,
            "training_period": {
                "start": ml_model.training_data_start.isoformat() if ml_model.training_data_start else None,
                "end": ml_model.training_data_end.isoformat() if ml_model.training_data_end else None
            },
            "recent_predictions_count": len(recent_predictions),
            "is_active": ml_model.is_active
        }
    
    def calculate_shap_explanations(self, model_id: int, symbol: str, prediction_date: date, db: Session = None) -> Dict:
        """Calculer les explications SHAP pour une prédiction"""
        # Utiliser la session passée en paramètre ou celle de l'instance
        session = db or self.db
        
        # Récupérer le modèle
        ml_model = session.query(MLModels).filter(MLModels.id == model_id).first()
        if not ml_model:
            return {"error": "Modèle non trouvé"}
        
        # Charger le modèle et le scaler
        model = joblib.load(ml_model.model_path)
        scaler_path = ml_model.model_path.replace('.joblib', '_scaler.joblib')
        scaler = joblib.load(scaler_path)
        
        # Récupérer les données du jour
        historical_data = session.query(HistoricalData).filter(
            HistoricalData.symbol == symbol,
            HistoricalData.date == prediction_date
        ).first()
        
        if not historical_data:
            # Prendre la plus récente disponible
            historical_data = session.query(HistoricalData).filter(
                HistoricalData.symbol == symbol
            ).order_by(HistoricalData.date.desc()).first()
            
            if not historical_data:
                return {"error": "Aucune donnée historique trouvée pour ce symbole"}
        
        # Récupérer les indicateurs techniques et de sentiment
        tech = session.query(TechnicalIndicators).filter(
            TechnicalIndicators.symbol == symbol,
            TechnicalIndicators.date == historical_data.date
        ).first()
        
        sent = session.query(SentimentIndicators).filter(
            SentimentIndicators.symbol == symbol,
            SentimentIndicators.date == historical_data.date
        ).first()
        
        # Créer le DataFrame avec toutes les dimensions enrichies
        row_data = {
            'close': float(historical_data.close),
            'volume': historical_data.volume,
            'vwap': float(historical_data.vwap) if historical_data.vwap else None,
        }
        
        # Ajouter tous les indicateurs techniques disponibles
        if tech:
            tech_indicators = {
                # Moyennes mobiles
                'sma_5': float(tech.sma_5) if tech.sma_5 else None,
                'sma_10': float(tech.sma_10) if tech.sma_10 else None,
                'sma_20': float(tech.sma_20) if tech.sma_20 else None,
                'sma_50': float(tech.sma_50) if tech.sma_50 else None,
                'sma_200': float(tech.sma_200) if tech.sma_200 else None,
                'ema_5': float(tech.ema_5) if tech.ema_5 else None,
                'ema_10': float(tech.ema_10) if tech.ema_10 else None,
                'ema_20': float(tech.ema_20) if tech.ema_20 else None,
                'ema_50': float(tech.ema_50) if tech.ema_50 else None,
                'ema_200': float(tech.ema_200) if tech.ema_200 else None,
                
                # Indicateurs de momentum
                'rsi_14': float(tech.rsi_14) if tech.rsi_14 else None,
                'macd': float(tech.macd) if tech.macd else None,
                'macd_signal': float(tech.macd_signal) if tech.macd_signal else None,
                'macd_histogram': float(tech.macd_histogram) if tech.macd_histogram else None,
                'stochastic_k': float(tech.stochastic_k) if tech.stochastic_k else None,
                'stochastic_d': float(tech.stochastic_d) if tech.stochastic_d else None,
                'williams_r': float(tech.williams_r) if tech.williams_r else None,
                'roc': float(tech.roc) if tech.roc else None,
                'cci': float(tech.cci) if tech.cci else None,
                
                # Bollinger Bands
                'bb_middle': float(tech.bb_middle) if tech.bb_middle else None,
                'bb_lower': float(tech.bb_lower) if tech.bb_lower else None,
                'bb_width': float(tech.bb_width) if tech.bb_width else None,
                'bb_position': float(tech.bb_position) if tech.bb_position else None,
                
                # Volume
                'obv': float(tech.obv) if tech.obv else None,
                'volume_roc': float(tech.volume_roc) if tech.volume_roc else None,
                'volume_sma_20': float(tech.volume_sma_20) if tech.volume_sma_20 else None,
                
                # ATR
                'atr_14': float(tech.atr_14) if tech.atr_14 else None,
            }
            row_data.update(tech_indicators)
        
        # Ajouter tous les indicateurs de sentiment disponibles
        if sent:
            sent_indicators = {
                # Base Sentiment Indicators
                'sentiment_score_normalized': float(sent.sentiment_score_normalized) if sent.sentiment_score_normalized else None,
                
                # Sentiment Momentum
                'sentiment_momentum_1d': float(sent.sentiment_momentum_1d) if sent.sentiment_momentum_1d else None,
                'sentiment_momentum_3d': float(sent.sentiment_momentum_3d) if sent.sentiment_momentum_3d else None,
                'sentiment_momentum_7d': float(sent.sentiment_momentum_7d) if sent.sentiment_momentum_7d else None,
                'sentiment_momentum_14d': float(sent.sentiment_momentum_14d) if sent.sentiment_momentum_14d else None,
                
                # Sentiment Volatility
                'sentiment_volatility_3d': float(sent.sentiment_volatility_3d) if sent.sentiment_volatility_3d else None,
                'sentiment_volatility_7d': float(sent.sentiment_volatility_7d) if sent.sentiment_volatility_7d else None,
                'sentiment_volatility_14d': float(sent.sentiment_volatility_14d) if sent.sentiment_volatility_14d else None,
                'sentiment_volatility_30d': float(sent.sentiment_volatility_30d) if sent.sentiment_volatility_30d else None,
                
                # Sentiment Moving Averages
                'sentiment_sma_3': float(sent.sentiment_sma_3) if sent.sentiment_sma_3 else None,
                'sentiment_sma_7': float(sent.sentiment_sma_7) if sent.sentiment_sma_7 else None,
                'sentiment_sma_14': float(sent.sentiment_sma_14) if sent.sentiment_sma_14 else None,
                'sentiment_sma_30': float(sent.sentiment_sma_30) if sent.sentiment_sma_30 else None,
                'sentiment_ema_3': float(sent.sentiment_ema_3) if sent.sentiment_ema_3 else None,
                'sentiment_ema_7': float(sent.sentiment_ema_7) if sent.sentiment_ema_7 else None,
                'sentiment_ema_14': float(sent.sentiment_ema_14) if sent.sentiment_ema_14 else None,
                'sentiment_ema_30': float(sent.sentiment_ema_30) if sent.sentiment_ema_30 else None,
                
                # Sentiment Oscillators
                'sentiment_rsi_14': float(sent.sentiment_rsi_14) if sent.sentiment_rsi_14 else None,
                'sentiment_macd': float(sent.sentiment_macd) if sent.sentiment_macd else None,
                'sentiment_macd_signal': float(sent.sentiment_macd_signal) if sent.sentiment_macd_signal else None,
                'sentiment_macd_histogram': float(sent.sentiment_macd_histogram) if sent.sentiment_macd_histogram else None,
                
                # News Volume Indicators
                'news_volume_sma_7': float(sent.news_volume_sma_7) if sent.news_volume_sma_7 else None,
                'news_volume_sma_14': float(sent.news_volume_sma_14) if sent.news_volume_sma_14 else None,
                'news_volume_sma_30': float(sent.news_volume_sma_30) if sent.news_volume_sma_30 else None,
                'news_volume_roc_7d': float(sent.news_volume_roc_7d) if sent.news_volume_roc_7d else None,
                'news_volume_roc_14d': float(sent.news_volume_roc_14d) if sent.news_volume_roc_14d else None,
                
                # Sentiment Distribution Ratios
                'news_positive_ratio': float(sent.news_positive_ratio) if sent.news_positive_ratio else None,
                'news_negative_ratio': float(sent.news_negative_ratio) if sent.news_negative_ratio else None,
                'news_neutral_ratio': float(sent.news_neutral_ratio) if sent.news_neutral_ratio else None,
                'news_sentiment_quality': float(sent.news_sentiment_quality) if sent.news_sentiment_quality else None,
                
                # Short Interest Indicators
                
                # Short Volume Indicators
                
                # Composite Sentiment Indicators
                'sentiment_strength_index': float(sent.sentiment_strength_index) if sent.sentiment_strength_index else None,
                'market_sentiment_index': float(sent.market_sentiment_index) if sent.market_sentiment_index else None,
                'sentiment_divergence': float(sent.sentiment_divergence) if sent.sentiment_divergence else None,
                'sentiment_acceleration': float(sent.sentiment_acceleration) if sent.sentiment_acceleration else None,
                'sentiment_trend_strength': float(sent.sentiment_trend_strength) if sent.sentiment_trend_strength else None,
                'sentiment_quality_index': float(sent.sentiment_quality_index) if sent.sentiment_quality_index else None,
                'sentiment_risk_score': float(sent.sentiment_risk_score) if sent.sentiment_risk_score else None,
            }
            row_data.update(sent_indicators)
        
        data = [row_data]
        
        df = pd.DataFrame(data)
        
        # Remplacer les valeurs NaN avec toutes les colonnes enrichies
        numeric_columns = [
            # Données de base
            'close', 'volume', 'vwap',
            
            # Moyennes mobiles techniques
            'sma_5', 'sma_10', 'sma_20', 'sma_50', 'sma_200',
            'ema_5', 'ema_10', 'ema_20', 'ema_50', 'ema_200',
            
            # Indicateurs de momentum techniques
            'rsi_14', 'macd', 'macd_signal', 'macd_histogram',
            'stochastic_k', 'stochastic_d', 'williams_r', 'roc', 'cci',
            
            # Bollinger Bands
            'bb_middle', 'bb_lower', 'bb_width', 'bb_position',
            
            # Volume techniques
            'obv', 'volume_roc', 'volume_sma_20',
            
            # ATR
            'atr_14',
            
            # Indicateurs de sentiment de base
            'sentiment_score_normalized',
            
            # Sentiment Momentum
            'sentiment_momentum_1d', 'sentiment_momentum_3d', 'sentiment_momentum_7d', 'sentiment_momentum_14d',
            
            # Sentiment Volatility
            'sentiment_volatility_3d', 'sentiment_volatility_7d', 'sentiment_volatility_14d', 'sentiment_volatility_30d',
            
            # Sentiment Moving Averages
            'sentiment_sma_3', 'sentiment_sma_7', 'sentiment_sma_14', 'sentiment_sma_30',
            'sentiment_ema_3', 'sentiment_ema_7', 'sentiment_ema_14', 'sentiment_ema_30',
            
            # Sentiment Oscillators
            'sentiment_rsi_14', 'sentiment_macd', 'sentiment_macd_signal', 'sentiment_macd_histogram',
            
            # News Volume Indicators
            'news_volume_sma_7', 'news_volume_sma_14', 'news_volume_sma_30',
            'news_volume_roc_7d', 'news_volume_roc_14d',
            
            # Sentiment Distribution Ratios
            'news_positive_ratio', 'news_negative_ratio', 'news_neutral_ratio', 'news_sentiment_quality',
            
            # Short Interest Indicators
            
            # Short Volume Indicators
            
            # Composite Sentiment Indicators
            'sentiment_strength_index', 'market_sentiment_index', 'sentiment_divergence',
            'sentiment_acceleration', 'sentiment_trend_strength', 'sentiment_quality_index', 'sentiment_risk_score'
        ]
        
        for col in numeric_columns:
            if col in df.columns:
                median_val = df[col].median() if not df[col].isna().all() else 0
                df[col] = df[col].fillna(median_val)
        
        # Récupérer les noms des features utilisées lors de l'entraînement
        feature_names = ml_model.model_parameters.get('feature_names', [])
        if not feature_names:
            return {"error": "Noms des features non trouvés dans le modèle"}
        
        # Utiliser la méthode prepare_features_for_prediction pour garantir la cohérence
        X = self.prepare_features_for_prediction(df, feature_names)
        
        # Normaliser
        X_scaled = scaler.transform(X)
        feature_names = list(X.columns)
        
        # Calculer les explications SHAP
        try:
            # Créer un explainer SHAP pour Random Forest
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_scaled)
            
            # Gestion spécifique pour la classification et la régression
            prediction = model.predict(X_scaled)[0]
            
            if ml_model.model_type == "classification":
                # Pour la classification binaire, toujours prendre la classe positive (1)
                if isinstance(shap_values, list) and len(shap_values) == 2:
                    shap_values = shap_values[1]  # Classe positive
                elif isinstance(shap_values, list):
                    shap_values = shap_values[int(prediction)]
                
                # S'assurer que shap_values est un array 1D
                if hasattr(shap_values, 'shape') and len(shap_values.shape) > 1:
                    shap_values = shap_values.flatten()
                    
                base_value = explainer.expected_value[1] if isinstance(explainer.expected_value, (list, np.ndarray)) and len(explainer.expected_value) > 1 else explainer.expected_value
            else:
                # Régression
                if isinstance(shap_values, list):
                    shap_values = shap_values[0]
                
                # S'assurer que shap_values est un array 1D
                if hasattr(shap_values, 'shape') and len(shap_values.shape) > 1:
                    shap_values = shap_values.flatten()
                    
                base_value = explainer.expected_value
            
            # Créer les explications
            explanations = []
            for i, feature in enumerate(feature_names):
                explanations.append({
                    "feature": feature,
                    "shap_value": float(shap_values[i]),
                    "feature_value": float(X.iloc[0, i]),
                    "impact": "positive" if shap_values[i] > 0 else "negative"
                })
            
            # Trier par importance (valeur absolue de SHAP) puis par sens (positif d'abord, négatif ensuite)
            explanations.sort(key=lambda x: (-abs(x["shap_value"]), x["shap_value"] < 0))
            
            return {
                "model_id": model_id,
                "model_name": ml_model.model_name,
                "model_type": ml_model.model_type,
                "symbol": symbol,
                "prediction_date": historical_data.date,
                "prediction": float(model.predict(X_scaled)[0]),
                "shap_explanations": explanations,
                "base_value": float(base_value) if hasattr(base_value, '__float__') else 0.0
            }
            
        except Exception as e:
            return {"error": f"Erreur lors du calcul SHAP: {str(e)}"}
    
    def get_model_feature_importance(self, model_id: int, db: Session = None) -> Dict:
        """Récupérer l'importance des features d'un modèle"""
        # Utiliser la session passée en paramètre ou celle de l'instance
        session = db or self.db
        
        # Récupérer le modèle
        ml_model = session.query(MLModels).filter(MLModels.id == model_id).first()
        if not ml_model:
            return {"error": "Modèle non trouvé"}
        
        # Charger le modèle
        model = joblib.load(ml_model.model_path)
        
        # Récupérer les feature importances
        if hasattr(model, 'feature_importances_'):
            feature_names = ml_model.model_parameters.get("feature_names", [])
            importances = model.feature_importances_
            
            # Créer la liste des importances
            importance_list = []
            for i, feature in enumerate(feature_names):
                if i < len(importances):
                    importance_list.append({
                        "feature": feature,
                        "importance": float(importances[i])
                    })
            
            # Trier par importance
            importance_list.sort(key=lambda x: x["importance"], reverse=True)
            
            return {
                "model_id": model_id,
                "model_name": ml_model.model_name,
                "model_type": ml_model.model_type,
                "feature_importances": importance_list
            }
        else:
            return {"error": "Ce type de modèle ne supporte pas l'importance des features"}

    def train_neural_network_model(self, symbol: str, target_param: TargetParameters, db: Session = None, search_id: str = None) -> Dict:
        """Entraîner un modèle de réseau de neurones pour la classification"""
        try:
            from sklearn.neural_network import MLPClassifier
        except ImportError:
            return {"error": "MLPClassifier non disponible"}
        
        # Utiliser la session passée en paramètre ou celle de l'instance
        session = db or self.db
        
        # Créer les données d'entraînement
        df = self.create_labels_for_training(symbol, target_param, session)
        
        if df.empty or len(df) < 100:
            return {"error": "Pas assez de données pour l'entraînement"}
        
        # Préparer les features et labels
        feature_columns = [col for col in df.columns if col not in [
            'date', 'symbol', 'target_achieved', 'target_return', 'target_price', 
            'future_close', 'actual_return', 'target_return_percentage', 
            'time_horizon_days', 'return_vs_target', 'days_to_target'
        ]]
        
        X = df[feature_columns].fillna(0)
        y = df['target_achieved']
        
        # Supprimer les lignes avec des valeurs infinies
        mask = np.isfinite(X).all(axis=1) & np.isfinite(y)
        X = X[mask]
        y = y[mask]
        
        if len(X) < 50:
            return {"error": "Pas assez de données valides après nettoyage"}
        
        # Diviser en train/test
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
        
        # Normaliser les features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Entraîner le modèle
        model = MLPClassifier(
            hidden_layer_sizes=(150, 100, 50),
            max_iter=800,
            learning_rate_init=0.001,
            alpha=0.0001,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1
        )
        
        model.fit(X_train_scaled, y_train)
        
        # Prédictions
        y_pred = model.predict(X_test_scaled)
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        
        # Métriques
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, zero_division=0)
        recall = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        # Validation croisée
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='accuracy')
        
        # Sauvegarder le modèle
        model_name = f"NeuralNetwork_{symbol}_{target_param.id}"
        model_path = os.path.join(self.models_path, f"{model_name}.joblib")
        
        # Sauvegarder le modèle et le scaler
        model_data = {
            'model': model,
            'scaler': scaler,
            'feature_names': feature_columns
        }
        joblib.dump(model_data, model_path)
        
        # Enregistrer en base de données
        ml_model = MLModels(
            model_name=model_name,
            model_type="classification",
            symbol=symbol,
            target_parameter_id=target_param.id,
            search_id=search_id,
            model_path=model_path,
            model_parameters={
                "algorithm": "NeuralNetwork",
                "hidden_layer_sizes": (100, 50),
                "max_iter": 500,
                "feature_names": feature_columns,
                "target_return_percentage": float(target_param.target_return_percentage),
                "time_horizon_days": target_param.time_horizon_days
            },
            performance_metrics={
                "accuracy": float(accuracy),
                "precision": float(precision),
                "recall": float(recall),
                "f1_score": float(f1),
                "cv_mean": float(cv_scores.mean()),
                "cv_std": float(cv_scores.std())
            },
            created_at=datetime.now(),
            is_active=True
        )
        
        session.add(ml_model)
        session.commit()
        session.refresh(ml_model)
        
        return {
            "model_id": ml_model.id,
            "model_name": model_name,
            "algorithm": "NeuralNetwork",
            "accuracy": float(accuracy),
            "precision": float(precision),
            "recall": float(recall),
            "f1_score": float(f1),
            "cv_mean": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
            "model_path": model_path
        }
