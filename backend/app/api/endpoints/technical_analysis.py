"""
Endpoints API pour l'analyse technique.

Ce module expose les endpoints pour accéder aux fonctionnalités
d'analyse technique.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta

from ...core.database import get_db
from ...services.technical_analysis import TechnicalIndicators, CandlestickPatterns, SupportResistanceAnalyzer, SignalGenerator
from ...models.technical_analysis import TechnicalSignals, CandlestickPatterns as CandlestickPatternsModel, SupportResistanceLevels, TechnicalAnalysisSummary

router = APIRouter()


@router.get("/signals/{symbol}")
async def get_technical_signals(
    symbol: str,
    period: int = 30,
    db: Session = Depends(get_db)
):
    """
    Récupère les signaux techniques pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant les signaux techniques
    """
    try:
        # Récupérer les données historiques
        from ...services.data_service import DataService
        data_service = DataService(db)
        
        # Récupérer les données OHLCV
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period + 50)  # Buffer pour les calculs
        
        historical_data = data_service.get_historical_data(
            symbol=symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
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
        
        # Calculer les indicateurs techniques
        indicators = TechnicalIndicators.calculate_all_indicators(
            df['high'], df['low'], df['close'], df.get('volume')
        )
        
        # Détecter les patterns
        patterns = CandlestickPatterns.detect_all_patterns(
            df['open'], df['high'], df['low'], df['close']
        )
        
        # Générer les signaux
        signal_generator = SignalGenerator()
        composite_signal = signal_generator.generate_composite_signal(indicators, patterns)
        
        # Analyser les niveaux de support/résistance
        support_resistance = SupportResistanceAnalyzer.analyze_all_levels(
            df['high'], df['low'], df['close'], df.get('volume')
        )
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "indicators": {
                "rsi": indicators.get('rsi', {}).iloc[-1] if 'rsi' in indicators and not indicators['rsi'].empty else None,
                "macd": {
                    "macd": indicators.get('macd', {}).get('macd', pd.Series()).iloc[-1] if 'macd' in indicators else None,
                    "signal": indicators.get('macd', {}).get('signal', pd.Series()).iloc[-1] if 'macd' in indicators else None,
                    "histogram": indicators.get('macd', {}).get('histogram', pd.Series()).iloc[-1] if 'macd' in indicators else None
                },
                "bollinger_bands": {
                    "upper": indicators.get('bollinger_bands', {}).get('upper', pd.Series()).iloc[-1] if 'bollinger_bands' in indicators else None,
                    "middle": indicators.get('bollinger_bands', {}).get('middle', pd.Series()).iloc[-1] if 'bollinger_bands' in indicators else None,
                    "lower": indicators.get('bollinger_bands', {}).get('lower', pd.Series()).iloc[-1] if 'bollinger_bands' in indicators else None
                },
                "stochastic": {
                    "k_percent": indicators.get('stochastic', {}).get('k_percent', pd.Series()).iloc[-1] if 'stochastic' in indicators else None,
                    "d_percent": indicators.get('stochastic', {}).get('d_percent', pd.Series()).iloc[-1] if 'stochastic' in indicators else None
                }
            },
            "patterns": {
                "recent_patterns": {
                    pattern_name: pattern_data.iloc[-5:].sum() if isinstance(pattern_data, pd.Series) else 0
                    for pattern_name, pattern_data in patterns.items()
                },
                "pattern_signals": CandlestickPatterns.get_pattern_signals(patterns)
            },
            "support_resistance": {
                "pivot_points": {
                    "pivot": support_resistance.get('pivot_points', {}).get('pivot', pd.Series()).iloc[-1] if 'pivot_points' in support_resistance else None,
                    "r1": support_resistance.get('pivot_points', {}).get('r1', pd.Series()).iloc[-1] if 'pivot_points' in support_resistance else None,
                    "r2": support_resistance.get('pivot_points', {}).get('r2', pd.Series()).iloc[-1] if 'pivot_points' in support_resistance else None,
                    "s1": support_resistance.get('pivot_points', {}).get('s1', pd.Series()).iloc[-1] if 'pivot_points' in support_resistance else None,
                    "s2": support_resistance.get('pivot_points', {}).get('s2', pd.Series()).iloc[-1] if 'pivot_points' in support_resistance else None
                },
                "support_levels": support_resistance.get('support_resistance', {}).get('support_levels', []),
                "resistance_levels": support_resistance.get('support_resistance', {}).get('resistance_levels', [])
            },
            "composite_signal": composite_signal,
            "current_price": df['close'].iloc[-1],
            "period": period
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse technique: {str(e)}"
        )


@router.get("/patterns/{symbol}")
async def get_candlestick_patterns(
    symbol: str,
    period: int = 30,
    db: Session = Depends(get_db)
):
    """
    Récupère les patterns de chandeliers pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant les patterns détectés
    """
    try:
        # Récupérer les données historiques
        from ...services.data_service import DataService
        data_service = DataService(db)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period + 20)
        
        historical_data = data_service.get_historical_data(
            symbol=symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
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
        
        # Détecter les patterns
        patterns = CandlestickPatterns.detect_all_patterns(
            df['open'], df['high'], df['low'], df['close']
        )
        
        # Analyser les signaux
        pattern_signals = CandlestickPatterns.get_pattern_signals(patterns)
        
        # Compter les patterns récents
        recent_patterns = {}
        for pattern_name, pattern_data in patterns.items():
            if isinstance(pattern_data, pd.Series):
                recent_count = pattern_data.iloc[-10:].sum()  # 10 dernières périodes
                recent_patterns[pattern_name] = int(recent_count)
            else:
                recent_patterns[pattern_name] = 0
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "patterns": recent_patterns,
            "pattern_signals": pattern_signals,
            "current_price": df['close'].iloc[-1],
            "period": period
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la détection des patterns: {str(e)}"
        )


@router.get("/support-resistance/{symbol}")
async def get_support_resistance_levels(
    symbol: str,
    period: int = 60,
    db: Session = Depends(get_db)
):
    """
    Récupère les niveaux de support et résistance pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant les niveaux de support/résistance
    """
    try:
        # Récupérer les données historiques
        from ...services.data_service import DataService
        data_service = DataService(db)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period + 30)
        
        historical_data = data_service.get_historical_data(
            symbol=symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
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
        
        # Analyser les niveaux de support/résistance
        support_resistance = SupportResistanceAnalyzer.analyze_all_levels(
            df['high'], df['low'], df['close'], df.get('volume')
        )
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "pivot_points": {
                "pivot": float(support_resistance.get('pivot_points', {}).get('pivot', pd.Series()).iloc[-1]) if 'pivot_points' in support_resistance else None,
                "r1": float(support_resistance.get('pivot_points', {}).get('r1', pd.Series()).iloc[-1]) if 'pivot_points' in support_resistance else None,
                "r2": float(support_resistance.get('pivot_points', {}).get('r2', pd.Series()).iloc[-1]) if 'pivot_points' in support_resistance else None,
                "r3": float(support_resistance.get('pivot_points', {}).get('r3', pd.Series()).iloc[-1]) if 'pivot_points' in support_resistance else None,
                "s1": float(support_resistance.get('pivot_points', {}).get('s1', pd.Series()).iloc[-1]) if 'pivot_points' in support_resistance else None,
                "s2": float(support_resistance.get('pivot_points', {}).get('s2', pd.Series()).iloc[-1]) if 'pivot_points' in support_resistance else None,
                "s3": float(support_resistance.get('pivot_points', {}).get('s3', pd.Series()).iloc[-1]) if 'pivot_points' in support_resistance else None
            },
            "fibonacci_levels": {
                "fib_236": float(support_resistance.get('fibonacci_up', {}).get('fib_236', pd.Series()).iloc[-1]) if 'fibonacci_up' in support_resistance else None,
                "fib_382": float(support_resistance.get('fibonacci_up', {}).get('fib_382', pd.Series()).iloc[-1]) if 'fibonacci_up' in support_resistance else None,
                "fib_500": float(support_resistance.get('fibonacci_up', {}).get('fib_500', pd.Series()).iloc[-1]) if 'fibonacci_up' in support_resistance else None,
                "fib_618": float(support_resistance.get('fibonacci_up', {}).get('fib_618', pd.Series()).iloc[-1]) if 'fibonacci_up' in support_resistance else None,
                "fib_786": float(support_resistance.get('fibonacci_up', {}).get('fib_786', pd.Series()).iloc[-1]) if 'fibonacci_up' in support_resistance else None
            },
            "support_levels": support_resistance.get('support_resistance', {}).get('support_levels', []),
            "resistance_levels": support_resistance.get('support_resistance', {}).get('resistance_levels', []),
            "trend_lines": support_resistance.get('trend_lines', {}),
            "current_price": float(df['close'].iloc[-1]),
            "period": period
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse des niveaux: {str(e)}"
        )


@router.get("/analysis/{symbol}")
async def get_comprehensive_technical_analysis(
    symbol: str,
    period: int = 30,
    db: Session = Depends(get_db)
):
    """
    Effectue une analyse technique complète pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant l'analyse technique complète
    """
    try:
        # Récupérer les données historiques
        from ...services.data_service import DataService
        data_service = DataService(db)
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period + 50)
        
        historical_data = data_service.get_historical_data(
            symbol=symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
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
        
        # Effectuer l'analyse complète
        signal_generator = SignalGenerator()
        analysis = signal_generator.analyze_symbol(
            symbol, df['high'], df['low'], df['close'], df['open'], df.get('volume')
        )
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "current_price": float(df['close'].iloc[-1]),
            "analysis": analysis,
            "period": period
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse technique complète: {str(e)}"
        )
