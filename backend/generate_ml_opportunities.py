#!/usr/bin/env python3
"""
Generate ML opportunities using sophisticated models and real historical data.
This script will:
1. Recalculate technical indicators for all historical data
2. Train/retrain ML models with the latest data
3. Generate opportunities for 1d, 7d, and 30d horizons
4. Store results in ml_opportunities table
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import logging
from typing import List, Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Database imports
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ML imports
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, mean_squared_error, r2_score
import joblib

# Technical analysis
import talib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_opportunities_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MLOpportunityGenerator:
    def __init__(self):
        """Initialize the ML opportunity generator."""
        self.db_url = "postgresql://loiclinais:password@localhost:5432/aimarkets"
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # ML models
        self.classification_model = None
        self.regression_model = None
        self.scaler = StandardScaler()
        
        # Feature columns
        self.feature_columns = [
            'price_change_1d', 'price_change_5d', 'price_change_20d',
            'volatility_5d', 'volatility_20d', 'volume_change',
            'volume_sma_ratio', 'rsi_normalized', 'macd_normalized',
            'bollinger_position', 'momentum_5d', 'momentum_20d',
            'trend_5d', 'trend_20d', 'support_distance', 'resistance_distance',
            'day_of_week', 'month', 'quarter', 'market_correlation'
        ]
        
        # Recommendation thresholds
        self.recommendation_thresholds = {
            'BUY_STRONG': (0.03, float('inf')),
            'BUY_MODERATE': (0.02, float('inf')),
            'BUY_WEAK': (0.01, float('inf')),
            'HOLD': (-0.01, 0.01),
            'SELL_WEAK': (-float('inf'), -0.01),
            'SELL_MODERATE': (-float('inf'), -0.02),
            'SELL_STRONG': (-float('inf'), -0.03)
        }

    def get_historical_data(self, symbol: str = None) -> pd.DataFrame:
        """Get historical data for all symbols or a specific symbol."""
        query = """
        SELECT symbol, date, open, high, low, close, volume
        FROM historical_data
        ORDER BY symbol, date
        """
        
        if symbol:
            query = """
            SELECT symbol, date, open, high, low, close, volume
            FROM historical_data
            WHERE symbol = %s
            ORDER BY date
            """
            df = pd.read_sql(query, self.engine, params=(symbol,))
        else:
            df = pd.read_sql(query, self.engine)
        
        # Convert to proper types
        df['date'] = pd.to_datetime(df['date'])
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        return df

    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators for a single symbol."""
        if len(df) < 50:  # Need enough data for indicators
            return df
        
        # Sort by date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Convert to numpy arrays for TA-Lib
        high = df['high'].values.astype(float)
        low = df['low'].values.astype(float)
        close = df['close'].values.astype(float)
        volume = df['volume'].values.astype(float)
        
        try:
            # Price-based indicators
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
            
            df['atr_14'] = talib.ATR(high, low, close, timeperiod=14)
            df['volatility_20'] = talib.STDDEV(close, timeperiod=20) / close
            
            # Volume indicators
            df['volume_sma_20'] = talib.SMA(volume, timeperiod=20)
            df['volume_ratio'] = volume / df['volume_sma_20']
            df['obv'] = talib.OBV(close, volume)
            df['vwap'] = (high + low + close) / 3  # Simplified VWAP
            
            # Additional indicators
            df['stochastic_k'], df['stochastic_d'] = talib.STOCH(high, low, close)
            df['williams_r'] = talib.WILLR(high, low, close)
            df['cci'] = talib.CCI(high, low, close)
            df['roc'] = talib.ROC(close, timeperiod=10)
            
            # Support/Resistance (simplified)
            df['support_level'] = df['low'].rolling(window=20).min()
            df['resistance_level'] = df['high'].rolling(window=20).max()
            df['pivot_point'] = (df['high'] + df['low'] + df['close']) / 3
            
        except Exception as e:
            logger.warning(f"Error calculating technical indicators: {e}")
        
        return df

    def create_ml_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create ML features from technical indicators."""
        df = df.copy()
        
        # Price changes
        df['price_change_1d'] = df['close'].pct_change(1)
        df['price_change_5d'] = df['close'].pct_change(5)
        df['price_change_20d'] = df['close'].pct_change(20)
        
        # Volatility
        df['volatility_5d'] = df['price_change_1d'].rolling(5).std()
        df['volatility_20d'] = df['price_change_1d'].rolling(20).std()
        
        # Volume features
        df['volume_change'] = df['volume'].pct_change(1)
        df['volume_sma_ratio'] = df['volume'] / df['volume_sma_20']
        
        # Normalized indicators
        df['rsi_normalized'] = (df['rsi_14'] - 50) / 50
        df['macd_normalized'] = df['macd_line'] / df['close']
        df['bollinger_position'] = (df['close'] - df['bollinger_lower']) / (df['bollinger_upper'] - df['bollinger_lower'])
        
        # Momentum
        df['momentum_5d'] = df['close'] / df['close'].shift(5) - 1
        df['momentum_20d'] = df['close'] / df['close'].shift(20) - 1
        
        # Trend
        df['trend_5d'] = (df['close'] - df['sma_5']) / df['sma_5']
        df['trend_20d'] = (df['close'] - df['sma_20']) / df['sma_20']
        
        # Support/Resistance distances
        df['support_distance'] = (df['close'] - df['support_level']) / df['close']
        df['resistance_distance'] = (df['resistance_level'] - df['close']) / df['close']
        
        # Time features
        df['day_of_week'] = df['date'].dt.dayofweek
        df['month'] = df['date'].dt.month
        df['quarter'] = df['date'].dt.quarter
        
        # Market correlation (simplified - using SPY as proxy)
        try:
            spy_data = self.get_historical_data('SPY')
            spy_data = spy_data.sort_values('date')
            spy_data['spy_return'] = spy_data['close'].pct_change()
            
            # Merge with main data
            df = df.merge(spy_data[['date', 'spy_return']], on='date', how='left')
            df['market_correlation'] = df['price_change_1d'].rolling(20).corr(df['spy_return'])
        except:
            df['market_correlation'] = 0
        
        return df

    def create_targets(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create target variables for ML models."""
        df = df.copy()
        
        # Future returns
        df['future_return_1d'] = df['close'].shift(-1) / df['close'] - 1
        df['future_return_7d'] = df['close'].shift(-7) / df['close'] - 1
        df['future_return_30d'] = df['close'].shift(-30) / df['close'] - 1
        
        # Recommendation targets based on future returns
        def get_recommendation(return_1d, return_7d, return_30d):
            avg_return = (return_1d + return_7d + return_30d) / 3
            
            if avg_return >= 0.03:
                return 'BUY_STRONG'
            elif avg_return >= 0.02:
                return 'BUY_MODERATE'
            elif avg_return >= 0.01:
                return 'BUY_WEAK'
            elif avg_return >= -0.01:
                return 'HOLD'
            elif avg_return >= -0.02:
                return 'SELL_WEAK'
            elif avg_return >= -0.03:
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

    def train_models(self, df: pd.DataFrame):
        """Train ML models with the prepared data."""
        logger.info("Training ML models...")
        
        # Prepare features and targets
        feature_data = df[self.feature_columns].fillna(0)
        regression_target = df['future_return_7d'].fillna(0)  # Use 7-day return for regression
        classification_target = df['target_recommendation'].fillna('HOLD')
        
        # Remove rows with invalid targets
        valid_mask = ~(regression_target.isna() | classification_target.isna())
        feature_data = feature_data[valid_mask]
        regression_target = regression_target[valid_mask]
        classification_target = classification_target[valid_mask]
        
        if len(feature_data) < 100:
            logger.warning("Not enough data for training")
            return
        
        # Split data
        X_train, X_test, y_reg_train, y_reg_test, y_cls_train, y_cls_test = train_test_split(
            feature_data, regression_target, classification_target, 
            test_size=0.2, random_state=42
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train regression model
        self.regression_model = RandomForestRegressor(
            n_estimators=200,
            max_depth=15,
            random_state=42,
            n_jobs=-1
        )
        self.regression_model.fit(X_train_scaled, y_reg_train)
        
        # Train classification model
        self.classification_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            random_state=42,
            n_jobs=-1
        )
        self.classification_model.fit(X_train_scaled, y_cls_train)
        
        # Evaluate models
        reg_pred = self.regression_model.predict(X_test_scaled)
        cls_pred = self.classification_model.predict(X_test_scaled)
        
        reg_score = r2_score(y_reg_test, reg_pred)
        cls_score = accuracy_score(y_cls_test, cls_pred)
        
        logger.info(f"Regression R² Score: {reg_score:.4f}")
        logger.info(f"Classification Accuracy: {cls_score:.4f}")
        
        # Save models
        joblib.dump(self.regression_model, 'ml_regression_model.pkl')
        joblib.dump(self.classification_model, 'ml_classification_model.pkl')
        joblib.dump(self.scaler, 'ml_scaler.pkl')

    def generate_opportunities(self, symbols: List[str], horizons: List[int] = [1, 7, 30]):
        """Generate ML opportunities for given symbols and horizons."""
        logger.info(f"Generating opportunities for {len(symbols)} symbols and horizons {horizons}")
        
        opportunities = []
        
        for symbol in symbols:
            logger.info(f"Processing {symbol}...")
            
            try:
                # Get historical data
                df = self.get_historical_data(symbol)
                if len(df) < 100:
                    logger.warning(f"Not enough data for {symbol}")
                    continue
                
                # Calculate technical indicators
                df = self.calculate_technical_indicators(df)
                
                # Create ML features
                df = self.create_ml_features(df)
                
                # Get latest data for prediction
                latest_data = df.tail(1).copy()
                
                if latest_data.empty:
                    continue
                
                # Prepare features for prediction
                features = latest_data[self.feature_columns].fillna(0)
                features_scaled = self.scaler.transform(features)
                
                # Generate predictions for each horizon
                for horizon in horizons:
                    # Predict return
                    predicted_return = self.regression_model.predict(features_scaled)[0]
                    
                    # Predict recommendation
                    predicted_recommendation = self.classification_model.predict(features_scaled)[0]
                    
                    # Get confidence (probability of predicted class)
                    confidence_probs = self.classification_model.predict_proba(features_scaled)[0]
                    confidence_level = max(confidence_probs)
                    
                    # Calculate risk score (volatility)
                    risk_score = latest_data['volatility_20'].iloc[0] if not pd.isna(latest_data['volatility_20'].iloc[0]) else 0.1
                    
                    # Clean data for JSON serialization
                    tech_data = latest_data.iloc[0].to_dict()
                    feature_data = features.iloc[0].to_dict()
                    
                    # Replace NaN values and convert Timestamps for JSON serialization
                    for key, value in tech_data.items():
                        if pd.isna(value):
                            tech_data[key] = None
                        elif isinstance(value, pd.Timestamp):
                            tech_data[key] = value.isoformat()
                        elif hasattr(value, 'item'):  # numpy types
                            tech_data[key] = value.item()
                    
                    for key, value in feature_data.items():
                        if pd.isna(value):
                            feature_data[key] = None
                        elif hasattr(value, 'item'):  # numpy types
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
                        'ml_model_name': 'sophisticated_ml_v1',
                        'ml_model_version': '1.0',
                        'technical_indicators': json.dumps(tech_data),
                        'ml_features': json.dumps(feature_data)
                    }
                    
                    opportunities.append(opportunity)
                    
            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                continue
        
        # Store opportunities in database
        self.store_opportunities(opportunities)
        
        logger.info(f"Generated {len(opportunities)} opportunities")

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

    def run_full_pipeline(self):
        """Run the complete ML opportunity generation pipeline."""
        logger.info("Starting ML opportunity generation pipeline...")
        
        # Get all symbols
        symbols_query = "SELECT DISTINCT symbol FROM historical_data ORDER BY symbol"
        symbols_df = pd.read_sql(symbols_query, self.engine)
        symbols = symbols_df['symbol'].tolist()
        
        logger.info(f"Found {len(symbols)} symbols")
        
        # Use a subset for initial testing (first 20 symbols)
        test_symbols = symbols[:20]
        logger.info(f"Using {len(test_symbols)} symbols for testing")
        
        # Get historical data for training
        logger.info("Loading historical data for training...")
        all_data = []
        
        for symbol in test_symbols:
            df = self.get_historical_data(symbol)
            if len(df) >= 100:
                df = self.calculate_technical_indicators(df)
                df = self.create_ml_features(df)
                df = self.create_targets(df)
                df['symbol'] = symbol
                all_data.append(df)
        
        if not all_data:
            logger.error("No data available for training")
            return
        
        # Combine all data
        combined_data = pd.concat(all_data, ignore_index=True)
        logger.info(f"Combined dataset shape: {combined_data.shape}")
        
        # Train models
        self.train_models(combined_data)
        
        # Generate opportunities
        self.generate_opportunities(test_symbols, horizons=[1, 7, 30])
        
        logger.info("ML opportunity generation pipeline completed!")

def main():
    """Main function to run the ML opportunity generation."""
    generator = MLOpportunityGenerator()
    generator.run_full_pipeline()

if __name__ == "__main__":
    main()
