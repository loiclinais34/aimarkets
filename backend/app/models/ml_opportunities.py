from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Date, Numeric, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

Base = declarative_base()

class MLOpportunities(Base):
    __tablename__ = 'ml_opportunities'

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    horizon_days = Column(Integer, nullable=False, index=True)
    recommendation = Column(String(20), nullable=False, index=True)
    confidence_level = Column(Numeric(5,4), nullable=False, index=True)
    potential_return = Column(Numeric(8,4))
    risk_score = Column(Numeric(5,4))
    ml_model_name = Column(String(100))
    ml_model_version = Column(String(20))
    technical_indicators = Column(JSONB)
    ml_features = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Indexes for better query performance
    __table_args__ = (
        Index('idx_ml_opportunities_symbol_date', 'symbol', 'date'),
        Index('idx_ml_opportunities_horizon', 'horizon_days'),
        Index('idx_ml_opportunities_recommendation', 'recommendation'),
        Index('idx_ml_opportunities_confidence', 'confidence_level'),
    )
