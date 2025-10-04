"""
Service de gestion des positions de titres
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status

from app.models.portfolios import (
    Position, PositionTransaction, PositionType,
    Portfolio, Wallet
)
from app.services.authentication_service import AuthenticationService


class PositionService:
    """Service de gestion des positions de titres"""
    
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthenticationService(db)
    
    # ==================== GESTION DES TRANSACTIONS DE POSITIONS ====================
    
    def execute_buy_order(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal = Decimal('0.00'),
        currency: str = "USD"
    ) -> Tuple[Position, PositionTransaction]:
        """Exécute un ordre d'achat"""
        
        # Vérifier que le portefeuille existe
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == portfolio_id
        ).first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portefeuille non trouvé"
            )
        
        # Vérifier qu'il y a assez de liquidités
        total_cost = (quantity * price) + fee
        wallet = self._get_or_create_wallet(portfolio_id, currency)
        
        if wallet.available_balance < total_cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fonds insuffisants. Coût: {total_cost}, Disponible: {wallet.available_balance}"
            )
        
        # Vérifier si une position existe déjà
        existing_position = self.db.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.symbol == symbol
        ).first()
        
        if existing_position:
            # Ajouter à la position existante
            self._add_to_position(existing_position, quantity, price)
            position = existing_position
        else:
            # Créer une nouvelle position
            position = self._create_new_position(
                portfolio_id, symbol, quantity, price, currency
            )
        
        # Créer la transaction
        transaction = self._create_position_transaction(
            position.id, "BUY", quantity, price, fee
        )
        
        # Débiter le wallet
        wallet.available_balance -= total_cost
        wallet.total_balance -= total_cost
        wallet.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return position, transaction
    
    def execute_sell_order(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal = Decimal('0.00'),
        currency: str = "USD"
    ) -> Tuple[Position, PositionTransaction]:
        """Exécute un ordre de vente"""
        
        # Vérifier que le portefeuille existe
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == portfolio_id
        ).first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portefeuille non trouvé"
            )
        
        # Vérifier que la position existe
        position = self.db.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.symbol == symbol
        ).first()
        
        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Position {symbol} non trouvée"
            )
        
        if position.quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quantité insuffisante. Disponible: {position.quantity}, Demandée: {quantity}"
            )
        
        # Réduire la position
        realized_pnl = self._reduce_position(position, quantity, price)
        
        # Créer la transaction
        transaction = self._create_position_transaction(
            position.id, "SELL", quantity, price, fee
        )
        
        # Créditer le wallet
        net_proceeds = (quantity * price) - fee
        wallet = self._get_or_create_wallet(portfolio_id, currency)
        wallet.available_balance += net_proceeds
        wallet.total_balance += net_proceeds
        wallet.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return position, transaction
    
    def _get_or_create_wallet(self, portfolio_id: int, currency: str) -> Wallet:
        """Récupère ou crée un wallet pour une devise"""
        
        wallet = self.db.query(Wallet).filter(
            Wallet.portfolio_id == portfolio_id,
            Wallet.currency == currency
        ).first()
        
        if not wallet:
            # Créer un nouveau wallet
            wallet = Wallet(
                portfolio_id=portfolio_id,
                name=f"Wallet {currency}",
                currency=currency,
                available_balance=Decimal('0.00'),
                total_balance=Decimal('0.00')
            )
            self.db.add(wallet)
            self.db.flush()  # Pour obtenir l'ID
        
        return wallet
    
    def _create_new_position(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        currency: str
    ) -> Position:
        """Crée une nouvelle position"""
        
        cost_basis = quantity * price
        
        position = Position(
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=quantity,
            average_buy_price=price,
            current_price=price,
            cost_basis=cost_basis,
            market_value=cost_basis,
            unrealized_pnl=Decimal('0.00'),
            unrealized_pnl_percent=Decimal('0.00'),
            currency=currency,
            position_type=PositionType.LONG
        )
        
        self.db.add(position)
        self.db.flush()  # Pour obtenir l'ID
        
        return position
    
    def _add_to_position(self, position: Position, quantity: Decimal, price: Decimal) -> None:
        """Ajoute des titres à une position existante"""
        
        # Calculer la nouvelle moyenne pondérée
        total_cost = (position.quantity * position.average_buy_price) + (
            quantity * price
        )
        total_quantity = position.quantity + quantity
        
        # Mettre à jour la position
        position.quantity = total_quantity
        position.average_buy_price = total_cost / total_quantity
        position.cost_basis = total_cost
        position.current_price = price
        position.market_value = total_quantity * price
        position.unrealized_pnl = position.market_value - position.cost_basis
        
        if position.cost_basis > 0:
            position.unrealized_pnl_percent = (
                position.unrealized_pnl / position.cost_basis
            ) * 100
        
        position.updated_at = datetime.utcnow()
    
    def _reduce_position(self, position: Position, quantity: Decimal, price: Decimal) -> Decimal:
        """Réduit une position et calcule le P&L réalisé"""
        
        # Calculer le P&L réalisé
        realized_pnl = (price - position.average_buy_price) * quantity
        
        # Mettre à jour la position
        position.quantity -= quantity
        position.cost_basis -= (position.average_buy_price * quantity)
        position.current_price = price
        position.market_value = position.quantity * price
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
        
        return realized_pnl
    
    def _create_position_transaction(
        self,
        position_id: int,
        transaction_type: str,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal
    ) -> PositionTransaction:
        """Crée une transaction de position"""
        
        transaction = PositionTransaction(
            position_id=position_id,
            transaction_type=transaction_type,
            quantity=quantity,
            price=price,
            fee=fee,
            transaction_date=datetime.utcnow()
        )
        
        self.db.add(transaction)
        self.db.flush()  # Pour obtenir l'ID
        
        return transaction
    
    # ==================== GESTION DES POSITIONS ====================
    
    def get_position_by_id(self, position_id: int) -> Optional[Position]:
        """Récupère une position par son ID"""
        
        return self.db.query(Position).options(
            joinedload(Position.portfolio)
        ).filter(Position.id == position_id).first()
    
    def get_position_by_symbol(self, portfolio_id: int, symbol: str) -> Optional[Position]:
        """Récupère une position par symbole dans un portefeuille"""
        
        return self.db.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.symbol == symbol
        ).first()
    
    def get_portfolio_positions(
        self,
        portfolio_id: int,
        skip: int = 0,
        limit: int = 100,
        symbol_filter: Optional[str] = None,
        min_quantity: Optional[Decimal] = None
    ) -> List[Position]:
        """Récupère toutes les positions d'un portefeuille avec filtres"""
        
        query = self.db.query(Position).filter(
            Position.portfolio_id == portfolio_id
        )
        
        if symbol_filter:
            query = query.filter(Position.symbol.ilike(f"%{symbol_filter}%"))
        
        if min_quantity is not None:
            query = query.filter(Position.quantity >= min_quantity)
        
        return query.offset(skip).limit(limit).all()
    
    def update_position_prices(self, portfolio_id: int, price_updates: Dict[str, Decimal]) -> int:
        """Met à jour les prix de plusieurs positions"""
        
        updated_count = 0
        
        for symbol, new_price in price_updates.items():
            position = self.get_position_by_symbol(portfolio_id, symbol)
            if position:
                # Mettre à jour le prix et recalculer les valeurs
                position.current_price = new_price
                position.market_value = position.quantity * new_price
                position.unrealized_pnl = position.market_value - position.cost_basis
                
                if position.cost_basis > 0:
                    position.unrealized_pnl_percent = (
                        position.unrealized_pnl / position.cost_basis
                    ) * 100
                
                position.updated_at = datetime.utcnow()
                updated_count += 1
        
        self.db.commit()
        return updated_count
    
    def close_position(self, position_id: int, sell_price: Decimal) -> Tuple[bool, Optional[Decimal]]:
        """Ferme complètement une position"""
        
        position = self.get_position_by_id(position_id)
        if not position:
            return False, None
        
        if position.quantity <= 0:
            return False, None
        
        # Calculer le P&L total
        total_realized_pnl = (sell_price - position.average_buy_price) * position.quantity
        
        # Créer la transaction de vente
        transaction = self._create_position_transaction(
            position_id, "SELL", position.quantity, sell_price, Decimal('0.00')
        )
        
        # Mettre à jour la position
        position.quantity = Decimal('0.00')
        position.current_price = sell_price
        position.market_value = Decimal('0.00')
        position.unrealized_pnl = Decimal('0.00')
        position.unrealized_pnl_percent = Decimal('0.00')
        position.realized_pnl += total_realized_pnl
        position.updated_at = datetime.utcnow()
        
        # Créditer le wallet
        net_proceeds = position.quantity * sell_price
        wallet = self._get_or_create_wallet(position.portfolio_id, position.currency)
        wallet.available_balance += net_proceeds
        wallet.total_balance += net_proceeds
        wallet.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return True, total_realized_pnl
    
    # ==================== GESTION DES TRANSACTIONS ====================
    
    def get_position_transactions(
        self,
        position_id: int,
        skip: int = 0,
        limit: int = 100,
        transaction_type: Optional[str] = None
    ) -> List[PositionTransaction]:
        """Récupère les transactions d'une position"""
        
        query = self.db.query(PositionTransaction).filter(
            PositionTransaction.position_id == position_id
        )
        
        if transaction_type:
            query = query.filter(PositionTransaction.transaction_type == transaction_type)
        
        return query.order_by(
            desc(PositionTransaction.transaction_date)
        ).offset(skip).limit(limit).all()
    
    def get_portfolio_transactions(
        self,
        portfolio_id: int,
        skip: int = 0,
        limit: int = 100,
        symbol_filter: Optional[str] = None,
        transaction_type: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[PositionTransaction]:
        """Récupère toutes les transactions d'un portefeuille"""
        
        query = self.db.query(PositionTransaction).join(Position).filter(
            Position.portfolio_id == portfolio_id
        )
        
        if symbol_filter:
            query = query.filter(Position.symbol.ilike(f"%{symbol_filter}%"))
        
        if transaction_type:
            query = query.filter(PositionTransaction.transaction_type == transaction_type)
        
        if date_from:
            query = query.filter(PositionTransaction.transaction_date >= date_from)
        
        if date_to:
            query = query.filter(PositionTransaction.transaction_date <= date_to)
        
        return query.order_by(
            desc(PositionTransaction.transaction_date)
        ).offset(skip).limit(limit).all()
    
    # ==================== ANALYSE ET RAPPORTS ====================
    
    def calculate_position_performance(self, position_id: int) -> Dict[str, Any]:
        """Calcule la performance d'une position"""
        
        position = self.get_position_by_id(position_id)
        if not position:
            return {}
        
        # Calculer les métriques de base
        current_value = position.quantity * position.current_price
        unrealized_pnl = current_value - position.cost_basis
        unrealized_pnl_percent = 0
        
        if position.cost_basis > 0:
            unrealized_pnl_percent = (unrealized_pnl / position.cost_basis) * 100
        
        # Calculer le rendement total (réalisé + non réalisé)
        total_pnl = position.realized_pnl + unrealized_pnl
        total_return_percent = 0
        
        if position.cost_basis > 0:
            total_return_percent = (total_pnl / position.cost_basis) * 100
        
        return {
            "position_id": position_id,
            "symbol": position.symbol,
            "quantity": position.quantity,
            "average_buy_price": position.average_buy_price,
            "current_price": position.current_price,
            "cost_basis": position.cost_basis,
            "current_value": current_value,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_percent": unrealized_pnl_percent,
            "realized_pnl": position.realized_pnl,
            "total_pnl": total_pnl,
            "total_return_percent": total_return_percent
        }
    
    def get_portfolio_summary(self, portfolio_id: int) -> Dict[str, Any]:
        """Retourne un résumé des positions d'un portefeuille"""
        
        positions = self.get_portfolio_positions(portfolio_id)
        
        if not positions:
            return {
                "total_positions": 0,
                "total_value": Decimal('0.00'),
                "total_cost_basis": Decimal('0.00'),
                "total_pnl": Decimal('0.00'),
                "winning_positions": 0,
                "losing_positions": 0
            }
        
        total_value = sum(pos.market_value for pos in positions)
        total_cost_basis = sum(pos.cost_basis for pos in positions)
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
        total_realized_pnl = sum(pos.realized_pnl for pos in positions)
        total_pnl = total_unrealized_pnl + total_realized_pnl
        
        winning_positions = len([pos for pos in positions if pos.unrealized_pnl > 0])
        losing_positions = len([pos for pos in positions if pos.unrealized_pnl < 0])
        
        return {
            "total_positions": len(positions),
            "total_value": total_value,
            "total_cost_basis": total_cost_basis,
            "total_unrealized_pnl": total_unrealized_pnl,
            "total_realized_pnl": total_realized_pnl,
            "total_pnl": total_pnl,
            "winning_positions": winning_positions,
            "losing_positions": losing_positions,
            "neutral_positions": len(positions) - winning_positions - losing_positions
        }
    
    def get_top_positions(self, portfolio_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Retourne les meilleures positions d'un portefeuille"""
        
        positions = self.get_portfolio_positions(portfolio_id)
        
        # Trier par P&L non réalisé
        sorted_positions = sorted(
            positions,
            key=lambda x: x.unrealized_pnl,
            reverse=True
        )
        
        return [
            self.calculate_position_performance(pos.id)
            for pos in sorted_positions[:limit]
        ]
    
    def get_worst_positions(self, portfolio_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Retourne les pires positions d'un portefeuille"""
        
        positions = self.get_portfolio_positions(portfolio_id)
        
        # Trier par P&L non réalisé (croissant)
        sorted_positions = sorted(
            positions,
            key=lambda x: x.unrealized_pnl
        )
        
        return [
            self.calculate_position_performance(pos.id)
            for pos in sorted_positions[:limit]
        ]
