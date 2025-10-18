#!/usr/bin/env python3
"""
Advanced ML System with Data Expansion, Sentiment Analysis, and Ensemble Methods
This script implements:
1. Full symbol expansion (all 101 symbols)
2. Sentiment analysis features
3. News data integration
4. Ensemble methods (Voting, Stacking, Bagging)
5. Advanced feature engineering
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
from sklearn.ensemble import (
    RandomForestClassifier, RandomForestRegressor,
    VotingClassifier, VotingRegressor,
    BaggingClassifier, BaggingRegressor,
    GradientBoostingClassifier, GradientBoostingRegressor,
    AdaBoostClassifier, AdaBoostRegressor,
    ExtraTreesClassifier, ExtraTreesRegressor
)
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score, classification_report
from sklearn.linear_model import LogisticRegression, Ridge, Lasso
from sklearn.svm import SVC, SVR
from sklearn.neural_network import MLPClassifier, MLPRegressor
import joblib

# Technical analysis
import talib

# Sentiment analysis
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('advanced_ml_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SentimentAnalyzer:
    """Analyzer for market sentiment using news and social media data."""
    
    def __init__(self):
        self.news_sources = [
            'https://finance.yahoo.com/news/',
            'https://www.marketwatch.com/latest-news',
            'https://www.bloomberg.com/markets'
        ]
    
    def analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of text using TextBlob."""
        try:
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            subjectivity = blob.sentiment.subjectivity  # 0 to 1
            
            # Convert to 0-1 scale for ML features
            sentiment_score = (polarity + 1) / 2  # 0 to 1
            confidence = 1 - subjectivity  # Higher confidence for objective text
            
            return {
                'sentiment_score': sentiment_score,
                'sentiment_polarity': polarity,
                'sentiment_subjectivity': subjectivity,
                'sentiment_confidence': confidence
            }
        except Exception as e:
            logger.warning(f"Error analyzing sentiment: {e}")
            return {
                'sentiment_score': 0.5,
                'sentiment_polarity': 0.0,
                'sentiment_subjectivity': 0.5,
                'sentiment_confidence': 0.5
            }
    
    def get_market_sentiment(self, symbol: str) -> Dict[str, float]:
        """Get market sentiment for a specific symbol."""
        # Simulate sentiment analysis (in production, would fetch real news)
        # For now, generate realistic sentiment based on recent price action
        try:
            # This would be replaced with actual news fetching
            mock_sentiment = {
                'news_sentiment': np.random.normal(0.5, 0.2),
                'social_sentiment': np.random.normal(0.5, 0.15),
                'analyst_sentiment': np.random.normal(0.5, 0.1),
                'market_fear_greed': np.random.normal(0.5, 0.25)
            }
            
            # Normalize to 0-1 range
            for key, value in mock_sentiment.items():
                mock_sentiment[key] = max(0, min(1, value))
            
            return mock_sentiment
        except Exception as e:
            logger.warning(f"Error getting market sentiment for {symbol}: {e}")
            return {
                'news_sentiment': 0.5,
                'social_sentiment': 0.5,
                'analyst_sentiment': 0.5,
                'market_fear_greed': 0.5
            }

