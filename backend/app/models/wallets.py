from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class WalletType(enum.Enum):
    CASH = "cash"
    CRYPTO = "crypto"
    MARGIN = "margin"


class WalletStatus(enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


class Wallet(Base):
    __tablename__ = "wallets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    wallet_type = Column(Enum(WalletType), default=WalletType.CASH, nullable=False)
    status = Column(Enum(WalletStatus), default=WalletStatus.ACTIVE, nullable=False)
    
    # Balance information
    currency = Column(String(10), default="USD", nullable=False)
    available_balance = Column(Numeric(15, 2), default=0.00, nullable=False)
    pending_balance = Column(Numeric(15, 2), default=0.00, nullable=False)
    total_balance = Column(Numeric(15, 2), default=0.00, nullable=False)
    
    # Settings
    auto_reinvest = Column(Boolean, default=False, nullable=False)
    min_balance_threshold = Column(Numeric(15, 2), default=0.00, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_transaction_at = Column(DateTime, nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="wallets")
    transactions = relationship("WalletTransaction", back_populates="wallet", cascade="all, delete-orphan")
    portfolios = relationship("Portfolio", back_populates="wallet", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Wallet(id={self.id}, user_id={self.user_id}, name='{self.name}', balance={self.total_balance})>"


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(String(50), nullable=False)  # deposit, withdrawal, transfer_in, transfer_out, fee
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default="USD", nullable=False)
    balance_before = Column(Numeric(15, 2), nullable=False)
    balance_after = Column(Numeric(15, 2), nullable=False)
    
    # Reference information
    reference_id = Column(String(100), nullable=True)  # External transaction ID
    description = Column(String(255), nullable=True)
    notes = Column(String(500), nullable=True)
    
    # Status
    status = Column(String(20), default="completed", nullable=False)  # pending, completed, failed, cancelled
    
    # Timestamps
    transaction_date = Column(DateTime, default=func.now(), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    wallet = relationship("Wallet", back_populates="transactions")

    def __repr__(self):
        return f"<WalletTransaction(id={self.id}, wallet_id={self.wallet_id}, type='{self.transaction_type}', amount={self.amount})>"
