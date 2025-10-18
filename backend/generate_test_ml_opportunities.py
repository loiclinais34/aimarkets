#!/usr/bin/env python3
"""
Generate Test ML Opportunities
This script generates ML opportunities with historical dates for testing the performance analysis.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import json
import logging
from typing import List, Dict, Any

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Database imports
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_test_ml_opportunities():
    """Generate test ML opportunities with historical dates."""
    logger.info("🚀 Generating Test ML Opportunities...")
    
    db_url = "postgresql://loiclinais:password@localhost:5432/aimarkets"
    engine = create_engine(db_url)
    
    # Get some symbols from historical_data
    symbols_query = """
    SELECT DISTINCT symbol 
    FROM historical_data 
    WHERE date >= '2025-01-01' 
    ORDER BY symbol 
    LIMIT 20
    """
    symbols_df = pd.read_sql(symbols_query, engine)
    symbols = symbols_df['symbol'].tolist()
    
    logger.info(f"Using {len(symbols)} symbols: {symbols[:5]}...")
    
    # Generate opportunities for the last 60 days (to ensure we have future data)
    end_date = date.today() - timedelta(days=30)  # 30 days ago
    start_date = end_date - timedelta(days=60)    # 90 days ago
    
    opportunities = []
    
    for symbol in symbols:
        for current_date in pd.date_range(start_date, end_date, freq='D'):
            current_date = current_date.date()
            
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
            
            # Generate opportunities for each horizon
            for horizon in [1, 7, 30]:
                # Generate random recommendation
                recommendations = ['BUY_STRONG', 'BUY_MODERATE', 'BUY_WEAK', 'HOLD', 'SELL_WEAK', 'SELL_MODERATE', 'SELL_STRONG']
                recommendation = np.random.choice(recommendations)
                
                # Generate confidence level
                confidence_level = np.random.uniform(0.3, 0.9)
                
                # Generate potential return
                if 'BUY' in recommendation:
                    potential_return = np.random.uniform(0.01, 0.15)
                elif 'SELL' in recommendation:
                    potential_return = np.random.uniform(-0.15, -0.01)
                else:
                    potential_return = np.random.uniform(-0.02, 0.02)
                
                # Generate risk score
                risk_score = np.random.uniform(0.1, 0.8)
                
                # Create technical indicators (simplified)
                technical_indicators = {
                    'sma_20': np.random.uniform(50, 200),
                    'rsi_14': np.random.uniform(20, 80),
                    'macd_line': np.random.uniform(-2, 2),
                    'bollinger_upper': np.random.uniform(100, 300),
                    'bollinger_lower': np.random.uniform(50, 150),
                    'volume_ratio': np.random.uniform(0.5, 2.0)
                }
                
                # Create ML features (simplified)
                ml_features = {
                    'price_momentum': np.random.uniform(-0.1, 0.1),
                    'volume_trend': np.random.uniform(-0.2, 0.2),
                    'volatility': np.random.uniform(0.1, 0.5),
                    'market_correlation': np.random.uniform(0.3, 0.9)
                }
                
                opportunity = {
                    'symbol': symbol,
                    'date': current_date,
                    'horizon_days': horizon,
                    'recommendation': recommendation,
                    'confidence_level': confidence_level,
                    'potential_return': potential_return,
                    'risk_score': risk_score,
                    'ml_model_name': 'test_ml_v1',
                    'ml_model_version': '1.0',
                    'technical_indicators': json.dumps(technical_indicators),
                    'ml_features': json.dumps(ml_features),
                    'created_at': datetime.now()
                }
                
                opportunities.append(opportunity)
    
    logger.info(f"Generated {len(opportunities)} test opportunities")
    
    # Insert into database
    if opportunities:
        opportunities_df = pd.DataFrame(opportunities)
        
        # Insert in batches
        batch_size = 1000
        for i in range(0, len(opportunities_df), batch_size):
            batch = opportunities_df.iloc[i:i+batch_size]
            batch.to_sql('ml_opportunities', engine, if_exists='append', index=False, method='multi')
            logger.info(f"Inserted batch {i//batch_size + 1}/{(len(opportunities_df)-1)//batch_size + 1}")
    
    logger.info("✅ Test ML Opportunities generation completed!")
    
    # Verify insertion
    count_query = "SELECT COUNT(*) FROM ml_opportunities WHERE ml_model_name = 'test_ml_v1'"
    count = pd.read_sql(count_query, engine).iloc[0, 0]
    logger.info(f"Total test opportunities in database: {count}")

if __name__ == "__main__":
    generate_test_ml_opportunities()
