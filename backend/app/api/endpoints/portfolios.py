"""
Endpoints de gestion des portefeuilles
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.services.portfolio_service import PortfolioService
from app.services.authentication_service import AuthenticationService
from app.api.endpoints.auth import get_current_user
from app.models.portfolios import PortfolioType, PortfolioStatus

router = APIRouter()


# ==================== MODÈLES PYDANTIC ====================

class PortfolioCreate(BaseModel):
    name: str
    description: Optional[str] = None
    portfolio_type: PortfolioType = PortfolioType.PERSONAL
    initial_capital: Decimal = Decimal('0.00')
    risk_tolerance: str = "MODERATE"


class PortfolioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    portfolio_type: Optional[PortfolioType] = None
    risk_tolerance: Optional[str] = None
    auto_rebalance: Optional[bool] = None


class WalletCreate(BaseModel):
    name: str
    currency: str
    initial_balance: Decimal = Decimal('0.00')


class WalletResponse(BaseModel):
    id: int
    name: str
    currency: str
    wallet_type: str
    status: str
    available_balance: Decimal
    total_balance: Decimal
    created_at: str


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


class PortfolioResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    portfolio_type: str
    status: str
    initial_capital: Decimal
    current_value: Decimal
    total_invested: Decimal
    total_withdrawn: Decimal
    total_return: Decimal
    total_return_percentage: Decimal
    risk_tolerance: str
    currency: str
    auto_rebalance: bool
    created_at: str
    updated_at: str
    wallets: List[WalletResponse]
    positions: List[PositionResponse]


class PortfolioListResponse(BaseModel):
    portfolios: List[PortfolioResponse]
    total: int
    skip: int
    limit: int


class PortfolioPerformanceResponse(BaseModel):
    portfolio_id: int
    total_cost_basis: Decimal
    total_market_value: Decimal
    total_cash: Decimal
    portfolio_value: Decimal
    total_unrealized_pnl: Decimal
    total_realized_pnl: Decimal
    total_return: Decimal
    total_return_percentage: Decimal
    position_count: int
    wallet_count: int


class PortfolioStatsResponse(BaseModel):
    total_portfolios: int
    total_value: Decimal
    active_portfolios: int
    total_positions: int


# ==================== ENDPOINTS ====================

@router.post("/", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio_data: PortfolioCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crée un nouveau portefeuille"""
    
    portfolio_service = PortfolioService(db)
    
    try:
        portfolio = portfolio_service.create_portfolio(
            user_id=current_user.id,
            name=portfolio_data.name,
            description=portfolio_data.description,
            portfolio_type=portfolio_data.portfolio_type,
            initial_capital=portfolio_data.initial_capital,
            risk_tolerance=portfolio_data.risk_tolerance
        )
        
        # Récupérer le portefeuille avec toutes ses relations
        full_portfolio = portfolio_service.get_portfolio_by_id(portfolio.id, current_user.id)
        
        return PortfolioResponse(
            id=full_portfolio.id,
            name=full_portfolio.name,
            description=full_portfolio.description,
            portfolio_type=full_portfolio.portfolio_type.value,
            status=full_portfolio.status.value,
            initial_capital=full_portfolio.initial_capital,
            current_value=full_portfolio.current_value,
            total_invested=full_portfolio.total_invested,
            total_withdrawn=full_portfolio.total_withdrawn,
            total_return=full_portfolio.total_return,
            total_return_percentage=full_portfolio.total_return_percentage,
            risk_tolerance=full_portfolio.risk_tolerance,
            currency="EUR",  # Devise par défaut
            auto_rebalance=full_portfolio.auto_rebalance,
            created_at=full_portfolio.created_at.isoformat(),
            updated_at=full_portfolio.updated_at.isoformat(),
            wallets=[
                WalletResponse(
                    id=wallet.id,
                    name=wallet.name,
                    currency=wallet.currency,
                    wallet_type=wallet.wallet_type.value,
                    status=wallet.status.value,
                    available_balance=wallet.available_balance,
                    total_balance=wallet.total_balance,
                    created_at=wallet.created_at.isoformat()
                )
                for wallet in full_portfolio.wallets
            ],
            positions=[
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
                for position in full_portfolio.positions
            ]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du portefeuille: {str(e)}"
        )


