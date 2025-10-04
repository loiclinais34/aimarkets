"""
Endpoints de gestion des positions et transactions
"""

from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.position_service import PositionService
from app.services.portfolio_service import PortfolioService
from app.api.endpoints.auth import get_current_user

router = APIRouter()


# ==================== MODÈLES PYDANTIC ====================

class BuyOrderRequest(BaseModel):
    symbol: str
    quantity: Decimal
    price: Decimal
    fee: Decimal = Decimal('0.00')
    currency: str = "USD"


class SellOrderRequest(BaseModel):
    symbol: str
    quantity: Decimal
    price: Decimal
    fee: Decimal = Decimal('0.00')
    currency: str = "USD"


class PositionTransactionResponse(BaseModel):
    id: int
    transaction_type: str
    quantity: Decimal
    price: Decimal
    fee: Decimal
    transaction_date: str


class PositionResponse(BaseModel):
    id: int
    symbol: str
    quantity: Decimal
    average_buy_price: Decimal
    current_price: Decimal
    cost_basis: Decimal
    market_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percent: Decimal
    realized_pnl: Decimal
    currency: str
    position_type: str
    created_at: str
    updated_at: str


class PositionPerformanceResponse(BaseModel):
    position_id: int
    symbol: str
    quantity: Decimal
    average_buy_price: Decimal
    current_price: Decimal
    cost_basis: Decimal
    current_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percent: Decimal
    realized_pnl: Decimal
    total_pnl: Decimal
    total_return_percent: Decimal


class OrderExecutionResponse(BaseModel):
    position: PositionResponse
    transaction: PositionTransactionResponse
    message: str


class PortfolioSummaryResponse(BaseModel):
    total_positions: int
    total_value: Decimal
    total_cost_basis: Decimal
    total_pnl: Decimal
    winning_positions: int
    losing_positions: int
    neutral_positions: int


class PriceUpdateRequest(BaseModel):
    symbol: str
    price: Decimal


class BatchPriceUpdateRequest(BaseModel):
    price_updates: List[PriceUpdateRequest]


# ==================== ENDPOINTS ====================

