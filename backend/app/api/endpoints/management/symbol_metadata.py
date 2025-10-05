from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.database import SymbolMetadata
from app.models.schemas import SymbolMetadata as SymbolMetadataSchema, SymbolMetadataCreate, SymbolMetadataUpdate

router = APIRouter()

@router.get("/", response_model=List[SymbolMetadataSchema])
def get_symbols_metadata(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre d'éléments à retourner"),
    sector: Optional[str] = Query(None, description="Filtrer par secteur"),
    is_active: Optional[bool] = Query(True, description="Filtrer par statut actif"),
    db: Session = Depends(get_db)
):
    """Récupérer la liste des métadonnées des symboles"""
    try:
        query = db.query(SymbolMetadata)
        
        if sector:
            query = query.filter(SymbolMetadata.sector == sector)
        
        if is_active is not None:
            query = query.filter(SymbolMetadata.is_active == is_active)
        
        symbols = query.offset(skip).limit(limit).all()
        return symbols
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des métadonnées: {str(e)}")

@router.get("/{symbol}", response_model=SymbolMetadataSchema)
def get_symbol_metadata(symbol: str, db: Session = Depends(get_db)):
    """Récupérer les métadonnées d'un symbole spécifique"""
    try:
        symbol_metadata = db.query(SymbolMetadata).filter(SymbolMetadata.symbol == symbol.upper()).first()
        if not symbol_metadata:
            raise HTTPException(status_code=404, detail=f"Métadonnées non trouvées pour le symbole {symbol}")
        return symbol_metadata
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des métadonnées: {str(e)}")

@router.get("/search/company", response_model=List[SymbolMetadataSchema])
def search_symbols_by_company(
    company_name: str = Query(..., description="Nom de l'entreprise à rechercher"),
    limit: int = Query(10, ge=1, le=50, description="Nombre de résultats à retourner"),
    db: Session = Depends(get_db)
):
    """Rechercher des symboles par nom d'entreprise"""
    try:
        symbols = db.query(SymbolMetadata).filter(
            SymbolMetadata.company_name.ilike(f"%{company_name}%")
        ).limit(limit).all()
        return symbols
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la recherche: {str(e)}")

@router.get("/sectors/list", response_model=List[str])
def get_sectors_list(db: Session = Depends(get_db)):
    """Récupérer la liste des secteurs disponibles"""
    try:
        sectors = db.query(SymbolMetadata.sector).distinct().filter(
            SymbolMetadata.sector.isnot(None)
        ).all()
        return [sector[0] for sector in sectors if sector[0]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur lors de la récupération des secteurs: {str(e)}")

@router.post("/", response_model=SymbolMetadataSchema)
def create_symbol_metadata(symbol_data: SymbolMetadataCreate, db: Session = Depends(get_db)):
    """Créer de nouvelles métadonnées pour un symbole"""
    try:
        # Vérifier si le symbole existe déjà
        existing = db.query(SymbolMetadata).filter(SymbolMetadata.symbol == symbol_data.symbol.upper()).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Les métadonnées pour le symbole {symbol_data.symbol} existent déjà")
        
        new_metadata = SymbolMetadata(
            symbol=symbol_data.symbol.upper(),
            company_name=symbol_data.company_name,
            sector=symbol_data.sector,
            industry=symbol_data.industry,
            market_cap_category=symbol_data.market_cap_category,
            is_active=symbol_data.is_active
        )
        
        db.add(new_metadata)
        db.commit()
        db.refresh(new_metadata)
        
        return new_metadata
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la création des métadonnées: {str(e)}")

@router.put("/{symbol}", response_model=SymbolMetadataSchema)
def update_symbol_metadata(
    symbol: str, 
    symbol_data: SymbolMetadataUpdate, 
    db: Session = Depends(get_db)
):
    """Mettre à jour les métadonnées d'un symbole"""
    try:
        symbol_metadata = db.query(SymbolMetadata).filter(SymbolMetadata.symbol == symbol.upper()).first()
        if not symbol_metadata:
            raise HTTPException(status_code=404, detail=f"Métadonnées non trouvées pour le symbole {symbol}")
        
        # Mettre à jour les champs fournis
        update_data = symbol_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(symbol_metadata, field, value)
        
        db.commit()
        db.refresh(symbol_metadata)
        
        return symbol_metadata
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la mise à jour des métadonnées: {str(e)}")

@router.delete("/{symbol}")
def delete_symbol_metadata(symbol: str, db: Session = Depends(get_db)):
    """Supprimer les métadonnées d'un symbole"""
    try:
        symbol_metadata = db.query(SymbolMetadata).filter(SymbolMetadata.symbol == symbol.upper()).first()
        if not symbol_metadata:
            raise HTTPException(status_code=404, detail=f"Métadonnées non trouvées pour le symbole {symbol}")
        
        db.delete(symbol_metadata)
        db.commit()
        
        return {"message": f"Métadonnées supprimées pour le symbole {symbol}"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erreur lors de la suppression des métadonnées: {str(e)}")
