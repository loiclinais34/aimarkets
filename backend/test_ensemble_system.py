#!/usr/bin/env python3
"""
Test script for Ensemble ML System
This script tests the ensemble methods and advanced features.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from advanced_ml_system import EnsembleMLSystem, SentimentAnalyzer, AdvancedFeatureEngineer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ensemble_features():
    """Test the ensemble ML features."""
    logger.info("🧪 Testing Ensemble ML Features...")
    
    # Test sentiment analyzer
    logger.info("Testing Sentiment Analysis...")
    sentiment_analyzer = SentimentAnalyzer()
    
    # Test text sentiment
    test_text = "The stock market is performing exceptionally well with strong bullish momentum"
    sentiment_result = sentiment_analyzer.analyze_text_sentiment(test_text)
    logger.info(f"Text sentiment result: {sentiment_result}")
    
    # Test market sentiment
    market_sentiment = sentiment_analyzer.get_market_sentiment("AAPL")
    logger.info(f"Market sentiment for AAPL: {market_sentiment}")
    
    # Test feature engineer
    logger.info("Testing Advanced Feature Engineering...")
    feature_engineer = AdvancedFeatureEngineer()
    
    # Create sample data
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    sample_data = pd.DataFrame({
        'date': dates,
        'open': np.random.uniform(100, 200, 100),
        'high': np.random.uniform(150, 250, 100),
        'low': np.random.uniform(50, 150, 100),
        'close': np.random.uniform(100, 200, 100),
        'volume': np.random.uniform(1000000, 10000000, 100)
    })
    
    # Test feature creation
    enhanced_data = feature_engineer.create_advanced_features(sample_data, "TEST")
    logger.info(f"Enhanced data shape: {enhanced_data.shape}")
    logger.info(f"New features added: {len(enhanced_data.columns) - len(sample_data.columns)}")
    
    # Test ensemble system
    logger.info("Testing Ensemble ML System...")
    system = EnsembleMLSystem()
    
    # Test symbol retrieval
    symbols = system.get_all_symbols()
    logger.info(f"Total symbols available: {len(symbols)}")
    
    # Test data loading for one symbol
    test_symbol = symbols[0]
    df = system.get_historical_data(test_symbol)
    logger.info(f"Loaded {len(df)} rows for {test_symbol}")
    
    # Test technical indicators
    df_with_indicators = system.calculate_technical_indicators(df)
    logger.info(f"Added technical indicators: {len(df_with_indicators.columns) - len(df.columns)} new columns")
    
    # Test target creation
    df_with_targets = system.create_targets(df_with_indicators)
    logger.info(f"Added targets: {len(df_with_targets.columns) - len(df_with_indicators.columns)} new columns")
    
    # Check target distribution
    if 'target_recommendation' in df_with_targets.columns:
        target_dist = df_with_targets['target_recommendation'].value_counts()
        logger.info(f"Target recommendation distribution:\n{target_dist}")
    
    logger.info("✅ Ensemble ML Features Test completed successfully!")
    return True

def test_model_performance():
    """Test model performance with sample data."""
    logger.info("🎯 Testing Model Performance...")
    
    system = EnsembleMLSystem()
    
    # Get sample data for training
    symbols = system.get_all_symbols()[:5]  # Use first 5 symbols for quick test
    all_data = []
    
    for symbol in symbols:
        df = system.get_historical_data(symbol)
        if len(df) >= 100:
            df = system.calculate_technical_indicators(df)
            df = system.feature_engineer.create_advanced_features(df, symbol)
            df = system.create_targets(df)
            df['symbol'] = symbol
            all_data.append(df)
    
    if not all_data:
        logger.error("No data available for testing")
        return False
    
    # Combine data
    combined_data = pd.concat(all_data, ignore_index=True)
    logger.info(f"Combined dataset shape: {combined_data.shape}")
    
    # Check feature availability
    available_features = [col for col in system.feature_columns if col in combined_data.columns]
    logger.info(f"Available features: {len(available_features)}/{len(system.feature_columns)}")
    
    # Test ensemble training (quick version)
    logger.info("Training quick ensemble model...")
    
    # Prepare features and targets
    feature_data = combined_data[available_features].fillna(0)
    regression_target = combined_data['future_return_7d'].fillna(0)
    classification_target = combined_data['target_recommendation'].fillna('HOLD')
    
    # Remove rows with invalid targets
    valid_mask = ~(regression_target.isna() | classification_target.isna())
    feature_data = feature_data[valid_mask]
    regression_target = regression_target[valid_mask]
    classification_target = classification_target[valid_mask]
    
    if len(feature_data) < 100:
        logger.warning("Not enough data for ensemble training")
        return False
    
    # Quick ensemble test
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, r2_score
    
    X_train, X_test, y_reg_train, y_reg_test, y_cls_train, y_cls_test = train_test_split(
        feature_data, regression_target, classification_target, 
        test_size=0.2, random_state=42
    )
    
    # Train simple ensemble
    classifier = RandomForestClassifier(n_estimators=50, random_state=42)
    regressor = RandomForestRegressor(n_estimators=50, random_state=42)
    
    classifier.fit(X_train, y_cls_train)
    regressor.fit(X_train, y_reg_train)
    
    # Evaluate
    cls_pred = classifier.predict(X_test)
    reg_pred = regressor.predict(X_test)
    
    cls_score = accuracy_score(y_cls_test, cls_pred)
    reg_score = r2_score(y_reg_test, reg_pred)
    
    logger.info(f"Quick Ensemble Classification Accuracy: {cls_score:.4f}")
    logger.info(f"Quick Ensemble Regression R² Score: {reg_score:.4f}")
    
    # Check prediction distribution
    cls_dist = pd.Series(cls_pred).value_counts()
    logger.info(f"Prediction distribution:\n{cls_dist}")
    
    logger.info("✅ Model Performance Test completed successfully!")
    return True

if __name__ == "__main__":
    test_ensemble_features()
    test_model_performance()
