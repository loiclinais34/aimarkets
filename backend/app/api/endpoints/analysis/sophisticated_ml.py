#!/usr/bin/env python3
"""
Endpoint API pour le nouveau système ML sophistiqué.
Intègre les modèles ML, simulations Monte Carlo et indicateurs techniques avancés.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import json
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

from app.core.database import get_db
from app.models.historical_opportunities import HistoricalOpportunities
from app.models.advanced_technical_indicators import AdvancedTechnicalIndicators
from app.models.ml_models_v2 import MLModelsV2
from app.models.monte_carlo_simulations_v2 import MonteCarloSimulationsV2

router = APIRouter()

@router.get("/ml/recommendations", response_model=Dict[str, Any])
async def get_ml_recommendations(
    symbols: Optional[str] = None,
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Génère des recommandations ML sophistiquées pour les symboles demandés.
    """
    try:
        # Paramètres par défaut
        if not symbols:
            symbols = "AAPL,MSFT,GOOGL,TSLA,NVDA"
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        symbol_list = [s.strip() for s in symbols.split(',')]
        
        recommendations = {}
        
        for symbol in symbol_list:
            try:
                # Récupérer les données techniques
                tech_data = db.query(AdvancedTechnicalIndicators).filter(
                    AdvancedTechnicalIndicators.symbol == symbol,
                    AdvancedTechnicalIndicators.date == date
                ).first()
                
                if not tech_data:
                    recommendations[symbol] = {
                        'error': 'Données techniques non disponibles',
                        'recommendation': 'HOLD',
                        'confidence_level': 0.5
                    }
                    continue
                
                # Récupérer les résultats Monte Carlo
                mc_data = db.query(MonteCarloSimulationsV2).filter(
                    MonteCarloSimulationsV2.status == 'completed'
                ).order_by(MonteCarloSimulationsV2.created_at.desc()).first()
                
                # Générer la recommandation basée sur les données
                recommendation = generate_sophisticated_recommendation(tech_data, mc_data)
                recommendations[symbol] = recommendation
                
            except Exception as e:
                recommendations[symbol] = {
                    'error': str(e),
                    'recommendation': 'HOLD',
                    'confidence_level': 0.5
                }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'date': date,
            'recommendations': recommendations,
            'total_symbols': len(symbol_list),
            'successful_recommendations': len([r for r in recommendations.values() if 'error' not in r])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération des recommandations ML: {str(e)}"
        )

def generate_sophisticated_recommendation(tech_data, mc_data) -> Dict[str, Any]:
    """Génère une recommandation sophistiquée basée sur les données techniques et Monte Carlo"""
    
    # Calculer un score composite
    score = 0
    confidence = 0.5
    factors = []
    
    # RSI Analysis
    if tech_data.rsi_14:
        if tech_data.rsi_14 < 30:
            score += 2
            confidence += 0.1
            factors.append(f"RSI survente ({tech_data.rsi_14:.1f})")
        elif tech_data.rsi_14 > 70:
            score -= 2
            confidence += 0.1
            factors.append(f"RSI surachat ({tech_data.rsi_14:.1f})")
        else:
            factors.append(f"RSI neutre ({tech_data.rsi_14:.1f})")
    
    # MACD Analysis
    if tech_data.macd_line and tech_data.macd_signal:
        if tech_data.macd_line > tech_data.macd_signal:
            score += 1
            confidence += 0.05
            factors.append("MACD bullish")
        else:
            score -= 1
            confidence += 0.05
            factors.append("MACD bearish")
    
    # Bollinger Bands Analysis
    if tech_data.bollinger_upper and tech_data.bollinger_lower:
        bb_width = (tech_data.bollinger_upper - tech_data.bollinger_lower) / tech_data.bollinger_middle if tech_data.bollinger_middle else 0
        if bb_width > 0.1:
            confidence += 0.05
            factors.append(f"Volatilité élevée (BB width: {bb_width:.3f})")
    
    # Stochastic Analysis
    if tech_data.stochastic_k and tech_data.stochastic_d:
        if tech_data.stochastic_k < 20 and tech_data.stochastic_d < 20:
            score += 1
            confidence += 0.05
            factors.append("Stochastic survente")
        elif tech_data.stochastic_k > 80 and tech_data.stochastic_d > 80:
            score -= 1
            confidence += 0.05
            factors.append("Stochastic surachat")
    
    # Monte Carlo Analysis
    if mc_data and hasattr(mc_data, 'statistics') and mc_data.statistics:
        stats = mc_data.statistics if isinstance(mc_data.statistics, dict) else {}
        sharpe_ratio = stats.get('sharpe_ratio', 0)
        if sharpe_ratio > 1.0:
            score += 1
            confidence += 0.1
            factors.append(f"Sharpe ratio excellent ({sharpe_ratio:.3f})")
        elif sharpe_ratio > 0.5:
            score += 0.5
            confidence += 0.05
            factors.append(f"Sharpe ratio bon ({sharpe_ratio:.3f})")
        elif sharpe_ratio < 0:
            score -= 1
            confidence += 0.05
            factors.append(f"Sharpe ratio négatif ({sharpe_ratio:.3f})")
    
    # Déterminer la recommandation finale
    if score >= 3 and confidence >= 0.7:
        recommendation = 'BUY_STRONG'
        reasoning = "Signal d'achat fort avec haute confiance"
    elif score >= 2 and confidence >= 0.6:
        recommendation = 'BUY_MODERATE'
        reasoning = "Signal d'achat modéré avec confiance moyenne"
    elif score >= 1 and confidence >= 0.5:
        recommendation = 'BUY_WEAK'
        reasoning = "Signal d'achat faible"
    elif score <= -3 and confidence >= 0.7:
        recommendation = 'SELL_STRONG'
        reasoning = "Signal de vente fort avec haute confiance"
    elif score <= -2 and confidence >= 0.6:
        recommendation = 'SELL_WEAK'
        reasoning = "Signal de vente modéré"
    else:
        recommendation = 'HOLD'
        reasoning = "Signal neutre, maintien recommandé"
    
    return {
        'symbol': tech_data.symbol,
        'date': tech_data.date.isoformat(),
        'recommendation': recommendation,
        'confidence_level': min(confidence, 1.0),
        'composite_score': score,
        'reasoning': reasoning,
        'key_factors': factors,
        'technical_indicators': {
            'rsi_14': tech_data.rsi_14,
            'macd_line': tech_data.macd_line,
            'macd_signal': tech_data.macd_signal,
            'stochastic_k': tech_data.stochastic_k,
            'stochastic_d': tech_data.stochastic_d,
            'bollinger_width': bb_width if 'bb_width' in locals() else None,
            'atr_14': tech_data.atr_14,
            'volatility_20': tech_data.volatility_20
        },
        'monte_carlo_metrics': {
            'sharpe_ratio': stats.get('sharpe_ratio', 0) if mc_data and hasattr(mc_data, 'statistics') else None,
            'max_drawdown': mc_data.max_drawdown if mc_data else None,
            'var_95': mc_data.var_95 if mc_data else None
        } if mc_data else None
    }

