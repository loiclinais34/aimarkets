"""
Endpoint API simple pour l'analyse technique.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ...services.polygon_service import PolygonService
from ...services.technical_analysis import TechnicalIndicators
from ...utils.json_encoder import make_json_safe

router = APIRouter()

@router.get("/signals/{symbol}")
async def get_technical_signals_simple(symbol: str) -> Dict[str, Any]:
    """
    Récupère les signaux d'analyse technique pour un symbole.
    
    Args:
        symbol: Symbole du titre (ex: AAPL)
        
    Returns:
        Dictionnaire contenant les signaux d'analyse technique
    """
    try:
        period = 252
        
        # Récupérer les données
        polygon_service = PolygonService()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period + 50)
        
        historical_data = polygon_service.get_historical_data(
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
        
        # Calculer les indicateurs techniques
        rsi = TechnicalIndicators.rsi(df['close'], period=14)
        macd_result = TechnicalIndicators.macd(df['close'])
        bb_result = TechnicalIndicators.bollinger_bands(df['close'])
        
        return make_json_safe({
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "rsi": float(rsi.iloc[-1]),
            "macd": {
                "macd": float(macd_result['macd'].iloc[-1]),
                "signal": float(macd_result['signal'].iloc[-1]),
                "histogram": float(macd_result['histogram'].iloc[-1])
            },
            "bollinger_bands": {
                "upper": float(bb_result['upper'].iloc[-1]),
                "middle": float(bb_result['middle'].iloc[-1]),
                "lower": float(bb_result['lower'].iloc[-1])
            },
            "current_price": float(df['close'].iloc[-1])
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse technique: {str(e)}"
        )
