"""
Modèles de base de données pour les indicateurs de marché.

Ce module définit les modèles SQLAlchemy pour stocker
les indicateurs de marché et leurs analyses.
"""

from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, Boolean, Text, JSON
from sqlalchemy.sql import func
from .database import Base


class MarketIndicators(Base):
    """
    Modèle pour stocker les indicateurs de marché généraux.
    """
    __tablename__ = "market_indicators"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    indicator_type = Column(String(50), nullable=False)  # VIX, VIX9D, VVIX, etc.
    indicator_value = Column(DECIMAL(10, 6), nullable=False)
    indicator_name = Column(String(100), nullable=True)
    analysis_date = Column(TIMESTAMP, nullable=False, index=True)
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = ({"schema": "public"},)


class VolatilityIndicators(Base):
    """
    Modèle pour stocker les indicateurs de volatilité.
    """
    __tablename__ = "volatility_indicators"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    analysis_date = Column(TIMESTAMP, nullable=False, index=True)
    current_volatility = Column(DECIMAL(10, 6), nullable=False)
    historical_volatility = Column(DECIMAL(10, 6), nullable=True)
    implied_volatility = Column(DECIMAL(10, 6), nullable=True)
    vix_value = Column(DECIMAL(10, 6), nullable=True)
    volatility_ratio = Column(DECIMAL(10, 6), nullable=True)  # Ratio actuel/historique
    volatility_percentile = Column(DECIMAL(5, 2), nullable=True)  # Percentile
    volatility_skew = Column(DECIMAL(10, 6), nullable=True)  # Skew de volatilité
    risk_premium = Column(DECIMAL(10, 6), nullable=True)  # Prime de risque de volatilité
    risk_level = Column(String(20), nullable=True)  # Niveau de risque
    regime_analysis = Column(JSON, nullable=True)  # Analyse des régimes
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = ({"schema": "public"},)


class CorrelationAnalysis(Base):
    """
    Modèle pour stocker les analyses de corrélation.
    """
    __tablename__ = "correlation_analysis"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    analysis_date = Column(TIMESTAMP, nullable=False, index=True)
    correlation_type = Column(String(50), nullable=False)  # market, sector, peer
    target_symbol = Column(String(10), nullable=True)  # Symbole de référence
    correlation_value = Column(DECIMAL(5, 4), nullable=False)  # -1 à 1
    correlation_strength = Column(String(20), nullable=True)  # weak, moderate, strong
    rolling_correlation = Column(JSON, nullable=True)  # Corrélation mobile
    correlation_stability = Column(DECIMAL(5, 4), nullable=True)  # Stabilité de la corrélation
    network_analysis = Column(JSON, nullable=True)  # Analyse du réseau
    risk_contribution = Column(DECIMAL(5, 4), nullable=True)  # Contribution au risque
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = ({"schema": "public"},)


class MomentumIndicators(Base):
    """
    Modèle pour stocker les indicateurs de momentum.
    """
    __tablename__ = "momentum_indicators"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    analysis_date = Column(TIMESTAMP, nullable=False, index=True)
    price_momentum_5d = Column(DECIMAL(10, 6), nullable=True)
    price_momentum_10d = Column(DECIMAL(10, 6), nullable=True)
    price_momentum_20d = Column(DECIMAL(10, 6), nullable=True)
    price_momentum_50d = Column(DECIMAL(10, 6), nullable=True)
    volume_momentum = Column(DECIMAL(10, 6), nullable=True)
    relative_volume = Column(DECIMAL(10, 6), nullable=True)
    relative_strength = Column(DECIMAL(10, 6), nullable=True)  # Par rapport au benchmark
    momentum_score = Column(DECIMAL(10, 6), nullable=True)  # Score composite
    momentum_class = Column(String(20), nullable=True)  # Strong Positive, Positive, etc.
    momentum_divergence = Column(DECIMAL(10, 6), nullable=True)  # Divergence prix/momentum
    momentum_ranking = Column(Integer, nullable=True)  # Classement dans le secteur
    momentum_percentile = Column(DECIMAL(5, 2), nullable=True)  # Percentile
    analysis_details = Column(JSON, nullable=True)  # Détails de l'analyse
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = ({"schema": "public"},)


class MarketSentimentSummary(Base):
    """
    Modèle pour stocker un résumé de l'analyse de sentiment de marché.
    """
    __tablename__ = "market_sentiment_summary"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    analysis_date = Column(TIMESTAMP, nullable=False, index=True)
    overall_sentiment = Column(String(20), nullable=False)  # BULLISH, BEARISH, NEUTRAL
    sentiment_score = Column(DECIMAL(5, 4), nullable=False)  # -1 à 1
    confidence_level = Column(DECIMAL(3, 2), nullable=False)  # 0-1
    volatility_regime = Column(String(20), nullable=True)  # LOW, MEDIUM, HIGH, VERY_HIGH
    correlation_regime = Column(String(20), nullable=True)  # LOW, MEDIUM, HIGH
    momentum_regime = Column(String(20), nullable=True)  # STRONG_POSITIVE, POSITIVE, etc.
    risk_level = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, VERY_HIGH
    market_state = Column(String(20), nullable=True)  # BULL, BEAR, SIDEWAYS
    key_indicators = Column(JSON, nullable=True)  # Indicateurs clés
    analysis_components = Column(JSON, nullable=True)  # Composants de l'analyse
    recommendations = Column(JSON, nullable=True)  # Recommandations
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = ({"schema": "public"},)
