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
    Calcule et persiste les indicateurs en base de données.
    
    Args:
        symbol: Symbole à analyser
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant les indicateurs de volatilité
    """
    try:
        # Récupérer les données historiques depuis la base de données
        from ...models.database import HistoricalData, TechnicalIndicators
        
        # Récupérer les données historiques stockées
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365)  # 1 an de données
        
        historical_records = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol,
            HistoricalData.date >= start_date,
            HistoricalData.date <= end_date
        ).order_by(HistoricalData.date).all()
        
        if not historical_records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune donnée historique trouvée pour {symbol} en base de données"
            )
        
        # Convertir en DataFrame
        data = []
        for record in historical_records:
            data.append({
                'date': record.date,
                'open': float(record.open),
                'high': float(record.high),
                'low': float(record.low),
                'close': float(record.close),
                'volume': int(record.volume)
            })
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Récupérer les indicateurs techniques stockés
        technical_records = db.query(TechnicalIndicators).filter(
            TechnicalIndicators.symbol == symbol,
            TechnicalIndicators.date >= start_date,
            TechnicalIndicators.date <= end_date
        ).order_by(TechnicalIndicators.date).all()
        
        # Effectuer l'analyse de volatilité
        volatility_analysis = VolatilityIndicators.comprehensive_volatility_analysis(
            df['close'], df['close'].pct_change().dropna()
        )
        
        # Extraire les valeurs clés pour la persistance
        current_volatility = volatility_analysis.get('current_volatility', 0.0)
        current_vix = volatility_analysis.get('current_vix', 0.0)
        vol_ratio = volatility_analysis.get('volatility_ratio', {})
        risk_premium = volatility_analysis.get('risk_premium', {})
        
        # Calculer les métriques supplémentaires
        historical_vol = volatility_analysis.get('historical_volatility', pd.Series(dtype=float))
        historical_vol_mean = historical_vol.mean() if not historical_vol.empty else 0.0
        historical_vol_std = historical_vol.std() if not historical_vol.empty else 0.0
        
        # Calculer le percentile de volatilité
        volatility_percentile = vol_ratio.get('percentile', 50.0)
        
        # Calculer le ratio de volatilité
        volatility_ratio_value = vol_ratio.get('ratio_to_mean', 1.0)
        
        # Déterminer le niveau de risque
        if current_volatility > historical_vol_mean + 2 * historical_vol_std:
            risk_level = "VERY_HIGH"
        elif current_volatility > historical_vol_mean + historical_vol_std:
            risk_level = "HIGH"
        elif current_volatility > historical_vol_mean:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Préparer les données pour la persistance
        regime_analysis = volatility_analysis.get('regime_analysis', {})
        
        # Nettoyer les données pour la sérialisation JSON
        if 'regimes' in regime_analysis and hasattr(regime_analysis['regimes'], 'tolist'):
            regime_analysis['regimes'] = regime_analysis['regimes'].tolist()
        
        if 'model' in regime_analysis:
            # Supprimer le modèle sklearn qui n'est pas sérialisable
            del regime_analysis['model']
        
        # Nettoyer les valeurs numériques dans regime_analysis
        if 'regime_analysis' in regime_analysis:
            for regime_key, regime_data in regime_analysis['regime_analysis'].items():
                if isinstance(regime_data, dict):
                    for key, value in regime_data.items():
                        if hasattr(value, 'item'):  # numpy scalar
                            regime_data[key] = value.item()
                        elif hasattr(value, 'tolist'):  # numpy array
                            regime_data[key] = value.tolist()
        
        # Nettoyer current_regime et n_regimes
        if 'current_regime' in regime_analysis and hasattr(regime_analysis['current_regime'], 'item'):
            regime_analysis['current_regime'] = regime_analysis['current_regime'].item()
        if 'n_regimes' in regime_analysis and hasattr(regime_analysis['n_regimes'], 'item'):
            regime_analysis['n_regimes'] = regime_analysis['n_regimes'].item()
        
        volatility_data = {
            'symbol': symbol,
            'analysis_date': datetime.now(),
            'current_volatility': float(current_volatility),
            'historical_volatility': float(historical_vol_mean),
            'implied_volatility': float(current_vix / 100) if current_vix > 0 else None,
            'vix_value': float(current_vix),
            'volatility_ratio': float(volatility_ratio_value),
            'volatility_percentile': float(volatility_percentile),
            'volatility_skew': 0.0,  # À calculer si nécessaire
            'risk_premium': float(risk_premium.get('risk_premium', 0.0)),
            'risk_level': risk_level,
            'regime_analysis': regime_analysis
        }
        
        # Vérifier si un enregistrement existe déjà pour aujourd'hui
        existing_record = db.query(VolatilityIndicatorsModel).filter(
            VolatilityIndicatorsModel.symbol == symbol,
            VolatilityIndicatorsModel.analysis_date >= datetime.now().date()
        ).first()
        
        if existing_record:
            # Mettre à jour l'enregistrement existant
            for key, value in volatility_data.items():
                if hasattr(existing_record, key):
                    setattr(existing_record, key, value)
            existing_record.updated_at = datetime.now()
        else:
            # Créer un nouvel enregistrement
            new_record = VolatilityIndicatorsModel(**volatility_data)
            db.add(new_record)
        
        # Sauvegarder en base de données
        db.commit()
        
        return make_json_safe({
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "period": period,
            "analysis": volatility_analysis,
            "current_price": float(df['close'].iloc[-1]),
            "persisted": True,
            "risk_level": risk_level,
            "volatility_metrics": {
                "current_volatility": current_volatility,
                "historical_mean": historical_vol_mean,
                "volatility_ratio": volatility_ratio_value,
                "percentile": volatility_percentile,
                "vix": current_vix
            }
        })
        
    except Exception as e:
        db.rollback()
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
    Calcule et persiste les indicateurs en base de données.
    
    Args:
        symbol: Symbole à analyser
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant les indicateurs de momentum
    """
    try:
        # Récupérer les données historiques depuis la base de données
        from ...models.database import HistoricalData, TechnicalIndicators
        
        # Récupérer les données historiques stockées
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=365)  # 1 an de données
        
        historical_records = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol,
            HistoricalData.date >= start_date,
            HistoricalData.date <= end_date
        ).order_by(HistoricalData.date).all()
        
        if not historical_records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune donnée historique trouvée pour {symbol} en base de données"
            )
        
        # Convertir en DataFrame
        data = []
        for record in historical_records:
            data.append({
                'date': record.date,
                'open': float(record.open),
                'high': float(record.high),
                'low': float(record.low),
                'close': float(record.close),
                'volume': int(record.volume)
            })
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Effectuer l'analyse de momentum
        momentum_analysis = MomentumIndicators.comprehensive_momentum_analysis(
            df['close'], df.get('volume')
        )
        
        # Extraire les valeurs clés pour la persistance
        momentum_score = momentum_analysis.get('momentum_score', {})
        price_momentum = momentum_analysis.get('price_momentum', {})
        volume_momentum = momentum_analysis.get('volume_momentum', {})
        momentum_divergence = momentum_analysis.get('momentum_divergence', {})
        
        # Extraire les valeurs spécifiques
        composite_score = momentum_score.get('composite_score', 0.0)
        momentum_class = momentum_score.get('momentum_class', 'Unknown')
        
        # Momentum des prix sur différentes périodes
        price_momentum_5d = price_momentum.get('momentum_5', pd.Series(dtype=float)).iloc[-1] if 'momentum_5' in price_momentum and not price_momentum['momentum_5'].empty else None
        price_momentum_10d = price_momentum.get('momentum_10', pd.Series(dtype=float)).iloc[-1] if 'momentum_10' in price_momentum and not price_momentum['momentum_10'].empty else None
        price_momentum_20d = price_momentum.get('momentum_20', pd.Series(dtype=float)).iloc[-1] if 'momentum_20' in price_momentum and not price_momentum['momentum_20'].empty else None
        price_momentum_50d = price_momentum.get('momentum_50', pd.Series(dtype=float)).iloc[-1] if 'momentum_50' in price_momentum and not price_momentum['momentum_50'].empty else None
        
        # Momentum du volume
        volume_momentum_value = volume_momentum.get('volume_momentum_10', pd.Series(dtype=float)).iloc[-1] if 'volume_momentum_10' in volume_momentum and not volume_momentum['volume_momentum_10'].empty else None
        relative_volume_value = volume_momentum.get('relative_volume_10', pd.Series(dtype=float)).iloc[-1] if 'relative_volume_10' in volume_momentum and not volume_momentum['relative_volume_10'].empty else None
        
        # Divergence de momentum
        momentum_divergence_value = momentum_divergence.get('divergence', 0.0)
        
        # Calculer le percentile de momentum (approximation)
        momentum_percentile = 50.0  # Valeur par défaut
        if composite_score > 5:
            momentum_percentile = 90.0
        elif composite_score > 2:
            momentum_percentile = 75.0
        elif composite_score > 0:
            momentum_percentile = 60.0
        elif composite_score > -2:
            momentum_percentile = 40.0
        elif composite_score > -5:
            momentum_percentile = 25.0
        else:
            momentum_percentile = 10.0
        
        # Préparer les données pour la persistance (version simplifiée)
        analysis_details = {
            'momentum_score': {
                'composite_score': float(composite_score),
                'momentum_class': momentum_class,
                'individual_scores': momentum_score.get('individual_scores', []),
                'volume_momentum_score': momentum_score.get('volume_momentum_score', 0.0)
            },
            'momentum_divergence': {
                'divergence': float(momentum_divergence_value),
                'signal': momentum_divergence.get('signal', 'No Data'),
                'price_trend': momentum_divergence.get('price_trend', 0.0),
                'momentum_trend': momentum_divergence.get('momentum_trend', 0.0)
            },
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        momentum_data = {
            'symbol': symbol,
            'analysis_date': datetime.now(),
            'price_momentum_5d': float(price_momentum_5d) if price_momentum_5d is not None else None,
            'price_momentum_10d': float(price_momentum_10d) if price_momentum_10d is not None else None,
            'price_momentum_20d': float(price_momentum_20d) if price_momentum_20d is not None else None,
            'price_momentum_50d': float(price_momentum_50d) if price_momentum_50d is not None else None,
            'volume_momentum': float(volume_momentum_value) if volume_momentum_value is not None else None,
            'relative_volume': float(relative_volume_value) if relative_volume_value is not None else None,
            'relative_strength': None,  # À calculer si nécessaire
            'momentum_score': float(composite_score),
            'momentum_class': momentum_class,
            'momentum_divergence': float(momentum_divergence_value),
            'momentum_ranking': None,  # À calculer si nécessaire
            'momentum_percentile': float(momentum_percentile),
            'analysis_details': analysis_details
        }
        
        # Vérifier si un enregistrement existe déjà pour aujourd'hui
        existing_record = db.query(MomentumIndicatorsModel).filter(
            MomentumIndicatorsModel.symbol == symbol,
            MomentumIndicatorsModel.analysis_date >= datetime.now().date()
        ).first()
        
        if existing_record:
            # Mettre à jour l'enregistrement existant
            for key, value in momentum_data.items():
                if hasattr(existing_record, key):
                    setattr(existing_record, key, value)
            existing_record.updated_at = datetime.now()
        else:
            # Créer un nouvel enregistrement
            new_record = MomentumIndicatorsModel(**momentum_data)
            db.add(new_record)
        
        # Sauvegarder en base de données
        db.commit()
        
        return make_json_safe({
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "period": period,
            "analysis": momentum_analysis,
            "current_price": float(df['close'].iloc[-1]),
            "persisted": True,
            "momentum_class": momentum_class,
            "momentum_metrics": {
                "composite_score": composite_score,
                "price_momentum_5d": price_momentum_5d,
                "price_momentum_10d": price_momentum_10d,
                "price_momentum_20d": price_momentum_20d,
                "price_momentum_50d": price_momentum_50d,
                "volume_momentum": volume_momentum_value,
                "relative_volume": relative_volume_value,
                "momentum_divergence": momentum_divergence_value,
                "momentum_percentile": momentum_percentile
            }
        })
        
    except Exception as e:
        db.rollback()
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
