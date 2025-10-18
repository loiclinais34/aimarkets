#!/usr/bin/env python3
"""
Test ML Performance Analysis
This script tests the ML performance analysis with a sample of opportunities.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml_performance_analyzer import MLPerformanceAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ml_performance_analysis():
    """Test ML performance analysis with a sample."""
    logger.info("🧪 Testing ML Performance Analysis...")
    
    analyzer = MLPerformanceAnalyzer()
    
    # Test with a sample of 1000 opportunities
    logger.info("Analyzing sample of 1000 ML opportunities...")
    results = analyzer.analyze_ml_performance(limit=1000)
    
    if 'error' in results:
        logger.error(f"Analysis failed: {results['error']}")
        return
    
    # Generate and display report
    report = analyzer.generate_performance_report(results)
    print(report)
    
    # Display key metrics
    overall = results['overall_performance']
    logger.info(f"\n🎯 Key Metrics:")
    logger.info(f"  Success Rate: {overall['success_rate']:.1%}")
    logger.info(f"  Mean Return: {overall['mean_return']:.3f}")
    logger.info(f"  Sharpe Ratio: {overall['sharpe_ratio']:.3f}")
    logger.info(f"  Win Rate: {overall['win_rate']:.1%}")
    
    # Display recommendation performance
    logger.info(f"\n📊 Recommendation Performance:")
    for rec, metrics in results['performance_by_recommendation'].items():
        logger.info(f"  {rec}: {metrics['success_rate']:.1%} success rate, "
                   f"{metrics['mean_return']:.3f} mean return")
    
    logger.info("✅ Test completed successfully!")
    return results

if __name__ == "__main__":
    test_ml_performance_analysis()
