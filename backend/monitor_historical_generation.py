#!/usr/bin/env python3
"""
Historical ML Generation Monitor
This script monitors the progress of historical ML opportunities generation.
"""

import time
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from datetime import datetime, date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def monitor_historical_generation():
    """Monitor the progress of historical ML generation."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            user="loiclinais",
            password="password",
            database="aimarkets"
        )
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        logger.info("🔍 Monitoring Historical ML Generation Progress...")
        logger.info("=" * 80)
        
        # Get initial counts
        cursor.execute("SELECT COUNT(*) as count FROM ml_opportunities")
        initial_count = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(DISTINCT symbol) as count FROM ml_opportunities")
        initial_symbols = cursor.fetchone()['count']
        
        logger.info(f"Initial state: {initial_count} opportunities, {initial_symbols} symbols")
        
        start_time = datetime.now()
        last_count = initial_count
        
        while True:
            # Check current counts
            cursor.execute("SELECT COUNT(*) as count FROM ml_opportunities")
            current_count = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(DISTINCT symbol) as count FROM ml_opportunities")
            current_symbols = cursor.fetchone()['count']
            
            # Check opportunities by date range
            cursor.execute("""
                SELECT MIN(date) as min_date, MAX(date) as max_date, COUNT(*) as count
                FROM ml_opportunities
            """)
            date_range = cursor.fetchone()
            
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
            
            # Calculate progress
            elapsed = datetime.now() - start_time
            new_opportunities = current_count - last_count
            rate = new_opportunities / max(1, elapsed.total_seconds() / 60)  # per minute
            
            # Display progress
            print(f"\n📊 Historical ML Generation Status - {datetime.now().strftime('%H:%M:%S')}")
            print(f"Total Opportunities: {current_count:,} (+{new_opportunities:,} since last check)")
            print(f"Unique Symbols: {current_symbols}")
            print(f"Generation Rate: {rate:.1f} opportunities/minute")
            print(f"Elapsed Time: {elapsed}")
            
            if date_range['min_date'] and date_range['max_date']:
                print(f"\n📅 Date Range: {date_range['min_date']} to {date_range['max_date']}")
            
            if recommendations:
                print(f"\n📈 By Recommendation Type:")
                for rec in recommendations:
                    print(f"  {rec['recommendation']}: {rec['count']:,}")
            
            if horizons:
                print(f"\n⏰ By Horizon:")
                for horizon in horizons:
                    print(f"  {horizon['horizon_days']} days: {horizon['count']:,}")
            
            if confidence_stats and confidence_stats['avg_confidence']:
                print(f"\n🎯 Confidence Stats:")
                print(f"  Average: {confidence_stats['avg_confidence']:.3f}")
                print(f"  Min: {confidence_stats['min_confidence']:.3f}")
                print(f"  Max: {confidence_stats['max_confidence']:.3f}")
            
            # Calculate expected completion
            start_date = date(2025, 1, 1)
            today = date.today()
            total_days = (today - start_date).days + 1
            total_symbols = 101  # Known total
            total_horizons = 3
            expected_total = total_symbols * total_days * total_horizons
            
            completion_pct = (current_count / expected_total) * 100 if expected_total > 0 else 0
            
            print(f"\n🎯 Progress:")
            print(f"  Expected Total: {expected_total:,}")
            print(f"  Completion: {completion_pct:.1f}%")
            
            # Check if generation is still active
            if new_opportunities == 0:
                print(f"\n⚠️  No new opportunities generated in the last check")
                print(f"    Generation may be paused or completed")
            
            print("-" * 80)
            
            last_count = current_count
            
            # Wait before next check
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Error monitoring progress: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    monitor_historical_generation()