@router.get("/ml/models/performance", response_model=Dict[str, Any])
async def get_ml_models_performance(db: Session = Depends(get_db)):
    """
    Récupère les performances des modèles ML entraînés.
    """
    try:
        models = db.query(MLModelsV2).filter(
            MLModelsV2.is_active == True
        ).order_by(MLModelsV2.created_at.desc()).all()
        
        model_performance = []
        
        for model in models:
            model_data = {
                'model_name': model.model_name,
                'model_type': model.model_type,
                'model_version': model.model_version,
                'target_column': model.target_column,
                'training_score': model.training_score,
                'validation_score': model.validation_score,
                'test_score': model.test_score,
                'sharpe_ratio': model.sharpe_ratio,
                'max_drawdown': model.max_drawdown,
                'win_rate': model.win_rate,
                'profit_factor': model.profit_factor,
                'model_parameters': model.model_parameters,
                'feature_columns': model.feature_columns,
                'feature_importance': model.feature_importance,
                'created_at': model.created_at.isoformat(),
                'is_active': model.is_active,
                'is_production': model.is_production
            }
            model_performance.append(model_data)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_models': len(model_performance),
            'models': model_performance,
            'summary': {
                'best_training_score': max([m['training_score'] for m in model_performance if m['training_score']], default=0),
                'best_test_score': max([m['test_score'] for m in model_performance if m['test_score']], default=0),
                'best_sharpe_ratio': max([m['sharpe_ratio'] for m in model_performance if m['sharpe_ratio']], default=0),
                'active_models': len([m for m in model_performance if m['is_active']]),
                'production_models': len([m for m in model_performance if m['is_production']])
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des performances ML: {str(e)}"
        )

