"""
Endpoints API pour le trading de titres
"""

from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.endpoints.auth.auth import get_current_user
from app.services.trading_service import TradingService
from app.services.portfolio_service import PortfolioService

router = APIRouter()

# ==================== MODÈLES PYDANTIC ====================

class BuyStockRequest(BaseModel):
    wallet_id: int
    symbol: str
    quantity: Decimal
    price: Decimal
    fees: Decimal = Decimal('0.00')
    description: Optional[str] = None

class SellStockRequest(BaseModel):
    wallet_id: int
    symbol: str
    quantity: Decimal
    price: Decimal
    fees: Decimal = Decimal('0.00')
    description: Optional[str] = None
    target_wallet_id: Optional[int] = None  # Wallet de destination pour le produit de la vente

class WalletTransactionResponse(BaseModel):
    id: int
    wallet_id: int
    transaction_type: str
    amount: Decimal
    balance_after: Decimal
    symbol: Optional[str]
    quantity: Optional[Decimal]
    price: Optional[Decimal]
    fees: Optional[Decimal]
    description: Optional[str]
    created_at: str

class PositionResponse(BaseModel):
    id: int
    symbol: str
    company_name: Optional[str]
    quantity: Decimal
    average_cost: Decimal
    current_price: Optional[Decimal]
    total_cost: Decimal
    current_value: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_percentage: Decimal
    realized_pnl: Decimal
    total_dividends: Decimal
    total_fees: Decimal
    weight_percentage: Decimal
    currency: str
    created_at: str
    updated_at: str
    first_purchase_date: Optional[str]
    last_purchase_date: Optional[str]
    last_sale_date: Optional[str]

class TradingResponse(BaseModel):
    transaction: WalletTransactionResponse
    position: PositionResponse
    message: str

# ==================== ENDPOINTS ====================

