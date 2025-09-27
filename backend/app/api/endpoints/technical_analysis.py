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
                if isinstance(value, np.integer):
                    return float(int(value))
                elif isinstance(value, np.floating):
                    return float(value)
                else:
                    return float(value)
            except (ValueError, TypeError):
                return None
        
        def safe_int(value):
            """Convertit une valeur en int de manière sécurisée."""
            if pd.isna(value) or value is None:
                return None
            try:
                if isinstance(value, np.integer):
                    return int(value)
                elif isinstance(value, np.floating):
                    return int(value)
                else:
                    return int(value)
            except (ValueError, TypeError):
                return None
        
        # Préparer les indicateurs
        indicators_data = {}
        
        # RSI
        if 'rsi' in indicators and not indicators['rsi'].empty:
            indicators_data['rsi'] = safe_float(indicators['rsi'].iloc[-1])
        
        # MACD
        if 'macd' in indicators:
            macd_data = indicators['macd']
            indicators_data['macd'] = {
                "macd": safe_float(macd_data.get('macd', pd.Series()).iloc[-1]) if not macd_data.get('macd', pd.Series()).empty else None,
                "signal": safe_float(macd_data.get('signal', pd.Series()).iloc[-1]) if not macd_data.get('signal', pd.Series()).empty else None,
                "histogram": safe_float(macd_data.get('histogram', pd.Series()).iloc[-1]) if not macd_data.get('histogram', pd.Series()).empty else None
            }
        
        # Bollinger Bands
        if 'bollinger_bands' in indicators:
            bb_data = indicators['bollinger_bands']
            indicators_data['bollinger_bands'] = {
                "upper": safe_float(bb_data.get('upper', pd.Series()).iloc[-1]) if not bb_data.get('upper', pd.Series()).empty else None,
                "middle": safe_float(bb_data.get('middle', pd.Series()).iloc[-1]) if not bb_data.get('middle', pd.Series()).empty else None,
                "lower": safe_float(bb_data.get('lower', pd.Series()).iloc[-1]) if not bb_data.get('lower', pd.Series()).empty else None
            }
        
        # Stochastic
        if 'stochastic' in indicators:
            stoch_data = indicators['stochastic']
            indicators_data['stochastic'] = {
                "k_percent": safe_float(stoch_data.get('k_percent', pd.Series()).iloc[-1]) if not stoch_data.get('k_percent', pd.Series()).empty else None,
                "d_percent": safe_float(stoch_data.get('d_percent', pd.Series()).iloc[-1]) if not stoch_data.get('d_percent', pd.Series()).empty else None
            }
        
        # Williams %R
        if 'williams_r' in indicators and not indicators['williams_r'].empty:
            indicators_data['williams_r'] = safe_float(indicators['williams_r'].iloc[-1])
        
        # CCI (Commodity Channel Index)
        if 'cci' in indicators and not indicators['cci'].empty:
            indicators_data['cci'] = safe_float(indicators['cci'].iloc[-1])
        
        # ADX (Average Directional Index)
        if 'adx' in indicators:
            adx_data = indicators['adx']
            indicators_data['adx'] = {
                "adx": safe_float(adx_data.get('adx', pd.Series()).iloc[-1]) if not adx_data.get('adx', pd.Series()).empty else None,
                "plus_di": safe_float(adx_data.get('plus_di', pd.Series()).iloc[-1]) if not adx_data.get('plus_di', pd.Series()).empty else None,
                "minus_di": safe_float(adx_data.get('minus_di', pd.Series()).iloc[-1]) if not adx_data.get('minus_di', pd.Series()).empty else None
            }
        
        # Parabolic SAR
        if 'parabolic_sar' in indicators and not indicators['parabolic_sar'].empty:
            indicators_data['parabolic_sar'] = safe_float(indicators['parabolic_sar'].iloc[-1])
        
        # Ichimoku Cloud
        if 'ichimoku' in indicators:
            ichimoku_data = indicators['ichimoku']
            indicators_data['ichimoku'] = {
                "tenkan_sen": safe_float(ichimoku_data.get('tenkan_sen', pd.Series()).iloc[-1]) if not ichimoku_data.get('tenkan_sen', pd.Series()).empty else None,
                "kijun_sen": safe_float(ichimoku_data.get('kijun_sen', pd.Series()).iloc[-1]) if not ichimoku_data.get('kijun_sen', pd.Series()).empty else None,
                "senkou_span_a": safe_float(ichimoku_data.get('senkou_span_a', pd.Series()).iloc[-1]) if not ichimoku_data.get('senkou_span_a', pd.Series()).empty else None,
                "senkou_span_b": safe_float(ichimoku_data.get('senkou_span_b', pd.Series()).iloc[-1]) if not ichimoku_data.get('senkou_span_b', pd.Series()).empty else None,
                "chikou_span": safe_float(ichimoku_data.get('chikou_span', pd.Series()).iloc[-1]) if not ichimoku_data.get('chikou_span', pd.Series()).empty else None
            }
        
        # SMA 20 et 50
        if 'sma_20' in indicators and not indicators['sma_20'].empty:
            indicators_data['sma_20'] = safe_float(indicators['sma_20'].iloc[-1])
        
        if 'sma_50' in indicators and not indicators['sma_50'].empty:
            indicators_data['sma_50'] = safe_float(indicators['sma_50'].iloc[-1])
        
        # Préparer les patterns
        patterns_data = {}
        for pattern_name, pattern_data in patterns.items():
            if isinstance(pattern_data, pd.Series) and not pattern_data.empty:
                sum_value = pattern_data.iloc[-5:].sum()
                if isinstance(sum_value, np.integer):
                    patterns_data[pattern_name] = int(sum_value)
                elif isinstance(sum_value, np.floating):
                    patterns_data[pattern_name] = float(sum_value)
                else:
                    patterns_data[pattern_name] = safe_int(sum_value)
            else:
                patterns_data[pattern_name] = 0
        
        # Préparer les signaux
        signals_data = {}
        for key, value in composite_signal.items():
            if isinstance(value, (int, float, np.number)):
                signals_data[key] = safe_float(value)
            elif isinstance(value, str):
                signals_data[key] = value
            elif isinstance(value, np.integer):
                signals_data[key] = int(value)
            elif isinstance(value, np.floating):
                signals_data[key] = float(value)
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
        
        # Signal Williams %R
        if 'williams_r' in indicators_data and indicators_data['williams_r'] is not None:
            williams_r = indicators_data['williams_r']
            if williams_r > -20:
                signal_direction = "SELL"
                signal_strength = min(1.0, (williams_r + 20) / 20)
                confidence = 0.6
            elif williams_r < -80:
                signal_direction = "BUY"
                signal_strength = min(1.0, (-80 - williams_r) / 20)
                confidence = 0.6
            else:
                signal_direction = "HOLD"
                signal_strength = 0.0
                confidence = 0.5
            
            signals_to_save.append(TechnicalSignalsModel(
                symbol=symbol,
                signal_type="WILLIAMS_R",
                signal_value=float(williams_r),
                signal_strength=float(signal_strength),
                signal_direction=signal_direction,
                indicator_value=float(williams_r),
                threshold_upper=-20.0,
                threshold_lower=-80.0,
                confidence=float(confidence)
            ))
        
        # Signal CCI
        if 'cci' in indicators_data and indicators_data['cci'] is not None:
            cci = indicators_data['cci']
            if cci > 100:
                signal_direction = "BUY"
                signal_strength = min(1.0, (cci - 100) / 100)
                confidence = 0.6
            elif cci < -100:
                signal_direction = "SELL"
                signal_strength = min(1.0, (-100 - cci) / 100)
                confidence = 0.6
            else:
                signal_direction = "HOLD"
                signal_strength = 0.0
                confidence = 0.5
            
            signals_to_save.append(TechnicalSignalsModel(
                symbol=symbol,
                signal_type="CCI",
                signal_value=float(cci),
                signal_strength=float(signal_strength),
                signal_direction=signal_direction,
                indicator_value=float(cci),
                threshold_upper=100.0,
                threshold_lower=-100.0,
                confidence=float(confidence)
            ))
        
        # Signal ADX
        if 'adx' in indicators_data and indicators_data['adx']['adx'] is not None:
            adx = indicators_data['adx']['adx']
            plus_di = indicators_data['adx']['plus_di']
            minus_di = indicators_data['adx']['minus_di']
            
            if adx > 25:  # Tendance forte
                if plus_di and minus_di:
                    if plus_di > minus_di:
                        signal_direction = "BUY"
                        signal_strength = min(1.0, (plus_di - minus_di) / 50)
                        confidence = 0.8
                    else:
                        signal_direction = "SELL"
                        signal_strength = min(1.0, (minus_di - plus_di) / 50)
                        confidence = 0.8
                else:
                    signal_direction = "HOLD"
                    signal_strength = 0.0
                    confidence = 0.5
            else:
                signal_direction = "HOLD"
                signal_strength = 0.0
                confidence = 0.3
            
            signals_to_save.append(TechnicalSignalsModel(
                symbol=symbol,
                signal_type="ADX",
                signal_value=float(adx),
                signal_strength=float(signal_strength),
                signal_direction=signal_direction,
                indicator_value=float(adx),
                threshold_upper=25.0,
                threshold_lower=0.0,
                confidence=float(confidence)
            ))
        
        # Signal Parabolic SAR
        if 'parabolic_sar' in indicators_data and indicators_data['parabolic_sar'] is not None:
            sar = indicators_data['parabolic_sar']
            current_price = safe_float(df['close'].iloc[-1])
            
            if current_price and sar:
                if current_price > sar:
                    signal_direction = "BUY"
                    signal_strength = min(1.0, (current_price - sar) / current_price)
                    confidence = 0.7
                else:
                    signal_direction = "SELL"
                    signal_strength = min(1.0, (sar - current_price) / current_price)
                    confidence = 0.7
                
                signals_to_save.append(TechnicalSignalsModel(
                    symbol=symbol,
                    signal_type="PARABOLIC_SAR",
                    signal_value=float(current_price),
                    signal_strength=float(signal_strength),
                    signal_direction=signal_direction,
                    indicator_value=float(sar),
                    threshold_upper=float(current_price),
                    threshold_lower=float(sar),
                    confidence=float(confidence)
                ))
        
        # Signal Ichimoku
        if 'ichimoku' in indicators_data:
            ichimoku = indicators_data['ichimoku']
            current_price = safe_float(df['close'].iloc[-1])
            
            if (current_price and ichimoku['tenkan_sen'] and ichimoku['kijun_sen'] and 
                ichimoku['senkou_span_a'] and ichimoku['senkou_span_b']):
                
                tenkan = ichimoku['tenkan_sen']
                kijun = ichimoku['kijun_sen']
                senkou_a = ichimoku['senkou_span_a']
                senkou_b = ichimoku['senkou_span_b']
                
                # Logique Ichimoku simplifiée
                if current_price > tenkan and current_price > kijun:
                    if current_price > max(senkou_a, senkou_b):
                        signal_direction = "BUY"
                        signal_strength = 0.8
                        confidence = 0.8
                    else:
                        signal_direction = "HOLD"
                        signal_strength = 0.3
                        confidence = 0.6
                elif current_price < tenkan and current_price < kijun:
                    if current_price < min(senkou_a, senkou_b):
                        signal_direction = "SELL"
                        signal_strength = 0.8
                        confidence = 0.8
                    else:
                        signal_direction = "HOLD"
                        signal_strength = 0.3
                        confidence = 0.6
                else:
                    signal_direction = "HOLD"
                    signal_strength = 0.0
                    confidence = 0.5
                
                signals_to_save.append(TechnicalSignalsModel(
                    symbol=symbol,
                    signal_type="ICHIMOKU",
                    signal_value=float(current_price),
                    signal_strength=float(signal_strength),
                    signal_direction=signal_direction,
                    indicator_value=float(tenkan),
                    threshold_upper=float(max(senkou_a, senkou_b)),
                    threshold_lower=float(min(senkou_a, senkou_b)),
                    confidence=float(confidence)
                ))
        
        # Sauvegarder tous les signaux
        for signal in signals_to_save:
            db.add(signal)
        
        db.commit()
        
        # Préparer les données de support/résistance de manière sécurisée
        support_resistance_data = {
            "pivot_points": {
                "pivot": None,
                "r1": None,
                "r2": None,
                "s1": None,
                "s2": None
            },
            "support_levels": [],
            "resistance_levels": []
        }
        
        if 'pivot_points' in support_resistance:
            pivot_data = support_resistance['pivot_points']
            for key in ['pivot', 'r1', 'r2', 's1', 's2']:
                if key in pivot_data and not pivot_data[key].empty:
                    support_resistance_data["pivot_points"][key] = safe_float(pivot_data[key].iloc[-1])
        
        # Convertir les listes de niveaux de manière sécurisée (nouveau format multi-temporel)
        if 'support_levels' in support_resistance:
            for level in support_resistance['support_levels']:
                if isinstance(level, dict):
                    # Nouveau format avec métadonnées
                    price = safe_float(level.get('price'))
                    if price is not None:
                        support_resistance_data["support_levels"].append(price)
                else:
                    # Ancien format simple
                    converted_level = safe_float(level)
                    if converted_level is not None:
                        support_resistance_data["support_levels"].append(converted_level)
        
        if 'resistance_levels' in support_resistance:
            for level in support_resistance['resistance_levels']:
                if isinstance(level, dict):
                    # Nouveau format avec métadonnées
                    price = safe_float(level.get('price'))
                    if price is not None:
                        support_resistance_data["resistance_levels"].append(price)
                else:
                    # Ancien format simple
                    converted_level = safe_float(level)
                    if converted_level is not None:
                        support_resistance_data["resistance_levels"].append(converted_level)
        
        # Préparer les signaux de patterns de manière sécurisée
        pattern_signals = {}
        try:
            pattern_signals = CandlestickPatterns.get_pattern_signals(patterns)
            # Convertir les valeurs numpy en types Python natifs
            for key, value in pattern_signals.items():
                if isinstance(value, np.integer):
                    pattern_signals[key] = int(value)
                elif isinstance(value, np.floating):
                    pattern_signals[key] = float(value)
        except Exception:
            pattern_signals = {}
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "indicators": indicators_data,
            "patterns": {
                "recent_patterns": patterns_data,
                "pattern_signals": pattern_signals
            },
            "support_resistance": support_resistance_data,
            "composite_signal": signals_data,
            "persisted_signals": len(signals_to_save),
            "current_price": safe_float(df['close'].iloc[-1]),
            "previous_price": safe_float(df['close'].iloc[-2]) if len(df) > 1 else None,
            "last_update": df.index[-1].strftime('%Y-%m-%d %H:%M:%S') if hasattr(df.index[-1], 'strftime') else datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "historical_prices": df[['close']].tail(30).to_dict('records'),  # 30 derniers cours
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
