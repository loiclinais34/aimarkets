#!/usr/bin/env python3
"""
ML Opportunities Quality Analyzer
This script analyzes the quality and distribution of generated ML opportunities.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_ml_opportunities_quality():
    """Analyze the quality of generated ML opportunities."""
    logger.info("🔍 Analyzing ML Opportunities Quality...")
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            user="loiclinais",
            password="password",
            database="aimarkets"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Basic statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_opportunities,
                COUNT(DISTINCT symbol) as unique_symbols,
                COUNT(DISTINCT date) as unique_dates,
                MIN(date) as min_date,
                MAX(date) as max_date,
                AVG(confidence_level) as avg_confidence,
                STDDEV(confidence_level) as std_confidence,
                MIN(confidence_level) as min_confidence,
                MAX(confidence_level) as max_confidence
            FROM ml_opportunities
        """)
        basic_stats = cursor.fetchone()
        
        logger.info("📊 Basic Statistics:")
        logger.info(f"  Total Opportunities: {basic_stats['total_opportunities']:,}")
        logger.info(f"  Unique Symbols: {basic_stats['unique_symbols']}")
        logger.info(f"  Unique Dates: {basic_stats['unique_dates']}")
        logger.info(f"  Date Range: {basic_stats['min_date']} to {basic_stats['max_date']}")
        logger.info(f"  Confidence: {basic_stats['avg_confidence']:.3f} ± {basic_stats['std_confidence']:.3f}")
        logger.info(f"  Confidence Range: {basic_stats['min_confidence']:.3f} - {basic_stats['max_confidence']:.3f}")
        
        # Recommendation distribution
        cursor.execute("""
            SELECT 
                recommendation,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ml_opportunities), 2) as percentage,
                AVG(confidence_level) as avg_confidence,
                AVG(potential_return) as avg_return,
                AVG(risk_score) as avg_risk
            FROM ml_opportunities
            GROUP BY recommendation
            ORDER BY count DESC
        """)
        recommendations = cursor.fetchall()
        
        logger.info("\n📈 Recommendation Distribution:")
        for rec in recommendations:
            logger.info(f"  {rec['recommendation']:12}: {rec['count']:6,} ({rec['percentage']:5.1f}%) "
                       f"conf: {rec['avg_confidence']:.3f} ret: {rec['avg_return']:.3f} risk: {rec['avg_risk']:.3f}")
        
        # Horizon distribution
        cursor.execute("""
            SELECT 
                horizon_days,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM ml_opportunities), 2) as percentage,
                AVG(confidence_level) as avg_confidence,
                AVG(potential_return) as avg_return
            FROM ml_opportunities
            GROUP BY horizon_days
            ORDER BY horizon_days
        """)
        horizons = cursor.fetchall()
        
        logger.info("\n⏰ Horizon Distribution:")
        for horizon in horizons:
            logger.info(f"  {horizon['horizon_days']:2} days: {horizon['count']:6,} ({horizon['percentage']:5.1f}%) "
                       f"conf: {horizon['avg_confidence']:.3f} ret: {horizon['avg_return']:.3f}")
        
        # Symbol coverage
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as opportunities,
                COUNT(DISTINCT date) as unique_dates,
                AVG(confidence_level) as avg_confidence,
                AVG(potential_return) as avg_return
            FROM ml_opportunities
            GROUP BY symbol
            ORDER BY opportunities DESC
            LIMIT 10
        """)
        top_symbols = cursor.fetchall()
        
        logger.info("\n🏆 Top 10 Symbols by Opportunities:")
        for symbol in top_symbols:
            logger.info(f"  {symbol['symbol']:6}: {symbol['opportunities']:4} opps, "
                       f"{symbol['unique_dates']:3} dates, "
                       f"conf: {symbol['avg_confidence']:.3f}, ret: {symbol['avg_return']:.3f}")
        
        # Date coverage analysis
        cursor.execute("""
            SELECT 
                DATE_TRUNC('month', date) as month,
                COUNT(*) as opportunities,
                COUNT(DISTINCT symbol) as symbols_covered,
                AVG(confidence_level) as avg_confidence
            FROM ml_opportunities
            GROUP BY DATE_TRUNC('month', date)
            ORDER BY month
        """)
        monthly_stats = cursor.fetchall()
        
        logger.info("\n📅 Monthly Coverage:")
        for month in monthly_stats:
            logger.info(f"  {month['month'].strftime('%Y-%m')}: {month['opportunities']:5,} opps, "
                       f"{month['symbols_covered']:3} symbols, conf: {month['avg_confidence']:.3f}")
        
        # Quality metrics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN confidence_level > 0.5 THEN 1 END) as high_confidence,
                COUNT(CASE WHEN confidence_level > 0.7 THEN 1 END) as very_high_confidence,
                COUNT(CASE WHEN ABS(potential_return) > 0.05 THEN 1 END) as high_return,
                COUNT(CASE WHEN risk_score < 0.1 THEN 1 END) as low_risk
            FROM ml_opportunities
        """)
        quality_metrics = cursor.fetchone()
        
        logger.info("\n🎯 Quality Metrics:")
        logger.info(f"  High Confidence (>0.5): {quality_metrics['high_confidence']:,} ({quality_metrics['high_confidence']/quality_metrics['total']*100:.1f}%)")
        logger.info(f"  Very High Confidence (>0.7): {quality_metrics['very_high_confidence']:,} ({quality_metrics['very_high_confidence']/quality_metrics['total']*100:.1f}%)")
        logger.info(f"  High Return (>5%): {quality_metrics['high_return']:,} ({quality_metrics['high_return']/quality_metrics['total']*100:.1f}%)")
        logger.info(f"  Low Risk (<10%): {quality_metrics['low_risk']:,} ({quality_metrics['low_risk']/quality_metrics['total']*100:.1f}%)")
        
        # Expected vs Actual
        start_date = date(2025, 1, 1)
        today = date.today()
        total_days = (today - start_date).days + 1
        total_symbols = 101
        total_horizons = 3
        expected_total = total_symbols * total_days * total_horizons
        
        completion_pct = (basic_stats['total_opportunities'] / expected_total) * 100
        
        logger.info("\n📊 Completion Analysis:")
        logger.info(f"  Expected Total: {expected_total:,}")
        logger.info(f"  Actual Total: {basic_stats['total_opportunities']:,}")
        logger.info(f"  Completion: {completion_pct:.1f}%")
        
        if completion_pct < 100:
            remaining = expected_total - basic_stats['total_opportunities']
            logger.info(f"  Remaining: {remaining:,} opportunities")
        
        conn.close()
        
        logger.info("\n✅ Quality Analysis completed!")
        
    except Exception as e:
        logger.error(f"Error analyzing opportunities: {e}")

if __name__ == "__main__":
    analyze_ml_opportunities_quality()
