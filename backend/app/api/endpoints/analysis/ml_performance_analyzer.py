#!/usr/bin/env python3
"""
ML Opportunities Performance Analysis
This script analyzes the performance of ML-generated opportunities for backtesting.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from decimal import Decimal
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

# Database imports
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ml_performance_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MLPerformanceAnalyzer:
    """Analyzer for ML opportunities performance."""
    
    def __init__(self):
        self.db_url = "postgresql://loiclinais:password@localhost:5432/aimarkets"
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Recommendation thresholds
        self.recommendation_thresholds = {
            'BUY_STRONG': (0.05, float('inf')),
            'BUY_MODERATE': (0.03, float('inf')),
            'BUY_WEAK': (0.01, float('inf')),
            'HOLD': (-0.01, 0.01),
            'SELL_WEAK': (-float('inf'), -0.01),
            'SELL_MODERATE': (-float('inf'), -0.03),
            'SELL_STRONG': (-float('inf'), -0.05)
        }
        
        # Performance metrics
        self.metrics = {}

    def get_ml_opportunities(self, limit: Optional[int] = None) -> pd.DataFrame:
        """Get ML opportunities from the database."""
        query = """
        SELECT 
            id, symbol, date, horizon_days, recommendation, confidence_level,
            potential_return, risk_score, ml_model_name, ml_model_version,
            technical_indicators, ml_features, created_at
        FROM ml_opportunities
        WHERE ml_model_name = 'optimized_historical_v1'
        AND date <= '2025-09-15'
        ORDER BY date DESC, confidence_level DESC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        df = pd.read_sql(query, self.engine)
        
        # Convert types
        df['date'] = pd.to_datetime(df['date'])
        df['confidence_level'] = pd.to_numeric(df['confidence_level'], errors='coerce')
        df['potential_return'] = pd.to_numeric(df['potential_return'], errors='coerce')
        df['risk_score'] = pd.to_numeric(df['risk_score'], errors='coerce')
        
        return df

    def get_historical_data_for_symbol(self, symbol: str, start_date: date, end_date: date) -> pd.DataFrame:
        """Get historical data for a symbol within date range."""
        query = """
        SELECT symbol, date, open, high, low, close, volume
        FROM historical_data
        WHERE symbol = %s AND date >= %s AND date <= %s
        ORDER BY date
        """
        df = pd.read_sql(query, self.engine, params=(symbol, start_date, end_date))
        
        # Convert to proper types
        df['date'] = pd.to_datetime(df['date'])
        df['open'] = pd.to_numeric(df['open'], errors='coerce')
        df['high'] = pd.to_numeric(df['high'], errors='coerce')
        df['low'] = pd.to_numeric(df['low'], errors='coerce')
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
        df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        return df

    def calculate_actual_returns(self, opportunities: pd.DataFrame) -> pd.DataFrame:
        """Calculate actual returns for ML opportunities."""
        logger.info("Calculating actual returns for ML opportunities...")
        
        opportunities_with_returns = []
        
        for _, opp in opportunities.iterrows():
            try:
                symbol = opp['symbol']
                opp_date = opp['date'].date()
                horizon_days = opp['horizon_days']
                
                # Calculate end date for the horizon
                end_date = opp_date + timedelta(days=horizon_days)
                
                # Get historical data
                hist_data = self.get_historical_data_for_symbol(symbol, opp_date, end_date)
                
                if len(hist_data) < 2:
                    continue
                
                # Get price at opportunity date and end date
                opp_price = hist_data[hist_data['date'].dt.date == opp_date]['close'].iloc[0]
                
                # Find the closest available date to end_date
                available_dates = hist_data['date'].dt.date.tolist()
                actual_end_date = min([d for d in available_dates if d >= end_date], default=available_dates[-1])
                
                end_price = hist_data[hist_data['date'].dt.date == actual_end_date]['close'].iloc[0]
                
                # Calculate actual return
                actual_return = (end_price - opp_price) / opp_price
                
                # Add to results
                opp_dict = opp.to_dict()
                opp_dict['actual_return'] = actual_return
                opp_dict['actual_end_date'] = actual_end_date
                opp_dict['opp_price'] = opp_price
                opp_dict['end_price'] = end_price
                
                opportunities_with_returns.append(opp_dict)
                
            except Exception as e:
                logger.warning(f"Error calculating return for {opp['symbol']} on {opp['date']}: {e}")
                continue
        
        return pd.DataFrame(opportunities_with_returns)

    def calculate_opportunity_success(self, opp: Dict) -> Tuple[bool, float]:
        """Calculate if an opportunity was successful."""
        recommendation = opp['recommendation']
        actual_return = opp['actual_return']
        confidence_level = opp['confidence_level']
        
        # Get threshold for recommendation
        if recommendation in self.recommendation_thresholds:
            min_threshold, max_threshold = self.recommendation_thresholds[recommendation]
            
            # Check if actual return is within expected range
            if min_threshold <= actual_return <= max_threshold:
                # Additional validation for high-confidence recommendations
                if recommendation == 'BUY_STRONG':
                    return actual_return >= 0.01 and confidence_level >= 0.6, actual_return
                elif recommendation == 'SELL_STRONG':
                    return actual_return <= -0.01 and confidence_level >= 0.6, actual_return
                else:
                    return True, actual_return
        
        return False, actual_return

    def calculate_performance_metrics(self, opportunities: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        logger.info("Calculating performance metrics...")
        
        if opportunities.empty:
            return {"error": "No opportunities to analyze"}
        
        # Basic statistics
        total_opportunities = len(opportunities)
        successful_opportunities = len(opportunities[opportunities['is_successful'] == True])
        success_rate = successful_opportunities / total_opportunities if total_opportunities > 0 else 0
        
        # Return statistics
        actual_returns = opportunities['actual_return'].dropna()
        mean_return = actual_returns.mean()
        median_return = actual_returns.median()
        std_return = actual_returns.std()
        
        # Risk metrics
        volatility = std_return
        sharpe_ratio = mean_return / std_return if std_return > 0 else 0
        
        # Drawdown analysis
        cumulative_returns = (1 + actual_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # Win rate
        positive_returns = actual_returns[actual_returns > 0]
        win_rate = len(positive_returns) / len(actual_returns) if len(actual_returns) > 0 else 0
        
        # Profit factor
        total_profit = positive_returns.sum() if len(positive_returns) > 0 else 0
        total_loss = abs(actual_returns[actual_returns < 0].sum()) if len(actual_returns[actual_returns < 0]) > 0 else 0
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # VaR and CVaR
        var_95 = actual_returns.quantile(0.05)
        cvar_95 = actual_returns[actual_returns <= var_95].mean()
        
        # Calmar ratio
        calmar_ratio = mean_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # Downside deviation
        downside_returns = actual_returns[actual_returns < 0]
        downside_deviation = downside_returns.std() if len(downside_returns) > 0 else 0
        
        # Sortino ratio
        sortino_ratio = mean_return / downside_deviation if downside_deviation > 0 else 0
        
        return {
            "total_opportunities": int(total_opportunities),
            "successful_opportunities": int(successful_opportunities),
            "success_rate": float(success_rate),
            "mean_return": float(mean_return),
            "median_return": float(median_return),
            "volatility": float(volatility),
            "sharpe_ratio": float(sharpe_ratio),
            "max_drawdown": float(max_drawdown),
            "win_rate": float(win_rate),
            "profit_factor": float(profit_factor) if profit_factor != float('inf') else None,
            "var_95": float(var_95),
            "cvar_95": float(cvar_95),
            "calmar_ratio": float(calmar_ratio),
            "downside_deviation": float(downside_deviation),
            "sortino_ratio": float(sortino_ratio)
        }

    def calculate_performance_by_recommendation(self, opportunities: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Calculate performance metrics by recommendation type."""
        logger.info("Calculating performance by recommendation type...")
        
        recommendation_metrics = {}
        
        for recommendation in opportunities['recommendation'].unique():
            rec_opportunities = opportunities[opportunities['recommendation'] == recommendation]
            
            if len(rec_opportunities) == 0:
                continue
            
            metrics = self.calculate_performance_metrics(rec_opportunities)
            
            # Add recommendation-specific metrics
            metrics['count'] = int(len(rec_opportunities))
            metrics['avg_confidence'] = float(rec_opportunities['confidence_level'].mean())
            metrics['avg_predicted_return'] = float(rec_opportunities['potential_return'].mean())
            metrics['avg_actual_return'] = float(rec_opportunities['actual_return'].mean())
            metrics['prediction_accuracy'] = float(abs(metrics['avg_predicted_return'] - metrics['avg_actual_return']))
            
            recommendation_metrics[recommendation] = metrics
        
        return recommendation_metrics

    def calculate_performance_by_horizon(self, opportunities: pd.DataFrame) -> Dict[int, Dict[str, Any]]:
        """Calculate performance metrics by horizon."""
        logger.info("Calculating performance by horizon...")
        
        horizon_metrics = {}
        
        for horizon in opportunities['horizon_days'].unique():
            horizon_opportunities = opportunities[opportunities['horizon_days'] == horizon]
            
            if len(horizon_opportunities) == 0:
                continue
            
            metrics = self.calculate_performance_metrics(horizon_opportunities)
            metrics['count'] = int(len(horizon_opportunities))
            
            horizon_metrics[str(horizon)] = metrics
        
        return horizon_metrics

    def calculate_performance_by_symbol(self, opportunities: pd.DataFrame, top_n: int = 10) -> Dict[str, Dict[str, Any]]:
        """Calculate performance metrics by symbol (top N)."""
        logger.info(f"Calculating performance by symbol (top {top_n})...")
        
        symbol_metrics = {}
        
        # Get symbols with most opportunities
        symbol_counts = opportunities['symbol'].value_counts()
        top_symbols = symbol_counts.head(top_n).index.tolist()
        
        for symbol in top_symbols:
            symbol_opportunities = opportunities[opportunities['symbol'] == symbol]
            
            if len(symbol_opportunities) == 0:
                continue
            
            metrics = self.calculate_performance_metrics(symbol_opportunities)
            metrics['count'] = int(len(symbol_opportunities))
            metrics['avg_confidence'] = float(symbol_opportunities['confidence_level'].mean())
            
            symbol_metrics[symbol] = metrics
        
        return symbol_metrics

    def analyze_ml_performance(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Main function to analyze ML opportunities performance."""
        logger.info("🚀 Starting ML Opportunities Performance Analysis...")
        
        # Get ML opportunities
        opportunities = self.get_ml_opportunities(limit)
        logger.info(f"Retrieved {len(opportunities)} ML opportunities")
        
        if opportunities.empty:
            return {"error": "No ML opportunities found"}
        
        # Calculate actual returns
        opportunities_with_returns = self.calculate_actual_returns(opportunities)
        logger.info(f"Calculated returns for {len(opportunities_with_returns)} opportunities")
        
        if opportunities_with_returns.empty:
            return {"error": "No opportunities with calculated returns"}
        
        # Calculate success for each opportunity
        opportunities_with_returns['is_successful'] = opportunities_with_returns.apply(
            lambda row: self.calculate_opportunity_success(row.to_dict())[0], axis=1
        )
        
        # Calculate overall performance metrics
        overall_metrics = self.calculate_performance_metrics(opportunities_with_returns)
        
        # Calculate performance by recommendation
        recommendation_metrics = self.calculate_performance_by_recommendation(opportunities_with_returns)
        
        # Calculate performance by horizon
        horizon_metrics = self.calculate_performance_by_horizon(opportunities_with_returns)
        
        # Calculate performance by symbol
        symbol_metrics = self.calculate_performance_by_symbol(opportunities_with_returns)
        
        # Compile results
        results = {
            "timestamp": datetime.now().isoformat(),
            "analysis_summary": {
                "total_opportunities_analyzed": len(opportunities_with_returns),
                "date_range": {
                    "start": opportunities_with_returns['date'].min().isoformat(),
                    "end": opportunities_with_returns['date'].max().isoformat()
                },
                "symbols_covered": opportunities_with_returns['symbol'].nunique(),
                "horizons_analyzed": sorted(opportunities_with_returns['horizon_days'].unique().tolist())
            },
            "overall_performance": overall_metrics,
            "performance_by_recommendation": recommendation_metrics,
            "performance_by_horizon": horizon_metrics,
            "performance_by_symbol": symbol_metrics
        }
        
        logger.info("✅ ML Performance Analysis completed!")
        return results

    def generate_performance_report(self, results: Dict[str, Any]) -> str:
        """Generate a human-readable performance report."""
        report = []
        report.append("📊 ML OPPORTUNITIES PERFORMANCE REPORT")
        report.append("=" * 50)
        
        # Summary
        summary = results['analysis_summary']
        report.append(f"\n📈 Analysis Summary:")
        report.append(f"  Total Opportunities: {summary['total_opportunities_analyzed']:,}")
        report.append(f"  Date Range: {summary['date_range']['start']} to {summary['date_range']['end']}")
        report.append(f"  Symbols Covered: {summary['symbols_covered']}")
        report.append(f"  Horizons: {summary['horizons_analyzed']}")
        
        # Overall Performance
        overall = results['overall_performance']
        report.append(f"\n🎯 Overall Performance:")
        report.append(f"  Success Rate: {overall['success_rate']:.1%}")
        report.append(f"  Mean Return: {overall['mean_return']:.3f}")
        report.append(f"  Volatility: {overall['volatility']:.3f}")
        report.append(f"  Sharpe Ratio: {overall['sharpe_ratio']:.3f}")
        report.append(f"  Max Drawdown: {overall['max_drawdown']:.3f}")
        report.append(f"  Win Rate: {overall['win_rate']:.1%}")
        report.append(f"  Profit Factor: {overall['profit_factor']:.2f}")
        
        # Performance by Recommendation
        report.append(f"\n📊 Performance by Recommendation:")
        for rec, metrics in results['performance_by_recommendation'].items():
            report.append(f"  {rec}:")
            report.append(f"    Count: {metrics['count']:,}")
            report.append(f"    Success Rate: {metrics['success_rate']:.1%}")
            report.append(f"    Mean Return: {metrics['mean_return']:.3f}")
            report.append(f"    Avg Confidence: {metrics['avg_confidence']:.3f}")
            report.append(f"    Prediction Accuracy: {metrics['prediction_accuracy']:.3f}")
        
        # Performance by Horizon
        report.append(f"\n⏰ Performance by Horizon:")
        for horizon, metrics in results['performance_by_horizon'].items():
            report.append(f"  {horizon} days:")
            report.append(f"    Count: {metrics['count']:,}")
            report.append(f"    Success Rate: {metrics['success_rate']:.1%}")
            report.append(f"    Mean Return: {metrics['mean_return']:.3f}")
            report.append(f"    Sharpe Ratio: {metrics['sharpe_ratio']:.3f}")
        
        return "\n".join(report)

def main():
    """Main function to run ML performance analysis."""
    analyzer = MLPerformanceAnalyzer()
    
    # Analyze all opportunities (this might take a while)
    logger.info("Starting comprehensive ML performance analysis...")
    results = analyzer.analyze_ml_performance()
    
    # Generate report
    report = analyzer.generate_performance_report(results)
    print(report)
    
    # Save results to file
    with open('ml_performance_results.json', 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info("Results saved to ml_performance_results.json")

if __name__ == "__main__":
    main()
