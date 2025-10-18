from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Date, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

Base = declarative_base()

class MLModelsV2(Base):
    __tablename__ = 'ml_models_v2'
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    model_type = Column(String(50), nullable=False)  # classification, regression
    model_version = Column(String(20), nullable=False)  # Changed from version to model_version
    
    # Model parameters
    model_parameters = Column(JSONB)  # Changed from parameters to model_parameters
    feature_columns = Column(JSONB)  # Added feature_columns
    target_column = Column(String(50))  # Changed from target_variable to target_column
    
    # Performance metrics
    training_score = Column(Numeric(6,4))  # Changed from accuracy to training_score
    validation_score = Column(Numeric(6,4))  # Changed from precision to validation_score
    test_score = Column(Numeric(6,4))  # Changed from recall to test_score
    cross_validation_scores = Column(JSONB)  # Added cross_validation_scores
    
    # Additional performance metrics
    sharpe_ratio = Column(Numeric(8,4))
    max_drawdown = Column(Numeric(8,4))
    win_rate = Column(Numeric(6,4))
    profit_factor = Column(Numeric(8,4))
    
    # Training metadata
    training_data_start = Column(Date)  # Changed from training_start_date to training_data_start
    training_data_end = Column(Date)  # Changed from training_end_date to training_data_end
    validation_data_start = Column(Date)  # Added validation_data_start
    validation_data_end = Column(Date)  # Added validation_data_end
    test_data_start = Column(Date)  # Added test_data_start
    test_data_end = Column(Date)  # Added test_data_end
    
    # Model status
    is_active = Column(Boolean, default=False)  # Changed default to False
    is_production = Column(Boolean, default=False)  # Added is_production
    
    # Model storage
    model_path = Column(Text)  # Added model_path
    
    # Feature importance
    feature_importance = Column(JSONB)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
