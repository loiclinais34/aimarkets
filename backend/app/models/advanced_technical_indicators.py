from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index, Boolean, Numeric, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

Base = declarative_base()

class AdvancedTechnicalIndicators(Base):
    __tablename__ = 'advanced_technical_indicators'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Price-based indicators
    sma_5 = Column(Numeric(10,4))
    sma_10 = Column(Numeric(10,4))
    sma_20 = Column(Numeric(10,4))
    sma_50 = Column(Numeric(10,4))
    sma_200 = Column(Numeric(10,4))
    
    ema_5 = Column(Numeric(10,4))
    ema_10 = Column(Numeric(10,4))
    ema_20 = Column(Numeric(10,4))
    ema_50 = Column(Numeric(10,4))
    ema_200 = Column(Numeric(10,4))
    
    # Momentum indicators
    rsi_14 = Column(Numeric(5,2))
    rsi_21 = Column(Numeric(5,2))
    macd_line = Column(Numeric(10,4))  # Changed from macd to macd_line
    macd_signal = Column(Numeric(10,4))
    macd_histogram = Column(Numeric(10,4))
    
    # Volatility indicators
    bollinger_upper = Column(Numeric(10,4))
    bollinger_middle = Column(Numeric(10,4))
    bollinger_lower = Column(Numeric(10,4))
    bollinger_width = Column(Numeric(8,4))
    
    atr_14 = Column(Numeric(10,4))
    volatility_20 = Column(Numeric(8,4))
    
    # Volume indicators
    volume_sma_20 = Column(Numeric(15,2))
    volume_ratio = Column(Numeric(8,4))
    obv = Column(Numeric(15,2))
    vwap = Column(Numeric(10,4))
    
    # Additional indicators
    stochastic_k = Column(Numeric(5,2))
    stochastic_d = Column(Numeric(5,2))
    williams_r = Column(Numeric(5,2))
    cci = Column(Numeric(8,2))
    roc = Column(Numeric(8,2))
    
    # Candlestick patterns
    doji = Column(Boolean, default=False)
    hammer = Column(Boolean, default=False)
    shooting_star = Column(Boolean, default=False)
    engulfing_bullish = Column(Boolean, default=False)
    engulfing_bearish = Column(Boolean, default=False)
    
    # Support/Resistance
    support_level = Column(Numeric(10,4))
    resistance_level = Column(Numeric(10,4))
    pivot_point = Column(Numeric(10,4))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_symbol_date', 'symbol', 'date'),
        Index('idx_date_symbol', 'date', 'symbol'),
    )
