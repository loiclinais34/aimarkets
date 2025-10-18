#!/usr/bin/env python3
"""
ML Performance Analysis for Historical Data
This script analyzes ML opportunities that have sufficient historical data for backtesting.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api.endpoints.analysis.ml_performance_analyzer import MLPerformanceAnalyzer
import logging
import pandas as pd
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_ml_performance_with_sufficient_data():
    """Analyze ML performance focusing on opportunities with sufficient historical data."""
    logger.info("🔍 Analyzing ML Performance with Sufficient Historical Data...")
    
    analyzer = MLPerformanceAnalyzer()
    
    # Get all ML opportunities
    all_opportunities = analyzer.get_ml_opportunities()
    logger.info(f"Total ML opportunities: {len(all_opportunities):,}")
    
    # Filter opportunities that are old enough to have historical data
    # We need opportunities from at least 30 days ago to have sufficient data
    cutoff_date = datetime.now().date() - timedelta(days=30)
    historical_opportunities = all_opportunities[all_opportunities['date'].dt.date <= cutoff_date]
    
    logger.info(f"Opportunities with sufficient historical data: {len(historical_opportunities):,}")
    
    if len(historical_opportunities) == 0:
        logger.warning("No opportunities with sufficient historical data found!")
        return
    
    # Analyze performance
    logger.info("Analyzing performance...")
    results = analyzer.analyze_ml_performance(limit=len(historical_opportunities))
    
    if 'error' in results:
        logger.error(f"Analysis failed: {results['error']}")
        return
    
    # Generate and display report
    report = analyzer.generate_performance_report(results)
    print(report)
    
    # Display key insights
    overall = results['overall_performance']
    logger.info(f"\n🎯 Key Performance Insights:")
    logger.info(f"  Success Rate: {overall['success_rate']:.1%}")
    logger.info(f"  Mean Return: {overall['mean_return']:.3f}")
    logger.info(f"  Sharpe Ratio: {overall['sharpe_ratio']:.3f}")
    logger.info(f"  Win Rate: {overall['win_rate']:.1%}")
    logger.info(f"  Profit Factor: {overall['profit_factor']:.2f}")
    logger.info(f"  Max Drawdown: {overall['max_drawdown']:.3f}")
    
    # Display recommendation performance
    logger.info(f"\n📊 Recommendation Performance Analysis:")
    for rec, metrics in results['performance_by_recommendation'].items():
        logger.info(f"  {rec}:")
        logger.info(f"    Count: {metrics['count']:,}")
        logger.info(f"    Success Rate: {metrics['success_rate']:.1%}")
        logger.info(f"    Mean Return: {metrics['mean_return']:.3f}")
        logger.info(f"    Avg Confidence: {metrics['avg_confidence']:.3f}")
        logger.info(f"    Prediction Accuracy: {metrics['prediction_accuracy']:.3f}")
    
    # Display horizon performance
    logger.info(f"\n⏰ Horizon Performance Analysis:")
    for horizon, metrics in results['performance_by_horizon'].items():
        logger.info(f"  {horizon} days:")
        logger.info(f"    Count: {metrics['count']:,}")
        logger.info(f"    Success Rate: {metrics['success_rate']:.1%}")
        logger.info(f"    Mean Return: {metrics['mean_return']:.3f}")
        logger.info(f"    Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
    
    # Save detailed results
    import json
    with open('ml_performance_historical_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("✅ Historical ML Performance Analysis completed!")
    logger.info("Results saved to ml_performance_historical_results.json")
    
    return results

if __name__ == "__main__":
    analyze_ml_performance_with_sufficient_data()
