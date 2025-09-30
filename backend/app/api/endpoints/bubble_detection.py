"""
API endpoints pour la détection de bulles spéculatives
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta
import logging

from app.core.database import get_db
from app.models.bubble_indicators import BubbleIndicators
from app.models.financial_ratios import FinancialRatios
from app.services.bubble_detection import BubbleDetectionService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Bubble Detection"])


@router.get("/bubble-risk/{symbol}")
async def get_bubble_risk(
    symbol: str,
    analysis_date: Optional[str] = Query(None, description="Date d'analyse (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère le score de risque de bulle pour un symbole
    
    Args:
        symbol: Symbole du titre
        analysis_date: Date d'analyse (par défaut aujourd'hui)
        
    Returns:
        Dict avec le score de bulle et tous les détails
    """
    try:
        # Déterminer la date d'analyse
        if analysis_date:
            target_date = datetime.strptime(analysis_date, '%Y-%m-%d').date()
        else:
            target_date = date.today()
        
        # Récupérer les indicateurs depuis la base
        bubble_indicator = db.query(BubbleIndicators).filter(
            BubbleIndicators.symbol == symbol.upper(),
            BubbleIndicators.analysis_date == target_date
        ).first()
        
        if not bubble_indicator:
            # Si pas trouvé, calculer en temps réel
            logger.info(f"Indicateurs de bulle non trouvés pour {symbol}, calcul en temps réel")
            bubble_service = BubbleDetectionService(db)
            bubble_data = bubble_service.analyze_bubble_risk(symbol.upper(), target_date, db)
            
            if 'error' in bubble_data:
                raise HTTPException(status_code=500, detail=f"Erreur lors du calcul: {bubble_data['error']}")
            
            # Sauvegarder pour la prochaine fois
            bubble_service.save_bubble_indicators(bubble_data, db)
            
            return {
                'symbol': symbol.upper(),
                'analysis_date': target_date.isoformat(),
                'bubble_score': bubble_data['bubble_score'],
                'bubble_level': bubble_data['bubble_level'],
                'scores': bubble_data['scores'],
                'details': bubble_data['details'],
                'source': 'real_time_calculation'
            }
        
        # Retourner les indicateurs stockés
        return {
            'symbol': bubble_indicator.symbol,
            'analysis_date': bubble_indicator.analysis_date.isoformat(),
            'bubble_score': float(bubble_indicator.bubble_score),
            'bubble_level': bubble_indicator.bubble_level,
            'scores': {
                'valuation': float(bubble_indicator.valuation_score),
                'momentum': float(bubble_indicator.momentum_score),
                'statistical': float(bubble_indicator.statistical_score),
                'sentiment': float(bubble_indicator.sentiment_score)
            },
            'ratios': {
                'pe_ratio': float(bubble_indicator.pe_ratio) if bubble_indicator.pe_ratio else None,
                'ps_ratio': float(bubble_indicator.ps_ratio) if bubble_indicator.ps_ratio else None,
                'pb_ratio': float(bubble_indicator.pb_ratio) if bubble_indicator.pb_ratio else None,
                'peg_ratio': float(bubble_indicator.peg_ratio) if bubble_indicator.peg_ratio else None
            },
            'momentum_indicators': {
                'price_growth_30d': float(bubble_indicator.price_growth_30d) if bubble_indicator.price_growth_30d else None,
                'price_growth_90d': float(bubble_indicator.price_growth_90d) if bubble_indicator.price_growth_90d else None,
                'price_growth_180d': float(bubble_indicator.price_growth_180d) if bubble_indicator.price_growth_180d else None,
                'rsi_14d': float(bubble_indicator.rsi_14d) if bubble_indicator.rsi_14d else None,
                'distance_from_sma50': float(bubble_indicator.distance_from_sma50) if bubble_indicator.distance_from_sma50 else None,
                'distance_from_sma200': float(bubble_indicator.distance_from_sma200) if bubble_indicator.distance_from_sma200 else None
            },
            'statistical_indicators': {
                'price_zscore': float(bubble_indicator.price_zscore) if bubble_indicator.price_zscore else None,
                'volatility_ratio': float(bubble_indicator.volatility_ratio) if bubble_indicator.volatility_ratio else None,
                'returns_skewness': float(bubble_indicator.returns_skewness) if bubble_indicator.returns_skewness else None,
                'returns_kurtosis': float(bubble_indicator.returns_kurtosis) if bubble_indicator.returns_kurtosis else None
            },
            'details': {
                'valuation': bubble_indicator.valuation_details,
                'momentum': bubble_indicator.momentum_details,
                'statistical': bubble_indicator.statistical_details,
                'sentiment': bubble_indicator.sentiment_details
            },
            'source': 'database'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des indicateurs de bulle pour {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bubble-risk/alerts/all")
async def get_bubble_alerts(
    min_score: float = Query(30.0, ge=0, le=100, description="Score minimum"),
    levels: Optional[str] = Query(None, description="Niveaux séparés par virgule (WATCH,RISK,PROBABLE,CRITICAL)"),
    limit: int = Query(50, ge=1, le=200, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère les alertes de bulle pour tous les symboles
    
    Args:
        min_score: Score minimum de bulle
        levels: Niveaux de bulle à filtrer
        limit: Nombre maximum de résultats
        
    Returns:
        Dict avec les alertes de bulle
    """
    try:
        # Construire la requête
        query = db.query(BubbleIndicators).filter(
            BubbleIndicators.bubble_score >= min_score
        )
        
        # Filtrer par niveaux si spécifié
        if levels:
            level_list = [level.strip().upper() for level in levels.split(',')]
            query = query.filter(BubbleIndicators.bubble_level.in_(level_list))
        
        # Ordonner par score décroissant
        query = query.order_by(BubbleIndicators.bubble_score.desc())
        
        # Limiter les résultats
        indicators = query.limit(limit).all()
        
        # Formater les résultats
        results = []
        for indicator in indicators:
            results.append({
                'symbol': indicator.symbol,
                'analysis_date': indicator.analysis_date.isoformat(),
                'bubble_score': float(indicator.bubble_score),
                'bubble_level': indicator.bubble_level,
                'valuation_score': float(indicator.valuation_score),
                'momentum_score': float(indicator.momentum_score),
                'statistical_score': float(indicator.statistical_score),
                'sentiment_score': float(indicator.sentiment_score),
                'pe_ratio': float(indicator.pe_ratio) if indicator.pe_ratio else None,
                'ps_ratio': float(indicator.ps_ratio) if indicator.ps_ratio else None,
                'pb_ratio': float(indicator.pb_ratio) if indicator.pb_ratio else None,
                'rsi_14d': float(indicator.rsi_14d) if indicator.rsi_14d else None
            })
        
        return {
            'total_alerts': len(results),
            'filters_applied': {
                'min_score': min_score,
                'levels': levels,
                'limit': limit
            },
            'alerts': results
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des alertes de bulle: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bubble-risk/sector/{sector}")
async def get_sector_bubble_overview(
    sector: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Vue d'ensemble des bulles pour un secteur
    
    Args:
        sector: Nom du secteur (ex: Technology)
        
    Returns:
        Dict avec les statistiques sectorielles
    """
    try:
        # Récupérer tous les symboles du secteur via financial_ratios
        sector_symbols = db.query(FinancialRatios.symbol).filter(
            FinancialRatios.sector == sector
        ).distinct().all()
        
        symbol_list = [s[0] for s in sector_symbols]
        
        if not symbol_list:
            return {
                'sector': sector,
                'total_symbols': 0,
                'message': 'Aucun symbole trouvé pour ce secteur'
            }
        
        # Récupérer les indicateurs de bulle pour ces symboles
        today = date.today()
        indicators = db.query(BubbleIndicators).filter(
            BubbleIndicators.symbol.in_(symbol_list),
            BubbleIndicators.analysis_date == today
        ).all()
        
        if not indicators:
            return {
                'sector': sector,
                'total_symbols': len(symbol_list),
                'message': 'Aucun indicateur de bulle calculé pour ce secteur'
            }
        
        # Calculer les statistiques
        scores = [float(i.bubble_score) for i in indicators]
        levels_count = {}
        for indicator in indicators:
            level = indicator.bubble_level
            levels_count[level] = levels_count.get(level, 0) + 1
        
        return {
            'sector': sector,
            'analysis_date': today.isoformat(),
            'total_symbols': len(symbol_list),
            'symbols_analyzed': len(indicators),
            'statistics': {
                'avg_bubble_score': sum(scores) / len(scores),
                'max_bubble_score': max(scores),
                'min_bubble_score': min(scores),
                'levels_distribution': levels_count
            },
            'top_risks': [
                {
                    'symbol': i.symbol,
                    'bubble_score': float(i.bubble_score),
                    'bubble_level': i.bubble_level
                }
                for i in sorted(indicators, key=lambda x: x.bubble_score, reverse=True)[:10]
            ]
        }
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'aperçu sectoriel: {e}")
        raise HTTPException(status_code=500, detail=str(e))
