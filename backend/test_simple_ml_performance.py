#!/usr/bin/env python3
"""
Simple ML Performance Test
This script tests the ML performance analysis with minimal data to identify the issue.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.endpoints.analysis.ml_performance_analyzer import MLPerformanceAnalyzer
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simple_ml_performance():
    """Test ML performance analysis with minimal data."""
    logger.info("🔍 Testing Simple ML Performance Analysis...")
    
    try:
        analyzer = MLPerformanceAnalyzer()
        
        # Get test opportunities specifically
        opportunities = analyzer.get_ml_opportunities(limit=50)
        logger.info(f"Found {len(opportunities)} opportunities")
        
        # Filter to only test opportunities with historical dates
        test_opportunities = opportunities[opportunities['ml_model_name'] == 'test_ml_v1']
        logger.info(f"Found {len(test_opportunities)} test opportunities")
        
        if len(test_opportunities) == 0:
            logger.error("No test opportunities found!")
            return
        
        opportunities = test_opportunities
        
        # Calculate returns
        opportunities_with_returns = analyzer.calculate_actual_returns(opportunities)
        logger.info(f"Calculated returns for {len(opportunities_with_returns)} opportunities")
        
        if len(opportunities_with_returns) == 0:
            logger.error("No opportunities with calculated returns!")
            return
        
        # Calculate success
        opportunities_with_returns['is_successful'] = opportunities_with_returns.apply(
            lambda row: analyzer.calculate_opportunity_success(row.to_dict())[0], axis=1
        )
        
        # Test overall metrics
        overall_metrics = analyzer.calculate_performance_metrics(opportunities_with_returns)
        logger.info(f"Overall metrics: {overall_metrics}")
        
        # Test JSON serialization
        try:
            json_str = json.dumps(overall_metrics, default=str)
            logger.info("JSON serialization successful")
        except Exception as e:
            logger.error(f"JSON serialization failed: {e}")
            return
        
        # Test recommendation metrics
        recommendation_metrics = analyzer.calculate_performance_by_recommendation(opportunities_with_returns)
        logger.info(f"Recommendation metrics: {list(recommendation_metrics.keys())}")
        
        # Test JSON serialization of recommendation metrics
        try:
            json_str = json.dumps(recommendation_metrics, default=str)
            logger.info("Recommendation metrics JSON serialization successful")
        except Exception as e:
            logger.error(f"Recommendation metrics JSON serialization failed: {e}")
            return
        
        # Test horizon metrics
        horizon_metrics = analyzer.calculate_performance_by_horizon(opportunities_with_returns)
        logger.info(f"Horizon metrics: {list(horizon_metrics.keys())}")
        
        # Test JSON serialization of horizon metrics
        try:
            json_str = json.dumps(horizon_metrics, default=str)
            logger.info("Horizon metrics JSON serialization successful")
        except Exception as e:
            logger.error(f"Horizon metrics JSON serialization failed: {e}")
            return
        
        logger.info("✅ All tests passed!")
        
    except Exception as e:
        logger.error(f"Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simple_ml_performance()
