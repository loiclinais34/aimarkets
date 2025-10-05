from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ...core.database import get_db
from ...models.database import SymbolMetadata

router = APIRouter()

@router.get("/symbols", response_model=List[dict])
async def get_symbols(
    search: Optional[str] = Query(None, description="Recherche par symbole ou nom d'entreprise"),
    limit: int = Query(100, description="Nombre maximum de résultats"),
    db: Session = Depends(get_db)
):
    """
    Récupère la liste des symboles disponibles depuis symbol_metadata
    """
    query = db.query(SymbolMetadata).filter(SymbolMetadata.is_active == True)
    
    if search:
        search_term = f"%{search.upper()}%"
        query = query.filter(
            (SymbolMetadata.symbol.contains(search_term.upper())) |
            (SymbolMetadata.company_name.contains(search_term))
        )
    
    symbols = query.order_by(SymbolMetadata.symbol).limit(limit).all()
    
    return [
        {
            "symbol": symbol.symbol,
            "company_name": symbol.company_name,
            "sector": symbol.sector,
            "industry": symbol.industry,
            "market_cap_category": symbol.market_cap_category
        }
        for symbol in symbols
    ]

@router.get("/symbols/{symbol}")
async def get_symbol_details(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Récupère les détails d'un symbole spécifique
    """
    symbol_data = db.query(SymbolMetadata).filter(
        SymbolMetadata.symbol == symbol.upper(),
        SymbolMetadata.is_active == True
    ).first()
    
    if not symbol_data:
        return {"error": "Symbole non trouvé"}
    
    return {
        "symbol": symbol_data.symbol,
        "company_name": symbol_data.company_name,
        "sector": symbol_data.sector,
        "industry": symbol_data.industry,
        "market_cap_category": symbol_data.market_cap_category
    }
