from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

Base = declarative_base()

class MLRecommendationsV2(Base):
    __tablename__ = 'ml_recommendations_v2'
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey('ml_models_v2.id'), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    recommendation_date = Column(DateTime, nullable=False, index=True)
    
    # Recommendation details
    recommendation = Column(String(20), nullable=False)  # BUY_STRONG, BUY_MODERATE, etc.
    confidence_score = Column(Float, nullable=False)
    expected_return = Column(Float)
    risk_score = Column(Float)
    
    # Supporting data
    technical_score = Column(Float)
    fundamental_score = Column(Float)
    sentiment_score = Column(Float)
    
    # Prediction details
    prediction_probabilities = Column(JSONB)
    feature_contributions = Column(JSONB)
    
    # Recommendation metadata
    recommendation_horizon = Column(String(20))  # 1d, 5d, 20d
    model_version = Column(String(20))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional metadata
    notes = Column(Text)
    validation_status = Column(String(20))  # pending, validated, rejected