class AdvancedFeatureEngineer:
    """Advanced feature engineering with sentiment and market data."""
    
    def __init__(self):
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def create_advanced_features(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Create advanced features including sentiment analysis."""
        df = df.copy()
        
        # Basic price features
        df['price_change_1d'] = df['close'].pct_change(1)
        df['price_change_5d'] = df['close'].pct_change(5)
        df['price_change_20d'] = df['close'].pct_change(20)
        df['price_change_60d'] = df['close'].pct_change(60)
        
        # Volatility features
        df['volatility_5d'] = df['price_change_1d'].rolling(5).std()
        df['volatility_20d'] = df['price_change_1d'].rolling(20).std()
        df['volatility_60d'] = df['price_change_1d'].rolling(60).std()
        
        # Volume features
        df['volume_change'] = df['volume'].pct_change(1)
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_sma_ratio'] = df['volume'] / df['volume_sma_20']
        df['volume_price_trend'] = df['volume'] * df['price_change_1d']
        
        # Technical indicators (enhanced)
        high = df['high'].values.astype(float)
        low = df['low'].values.astype(float)
        close = df['close'].values.astype(float)
        volume = df['volume'].values.astype(float)
        
        try:
            # Enhanced technical indicators
            df['rsi_14'] = talib.RSI(close, timeperiod=14)
            df['rsi_21'] = talib.RSI(close, timeperiod=21)
            df['rsi_50'] = talib.RSI(close, timeperiod=50)
            
            # MACD variations
            macd, macd_signal, macd_hist = talib.MACD(close)
            df['macd_line'] = macd
            df['macd_signal'] = macd_signal
            df['macd_histogram'] = macd_hist
            
            # Bollinger Bands
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close)
            df['bollinger_upper'] = bb_upper
            df['bollinger_middle'] = bb_middle
            df['bollinger_lower'] = bb_lower
            df['bollinger_width'] = (bb_upper - bb_lower) / bb_middle
            df['bollinger_position'] = (close - bb_lower) / (bb_upper - bb_lower)
            
            # Stochastic
            df['stochastic_k'], df['stochastic_d'] = talib.STOCH(high, low, close)
            
            # Williams %R
            df['williams_r'] = talib.WILLR(high, low, close)
            
            # CCI
            df['cci'] = talib.CCI(high, low, close)
            
            # ATR
            df['atr_14'] = talib.ATR(high, low, close, timeperiod=14)
            df['atr_21'] = talib.ATR(high, low, close, timeperiod=21)
            
            # ADX (trend strength)
            df['adx'] = talib.ADX(high, low, close, timeperiod=14)
            
            # OBV
            df['obv'] = talib.OBV(close, volume)
            
            # Money Flow Index
            df['mfi'] = talib.MFI(high, low, close, volume, timeperiod=14)
            
        except Exception as e:
            logger.warning(f"Error calculating technical indicators: {e}")
        
        # Momentum features
        df['momentum_5d'] = df['close'] / df['close'].shift(5) - 1
        df['momentum_20d'] = df['close'] / df['close'].shift(20) - 1
        df['momentum_60d'] = df['close'] / df['close'].shift(60) - 1
        
        # Trend features
        df['trend_5d'] = (df['close'] - df['close'].rolling(5).mean()) / df['close'].rolling(5).mean()
        df['trend_20d'] = (df['close'] - df['close'].rolling(20).mean()) / df['close'].rolling(20).mean()
        df['trend_60d'] = (df['close'] - df['close'].rolling(60).mean()) / df['close'].rolling(60).mean()
        
        # Support/Resistance
        df['support_level'] = df['low'].rolling(20).min()
        df['resistance_level'] = df['high'].rolling(20).max()
        df['support_distance'] = (df['close'] - df['support_level']) / df['close']
        df['resistance_distance'] = (df['resistance_level'] - df['close']) / df['close']
        
        # Time features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        df['is_month_end'] = df['date'].dt.is_month_end.astype(int)
        df['is_quarter_end'] = df['date'].dt.is_quarter_end.astype(int)
        
        # Market correlation (enhanced)
        try:
            spy_data = self.get_market_data('SPY')
            if not spy_data.empty:
                spy_data = spy_data.sort_values('date')
                spy_data['spy_return'] = spy_data['close'].pct_change()
                
                df = df.merge(spy_data[['date', 'spy_return']], on='date', how='left')
                df['market_correlation_20d'] = df['price_change_1d'].rolling(20).corr(df['spy_return'])
                df['market_correlation_60d'] = df['price_change_1d'].rolling(60).corr(df['spy_return'])
                df['relative_strength'] = df['price_change_20d'] - df['spy_return'].rolling(20).mean()
            else:
                df['market_correlation_20d'] = 0
                df['market_correlation_60d'] = 0
                df['relative_strength'] = 0
        except Exception as e:
            logger.warning(f"Error calculating market correlation: {e}")
            df['market_correlation_20d'] = 0
            df['market_correlation_60d'] = 0
            df['relative_strength'] = 0
        
        # Sentiment features
        sentiment_data = self.sentiment_analyzer.get_market_sentiment(symbol)
        for key, value in sentiment_data.items():
            df[key] = value
        
        # Advanced derived features
        df['price_volume_divergence'] = df['price_change_1d'] * df['volume_change']
        df['volatility_regime'] = pd.cut(df['volatility_20d'], bins=3, labels=['low', 'medium', 'high']).astype(str)
        df['trend_strength'] = abs(df['trend_20d']) * df['adx'] if 'adx' in df.columns else abs(df['trend_20d'])
        
        # Risk features
        df['var_95'] = df['price_change_1d'].rolling(20).quantile(0.05)
        df['cvar_95'] = df['price_change_1d'].rolling(20).apply(lambda x: x[x <= x.quantile(0.05)].mean())
        
        return df
    
    def get_market_data(self, symbol: str) -> pd.DataFrame:
        """Get market data for correlation analysis."""
        try:
            engine = create_engine("postgresql://loiclinais:password@localhost:5432/aimarkets")
            query = f"SELECT date, close FROM historical_data WHERE symbol = '{symbol}' ORDER BY date"
            return pd.read_sql(query, engine)
        except:
            return pd.DataFrame()

class EnsembleMLSystem:
    """Advanced ML system with ensemble methods."""
    
    def __init__(self):
        self.db_url = "postgresql://loiclinais:password@localhost:5432/aimarkets"
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        self.feature_engineer = AdvancedFeatureEngineer()
        
        # TA-Lib integration
        self.talib_calculator = TALibIndicators()
        
        # Ensemble models
        self.ensemble_classifier = None
        self.ensemble_regressor = None
        self.scalers = {
            'standard': StandardScaler(),
            'robust': RobustScaler(),
            'minmax': MinMaxScaler()
        }
        
        # Feature columns (expanded)
        self.feature_columns = [
            # Price features
            'price_change_1d', 'price_change_5d', 'price_change_20d', 'price_change_60d',
            'volatility_5d', 'volatility_20d', 'volatility_60d',
            
            # Volume features
            'volume_change', 'volume_sma_ratio', 'volume_price_trend',
            
            # Technical indicators
            'rsi_14', 'rsi_21', 'rsi_50', 'macd_line', 'macd_signal', 'macd_histogram',
            'bollinger_position', 'bollinger_width', 'stochastic_k', 'stochastic_d',
            'williams_r', 'cci', 'atr_14', 'atr_21', 'adx', 'obv', 'mfi',
            
            # Momentum and trend
            'momentum_5d', 'momentum_20d', 'momentum_60d',
            'trend_5d', 'trend_20d', 'trend_60d',
            
            # Support/Resistance
            'support_distance', 'resistance_distance',
            
            # Time features
            'day_of_week', 'month', 'quarter', 'is_month_end', 'is_quarter_end',
            
            # Market correlation
            'market_correlation_20d', 'market_correlation_60d', 'relative_strength',
            
            # Sentiment features
            'news_sentiment', 'social_sentiment', 'analyst_sentiment', 'market_fear_greed',
            
            # Advanced features
            'price_volume_divergence', 'trend_strength', 'var_95', 'cvar_95'
        ]
        
        # Recommendation thresholds (enhanced)
        self.recommendation_thresholds = {
            'BUY_STRONG': (0.05, float('inf')),
            'BUY_MODERATE': (0.03, float('inf')),
            'BUY_WEAK': (0.01, float('inf')),
            'HOLD': (-0.01, 0.01),
            'SELL_WEAK': (-float('inf'), -0.01),
            'SELL_MODERATE': (-float('inf'), -0.03),
            'SELL_STRONG': (-float('inf'), -0.05)
        }

    def get_all_symbols(self) -> List[str]:
        """Get all available symbols."""
        query = "SELECT DISTINCT symbol FROM historical_data ORDER BY symbol"
        df = pd.read_sql(query, self.engine)
        return df['symbol'].tolist()

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators using TA-Lib integration."""
        if len(df) < 50:  # Minimum required for most TA-Lib indicators
            logger.warning(f"DataFrame too small ({len(df)} rows) for technical indicators")
            return df
        
        df = df.sort_values('date').reset_index(drop=True)
        
        try:
            # Use our comprehensive TA-Lib integration
            logger.info(f"Calculating technical indicators for {len(df)} rows")
            df = self.talib_calculator.calculate_all_indicators(df)
            
            # Add custom features based on TA-Lib indicators
            df = self.talib_calculator.calculate_custom_features(df)
            
            logger.info(f"Technical indicators calculated successfully. Shape: {df.shape}")
            
        except Exception as e:
            logger.error(f"Error calculating technical indicators with TA-Lib integration: {e}")
            # Fallback to basic indicators if TA-Lib integration fails
            try:
                logger.info("Falling back to basic TA-Lib indicators")
                high = df['high'].values.astype(float)
                low = df['low'].values.astype(float)
                close = df['close'].values.astype(float)
                volume = df['volume'].values.astype(float)
                
                # Basic indicators as fallback
                df['sma_20'] = talib.SMA(close, timeperiod=20)
                df['sma_50'] = talib.SMA(close, timeperiod=50)
                df['ema_20'] = talib.EMA(close, timeperiod=20)
                df['rsi_14'] = talib.RSI(close, timeperiod=14)
                df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(close)
                df['atr_14'] = talib.ATR(high, low, close, timeperiod=14)
                df['obv'] = talib.OBV(close, volume)
                
                logger.info("Basic technical indicators calculated as fallback")
                
            except Exception as fallback_error:
                logger.error(f"Fallback technical indicators also failed: {fallback_error}")
        
        return df

    def create_targets(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create enhanced target variables."""
        df = df.copy()
        
        # Future returns for different horizons
        df['future_return_1d'] = df['close'].shift(-1) / df['close'] - 1
        df['future_return_7d'] = df['close'].shift(-7) / df['close'] - 1
        df['future_return_30d'] = df['close'].shift(-30) / df['close'] - 1
        df['future_return_90d'] = df['close'].shift(-90) / df['close'] - 1
        
        # Enhanced recommendation targets
        def get_enhanced_recommendation(return_1d, return_7d, return_30d, return_90d):
            # Weighted average with more weight on shorter horizons
            avg_return = (return_1d * 0.4 + return_7d * 0.3 + return_30d * 0.2 + return_90d * 0.1)
            
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
            elif avg_return >= -0.05:
                return 'SELL_MODERATE'
            else:
                return 'SELL_STRONG'
        
        df['target_recommendation'] = df.apply(
            lambda row: get_enhanced_recommendation(
                row['future_return_1d'], 
                row['future_return_7d'], 
                row['future_return_30d'],
                row['future_return_90d']
            ), axis=1
        )
        
        return df

    def train_ensemble_models(self, df: pd.DataFrame):
        """Train ensemble models with multiple algorithms."""
        logger.info("Training ensemble ML models...")
        
        # Prepare features and targets
        feature_data = df[self.feature_columns].fillna(0)
        regression_target = df['future_return_7d'].fillna(0)
        classification_target = df['target_recommendation'].fillna('HOLD')
        
        # Remove rows with invalid targets
        valid_mask = ~(regression_target.isna() | classification_target.isna())
        feature_data = feature_data[valid_mask]
        regression_target = regression_target[valid_mask]
        classification_target = classification_target[valid_mask]
        
        if len(feature_data) < 1000:
            logger.warning("Not enough data for ensemble training")
            return
        
        # Split data
        X_train, X_test, y_reg_train, y_reg_test, y_cls_train, y_cls_test = train_test_split(
            feature_data, regression_target, classification_target, 
            test_size=0.2, random_state=42, stratify=classification_target
        )
        
        # Scale features with different scalers
        X_train_scaled = {}
        X_test_scaled = {}
        
        for name, scaler in self.scalers.items():
            X_train_scaled[name] = scaler.fit_transform(X_train)
            X_test_scaled[name] = scaler.transform(X_test)
        
        # Individual models for ensemble
        classifiers = [
            ('rf', RandomForestClassifier(n_estimators=200, max_depth=15, random_state=42)),
            ('et', ExtraTreesClassifier(n_estimators=200, max_depth=15, random_state=42)),
            ('gb', GradientBoostingClassifier(n_estimators=200, max_depth=6, random_state=42)),
            ('ada', AdaBoostClassifier(n_estimators=200, random_state=42)),
            ('svm', SVC(probability=True, random_state=42)),
            ('mlp', MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42))
        ]
        
        regressors = [
            ('rf', RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42)),
            ('et', ExtraTreesRegressor(n_estimators=200, max_depth=15, random_state=42)),
            ('gb', GradientBoostingRegressor(n_estimators=200, max_depth=6, random_state=42)),
            ('ada', AdaBoostRegressor(n_estimators=200, random_state=42)),
            ('svr', SVR()),
            ('mlp', MLPRegressor(hidden_layer_sizes=(100, 50), random_state=42))
        ]
        
        # Create ensemble models
        self.ensemble_classifier = VotingClassifier(
            classifiers, voting='soft'
        )
        
        self.ensemble_regressor = VotingRegressor(
            regressors
        )
        
        # Train ensemble models
        logger.info("Training ensemble classifier...")
        self.ensemble_classifier.fit(X_train_scaled['standard'], y_cls_train)
        
        logger.info("Training ensemble regressor...")
        self.ensemble_regressor.fit(X_train_scaled['standard'], y_reg_train)
        
        # Evaluate models
        cls_pred = self.ensemble_classifier.predict(X_test_scaled['standard'])
        reg_pred = self.ensemble_regressor.predict(X_test_scaled['standard'])
        
        cls_score = accuracy_score(y_cls_test, cls_pred)
        reg_score = r2_score(y_reg_test, reg_pred)
        
        logger.info(f"Ensemble Classification Accuracy: {cls_score:.4f}")
        logger.info(f"Ensemble Regression R² Score: {reg_score:.4f}")
        
        # Save models
        joblib.dump(self.ensemble_classifier, 'ensemble_classification_model.pkl')
        joblib.dump(self.ensemble_regressor, 'ensemble_regression_model.pkl')
        joblib.dump(self.scalers['standard'], 'ensemble_scaler.pkl')

    def generate_advanced_opportunities(self, symbols: List[str], horizons: List[int] = [1, 7, 30]):
        """Generate advanced ML opportunities for all symbols."""
        logger.info(f"Generating advanced opportunities for {len(symbols)} symbols")
        
        opportunities = []
        
        for i, symbol in enumerate(symbols):
            logger.info(f"Processing {symbol} ({i+1}/{len(symbols)})...")
            
            try:
                # Get historical data
                df = self.get_historical_data(symbol)
                if len(df) < 100:
                    logger.warning(f"Not enough data for {symbol}")
                    continue
                
                # Calculate technical indicators
                df = self.calculate_technical_indicators(df)
                
                # Create advanced features
                df = self.feature_engineer.create_advanced_features(df, symbol)
                
                # Get latest data for prediction
                latest_data = df.tail(1).copy()
                
                if latest_data.empty:
                    continue
                
                # Prepare features for prediction
                features = latest_data[self.feature_columns].fillna(0)
                features_scaled = self.scalers['standard'].transform(features)
                
                # Generate predictions for each horizon
                for horizon in horizons:
                    # Predict return
                    predicted_return = self.ensemble_regressor.predict(features_scaled)[0]
                    
                    # Predict recommendation
                    predicted_recommendation = self.ensemble_classifier.predict(features_scaled)[0]
                    
                    # Get confidence (probability of predicted class)
                    confidence_probs = self.ensemble_classifier.predict_proba(features_scaled)[0]
                    confidence_level = max(confidence_probs)
                    
                    # Calculate risk score (enhanced)
                    risk_score = latest_data['volatility_20d'].iloc[0] if not pd.isna(latest_data['volatility_20d'].iloc[0]) else 0.1
                    
                    # Clean data for JSON serialization
                    tech_data = latest_data.iloc[0].to_dict()
                    feature_data = features.iloc[0].to_dict()
                    
                    # Replace NaN values and convert for JSON serialization
                    for key, value in tech_data.items():
                        if pd.isna(value):
                            tech_data[key] = None
                        elif isinstance(value, pd.Timestamp):
                            tech_data[key] = value.isoformat()
                        elif hasattr(value, 'item'):
                            tech_data[key] = value.item()
                    
                    for key, value in feature_data.items():
                        if pd.isna(value):
                            feature_data[key] = None
                        elif hasattr(value, 'item'):
                            feature_data[key] = value.item()
                    
                    # Create opportunity
                    opportunity = {
                        'symbol': symbol,
                        'date': latest_data['date'].iloc[0].date(),
                        'horizon_days': horizon,
                        'recommendation': predicted_recommendation,
                        'confidence_level': float(confidence_level),
                        'potential_return': float(predicted_return),
                        'risk_score': float(risk_score),
                        'ml_model_name': 'advanced_ensemble_v1',
                        'ml_model_version': '2.0',
                        'technical_indicators': json.dumps(tech_data),
                        'ml_features': json.dumps(feature_data)
                    }
                    
                    opportunities.append(opportunity)
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        # Store opportunities in database
        self.store_opportunities(opportunities)
        
        logger.info(f"Generated {len(opportunities)} advanced opportunities")

    def get_historical_data(self, symbol: str) -> pd.DataFrame:
        """Get historical data for a symbol."""
        query = """
        SELECT symbol, date, open, high, low, close, volume
        FROM historical_data
        WHERE symbol = %s
        ORDER BY date
        """
        df = pd.read_sql(query, self.engine, params=(symbol,))
        
        # Convert to proper types
        df['date'] = pd.to_datetime(df['date'])
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        return df

    def store_opportunities(self, opportunities: List[Dict]):
        """Store opportunities in the database."""
        if not opportunities:
            return
        
        with self.Session() as session:
            try:
                # Clear existing opportunities
                session.execute(text("DELETE FROM ml_opportunities"))
                
                # Insert new opportunities
                for opp in opportunities:
                    session.execute(text("""
                        INSERT INTO ml_opportunities 
                        (symbol, date, horizon_days, recommendation, confidence_level, 
                         potential_return, risk_score, ml_model_name, ml_model_version, 
                         technical_indicators, ml_features)
                        VALUES 
                        (:symbol, :date, :horizon_days, :recommendation, :confidence_level,
                         :potential_return, :risk_score, :ml_model_name, :ml_model_version,
                         :technical_indicators, :ml_features)
                    """), opp)
                
                session.commit()
                logger.info(f"Stored {len(opportunities)} opportunities in database")
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error storing opportunities: {e}")

    def run_advanced_pipeline(self):
        """Run the complete advanced ML pipeline."""
        logger.info("Starting Advanced ML System Pipeline...")
        
        # Get all symbols
        symbols = self.get_all_symbols()
        logger.info(f"Found {len(symbols)} symbols")
        
        # Use all symbols for training
        logger.info("Loading historical data for training...")
        all_data = []
        
        for i, symbol in enumerate(symbols):
            logger.info(f"Processing {symbol} for training ({i+1}/{len(symbols)})...")
            df = self.get_historical_data(symbol)
            if len(df) >= 100:
                df = self.calculate_technical_indicators(df)
                df = self.feature_engineer.create_advanced_features(df, symbol)
                df = self.create_targets(df)
                df['symbol'] = symbol
                all_data.append(df)
        
        if not all_data:
            logger.error("No data available for training")
            return
        
        # Combine all data
        combined_data = pd.concat(all_data, ignore_index=True)
        logger.info(f"Combined dataset shape: {combined_data.shape}")
        
        # Train ensemble models
        self.train_ensemble_models(combined_data)
        
        # Generate opportunities for all symbols
        self.generate_advanced_opportunities(symbols, horizons=[1, 7, 30])
        
        logger.info("Advanced ML System Pipeline completed!")

def main():
    """Main function to run the advanced ML system."""
    system = EnsembleMLSystem()
    system.run_advanced_pipeline()

if __name__ == "__main__":
    main()