@router.get("/", response_model=PortfolioListResponse)
async def get_portfolios(
    skip: int = Query(0, ge=0, description="Nombre de portefeuilles à ignorer"),
    limit: int = Query(100, ge=1, le=1000, description="Nombre maximum de portefeuilles à retourner"),
    portfolio_type: Optional[PortfolioType] = Query(None, description="Filtrer par type de portefeuille"),
    status: Optional[PortfolioStatus] = Query(None, description="Filtrer par statut"),
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère les portefeuilles de l'utilisateur actuel"""
    
    portfolio_service = PortfolioService(db)
    
    portfolios = portfolio_service.get_user_portfolios(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        portfolio_type=portfolio_type,
        status=status
    )
    
    return PortfolioListResponse(
        portfolios=[
            PortfolioResponse(
                id=portfolio.id,
                name=portfolio.name,
                description=portfolio.description,
                portfolio_type=portfolio.portfolio_type.value,
                status=portfolio.status.value,
                initial_capital=portfolio.initial_capital,
                current_value=portfolio.current_value,
                total_invested=portfolio.total_invested,
                total_withdrawn=portfolio.total_withdrawn,
                total_return=portfolio.total_return,
                total_return_percentage=portfolio.total_return_percentage,
                risk_tolerance=portfolio.risk_tolerance,
                currency="EUR",  # Devise par défaut
                auto_rebalance=portfolio.auto_rebalance,
                created_at=portfolio.created_at.isoformat(),
                updated_at=portfolio.updated_at.isoformat(),
                wallets=[
                    WalletResponse(
                        id=wallet.id,
                        name=wallet.name,
                        currency=wallet.currency,
                        wallet_type=wallet.wallet_type.value,
                        status=wallet.status.value,
                        available_balance=wallet.available_balance,
                        total_balance=wallet.total_balance,
                        created_at=wallet.created_at.isoformat()
                    )
                    for wallet in portfolio.wallets
                ],
                positions=[
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
                    for position in portfolio.positions
                ]
            )
            for portfolio in portfolios
        ],
        total=len(portfolios),  # Note: Pour une vraie pagination, il faudrait compter le total
        skip=skip,
        limit=limit
    )


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Récupère un portefeuille par son ID"""
    
    portfolio_service = PortfolioService(db)
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    return PortfolioResponse(
        id=portfolio.id,
        name=portfolio.name,
        description=portfolio.description,
        portfolio_type=portfolio.portfolio_type.value,
        status=portfolio.status.value,
        initial_capital=portfolio.initial_capital,
        current_value=portfolio.current_value,
        total_invested=portfolio.total_invested,
        total_withdrawn=portfolio.total_withdrawn,
        total_return=portfolio.total_return,
        total_return_percentage=portfolio.total_return_percentage,
        risk_tolerance=portfolio.risk_tolerance,
        currency="EUR",  # Devise par défaut
        auto_rebalance=portfolio.auto_rebalance,
        created_at=portfolio.created_at.isoformat(),
        updated_at=portfolio.updated_at.isoformat(),
        wallets=[
            WalletResponse(
                id=wallet.id,
                name=wallet.name,
                currency=wallet.currency,
                wallet_type=wallet.wallet_type.value,
                status=wallet.status.value,
                available_balance=wallet.available_balance,
                total_balance=wallet.total_balance,
                created_at=wallet.created_at.isoformat()
            )
            for wallet in portfolio.wallets
        ],
        positions=[
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
            for position in portfolio.positions
        ]
    )


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: int,
    portfolio_update: PortfolioUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Met à jour un portefeuille"""
    
    portfolio_service = PortfolioService(db)
    
    try:
        updated_portfolio = portfolio_service.update_portfolio(
            portfolio_id=portfolio_id,
            user_id=current_user.id,
            name=portfolio_update.name,
            description=portfolio_update.description,
            portfolio_type=portfolio_update.portfolio_type,
            risk_tolerance=portfolio_update.risk_tolerance,
            auto_rebalance=portfolio_update.auto_rebalance
        )
        
        if not updated_portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portefeuille non trouvé"
            )
        
        # Récupérer le portefeuille complet
        full_portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
        
        return PortfolioResponse(
            id=full_portfolio.id,
            name=full_portfolio.name,
            description=full_portfolio.description,
            portfolio_type=full_portfolio.portfolio_type.value,
            status=full_portfolio.status.value,
            initial_capital=full_portfolio.initial_capital,
            current_value=full_portfolio.current_value,
            total_invested=full_portfolio.total_invested,
            total_withdrawn=full_portfolio.total_withdrawn,
            total_return=full_portfolio.total_return,
            total_return_percentage=full_portfolio.total_return_percentage,
            risk_tolerance=full_portfolio.risk_tolerance,
            currency="EUR",  # Devise par défaut
            auto_rebalance=full_portfolio.auto_rebalance,
            created_at=full_portfolio.created_at.isoformat(),
            updated_at=full_portfolio.updated_at.isoformat(),
            wallets=[
                WalletResponse(
                    id=wallet.id,
                    name=wallet.name,
                    currency=wallet.currency,
                    wallet_type=wallet.wallet_type.value,
                    status=wallet.status.value,
                    available_balance=wallet.available_balance,
                    total_balance=wallet.total_balance,
                    created_at=wallet.created_at.isoformat()
                )
                for wallet in full_portfolio.wallets
            ],
            positions=[
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
                for position in full_portfolio.positions
            ]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la mise à jour: {str(e)}"
        )


