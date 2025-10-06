"""
Endpoint pour récupérer les cours en temps réel via Polygon.io
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings
from app.services.polygon_service import PolygonService
from app.api.endpoints.auth.auth import get_current_user

router = APIRouter()


class RealtimePriceRequest(BaseModel):
    """Requête pour obtenir les cours en temps réel"""
    symbols: List[str]


class RealtimePriceResponse(BaseModel):
    """Réponse avec les cours en temps réel"""
    symbol: str
    price: float
    timestamp: str
    source: str = "polygon"


class RealtimePricesResponse(BaseModel):
    """Réponse avec plusieurs cours en temps réel"""
    prices: List[RealtimePriceResponse]
    timestamp: str
    total_symbols: int
    found_symbols: int


@router.post("/realtime-prices", response_model=RealtimePricesResponse)
async def get_realtime_prices(
    request: RealtimePriceRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Récupère les cours en temps réel pour une liste de symboles via Polygon.io
    
    Args:
        request: Liste des symboles à récupérer
    
    Returns:
        Dictionnaire avec les cours en temps réel
    """
    try:
        polygon_service = PolygonService()
        prices = []
        found_count = 0
        
        for symbol in request.symbols:
            try:
                # Essayer d'abord le snapshot (cours le plus récent disponible - 15min delay)
                quote_data = polygon_service.get_latest_quote(symbol)
                
                if quote_data:
                    prices.append(RealtimePriceResponse(
                        symbol=symbol,
                        price=float(quote_data['price']),
                        timestamp=quote_data['timestamp'].isoformat(),
                        source=quote_data.get('source', 'polygon_snapshot')
                    ))
                    found_count += 1
                else:
                    # Fallback : essayer le cours de clôture précédent
                    close_data = polygon_service.get_previous_close(symbol)
                    if close_data:
                        prices.append(RealtimePriceResponse(
                            symbol=symbol,
                            price=float(close_data['price']),
                            timestamp=close_data['timestamp'].isoformat(),
                            source="polygon_previous_close"
                        ))
                        found_count += 1
                    else:
                        # Si aucun cours Polygon, retourner 0
                        prices.append(RealtimePriceResponse(
                            symbol=symbol,
                            price=0.0,
                            timestamp=datetime.now().isoformat(),
                            source="not_found"
                        ))
            except Exception as e:
                print(f"Erreur lors de la récupération du cours pour {symbol}: {e}")
                # En cas d'erreur, retourner 0
                prices.append(RealtimePriceResponse(
                    symbol=symbol,
                    price=0.0,
                    timestamp=datetime.now().isoformat(),
                    source="error"
                ))
        
        return RealtimePricesResponse(
            prices=prices,
            timestamp=datetime.now().isoformat(),
            total_symbols=len(request.symbols),
            found_symbols=found_count
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la récupération des cours en temps réel: {str(e)}"
        )

