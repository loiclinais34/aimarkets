#!/usr/bin/env python3
"""
Test script for the Advanced ML System
This script tests the system with a subset of symbols before full deployment.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from advanced_ml_system import EnsembleMLSystem
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_advanced_system():
    """Test the advanced ML system with a subset of symbols."""
    logger.info("Starting Advanced ML System Test...")
    
    system = EnsembleMLSystem()
    
    # Get all symbols
    all_symbols = system.get_all_symbols()
    logger.info(f"Total symbols available: {len(all_symbols)}")
    
    # Test with first 10 symbols
    test_symbols = all_symbols[:10]
    logger.info(f"Testing with symbols: {test_symbols}")
    
    # Load and process data for test symbols
    all_data = []
    
    for symbol in test_symbols:
        logger.info(f"Processing {symbol}...")
        df = system.get_historical_data(symbol)
        if len(df) >= 100:
            df = system.calculate_technical_indicators(df)
            df = system.feature_engineer.create_advanced_features(df, symbol)
            df = system.create_targets(df)
            df['symbol'] = symbol
            all_data.append(df)
            logger.info(f"Processed {symbol}: {len(df)} rows")
    
    if not all_data:
        logger.error("No data available for testing")
        return
    
    # Combine data
    combined_data = pd.concat(all_data, ignore_index=True)
    logger.info(f"Combined test dataset shape: {combined_data.shape}")
    
    # Check feature columns
    available_features = [col for col in system.feature_columns if col in combined_data.columns]
    logger.info(f"Available features: {len(available_features)}/{len(system.feature_columns)}")
    
    # Test feature engineering
    logger.info("Testing feature engineering...")
    sample_symbol = test_symbols[0]
    sample_df = system.get_historical_data(sample_symbol)
    sample_df = system.calculate_technical_indicators(sample_df)
    sample_df = system.feature_engineer.create_advanced_features(sample_df, sample_symbol)
    
    logger.info(f"Sample data shape after feature engineering: {sample_df.shape}")
    logger.info(f"Sample features: {list(sample_df.columns)[:10]}...")
    
    # Test sentiment analysis
    logger.info("Testing sentiment analysis...")
    sentiment = system.feature_engineer.sentiment_analyzer.get_market_sentiment(sample_symbol)
    logger.info(f"Sample sentiment: {sentiment}")
    
    logger.info("Advanced ML System Test completed successfully!")
    return True

if __name__ == "__main__":
    test_advanced_system()
