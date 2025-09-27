"""
Modèle pour les opportunités d'analyse avancée
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class AdvancedOpportunity(Base):
    """Table pour stocker les opportunités d'analyse avancée"""
    __tablename__ = "advanced_opportunities"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    analysis_date = Column(DateTime, nullable=False, default=func.now())
    
    # Scores principaux
    technical_score = Column(Float, nullable=False)
    sentiment_score = Column(Float, nullable=False)
    market_score = Column(Float, nullable=False)
    ml_score = Column(Float, nullable=False)
    candlestick_score = Column(Float, nullable=False)
    garch_score = Column(Float, nullable=False)
    monte_carlo_score = Column(Float, nullable=False)
    markov_score = Column(Float, nullable=False)
    volatility_score = Column(Float, nullable=False)
    composite_score = Column(Float, nullable=False)
    
    # Métadonnées
    confidence_level = Column(Float, nullable=False)
    recommendation = Column(String(20), nullable=False)  # BUY, SELL, HOLD, STRONG_BUY, STRONG_SELL
    risk_level = Column(String(20), nullable=False)     # LOW, MEDIUM, HIGH
    
    # Détails d'analyse (stockés en JSON pour flexibilité)
    technical_analysis = Column(JSON)
    sentiment_analysis = Column(JSON)
    market_analysis = Column(JSON)
    ml_analysis = Column(JSON)
    candlestick_analysis = Column(JSON)
    garch_analysis = Column(JSON)
    monte_carlo_analysis = Column(JSON)
    markov_analysis = Column(JSON)
    volatility_analysis = Column(JSON)
    
    # Configuration de l'analyse
    time_horizon = Column(Integer, nullable=False, default=30)
    analysis_types = Column(JSON)  # Liste des types d'analyse utilisés
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Index pour les requêtes fréquentes
    __table_args__ = (
        Index('idx_symbol_analysis_date', 'symbol', 'analysis_date'),
        Index('idx_composite_score', 'composite_score'),
        Index('idx_recommendation', 'recommendation'),
        Index('idx_analysis_date', 'analysis_date'),
    )

class AdvancedAnalysisConfig(Base):
    """Configuration pour les analyses avancées"""
    __tablename__ = "advanced_analysis_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    
    # Configuration des scores
    technical_weight = Column(Float, default=0.25)
    sentiment_weight = Column(Float, default=0.25)
    market_weight = Column(Float, default=0.25)
    ml_weight = Column(Float, default=0.25)
    
    # Seuils de recommandation
    strong_buy_threshold = Column(Float, default=0.8)
    buy_threshold = Column(Float, default=0.6)
    hold_threshold_min = Column(Float, default=0.4)
    hold_threshold_max = Column(Float, default=0.6)
    sell_threshold = Column(Float, default=0.4)
    strong_sell_threshold = Column(Float, default=0.2)
    
    # Configuration des analyses
    time_horizon_default = Column(Integer, default=30)
    analysis_types_default = Column(JSON, default=["technical", "sentiment", "market", "ml"])
    
    # Métadonnées
    is_active = Column(String(10), default="true")
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

