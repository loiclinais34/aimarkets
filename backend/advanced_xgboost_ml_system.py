#!/usr/bin/env python3
"""
Advanced ML System with XGBoost and TA-Lib Technical Indicators
This script implements:
1. XGBoost models for classification and regression
2. TA-Lib technical indicators from advanced_technical_indicators table
3. Advanced feature engineering
4. Ensemble methods with XGBoost
5. Performance optimization
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import TA-Lib integration
from talib_indicators import TALibIndicators

# Database imports
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ML imports
import xgboost as xgb
from sklearn.ensemble import VotingClassifier, VotingRegressor
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
import joblib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_xgboost_ml_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AdvancedXGBoostMLSystem:
    """Système ML avancé avec XGBoost et indicateurs techniques TA-Lib."""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.engine = create_engine(
            f"postgresql://{db_config['user']}:{db_config['password']}@"
            f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        self.Session = sessionmaker(bind=self.engine)
        
        # TA-Lib calculator
        self.talib_calculator = TALibIndicators()
        
        # XGBoost models
        self.classification_models = {}
        self.regression_models = {}
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        
        # Cache pour les données
        self.data_cache = {}
        
        # Configuration des horizons
        self.horizons = [1, 7, 30]
        
        # Configuration des symboles
        self.symbols = self._get_all_symbols()
        
        # Feature columns from TA-Lib indicators
        self.feature_columns = self._get_talib_feature_columns()
        
        logger.info(f"AdvancedXGBoostMLSystem initialisé avec {len(self.symbols)} symboles et {len(self.feature_columns)} features TA-Lib")
    
    def _get_all_symbols(self) -> List[str]:
        """Récupère tous les symboles disponibles."""
        query = "SELECT DISTINCT symbol FROM advanced_technical_indicators ORDER BY symbol"
        df = pd.read_sql(query, self.engine)
        return df['symbol'].tolist()
    
    def _get_talib_feature_columns(self) -> List[str]:
        """Retourne la liste des colonnes d'indicateurs TA-Lib disponibles."""
        return [
            # Overlap Studies
            'sma_5', 'sma_10', 'sma_20', 'sma_50', 'sma_100', 'sma_200',
            'ema_5', 'ema_10', 'ema_20', 'ema_50', 'ema_100', 'ema_200',
            'wma_20', 'wma_50', 'trima_20', 'trima_50', 'kama_20', 'kama_50',
            'mama', 'fama', 'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_percent',
            'dema_20', 'tema_20', 'midpoint_20', 'midprice_20', 'sar', 't3_20',
            
            # Momentum Indicators
            'rsi_14', 'rsi_21', 'stoch_k', 'stoch_d', 'stochf_k', 'stochf_d',
            'stochrsi_k', 'stochrsi_d', 'willr_14', 'adx_14', 'adxr_14',
            'plus_di', 'minus_di', 'aroon_up', 'aroon_down', 'aroonosc', 'bop',
            'cci_14', 'cmo_14', 'dx_14', 'macd', 'macd_signal', 'macd_hist',
            'macd_fix', 'macd_fix_signal', 'macd_fix_hist', 'mom_10', 'mom_20',
            'roc_10', 'roc_20', 'rocp_10', 'rocr_10', 'rocr100_10', 'ultosc',
            
            # Volume Indicators
            'ad', 'adosc', 'obv', 'mfi_14', 'vpt', 'wad',
            
            # Volatility Indicators
            'atr_14', 'atr_20', 'trange', 'natr_14', 'stddev_20', 'stddev_50',
            'var_20', 'var_50',
            
            # Price Transform
            'avgprice', 'medprice', 'typprice', 'wclprice',
            
            # Cycle Indicators
            'ht_dcperiod', 'ht_dcphase', 'ht_phasor_inphase', 'ht_phasor_quadrature',
            'ht_sine', 'ht_leadsine', 'ht_trendmode',
            
            # Pattern Recognition
            'cdl_doji', 'cdl_hammer', 'cdl_hangingman', 'cdl_engulfing',
            'cdl_morningstar', 'cdl_eveningstar', 'cdl_piercing', 'cdl_darkcloudcover',
            'cdl_shootingstar', 'cdl_marubozu', 'cdl_spinningtop',
            
            # Statistical Functions
            'beta_20', 'correl_20', 'linearreg', 'linearreg_angle',
            'linearreg_intercept', 'linearreg_slope', 'tsf_20',
            
            # Custom Features
            'sma_ratio_20_50', 'ema_ratio_20_50', 'bb_position', 'bb_squeeze',
            'momentum_composite', 'volatility_composite', 'trend_strength', 'obv_price_divergence'
        ]
    
    def get_technical_indicators_data(self, symbols: Optional[List[str]] = None, limit: Optional[int] = None) -> pd.DataFrame:
        """Récupère les données d'indicateurs techniques depuis la table advanced_technical_indicators."""
        logger.info("📊 Récupération des données d'indicateurs techniques TA-Lib...")
        
        try:
            # Construire la requête
            if symbols:
                symbols_str = "', '".join(symbols)
                where_clause = f"WHERE symbol IN ('{symbols_str}')"
            else:
                where_clause = ""
            
            limit_clause = f"LIMIT {limit}" if limit else ""
            
            query = f"""
            SELECT symbol, date, open, high, low, close, volume,
                   {', '.join(self.feature_columns)}
            FROM advanced_technical_indicators
            {where_clause}
            ORDER BY symbol, date ASC
            {limit_clause}
            """
            
            df = pd.read_sql(query, self.engine)
            
            if not df.empty:
                # Convertir les types
                df['date'] = pd.to_datetime(df['date']).dt.date
                for col in ['open', 'high', 'low', 'close']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
                
                # Remplacer les valeurs NaN par None pour les indicateurs
                indicator_cols = [col for col in df.columns if col not in ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]
                df[indicator_cols] = df[indicator_cols].replace({np.nan: None})
                
                logger.info(f"✅ Récupéré {len(df)} enregistrements avec {len(indicator_cols)} indicateurs")
            else:
                logger.warning("⚠️ Aucune donnée trouvée")
            
            return df
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la récupération des données: {e}")
            return pd.DataFrame()
    
    def create_advanced_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crée des features avancées basées sur les indicateurs TA-Lib."""
        df = df.copy()
        
        try:
            # Features de prix
            df['price_change_1d'] = df['close'].pct_change(1)
            df['price_change_5d'] = df['close'].pct_change(5)
            df['price_change_20d'] = df['close'].pct_change(20)
            
            # Features de volatilité
            df['volatility_5d'] = df['price_change_1d'].rolling(5).std()
            df['volatility_20d'] = df['price_change_1d'].rolling(20).std()
            
            # Features de volume
            df['volume_change'] = df['volume'].pct_change(1)
            df['volume_sma_20'] = df['volume'].rolling(20).mean()
            df['volume_sma_ratio'] = df['volume'] / df['volume_sma_20']
            
            # Features de momentum
            df['momentum_5d'] = df['close'] / df['close'].shift(5) - 1
            df['momentum_20d'] = df['close'] / df['close'].shift(20) - 1
            
            # Features de tendance
            df['trend_5d'] = (df['close'] - df['close'].rolling(5).mean()) / df['close'].rolling(5).mean()
            df['trend_20d'] = (df['close'] - df['close'].rolling(20).mean()) / df['close'].rolling(20).mean()
            
            # Support/Resistance
            df['support_level'] = df['low'].rolling(20).min()
            df['resistance_level'] = df['high'].rolling(20).max()
            df['support_distance'] = (df['close'] - df['support_level']) / df['close']
            df['resistance_distance'] = (df['resistance_level'] - df['close']) / df['close']
            
            # Features temporelles
            df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
            df['month'] = pd.to_datetime(df['date']).dt.month
            df['quarter'] = pd.to_datetime(df['date']).dt.quarter
            
            # Features composites basées sur les indicateurs TA-Lib
            if 'rsi_14' in df.columns and 'stoch_k' in df.columns:
                df['momentum_score'] = (df['rsi_14'] + df['stoch_k']) / 2
            
            if 'adx_14' in df.columns and 'plus_di' in df.columns and 'minus_di' in df.columns:
                df['trend_score'] = df['adx_14'] * (df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
            
            if 'bb_position' in df.columns and 'bb_squeeze' in df.columns:
                df['bb_signal'] = df['bb_position'] * df['bb_squeeze']
            
            logger.info(f"✅ Features avancées créées: {len([col for col in df.columns if col not in self.feature_columns + ['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']])}")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création des features avancées: {e}")
        
        return df
    
    def create_targets(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crée les variables cibles pour l'entraînement ML."""
        df = df.copy()
        
        try:
            # Retours futurs pour différents horizons
            # Pour chaque date t, calculer le retour vers t+horizon
            df['future_return_1d'] = df['close'].shift(-1) / df['close'] - 1
            df['future_return_7d'] = df['close'].shift(-7) / df['close'] - 1  
            df['future_return_30d'] = df['close'].shift(-30) / df['close'] - 1
            
            # Vérification : pour une date donnée, nous regardons le prix dans X jours
            # shift(-7) = prix dans 7 jours / prix actuel - 1
            
            # Recommandations basées sur les retours futurs
            def get_recommendation(return_1d, return_7d, return_30d):
                # Moyenne pondérée avec plus de poids sur les horizons courts
                avg_return = (return_1d * 0.5 + return_7d * 0.3 + return_30d * 0.2)
                
                if avg_return >= 0.05:
                    return 'BUY_STRONG'
                elif avg_return >= 0.03:
                    return 'BUY_MODERATE'
                elif avg_return >= 0.01:
                    return 'BUY_WEAK'
                elif avg_return >= -0.01:
                    return 'HOLD'
                elif avg_return >= -0.03:
                    return 'SELL_WEAK'
                else:
                    return 'SELL_STRONG'
            
            df['target_recommendation'] = df.apply(
                lambda row: get_recommendation(
                    row['future_return_1d'], 
                    row['future_return_7d'], 
                    row['future_return_30d']
                ), axis=1
            )
            
            logger.info("✅ Variables cibles créées")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la création des variables cibles: {e}")
        
        return df
    
    def prepare_ml_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, List[str]]:
        """Prépare les données pour l'entraînement ML."""
        logger.info("🤖 Préparation des données ML...")
        
        try:
            # Sélectionner les features disponibles
            available_features = []
            for feature in self.feature_columns:
                if feature in df.columns:
                    available_features.append(feature)
            
            # Ajouter les features avancées
            advanced_features = [
                'price_change_1d', 'price_change_5d', 'price_change_20d',
                'volatility_5d', 'volatility_20d', 'volume_change', 'volume_sma_ratio',
                'momentum_5d', 'momentum_20d', 'trend_5d', 'trend_20d',
                'support_distance', 'resistance_distance', 'day_of_week', 'month', 'quarter'
            ]
            
            for feature in advanced_features:
                if feature in df.columns:
                    available_features.append(feature)
            
            # Features composites
            composite_features = ['momentum_score', 'trend_score', 'bb_signal']
            for feature in composite_features:
                if feature in df.columns:
                    available_features.append(feature)
            
            logger.info(f"📊 Features disponibles: {len(available_features)}")
            
            # Sélectionner les colonnes pour ML
            ml_columns = ['symbol', 'date'] + available_features + ['target_recommendation', 'future_return_1d', 'future_return_7d', 'future_return_30d']
            ml_data = df[ml_columns].copy()
            
            # Remplacer les valeurs NaN par 0 pour les features numériques
            feature_columns = [col for col in ml_data.columns if col not in ['symbol', 'date', 'target_recommendation']]
            ml_data[feature_columns] = ml_data[feature_columns].fillna(0)
            
            # Supprimer seulement les lignes avec des valeurs manquantes dans les colonnes essentielles
            essential_columns = ['target_recommendation', 'future_return_1d']
            ml_data = ml_data.dropna(subset=essential_columns)
            
            logger.info(f"✅ Données ML préparées: {len(ml_data)} échantillons, {len(available_features)} features")
            
            return ml_data, ml_data[available_features], available_features
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la préparation des données ML: {e}")
            return pd.DataFrame(), pd.DataFrame(), []
    
    def train_xgboost_models(self, X: pd.DataFrame, y_classification: pd.Series, y_regression: pd.Series, 
                           feature_names: List[str]) -> Dict[str, Any]:
        """Entraîne les modèles XGBoost pour classification et régression."""
        logger.info("🚀 Entraînement des modèles XGBoost...")
        
        try:
            # Encoder les labels de classification
            y_classification_encoded = self.label_encoder.fit_transform(y_classification)
            
            # Séparer les données d'entraînement et de test
            X_train, X_test, y_class_train, y_class_test = train_test_split(
                X, y_classification_encoded, test_size=0.2, random_state=42, stratify=y_classification_encoded
            )
            
            _, _, y_reg_train, y_reg_test = train_test_split(
                X, y_regression, test_size=0.2, random_state=42
            )
            
            # Normaliser les features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Configuration XGBoost optimisée
            xgb_classifier_params = {
                'n_estimators': 1000,
                'max_depth': 6,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': 42,
                'n_jobs': -1,
                'eval_metric': 'mlogloss'
            }
            
            xgb_regressor_params = {
                'n_estimators': 1000,
                'max_depth': 6,
                'learning_rate': 0.1,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': 42,
                'n_jobs': -1,
                'eval_metric': 'rmse'
            }
            
            # Entraîner le modèle de classification
            logger.info("📊 Entraînement du modèle de classification...")
            xgb_classifier = xgb.XGBClassifier(**xgb_classifier_params)
            xgb_classifier.fit(
                X_train_scaled, y_class_train,
                eval_set=[(X_test_scaled, y_class_test)],
                verbose=False
            )
            
            # Entraîner le modèle de régression
            logger.info("📈 Entraînement du modèle de régression...")
            xgb_regressor = xgb.XGBRegressor(**xgb_regressor_params)
            xgb_regressor.fit(
                X_train_scaled, y_reg_train,
                eval_set=[(X_test_scaled, y_reg_test)],
                verbose=False
            )
            
            # Évaluer les modèles
            class_pred = xgb_classifier.predict(X_test_scaled)
            reg_pred = xgb_regressor.predict(X_test_scaled)
            
            class_accuracy = accuracy_score(y_class_test, class_pred)
            reg_r2 = r2_score(y_reg_test, reg_pred)
            reg_rmse = np.sqrt(mean_squared_error(y_reg_test, reg_pred))
            
            logger.info(f"✅ Classification Accuracy: {class_accuracy:.4f}")
            logger.info(f"✅ Regression R²: {reg_r2:.4f}")
            logger.info(f"✅ Regression RMSE: {reg_rmse:.4f}")
            
            # Importance des features
            feature_importance = pd.DataFrame({
                'feature': feature_names,
                'importance': xgb_classifier.feature_importances_
            }).sort_values('importance', ascending=False)
            
            logger.info("🎯 Top 10 Features les plus importantes:")
            for _, row in feature_importance.head(10).iterrows():
                logger.info(f"  {row['feature']}: {row['importance']:.4f}")
            
            # Sauvegarder les modèles
            models = {
                'classifier': xgb_classifier,
                'regressor': xgb_regressor,
                'scaler': self.scaler,
                'label_encoder': self.label_encoder,
                'feature_names': feature_names,
                'performance': {
                    'classification_accuracy': class_accuracy,
                    'regression_r2': reg_r2,
                    'regression_rmse': reg_rmse
                },
                'feature_importance': feature_importance
            }
            
            # Sauvegarder sur disque
            joblib.dump(models, 'xgboost_models.pkl')
            logger.info("💾 Modèles sauvegardés dans xgboost_models.pkl")
            
            return models
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'entraînement des modèles: {e}")
            return {}
    
    def generate_opportunities(self, symbols: Optional[List[str]] = None, 
                            horizons: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Génère des opportunités de trading basées sur les modèles XGBoost."""
        logger.info("🎯 Génération d'opportunités de trading...")
        
        try:
            if horizons is None:
                horizons = self.horizons
            
            if symbols is None:
                symbols = self.symbols[:10]  # Limiter pour les tests
            
            # Charger les modèles
            if os.path.exists('xgboost_models.pkl'):
                models = joblib.load('xgboost_models.pkl')
                classifier = models['classifier']
                regressor = models['regressor']
                scaler = models['scaler']
                label_encoder = models['label_encoder']
                feature_names = models['feature_names']
            else:
                logger.error("❌ Modèles non trouvés. Veuillez d'abord entraîner les modèles.")
                return []
            
            opportunities = []
            
            for symbol in symbols:
                logger.info(f"📊 Génération d'opportunités pour {symbol}...")
                
                # Récupérer les données récentes
                symbol_data = self.get_technical_indicators_data([symbol], limit=100)
                
                if symbol_data.empty:
                    continue
                
                # Créer les features avancées
                symbol_data = self.create_advanced_features(symbol_data)
                
                # Sélectionner les features disponibles
                available_features = [f for f in feature_names if f in symbol_data.columns]
                
                if len(available_features) < len(feature_names) * 0.8:  # Au moins 80% des features
                    logger.warning(f"⚠️ Features insuffisantes pour {symbol}")
                    continue
                
                # Préparer les données pour la prédiction
                X = symbol_data[available_features].fillna(0)
                
                # Normaliser
                X_scaled = scaler.transform(X)
                
                # Prédictions
                predictions_encoded = classifier.predict(X_scaled)
                probabilities = classifier.predict_proba(X_scaled)
                returns = regressor.predict(X_scaled)
                
                # Décoder les prédictions
                predictions = label_encoder.inverse_transform(predictions_encoded)
                
                # Créer les opportunités pour chaque horizon
                for horizon in horizons:
                    for i, (pred, prob, ret) in enumerate(zip(predictions, probabilities, returns)):
                        if i >= len(symbol_data):
                            break
                        
                        row = symbol_data.iloc[i]
                        confidence = np.max(prob)
                        
                        # Filtrer les opportunités avec une confiance suffisante
                        if confidence >= 0.6:
                            opportunity = {
                                'symbol': symbol,
                                'date': row['date'],
                                'horizon_days': horizon,
                                'recommendation': pred,
                                'confidence_level': float(confidence),
                                'potential_return': float(ret),
                                'risk_score': float(1 - confidence),  # Score de risque inverse de la confiance
                                'ml_model_name': 'xgboost_advanced_v1',
                                'ml_model_version': '1.0',
                                'technical_indicators': json.dumps({
                                    'rsi_14': float(row.get('rsi_14', 0) or 0) if pd.notna(row.get('rsi_14', 0)) else 0,
                                    'macd': float(row.get('macd', 0) or 0) if pd.notna(row.get('macd', 0)) else 0,
                                    'bb_position': float(row.get('bb_position', 0) or 0) if pd.notna(row.get('bb_position', 0)) else 0,
                                    'adx_14': float(row.get('adx_14', 0) or 0) if pd.notna(row.get('adx_14', 0)) else 0,
                                    'volume_sma_ratio': float(row.get('volume_sma_ratio', 0) or 0) if pd.notna(row.get('volume_sma_ratio', 0)) else 0
                                }),
                                'ml_features': json.dumps({
                                    'momentum_score': float(row.get('momentum_score', 0) or 0) if pd.notna(row.get('momentum_score', 0)) else 0,
                                    'trend_score': float(row.get('trend_score', 0) or 0) if pd.notna(row.get('trend_score', 0)) else 0,
                                    'bb_signal': float(row.get('bb_signal', 0) or 0) if pd.notna(row.get('bb_signal', 0)) else 0
                                })
                            }
                            
                            opportunities.append(opportunity)
            
            logger.info(f"✅ {len(opportunities)} opportunités générées")
            return opportunities
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la génération d'opportunités: {e}")
            return []
    
    def store_opportunities(self, opportunities: List[Dict[str, Any]]):
        """Stocke les opportunités générées en base de données."""
        if not opportunities:
            logger.warning("⚠️ Aucune opportunité à stocker")
            return
        
        logger.info(f"💾 Stockage de {len(opportunities)} opportunités...")
        
        try:
            # Créer la table si elle n'existe pas
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS ml_opportunities_xgboost (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                recommendation VARCHAR(20) NOT NULL,
                confidence_level DECIMAL(5,4) NOT NULL,
                potential_return DECIMAL(8,4),
                risk_score DECIMAL(5,4),
                ml_model_name VARCHAR(100),
                ml_model_version VARCHAR(20),
                technical_indicators JSONB,
                ml_features JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
            
            with self.engine.connect() as conn:
                conn.execute(text(create_table_sql))
                conn.commit()
            
            # Insérer les opportunités
            df = pd.DataFrame(opportunities)
            df.to_sql('ml_opportunities_xgboost', self.engine, if_exists='append', index=False)
            
            logger.info(f"✅ {len(opportunities)} opportunités stockées avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du stockage des opportunités: {e}")
    
    def run_full_pipeline(self, symbols: Optional[List[str]] = None, 
                         train_models: bool = True, generate_opportunities: bool = True):
        """Exécute le pipeline complet ML."""
        logger.info("🚀 Démarrage du pipeline ML complet...")
        
        try:
            # 1. Récupérer les données
            logger.info("📊 Étape 1: Récupération des données...")
            data = self.get_technical_indicators_data(symbols, limit=10000)
            
            if data.empty:
                logger.error("❌ Aucune donnée récupérée")
                return
            
            # 2. Créer les features avancées
            logger.info("🔧 Étape 2: Création des features avancées...")
            data = self.create_advanced_features(data)
            
            # 3. Créer les variables cibles
            logger.info("🎯 Étape 3: Création des variables cibles...")
            data = self.create_targets(data)
            
            # 4. Préparer les données ML
            logger.info("🤖 Étape 4: Préparation des données ML...")
            ml_data, X, feature_names = self.prepare_ml_data(data)
            
            if X.empty:
                logger.error("❌ Aucune donnée ML préparée")
                return
            
            # 5. Entraîner les modèles
            if train_models:
                logger.info("🚀 Étape 5: Entraînement des modèles XGBoost...")
                models = self.train_xgboost_models(
                    X, 
                    ml_data['target_recommendation'], 
                    ml_data['future_return_1d'],
                    feature_names
                )
                
                if not models:
                    logger.error("❌ Échec de l'entraînement des modèles")
                    return
            
            # 6. Générer les opportunités
            if generate_opportunities:
                logger.info("🎯 Étape 6: Génération des opportunités...")
                opportunities = self.generate_opportunities(symbols)
                
                if opportunities:
                    self.store_opportunities(opportunities)
            
            logger.info("🎉 Pipeline ML complet terminé avec succès!")
            
        except Exception as e:
            logger.error(f"❌ Erreur dans le pipeline ML: {e}", exc_info=True)

def main():
    """Fonction principale."""
    logger.info("🚀 Démarrage du système ML avancé avec XGBoost et TA-Lib")
    
    # Configuration de la base de données
    db_config = {
        'host': 'localhost',
        'port': '5432',
        'database': 'aimarkets',
        'user': 'loiclinais',
        'password': 'password'
    }
    
    try:
        # Initialiser le système
        ml_system = AdvancedXGBoostMLSystem(db_config)
        
        # Exécuter le pipeline complet
        ml_system.run_full_pipeline(
            symbols=['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],  # Test avec 5 symboles
            train_models=True,
            generate_opportunities=True
        )
        
        logger.info("🎉 Script terminé avec succès!")
        
    except Exception as e:
        logger.error(f"❌ Erreur dans le script principal: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
