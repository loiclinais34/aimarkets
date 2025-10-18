from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import json
from datetime import datetime, date

from ....core.database import get_db

router = APIRouter()

@router.get("/ml-opportunities")
async def get_ml_opportunities(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    horizon_days: Optional[int] = Query(None, description="Filter by horizon days (1, 7, 30)"),
    recommendation: Optional[str] = Query(None, description="Filter by recommendation"),
    min_confidence: Optional[float] = Query(0.0, description="Minimum confidence level"),
    limit: int = Query(50, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Get ML-generated opportunities with optional filters.
    """
    try:
        # Build query
        query = """
        SELECT symbol, date, horizon_days, recommendation, confidence_level, 
               potential_return, risk_score, ml_model_name, ml_model_version,
               technical_indicators, ml_features, created_at
        FROM ml_opportunities
        WHERE 1=1
        """
        
        params = {}
        
        if symbol:
            query += " AND symbol = :symbol"
            params['symbol'] = symbol
            
        if horizon_days:
            query += " AND horizon_days = :horizon_days"
            params['horizon_days'] = horizon_days
            
        if recommendation:
            query += " AND recommendation = :recommendation"
            params['recommendation'] = recommendation
            
        if min_confidence:
            query += " AND confidence_level >= :min_confidence"
            params['min_confidence'] = min_confidence
        
        query += " ORDER BY confidence_level DESC, created_at DESC LIMIT :limit"
        params['limit'] = limit
        
        result = db.execute(text(query), params)
        opportunities = result.fetchall()
        
        # Convert to list of dictionaries
        opportunities_list = []
        for opp in opportunities:
            opp_dict = {
                'symbol': opp.symbol,
                'date': opp.date.isoformat() if opp.date else None,
                'horizon_days': opp.horizon_days,
                'recommendation': opp.recommendation,
                'confidence_level': float(opp.confidence_level),
                'potential_return': float(opp.potential_return) if opp.potential_return else None,
                'risk_score': float(opp.risk_score) if opp.risk_score else None,
                'ml_model_name': opp.ml_model_name,
                'ml_model_version': opp.ml_model_version,
                'technical_indicators': opp.technical_indicators if opp.technical_indicators else None,
                'ml_features': opp.ml_features if opp.ml_features else None,
                'created_at': opp.created_at.isoformat() if opp.created_at else None
            }
            opportunities_list.append(opp_dict)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'total_opportunities': len(opportunities_list),
            'opportunities': opportunities_list
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving ML opportunities: {str(e)}"
        )

@router.get("/ml-opportunities/summary")
async def get_ml_opportunities_summary(
    db: Session = Depends(get_db)
):
    """
    Get summary statistics of ML opportunities.
    """
    try:
        # Get summary statistics
        summary_query = """
        SELECT 
            COUNT(*) as total_opportunities,
            COUNT(DISTINCT symbol) as unique_symbols,
            AVG(confidence_level) as avg_confidence,
            AVG(potential_return) as avg_return,
            AVG(risk_score) as avg_risk,
            MIN(confidence_level) as min_confidence,
            MAX(confidence_level) as max_confidence,
            MIN(potential_return) as min_return,
            MAX(potential_return) as max_return
        FROM ml_opportunities
        """
        
        summary_result = db.execute(text(summary_query))
        summary = summary_result.fetchone()
        
        # Get recommendation distribution
        rec_query = """
        SELECT recommendation, COUNT(*) as count, AVG(confidence_level) as avg_confidence, AVG(potential_return) as avg_return
        FROM ml_opportunities
        GROUP BY recommendation
        ORDER BY count DESC
        """
        
        rec_result = db.execute(text(rec_query))
        recommendations = rec_result.fetchall()
        
        # Get horizon distribution
        horizon_query = """
        SELECT horizon_days, COUNT(*) as count, AVG(confidence_level) as avg_confidence, AVG(potential_return) as avg_return
        FROM ml_opportunities
        GROUP BY horizon_days
        ORDER BY horizon_days
        """
        
        horizon_result = db.execute(text(horizon_query))
        horizons = horizon_result.fetchall()
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_opportunities': summary.total_opportunities,
                'unique_symbols': summary.unique_symbols,
                'avg_confidence': float(summary.avg_confidence) if summary.avg_confidence else 0,
                'avg_return': float(summary.avg_return) if summary.avg_return else 0,
                'avg_risk': float(summary.avg_risk) if summary.avg_risk else 0,
                'confidence_range': {
                    'min': float(summary.min_confidence) if summary.min_confidence else 0,
                    'max': float(summary.max_confidence) if summary.max_confidence else 0
                },
                'return_range': {
                    'min': float(summary.min_return) if summary.min_return else 0,
                    'max': float(summary.max_return) if summary.max_return else 0
                }
            },
            'recommendation_distribution': [
                {
                    'recommendation': rec.recommendation,
                    'count': rec.count,
                    'avg_confidence': float(rec.avg_confidence) if rec.avg_confidence else 0,
                    'avg_return': float(rec.avg_return) if rec.avg_return else 0
                }
                for rec in recommendations
            ],
            'horizon_distribution': [
                {
                    'horizon_days': horizon.horizon_days,
                    'count': horizon.count,
                    'avg_confidence': float(horizon.avg_confidence) if horizon.avg_confidence else 0,
                    'avg_return': float(horizon.avg_return) if horizon.avg_return else 0
                }
                for horizon in horizons
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving ML opportunities summary: {str(e)}"
        )

@router.get("/ml-opportunities/top-performers")
async def get_top_performing_ml_opportunities(
    metric: str = Query("confidence_level", description="Metric to sort by (confidence_level, potential_return)"),
    limit: int = Query(10, description="Number of top performers to return"),
    db: Session = Depends(get_db)
):
    """
    Get top performing ML opportunities based on specified metric.
    """
    try:
        valid_metrics = ['confidence_level', 'potential_return']
        if metric not in valid_metrics:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid metric. Must be one of: {valid_metrics}"
            )
        
        query = f"""
        SELECT symbol, date, horizon_days, recommendation, confidence_level, 
               potential_return, risk_score, ml_model_name, ml_model_version
        FROM ml_opportunities
        ORDER BY {metric} DESC
        LIMIT :limit
        """
        
        result = db.execute(text(query), {'limit': limit})
        opportunities = result.fetchall()
        
        opportunities_list = []
        for opp in opportunities:
            opp_dict = {
                'symbol': opp.symbol,
                'date': opp.date.isoformat() if opp.date else None,
                'horizon_days': opp.horizon_days,
                'recommendation': opp.recommendation,
                'confidence_level': float(opp.confidence_level),
                'potential_return': float(opp.potential_return) if opp.potential_return else None,
                'risk_score': float(opp.risk_score) if opp.risk_score else None,
                'ml_model_name': opp.ml_model_name,
                'ml_model_version': opp.ml_model_version
            }
            opportunities_list.append(opp_dict)
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'metric': metric,
            'top_performers': opportunities_list
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving top performing ML opportunities: {str(e)}"
        )
