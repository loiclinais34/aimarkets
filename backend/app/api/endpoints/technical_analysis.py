"""
Endpoints API pour l'analyse technique.

Ce module expose les endpoints pour accéder aux fonctionnalités
d'analyse technique.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta

from ...core.database import get_db
from ...services.technical_analysis import TechnicalIndicators, CandlestickPatterns, SupportResistanceAnalyzer, SignalGenerator
from ...models.technical_analysis import TechnicalSignals, CandlestickPatterns as CandlestickPatternsModel, SupportResistanceLevels, TechnicalAnalysisSummary

# Encoder personnalisé pour les types NumPy
class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

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
        # Récupérer les données historiques depuis la base de données
        from ...models.database import HistoricalData
        
        # Récupérer les données historiques stockées
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=period + 50)  # Buffer pour les calculs
        
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
        
        # Fonctions utilitaires pour la sérialisation
        def safe_float(value):
            """Convertit une valeur en float de manière sécurisée."""
            if pd.isna(value) or value is None:
                return None
            try:
                return float(value)
            except (ValueError, TypeError):
                return None
        
        def safe_int(value):
            """Convertit une valeur en int de manière sécurisée."""
            if pd.isna(value) or value is None:
                return None
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        
        # Préparer les indicateurs
        indicators_data = {}
        if 'rsi' in indicators and not indicators['rsi'].empty:
            indicators_data['rsi'] = safe_float(indicators['rsi'].iloc[-1])
        
        if 'macd' in indicators:
            macd_data = indicators['macd']
            indicators_data['macd'] = {
                "macd": safe_float(macd_data.get('macd', pd.Series()).iloc[-1]) if not macd_data.get('macd', pd.Series()).empty else None,
                "signal": safe_float(macd_data.get('signal', pd.Series()).iloc[-1]) if not macd_data.get('signal', pd.Series()).empty else None,
                "histogram": safe_float(macd_data.get('histogram', pd.Series()).iloc[-1]) if not macd_data.get('histogram', pd.Series()).empty else None
            }
        
        if 'bollinger_bands' in indicators:
            bb_data = indicators['bollinger_bands']
            indicators_data['bollinger_bands'] = {
                "upper": safe_float(bb_data.get('upper', pd.Series()).iloc[-1]) if not bb_data.get('upper', pd.Series()).empty else None,
                "middle": safe_float(bb_data.get('middle', pd.Series()).iloc[-1]) if not bb_data.get('middle', pd.Series()).empty else None,
                "lower": safe_float(bb_data.get('lower', pd.Series()).iloc[-1]) if not bb_data.get('lower', pd.Series()).empty else None
            }
        
        if 'stochastic' in indicators:
            stoch_data = indicators['stochastic']
            indicators_data['stochastic'] = {
                "k_percent": safe_float(stoch_data.get('k_percent', pd.Series()).iloc[-1]) if not stoch_data.get('k_percent', pd.Series()).empty else None,
                "d_percent": safe_float(stoch_data.get('d_percent', pd.Series()).iloc[-1]) if not stoch_data.get('d_percent', pd.Series()).empty else None
            }
        
        # Préparer les patterns
        patterns_data = {}
        for pattern_name, pattern_data in patterns.items():
            if isinstance(pattern_data, pd.Series) and not pattern_data.empty:
                patterns_data[pattern_name] = safe_int(pattern_data.iloc[-5:].sum())
            else:
                patterns_data[pattern_name] = 0
        
        # Préparer les signaux
        signals_data = {}
        for key, value in composite_signal.items():
            if isinstance(value, (int, float, np.number)):
                signals_data[key] = safe_float(value)
            elif isinstance(value, str):
                signals_data[key] = value
            else:
                signals_data[key] = str(value)
        
        # Persister les signaux techniques en base de données
        from ...models.technical_analysis import TechnicalSignals as TechnicalSignalsModel
        
        # Supprimer les anciens signaux pour ce symbole (garder seulement les plus récents)
        db.query(TechnicalSignalsModel).filter(
            TechnicalSignalsModel.symbol == symbol,
            TechnicalSignalsModel.created_at < datetime.now() - timedelta(hours=1)
        ).delete()
        
        # Créer les nouveaux signaux
        signals_to_save = []
        
        # Signal RSI
        if 'rsi' in indicators_data and indicators_data['rsi'] is not None:
            rsi_value = indicators_data['rsi']
            if rsi_value > 70:
                signal_direction = "SELL"
                signal_strength = min(1.0, (rsi_value - 70) / 30)
                confidence = 0.8
            elif rsi_value < 30:
                signal_direction = "BUY"
                signal_strength = min(1.0, (30 - rsi_value) / 30)
                confidence = 0.8
            else:
                signal_direction = "HOLD"
                signal_strength = 0.0
                confidence = 0.5
            
            signals_to_save.append(TechnicalSignalsModel(
                symbol=symbol,
                signal_type="RSI",
                signal_value=float(rsi_value),
                signal_strength=float(signal_strength),
                signal_direction=signal_direction,
                indicator_value=float(rsi_value),
                threshold_upper=70.0,
                threshold_lower=30.0,
                confidence=float(confidence)
            ))
        
        # Signal MACD
        if 'macd' in indicators_data and indicators_data['macd']['histogram'] is not None:
            histogram = indicators_data['macd']['histogram']
            if histogram > 0:
                signal_direction = "BUY"
                signal_strength = min(1.0, abs(histogram) / 0.1)
                confidence = 0.7
            elif histogram < 0:
                signal_direction = "SELL"
                signal_strength = min(1.0, abs(histogram) / 0.1)
                confidence = 0.7
            else:
                signal_direction = "HOLD"
                signal_strength = 0.0
                confidence = 0.5
            
            signals_to_save.append(TechnicalSignalsModel(
                symbol=symbol,
                signal_type="MACD",
                signal_value=float(histogram),
                signal_strength=float(signal_strength),
                signal_direction=signal_direction,
                indicator_value=float(histogram),
                threshold_upper=0.1,
                threshold_lower=-0.1,
                confidence=float(confidence)
            ))
        
        # Signal Bollinger Bands
        if 'bollinger_bands' in indicators_data:
            bb = indicators_data['bollinger_bands']
            current_price = safe_float(df['close'].iloc[-1])
            
            if bb['upper'] and bb['lower'] and current_price:
                if current_price > bb['upper']:
                    signal_direction = "SELL"
                    signal_strength = min(1.0, (current_price - bb['upper']) / (bb['upper'] - bb['lower']) * 2)
                    confidence = 0.8
                elif current_price < bb['lower']:
                    signal_direction = "BUY"
                    signal_strength = min(1.0, (bb['lower'] - current_price) / (bb['upper'] - bb['lower']) * 2)
                    confidence = 0.8
                else:
                    signal_direction = "HOLD"
                    signal_strength = 0.0
                    confidence = 0.5
                
                signals_to_save.append(TechnicalSignalsModel(
                    symbol=symbol,
                    signal_type="BOLLINGER_BANDS",
                    signal_value=float(current_price),
                    signal_strength=float(signal_strength),
                    signal_direction=signal_direction,
                    indicator_value=float(current_price),
                    threshold_upper=float(bb['upper']),
                    threshold_lower=float(bb['lower']),
                    confidence=float(confidence)
                ))
        
        # Signal Stochastic
        if 'stochastic' in indicators_data and indicators_data['stochastic']['k_percent'] is not None:
            k_percent = indicators_data['stochastic']['k_percent']
            if k_percent > 80:
                signal_direction = "SELL"
                signal_strength = min(1.0, (k_percent - 80) / 20)
                confidence = 0.7
            elif k_percent < 20:
                signal_direction = "BUY"
                signal_strength = min(1.0, (20 - k_percent) / 20)
                confidence = 0.7
            else:
                signal_direction = "HOLD"
                signal_strength = 0.0
                confidence = 0.5
            
            signals_to_save.append(TechnicalSignalsModel(
                symbol=symbol,
                signal_type="STOCHASTIC",
                signal_value=float(k_percent),
                signal_strength=float(signal_strength),
                signal_direction=signal_direction,
                indicator_value=float(k_percent),
                threshold_upper=80.0,
                threshold_lower=20.0,
                confidence=float(confidence)
            ))
        
        # Sauvegarder tous les signaux
        for signal in signals_to_save:
            db.add(signal)
        
        db.commit()
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "indicators": indicators_data,
            "patterns": {
                "recent_patterns": patterns_data,
                "pattern_signals": CandlestickPatterns.get_pattern_signals(patterns)
            },
            "support_resistance": {
                "pivot_points": {
                    "pivot": safe_float(support_resistance.get('pivot_points', {}).get('pivot', pd.Series()).iloc[-1]) if 'pivot_points' in support_resistance and not support_resistance.get('pivot_points', {}).get('pivot', pd.Series()).empty else None,
                    "r1": safe_float(support_resistance.get('pivot_points', {}).get('r1', pd.Series()).iloc[-1]) if 'pivot_points' in support_resistance and not support_resistance.get('pivot_points', {}).get('r1', pd.Series()).empty else None,
                    "r2": safe_float(support_resistance.get('pivot_points', {}).get('r2', pd.Series()).iloc[-1]) if 'pivot_points' in support_resistance and not support_resistance.get('pivot_points', {}).get('r2', pd.Series()).empty else None,
                    "s1": safe_float(support_resistance.get('pivot_points', {}).get('s1', pd.Series()).iloc[-1]) if 'pivot_points' in support_resistance and not support_resistance.get('pivot_points', {}).get('s1', pd.Series()).empty else None,
                    "s2": safe_float(support_resistance.get('pivot_points', {}).get('s2', pd.Series()).iloc[-1]) if 'pivot_points' in support_resistance and not support_resistance.get('pivot_points', {}).get('s2', pd.Series()).empty else None
                },
                "support_levels": [safe_float(level) for level in support_resistance.get('support_levels', [])],
                "resistance_levels": [safe_float(level) for level in support_resistance.get('resistance_levels', [])]
            },
            "composite_signal": signals_data,
            "persisted_signals": len(signals_to_save),
            "current_price": safe_float(df['close'].iloc[-1]),
            "period": period
        }
        
    except Exception as e:
        db.rollback()
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
        from ...services.polygon_service import PolygonService
        data_service = PolygonService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period + 20)
        
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
        from ...services.polygon_service import PolygonService
        data_service = PolygonService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period + 30)
        
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
        from ...services.polygon_service import PolygonService
        data_service = PolygonService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period + 50)
        
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
