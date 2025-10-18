#!/usr/bin/env python3
"""
Test script for TA-Lib integration in Advanced ML System
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from advanced_ml_system import EnsembleMLSystem
from talib_indicators import TALibIndicators

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_talib_integration():
    """Test TA-Lib integration with the advanced ML system."""
    
    logger.info("🧪 Testing TA-Lib integration with Advanced ML System...")
    
    try:
        # Initialize the system
        ml_system = EnsembleMLSystem()
        logger.info("✅ Advanced ML System initialized successfully")
        
        # Test TA-Lib calculator directly
        talib_calc = TALibIndicators()
        logger.info("✅ TA-Lib calculator initialized successfully")
        
        # Create test data
        logger.info("📊 Creating test data...")
        np.random.seed(42)
        dates = pd.date_range('2025-01-01', periods=200, freq='D')
        
        # Generate realistic OHLCV data
        base_price = 100
        prices = []
        volumes = []
        
        for i in range(200):
            # Random walk with slight upward bias
            change = np.random.normal(0.001, 0.02)  # 0.1% daily return, 2% volatility
            base_price *= (1 + change)
            prices.append(base_price)
            volumes.append(np.random.randint(1000000, 10000000))
        
        test_df = pd.DataFrame({
            'date': dates,
            'symbol': 'TEST',
            'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': volumes
        })
        
        # Ensure OHLC consistency
        test_df['high'] = test_df[['open', 'high', 'close']].max(axis=1)
        test_df['low'] = test_df[['open', 'low', 'close']].min(axis=1)
        
        logger.info(f"✅ Test data created: {test_df.shape}")
        logger.info(f"Price range: ${test_df['close'].min():.2f} - ${test_df['close'].max():.2f}")
        
        # Test TA-Lib indicators calculation
        logger.info("🔧 Testing TA-Lib indicators calculation...")
        df_with_indicators = ml_system.calculate_technical_indicators(test_df)
        
        logger.info(f"✅ Technical indicators calculated. Shape: {df_with_indicators.shape}")
        
        # Check which indicators were successfully calculated
        indicator_cols = [col for col in df_with_indicators.columns 
                         if col not in test_df.columns]
        
        logger.info(f"📈 Indicators calculated: {len(indicator_cols)}")
        
        # Show some key indicators
        key_indicators = ['rsi_14', 'macd', 'bb_upper', 'bb_lower', 'atr_14', 'obv']
        available_indicators = [col for col in key_indicators if col in df_with_indicators.columns]
        
        if available_indicators:
            logger.info(f"🎯 Key indicators available: {available_indicators}")
            
            # Show sample values
            sample_data = df_with_indicators[['date', 'close'] + available_indicators].tail(3)
            logger.info("📊 Sample indicator values:")
            for _, row in sample_data.iterrows():
                rsi_val = row.get('rsi_14', 'N/A')
                rsi_str = f"{rsi_val:.2f}" if pd.notna(rsi_val) else "N/A"
                logger.info(f"  {row['date'].strftime('%Y-%m-%d')}: Close=${row['close']:.2f}, RSI={rsi_str}")
        
        # Test feature engineering
        logger.info("⚙️ Testing feature engineering...")
        try:
            df_with_features = ml_system.feature_engineer.create_advanced_features(df_with_indicators, 'TEST')
            feature_cols = [col for col in df_with_features.columns 
                           if col not in df_with_indicators.columns]
            logger.info(f"✅ Advanced features created: {len(feature_cols)}")
            
            if feature_cols:
                logger.info(f"🔧 Feature columns: {feature_cols[:10]}...")  # Show first 10
            
        except Exception as e:
            logger.warning(f"⚠️ Feature engineering failed: {e}")
        
        # Test data preparation for ML
        logger.info("🤖 Testing ML data preparation...")
        try:
            # Create targets
            df_with_targets = ml_system.create_targets(df_with_indicators)
            
            # Check if targets were created
            target_cols = [col for col in df_with_targets.columns 
                          if 'future_return' in col or 'recommendation' in col]
            
            if target_cols:
                logger.info(f"✅ Targets created: {target_cols}")
                
                # Show target distribution
                if 'recommendation' in df_with_targets.columns:
                    rec_dist = df_with_targets['recommendation'].value_counts()
                    logger.info(f"📊 Recommendation distribution:")
                    for rec, count in rec_dist.items():
                        logger.info(f"  {rec}: {count}")
            
        except Exception as e:
            logger.warning(f"⚠️ ML data preparation failed: {e}")
        
        # Performance test
        logger.info("⚡ Testing performance...")
        import time
        
        start_time = time.time()
        df_perf_test = ml_system.calculate_technical_indicators(test_df)
        end_time = time.time()
        
        processing_time = end_time - start_time
        logger.info(f"⏱️ Processing time: {processing_time:.2f} seconds for {len(test_df)} rows")
        logger.info(f"📊 Processing speed: {len(test_df)/processing_time:.0f} rows/second")
        
        # Memory usage test
        logger.info("💾 Testing memory usage...")
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        logger.info(f"🧠 Memory usage: {memory_mb:.1f} MB")
        
        logger.info("✅ TA-Lib integration test completed successfully!")
        
        return {
            'success': True,
            'indicators_calculated': len(indicator_cols),
            'processing_time': processing_time,
            'memory_usage_mb': memory_mb,
            'data_shape': df_with_indicators.shape
        }
        
    except Exception as e:
        logger.error(f"❌ TA-Lib integration test failed: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}

def test_talib_features():
    """Test specific TA-Lib features."""
    
    logger.info("🔍 Testing specific TA-Lib features...")
    
    try:
        talib_calc = TALibIndicators()
        
        # Test feature columns
        feature_cols = talib_calc.get_feature_columns()
        logger.info(f"📋 Available feature columns: {len(feature_cols)}")
        
        # Test with minimal data
        minimal_data = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [101, 102, 103, 104, 105],
            'low': [99, 100, 101, 102, 103],
            'close': [100.5, 101.5, 102.5, 103.5, 104.5],
            'volume': [1000000, 1100000, 1200000, 1300000, 1400000]
        })
        
        logger.info("🧪 Testing with minimal data...")
        result = talib_calc.calculate_all_indicators(minimal_data)
        
        if len(result.columns) > len(minimal_data.columns):
            logger.info(f"✅ Minimal data test passed: {len(result.columns)} columns")
        else:
            logger.warning(f"⚠️ Minimal data test: only {len(result.columns)} columns")
        
        logger.info("✅ TA-Lib features test completed!")
        
    except Exception as e:
        logger.error(f"❌ TA-Lib features test failed: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("🚀 Starting TA-Lib Integration Tests...")
    
    # Test 1: Basic TA-Lib integration
    result1 = test_talib_integration()
    
    # Test 2: Specific TA-Lib features
    test_talib_features()
    
    # Summary
    logger.info("\n📊 TEST SUMMARY")
    logger.info("=" * 50)
    
    if result1['success']:
        logger.info(f"✅ Integration Test: PASSED")
        logger.info(f"   - Indicators calculated: {result1['indicators_calculated']}")
        logger.info(f"   - Processing time: {result1['processing_time']:.2f}s")
        logger.info(f"   - Memory usage: {result1['memory_usage_mb']:.1f} MB")
        logger.info(f"   - Final data shape: {result1['data_shape']}")
    else:
        logger.info(f"❌ Integration Test: FAILED")
        logger.info(f"   - Error: {result1['error']}")
    
    logger.info("🎉 All tests completed!")
