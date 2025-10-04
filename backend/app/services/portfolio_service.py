"""
Service de gestion des portefeuilles
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status

from app.models.portfolios import (
    Portfolio, PortfolioType, PortfolioStatus, 
    Wallet, WalletType, WalletStatus,
    Position, PositionTransaction, PositionType,
    PortfolioTransaction, TransactionType,
    PortfolioPerformance
)
from app.models.users import User
from app.services.authentication_service import AuthenticationService


class PortfolioService:
    """Service de gestion des portefeuilles"""
    
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthenticationService(db)
    
    # ==================== GESTION DES PORTEFEUILLES ====================
    
    def create_portfolio(
        self,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        portfolio_type: PortfolioType = PortfolioType.PERSONAL,
        initial_capital: Decimal = Decimal('0.00'),
        risk_tolerance: str = "MODERATE",
        currency: str = "USD"
    ) -> Portfolio:
        """Crée un nouveau portefeuille"""
        
        # Vérifier que l'utilisateur existe
        user = self.auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé"
            )
        
        # Créer le portefeuille
        portfolio = Portfolio(
            user_id=user_id,
            name=name,
            description=description,
            portfolio_type=portfolio_type,
            initial_capital=initial_capital,
            current_value=initial_capital,
            risk_tolerance=risk_tolerance,
            currency=currency,
            status=PortfolioStatus.ACTIVE
        )
        
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        
        # Créer un wallet par défaut dans la devise principale
        self.create_wallet(
            portfolio_id=portfolio.id,
            name=f"Wallet {currency}",
            currency=currency,
            initial_balance=initial_capital
        )
        
        return portfolio
    
    def get_portfolio_by_id(self, portfolio_id: int, user_id: Optional[int] = None) -> Optional[Portfolio]:
        """Récupère un portefeuille par son ID"""
        
        query = self.db.query(Portfolio).options(
            joinedload(Portfolio.wallets),
            joinedload(Portfolio.positions),
            joinedload(Portfolio.owner)
        )
        
        if user_id:
            query = query.filter(Portfolio.user_id == user_id)
        
        return query.filter(Portfolio.id == portfolio_id).first()
    
    def get_user_portfolios(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        portfolio_type: Optional[PortfolioType] = None,
        status: Optional[PortfolioStatus] = None
    ) -> List[Portfolio]:
        """Récupère tous les portefeuilles d'un utilisateur"""
        
        query = self.db.query(Portfolio).options(
            joinedload(Portfolio.wallets),
            joinedload(Portfolio.positions)
        ).filter(Portfolio.user_id == user_id)
        
        if portfolio_type:
            query = query.filter(Portfolio.portfolio_type == portfolio_type)
        
        if status:
            query = query.filter(Portfolio.status == status)
        
        return query.offset(skip).limit(limit).all()
    
    def update_portfolio(
        self,
        portfolio_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        portfolio_type: Optional[PortfolioType] = None,
        risk_tolerance: Optional[str] = None,
        auto_rebalance: Optional[bool] = None
    ) -> Optional[Portfolio]:
        """Met à jour un portefeuille"""
        
        portfolio = self.get_portfolio_by_id(portfolio_id, user_id)
        if not portfolio:
            return None
        
        if name is not None:
            portfolio.name = name
        
        if description is not None:
            portfolio.description = description
        
        if portfolio_type is not None:
            portfolio.portfolio_type = portfolio_type
        
        if risk_tolerance is not None:
            portfolio.risk_tolerance = risk_tolerance
        
        if auto_rebalance is not None:
            portfolio.auto_rebalance = auto_rebalance
        
        portfolio.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(portfolio)
        
        return portfolio
    
    def delete_portfolio(self, portfolio_id: int, user_id: int) -> bool:
        """Supprime un portefeuille (soft delete)"""
        
        portfolio = self.get_portfolio_by_id(portfolio_id, user_id)
        if not portfolio:
            return False
        
        portfolio.status = PortfolioStatus.CLOSED
        portfolio.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    # ==================== GESTION DES WALLETS ====================
    
    def create_wallet(
        self,
        portfolio_id: int,
        name: str,
        currency: str,
        initial_balance: Decimal = Decimal('0.00'),
        wallet_type: WalletType = WalletType.CASH
    ) -> Wallet:
        """Crée un nouveau wallet dans un portefeuille"""
        
        # Vérifier que le portefeuille existe
        portfolio = self.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portefeuille non trouvé"
            )
        
        # Vérifier qu'un wallet dans cette devise n'existe pas déjà
        existing_wallet = self.get_wallet_by_currency(portfolio_id, currency)
        if existing_wallet:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Un wallet en {currency} existe déjà dans ce portefeuille"
            )
        
        # Créer le wallet
        wallet = Wallet(
            portfolio_id=portfolio_id,
            name=name,
            currency=currency,
            wallet_type=wallet_type,
            available_balance=initial_balance,
            total_balance=initial_balance,
            status=WalletStatus.ACTIVE
        )
        
        self.db.add(wallet)
        self.db.commit()
        self.db.refresh(wallet)
        
        return wallet
    
    def get_wallet_by_id(self, wallet_id: int, portfolio_id: Optional[int] = None) -> Optional[Wallet]:
        """Récupère un wallet par son ID"""
        
        query = self.db.query(Wallet)
        
        if portfolio_id:
            query = query.filter(Wallet.portfolio_id == portfolio_id)
        
        return query.filter(Wallet.id == wallet_id).first()
    
    def get_wallet_by_currency(self, portfolio_id: int, currency: str) -> Optional[Wallet]:
        """Récupère un wallet par devise dans un portefeuille"""
        
        return self.db.query(Wallet).filter(
            Wallet.portfolio_id == portfolio_id,
            Wallet.currency == currency
        ).first()
    
    def get_portfolio_wallets(self, portfolio_id: int) -> List[Wallet]:
        """Récupère tous les wallets d'un portefeuille"""
        
        return self.db.query(Wallet).filter(
            Wallet.portfolio_id == portfolio_id
        ).all()
    
    def update_wallet_balance(
        self,
        wallet_id: int,
        amount: Decimal,
        transaction_type: str = "DEPOSIT"
    ) -> bool:
        """Met à jour le solde d'un wallet"""
        
        wallet = self.get_wallet_by_id(wallet_id)
        if not wallet:
            return False
        
        if transaction_type == "DEPOSIT":
            wallet.available_balance += amount
            wallet.total_balance += amount
        elif transaction_type == "WITHDRAWAL":
            if wallet.available_balance >= amount:
                wallet.available_balance -= amount
                wallet.total_balance -= amount
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Solde insuffisant"
                )
        
        wallet.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    # ==================== GESTION DES POSITIONS ====================
    
    def create_position(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: Decimal,
        average_buy_price: Decimal,
        currency: str = "USD"
    ) -> Position:
        """Crée une nouvelle position"""
        
        # Vérifier que le portefeuille existe
        portfolio = self.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portefeuille non trouvé"
            )
        
        # Calculer les valeurs initiales
        cost_basis = quantity * average_buy_price
        market_value = cost_basis  # Prix initial
        
        # Créer la position
        position = Position(
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=quantity,
            average_buy_price=average_buy_price,
            current_price=average_buy_price,
            cost_basis=cost_basis,
            market_value=market_value,
            unrealized_pnl=Decimal('0.00'),
            unrealized_pnl_percent=Decimal('0.00'),
            currency=currency,
            position_type=PositionType.LONG
        )
        
        self.db.add(position)
        self.db.commit()
        self.db.refresh(position)
        
        return position
    
    def get_position_by_id(self, position_id: int, portfolio_id: Optional[int] = None) -> Optional[Position]:
        """Récupère une position par son ID"""
        
        query = self.db.query(Position)
        
        if portfolio_id:
            query = query.filter(Position.portfolio_id == portfolio_id)
        
        return query.filter(Position.id == position_id).first()
    
    def get_portfolio_positions(self, portfolio_id: int) -> List[Position]:
        """Récupère toutes les positions d'un portefeuille"""
        
        return self.db.query(Position).filter(
            Position.portfolio_id == portfolio_id
        ).all()
    
    def update_position_price(self, position_id: int, new_price: Decimal) -> bool:
        """Met à jour le prix d'une position"""
        
        position = self.get_position_by_id(position_id)
        if not position:
            return False
        
        # Mettre à jour le prix et recalculer les valeurs
        position.current_price = new_price
        position.market_value = position.quantity * new_price
        position.unrealized_pnl = position.market_value - position.cost_basis
        
        if position.cost_basis > 0:
            position.unrealized_pnl_percent = (
                position.unrealized_pnl / position.cost_basis
            ) * 100
        
        position.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def add_to_position(
        self,
        position_id: int,
        additional_quantity: Decimal,
        purchase_price: Decimal
    ) -> bool:
        """Ajoute des titres à une position existante"""
        
        position = self.get_position_by_id(position_id)
        if not position:
            return False
        
        # Calculer la nouvelle moyenne pondérée
        total_cost = (position.quantity * position.average_buy_price) + (
            additional_quantity * purchase_price
        )
        total_quantity = position.quantity + additional_quantity
        
        # Mettre à jour la position
        position.quantity = total_quantity
        position.average_buy_price = total_cost / total_quantity
        position.cost_basis = total_cost
        position.current_price = purchase_price
        position.market_value = total_quantity * purchase_price
        position.unrealized_pnl = position.market_value - position.cost_basis
        
        if position.cost_basis > 0:
            position.unrealized_pnl_percent = (
                position.unrealized_pnl / position.cost_basis
            ) * 100
        
        position.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def reduce_position(
        self,
        position_id: int,
        sell_quantity: Decimal,
        sell_price: Decimal
    ) -> Tuple[bool, Optional[Decimal]]:
        """Réduit une position et calcule le P&L réalisé"""
        
        position = self.get_position_by_id(position_id)
        if not position:
            return False, None
        
        if position.quantity < sell_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Quantité à vendre supérieure à la position"
            )
        
        # Calculer le P&L réalisé
        realized_pnl = (sell_price - position.average_buy_price) * sell_quantity
        
        # Mettre à jour la position
        position.quantity -= sell_quantity
        position.cost_basis -= (position.average_buy_price * sell_quantity)
        position.current_price = sell_price
        position.market_value = position.quantity * sell_price
        position.realized_pnl += realized_pnl
        
        # Recalculer le P&L non réalisé
        if position.quantity > 0:
            position.unrealized_pnl = position.market_value - position.cost_basis
            if position.cost_basis > 0:
                position.unrealized_pnl_percent = (
                    position.unrealized_pnl / position.cost_basis
                ) * 100
        else:
            # Position fermée
            position.unrealized_pnl = Decimal('0.00')
            position.unrealized_pnl_percent = Decimal('0.00')
        
        position.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True, realized_pnl
    
    # ==================== CALCULS DE PERFORMANCE ====================
    
    def calculate_portfolio_performance(self, portfolio_id: int) -> Dict[str, Any]:
        """Calcule la performance d'un portefeuille"""
        
        portfolio = self.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return {}
        
        # Récupérer toutes les positions
        positions = self.get_portfolio_positions(portfolio_id)
        
        # Calculer les totaux
        total_cost_basis = sum(pos.cost_basis for pos in positions)
        total_market_value = sum(pos.market_value for pos in positions)
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
        total_realized_pnl = sum(pos.realized_pnl for pos in positions)
        
        # Calculer les rendements
        total_return = total_unrealized_pnl + total_realized_pnl
        total_return_percentage = 0
        
        if total_cost_basis > 0:
            total_return_percentage = (total_return / total_cost_basis) * 100
        
        # Calculer la valeur totale du portefeuille (positions + cash)
        wallets = self.get_portfolio_wallets(portfolio_id)
        total_cash = sum(wallet.total_balance for wallet in wallets)
        
        portfolio_value = total_market_value + total_cash
        
        return {
            "portfolio_id": portfolio_id,
            "total_cost_basis": total_cost_basis,
            "total_market_value": total_market_value,
            "total_cash": total_cash,
            "portfolio_value": portfolio_value,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_realized_pnl": total_realized_pnl,
            "total_return": total_return,
            "total_return_percentage": total_return_percentage,
            "position_count": len(positions),
            "wallet_count": len(wallets)
        }
    
    def update_portfolio_performance(self, portfolio_id: int) -> bool:
        """Met à jour les métriques de performance d'un portefeuille"""
        
        portfolio = self.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return False
        
        performance = self.calculate_portfolio_performance(portfolio_id)
        
        # Mettre à jour le portefeuille
        portfolio.current_value = performance["portfolio_value"]
        portfolio.total_return = performance["total_return"]
        portfolio.total_return_percentage = performance["total_return_percentage"]
        portfolio.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def record_portfolio_performance(self, portfolio_id: int, date: datetime = None) -> bool:
        """Enregistre un snapshot de performance"""
        
        if date is None:
            date = datetime.utcnow()
        
        performance = self.calculate_portfolio_performance(portfolio_id)
        
        # Créer l'enregistrement de performance
        perf_record = PortfolioPerformance(
            portfolio_id=portfolio_id,
            date=date.date(),
            total_value=performance["portfolio_value"],
            cash_value=performance["total_cash"],
            invested_value=performance["total_market_value"],
            daily_return=Decimal('0.00'),  # À calculer avec les données précédentes
            cumulative_return=performance["total_return_percentage"],
            sharpe_ratio=None,  # À calculer avec plus de données
            max_drawdown=None,  # À calculer avec plus de données
            volatility=None  # À calculer avec plus de données
        )
        
        self.db.add(perf_record)
        self.db.commit()
        return True
    
    # ==================== STATISTIQUES ====================
    
    def get_portfolio_stats(self, user_id: int) -> Dict[str, Any]:
        """Retourne les statistiques des portefeuilles d'un utilisateur"""
        
        portfolios = self.get_user_portfolios(user_id)
        
        if not portfolios:
            return {
                "total_portfolios": 0,
                "total_value": Decimal('0.00'),
                "active_portfolios": 0,
                "total_positions": 0
            }
        
        total_value = sum(p.current_value for p in portfolios)
        active_portfolios = len([p for p in portfolios if p.status == PortfolioStatus.ACTIVE])
        total_positions = sum(
            len(self.get_portfolio_positions(p.id)) for p in portfolios
        )
        
        return {
            "total_portfolios": len(portfolios),
            "total_value": total_value,
            "active_portfolios": active_portfolios,
            "total_positions": total_positions
        }
