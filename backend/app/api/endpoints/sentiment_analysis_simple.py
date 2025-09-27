"""
Endpoint API simple pour l'analyse de sentiment.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ...services.polygon_service import PolygonService
from ...services.sentiment_analysis import GARCHModels
from ...utils.json_encoder import make_json_safe

router = APIRouter()

@router.get("/garch/{symbol}")
async def get_garch_analysis_simple(symbol: str) -> Dict[str, Any]:
    """
    Récupère l'analyse GARCH simplifiée pour un symbole.
    
    Args:
        symbol: Symbole du titre (ex: AAPL)
        
    Returns:
        Dictionnaire contenant l'analyse GARCH simplifiée
    """
    try:
        # Récupérer les données historiques
        polygon_service = PolygonService()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
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
        
        # Calculer les rendements
        returns = GARCHModels.calculate_returns(df['close'])
        
        if len(returns) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pas assez de données pour ajuster un modèle GARCH. Requis: 100, Disponible: {len(returns)}"
            )
        
        # Statistiques descriptives simples
        descriptive_stats = {
            "mean_return": float(returns.mean()),
            "std_return": float(returns.std()),
            "skewness": float(returns.skew()),
            "kurtosis": float(returns.kurtosis()),
            "min_return": float(returns.min()),
            "max_return": float(returns.max()),
            "total_observations": len(returns)
        }
        
        # Test simple d'un modèle GARCH
        try:
            garch_result = GARCHModels.fit_garch(returns, model_type="GARCH", p=1, q=1)
            garch_success = True
            garch_error = None
        except Exception as e:
            garch_success = False
            garch_error = str(e)
        
        return make_json_safe({
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "descriptive_stats": descriptive_stats,
            "garch_model": {
                "success": garch_success,
                "error": garch_error
            },
            "current_price": float(df['close'].iloc[-1]),
            "data_period": {
                "start": str(returns.index[0]),
                "end": str(returns.index[-1]),
                "duration_days": (returns.index[-1] - returns.index[0]).days
            }
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse GARCH: {str(e)}"
        )
