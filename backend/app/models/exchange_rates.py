from sqlalchemy import Column, Integer, String, DateTime, Numeric, Boolean, Index
from sqlalchemy.sql import func
from app.core.database import Base


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True, index=True)
    
    # Currency pair information
    from_currency = Column(String(3), nullable=False, index=True)  # Base currency (e.g., 'USD')
    to_currency = Column(String(3), nullable=False, index=True)   # Quote currency (e.g., 'EUR')
    pair = Column(String(7), nullable=False, index=True)          # Combined pair (e.g., 'USD/EUR')
    
    # Exchange rate data
    rate = Column(Numeric(10, 6), nullable=False)                 # Exchange rate
    inverse_rate = Column(Numeric(10, 6), nullable=False)         # Inverse rate (1/rate)
    
    # Metadata
    source = Column(String(50), nullable=False, default="api")     # Data source (api, manual, etc.)
    is_active = Column(Boolean, default=True, nullable=False)      # Whether rate is currently valid
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_fetched_at = Column(DateTime, nullable=True)              # When rate was last fetched from API
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_currency_pair', 'from_currency', 'to_currency'),
        Index('idx_pair_active', 'pair', 'is_active'),
        Index('idx_updated_at', 'updated_at'),
    )
    
    def __repr__(self):
        return f"<ExchangeRate({self.pair}={self.rate})>"
    
    @property
    def currency_pair(self) -> str:
        """Returns the currency pair in standard format"""
        return f"{self.from_currency}/{self.to_currency}"
    
    def convert_amount(self, amount: float, reverse: bool = False) -> float:
        """
        Convert amount using this exchange rate
        
        Args:
            amount: Amount to convert
            reverse: If True, use inverse rate
            
        Returns:
            Converted amount
        """
        rate = self.inverse_rate if reverse else self.rate
        return float(amount) * float(rate)
