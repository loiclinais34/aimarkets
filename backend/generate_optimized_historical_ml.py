#!/usr/bin/env python3
"""
Optimized Historical ML Opportunities Generator
This script generates ML opportunities for all symbols from January 1, 2025 onwards
with optimized performance and memory management.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import json
import logging
from typing import List, Dict, Any
import warnings
import gc
warnings.filterwarnings('ignore')

# Database imports
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ML imports
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, VotingClassifier, VotingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, SVR
from sklearn.neural_network import MLPClassifier, MLPRegressor
import joblib

# Technical analysis
import talib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimized_historical_ml.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class OptimizedHistoricalMLGenerator:
    """Optimized generator for historical ML opportunities."""
    
    def __init__(self):
        self.db_url = "postgresql://loiclinais:password@localhost:5432/aimarkets"
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Feature columns (simplified for performance)
        self.feature_columns = [
            'price_change_1d', 'price_change_5d', 'price_change_20d',
            'volatility_20d', 'volume_change', 'volume_sma_ratio',
            'rsi_14', 'macd_line', 'macd_signal', 'bollinger_position',
            'stochastic_k', 'williams_r', 'atr_14', 'adx',
            'momentum_5d', 'momentum_20d', 'trend_5d', 'trend_20d',
            'support_distance', 'resistance_distance',
            'day_of_week', 'month', 'quarter',
            'news_sentiment', 'social_sentiment', 'analyst_sentiment'
        ]
        
        # Start date and horizons
        self.start_date = date(2025, 1, 1)
        self.horizons = [1, 7, 30]
        
        # Performance tracking
        self.stats = {
            'symbols_processed': 0,
            'opportunities_generated': 0,
            'errors': 0,
            'start_time': datetime.now()
        }

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

    def calculate_technical_indicators_fast(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators efficiently."""
        if len(df) < 50:
            return df
        
        df = df.sort_values('date').reset_index(drop=True)
        
        high = df['high'].values.astype(float)
        low = df['low'].values.astype(float)
        close = df['close'].values.astype(float)
        volume = df['volume'].values.astype(float)
        
        try:
            # Essential indicators only
            df['rsi_14'] = talib.RSI(close, timeperiod=14)
            macd, macd_signal, _ = talib.MACD(close)
            df['macd_line'] = macd
            df['macd_signal'] = macd_signal
            
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close)
            df['bollinger_position'] = (close - bb_lower) / (bb_upper - bb_lower)
            
            df['stochastic_k'], _ = talib.STOCH(high, low, close)
            df['williams_r'] = talib.WILLR(high, low, close)
            df['atr_14'] = talib.ATR(high, low, close, timeperiod=14)
            df['adx'] = talib.ADX(high, low, close, timeperiod=14)
            
        except Exception as e:
            logger.warning(f"Error calculating technical indicators: {e}")
        
        return df

    def create_features_fast(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Create features efficiently."""
        df = df.copy()
        
        # Basic features
        df['price_change_1d'] = df['close'].pct_change(1)
        df['price_change_5d'] = df['close'].pct_change(5)
        df['price_change_20d'] = df['close'].pct_change(20)
        df['volatility_20d'] = df['price_change_1d'].rolling(20).std()
        
        df['volume_change'] = df['volume'].pct_change(1)
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_sma_ratio'] = df['volume'] / df['volume_sma_20']
        
        df['momentum_5d'] = df['close'] / df['close'].shift(5) - 1
        df['momentum_20d'] = df['close'] / df['close'].shift(20) - 1
        df['trend_5d'] = (df['close'] - df['close'].rolling(5).mean()) / df['close'].rolling(5).mean()
        df['trend_20d'] = (df['close'] - df['close'].rolling(20).mean()) / df['close'].rolling(20).mean()
        
        df['support_level'] = df['low'].rolling(20).min()
        df['resistance_level'] = df['high'].rolling(20).max()
        df['support_distance'] = (df['close'] - df['support_level']) / df['close']
        df['resistance_distance'] = (df['resistance_level'] - df['close']) / df['close']
        
        # Time features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        
        # Simulated sentiment (for performance)
        df['news_sentiment'] = 0.5
        df['social_sentiment'] = 0.5
        df['analyst_sentiment'] = 0.5
        
        return df

    def create_targets_fast(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create target variables efficiently."""
        df = df.copy()
        
        df['future_return_1d'] = df['close'].shift(-1) / df['close'] - 1
        df['future_return_7d'] = df['close'].shift(-7) / df['close'] - 1
        df['future_return_30d'] = df['close'].shift(-30) / df['close'] - 1
        
        # Simple recommendation logic
        def get_recommendation(return_1d, return_7d, return_30d):
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

    def train_fast_models(self, symbol: str, training_data: pd.DataFrame):
        """Train fast models for a symbol."""
        models = {}
        scalers = {}
        
        available_features = [col for col in self.feature_columns if col in training_data.columns]
        feature_data = training_data[available_features].fillna(0)
        
        for horizon in self.horizons:
            target_col = f'future_return_{horizon}d'
            if target_col not in training_data.columns:
                continue
            
            regression_target = training_data[target_col].fillna(0)
            classification_target = training_data['target_recommendation'].fillna('HOLD')
            
            valid_mask = ~(regression_target.isna() | classification_target.isna())
            X = feature_data[valid_mask]
            y_reg = regression_target[valid_mask]
            y_cls = classification_target[valid_mask]
            
            if len(X) < 50:
                continue
            
            # Fast models
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            classifier = RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42)
            regressor = RandomForestRegressor(n_estimators=50, max_depth=8, random_state=42)
            
            classifier.fit(X_scaled, y_cls)
            regressor.fit(X_scaled, y_reg)
            
            models[horizon] = {
                'classifier': classifier,
                'regressor': regressor,
                'features': available_features
            }
            scalers[horizon] = scaler
        
        return models, scalers

    def generate_opportunities_batch(self, symbol: str, dates: List[date], models: Dict, scalers: Dict) -> List[Dict]:
        """Generate opportunities for a batch of dates."""
        opportunities = []
        
        try:
            # Get data for the entire date range
            start_date = min(dates) - timedelta(days=365)
            end_date = max(dates)
            
            df = self.get_historical_data_range(symbol, start_date, end_date)
            if len(df) < 100:
                return opportunities
            
            # Calculate features once
            df = self.calculate_technical_indicators_fast(df)
            df = self.create_features_fast(df, symbol)
            
            # Generate opportunities for each date
            for target_date in dates:
                # Get data up to target date
                df_filtered = df[df['date'].dt.date <= target_date]
                if len(df_filtered) < 50:
                    continue
                
                latest_data = df_filtered.tail(1).copy()
                
                for horizon in self.horizons:
                    if horizon not in models:
                        continue
                    
                    model_data = models[horizon]
                    scaler = scalers[horizon]
                    
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
                    
                    # Create opportunity
                    opportunity = {
                        'symbol': symbol,
                        'date': target_date,
                        'horizon_days': horizon,
                        'recommendation': predicted_recommendation,
                        'confidence_level': float(confidence_level),
                        'potential_return': float(predicted_return),
                        'risk_score': float(risk_score),
                        'ml_model_name': 'optimized_historical_v1',
                        'ml_model_version': '1.0',
                        'technical_indicators': json.dumps({}),
                        'ml_features': json.dumps({})
                    }
                    
                    opportunities.append(opportunity)
                    
        except Exception as e:
            logger.error(f"Error generating opportunities for {symbol}: {e}")
            self.stats['errors'] += 1
        
        return opportunities

    def store_opportunities_batch(self, opportunities: List[Dict]):
        """Store opportunities in batches."""
        if not opportunities:
            return
        
        with self.Session() as session:
            try:
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
                
                self.stats['opportunities_generated'] += len(opportunities)
                logger.info(f"Stored {len(opportunities)} opportunities")
                
            except Exception as e:
                session.rollback()
                logger.error(f"Error storing opportunities: {e}")

    def generate_historical_opportunities_optimized(self):
        """Generate historical opportunities with optimized performance."""
        logger.info("🚀 Starting Optimized Historical ML Opportunities Generation...")
        
        # Get all symbols
        symbols = self.get_all_symbols()
        logger.info(f"Found {len(symbols)} symbols")
        
        # Get date range
        today = date.today()
        logger.info(f"Generating opportunities from {self.start_date} to {today}")
        
        # Process symbols in batches
        batch_size = 10
        date_batch_size = 30  # Process 30 days at a time
        
        for i in range(0, len(symbols), batch_size):
            symbol_batch = symbols[i:i + batch_size]
            logger.info(f"Processing symbol batch {i//batch_size + 1}/{(len(symbols)-1)//batch_size + 1}: {symbol_batch}")
            
            for symbol in symbol_batch:
                try:
                    logger.info(f"Processing {symbol}...")
                    
                    # Get training data
                    training_end = self.start_date + timedelta(days=180)
                    training_data = self.get_historical_data_range(symbol, self.start_date, training_end)
                    
                    if len(training_data) < 100:
                        logger.warning(f"Not enough training data for {symbol}")
                        continue
                    
                    # Calculate features and targets
                    training_data = self.calculate_technical_indicators_fast(training_data)
                    training_data = self.create_features_fast(training_data, symbol)
                    training_data = self.create_targets_fast(training_data)
                    
                    # Train models
                    models, scalers = self.train_fast_models(symbol, training_data)
                    
                    if not models:
                        logger.warning(f"No models trained for {symbol}")
                        continue
                    
                    # Generate opportunities in date batches
                    current_date = self.start_date
                    while current_date <= today:
                        date_batch = []
                        for j in range(date_batch_size):
                            if current_date <= today:
                                date_batch.append(current_date)
                                current_date += timedelta(days=1)
                            else:
                                break
                        
                        if date_batch:
                            opportunities = self.generate_opportunities_batch(symbol, date_batch, models, scalers)
                            if opportunities:
                                self.store_opportunities_batch(opportunities)
                    
                    self.stats['symbols_processed'] += 1
                    
                    # Memory cleanup
                    del models, scalers, training_data
                    gc.collect()
                    
                except Exception as e:
                    logger.error(f"Error processing {symbol}: {e}")
                    self.stats['errors'] += 1
                    continue
            
            # Progress update
            elapsed = datetime.now() - self.stats['start_time']
            logger.info(f"Progress: {self.stats['symbols_processed']}/{len(symbols)} symbols, "
                       f"{self.stats['opportunities_generated']} opportunities, "
                       f"{self.stats['errors']} errors, "
                       f"Elapsed: {elapsed}")
        
        # Final statistics
        elapsed = datetime.now() - self.stats['start_time']
        logger.info("✅ Optimized Historical ML Opportunities Generation completed!")
        logger.info(f"Final Statistics:")
        logger.info(f"  Symbols processed: {self.stats['symbols_processed']}")
        logger.info(f"  Opportunities generated: {self.stats['opportunities_generated']}")
        logger.info(f"  Errors: {self.stats['errors']}")
        logger.info(f"  Total time: {elapsed}")
        
        # Calculate expected vs actual
        expected_max = len(symbols) * ((today - self.start_date).days + 1) * len(self.horizons)
        logger.info(f"  Expected maximum: {expected_max}")
        logger.info(f"  Coverage: {self.stats['opportunities_generated']/expected_max*100:.1f}%")

def main():
    """Main function to run optimized historical ML generation."""
    generator = OptimizedHistoricalMLGenerator()
    generator.generate_historical_opportunities_optimized()

if __name__ == "__main__":
    main()
