#!/usr/bin/env python3
"""
Test Historical ML Opportunities Generator
This script tests the historical generation with a small subset before full deployment.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generate_historical_ml_opportunities import HistoricalMLGenerator
import logging
from datetime import date, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_historical_generation():
    """Test historical generation with a small subset."""
    logger.info("🧪 Testing Historical ML Opportunities Generation...")
    
    generator = HistoricalMLGenerator()
    
    # Test with first 3 symbols
    symbols = generator.get_all_symbols()[:3]
    logger.info(f"Testing with symbols: {symbols}")
    
    # Test with first 10 days of January 2025
    start_date = date(2025, 1, 1)
    test_dates = [start_date + timedelta(days=i) for i in range(10)]
    logger.info(f"Testing with dates: {test_dates[0]} to {test_dates[-1]}")
    
    total_opportunities = 0
    
    for symbol in symbols:
        logger.info(f"Processing {symbol}...")
        
        try:
            # Get training data
            training_end = start_date + timedelta(days=180)
            training_data = generator.get_historical_data_range(symbol, start_date, training_end)
            
            if len(training_data) < 100:
                logger.warning(f"Not enough training data for {symbol}")
                continue
            
            logger.info(f"Training data shape: {training_data.shape}")
            
            # Calculate features
            training_data = generator.calculate_technical_indicators(training_data)
            training_data = generator.create_advanced_features(training_data, symbol)
            training_data = generator.create_targets(training_data)
            
            logger.info(f"Enhanced training data shape: {training_data.shape}")
            
            # Train models
            generator.train_models_for_symbol(symbol, training_data)
            
            # Generate opportunities for test dates
            symbol_opportunities = []
            
            for target_date in test_dates:
                opportunities = generator.generate_opportunities_for_date(symbol, target_date)
                symbol_opportunities.extend(opportunities)
            
            logger.info(f"Generated {len(symbol_opportunities)} opportunities for {symbol}")
            total_opportunities += len(symbol_opportunities)
            
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
            continue
    
    logger.info(f"✅ Test completed! Generated {total_opportunities} opportunities")
    logger.info(f"Expected: {len(symbols)} symbols × {len(test_dates)} dates × 3 horizons = {len(symbols) * len(test_dates) * 3}")
    
    return total_opportunities

if __name__ == "__main__":
    test_historical_generation()