@router.post("/{portfolio_id}/buy", response_model=TradingResponse)
async def buy_stock(
    portfolio_id: int,
    request: BuyStockRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Acheter des titres"""
    
    trading_service = TradingService(db)
    portfolio_service = PortfolioService(db)
    
    # Vérifier que le portefeuille appartient à l'utilisateur
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    try:
        transaction, position = trading_service.buy_stock(
            portfolio_id=portfolio_id,
            wallet_id=request.wallet_id,
            symbol=request.symbol,
            quantity=request.quantity,
            price=request.price,
            fees=request.fees,
            description=request.description
        )
        
        return TradingResponse(
            transaction=WalletTransactionResponse(
                id=transaction.id,
                transaction_type=transaction.transaction_type.value,
                amount=transaction.amount,
                balance_after=transaction.balance_after,
                symbol=transaction.symbol,
                quantity=transaction.quantity,
                price=transaction.price,
                fees=transaction.fees,
                description=transaction.description,
                created_at=transaction.created_at.isoformat()
            ),
            position=PositionResponse(
                id=position.id,
                symbol=position.symbol,
                company_name=position.company_name,
                quantity=position.quantity,
                average_cost=position.average_cost,
                current_price=position.current_price,
                total_cost=position.total_cost,
                current_value=position.current_value,
                unrealized_pnl=position.unrealized_pnl,
                unrealized_pnl_percentage=position.unrealized_pnl_percentage,
                realized_pnl=position.realized_pnl,
                total_dividends=position.total_dividends,
                total_fees=position.total_fees,
                weight_percentage=position.weight_percentage,
                currency=position.currency,
                created_at=position.created_at.isoformat(),
                updated_at=position.updated_at.isoformat(),
                first_purchase_date=position.first_purchase_date.isoformat() if position.first_purchase_date else None,
                last_purchase_date=position.last_purchase_date.isoformat() if position.last_purchase_date else None,
                last_sale_date=position.last_sale_date.isoformat() if position.last_sale_date else None
            ),
            message=f"Achat de {request.quantity} {request.symbol} à {request.price} exécuté avec succès"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'achat: {str(e)}"
        )

@router.post("/{portfolio_id}/sell", response_model=TradingResponse)
async def sell_stock(
    portfolio_id: int,
    request: SellStockRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Vendre des titres"""
    
    trading_service = TradingService(db)
    portfolio_service = PortfolioService(db)
    
    # Vérifier que le portefeuille appartient à l'utilisateur
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    try:
        transaction, position = trading_service.sell_stock(
            portfolio_id=portfolio_id,
            wallet_id=request.wallet_id,
            symbol=request.symbol,
            quantity=request.quantity,
            price=request.price,
            fees=request.fees,
            description=request.description,
            target_wallet_id=request.target_wallet_id
        )
        
        return TradingResponse(
            transaction=WalletTransactionResponse(
                id=transaction.id,
                wallet_id=transaction.wallet_id,
                transaction_type=transaction.transaction_type.value,
                amount=transaction.amount,
                balance_after=transaction.balance_after,
                symbol=transaction.symbol,
                quantity=transaction.quantity,
                price=transaction.price,
                fees=transaction.fees,
                description=transaction.description,
                created_at=transaction.created_at.isoformat()
            ),
            position=PositionResponse(
                id=position.id,
                symbol=position.symbol,
                company_name=position.company_name,
                quantity=position.quantity,
                average_cost=position.average_cost,
                current_price=position.current_price,
                total_cost=position.total_cost,
                current_value=position.current_value,
                unrealized_pnl=position.unrealized_pnl,
                unrealized_pnl_percentage=position.unrealized_pnl_percentage,
                realized_pnl=position.realized_pnl,
                total_dividends=position.total_dividends,
                total_fees=position.total_fees,
                weight_percentage=position.weight_percentage,
                currency=position.currency,
                created_at=position.created_at.isoformat(),
                updated_at=position.updated_at.isoformat(),
                first_purchase_date=position.first_purchase_date.isoformat() if position.first_purchase_date else None,
                last_purchase_date=position.last_purchase_date.isoformat() if position.last_purchase_date else None,
                last_sale_date=position.last_sale_date.isoformat() if position.last_sale_date else None
            ),
            message=f"Vente de {request.quantity} {request.symbol} à {request.price} exécutée avec succès"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la vente: {str(e)}"
        )

@router.get("/{portfolio_id}/positions", response_model=List[PositionResponse])
async def get_positions(
    portfolio_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère toutes les positions d'un portefeuille"""
    
    trading_service = TradingService(db)
    portfolio_service = PortfolioService(db)
    
    # Vérifier que le portefeuille appartient à l'utilisateur
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    positions = trading_service.get_positions(portfolio_id)
    
    return [
        PositionResponse(
            id=position.id,
            symbol=position.symbol,
            company_name=position.company_name,
            quantity=position.quantity,
            average_cost=position.average_cost,
            current_price=position.current_price,
            total_cost=position.total_cost,
            current_value=position.current_value,
            unrealized_pnl=position.unrealized_pnl,
            unrealized_pnl_percentage=position.unrealized_pnl_percentage,
            realized_pnl=position.realized_pnl,
            total_dividends=position.total_dividends,
            total_fees=position.total_fees,
            weight_percentage=position.weight_percentage,
            currency=position.currency,
            created_at=position.created_at.isoformat(),
            updated_at=position.updated_at.isoformat(),
            first_purchase_date=position.first_purchase_date.isoformat() if position.first_purchase_date else None,
            last_purchase_date=position.last_purchase_date.isoformat() if position.last_purchase_date else None,
            last_sale_date=position.last_sale_date.isoformat() if position.last_sale_date else None
        )
        for position in positions
    ]

@router.get("/{portfolio_id}/history", response_model=List[WalletTransactionResponse])
async def get_trading_history(
    portfolio_id: int,
    symbol: Optional[str] = None,
    limit: int = 50,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère l'historique des transactions de trading"""
    
    trading_service = TradingService(db)
    portfolio_service = PortfolioService(db)
    
    # Vérifier que le portefeuille appartient à l'utilisateur
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    transactions = trading_service.get_trading_history(
        portfolio_id=portfolio_id,
        symbol=symbol,
        limit=limit
    )
    
    return [
        WalletTransactionResponse(
            id=transaction.id,
            transaction_type=transaction.transaction_type.value,
            amount=transaction.amount,
            balance_after=transaction.balance_after,
            symbol=transaction.symbol,
            quantity=transaction.quantity,
            price=transaction.price,
            fees=transaction.fees,
            description=transaction.description,
            created_at=transaction.created_at.isoformat()
        )
        for transaction in transactions
    ]
