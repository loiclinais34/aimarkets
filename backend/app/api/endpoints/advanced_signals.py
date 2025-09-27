"""
Endpoints API pour les signaux avancés.

Ce module expose les endpoints REST pour la gestion des signaux avancés,
incluant la génération, la récupération et l'analyse des signaux.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
import logging
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...services.advanced_signal_service import AdvancedSignalService
from ...services.polygon_service import PolygonService
from ...utils.json_encoder import make_json_safe

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/generate/{symbol}")
async def generate_advanced_signal(
    symbol: str,
    days: int = Query(252, description="Nombre de jours de données historiques"),
    include_ml: bool = Query(True, description="Inclure l'intégration ML"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Génère un signal avancé pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        days: Nombre de jours de données historiques
        include_ml: Inclure l'intégration ML
        db: Session de base de données
        
    Returns:
        Signal avancé généré
    """
    try:
        # Récupérer les données historiques
        data_service = PolygonService()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days + 50)
        
        historical_data = data_service.get_historical_data(
            symbol=symbol,
            from_date=start_date.strftime('%Y-%m-%d'),
            to_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not historical_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune donnée historique trouvée pour {symbol}"
            )
        
        # Convertir en DataFrame
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Préparer les données
        high = df['high']
        low = df['low']
        close = df['close']
        open_prices = df['open']
        volume = df['volume'] if 'volume' in df.columns else None
        
        # Récupérer la prédiction ML si demandée
        ml_prediction = None
        if include_ml:
            try:
                # TODO: Intégrer avec le service ML existant
                # Pour l'instant, on simule une prédiction
                ml_prediction = {
                    "prediction": 1,  # 1 = opportunité positive, 0 = négative
                    "confidence": 0.75,
                    "model_name": "RandomForest_v1.0",
                    "model_type": "classification"
                }
            except Exception as e:
                logger.warning(f"Impossible de récupérer la prédiction ML: {e}")
        
        # Générer et sauvegarder le signal
        signal_service = AdvancedSignalService(db)
        saved_signal = signal_service.generate_and_save_signal(
            symbol=symbol,
            high=high,
            low=low,
            close=close,
            open_prices=open_prices,
            volume=volume,
            ml_prediction=ml_prediction
        )
        
        # Formater la réponse
        response = {
            "symbol": symbol,
            "signal_id": saved_signal.id,
            "signal_type": saved_signal.signal_type,
            "score": saved_signal.score,
            "confidence": saved_signal.confidence,
            "confidence_level": saved_signal.confidence_level,
            "strength": saved_signal.strength,
            "risk_level": saved_signal.risk_level,
            "time_horizon": saved_signal.time_horizon,
            "reasoning": saved_signal.reasoning,
            "indicators_used": saved_signal.indicators_used,
            "individual_signals": saved_signal.individual_signals,
            "ml_signal": saved_signal.ml_signal,
            "current_price": float(close.iloc[-1]),
            "analysis_date": saved_signal.created_at.isoformat(),
            "data_period": {
                "start": df.index[0].isoformat(),
                "end": df.index[-1].isoformat(),
                "days": len(df)
            }
        }
        
        return make_json_safe(response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la génération du signal pour {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la génération du signal: {str(e)}"
        )


@router.get("/latest/{symbol}")
async def get_latest_signal(
    symbol: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère le dernier signal pour un symbole.
    
    Args:
        symbol: Symbole à rechercher
        db: Session de base de données
        
    Returns:
        Dernier signal
    """
    try:
        signal_service = AdvancedSignalService(db)
        latest_signal = signal_service.get_latest_signal(symbol)
        
        if not latest_signal:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun signal trouvé pour {symbol}"
            )
        
        response = {
            "symbol": symbol,
            "signal_id": latest_signal.id,
            "signal_type": latest_signal.signal_type,
            "score": latest_signal.score,
            "confidence": latest_signal.confidence,
            "confidence_level": latest_signal.confidence_level,
            "strength": latest_signal.strength,
            "risk_level": latest_signal.risk_level,
            "time_horizon": latest_signal.time_horizon,
            "reasoning": latest_signal.reasoning,
            "indicators_used": latest_signal.indicators_used,
            "individual_signals": latest_signal.individual_signals,
            "ml_signal": latest_signal.ml_signal,
            "created_at": latest_signal.created_at.isoformat(),
            "updated_at": latest_signal.updated_at.isoformat()
        }
        
        return make_json_safe(response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du dernier signal pour {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du signal: {str(e)}"
        )


@router.get("/history/{symbol}")
async def get_signal_history(
    symbol: str,
    days: int = Query(30, description="Nombre de jours d'historique"),
    limit: int = Query(100, description="Nombre maximum de résultats"),
    signal_type: Optional[str] = Query(None, description="Filtrer par type de signal"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère l'historique des signaux pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        days: Nombre de jours d'historique
        limit: Nombre maximum de résultats
        signal_type: Filtrer par type de signal
        db: Session de base de données
        
    Returns:
        Historique des signaux
    """
    try:
        signal_service = AdvancedSignalService(db)
        
        # Calculer les dates
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Récupérer les signaux
        signals = signal_service.get_signals(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            signal_type=signal_type,
            limit=limit
        )
        
        # Formater la réponse
        signals_data = []
        for signal in signals:
            signals_data.append({
                "signal_id": signal.id,
                "signal_type": signal.signal_type,
                "score": signal.score,
                "confidence": signal.confidence,
                "confidence_level": signal.confidence_level,
                "strength": signal.strength,
                "risk_level": signal.risk_level,
                "time_horizon": signal.time_horizon,
                "reasoning": signal.reasoning,
                "indicators_used": signal.indicators_used,
                "created_at": signal.created_at.isoformat()
            })
        
        response = {
            "symbol": symbol,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "total_signals": len(signals_data),
            "signals": signals_data,
            "filters": {
                "signal_type": signal_type,
                "limit": limit
            }
        }
        
        return make_json_safe(response)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'historique pour {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération de l'historique: {str(e)}"
        )


@router.get("/metrics/{symbol}")
async def get_signal_metrics(
    symbol: str,
    days: int = Query(30, description="Nombre de jours pour l'analyse"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère les métriques de performance des signaux pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        days: Nombre de jours pour l'analyse
        db: Session de base de données
        
    Returns:
        Métriques de performance
    """
    try:
        signal_service = AdvancedSignalService(db)
        metrics = signal_service.calculate_signal_metrics(symbol, days)
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune métrique trouvée pour {symbol}"
            )
        
        return make_json_safe(metrics)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des métriques pour {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des métriques: {str(e)}"
        )


@router.get("/summary/{symbol}")
async def get_signal_summary(
    symbol: str,
    days: int = Query(7, description="Nombre de jours pour le résumé"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère un résumé des signaux pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        days: Nombre de jours pour le résumé
        db: Session de base de données
        
    Returns:
        Résumé des signaux
    """
    try:
        signal_service = AdvancedSignalService(db)
        summary = signal_service.get_signal_summary(symbol, days)
        
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun résumé trouvé pour {symbol}"
            )
        
        return make_json_safe(summary)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du résumé pour {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération du résumé: {str(e)}"
        )


@router.get("/configurations")
async def get_signal_configurations(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère toutes les configurations de signaux.
    
    Args:
        db: Session de base de données
        
    Returns:
        Liste des configurations
    """
    try:
        signal_service = AdvancedSignalService(db)
        configurations = signal_service.get_signal_configurations()
        
        configurations_data = []
        for config in configurations:
            configurations_data.append({
                "id": config.id,
                "name": config.name,
                "description": config.description,
                "weights": config.weights,
                "scoring_thresholds": config.scoring_thresholds,
                "confidence_thresholds": config.confidence_thresholds,
                "ml_integration": config.ml_integration,
                "is_active": config.is_active,
                "created_by": config.created_by,
                "created_at": config.created_at.isoformat(),
                "updated_at": config.updated_at.isoformat()
            })
        
        response = {
            "total_configurations": len(configurations_data),
            "configurations": configurations_data
        }
        
        return make_json_safe(response)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des configurations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des configurations: {str(e)}"
        )


@router.post("/configurations")
async def create_signal_configuration(
    name: str,
    description: str,
    weights: Dict[str, float],
    scoring_thresholds: Dict[str, float],
    confidence_thresholds: Dict[str, float],
    ml_integration: Optional[Dict[str, Any]] = None,
    created_by: Optional[str] = None,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Crée une nouvelle configuration de signaux.
    
    Args:
        name: Nom de la configuration
        description: Description
        weights: Poids des indicateurs
        scoring_thresholds: Seuils de scoring
        confidence_thresholds: Seuils de confiance
        ml_integration: Configuration ML (optionnel)
        created_by: Créateur (optionnel)
        db: Session de base de données
        
    Returns:
        Configuration créée
    """
    try:
        signal_service = AdvancedSignalService(db)
        configuration = signal_service.save_signal_configuration(
            name=name,
            description=description,
            weights=weights,
            scoring_thresholds=scoring_thresholds,
            confidence_thresholds=confidence_thresholds,
            ml_integration=ml_integration,
            created_by=created_by
        )
        
        response = {
            "id": configuration.id,
            "name": configuration.name,
            "description": configuration.description,
            "weights": configuration.weights,
            "scoring_thresholds": configuration.scoring_thresholds,
            "confidence_thresholds": configuration.confidence_thresholds,
            "ml_integration": configuration.ml_integration,
            "is_active": configuration.is_active,
            "created_by": configuration.created_by,
            "created_at": configuration.created_at.isoformat()
        }
        
        return make_json_safe(response)
        
    except Exception as e:
        logger.error(f"Erreur lors de la création de la configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création de la configuration: {str(e)}"
        )


@router.get("/performance/{symbol}")
async def get_signal_performance(
    symbol: str,
    days: int = Query(30, description="Nombre de jours pour l'analyse"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Récupère les performances des signaux pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        days: Nombre de jours pour l'analyse
        db: Session de base de données
        
    Returns:
        Performances des signaux
    """
    try:
        signal_service = AdvancedSignalService(db)
        performances = signal_service.get_signal_performance(symbol, days)
        
        performances_data = []
        for perf in performances:
            performances_data.append({
                "signal_id": perf.signal_id,
                "entry_price": perf.entry_price,
                "exit_price": perf.exit_price,
                "entry_date": perf.entry_date.isoformat() if perf.entry_date else None,
                "exit_date": perf.exit_date.isoformat() if perf.exit_date else None,
                "return_percentage": perf.return_percentage,
                "max_drawdown": perf.max_drawdown,
                "holding_period_days": perf.holding_period_days,
                "was_profitable": perf.was_profitable,
                "performance_notes": perf.performance_notes,
                "created_at": perf.created_at.isoformat()
            })
        
        response = {
            "symbol": symbol,
            "period_days": days,
            "total_performances": len(performances_data),
            "performances": performances_data
        }
        
        return make_json_safe(response)
        
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des performances pour {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des performances: {str(e)}"
        )
