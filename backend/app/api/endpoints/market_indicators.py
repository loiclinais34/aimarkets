"""
Endpoints API pour les indicateurs de marché.

Ce module expose les endpoints pour accéder aux fonctionnalités
d'analyse des indicateurs de marché.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ...core.database import get_db
from ...services.market_indicators import VolatilityIndicators, CorrelationAnalyzer, MomentumIndicators
from ...models.market_indicators import MarketIndicators as MarketIndicatorsModel, VolatilityIndicators as VolatilityIndicatorsModel, CorrelationAnalysis, MomentumIndicators as MomentumIndicatorsModel, MarketSentimentSummary
from ...utils.json_encoder import make_json_safe

router = APIRouter()


@router.get("/volatility/{symbol}")
async def get_volatility_indicators(
    symbol: str,
    period: int = 252,
    db: Session = Depends(get_db)
):
    """
    Récupère les indicateurs de volatilité pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant les indicateurs de volatilité
    """
    try:
        # Récupérer les données historiques
        from ...services.polygon_service import PolygonService
        data_service = PolygonService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 an de données
        
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
        
        # Effectuer l'analyse de volatilité
        volatility_analysis = VolatilityIndicators.comprehensive_volatility_analysis(
            df['close'], df['close'].pct_change().dropna()
        )
        
        return make_json_safe({
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "period": period,
            "analysis": volatility_analysis,
            "current_price": float(df['close'].iloc[-1])
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse de volatilité: {str(e)}"
        )


@router.get("/correlations/{symbol}")
async def get_correlation_analysis(
    symbol: str,
    symbols: List[str] = None,
    period: int = 252,
    db: Session = Depends(get_db)
):
    """
    Récupère l'analyse de corrélation pour un symbole.
    
    Args:
        symbol: Symbole principal à analyser
        symbols: Liste des symboles à corréler (optionnel)
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant l'analyse de corrélation
    """
    try:
        # Récupérer les données historiques
        from ...services.polygon_service import PolygonService
        data_service = PolygonService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 an de données
        
        # Si pas de symboles spécifiés, utiliser des symboles par défaut
        if symbols is None:
            symbols = ["SPY", "QQQ", "IWM", "DIA"]  # Indices principaux
        
        # Récupérer les données pour tous les symboles
        all_data = {}
        for sym in [symbol] + symbols:
            historical_data = data_service.get_historical_data(
                symbol=sym,
                from_date=start_date.strftime('%Y-%m-%d'),
                to_date=end_date.strftime('%Y-%m-%d')
            )
            
            if historical_data:
                df = pd.DataFrame(historical_data)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                all_data[sym] = df['close'].pct_change().dropna()
        
        if not all_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucune donnée historique trouvée"
            )
        
        # Créer un DataFrame des rendements
        returns_df = pd.DataFrame(all_data)
        returns_df = returns_df.dropna()
        
        if len(returns_df) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pas assez de données pour l'analyse de corrélation"
            )
        
        # Effectuer l'analyse de corrélation
        correlation_analysis = CorrelationAnalyzer.comprehensive_correlation_analysis(
            returns_df, returns_df.get('SPY')  # Utiliser SPY comme benchmark
        )
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "period": period,
            "symbols_analyzed": list(returns_df.columns),
            "analysis": correlation_analysis,
            "current_price": float(all_data[symbol].iloc[-1] if symbol in all_data else 0.0)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse de corrélation: {str(e)}"
        )


@router.get("/momentum/{symbol}")
async def get_momentum_indicators(
    symbol: str,
    period: int = 252,
    db: Session = Depends(get_db)
):
    """
    Récupère les indicateurs de momentum pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant les indicateurs de momentum
    """
    try:
        # Récupérer les données historiques
        from ...services.polygon_service import PolygonService
        data_service = PolygonService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 an de données
        
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
        
        # Effectuer l'analyse de momentum
        momentum_analysis = MomentumIndicators.comprehensive_momentum_analysis(
            df['close'], df.get('volume')
        )
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "period": period,
            "analysis": momentum_analysis,
            "current_price": float(df['close'].iloc[-1])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse de momentum: {str(e)}"
        )


@router.get("/vix")
async def get_vix_data(
    period: str = "1y",
    db: Session = Depends(get_db)
):
    """
    Récupère les données du VIX.
    
    Args:
        period: Période des données ("1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant les données du VIX
    """
    try:
        # Récupérer les données VIX
        vix_data = VolatilityIndicators.get_vix_data(period)
        
        if vix_data.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Aucune donnée VIX trouvée"
            )
        
        # Calculer les statistiques
        current_vix = float(vix_data['Close'].iloc[-1])
        vix_mean = float(vix_data['Close'].mean())
        vix_std = float(vix_data['Close'].std())
        vix_min = float(vix_data['Close'].min())
        vix_max = float(vix_data['Close'].max())
        
        # Classification du niveau de peur
        if current_vix > 30:
            fear_level = "Extreme Fear"
        elif current_vix > 20:
            fear_level = "Fear"
        elif current_vix > 15:
            fear_level = "Neutral"
        elif current_vix > 10:
            fear_level = "Greed"
        else:
            fear_level = "Extreme Greed"
        
        return {
            "analysis_date": datetime.now().isoformat(),
            "period": period,
            "current_vix": current_vix,
            "fear_level": fear_level,
            "statistics": {
                "mean": vix_mean,
                "std": vix_std,
                "min": vix_min,
                "max": vix_max,
                "percentile": float((vix_data['Close'] <= current_vix).mean() * 100)
            },
            "data_points": len(vix_data)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des données VIX: {str(e)}"
        )


@router.get("/comprehensive/{symbol}")
async def get_comprehensive_market_analysis(
    symbol: str,
    period: int = 252,
    db: Session = Depends(get_db)
):
    """
    Effectue une analyse complète des indicateurs de marché pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant l'analyse complète des indicateurs de marché
    """
    try:
        # Récupérer les données historiques
        from ...services.polygon_service import PolygonService
        data_service = PolygonService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 an de données
        
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
        
        # Effectuer toutes les analyses
        volatility_analysis = VolatilityIndicators.comprehensive_volatility_analysis(
            df['close'], df['close'].pct_change().dropna()
        )
        
        momentum_analysis = MomentumIndicators.comprehensive_momentum_analysis(
            df['close'], df.get('volume')
        )
        
        # Récupérer les données VIX
        vix_data = VolatilityIndicators.get_vix_data("1y")
        current_vix = float(vix_data['Close'].iloc[-1]) if not vix_data.empty else 0.0
        
        # Calculer un score de sentiment global
        sentiment_score = 0.0
        sentiment_components = {}
        
        # Composant volatilité
        if 'volatility_ratio' in volatility_analysis:
            vol_ratio = volatility_analysis['volatility_ratio'].get('ratio_to_mean', 1.0)
            sentiment_components['volatility'] = -vol_ratio + 1  # Plus de volatilité = sentiment négatif
        
        # Composant momentum
        if 'momentum_score' in momentum_analysis:
            momentum_score = momentum_analysis['momentum_score'].get('composite_score', 0.0)
            sentiment_components['momentum'] = momentum_score / 10  # Normaliser
        
        # Composant VIX
        if current_vix > 0:
            vix_component = max(0, min(1, (30 - current_vix) / 20))  # VIX bas = sentiment positif
            sentiment_components['vix'] = vix_component
        
        # Score global
        if sentiment_components:
            sentiment_score = sum(sentiment_components.values()) / len(sentiment_components)
        
        # Classification du sentiment
        if sentiment_score > 0.6:
            overall_sentiment = "BULLISH"
        elif sentiment_score > 0.4:
            overall_sentiment = "NEUTRAL"
        else:
            overall_sentiment = "BEARISH"
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "period": period,
            "current_price": float(df['close'].iloc[-1]),
            "volatility_analysis": volatility_analysis,
            "momentum_analysis": momentum_analysis,
            "vix_analysis": {
                "current_vix": current_vix,
                "fear_level": "Extreme Fear" if current_vix > 30 else "Fear" if current_vix > 20 else "Neutral" if current_vix > 15 else "Greed" if current_vix > 10 else "Extreme Greed"
            },
            "sentiment_summary": {
                "overall_sentiment": overall_sentiment,
                "sentiment_score": sentiment_score,
                "sentiment_components": sentiment_components,
                "confidence_level": 0.8  # Placeholder
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse complète des indicateurs de marché: {str(e)}"
        )
