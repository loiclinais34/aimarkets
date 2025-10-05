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
    Position, PositionTransaction, PortfolioTransaction,
    Portfolio
)
from app.models.wallets import Wallet
from app.services.authentication_service import AuthenticationService
from app.services.exchange_rate_service import ExchangeRateService


class PositionService:
    """Service de gestion des positions de titres"""
    
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthenticationService(db)
        self.exchange_service = ExchangeRateService(db)
    
    # ==================== GESTION DES TRANSACTIONS DE POSITIONS ====================
    
    def execute_buy_order(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal = Decimal('0.00'),
        currency: str = "USD",
        wallet_id: int = None
    ) -> Tuple[Position, PortfolioTransaction]:
        """Exécute un ordre d'achat - crée d'abord une transaction, puis met à jour la position"""
        
        # Vérifier que le portefeuille existe
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == portfolio_id
        ).first()
        
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portefeuille non trouvé"
            )
        
        # Vérifier que le wallet existe et a suffisamment de fonds
        if wallet_id:
            from app.models.wallets import WalletStatus
            wallet = self.db.query(Wallet).filter(
                Wallet.id == wallet_id,
                Wallet.portfolio_id == portfolio_id,
                Wallet.status == WalletStatus.ACTIVE
            ).first()
            
            if not wallet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Wallet non trouvé ou inactif"
                )
        else:
            # Si aucun wallet spécifique n'est fourni, utiliser le wallet par défaut pour la devise
            wallet = self._get_or_create_wallet(portfolio_id, currency)
            wallet_id = wallet.id
        
        # Calculer le coût total
        total_cost = (quantity * price) + fee
        
        # Convertir le coût total vers la devise du wallet si nécessaire
        if currency != wallet.currency:
            converted_cost = self.exchange_service.convert_amount(
                total_cost, currency, wallet.currency
            )
            if not converted_cost:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Impossible de convertir {currency} vers {wallet.currency}"
                )
            total_cost = converted_cost
        
        # Vérifier les fonds disponibles
        if wallet.available_balance < total_cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fonds insuffisants. Solde: {wallet.available_balance} {wallet.currency}, "
                       f"Nécessaire: {total_cost} {wallet.currency}"
            )
        
        # 1. Créer la transaction de portefeuille
        portfolio_transaction = self._create_portfolio_transaction(
            portfolio_id=portfolio_id,
            transaction_type="buy",
            symbol=symbol,
            quantity=quantity,
            price=price,
            fee=fee,
            currency=currency
        )
        
        # 2. Mettre à jour ou créer la position
        position = self._update_position_from_transaction(
            portfolio_id=portfolio_id,
            symbol=symbol,
            transaction_type="buy",
            quantity=quantity,
            price=price,
            fee=fee,
            currency=currency,
            portfolio_transaction_id=portfolio_transaction.id
        )
        
        # 3. Débiter le wallet
        wallet.available_balance -= total_cost
        wallet.total_balance -= total_cost
        wallet.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return position, portfolio_transaction
    
    def execute_sell_order(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal = Decimal('0.00'),
        currency: str = "USD",
        wallet_id: int = None
    ) -> Tuple[Position, PortfolioTransaction]:
        """Exécute un ordre de vente - crée d'abord une transaction, puis met à jour la position"""
        
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
            Position.symbol == symbol,
            Position.currency == currency
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
        
        # Récupérer le wallet
        if wallet_id:
            from app.models.wallets import WalletStatus
            wallet = self.db.query(Wallet).filter(
                Wallet.id == wallet_id,
                Wallet.portfolio_id == portfolio_id,
                Wallet.status == WalletStatus.ACTIVE
            ).first()
        else:
            wallet = self._get_or_create_wallet(portfolio_id, currency)
            wallet_id = wallet.id
        
        # 1. Créer la transaction de portefeuille
        portfolio_transaction = self._create_portfolio_transaction(
            portfolio_id=portfolio_id,
            transaction_type="sell",
            symbol=symbol,
            quantity=quantity,
            price=price,
            fee=fee,
            currency=currency
        )
        
        # 2. Mettre à jour la position
        position = self._update_position_from_transaction(
            portfolio_id=portfolio_id,
            symbol=symbol,
            transaction_type="sell",
            quantity=quantity,
            price=price,
            fee=fee,
            currency=currency,
            portfolio_transaction_id=portfolio_transaction.id
        )
        
        # 3. Calculer le produit net et créditer le wallet
        net_proceeds = (quantity * price) - fee
        
        # Convertir vers la devise du wallet si nécessaire
        if currency != wallet.currency:
            converted_proceeds = self.exchange_service.convert_amount(
                net_proceeds, currency, wallet.currency
            )
            if not converted_proceeds:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Impossible de convertir {currency} vers {wallet.currency}"
                )
            net_proceeds = converted_proceeds
        
        wallet.available_balance += net_proceeds
        wallet.total_balance += net_proceeds
        wallet.updated_at = datetime.utcnow()
        
        self.db.commit()
        
        return position, portfolio_transaction
    
    def _create_portfolio_transaction(
        self,
        portfolio_id: int,
        transaction_type: str,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal,
        currency: str
    ) -> PortfolioTransaction:
        """Crée une transaction de portefeuille"""
        
        total_amount = (quantity * price) + fee
        
        transaction = PortfolioTransaction(
            portfolio_id=portfolio_id,
            transaction_type=transaction_type,
            symbol=symbol,
            quantity=quantity,
            price=price,
            total_amount=total_amount,
            fees=fee,
            transaction_date=datetime.utcnow()
        )
        
        self.db.add(transaction)
        self.db.flush()  # Pour obtenir l'ID
        
        return transaction
    
    def _update_position_from_transaction(
        self,
        portfolio_id: int,
        symbol: str,
        transaction_type: str,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal,
        currency: str,
        portfolio_transaction_id: int
    ) -> Position:
        """Met à jour une position basée sur une transaction"""
        
        # Chercher la position existante
        position = self.db.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.symbol == symbol,
            Position.currency == currency
        ).first()
        
        if transaction_type == "buy":
            if position:
                # Ajouter à la position existante
                old_quantity = position.quantity
                old_total_cost = position.total_cost
                
                new_quantity = old_quantity + quantity
                new_total_cost = old_total_cost + (quantity * price) + fee
                new_average_cost = new_total_cost / new_quantity
                
                position.quantity = new_quantity
                position.average_cost = new_average_cost
                position.total_cost = new_total_cost
                position.updated_at = datetime.utcnow()
                
                # Créer une transaction de position
                self._create_position_transaction(
                    position.id, "buy", quantity, price, fee, currency,
                    old_quantity, new_quantity, position.average_cost, new_average_cost,
                    portfolio_transaction_id
                )
            else:
                # Créer une nouvelle position
                total_cost = (quantity * price) + fee
                
                position = Position(
                    portfolio_id=portfolio_id,
                    symbol=symbol,
                    quantity=quantity,
                    average_cost=price + (fee / quantity),
                    current_price=price,
                    total_cost=total_cost,
                    current_value=quantity * price,
                    unrealized_pnl=quantity * price - total_cost,
                    unrealized_pnl_percentage=((quantity * price - total_cost) / total_cost) * 100 if total_cost > 0 else 0,
                    realized_pnl=Decimal('0.00'),
                    currency=currency,
                    position_type="LONG"
                )
                
                self.db.add(position)
                self.db.flush()
                
                # Créer une transaction de position
                self._create_position_transaction(
                    position.id, "buy", quantity, price, fee, currency,
                    Decimal('0.00'), quantity, Decimal('0.00'), position.average_cost,
                    portfolio_transaction_id
                )
        
        elif transaction_type == "sell":
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
            
            # Calculer le P&L réalisé
            realized_pnl = (price - position.average_cost) * quantity - fee
            
            old_quantity = position.quantity
            old_average_cost = position.average_cost
            
            new_quantity = old_quantity - quantity
            new_total_cost = position.total_cost - (position.average_cost * quantity)
            
            if new_quantity > 0:
                new_average_cost = new_total_cost / new_quantity
            else:
                new_average_cost = Decimal('0.00')
            
            position.quantity = new_quantity
            position.average_cost = new_average_cost
            position.total_cost = new_total_cost
            position.realized_pnl += realized_pnl
            position.updated_at = datetime.utcnow()
            
            # Créer une transaction de position
            self._create_position_transaction(
                position.id, "sell", quantity, price, fee, currency,
                old_quantity, new_quantity, old_average_cost, new_average_cost,
                portfolio_transaction_id
            )
        
        return position
    
    def _create_position_transaction(
        self,
        position_id: int,
        transaction_type: str,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal,
        currency: str,
        quantity_before: Decimal,
        quantity_after: Decimal,
        average_cost_before: Decimal,
        average_cost_after: Decimal,
        portfolio_transaction_id: int
    ) -> PositionTransaction:
        """Crée une transaction de position"""
        
        total_amount = (quantity * price) + fee
        
        transaction = PositionTransaction(
            position_id=position_id,
            portfolio_transaction_id=portfolio_transaction_id,
            transaction_type=transaction_type,
            quantity=quantity,
            price=price,
            total_amount=total_amount,
            fees=fee,
            currency=currency,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            average_cost_before=average_cost_before,
            average_cost_after=average_cost_after,
            transaction_date=datetime.utcnow()
        )
        
        self.db.add(transaction)
        
        return transaction
    
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
        currency: str = "USD"
    ) -> Position:
        """Crée une nouvelle position"""
        
        total_cost = quantity * price
        
        position = Position(
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=quantity,
            average_cost=price,
            current_price=price,
            currency=currency,
            total_cost=total_cost,
            current_value=total_cost,
            unrealized_pnl=Decimal('0.00'),
            unrealized_pnl_percentage=Decimal('0.00')
        )
        
        self.db.add(position)
        self.db.flush()  # Pour obtenir l'ID
        
        return position
    
    def _add_to_position(self, position: Position, quantity: Decimal, price: Decimal) -> None:
        """Ajoute des titres à une position existante"""
        
        # Calculer la nouvelle moyenne pondérée
        total_cost = (position.quantity * position.average_cost) + (
            quantity * price
        )
        total_quantity = position.quantity + quantity
        
        # Mettre à jour la position
        position.quantity = total_quantity
        position.average_cost = total_cost / total_quantity
        position.total_cost = total_cost
        position.current_price = price
        position.current_value = total_quantity * price
        position.unrealized_pnl = position.current_value - position.total_cost
        
        if position.total_cost > 0:
            position.unrealized_pnl_percentage = (
                position.unrealized_pnl / position.total_cost
            ) * 100
        
        position.updated_at = datetime.utcnow()
    
    def _reduce_position(self, position: Position, quantity: Decimal, price: Decimal) -> Decimal:
        """Réduit une position et calcule le P&L réalisé"""
        
        # Calculer le P&L réalisé
        realized_pnl = (price - position.average_cost) * quantity
        
        # Mettre à jour la position
        position.quantity -= quantity
        position.total_cost -= (position.average_cost * quantity)
        position.current_price = price
        position.current_value = position.quantity * price
        position.realized_pnl += realized_pnl
        
        # Recalculer le P&L non réalisé
        if position.quantity > 0:
            position.unrealized_pnl = position.current_value - position.total_cost
            if position.total_cost > 0:
                position.unrealized_pnl_percentage = (
                    position.unrealized_pnl / position.total_cost
                ) * 100
        else:
            # Position fermée
            position.unrealized_pnl = Decimal('0.00')
            position.unrealized_pnl_percentage = Decimal('0.00')
        
        position.updated_at = datetime.utcnow()
        
        return realized_pnl
    
    def _create_position_transaction(
        self,
        position_id: int,
        transaction_type: str,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal,
        currency: str = "USD"
    ) -> PositionTransaction:
        """Crée une transaction de position"""
        
        transaction = PositionTransaction(
            position_id=position_id,
            transaction_type=transaction_type,
            quantity=quantity,
            price=price,
            fee=fee,
            currency=currency,
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
                position.current_value = position.quantity * new_price
                position.unrealized_pnl = position.current_value - position.total_cost
                
                if position.total_cost > 0:
                    position.unrealized_pnl_percentage = (
                        position.unrealized_pnl / position.total_cost
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
        total_realized_pnl = (sell_price - position.average_cost) * position.quantity
        
        # Créer la transaction de vente
        transaction = self._create_position_transaction(
            position_id, "SELL", position.quantity, sell_price, Decimal('0.00')
        )
        
        # Mettre à jour la position
        position.quantity = Decimal('0.00')
        position.current_price = sell_price
        position.current_value = Decimal('0.00')
        position.unrealized_pnl = Decimal('0.00')
        position.unrealized_pnl_percentage = Decimal('0.00')
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
        unrealized_pnl = current_value - position.total_cost
        unrealized_pnl_percentage = 0
        
        if position.total_cost > 0:
            unrealized_pnl_percentage = (unrealized_pnl / position.total_cost) * 100
        
        # Calculer le rendement total (réalisé + non réalisé)
        total_pnl = position.realized_pnl + unrealized_pnl
        total_return_percent = 0
        
        if position.total_cost > 0:
            total_return_percent = (total_pnl / position.total_cost) * 100
        
        return {
            "position_id": position_id,
            "symbol": position.symbol,
            "quantity": position.quantity,
            "average_buy_price": position.average_cost,
            "current_price": position.current_price,
            "cost_basis": position.total_cost,
            "current_value": current_value,
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_percent": unrealized_pnl_percentage,
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
                "total_cost": Decimal('0.00'),
                "total_pnl": Decimal('0.00'),
                "winning_positions": 0,
                "losing_positions": 0
            }
        
        total_value = sum(pos.current_value for pos in positions)
        total_cost = sum(pos.total_cost for pos in positions)
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in positions)
        total_realized_pnl = sum(pos.realized_pnl for pos in positions)
        total_pnl = total_unrealized_pnl + total_realized_pnl
        
        winning_positions = len([pos for pos in positions if pos.unrealized_pnl > 0])
        losing_positions = len([pos for pos in positions if pos.unrealized_pnl < 0])
        
        return {
            "total_positions": len(positions),
            "total_value": total_value,
            "total_cost": total_cost,
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
