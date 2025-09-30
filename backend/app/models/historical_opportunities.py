"""
Modèle pour les opportunités historiques générées pour le backtesting ML
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Index, DECIMAL, TIMESTAMP, Date, BIGINT, BOOLEAN, Numeric
from sqlalchemy.sql import func
from .database import Base


class HistoricalOpportunities(Base):
    """
    Table pour stocker les opportunités générées historiquement pour le backtesting ML
    """
    __tablename__ = "historical_opportunities"

    id = Column(BIGINT, primary_key=True, index=True)
    
    # Identification de l'opportunité
    symbol = Column(String(10), nullable=False, index=True)
    opportunity_date = Column(Date, nullable=False, index=True)  # Date à laquelle l'opportunité a été générée
    generation_timestamp = Column(TIMESTAMP, default=func.now(), nullable=False)
    
    # Scores et recommandations
    technical_score = Column(Numeric(5, 4), nullable=True)
    sentiment_score = Column(Numeric(5, 4), nullable=True)
    market_score = Column(Numeric(5, 4), nullable=True)
    ml_score = Column(Numeric(5, 4), nullable=True)
    composite_score = Column(Numeric(5, 4), nullable=True)
    
    recommendation = Column(String(20), nullable=True)  # BUY_STRONG, BUY_MODERATE, BUY_WEAK, HOLD, SELL_MODERATE, SELL_STRONG
    confidence_level = Column(String(20), nullable=True)  # LOW, MEDIUM, HIGH, VERY_HIGH
    risk_level = Column(String(20), nullable=True)  # LOW, MEDIUM, HIGH, VERY_HIGH
    
    # Données contextuelles au moment de la génération
    price_at_generation = Column(Numeric(10, 4), nullable=True)
    volume_at_generation = Column(BIGINT, nullable=True)
    market_cap_at_generation = Column(BIGINT, nullable=True)
    
    # Métriques de performance futures (remplies après validation)
    price_1_day_later = Column(Numeric(10, 4), nullable=True)
    price_7_days_later = Column(Numeric(10, 4), nullable=True)
    price_30_days_later = Column(Numeric(10, 4), nullable=True)
    
    return_1_day = Column(Numeric(8, 6), nullable=True)  # Rendement sur 1 jour
    return_7_days = Column(Numeric(8, 6), nullable=True)  # Rendement sur 7 jours
    return_30_days = Column(Numeric(8, 6), nullable=True)  # Rendement sur 30 jours
    
    # Validation de la recommandation
    recommendation_correct_1_day = Column(BOOLEAN, nullable=True)
    recommendation_correct_7_days = Column(BOOLEAN, nullable=True)
    recommendation_correct_30_days = Column(BOOLEAN, nullable=True)
    
    # Score de performance global
    performance_score = Column(Numeric(5, 4), nullable=True)  # Score calculé basé sur les rendements
    
    # Données détaillées des indicateurs (JSON)
    technical_indicators_data = Column(JSON, nullable=True)
    sentiment_indicators_data = Column(JSON, nullable=True)
    market_indicators_data = Column(JSON, nullable=True)
    ml_indicators_data = Column(JSON, nullable=True)
    
    # Métadonnées
    created_at = Column(TIMESTAMP, default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Index pour optimiser les requêtes
    __table_args__ = (
        Index('idx_historical_opp_symbol_date', 'symbol', 'opportunity_date'),
        Index('idx_historical_opp_date_performance', 'opportunity_date', 'performance_score'),
        Index('idx_historical_opp_recommendation', 'recommendation', 'opportunity_date'),
        Index('idx_historical_opp_generation_timestamp', 'generation_timestamp'),
    )


class HistoricalOpportunityValidation(Base):
    """
    Table pour stocker les résultats de validation des opportunités historiques
    """
    __tablename__ = "historical_opportunity_validation"

    id = Column(BIGINT, primary_key=True, index=True)
    
    # Référence à l'opportunité historique
    historical_opportunity_id = Column(BIGINT, nullable=False, index=True)
    
    # Paramètres de validation
    validation_period_days = Column(Integer, nullable=False)  # Période de validation (1, 7, 30 jours)
    validation_date = Column(Date, nullable=False)  # Date de fin de validation
    
    # Résultats de validation
    actual_return = Column(Numeric(8, 6), nullable=True)
    predicted_return = Column(Numeric(8, 6), nullable=True)
    prediction_error = Column(Numeric(8, 6), nullable=True)  # Erreur de prédiction
    
    # Métriques de performance
    sharpe_ratio = Column(Numeric(8, 6), nullable=True)
    max_drawdown = Column(Numeric(8, 6), nullable=True)
    volatility = Column(Numeric(8, 6), nullable=True)
    
    # Classification de la performance
    performance_category = Column(String(20), nullable=True)  # EXCELLENT, GOOD, AVERAGE, POOR, TERRIBLE
    
    # Données de marché pendant la période de validation
    market_return = Column(Numeric(8, 6), nullable=True)  # Rendement du marché (NASDAQ)
    beta = Column(Numeric(8, 6), nullable=True)  # Beta calculé sur la période
    
    # Métadonnées
    created_at = Column(TIMESTAMP, default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Index
    __table_args__ = (
        Index('idx_validation_opp_id', 'historical_opportunity_id'),
        Index('idx_validation_period_date', 'validation_period_days', 'validation_date'),
        Index('idx_validation_performance', 'performance_category', 'validation_period_days'),
    )
