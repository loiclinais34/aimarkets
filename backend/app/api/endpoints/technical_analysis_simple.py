"""
Endpoint API simple pour l'analyse technique avec persistance.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ...core.database import get_db
from ...models.database import HistoricalData
from ...services.technical_analysis import TechnicalIndicators
from ...models.technical_analysis import TechnicalSignals as TechnicalSignalsModel
from ...utils.json_encoder import make_json_safe

router = APIRouter()

@router.get("/signals/{symbol}")
async def get_technical_signals_simple(symbol: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Récupère les signaux d'analyse technique pour un symbole avec persistance.
    
    Args:
        symbol: Symbole du titre (ex: AAPL)
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant les signaux d'analyse technique
    """
    try:
        period = 252
        
        # Récupérer les données depuis la base de données
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=period + 50)
        
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
        rsi = TechnicalIndicators.rsi(df['close'], period=14)
        macd_result = TechnicalIndicators.macd(df['close'])
        bb_result = TechnicalIndicators.bollinger_bands(df['close'])
        
        # Persister les signaux techniques
        signals_to_save = []
        
        # Signal RSI
        if not rsi.empty:
            rsi_value = float(rsi.iloc[-1])
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
                signal_value=rsi_value,
                signal_strength=signal_strength,
                signal_direction=signal_direction,
                indicator_value=rsi_value,
                threshold_upper=70.0,
                threshold_lower=30.0,
                confidence=confidence
            ))
        
        # Signal MACD
        if macd_result and 'histogram' in macd_result and not macd_result['histogram'].empty:
            histogram = float(macd_result['histogram'].iloc[-1])
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
                signal_value=histogram,
                signal_strength=signal_strength,
                signal_direction=signal_direction,
                indicator_value=histogram,
                threshold_upper=0.1,
                threshold_lower=-0.1,
                confidence=confidence
            ))
        
        # Signal Bollinger Bands
        if bb_result and 'upper' in bb_result and 'lower' in bb_result:
            current_price = float(df['close'].iloc[-1])
            upper = float(bb_result['upper'].iloc[-1])
            lower = float(bb_result['lower'].iloc[-1])
            
            if current_price > upper:
                signal_direction = "SELL"
                signal_strength = min(1.0, (current_price - upper) / (upper - lower) * 2)
                confidence = 0.8
            elif current_price < lower:
                signal_direction = "BUY"
                signal_strength = min(1.0, (lower - current_price) / (upper - lower) * 2)
                confidence = 0.8
            else:
                signal_direction = "HOLD"
                signal_strength = 0.0
                confidence = 0.5
            
            signals_to_save.append(TechnicalSignalsModel(
                symbol=symbol,
                signal_type="BOLLINGER_BANDS",
                signal_value=current_price,
                signal_strength=signal_strength,
                signal_direction=signal_direction,
                indicator_value=current_price,
                threshold_upper=upper,
                threshold_lower=lower,
                confidence=confidence
            ))
        
        # Supprimer les anciens signaux pour ce symbole
        db.query(TechnicalSignalsModel).filter(
            TechnicalSignalsModel.symbol == symbol,
            TechnicalSignalsModel.created_at < datetime.now() - timedelta(hours=1)
        ).delete()
        
        # Sauvegarder les nouveaux signaux
        for signal in signals_to_save:
            db.add(signal)
        
        db.commit()
        
        return make_json_safe({
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "rsi": float(rsi.iloc[-1]) if not rsi.empty else None,
            "macd": {
                "macd": float(macd_result['macd'].iloc[-1]) if macd_result and not macd_result['macd'].empty else None,
                "signal": float(macd_result['signal'].iloc[-1]) if macd_result and not macd_result['signal'].empty else None,
                "histogram": float(macd_result['histogram'].iloc[-1]) if macd_result and not macd_result['histogram'].empty else None
            },
            "bollinger_bands": {
                "upper": float(bb_result['upper'].iloc[-1]) if bb_result and not bb_result['upper'].empty else None,
                "middle": float(bb_result['middle'].iloc[-1]) if bb_result and not bb_result['middle'].empty else None,
                "lower": float(bb_result['lower'].iloc[-1]) if bb_result and not bb_result['lower'].empty else None
            },
            "current_price": float(df['close'].iloc[-1]),
            "persisted_signals": len(signals_to_save)
        })
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse technique: {str(e)}"
        )
