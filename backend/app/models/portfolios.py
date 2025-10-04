from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, ForeignKey, Enum, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum


class PortfolioType(enum.Enum):
    PERSONAL = "personal"
    JOINT = "joint"
    CORPORATE = "corporate"
    RETIREMENT = "retirement"


class PortfolioStatus(enum.Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    SUSPENDED = "suspended"


class Portfolio(Base):
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Portfolio information
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    portfolio_type = Column(Enum(PortfolioType), default=PortfolioType.PERSONAL, nullable=False)
    status = Column(Enum(PortfolioStatus), default=PortfolioStatus.ACTIVE, nullable=False)
    
    # Financial information
    initial_capital = Column(Numeric(15, 2), default=0.00, nullable=False)
    current_value = Column(Numeric(15, 2), default=0.00, nullable=False)
    total_invested = Column(Numeric(15, 2), default=0.00, nullable=False)
    total_withdrawn = Column(Numeric(15, 2), default=0.00, nullable=False)
    
    # Performance metrics
    total_return = Column(Numeric(15, 2), default=0.00, nullable=False)
    total_return_percentage = Column(Numeric(8, 4), default=0.0000, nullable=False)
    annualized_return = Column(Numeric(8, 4), default=0.0000, nullable=False)
    sharpe_ratio = Column(Numeric(8, 4), nullable=True)
    max_drawdown = Column(Numeric(8, 4), nullable=True)
    
    # Settings
    auto_rebalance = Column(Boolean, default=False, nullable=False)
    rebalance_threshold = Column(Numeric(5, 2), default=5.00, nullable=False)  # Percentage
    risk_tolerance = Column(String(20), default="moderate", nullable=False)  # conservative, moderate, aggressive
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_rebalance_at = Column(DateTime, nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="portfolios")
    wallets = relationship("Wallet", back_populates="portfolio", cascade="all, delete-orphan")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("PortfolioTransaction", back_populates="portfolio", cascade="all, delete-orphan")
    performance_records = relationship("PortfolioPerformance", back_populates="portfolio", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Portfolio(id={self.id}, user_id={self.user_id}, name='{self.name}', value={self.current_value})>"


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    
    # Position information
    symbol = Column(String(20), nullable=False, index=True)
    company_name = Column(String(255), nullable=True)
    
    # Position details
    quantity = Column(Numeric(15, 6), nullable=False, default=0.000000)
    average_cost = Column(Numeric(15, 6), nullable=False, default=0.000000)
    current_price = Column(Numeric(15, 6), nullable=True)
    
    # Financial information
    total_cost = Column(Numeric(15, 2), nullable=False, default=0.00)
    current_value = Column(Numeric(15, 2), nullable=False, default=0.00)
    unrealized_pnl = Column(Numeric(15, 2), nullable=False, default=0.00)
    unrealized_pnl_percentage = Column(Numeric(8, 4), nullable=False, default=0.0000)
    
    # Realized information
    realized_pnl = Column(Numeric(15, 2), nullable=False, default=0.00)
    total_dividends = Column(Numeric(15, 2), nullable=False, default=0.00)
    total_fees = Column(Numeric(15, 2), nullable=False, default=0.00)
    
    # Weight in portfolio
    weight_percentage = Column(Numeric(8, 4), nullable=False, default=0.0000)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    first_purchase_date = Column(DateTime, nullable=True)
    last_purchase_date = Column(DateTime, nullable=True)
    last_sale_date = Column(DateTime, nullable=True)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")
    transactions = relationship("PositionTransaction", back_populates="position", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Position(id={self.id}, portfolio_id={self.portfolio_id}, symbol='{self.symbol}', quantity={self.quantity})>"


class PortfolioTransaction(Base):
    __tablename__ = "portfolio_transactions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False)  # buy, sell, dividend, fee, transfer_in, transfer_out
    symbol = Column(String(20), nullable=False, index=True)
    quantity = Column(Numeric(15, 6), nullable=False)
    price = Column(Numeric(15, 6), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    fees = Column(Numeric(15, 2), default=0.00, nullable=False)
    
    # Reference information
    reference_id = Column(String(100), nullable=True)  # External transaction ID
    notes = Column(Text, nullable=True)
    
    # Status
    status = Column(String(20), default="completed", nullable=False)  # pending, completed, failed, cancelled
    
    # Timestamps
    transaction_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")

    def __repr__(self):
        return f"<PortfolioTransaction(id={self.id}, portfolio_id={self.portfolio_id}, type='{self.transaction_type}', symbol='{self.symbol}')>"


class PositionTransaction(Base):
    __tablename__ = "position_transactions"

    id = Column(Integer, primary_key=True, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False, index=True)
    portfolio_transaction_id = Column(Integer, ForeignKey("portfolio_transactions.id"), nullable=True, index=True)
    
    # Transaction details
    transaction_type = Column(String(20), nullable=False)  # buy, sell, dividend, split
    quantity = Column(Numeric(15, 6), nullable=False)
    price = Column(Numeric(15, 6), nullable=False)
    total_amount = Column(Numeric(15, 2), nullable=False)
    fees = Column(Numeric(15, 2), default=0.00, nullable=False)
    
    # Position impact
    quantity_before = Column(Numeric(15, 6), nullable=False)
    quantity_after = Column(Numeric(15, 6), nullable=False)
    average_cost_before = Column(Numeric(15, 6), nullable=False)
    average_cost_after = Column(Numeric(15, 6), nullable=False)
    
    # Timestamps
    transaction_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    position = relationship("Position", back_populates="transactions")

    def __repr__(self):
        return f"<PositionTransaction(id={self.id}, position_id={self.position_id}, type='{self.transaction_type}', quantity={self.quantity})>"


class PortfolioPerformance(Base):
    __tablename__ = "portfolio_performance"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    
    # Performance date
    performance_date = Column(DateTime, nullable=False, index=True)
    
    # Portfolio values
    total_value = Column(Numeric(15, 2), nullable=False)
    invested_capital = Column(Numeric(15, 2), nullable=False)
    
    # Performance metrics
    daily_return = Column(Numeric(8, 6), nullable=False, default=0.000000)
    daily_return_percentage = Column(Numeric(8, 4), nullable=False, default=0.0000)
    total_return = Column(Numeric(15, 2), nullable=False, default=0.00)
    total_return_percentage = Column(Numeric(8, 4), nullable=False, default=0.0000)
    
    # Risk metrics
    volatility = Column(Numeric(8, 6), nullable=True)
    sharpe_ratio = Column(Numeric(8, 4), nullable=True)
    max_drawdown = Column(Numeric(8, 4), nullable=True)
    
    # Benchmark comparison
    benchmark_return = Column(Numeric(8, 4), nullable=True)
    alpha = Column(Numeric(8, 4), nullable=True)
    beta = Column(Numeric(8, 4), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="performance_records")

    def __repr__(self):
        return f"<PortfolioPerformance(id={self.id}, portfolio_id={self.portfolio_id}, date='{self.performance_date}', return={self.daily_return_percentage}%)>"
