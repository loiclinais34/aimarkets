#!/usr/bin/env python3
"""
Monitoring script for the Advanced ML System
This script monitors the progress of the ML system and provides real-time updates.
"""

import time
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitor_ml_progress():
    """Monitor the progress of the ML system."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            user="loiclinais",
            password="password",
            database="aimarkets"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        logger.info("🔍 Monitoring Advanced ML System Progress...")
        logger.info("=" * 60)
        
        while True:
            # Check ML opportunities count
            cursor.execute("SELECT COUNT(*) as count FROM ml_opportunities")
            opportunities_count = cursor.fetchone()['count']
            
            # Check opportunities by recommendation type
            cursor.execute("""
                SELECT recommendation, COUNT(*) as count 
                FROM ml_opportunities 
                GROUP BY recommendation 
                ORDER BY count DESC
            """)
            recommendations = cursor.fetchall()
            
            # Check opportunities by horizon
            cursor.execute("""
                SELECT horizon_days, COUNT(*) as count 
                FROM ml_opportunities 
                GROUP BY horizon_days 
                ORDER BY horizon_days
            """)
            horizons = cursor.fetchall()
            
            # Check average confidence
            cursor.execute("""
                SELECT AVG(confidence_level) as avg_confidence,
                       MIN(confidence_level) as min_confidence,
                       MAX(confidence_level) as max_confidence
                FROM ml_opportunities
            """)
            confidence_stats = cursor.fetchone()
            
            # Display progress
            print(f"\n📊 ML Opportunities Status - {time.strftime('%H:%M:%S')}")
            print(f"Total Opportunities: {opportunities_count}")
            
            if recommendations:
                print("\n📈 By Recommendation Type:")
                for rec in recommendations:
                    print(f"  {rec['recommendation']}: {rec['count']}")
            
            if horizons:
                print("\n⏰ By Horizon:")
                for horizon in horizons:
                    print(f"  {horizon['horizon_days']} days: {horizon['count']}")
            
            if confidence_stats and confidence_stats['avg_confidence']:
                print(f"\n🎯 Confidence Stats:")
                print(f"  Average: {confidence_stats['avg_confidence']:.3f}")
                print(f"  Min: {confidence_stats['min_confidence']:.3f}")
                print(f"  Max: {confidence_stats['max_confidence']:.3f}")
            
            print("-" * 60)
            
            # Check if we have opportunities for all expected combinations
            expected_symbols = 101
            expected_horizons = 3  # 1, 7, 30 days
            expected_total = expected_symbols * expected_horizons
            
            if opportunities_count >= expected_total:
                print(f"\n✅ COMPLETED! Generated {opportunities_count} opportunities")
                print(f"Expected: {expected_total} (101 symbols × 3 horizons)")
                break
            
            # Wait before next check
            time.sleep(30)
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Error monitoring progress: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    monitor_ml_progress()
