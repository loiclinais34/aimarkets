#!/usr/bin/env python3
"""
Historical ML Opportunities Generator
This script generates ML opportunities for all symbols from January 1, 2025 onwards
for comprehensive backtesting database.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

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
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
from sklearn.linear_model import LogisticRegression, Ridge, Lasso
from sklearn.svm import SVC, SVR
from sklearn.neural_network import MLPClassifier, MLPRegressor
import joblib

# Technical analysis
import talib

# Sentiment analysis
from textblob import TextBlob

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('historical_ml_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HistoricalMLGenerator:
    """Generator for historical ML opportunities."""
    
    def __init__(self):
        self.db_url = "postgresql://loiclinais:password@localhost:5432/aimarkets"
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Feature columns (same as advanced system)
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
        
        # Models and scalers
        self.models = {}
        self.scalers = {}
        
        # Start date for historical generation
        self.start_date = date(2025, 1, 1)
        
        # Horizons
        self.horizons = [1, 7, 30]

    def get_all_symbols(self) -> List[str]:
        """Get all available symbols."""
        query = "SELECT DISTINCT symbol FROM historical_data ORDER BY symbol"
        df = pd.read_sql(query, self.engine)
        return df['symbol'].tolist()

    def get_historical_data_range(self, symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
        """Get historical data for a symbol within date range."""
        query = """
        SELECT symbol, date, open, high, low, close, volume
        FROM historical_data
        WHERE symbol = %s AND date >= %s AND date <= %s
        ORDER BY date
        """
        df = pd.read_sql(query, self.engine, params=(symbol, start_date, end_date))
        
        # Convert to proper types
        df['date'] = pd.to_datetime(df['date'])
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        return df

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive technical indicators."""
        if len(df) < 100:
            return df
        
        df = df.sort_values('date').reset_index(drop=True)
        
        high = df['high'].values.astype(float)
        low = df['low'].values.astype(float)
        close = df['close'].values.astype(float)
        volume = df['volume'].values.astype(float)
        
        try:
            # Moving averages
            df['sma_5'] = talib.SMA(close, timeperiod=5)
            df['sma_10'] = talib.SMA(close, timeperiod=10)
            df['sma_20'] = talib.SMA(close, timeperiod=20)
            df['sma_50'] = talib.SMA(close, timeperiod=50)
            df['sma_200'] = talib.SMA(close, timeperiod=200)
            
            df['ema_5'] = talib.EMA(close, timeperiod=5)
            df['ema_10'] = talib.EMA(close, timeperiod=10)
            df['ema_20'] = talib.EMA(close, timeperiod=20)
            df['ema_50'] = talib.EMA(close, timeperiod=50)
            df['ema_200'] = talib.EMA(close, timeperiod=200)
            
            # Momentum indicators
            df['rsi_14'] = talib.RSI(close, timeperiod=14)
            df['rsi_21'] = talib.RSI(close, timeperiod=21)
            df['rsi_50'] = talib.RSI(close, timeperiod=50)
            
            macd, macd_signal, macd_hist = talib.MACD(close)
            df['macd_line'] = macd
            df['macd_signal'] = macd_signal
            df['macd_histogram'] = macd_hist
            
            # Volatility indicators
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close)
            df['bollinger_upper'] = bb_upper
            df['bollinger_middle'] = bb_middle
            df['bollinger_lower'] = bb_lower
            df['bollinger_width'] = (bb_upper - bb_lower) / bb_middle
            df['bollinger_position'] = (close - bb_lower) / (bb_upper - bb_lower)
            
            df['atr_14'] = talib.ATR(high, low, close, timeperiod=14)
            df['atr_21'] = talib.ATR(high, low, close, timeperiod=21)
            
            # Volume indicators
            df['volume_sma_20'] = talib.SMA(volume, timeperiod=20)
            df['obv'] = talib.OBV(close, volume)
            df['mfi'] = talib.MFI(high, low, close, volume, timeperiod=14)
            
            # Additional indicators
            df['stochastic_k'], df['stochastic_d'] = talib.STOCH(high, low, close)
            df['williams_r'] = talib.WILLR(high, low, close)
            df['cci'] = talib.CCI(high, low, close)
            df['adx'] = talib.ADX(high, low, close, timeperiod=14)
            
            # Support/Resistance
            df['support_level'] = df['low'].rolling(20).min()
            df['resistance_level'] = df['high'].rolling(20).max()
            df['pivot_point'] = (df['high'] + df['low'] + df['close']) / 3
            
        except Exception as e:
            logger.warning(f"Error calculating technical indicators: {e}")
        
        return df

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
        
        # Market correlation (simplified)
        df['market_correlation_20d'] = 0
        df['market_correlation_60d'] = 0
        df['relative_strength'] = 0
        
        # Sentiment features (simulated)
        df['news_sentiment'] = np.random.normal(0.5, 0.2)
        df['social_sentiment'] = np.random.normal(0.5, 0.15)
        df['analyst_sentiment'] = np.random.normal(0.5, 0.1)
        df['market_fear_greed'] = np.random.normal(0.5, 0.25)
        
        # Normalize sentiment to 0-1 range
        for col in ['news_sentiment', 'social_sentiment', 'analyst_sentiment', 'market_fear_greed']:
            df[col] = df[col].clip(0, 1)
        
        # Advanced derived features
        df['price_volume_divergence'] = df['price_change_1d'] * df['volume_change']
        df['volatility_regime'] = pd.cut(df['volatility_20d'], bins=3, labels=['low', 'medium', 'high']).astype(str)
        df['trend_strength'] = abs(df['trend_20d']) * df.get('adx', 1)
        
        # Risk features
        df['var_95'] = df['price_change_1d'].rolling(20).quantile(0.05)
        df['cvar_95'] = df['price_change_1d'].rolling(20).apply(lambda x: x[x <= x.quantile(0.05)].mean())
        
        return df

    def create_targets(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create target variables for different horizons."""
        df = df.copy()
        
        # Future returns for different horizons
        df['future_return_1d'] = df['close'].shift(-1) / df['close'] - 1
        df['future_return_7d'] = df['close'].shift(-7) / df['close'] - 1
        df['future_return_30d'] = df['close'].shift(-30) / df['close'] - 1
        
        # Enhanced recommendation targets
        def get_recommendation(return_1d, return_7d, return_30d):
            # Weighted average with more weight on shorter horizons
            avg_return = (return_1d * 0.4 + return_7d * 0.3 + return_30d * 0.3)
            
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
            lambda row: get_recommendation(
                row['future_return_1d'], 
                row['future_return_7d'], 
                row['future_return_30d']
            ), axis=1
        )
        
        return df

    def train_models_for_symbol(self, symbol: str, training_data: pd.DataFrame):
        """Train models for a specific symbol."""
        logger.info(f"Training models for {symbol}...")
        
        # Prepare features and targets
        available_features = [col for col in self.feature_columns if col in training_data.columns]
        feature_data = training_data[available_features].fillna(0)
        
        # Train models for each horizon
        for horizon in self.horizons:
            target_col = f'future_return_{horizon}d'
            if target_col not in training_data.columns:
                continue
            
            regression_target = training_data[target_col].fillna(0)
            classification_target = training_data['target_recommendation'].fillna('HOLD')
            
            # Remove rows with invalid targets
            valid_mask = ~(regression_target.isna() | classification_target.isna())
            X = feature_data[valid_mask]
            y_reg = regression_target[valid_mask]
            y_cls = classification_target[valid_mask]
            
            if len(X) < 100:
                logger.warning(f"Not enough data for {symbol} horizon {horizon}d")
                continue
            
            # Scale features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Train ensemble models
            classifier = VotingClassifier([
                ('rf', RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)),
                ('gb', GradientBoostingClassifier(n_estimators=100, max_depth=6, random_state=42)),
                ('svm', SVC(probability=True, random_state=42))
            ], voting='soft')
            
            regressor = VotingRegressor([
                ('rf', RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)),
                ('gb', GradientBoostingRegressor(n_estimators=100, max_depth=6, random_state=42)),
                ('svr', SVR())
            ])
            
            # Train models
            classifier.fit(X_scaled, y_cls)
            regressor.fit(X_scaled, y_reg)
            
            # Store models
            model_key = f"{symbol}_{horizon}d"
            self.models[model_key] = {
                'classifier': classifier,
                'regressor': regressor,
                'features': available_features
            }
            self.scalers[model_key] = scaler
            
            logger.info(f"Trained models for {symbol} {horizon}d")

    def generate_opportunities_for_date(self, symbol: str, target_date: date) -> List[Dict]:
        """Generate opportunities for a specific symbol and date."""
        opportunities = []
        
        try:
            # Get data up to target date (for features)
            end_date = target_date
            start_date = end_date - timedelta(days=365)  # Get 1 year of data for features
            
            df = self.get_historical_data_range(symbol, start_date, end_date)
            if len(df) < 100:
                return opportunities
            
            # Calculate features
            df = self.calculate_technical_indicators(df)
            df = self.create_advanced_features(df, symbol)
            
            # Get latest data for prediction
            latest_data = df.tail(1).copy()
            if latest_data.empty:
                return opportunities
            
            # Generate opportunities for each horizon
            for horizon in self.horizons:
                model_key = f"{symbol}_{horizon}d"
                
                if model_key not in self.models:
                    continue
                
                model_data = self.models[model_key]
                scaler = self.scalers[model_key]
                
                # Prepare features
                features = latest_data[model_data['features']].fillna(0)
                features_scaled = scaler.transform(features)
                
                # Predict
                predicted_return = model_data['regressor'].predict(features_scaled)[0]
                predicted_recommendation = model_data['classifier'].predict(features_scaled)[0]
                
                # Get confidence
                confidence_probs = model_data['classifier'].predict_proba(features_scaled)[0]
                confidence_level = max(confidence_probs)
                
                # Calculate risk score
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
                    'date': target_date,
                    'horizon_days': horizon,
                    'recommendation': predicted_recommendation,
                    'confidence_level': float(confidence_level),
                    'potential_return': float(predicted_return),
                    'risk_score': float(risk_score),
                    'ml_model_name': 'historical_ensemble_v1',
                    'ml_model_version': '1.0',
                    'technical_indicators': json.dumps(tech_data),
                    'ml_features': json.dumps(feature_data)
                }
                
                opportunities.append(opportunity)
                
        except Exception as e:
            logger.error(f"Error generating opportunities for {symbol} on {target_date}: {e}")
        
        return opportunities

    def store_opportunities_batch(self, opportunities: List[Dict]):
        """Store opportunities in batches for better performance."""
        if not opportunities:
            return
        
        with self.Session() as session:
            try:
                # Insert opportunities in batches
                batch_size = 1000
                for i in range(0, len(opportunities), batch_size):
                    batch = opportunities[i:i + batch_size]
                    
                    for opp in batch:
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
                    logger.info(f"Stored batch {i//batch_size + 1}: {len(batch)} opportunities")
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error storing opportunities: {e}")

    def generate_historical_opportunities(self):
        """Generate historical opportunities for all symbols from start date."""
        logger.info("🚀 Starting Historical ML Opportunities Generation...")
        
        # Get all symbols
        symbols = self.get_all_symbols()
        logger.info(f"Found {len(symbols)} symbols")
        
        # Get date range
        today = date.today()
        logger.info(f"Generating opportunities from {self.start_date} to {today}")
        
        # Generate date list
        date_list = []
        current_date = self.start_date
        while current_date <= today:
            date_list.append(current_date)
            current_date += timedelta(days=1)
        
        logger.info(f"Will generate opportunities for {len(date_list)} dates")
        
        total_opportunities = 0
        
        # Process each symbol
        for i, symbol in enumerate(symbols):
            logger.info(f"Processing {symbol} ({i+1}/{len(symbols)})...")
            
            try:
                # Get training data for this symbol (first 6 months)
                training_end = self.start_date + timedelta(days=180)
                training_data = self.get_historical_data_range(symbol, self.start_date, training_end)
                
                if len(training_data) < 100:
                    logger.warning(f"Not enough training data for {symbol}")
                    continue
                
                # Calculate features for training
                training_data = self.calculate_technical_indicators(training_data)
                training_data = self.create_advanced_features(training_data, symbol)
                training_data = self.create_targets(training_data)
                
                # Train models for this symbol
                self.train_models_for_symbol(symbol, training_data)
                
                # Generate opportunities for each date
                symbol_opportunities = []
                
                for target_date in date_list:
                    opportunities = self.generate_opportunities_for_date(symbol, target_date)
                    symbol_opportunities.extend(opportunities)
                
                # Store opportunities for this symbol
                if symbol_opportunities:
                    self.store_opportunities_batch(symbol_opportunities)
                    total_opportunities += len(symbol_opportunities)
                    logger.info(f"Generated {len(symbol_opportunities)} opportunities for {symbol}")
                
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        logger.info(f"✅ Historical ML Opportunities Generation completed!")
        logger.info(f"Total opportunities generated: {total_opportunities}")
        logger.info(f"Expected maximum: {len(symbols)} symbols × {len(date_list)} dates × {len(self.horizons)} horizons = {len(symbols) * len(date_list) * len(self.horizons)}")

def main():
    """Main function to run historical ML generation."""
    generator = HistoricalMLGenerator()
    generator.generate_historical_opportunities()

if __name__ == "__main__":
    main()
