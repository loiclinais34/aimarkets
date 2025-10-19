#!/usr/bin/env python3
"""
API endpoint pour les opportunités ML XGBoost
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Optional
import pandas as pd
import json
from datetime import date, datetime

# Add the backend directory to Python path
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db

router = APIRouter()

@router.get("/xgboost-opportunities")
async def get_xgboost_opportunities(
    symbol: Optional[str] = Query(None, description="Symbole spécifique"),
    limit: Optional[int] = Query(100, description="Nombre maximum d'opportunités"),
    min_confidence: Optional[float] = Query(0.6, description="Confiance minimale"),
    recommendation: Optional[str] = Query(None, description="Type de recommandation"),
    db: Session = Depends(get_db)
):
    """
    Récupère les opportunités ML générées par XGBoost.
    """
    try:
        # Construire la requête
        where_conditions = []
        params = {}
        
        if symbol:
            where_conditions.append("symbol = :symbol")
            params['symbol'] = symbol
        
        if min_confidence:
            where_conditions.append("confidence_level >= :min_confidence")
            params['min_confidence'] = min_confidence
        
        if recommendation:
            where_conditions.append("recommendation = :recommendation")
            params['recommendation'] = recommendation
        
        where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        query = f"""
        SELECT symbol, date, recommendation, confidence_level, potential_return, 
               risk_score, ml_model_name, ml_model_version, technical_indicators, 
               ml_features, created_at
        FROM ml_opportunities_xgboost
        {where_clause}
        ORDER BY confidence_level DESC, date DESC
        LIMIT :limit
        """
        
        params['limit'] = limit
        
        result = db.execute(text(query), params)
        opportunities = result.fetchall()
        
        # Convertir en format JSON
        opportunities_list = []
        for opp in opportunities:
            opportunity_dict = {
                'symbol': opp.symbol,
                'date': opp.date.isoformat() if opp.date else None,
                'recommendation': opp.recommendation,
                'confidence_level': float(opp.confidence_level),
                'potential_return': float(opp.potential_return) if opp.potential_return else None,
                'risk_score': float(opp.risk_score) if opp.risk_score else None,
                'ml_model_name': opp.ml_model_name,
                'ml_model_version': opp.ml_model_version,
                'technical_indicators': opp.technical_indicators,
                'ml_features': opp.ml_features,
                'created_at': opp.created_at.isoformat() if opp.created_at else None
            }
            opportunities_list.append(opportunity_dict)
        
        return {
            "opportunities": opportunities_list,
            "count": len(opportunities_list),
            "filters": {
                "symbol": symbol,
                "min_confidence": min_confidence,
                "recommendation": recommendation,
                "limit": limit
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des opportunités: {str(e)}")

@router.get("/xgboost-opportunities/summary")
async def get_xgboost_opportunities_summary(db: Session = Depends(get_db)):
    """
    Récupère un résumé des opportunités XGBoost.
    """
    try:
        # Statistiques générales
        stats_query = """
        SELECT 
            COUNT(*) as total_opportunities,
            COUNT(DISTINCT symbol) as unique_symbols,
            AVG(confidence_level) as avg_confidence,
            AVG(potential_return) as avg_return,
            MIN(date) as earliest_date,
            MAX(date) as latest_date
        FROM ml_opportunities_xgboost
        """
        
        stats_result = db.execute(text(stats_query)).fetchone()
        
        # Distribution par recommandation
        rec_query = """
        SELECT recommendation, COUNT(*) as count, AVG(confidence_level) as avg_confidence
        FROM ml_opportunities_xgboost 
        GROUP BY recommendation 
        ORDER BY count DESC
        """
        
        rec_results = db.execute(text(rec_query)).fetchall()
        recommendations = [
            {
                'recommendation': rec.recommendation,
                'count': rec.count,
                'avg_confidence': float(rec.avg_confidence)
            }
            for rec in rec_results
        ]
        
        # Top symboles par nombre d'opportunités
        symbol_query = """
        SELECT symbol, COUNT(*) as count, AVG(confidence_level) as avg_confidence
        FROM ml_opportunities_xgboost 
        GROUP BY symbol 
        ORDER BY count DESC
        LIMIT 10
        """
        
        symbol_results = db.execute(text(symbol_query)).fetchall()
        top_symbols = [
            {
                'symbol': sym.symbol,
                'count': sym.count,
                'avg_confidence': float(sym.avg_confidence)
            }
            for sym in symbol_results
        ]
        
        return {
            "summary": {
                "total_opportunities": stats_result.total_opportunities,
                "unique_symbols": stats_result.unique_symbols,
                "avg_confidence": float(stats_result.avg_confidence),
                "avg_return": float(stats_result.avg_return),
                "date_range": {
                    "earliest": stats_result.earliest_date.isoformat() if stats_result.earliest_date else None,
                    "latest": stats_result.latest_date.isoformat() if stats_result.latest_date else None
                }
            },
            "recommendations": recommendations,
            "top_symbols": top_symbols
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération du résumé: {str(e)}")

@router.get("/xgboost-opportunities/top-performers")
async def get_xgboost_top_performers(
    limit: Optional[int] = Query(10, description="Nombre de top performers"),
    min_confidence: Optional[float] = Query(0.7, description="Confiance minimale"),
    db: Session = Depends(get_db)
):
    """
    Récupère les meilleures opportunités XGBoost.
    """
    try:
        query = """
        SELECT symbol, date, recommendation, confidence_level, potential_return, 
               risk_score, technical_indicators, ml_features
        FROM ml_opportunities_xgboost
        WHERE confidence_level >= :min_confidence
        ORDER BY confidence_level DESC, potential_return DESC
        LIMIT :limit
        """
        
        result = db.execute(text(query), {
            'min_confidence': min_confidence,
            'limit': limit
        })
        
        opportunities = result.fetchall()
        
        top_performers = []
        for opp in opportunities:
            performer_dict = {
                'symbol': opp.symbol,
                'date': opp.date.isoformat() if opp.date else None,
                'recommendation': opp.recommendation,
                'confidence_level': float(opp.confidence_level),
                'potential_return': float(opp.potential_return) if opp.potential_return else None,
                'risk_score': float(opp.risk_score) if opp.risk_score else None,
                'technical_indicators': opp.technical_indicators,
                'ml_features': opp.ml_features
            }
            top_performers.append(performer_dict)
        
        return {
            "top_performers": top_performers,
            "count": len(top_performers),
            "min_confidence": min_confidence
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des top performers: {str(e)}")

@router.get("/xgboost-opportunities/test")
async def test_xgboost_opportunities(db: Session = Depends(get_db)):
    """
    Test endpoint pour vérifier la connectivité et les données XGBoost.
    """
    try:
        # Vérifier si la table existe
        table_check = db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'ml_opportunities_xgboost'
            )
        """)).scalar()
        
        if not table_check:
            return {"status": "error", "message": "Table ml_opportunities_xgboost n'existe pas"}
        
        # Compter les enregistrements
        count = db.execute(text("SELECT COUNT(*) FROM ml_opportunities_xgboost")).scalar()
        
        # Récupérer un échantillon
        sample = db.execute(text("""
            SELECT symbol, recommendation, confidence_level, potential_return
            FROM ml_opportunities_xgboost 
            LIMIT 5
        """)).fetchall()
        
        sample_data = [
            {
                'symbol': row.symbol,
                'recommendation': row.recommendation,
                'confidence_level': float(row.confidence_level),
                'potential_return': float(row.potential_return) if row.potential_return else None
            }
            for row in sample
        ]
        
        return {
            "status": "success",
            "table_exists": True,
            "total_records": count,
            "sample_data": sample_data
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Erreur: {str(e)}"}
