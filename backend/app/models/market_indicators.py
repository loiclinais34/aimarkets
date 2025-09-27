"""
Modèles pour les indicateurs de marché
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Index
from sqlalchemy.sql import func
from app.core.database import Base

class MarketIndicators(Base):
    """Table pour les indicateurs de marché"""
    __tablename__ = "market_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    indicator_type = Column(String(50), nullable=False)
    indicator_value = Column(Float, nullable=False)
    indicator_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class MomentumIndicators(Base):
    """Table pour les indicateurs de momentum"""
    __tablename__ = "momentum_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    price_momentum_5d = Column(Float)
    price_momentum_10d = Column(Float)
    price_momentum_20d = Column(Float)
    price_momentum_50d = Column(Float)
    volume_momentum_5d = Column(Float)
    volume_momentum_10d = Column(Float)
    volume_momentum_20d = Column(Float)
    relative_volume = Column(Float)
    relative_strength = Column(Float)
    composite_momentum_score = Column(Float)
    momentum_class = Column(String(20))
    momentum_divergence = Column(Float)
    momentum_ranking = Column(Integer)
    momentum_percentile = Column(Float)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class VolatilityIndicators(Base):
    """Table pour les indicateurs de volatilité"""
    __tablename__ = "volatility_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    historical_volatility_20d = Column(Float)
    historical_volatility_30d = Column(Float)
    implied_volatility = Column(Float)
    vix_level = Column(Float)
    volatility_ratio = Column(Float)
    volatility_percentile = Column(Float)
    volatility_skew = Column(Float)
    volatility_risk_premium = Column(Float)
    volatility_regime = Column(String(20))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

