#!/usr/bin/env python3
"""
ML Performance API Endpoints
FastAPI endpoints for ML opportunities performance analysis.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import logging
from datetime import datetime
import json
import numpy as np

from ....core.database import get_db
from .ml_performance_analyzer import MLPerformanceAnalyzer

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/ml-performance/stats")
async def get_ml_performance_stats(
    limit: Optional[int] = Query(None, description="Limit number of opportunities to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive ML opportunities performance statistics.
    """
    try:
        analyzer = MLPerformanceAnalyzer()
        results = analyzer.analyze_ml_performance(limit=limit)
        
        if 'error' in results:
            raise HTTPException(status_code=404, detail=results['error'])
        
        return {
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "data": results
        }
        
    except Exception as e:
        logger.error(f"Error retrieving ML performance stats: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving ML performance stats: {str(e)}")

@router.get("/ml-performance/summary")
async def get_ml_performance_summary(
    limit: Optional[int] = Query(1000, description="Limit number of opportunities to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get summary of ML opportunities performance.
    """
    try:
        analyzer = MLPerformanceAnalyzer()
        results = analyzer.analyze_ml_performance(limit=limit)
        
        # Convert numpy types to Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(v) for v in obj]
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                val = float(obj)
                return None if np.isnan(val) or np.isinf(val) else val
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif obj is None or (isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj))):
                return None
            else:
                return obj
        
        # Convert all numpy types
        results = convert_numpy_types(results)
        
        if 'error' in results:
            raise HTTPException(status_code=404, detail=results['error'])
        
        # Extract key summary metrics
        overall = results.get('overall_performance', {})
        summary = results.get('analysis_summary', {})
        
        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_opportunities": summary.get('total_opportunities_analyzed', 0),
                "success_rate": overall.get('success_rate', 0),
                "mean_return": overall.get('mean_return', 0),
                "volatility": overall.get('volatility', 0),
                "sharpe_ratio": overall.get('sharpe_ratio', 0),
                "win_rate": overall.get('win_rate', 0),
                "profit_factor": overall.get('profit_factor', 0),
                "max_drawdown": overall.get('max_drawdown', 0)
            },
            "recommendation_performance": results.get('performance_by_recommendation', {}),
            "horizon_performance": results.get('performance_by_horizon', {}),
            "top_symbols": results.get('performance_by_symbol', {})
        }
        
    except Exception as e:
        logger.error(f"Error retrieving ML performance summary: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving ML performance summary: {str(e)}")

@router.get("/ml-performance/by-recommendation")
async def get_ml_performance_by_recommendation(
    recommendation: Optional[str] = Query(None, description="Filter by recommendation type"),
    limit: Optional[int] = Query(1000, description="Limit number of opportunities to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get ML performance metrics by recommendation type.
    """
    try:
        analyzer = MLPerformanceAnalyzer()
        results = analyzer.analyze_ml_performance(limit=limit)
        
        if 'error' in results:
            raise HTTPException(status_code=404, detail=results['error'])
        
        recommendation_performance = results.get('performance_by_recommendation', {})
        
        if recommendation and recommendation in recommendation_performance:
            return {
                "timestamp": datetime.now().isoformat(),
                "recommendation": recommendation,
                "performance": recommendation_performance[recommendation]
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "performance_by_recommendation": recommendation_performance
        }
        
    except Exception as e:
        logger.error(f"Error retrieving ML performance by recommendation: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving ML performance by recommendation: {str(e)}")

@router.get("/ml-performance/by-horizon")
async def get_ml_performance_by_horizon(
    horizon: Optional[int] = Query(None, description="Filter by horizon in days"),
    limit: Optional[int] = Query(1000, description="Limit number of opportunities to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get ML performance metrics by horizon.
    """
    try:
        analyzer = MLPerformanceAnalyzer()
        results = analyzer.analyze_ml_performance(limit=limit)
        
        if 'error' in results:
            raise HTTPException(status_code=404, detail=results['error'])
        
        horizon_performance = results.get('performance_by_horizon', {})
        
        if horizon and horizon in horizon_performance:
            return {
                "timestamp": datetime.now().isoformat(),
                "horizon_days": horizon,
                "performance": horizon_performance[horizon]
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "performance_by_horizon": horizon_performance
        }
        
    except Exception as e:
        logger.error(f"Error retrieving ML performance by horizon: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving ML performance by horizon: {str(e)}")

@router.get("/ml-performance/top-performers")
async def get_ml_top_performers(
    top_n: int = Query(10, description="Number of top performers to return"),
    limit: Optional[int] = Query(1000, description="Limit number of opportunities to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get top performing ML opportunities.
    """
    try:
        analyzer = MLPerformanceAnalyzer()
        results = analyzer.analyze_ml_performance(limit=limit)
        
        if 'error' in results:
            raise HTTPException(status_code=404, detail=results['error'])
        
        symbol_performance = results.get('performance_by_symbol', {})
        
        # Sort by success rate and return top N
        sorted_symbols = sorted(
            symbol_performance.items(),
            key=lambda x: x[1].get('success_rate', 0),
            reverse=True
        )[:top_n]
        
        return {
            "timestamp": datetime.now().isoformat(),
            "top_performers": [
                {
                    "symbol": symbol,
                    "performance": performance
                }
                for symbol, performance in sorted_symbols
            ]
        }
        
    except Exception as e:
        logger.error(f"Error retrieving ML top performers: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving ML top performers: {str(e)}")

@router.get("/ml-performance/report")
async def get_ml_performance_report(
    limit: Optional[int] = Query(1000, description="Limit number of opportunities to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get a human-readable ML performance report.
    """
    try:
        analyzer = MLPerformanceAnalyzer()
        results = analyzer.analyze_ml_performance(limit=limit)
        
        if 'error' in results:
            raise HTTPException(status_code=404, detail=results['error'])
        
        report = analyzer.generate_performance_report(results)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "report": report,
            "raw_data": results
        }
        
    except Exception as e:
        logger.error(f"Error generating ML performance report: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating ML performance report: {str(e)}")