@router.get("/ml/monte-carlo/results", response_model=Dict[str, Any])
async def get_monte_carlo_results(
    symbol: Optional[str] = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Récupère les résultats des simulations Monte Carlo.
    """
    try:
        query = db.query(MonteCarloSimulationsV2).filter(
            MonteCarloSimulationsV2.status == 'COMPLETED'
        )
        
        if symbol:
            query = query.filter(MonteCarloSimulationsV2.symbol == symbol)
        
        simulations = query.order_by(MonteCarloSimulationsV2.created_at.desc()).limit(limit).all()
        
        simulation_results = []
        
        for sim in simulations:
            sim_data = {
                'simulation_name': sim.simulation_name,
                'symbol': sim.symbol,
                'num_simulations': sim.num_simulations,
                'simulation_horizon': sim.simulation_horizon,
                'avg_return': sim.avg_return,
                'std_return': sim.std_return,
                'sharpe_ratio': sim.sharpe_ratio,
                'max_drawdown': sim.max_drawdown,
                'var_95': sim.var_95,
                'cvar_95': sim.cvar_95,
                'created_at': sim.created_at.isoformat(),
                'simulation_parameters': sim.simulation_parameters,
                'results': sim.results,
                'statistics': sim.statistics
            }
            simulation_results.append(sim_data)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_simulations': len(simulation_results),
            'simulations': simulation_results,
            'summary': {
                'best_avg_return': max([s['avg_return'] for s in simulation_results if s['avg_return']], default=0),
                'best_sharpe_ratio': max([s['sharpe_ratio'] for s in simulation_results if s['sharpe_ratio']], default=0),
                'worst_max_drawdown': min([s['max_drawdown'] for s in simulation_results if s['max_drawdown']], default=0),
                'avg_var_95': np.mean([s['var_95'] for s in simulation_results if s['var_95']]) if simulation_results else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des résultats Monte Carlo: {str(e)}"
        )

@router.get("/ml/technical-indicators", response_model=Dict[str, Any])
async def get_technical_indicators(
    symbol: str,
    date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Récupère les indicateurs techniques avancés pour un symbole.
    """
    try:
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
        
        indicators = db.query(AdvancedTechnicalIndicators).filter(
            AdvancedTechnicalIndicators.symbol == symbol,
            AdvancedTechnicalIndicators.date == date
        ).first()
        
        if not indicators:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Indicateurs techniques non trouvés pour {symbol} à la date {date}"
            )
        
        return {
            'timestamp': datetime.now().isoformat(),
            'symbol': indicators.symbol,
            'date': indicators.date.isoformat(),
            'indicators': {
                'sma_5': indicators.sma_5,
                'sma_10': indicators.sma_10,
                'sma_20': indicators.sma_20,
                'sma_50': indicators.sma_50,
                'sma_200': indicators.sma_200,
                'ema_5': indicators.ema_5,
                'ema_10': indicators.ema_10,
                'ema_20': indicators.ema_20,
                'ema_50': indicators.ema_50,
                'ema_200': indicators.ema_200,
                'rsi_14': indicators.rsi_14,
                'rsi_21': indicators.rsi_21,
                'macd_line': indicators.macd_line,
                'macd_signal': indicators.macd_signal,
                'macd_histogram': indicators.macd_histogram,
                'bollinger_upper': indicators.bollinger_upper,
                'bollinger_middle': indicators.bollinger_middle,
                'bollinger_lower': indicators.bollinger_lower,
                'bollinger_width': indicators.bollinger_width,
                'atr_14': indicators.atr_14,
                'volatility_20': indicators.volatility_20,
                'volume_sma_20': indicators.volume_sma_20,
                'volume_ratio': indicators.volume_ratio,
                'obv': indicators.obv,
                'vwap': indicators.vwap,
                'stochastic_k': indicators.stochastic_k,
                'stochastic_d': indicators.stochastic_d,
                'williams_r': indicators.williams_r,
                'cci': indicators.cci,
                'roc': indicators.roc,
                'support_level': indicators.support_level,
                'resistance_level': indicators.resistance_level,
                'pivot_point': indicators.pivot_point
            },
            'candlestick_patterns': {
                'doji': indicators.doji,
                'hammer': indicators.hammer,
                'shooting_star': indicators.shooting_star,
                'engulfing_bullish': indicators.engulfing_bullish,
                'engulfing_bearish': indicators.engulfing_bearish
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des indicateurs techniques: {str(e)}"
        )

@router.get("/ml/system/status", response_model=Dict[str, Any])
async def get_system_status(db: Session = Depends(get_db)):
    """
    Récupère le statut global du système ML sophistiqué.
    """
    try:
        # Compter les différents composants
        technical_indicators_count = db.query(AdvancedTechnicalIndicators).count()
        ml_models_count = db.query(MLModelsV2).filter(MLModelsV2.is_active == True).count()
        monte_carlo_simulations_count = db.query(MonteCarloSimulationsV2).filter(
            MonteCarloSimulationsV2.status == 'COMPLETED'
        ).count()
        
        # Récupérer les dernières activités
        latest_model = db.query(MLModelsV2).filter(
            MLModelsV2.is_active == True
        ).order_by(MLModelsV2.created_at.desc()).first()
        
        latest_simulation = db.query(MonteCarloSimulationsV2).filter(
            MonteCarloSimulationsV2.status == 'COMPLETED'
        ).order_by(MonteCarloSimulationsV2.created_at.desc()).first()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'system_status': 'OPERATIONAL',
            'components': {
                'technical_indicators': {
                    'count': technical_indicators_count,
                    'status': 'ACTIVE'
                },
                'ml_models': {
                    'count': ml_models_count,
                    'status': 'ACTIVE' if ml_models_count > 0 else 'INACTIVE',
                    'latest_model': latest_model.model_name if latest_model else None,
                    'latest_training': latest_model.created_at.isoformat() if latest_model else None
                },
                'monte_carlo_simulations': {
                    'count': monte_carlo_simulations_count,
                    'status': 'ACTIVE' if monte_carlo_simulations_count > 0 else 'INACTIVE',
                    'latest_simulation': latest_simulation.simulation_name if latest_simulation else None,
                    'latest_run': latest_simulation.created_at.isoformat() if latest_simulation else None
                }
            },
            'performance_summary': {
                'best_ml_training_score': latest_model.training_score if latest_model else 0,
                'best_avg_return': latest_simulation.avg_return if latest_simulation else 0,
                'total_data_points': technical_indicators_count
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du statut système: {str(e)}"
        )
