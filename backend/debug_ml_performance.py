#!/usr/bin/env python3
"""
Debug ML Performance API
This script debugs the ML performance analysis to identify issues.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.endpoints.analysis.ml_performance_analyzer import MLPerformanceAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_ml_performance():
    """Debug ML performance analysis."""
    logger.info("🔍 Debugging ML Performance Analysis...")
    
    try:
        analyzer = MLPerformanceAnalyzer()
        
        # Test 1: Get ML opportunities
        logger.info("Test 1: Getting ML opportunities...")
        opportunities = analyzer.get_ml_opportunities(limit=100)
        logger.info(f"Found {len(opportunities)} opportunities")
        
        if len(opportunities) == 0:
            logger.error("No opportunities found!")
            return
        
        # Test 2: Calculate actual returns
        logger.info("Test 2: Calculating actual returns...")
        opportunities_with_returns = analyzer.calculate_actual_returns(opportunities)
        logger.info(f"Calculated returns for {len(opportunities_with_returns)} opportunities")
        
        if len(opportunities_with_returns) == 0:
            logger.error("No opportunities with calculated returns!")
            return
        
        # Test 3: Calculate performance metrics
        logger.info("Test 3: Calculating performance metrics...")
        opportunities_with_returns['is_successful'] = opportunities_with_returns.apply(
            lambda row: analyzer.calculate_opportunity_success(row.to_dict())[0], axis=1
        )
        
        overall_metrics = analyzer.calculate_performance_metrics(opportunities_with_returns)
        logger.info(f"Overall metrics calculated: {overall_metrics}")
        
        # Test 4: Calculate by recommendation
        logger.info("Test 4: Calculating by recommendation...")
        recommendation_metrics = analyzer.calculate_performance_by_recommendation(opportunities_with_returns)
        logger.info(f"Recommendation metrics calculated for {len(recommendation_metrics)} types")
        
        logger.info("✅ All tests passed!")
        
    except Exception as e:
        logger.error(f"Error during debugging: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_ml_performance()