@router.post("/{portfolio_id}/buy", response_model=OrderExecutionResponse)
async def execute_buy_order(
    portfolio_id: int,
    order: BuyOrderRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exécute un ordre d'achat"""
    
    position_service = PositionService(db)
    
    # Vérifier que le portefeuille appartient à l'utilisateur
    portfolio_service = PortfolioService(db)
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    try:
        position, transaction = position_service.execute_buy_order(
            portfolio_id=portfolio_id,
            symbol=order.symbol,
            quantity=order.quantity,
            price=order.price,
            fee=order.fee,
            currency=order.currency
        )
        
        return OrderExecutionResponse(
            position=PositionResponse(
                id=position.id,
                symbol=position.symbol,
                quantity=position.quantity,
                average_buy_price=position.average_buy_price,
                current_price=position.current_price,
                cost_basis=position.cost_basis,
                market_value=position.market_value,
                unrealized_pnl=position.unrealized_pnl,
                unrealized_pnl_percent=position.unrealized_pnl_percent,
                realized_pnl=position.realized_pnl,
                currency=position.currency,
                position_type=position.position_type.value,
                created_at=position.created_at.isoformat(),
                updated_at=position.updated_at.isoformat()
            ),
            transaction=PositionTransactionResponse(
                id=transaction.id,
                transaction_type=transaction.transaction_type,
                quantity=transaction.quantity,
                price=transaction.price,
                fee=transaction.fee,
                transaction_date=transaction.transaction_date.isoformat()
            ),
            message=f"Achat de {order.quantity} {order.symbol} à {order.price} exécuté avec succès"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'exécution de l'ordre d'achat: {str(e)}"
        )


@router.post("/{portfolio_id}/sell", response_model=OrderExecutionResponse)
async def execute_sell_order(
    portfolio_id: int,
    order: SellOrderRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exécute un ordre de vente"""
    
    position_service = PositionService(db)
    
    # Vérifier que le portefeuille appartient à l'utilisateur
    portfolio_service = PortfolioService(db)
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    try:
        position, transaction = position_service.execute_sell_order(
            portfolio_id=portfolio_id,
            symbol=order.symbol,
            quantity=order.quantity,
            price=order.price,
            fee=order.fee,
            currency=order.currency
        )
        
        return OrderExecutionResponse(
            position=PositionResponse(
                id=position.id,
                symbol=position.symbol,
                quantity=position.quantity,
                average_buy_price=position.average_buy_price,
                current_price=position.current_price,
                cost_basis=position.cost_basis,
                market_value=position.market_value,
                unrealized_pnl=position.unrealized_pnl,
                unrealized_pnl_percent=position.unrealized_pnl_percent,
                realized_pnl=position.realized_pnl,
                currency=position.currency,
                position_type=position.position_type.value,
                created_at=position.created_at.isoformat(),
                updated_at=position.updated_at.isoformat()
            ),
            transaction=PositionTransactionResponse(
                id=transaction.id,
                transaction_type=transaction.transaction_type,
                quantity=transaction.quantity,
                price=transaction.price,
                fee=transaction.fee,
                transaction_date=transaction.transaction_date.isoformat()
            ),
            message=f"Vente de {order.quantity} {order.symbol} à {order.price} exécutée avec succès"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'exécution de l'ordre de vente: {str(e)}"
        )


@router.get("/{portfolio_id}/positions", response_model=List[PositionResponse])
async def get_portfolio_positions(
    portfolio_id: int,
    skip: int = Query(0, ge=0, description="Nombre de positions à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de positions à retourner"),
    symbol_filter: Optional[str] = Query(None, description="Filtrer par symbole"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les positions d'un portefeuille"""
    
    position_service = PositionService(db)
    
    # Vérifier que le portefeuille appartient à l'utilisateur
    portfolio_service = PortfolioService(db)
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    positions = position_service.get_portfolio_positions(
        portfolio_id=portfolio_id,
        skip=skip,
        limit=limit,
        symbol_filter=symbol_filter
    )
    
    return [
        PositionResponse(
            id=position.id,
            symbol=position.symbol,
            quantity=position.quantity,
            average_buy_price=position.average_buy_price,
            current_price=position.current_price,
            cost_basis=position.cost_basis,
            market_value=position.market_value,
            unrealized_pnl=position.unrealized_pnl,
            unrealized_pnl_percent=position.unrealized_pnl_percent,
            realized_pnl=position.realized_pnl,
            currency=position.currency,
            position_type=position.position_type.value,
            created_at=position.created_at.isoformat(),
            updated_at=position.updated_at.isoformat()
        )
        for position in positions
    ]


@router.get("/positions/{position_id}", response_model=PositionResponse)
async def get_position(
    position_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère une position par son ID"""
    
    position_service = PositionService(db)
    position = position_service.get_position_by_id(position_id)
    
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position non trouvée"
        )
    
    # Vérifier que la position appartient à un portefeuille de l'utilisateur
    portfolio_service = PortfolioService(db)
    portfolio = portfolio_service.get_portfolio_by_id(position.portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position non trouvée"
        )
    
    return PositionResponse(
        id=position.id,
        symbol=position.symbol,
        quantity=position.quantity,
        average_buy_price=position.average_buy_price,
        current_price=position.current_price,
        cost_basis=position.cost_basis,
        market_value=position.market_value,
        unrealized_pnl=position.unrealized_pnl,
        unrealized_pnl_percent=position.unrealized_pnl_percent,
        realized_pnl=position.realized_pnl,
        currency=position.currency,
        position_type=position.position_type.value,
        created_at=position.created_at.isoformat(),
        updated_at=position.updated_at.isoformat()
    )


@router.get("/positions/{position_id}/performance", response_model=PositionPerformanceResponse)
async def get_position_performance(
    position_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calcule et retourne la performance d'une position"""
    
    position_service = PositionService(db)
    position = position_service.get_position_by_id(position_id)
    
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position non trouvée"
        )
    
    # Vérifier que la position appartient à un portefeuille de l'utilisateur
    portfolio_service = PortfolioService(db)
    portfolio = portfolio_service.get_portfolio_by_id(position.portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position non trouvée"
        )
    
    performance = position_service.calculate_position_performance(position_id)
    
    return PositionPerformanceResponse(**performance)


@router.get("/positions/{position_id}/transactions", response_model=List[PositionTransactionResponse])
async def get_position_transactions(
    position_id: int,
    skip: int = Query(0, ge=0, description="Nombre de transactions à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de transactions à retourner"),
    transaction_type: Optional[str] = Query(None, description="Filtrer par type de transaction"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les transactions d'une position"""
    
    position_service = PositionService(db)
    position = position_service.get_position_by_id(position_id)
    
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position non trouvée"
        )
    
    # Vérifier que la position appartient à un portefeuille de l'utilisateur
    portfolio_service = PortfolioService(db)
    portfolio = portfolio_service.get_portfolio_by_id(position.portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position non trouvée"
        )
    
    transactions = position_service.get_position_transactions(
        position_id=position_id,
        skip=skip,
        limit=limit,
        transaction_type=transaction_type
    )
    
    return [
        PositionTransactionResponse(
            id=transaction.id,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            price=transaction.price,
            fee=transaction.fee,
            transaction_date=transaction.transaction_date.isoformat()
        )
        for transaction in transactions
    ]


@router.get("/{portfolio_id}/transactions", response_model=List[PositionTransactionResponse])
async def get_portfolio_transactions(
    portfolio_id: int,
    skip: int = Query(0, ge=0, description="Nombre de transactions à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de transactions à retourner"),
    symbol_filter: Optional[str] = Query(None, description="Filtrer par symbole"),
    transaction_type: Optional[str] = Query(None, description="Filtrer par type de transaction"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère toutes les transactions d'un portefeuille"""
    
    position_service = PositionService(db)
    
    # Vérifier que le portefeuille appartient à l'utilisateur
    portfolio_service = PortfolioService(db)
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    transactions = position_service.get_portfolio_transactions(
        portfolio_id=portfolio_id,
        skip=skip,
        limit=limit,
        symbol_filter=symbol_filter,
        transaction_type=transaction_type
    )
    
    return [
        PositionTransactionResponse(
            id=transaction.id,
            transaction_type=transaction.transaction_type,
            quantity=transaction.quantity,
            price=transaction.price,
            fee=transaction.fee,
            transaction_date=transaction.transaction_date.isoformat()
        )
        for transaction in transactions
    ]


@router.post("/{portfolio_id}/prices/update")
async def update_position_prices(
    portfolio_id: int,
    price_updates: BatchPriceUpdateRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Met à jour les prix de plusieurs positions"""
    
    position_service = PositionService(db)
    
    # Vérifier que le portefeuille appartient à l'utilisateur
    portfolio_service = PortfolioService(db)
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    # Convertir en dictionnaire
    price_dict = {update.symbol: update.price for update in price_updates.price_updates}
    
    updated_count = position_service.update_position_prices(portfolio_id, price_dict)
    
    return {
        "message": f"{updated_count} positions mises à jour",
        "updated_positions": updated_count
    }


@router.get("/{portfolio_id}/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    portfolio_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retourne un résumé des positions d'un portefeuille"""
    
    position_service = PositionService(db)
    
    # Vérifier que le portefeuille appartient à l'utilisateur
    portfolio_service = PortfolioService(db)
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    summary = position_service.get_portfolio_summary(portfolio_id)
    
    return PortfolioSummaryResponse(**summary)


@router.get("/{portfolio_id}/top-positions", response_model=List[PositionPerformanceResponse])
async def get_top_positions(
    portfolio_id: int,
    limit: int = Query(10, ge=1, le=50, description="Nombre de positions à retourner"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retourne les meilleures positions d'un portefeuille"""
    
    position_service = PositionService(db)
    
    # Vérifier que le portefeuille appartient à l'utilisateur
    portfolio_service = PortfolioService(db)
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    top_positions = position_service.get_top_positions(portfolio_id, limit)
    
    return [PositionPerformanceResponse(**pos) for pos in top_positions]


@router.get("/{portfolio_id}/worst-positions", response_model=List[PositionPerformanceResponse])
async def get_worst_positions(
    portfolio_id: int,
    limit: int = Query(10, ge=1, le=50, description="Nombre de positions à retourner"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retourne les pires positions d'un portefeuille"""
    
    position_service = PositionService(db)
    
    # Vérifier que le portefeuille appartient à l'utilisateur
    portfolio_service = PortfolioService(db)
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    worst_positions = position_service.get_worst_positions(portfolio_id, limit)
    
    return [PositionPerformanceResponse(**pos) for pos in worst_positions]


@router.post("/positions/{position_id}/close")
async def close_position(
    position_id: int,
    sell_price: Decimal,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ferme complètement une position"""
    
    position_service = PositionService(db)
    position = position_service.get_position_by_id(position_id)
    
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position non trouvée"
        )
    
    # Vérifier que la position appartient à un portefeuille de l'utilisateur
    portfolio_service = PortfolioService(db)
    portfolio = portfolio_service.get_portfolio_by_id(position.portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Position non trouvée"
        )
    
    success, realized_pnl = position_service.close_position(position_id, sell_price)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de fermer la position"
        )
    
    return {
        "message": "Position fermée avec succès",
        "realized_pnl": realized_pnl
    }
