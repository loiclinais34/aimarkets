"""
Service de trading simplifié pour les achats/ventes de titres
Logique: WalletTransaction -> Position (agrégation)
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from fastapi import HTTPException, status

from app.models.portfolios import Position, Portfolio
from app.models.wallets import Wallet, WalletTransaction, WalletTransactionType, WalletStatus
from app.services.authentication_service import AuthenticationService
from app.services.exchange_rate_service import ExchangeRateService


class TradingService:
    """Service de trading simplifié"""
    
    def __init__(self, db: Session):
        self.db = db
        self.auth_service = AuthenticationService(db)
        self.exchange_service = ExchangeRateService(db)
    
    def buy_stock(
        self,
        portfolio_id: int,
        wallet_id: int,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        fees: Decimal = Decimal('0.00'),
        description: str = None
    ) -> Tuple[WalletTransaction, Position]:
        """Acheter des titres - crée une transaction et met à jour la position"""
        
        # 1. Vérifier que le portfolio existe
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portefeuille non trouvé"
            )
        
        # 2. Vérifier que le wallet existe et est actif
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
        
        # 3. Calculer le coût total
        total_cost = (quantity * price) + fees
        
        # 4. Vérifier les fonds disponibles
        if wallet.available_balance < total_cost:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Fonds insuffisants. Solde: {wallet.available_balance} {wallet.currency}, "
                       f"Nécessaire: {total_cost} {wallet.currency}"
            )
        
        # 5. Créer la transaction de wallet
        new_balance = wallet.available_balance - total_cost
        
        wallet_transaction = WalletTransaction(
            wallet_id=wallet_id,
            transaction_type=WalletTransactionType.BUY_STOCK,
            amount=-total_cost,  # Négatif car c'est un débit
            balance_after=new_balance,
            symbol=symbol,
            quantity=quantity,
            price=price,
            fees=fees,
            description=description or f"Achat de {quantity} {symbol} à {price}"
        )
        
        self.db.add(wallet_transaction)
        self.db.flush()  # Pour obtenir l'ID
        
        # 6. Mettre à jour le balance du wallet
        wallet.available_balance = new_balance
        wallet.total_balance = new_balance
        wallet.updated_at = datetime.utcnow()
        
        # 7. Mettre à jour ou créer la position
        position = self._update_position_after_buy(
            portfolio_id=portfolio_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            fees=fees,
            currency=wallet.currency
        )
        
        self.db.commit()
        
        return wallet_transaction, position
    
    def sell_stock(
        self,
        portfolio_id: int,
        wallet_id: int,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        fees: Decimal = Decimal('0.00'),
        description: str = None,
        target_wallet_id: Optional[int] = None
    ) -> Tuple[WalletTransaction, Position]:
        """Vendre des titres - crée une transaction et met à jour la position"""
        
        # 1. Vérifier que le portfolio existe
        portfolio = self.db.query(Portfolio).filter(Portfolio.id == portfolio_id).first()
        if not portfolio:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Portefeuille non trouvé"
            )
        
        # 2. Vérifier que le wallet existe et est actif
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
        
        # 2.1. Vérifier le wallet de destination si spécifié
        target_wallet = None
        if target_wallet_id:
            target_wallet = self.db.query(Wallet).filter(
                Wallet.id == target_wallet_id,
                Wallet.portfolio_id == portfolio_id,
                Wallet.status == WalletStatus.ACTIVE
            ).first()
            
            if not target_wallet:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Wallet de destination non trouvé ou inactif"
                )
        
        # 3. Vérifier que la position existe
        position = self.db.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.symbol == symbol,
            Position.currency == wallet.currency
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
        
        # 4. Calculer le produit net
        net_proceeds = (quantity * price) - fees
        
        # 5. Déterminer le wallet de destination (celui spécifié ou celui de la position)
        destination_wallet = target_wallet if target_wallet else wallet
        print(f"DEBUG SELL: target_wallet_id={target_wallet_id}, target_wallet={target_wallet}, destination_wallet_id={destination_wallet.id}")
        
        # 6. Créer la transaction de wallet sur le wallet de destination
        new_balance = destination_wallet.available_balance + net_proceeds
        
        wallet_transaction = WalletTransaction(
            wallet_id=destination_wallet.id,
            transaction_type=WalletTransactionType.SELL_STOCK,
            amount=net_proceeds,  # Positif car c'est un crédit
            balance_after=new_balance,
            symbol=symbol,
            quantity=quantity,
            price=price,
            fees=fees,
            description=description or f"Vente de {quantity} {symbol} à {price}"
        )
        
        self.db.add(wallet_transaction)
        self.db.flush()  # Pour obtenir l'ID
        
        # 7. Mettre à jour le balance du wallet de destination
        destination_wallet.available_balance = new_balance
        destination_wallet.total_balance = new_balance
        destination_wallet.updated_at = datetime.utcnow()
        
        # 7. Mettre à jour la position
        position = self._update_position_after_sell(
            position=position,
            quantity=quantity,
            price=price,
            fees=fees
        )
        
        self.db.commit()
        
        return wallet_transaction, position
    
    def _update_position_after_buy(
        self,
        portfolio_id: int,
        symbol: str,
        quantity: Decimal,
        price: Decimal,
        fees: Decimal,
        currency: str
    ) -> Position:
        """Met à jour la position après un achat"""
        
        # Chercher la position existante
        position = self.db.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.symbol == symbol,
            Position.currency == currency
        ).first()
        
        if position:
            # Ajouter à la position existante
            old_quantity = position.quantity
            old_total_cost = position.total_cost
            
            new_quantity = old_quantity + quantity
            new_total_cost = old_total_cost + (quantity * price) + fees
            new_average_cost = new_total_cost / new_quantity
            
            position.quantity = new_quantity
            position.average_cost = new_average_cost
            position.total_cost = new_total_cost
            position.current_value = new_quantity * (position.current_price or price)
            position.unrealized_pnl = position.current_value - new_total_cost
            position.unrealized_pnl_percentage = (position.unrealized_pnl / new_total_cost) * 100 if new_total_cost > 0 else 0
            position.total_fees += fees
            position.last_purchase_date = datetime.utcnow()
            position.updated_at = datetime.utcnow()
            
            if not position.first_purchase_date:
                position.first_purchase_date = datetime.utcnow()
        else:
            # Créer une nouvelle position
            total_cost = (quantity * price) + fees
            
            position = Position(
                portfolio_id=portfolio_id,
                symbol=symbol,
                quantity=quantity,
                average_cost=price + (fees / quantity),
                current_price=price,
                total_cost=total_cost,
                current_value=quantity * price,
                unrealized_pnl=quantity * price - total_cost,
                unrealized_pnl_percentage=((quantity * price - total_cost) / total_cost) * 100 if total_cost > 0 else 0,
                realized_pnl=Decimal('0.00'),
                total_dividends=Decimal('0.00'),
                total_fees=fees,
                weight_percentage=Decimal('0.00'),
                currency=currency,
                first_purchase_date=datetime.utcnow(),
                last_purchase_date=datetime.utcnow()
            )
            
            self.db.add(position)
            self.db.flush()
        
        return position
    
    def _update_position_after_sell(
        self,
        position: Position,
        quantity: Decimal,
        price: Decimal,
        fees: Decimal
    ) -> Position:
        """Met à jour la position après une vente"""
        
        # Calculer le P&L réalisé
        realized_pnl = (price - position.average_cost) * quantity - fees
        
        old_quantity = position.quantity
        old_total_cost = position.total_cost
        
        new_quantity = old_quantity - quantity
        new_total_cost = position.total_cost - (position.average_cost * quantity)
        
        if new_quantity > 0:
            new_average_cost = new_total_cost / new_quantity
        else:
            new_average_cost = Decimal('0.00')
        
        position.quantity = new_quantity
        position.average_cost = new_average_cost
        position.total_cost = new_total_cost
        position.current_value = new_quantity * (position.current_price or price)
        position.unrealized_pnl = position.current_value - new_total_cost
        position.unrealized_pnl_percentage = (position.unrealized_pnl / new_total_cost) * 100 if new_total_cost > 0 else 0
        position.realized_pnl += realized_pnl
        position.total_fees += fees
        position.last_sale_date = datetime.utcnow()
        position.updated_at = datetime.utcnow()
        
        return position
    
    def get_positions(self, portfolio_id: int) -> List[Position]:
        """Récupère toutes les positions d'un portefeuille"""
        return self.db.query(Position).filter(
            Position.portfolio_id == portfolio_id
        ).all()
    
    def get_position(self, portfolio_id: int, symbol: str, currency: str = "USD") -> Optional[Position]:
        """Récupère une position spécifique"""
        return self.db.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.symbol == symbol,
            Position.currency == currency
        ).first()
    
    def get_trading_history(
        self, 
        portfolio_id: int, 
        symbol: str = None, 
        limit: int = 50
    ) -> List[WalletTransaction]:
        """Récupère l'historique des transactions de trading"""
        
        query = self.db.query(WalletTransaction).join(Wallet).filter(
            Wallet.portfolio_id == portfolio_id,
            WalletTransaction.transaction_type.in_([
                WalletTransactionType.BUY_STOCK,
                WalletTransactionType.SELL_STOCK
            ])
        )
        
        if symbol:
            query = query.filter(WalletTransaction.symbol == symbol)
        
        return query.order_by(desc(WalletTransaction.created_at)).limit(limit).all()
