from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

Base = declarative_base()

class MLPredictionsV2(Base):
    __tablename__ = 'ml_predictions_v2'
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey('ml_models_v2.id'), nullable=False, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    prediction_date = Column(DateTime, nullable=False, index=True)
    
    # Prediction results
    predicted_value = Column(Float)
    predicted_class = Column(String(50))
    prediction_probability = Column(Float)
    confidence_score = Column(Float)
    
    # Input features used for prediction
    features = Column(JSONB)
    
    # Actual values (for validation)
    actual_value = Column(Float)
    actual_class = Column(String(50))
    
    # Prediction metadata
    prediction_horizon = Column(String(20))  # 1d, 5d, 20d
    prediction_type = Column(String(50))  # recommendation, return, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Additional metadata
    notes = Column(Text)
