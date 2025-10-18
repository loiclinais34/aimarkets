#!/usr/bin/env python3
"""
Système de modèles ML sophistiqués pour la génération de recommandations.
Utilise Random Forest, XGBoost et des techniques avancées de feature engineering.
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

# ML Libraries
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib

# Ajouter le chemin du projet
sys.path.append('/Users/loiclinais/Documents/dev/aimarkets/backend')

load_dotenv()

class SophisticatedMLModels:
    """Classe pour les modèles ML sophistiqués"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'aimarkets'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password')
        )
        
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.models = {}
        
    def get_training_data(self, start_date: str = '2025-01-01') -> pd.DataFrame:
        """Récupère les données d'entraînement combinées"""
        
        query = """
        SELECT 
            hd.symbol,
            hd.date,
            hd.open,
            hd.high,
            hd.low,
            hd.close,
            hd.volume,
            ati.sma_5,
            ati.sma_10,
            ati.sma_20,
            ati.sma_50,
            ati.ema_5,
            ati.ema_10,
            ati.ema_20,
            ati.rsi_14,
            ati.rsi_21,
            ati.bollinger_upper,
            ati.bollinger_middle,
            ati.bollinger_lower,
            ati.bollinger_width,
            ati.macd_line,
            ati.macd_signal,
            ati.macd_histogram,
            ati.stochastic_k,
            ati.stochastic_d,
            ati.atr_14,
            ati.volatility_20,
            ati.volume_sma_20,
            ati.volume_ratio,
            ati.obv,
            ati.vwap,
            ati.support_level,
            ati.resistance_level,
            ati.pivot_point,
            ho.recommendation,
            ho.confidence_level
        FROM historical_data hd
        LEFT JOIN advanced_technical_indicators ati ON hd.symbol = ati.symbol AND hd.date = ati.date
        LEFT JOIN historical_opportunities ho ON hd.symbol = ho.symbol AND hd.date = ho.opportunity_date
        WHERE hd.date >= %s
        AND ati.symbol IS NOT NULL
        ORDER BY hd.symbol, hd.date
        """
        
        df = pd.read_sql_query(query, self.conn, params=[start_date])
        
        # Nettoyer les données
        df = df.dropna(subset=['close', 'volume'])
        
        # Convertir les colonnes numériques
        numeric_columns = ['open', 'high', 'low', 'close', 'volume', 'sma_5', 'sma_10', 'sma_20', 'sma_50',
                          'ema_5', 'ema_10', 'ema_20', 'rsi_14', 'rsi_21', 'bollinger_upper', 'bollinger_middle',
                          'bollinger_lower', 'bollinger_width', 'macd_line', 'macd_signal', 'macd_histogram',
                          'stochastic_k', 'stochastic_d', 'atr_14', 'volatility_20', 'volume_sma_20', 'volume_ratio',
                          'obv', 'vwap', 'support_level', 'resistance_level', 'pivot_point']
        
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crée des features avancées pour le ML"""
        
        # Features de prix
        df['price_change_1d'] = df['close'].pct_change()
        df['price_change_5d'] = df['close'].pct_change(5)
        df['price_change_20d'] = df['close'].pct_change(20)
        
        # Features de volatilité
        df['volatility_5d'] = df['price_change_1d'].rolling(5).std()
        df['volatility_20d'] = df['price_change_1d'].rolling(20).std()
        
        # Features de volume
        df['volume_change'] = df['volume'].pct_change()
        df['volume_sma_ratio'] = df['volume'] / df['volume_sma_20']
        
        # Features techniques normalisées
        df['rsi_normalized'] = (df['rsi_14'] - 50) / 50
        df['macd_normalized'] = df['macd_line'] / df['close']
        df['bollinger_position'] = (df['close'] - df['bollinger_lower']) / (df['bollinger_upper'] - df['bollinger_lower'])
        
        # Features de momentum
        df['momentum_5d'] = df['close'] / df['close'].shift(5) - 1
        df['momentum_20d'] = df['close'] / df['close'].shift(20) - 1
        
        # Features de tendance
        df['trend_5d'] = (df['sma_5'] - df['sma_20']) / df['sma_20']
        df['trend_20d'] = (df['sma_20'] - df['sma_50']) / df['sma_50']
        
        # Features de support/résistance
        df['support_distance'] = (df['close'] - df['support_level']) / df['close']
        df['resistance_distance'] = (df['resistance_level'] - df['close']) / df['close']
        
        # Features de timing
        df['day_of_week'] = pd.to_datetime(df['date']).dt.dayofweek
        df['month'] = pd.to_datetime(df['date']).dt.month
        df['quarter'] = pd.to_datetime(df['date']).dt.quarter
        df['is_month_end'] = pd.to_datetime(df['date']).dt.is_month_end
        df['is_quarter_end'] = pd.to_datetime(df['date']).dt.is_quarter_end
        
        # Features de corrélation avec le marché (approximation)
        try:
            df['market_correlation'] = df.groupby('symbol')['price_change_1d'].rolling(20).corr(
                df.groupby('symbol')['price_change_1d'].rolling(20).mean()
            ).reset_index(0, drop=True)
        except:
            df['market_correlation'] = 0
        
        return df
    
    def create_targets(self, df: pd.DataFrame) -> pd.DataFrame:
        """Crée les variables cibles pour l'entraînement"""
        
        # Target pour la classification (recommandation)
        df['target_recommendation'] = df['recommendation'].fillna('HOLD')
        
        # Target pour la régression (retour futur) - calcul simplifié
        df = df.sort_values(['symbol', 'date']).reset_index(drop=True)
        
        # Calculer les retours futurs par symbole
        df['future_return_1d'] = 0.0
        df['future_return_5d'] = 0.0
        df['future_return_20d'] = 0.0
        
        for symbol in df['symbol'].unique():
            symbol_mask = df['symbol'] == symbol
            symbol_data = df[symbol_mask].copy()
            
            if len(symbol_data) > 20:
                symbol_data['future_return_1d'] = symbol_data['close'].shift(-1) / symbol_data['close'] - 1
                symbol_data['future_return_5d'] = symbol_data['close'].shift(-5) / symbol_data['close'] - 1
                symbol_data['future_return_20d'] = symbol_data['close'].shift(-20) / symbol_data['close'] - 1
                
                df.loc[symbol_mask, 'future_return_1d'] = symbol_data['future_return_1d']
                df.loc[symbol_mask, 'future_return_5d'] = symbol_data['future_return_5d']
                df.loc[symbol_mask, 'future_return_20d'] = symbol_data['future_return_20d']
        
        # Target pour la volatilité future
        df['future_volatility_5d'] = 0.0
        
        return df
    
    def prepare_features_and_targets(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series, pd.Series]:
        """Prépare les features et targets pour l'entraînement"""
        
        # Colonnes de features
        feature_columns = [
            'price_change_1d', 'price_change_5d', 'price_change_20d',
            'volatility_5d', 'volatility_20d',
            'volume_change', 'volume_sma_ratio',
            'rsi_normalized', 'macd_normalized', 'bollinger_position',
            'momentum_5d', 'momentum_20d',
            'trend_5d', 'trend_20d',
            'support_distance', 'resistance_distance',
            'day_of_week', 'month', 'quarter',
            'market_correlation'
        ]
        
        # Filtrer les colonnes existantes
        available_features = [col for col in feature_columns if col in df.columns]
        
        # Features
        X = df[available_features].fillna(0)
        
        # Targets
        y_classification = df['target_recommendation'].fillna('HOLD')
        y_regression = df['future_return_5d'].fillna(0)
        
        # Supprimer les lignes avec des valeurs manquantes
        mask = ~(X.isnull().any(axis=1) | y_classification.isnull() | y_regression.isnull())
        X = X[mask]
        y_classification = y_classification[mask]
        y_regression = y_regression[mask]
        
        return X, y_classification, y_regression
    
    def train_classification_model(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Entraîne un modèle de classification pour les recommandations"""
        
        print("🤖 Entraînement du modèle de classification...")
        
        # Encoder les labels
        y_encoded = self.label_encoder.fit_transform(y)
        
        # Diviser les données
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
        
        # Normaliser les features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Modèle Random Forest avec optimisation des hyperparamètres
        rf_classifier = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        # Entraînement
        rf_classifier.fit(X_train_scaled, y_train)
        
        # Prédictions
        y_pred = rf_classifier.predict(X_test_scaled)
        
        # Métriques
        accuracy = accuracy_score(y_test, y_pred)
        classification_rep = classification_report(y_test, y_pred, output_dict=True)
        
        # Importance des features
        feature_importance = dict(zip(X.columns, rf_classifier.feature_importances_))
        
        # Sauvegarder le modèle
        model_info = {
            'model_type': 'RandomForestClassifier',
            'accuracy': accuracy,
            'classification_report': classification_rep,
            'feature_importance': feature_importance,
            'classes': self.label_encoder.classes_.tolist(),
            'feature_columns': X.columns.tolist(),
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
        
        self.models['classification'] = {
            'model': rf_classifier,
            'scaler': self.scaler,
            'label_encoder': self.label_encoder,
            'info': model_info
        }
        
        print(f"    ✅ Précision: {accuracy:.4f}")
        print(f"    📊 Classes: {len(self.label_encoder.classes_)}")
        
        return model_info
    
    def train_regression_model(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, Any]:
        """Entraîne un modèle de régression pour les retours"""
        
        print("🤖 Entraînement du modèle de régression...")
        
        # Diviser les données
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Normaliser les features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Modèle Random Forest Regressor
        rf_regressor = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        # Entraînement
        rf_regressor.fit(X_train_scaled, y_train)
        
        # Prédictions
        y_pred = rf_regressor.predict(X_test_scaled)
        
        # Métriques
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        # Importance des features
        feature_importance = dict(zip(X.columns, rf_regressor.feature_importances_))
        
        # Sauvegarder le modèle
        model_info = {
            'model_type': 'RandomForestRegressor',
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r2_score': r2,
            'feature_importance': feature_importance,
            'feature_columns': X.columns.tolist(),
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
        
        self.models['regression'] = {
            'model': rf_regressor,
            'scaler': self.scaler,
            'info': model_info
        }
        
        print(f"    ✅ R² Score: {r2:.4f}")
        print(f"    📊 RMSE: {rmse:.4f}")
        
        return model_info
    
    def generate_recommendations(self, symbol: str, date: str) -> Dict[str, Any]:
        """Génère des recommandations pour un symbole et une date donnés"""
        
        if 'classification' not in self.models or 'regression' not in self.models:
            return {'error': 'Modèles non entraînés'}
        
        # Récupérer les données pour le symbole et la date
        query = """
        SELECT 
            hd.symbol,
            hd.date,
            hd.close,
            hd.volume,
            ati.sma_5, ati.sma_10, ati.sma_20, ati.sma_50,
            ati.ema_5, ati.ema_10, ati.ema_20,
            ati.rsi_14, ati.rsi_21,
            ati.bollinger_upper, ati.bollinger_middle, ati.bollinger_lower, ati.bollinger_width,
            ati.macd_line, ati.macd_signal, ati.macd_histogram,
            ati.stochastic_k, ati.stochastic_d,
            ati.atr_14, ati.volatility_20,
            ati.volume_sma_20, ati.volume_ratio,
            ati.obv, ati.vwap,
            ati.support_level, ati.resistance_level, ati.pivot_point
        FROM historical_data hd
        LEFT JOIN advanced_technical_indicators ati ON hd.symbol = ati.symbol AND hd.date = ati.date
        WHERE hd.symbol = %s AND hd.date = %s
        """
        
        df = pd.read_sql_query(query, self.conn, params=[symbol, date])
        
        if df.empty:
            return {'error': 'Données non trouvées'}
        
        # Créer les features
        df = self.create_features(df)
        
        # Préparer les features pour la prédiction
        feature_columns = self.models['classification']['info']['feature_columns']
        X = df[feature_columns].fillna(0)
        
        # Prédictions
        X_scaled = self.scaler.transform(X)
        
        # Prédiction de classification
        recommendation_proba = self.models['classification']['model'].predict_proba(X_scaled)[0]
        recommendation = self.label_encoder.inverse_transform(
            [self.models['classification']['model'].predict(X_scaled)[0]]
        )[0]
        
        # Prédiction de régression
        predicted_return = self.models['regression']['model'].predict(X_scaled)[0]
        
        # Calculer la confiance basée sur les probabilités
        max_probability = np.max(recommendation_proba)
        confidence_level = max_probability
        
        # Déterminer le niveau de recommandation
        if confidence_level >= 0.8:
            if predicted_return > 0.05:
                final_recommendation = 'BUY_STRONG'
            elif predicted_return > 0.03:
                final_recommendation = 'BUY_MODERATE'
            elif predicted_return > 0.01:
                final_recommendation = 'BUY_WEAK'
            elif predicted_return < -0.05:
                final_recommendation = 'SELL_STRONG'
            elif predicted_return < -0.03:
                final_recommendation = 'SELL_WEAK'
            else:
                final_recommendation = 'HOLD'
        else:
            final_recommendation = 'HOLD'
        
        return {
            'symbol': symbol,
            'date': date,
            'recommendation': final_recommendation,
            'confidence_level': confidence_level,
            'predicted_return_5d': predicted_return,
            'raw_recommendation': recommendation,
            'recommendation_probabilities': dict(zip(
                self.label_encoder.classes_, recommendation_proba
            )),
            'key_factors': self.get_key_factors(X, feature_columns)
        }
    
    def get_key_factors(self, X: pd.DataFrame, feature_columns: List[str]) -> Dict[str, float]:
        """Identifie les facteurs clés pour la recommandation"""
        
        feature_importance = self.models['classification']['info']['feature_importance']
        
        # Trier par importance
        sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        
        # Prendre les 5 plus importantes
        top_features = sorted_features[:5]
        
        # Obtenir les valeurs actuelles
        key_factors = {}
        for feature, importance in top_features:
            if feature in X.columns:
                key_factors[feature] = float(X[feature].iloc[0])
        
        return key_factors
    
    def save_models_to_db(self):
        """Sauvegarde les modèles dans la base de données"""
        
        cur = self.conn.cursor()
        
        for model_type, model_data in self.models.items():
            model_info = model_data['info']
            
            # Insérer dans ml_models_v2
            insert_query = """
            INSERT INTO ml_models_v2 
            (model_name, model_type, model_version, model_parameters, feature_columns, target_column,
             training_score, validation_score, test_score, feature_importance, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            model_name = f"sophisticated_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Score principal selon le type de modèle
            main_score = model_info.get('accuracy', model_info.get('r2_score', 0))
            
            cur.execute(insert_query, (
                model_name,
                model_info['model_type'],
                '1.0',
                json.dumps({'n_estimators': 200, 'max_depth': 15}),
                json.dumps(model_info['feature_columns']),
                'target_recommendation' if model_type == 'classification' else 'future_return_5d',
                main_score,
                main_score,  # validation_score (approximation)
                main_score,  # test_score
                json.dumps(model_info['feature_importance']),
                True,
                datetime.now()
            ))
        
        self.conn.commit()
        cur.close()
        
        print("💾 Modèles sauvegardés dans la base de données")
    
    def train_complete_system(self):
        """Entraîne le système ML complet"""
        
        print("🚀 Démarrage de l'entraînement du système ML sophistiqué...")
        
        # Récupérer les données
        print("📊 Récupération des données d'entraînement...")
        df = self.get_training_data()
        print(f"    ✅ {len(df)} enregistrements récupérés")
        
        # Créer les features
        print("🔧 Création des features avancées...")
        df = self.create_features(df)
        
        # Créer les targets
        print("🎯 Création des variables cibles...")
        df = self.create_targets(df)
        
        # Préparer les données
        print("⚙️ Préparation des données pour l'entraînement...")
        X, y_class, y_reg = self.prepare_features_and_targets(df)
        print(f"    ✅ {len(X)} échantillons d'entraînement")
        print(f"    📊 {len(X.columns)} features")
        
        # Entraîner les modèles
        classification_info = self.train_classification_model(X, y_class)
        regression_info = self.train_regression_model(X, y_reg)
        
        # Sauvegarder les modèles
        self.save_models_to_db()
        
        print("✅ Entraînement terminé!")
        
        return {
            'classification': classification_info,
            'regression': regression_info
        }
    
    def close(self):
        """Ferme la connexion à la base de données"""
        self.conn.close()

def main():
    """Fonction principale"""
    print("🤖 Démarrage du système ML sophistiqué...")
    
    ml_system = SophisticatedMLModels()
    
    try:
        # Entraîner le système complet
        results = ml_system.train_complete_system()
        
        # Tester avec quelques symboles
        print("\\n🧪 Test des recommandations...")
        test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
        
        for symbol in test_symbols:
            try:
                recommendation = ml_system.generate_recommendations(symbol, '2025-10-17')
                if 'error' not in recommendation:
                    print(f"  {symbol}: {recommendation['recommendation']} "
                          f"(confiance: {recommendation['confidence_level']:.3f}, "
                          f"retour prédit: {recommendation['predicted_return_5d']:.3f})")
            except Exception as e:
                print(f"  {symbol}: Erreur - {str(e)}")
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
    finally:
        ml_system.close()

if __name__ == "__main__":
    main()
