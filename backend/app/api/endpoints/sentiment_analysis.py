"""
Endpoints API pour l'analyse de sentiment.

Ce module expose les endpoints pour accéder aux fonctionnalités
d'analyse de sentiment et de volatilité.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ...core.database import get_db
from ...services.sentiment_analysis import GARCHModels, MonteCarloSimulation, MarkovChainAnalysis, VolatilityForecaster
from ...models.sentiment_analysis import SentimentAnalysis, GARCHModels as GARCHModelsModel, MonteCarloSimulations, MarkovChainAnalysis as MarkovChainAnalysisModel, VolatilityForecasts
from ...utils.json_encoder import make_json_safe

router = APIRouter()


@router.get("/garch/{symbol}")
async def get_garch_analysis(
    symbol: str,
    model_type: str = "GARCH",
    period: int = 252,
    db: Session = Depends(get_db)
):
    """
    Récupère l'analyse GARCH pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        model_type: Type de modèle GARCH ("GARCH", "EGARCH", "GJR-GARCH")
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant l'analyse GARCH
    """
    try:
        # Récupérer les données historiques
        from ...services.polygon_service import PolygonService
        data_service = PolygonService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 an de données pour GARCH
        
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
        
        # Calculer les rendements
        returns = GARCHModels.calculate_returns(df['close'])
        
        if len(returns) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pas assez de données pour ajuster un modèle GARCH. Requis: 100, Disponible: {len(returns)}"
            )
        
        # Effectuer l'analyse GARCH
        garch_analysis = GARCHModels.comprehensive_analysis(returns)
        
        return make_json_safe({
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "model_type": model_type,
            "period": period,
            "analysis": garch_analysis,
            "current_price": float(df['close'].iloc[-1])
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse GARCH: {str(e)}"
        )


@router.get("/monte-carlo/{symbol}")
async def get_monte_carlo_simulation(
    symbol: str,
    simulations: int = 10000,
    time_horizon: int = 30,
    db: Session = Depends(get_db)
):
    """
    Récupère une simulation Monte Carlo pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        simulations: Nombre de simulations
        time_horizon: Horizon temporel en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant les résultats de simulation
    """
    try:
        # Récupérer les données historiques
        from ...services.polygon_service import PolygonService
        data_service = PolygonService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=252 + 50)  # 1 an de données
        
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
        
        # Calculer les paramètres
        current_price = float(df['close'].iloc[-1])
        returns = df['close'].pct_change().dropna()
        drift = float(returns.mean() * 252)  # Dérive annuelle
        volatility = float(returns.std() * (252 ** 0.5))  # Volatilité annuelle
        
        # Effectuer la simulation Monte Carlo
        monte_carlo_analysis = MonteCarloSimulation.comprehensive_monte_carlo_analysis(
            current_price, volatility, drift, time_horizon, simulations
        )
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "current_price": current_price,
            "parameters": {
                "drift": drift,
                "volatility": volatility,
                "time_horizon": time_horizon,
                "simulations": simulations
            },
            "analysis": monte_carlo_analysis
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la simulation Monte Carlo: {str(e)}"
        )


@router.get("/markov/{symbol}")
async def get_markov_analysis(
    symbol: str,
    n_states: int = 3,
    period: int = 252,
    db: Session = Depends(get_db)
):
    """
    Récupère l'analyse des chaînes de Markov pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        n_states: Nombre d'états à identifier
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant l'analyse des chaînes de Markov
    """
    try:
        # Récupérer les données historiques
        from ...services.polygon_service import PolygonService
        data_service = PolygonService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 an de données pour GARCH
        
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
        
        # Calculer les rendements
        returns = df['close'].pct_change().dropna()
        
        if len(returns) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pas assez de données pour l'analyse des chaînes de Markov"
            )
        
        # Effectuer l'analyse des chaînes de Markov
        markov_analysis = MarkovChainAnalysis.comprehensive_markov_analysis(returns, n_states)
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "n_states": n_states,
            "period": period,
            "analysis": markov_analysis,
            "current_price": float(df['close'].iloc[-1])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse des chaînes de Markov: {str(e)}"
        )


@router.get("/volatility-forecast/{symbol}")
async def get_volatility_forecast(
    symbol: str,
    horizon: int = 5,
    period: int = 252,
    db: Session = Depends(get_db)
):
    """
    Récupère la prédiction de volatilité pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        horizon: Horizon de prédiction en jours
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant la prédiction de volatilité
    """
    try:
        # Récupérer les données historiques
        from ...services.polygon_service import PolygonService
        data_service = PolygonService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 an de données pour GARCH
        
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
        
        # Calculer les rendements
        returns = df['close'].pct_change().dropna()
        
        if len(returns) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pas assez de données pour la prédiction de volatilité"
            )
        
        # Effectuer la prédiction de volatilité
        volatility_forecaster = VolatilityForecaster()
        volatility_forecast = volatility_forecaster.comprehensive_volatility_forecast(returns, horizon)
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "horizon": horizon,
            "period": period,
            "forecast": volatility_forecast,
            "current_price": float(df['close'].iloc[-1])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la prédiction de volatilité: {str(e)}"
        )


@router.get("/comprehensive/{symbol}")
async def get_comprehensive_sentiment_analysis(
    symbol: str,
    period: int = 252,
    db: Session = Depends(get_db)
):
    """
    Effectue une analyse de sentiment complète pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant l'analyse de sentiment complète
    """
    try:
        # Récupérer les données historiques
        from ...services.polygon_service import PolygonService
        data_service = PolygonService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 an de données pour GARCH
        
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
        
        # Calculer les rendements
        returns = df['close'].pct_change().dropna()
        
        if len(returns) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pas assez de données pour l'analyse de sentiment"
            )
        
        # Effectuer toutes les analyses
        garch_analysis = GARCHModels.comprehensive_analysis(returns)
        markov_analysis = MarkovChainAnalysis.comprehensive_markov_analysis(returns)
        
        # Simulation Monte Carlo
        current_price = float(df['close'].iloc[-1])
        drift = float(returns.mean() * 252)
        volatility = float(returns.std() * (252 ** 0.5))
        monte_carlo_analysis = MonteCarloSimulation.comprehensive_monte_carlo_analysis(
            current_price, volatility, drift, 30, 10000
        )
        
        # Prédiction de volatilité
        volatility_forecaster = VolatilityForecaster()
        volatility_forecast = volatility_forecaster.comprehensive_volatility_forecast(returns, 5)
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "period": period,
            "current_price": current_price,
            "garch_analysis": garch_analysis,
            "markov_analysis": markov_analysis,
            "monte_carlo_analysis": monte_carlo_analysis,
            "volatility_forecast": volatility_forecast,
            "summary": {
                "volatility_regime": volatility_forecast.get("risk_metrics", {}).get("risk_level", "Unknown"),
                "market_state": markov_analysis.get("current_state", "Unknown"),
                "var_95": monte_carlo_analysis.get("risk_metrics", {}).get("var_95", 0.0),
                "var_99": monte_carlo_analysis.get("risk_metrics", {}).get("var_99", 0.0),
                "confidence": garch_analysis.get("model_comparison", {}).get("best_model_results", {}).get("log_likelihood", 0.0)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse de sentiment complète: {str(e)}"
        )