@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprime un portefeuille (soft delete)"""
    
    portfolio_service = PortfolioService(db)
    success = portfolio_service.delete_portfolio(portfolio_id, current_user.id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    return {"message": "Portefeuille supprimé avec succès"}


@router.post("/{portfolio_id}/wallets", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    portfolio_id: int,
    wallet_data: WalletCreate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crée un nouveau wallet dans un portefeuille"""
    
    portfolio_service = PortfolioService(db)
    
    try:
        wallet = portfolio_service.create_wallet(
            portfolio_id=portfolio_id,
            name=wallet_data.name,
            currency=wallet_data.currency,
            initial_balance=wallet_data.initial_balance
        )
        
        return WalletResponse(
            id=wallet.id,
            name=wallet.name,
            currency=wallet.currency,
            wallet_type=wallet.wallet_type.value,
            status=wallet.status.value,
            available_balance=wallet.available_balance,
            total_balance=wallet.total_balance,
            created_at=wallet.created_at.isoformat()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du wallet: {str(e)}"
        )


@router.get("/{portfolio_id}/performance", response_model=PortfolioPerformanceResponse)
async def get_portfolio_performance(
    portfolio_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Calcule et retourne la performance d'un portefeuille"""
    
    portfolio_service = PortfolioService(db)
    
    # Vérifier que le portefeuille appartient à l'utilisateur
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    performance = portfolio_service.calculate_portfolio_performance(portfolio_id)
    
    return PortfolioPerformanceResponse(**performance)


@router.post("/{portfolio_id}/performance/update")
async def update_portfolio_performance(
    portfolio_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Met à jour les métriques de performance d'un portefeuille"""
    
    portfolio_service = PortfolioService(db)
    
    # Vérifier que le portefeuille appartient à l'utilisateur
    portfolio = portfolio_service.get_portfolio_by_id(portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portefeuille non trouvé"
        )
    
    success = portfolio_service.update_portfolio_performance(portfolio_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la mise à jour de la performance"
        )
    
    return {"message": "Performance mise à jour avec succès"}


@router.get("/stats/overview", response_model=PortfolioStatsResponse)
async def get_portfolio_stats(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retourne les statistiques des portefeuilles de l'utilisateur"""
    
    portfolio_service = PortfolioService(db)
    stats = portfolio_service.get_portfolio_stats(current_user.id)
    
    return PortfolioStatsResponse(**stats)
