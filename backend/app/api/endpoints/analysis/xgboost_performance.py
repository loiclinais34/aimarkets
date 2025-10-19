from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List, Optional
from datetime import datetime, date, timedelta
import logging
import numpy as np

from ....core.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/xgboost-performance/summary")
async def get_xgboost_performance_summary(
    db: Session = Depends(get_db),
    limit: Optional[int] = None
):
    """
    Récupère un résumé des performances des opportunités XGBoost.
    """
    try:
        # Construire la requête avec limite optionnelle
        limit_clause = f"LIMIT {limit}" if limit else ""
        
        # Statistiques générales
        stats_query = f"""
        SELECT 
            COUNT(*) as total_opportunities,
            COUNT(DISTINCT symbol) as unique_symbols,
            COUNT(DISTINCT horizon_days) as horizons_count,
            MIN(date) as earliest_date,
            MAX(date) as latest_date,
            AVG(confidence_level) as avg_confidence,
            AVG(potential_return) as avg_potential_return,
            AVG(risk_score) as avg_risk_score
        FROM ml_opportunities_xgboost
        {limit_clause}
        """
        
        stats_result = db.execute(text(stats_query)).fetchone()
        
        # Performance par recommandation
        recommendation_query = f"""
        SELECT 
            recommendation,
            COUNT(*) as count,
            AVG(confidence_level) as avg_confidence,
            AVG(potential_return) as avg_potential_return,
            AVG(risk_score) as avg_risk_score,
            MIN(confidence_level) as min_confidence,
            MAX(confidence_level) as max_confidence
        FROM ml_opportunities_xgboost
        {limit_clause}
        GROUP BY recommendation
        ORDER BY count DESC
        """
        
        recommendation_results = db.execute(text(recommendation_query)).fetchall()
        
        # Performance par horizon
        horizon_query = f"""
        SELECT 
            horizon_days,
            COUNT(*) as count,
            AVG(confidence_level) as avg_confidence,
            AVG(potential_return) as avg_potential_return,
            AVG(risk_score) as avg_risk_score
        FROM ml_opportunities_xgboost
        {limit_clause}
        GROUP BY horizon_days
        ORDER BY horizon_days
        """
        
        horizon_results = db.execute(text(horizon_query)).fetchall()
        
        # Top symboles par confiance
        top_symbols_query = f"""
        SELECT 
            symbol,
            COUNT(*) as count,
            AVG(confidence_level) as avg_confidence,
            AVG(potential_return) as avg_potential_return,
            MAX(confidence_level) as max_confidence
        FROM ml_opportunities_xgboost
        {limit_clause}
        GROUP BY symbol
        HAVING COUNT(*) >= 10
        ORDER BY avg_confidence DESC
        LIMIT 10
        """
        
        top_symbols_results = db.execute(text(top_symbols_query)).fetchall()
        
        # Distribution des confiances
        confidence_distribution_query = f"""
        SELECT 
            CASE 
                WHEN confidence_level >= 0.9 THEN 'Très Haute (≥90%)'
                WHEN confidence_level >= 0.8 THEN 'Haute (80-90%)'
                WHEN confidence_level >= 0.7 THEN 'Moyenne-Haute (70-80%)'
                WHEN confidence_level >= 0.6 THEN 'Moyenne (60-70%)'
                ELSE 'Faible (<60%)'
            END as confidence_range,
            COUNT(*) as count,
            AVG(confidence_level) as avg_confidence,
            AVG(potential_return) as avg_potential_return
        FROM ml_opportunities_xgboost
        {limit_clause}
        GROUP BY 
            CASE 
                WHEN confidence_level >= 0.9 THEN 'Très Haute (≥90%)'
                WHEN confidence_level >= 0.8 THEN 'Haute (80-90%)'
                WHEN confidence_level >= 0.7 THEN 'Moyenne-Haute (70-80%)'
                WHEN confidence_level >= 0.6 THEN 'Moyenne (60-70%)'
                ELSE 'Faible (<60%)'
            END
        ORDER BY avg_confidence DESC
        """
        
        confidence_distribution_results = db.execute(text(confidence_distribution_query)).fetchall()
        
        # Construire la réponse
        response = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_opportunities": int(stats_result[0]) if stats_result[0] else 0,
                "unique_symbols": int(stats_result[1]) if stats_result[1] else 0,
                "horizons_count": int(stats_result[2]) if stats_result[2] else 0,
                "date_range": {
                    "earliest": stats_result[3].isoformat() if stats_result[3] else None,
                    "latest": stats_result[4].isoformat() if stats_result[4] else None
                },
                "avg_confidence": float(stats_result[5]) if stats_result[5] else 0,
                "avg_potential_return": float(stats_result[6]) if stats_result[6] else 0,
                "avg_risk_score": float(stats_result[7]) if stats_result[7] else 0
            },
            "recommendation_performance": {
                row[0]: {
                    "count": int(row[1]),
                    "avg_confidence": float(row[2]),
                    "avg_potential_return": float(row[3]),
                    "avg_risk_score": float(row[4]),
                    "min_confidence": float(row[5]),
                    "max_confidence": float(row[6])
                }
                for row in recommendation_results
            },
            "horizon_performance": {
                str(row[0]): {
                    "count": int(row[1]),
                    "avg_confidence": float(row[2]),
                    "avg_potential_return": float(row[3]),
                    "avg_risk_score": float(row[4])
                }
                for row in horizon_results
            },
            "top_symbols": {
                row[0]: {
                    "count": int(row[1]),
                    "avg_confidence": float(row[2]),
                    "avg_potential_return": float(row[3]),
                    "max_confidence": float(row[4])
                }
                for row in top_symbols_results
            },
            "confidence_distribution": {
                row[0]: {
                    "count": int(row[1]),
                    "avg_confidence": float(row[2]),
                    "avg_potential_return": float(row[3])
                }
                for row in confidence_distribution_results
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des KPIs XGBoost: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/xgboost-performance/top-opportunities")
async def get_xgboost_top_opportunities(
    db: Session = Depends(get_db),
    limit: int = 20,
    recommendation: Optional[str] = None,
    horizon: Optional[int] = None
):
    """
    Récupère les meilleures opportunités XGBoost.
    """
    try:
        # Construire les conditions WHERE
        where_conditions = []
        if recommendation:
            where_conditions.append(f"recommendation = '{recommendation}'")
        if horizon:
            where_conditions.append(f"horizon_days = {horizon}")
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f"""
        SELECT 
            symbol,
            date,
            horizon_days,
            recommendation,
            confidence_level,
            potential_return,
            risk_score,
            ml_model_name,
            ml_model_version
        FROM ml_opportunities_xgboost
        {where_clause}
        ORDER BY confidence_level DESC, potential_return DESC
        LIMIT {limit}
        """
        
        results = db.execute(text(query)).fetchall()
        
        opportunities = []
        for row in results:
            opportunities.append({
                "symbol": row[0],
                "date": row[1].isoformat() if row[1] else None,
                "horizon_days": int(row[2]),
                "recommendation": row[3],
                "confidence_level": float(row[4]),
                "potential_return": float(row[5]),
                "risk_score": float(row[6]),
                "ml_model_name": row[7],
                "ml_model_version": row[8]
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "opportunities": opportunities,
            "total_returned": len(opportunities)
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des meilleures opportunités XGBoost: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/xgboost-performance/recent-opportunities")
async def get_xgboost_recent_opportunities(
    db: Session = Depends(get_db),
    days: int = 7,
    limit: int = 50
):
    """
    Récupère les opportunités XGBoost récentes.
    """
    try:
        cutoff_date = date.today() - timedelta(days=days)
        
        query = f"""
        SELECT 
            symbol,
            date,
            horizon_days,
            recommendation,
            confidence_level,
            potential_return,
            risk_score,
            created_at
        FROM ml_opportunities_xgboost
        WHERE date >= '{cutoff_date}'
        ORDER BY date DESC, confidence_level DESC
        LIMIT {limit}
        """
        
        results = db.execute(text(query)).fetchall()
        
        opportunities = []
        for row in results:
            opportunities.append({
                "symbol": row[0],
                "date": row[1].isoformat() if row[1] else None,
                "horizon_days": int(row[2]),
                "recommendation": row[3],
                "confidence_level": float(row[4]),
                "potential_return": float(row[5]),
                "risk_score": float(row[6]),
                "created_at": row[7].isoformat() if row[7] else None
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "opportunities": opportunities,
            "total_returned": len(opportunities),
            "date_range": {
                "from": cutoff_date.isoformat(),
                "to": date.today().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des opportunités récentes XGBoost: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")

@router.get("/xgboost-performance/statistics")
async def get_xgboost_statistics(
    db: Session = Depends(get_db)
):
    """
    Récupère des statistiques détaillées sur les opportunités XGBoost.
    """
    try:
        # Statistiques de qualité
        quality_query = """
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN confidence_level >= 0.8 THEN 1 END) as high_confidence,
            COUNT(CASE WHEN confidence_level >= 0.9 THEN 1 END) as very_high_confidence,
            COUNT(CASE WHEN potential_return > 0 THEN 1 END) as positive_return,
            COUNT(CASE WHEN potential_return > 0.05 THEN 1 END) as high_return,
            AVG(confidence_level) as avg_confidence,
            STDDEV(confidence_level) as std_confidence,
            AVG(potential_return) as avg_return,
            STDDEV(potential_return) as std_return
        FROM ml_opportunities_xgboost
        """
        
        quality_result = db.execute(text(quality_query)).fetchone()
        
        # Distribution par modèle
        model_query = """
        SELECT 
            ml_model_name,
            COUNT(*) as count,
            AVG(confidence_level) as avg_confidence,
            AVG(potential_return) as avg_return
        FROM ml_opportunities_xgboost
        GROUP BY ml_model_name
        ORDER BY count DESC
        """
        
        model_results = db.execute(text(model_query)).fetchall()
        
        # Tendances temporelles (derniers 30 jours)
        trend_query = """
        SELECT 
            DATE_TRUNC('day', date) as day,
            COUNT(*) as count,
            AVG(confidence_level) as avg_confidence,
            AVG(potential_return) as avg_return
        FROM ml_opportunities_xgboost
        WHERE date >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE_TRUNC('day', date)
        ORDER BY day DESC
        LIMIT 30
        """
        
        trend_results = db.execute(text(trend_query)).fetchall()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "quality_metrics": {
                "total_opportunities": int(quality_result[0]) if quality_result[0] else 0,
                "high_confidence_count": int(quality_result[1]) if quality_result[1] else 0,
                "very_high_confidence_count": int(quality_result[2]) if quality_result[2] else 0,
                "positive_return_count": int(quality_result[3]) if quality_result[3] else 0,
                "high_return_count": int(quality_result[4]) if quality_result[4] else 0,
                "high_confidence_rate": float(quality_result[1] / quality_result[0]) if quality_result[0] > 0 else 0,
                "very_high_confidence_rate": float(quality_result[2] / quality_result[0]) if quality_result[0] > 0 else 0,
                "positive_return_rate": float(quality_result[3] / quality_result[0]) if quality_result[0] > 0 else 0,
                "avg_confidence": float(quality_result[5]) if quality_result[5] else 0,
                "confidence_std": float(quality_result[6]) if quality_result[6] else 0,
                "avg_return": float(quality_result[7]) if quality_result[7] else 0,
                "return_std": float(quality_result[8]) if quality_result[8] else 0
            },
            "model_performance": {
                row[0]: {
                    "count": int(row[1]),
                    "avg_confidence": float(row[2]),
                    "avg_return": float(row[3])
                }
                for row in model_results
            },
            "daily_trends": [
                {
                    "date": row[0].isoformat() if row[0] else None,
                    "count": int(row[1]),
                    "avg_confidence": float(row[2]),
                    "avg_return": float(row[3])
                }
                for row in trend_results
            ]
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques XGBoost: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne: {str(e)}")
