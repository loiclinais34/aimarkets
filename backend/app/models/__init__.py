# Import all models to ensure they are registered with SQLAlchemy
from .users import User, UserSession, PasswordReset
from .wallets import Wallet, WalletTransaction
from .portfolios import (
    Portfolio, 
    Position, 
    PortfolioTransaction, 
    PositionTransaction, 
    PortfolioPerformance
)
from .database import (
    HistoricalData,
    TechnicalIndicators,
    SentimentData,
    SentimentIndicators,
    FinancialRatios
)

__all__ = [
    # User management
    "User",
    "UserSession", 
    "PasswordReset",
    
    # Wallet management
    "Wallet",
    "WalletTransaction",
    
    # Portfolio management
    "Portfolio",
    "Position",
    "PortfolioTransaction",
    "PositionTransaction",
    "PortfolioPerformance",
    
    # Market data
    "HistoricalData",
    "TechnicalIndicators",
    "SentimentData",
    "SentimentIndicators",
    "FinancialRatios"
]
