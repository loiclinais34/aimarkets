#!/usr/bin/env python3
"""
Simplified Advanced ML Opportunities Generator
This script generates opportunities using available features only.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from advanced_ml_system import EnsembleMLSystem
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_simplified_opportunities():
    """Generate opportunities using simplified feature set."""
    logger.info("🚀 Generating Simplified Advanced ML Opportunities...")
    
    system = EnsembleMLSystem()
    
    # Get all symbols
    symbols = system.get_all_symbols()
    logger.info(f"Total symbols available: {len(symbols)}")
    
    # Use first 10 symbols for quick test
    test_symbols = symbols[:10]
    logger.info(f"Testing with {len(test_symbols)} symbols: {test_symbols}")
    
    # Load and process data for training
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
    
    if not all_data:
        logger.error("No data available for training")
        return
    
    # Combine data
    combined_data = pd.concat(all_data, ignore_index=True)
    logger.info(f"Combined dataset shape: {combined_data.shape}")
    
    # Check available features
    available_features = [col for col in system.feature_columns if col in combined_data.columns]
    logger.info(f"Available features: {len(available_features)}/{len(system.feature_columns)}")
    logger.info(f"Missing features: {set(system.feature_columns) - set(available_features)}")
    
    # Update feature columns to only use available ones
    system.feature_columns = available_features
    logger.info(f"Using {len(system.feature_columns)} features for training")
    
    # Train ensemble models
    logger.info("Training ensemble models...")
    system.train_ensemble_models(combined_data)
    
    # Generate opportunities for all symbols
    logger.info("Generating opportunities...")
    system.generate_advanced_opportunities(symbols, horizons=[1, 7, 30])
    
    logger.info("✅ Simplified Advanced ML Opportunities Generation completed!")

def check_opportunities():
    """Check the generated opportunities."""
    logger.info("📊 Checking Generated Opportunities...")
    
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(
            host="localhost",
            user="loiclinais",
            password="password",
            database="aimarkets"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Check total count
        cursor.execute("SELECT COUNT(*) as count FROM ml_opportunities")
        total_count = cursor.fetchone()['count']
        logger.info(f"Total opportunities: {total_count}")
        
        # Check by recommendation
        cursor.execute("""
            SELECT recommendation, COUNT(*) as count 
            FROM ml_opportunities 
            GROUP BY recommendation 
            ORDER BY count DESC
        """)
        recommendations = cursor.fetchall()
        
        logger.info("Recommendation distribution:")
        for rec in recommendations:
            logger.info(f"  {rec['recommendation']}: {rec['count']}")
        
        # Check by horizon
        cursor.execute("""
            SELECT horizon_days, COUNT(*) as count 
            FROM ml_opportunities 
            GROUP BY horizon_days 
            ORDER BY horizon_days
        """)
        horizons = cursor.fetchall()
        
        logger.info("Horizon distribution:")
        for horizon in horizons:
            logger.info(f"  {horizon['horizon_days']} days: {horizon['count']}")
        
        # Check confidence stats
        cursor.execute("""
            SELECT AVG(confidence_level) as avg_confidence,
                   MIN(confidence_level) as min_confidence,
                   MAX(confidence_level) as max_confidence,
                   STDDEV(confidence_level) as std_confidence
            FROM ml_opportunities
        """)
        confidence_stats = cursor.fetchone()
        
        logger.info("Confidence statistics:")
        logger.info(f"  Average: {confidence_stats['avg_confidence']:.3f}")
        logger.info(f"  Min: {confidence_stats['min_confidence']:.3f}")
        logger.info(f"  Max: {confidence_stats['max_confidence']:.3f}")
        logger.info(f"  Std Dev: {confidence_stats['std_confidence']:.3f}")
        
        # Check sample opportunities
        cursor.execute("""
            SELECT symbol, recommendation, confidence_level, potential_return, risk_score
            FROM ml_opportunities 
            ORDER BY confidence_level DESC 
            LIMIT 5
        """)
        top_opportunities = cursor.fetchall()
        
        logger.info("Top 5 opportunities by confidence:")
        for opp in top_opportunities:
            logger.info(f"  {opp['symbol']}: {opp['recommendation']} "
                       f"(conf: {opp['confidence_level']:.3f}, "
                       f"return: {opp['potential_return']:.3f}, "
                       f"risk: {opp['risk_score']:.3f})")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error checking opportunities: {e}")

if __name__ == "__main__":
    generate_simplified_opportunities()
    check_opportunities()
