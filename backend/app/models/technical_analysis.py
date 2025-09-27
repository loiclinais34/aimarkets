"""
Modèles de base de données pour l'analyse technique.

Ce module définit les modèles SQLAlchemy pour stocker
les signaux d'analyse technique.
"""

from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, Boolean, Text, JSON
from sqlalchemy.sql import func
from .database import Base


class TechnicalSignals(Base):
    """
    Modèle pour stocker les signaux d'analyse technique.
    """
    __tablename__ = "technical_signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    signal_type = Column(String(50), nullable=False)  # RSI, MACD, Bollinger, etc.
    signal_value = Column(DECIMAL(10, 6), nullable=False)
    signal_strength = Column(DECIMAL(3, 2), nullable=False)  # 0-1
    signal_direction = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    indicator_value = Column(DECIMAL(10, 6), nullable=True)  # Valeur de l'indicateur
    threshold_upper = Column(DECIMAL(10, 6), nullable=True)  # Seuil supérieur
    threshold_lower = Column(DECIMAL(10, 6), nullable=True)  # Seuil inférieur
    confidence = Column(DECIMAL(3, 2), nullable=True)  # Niveau de confiance
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = ({"schema": "public"},)


class CandlestickPatterns(Base):
    """
    Modèle pour stocker les patterns de chandeliers détectés.
    """
    __tablename__ = "candlestick_patterns"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    pattern_type = Column(String(50), nullable=False)  # Doji, Hammer, Engulfing, etc.
    pattern_direction = Column(String(10), nullable=False)  # BULLISH, BEARISH, NEUTRAL
    pattern_strength = Column(DECIMAL(3, 2), nullable=False)  # 0-1
    open_price = Column(DECIMAL(10, 4), nullable=False)
    high_price = Column(DECIMAL(10, 4), nullable=False)
    low_price = Column(DECIMAL(10, 4), nullable=False)
    close_price = Column(DECIMAL(10, 4), nullable=False)
    volume = Column(DECIMAL(15, 2), nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = ({"schema": "public"},)


class SupportResistanceLevels(Base):
    """
    Modèle pour stocker les niveaux de support et résistance.
    """
    __tablename__ = "support_resistance_levels"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    level_type = Column(String(20), nullable=False)  # SUPPORT, RESISTANCE
    price_level = Column(DECIMAL(10, 4), nullable=False)
    strength = Column(DECIMAL(3, 2), nullable=False)  # 0-1
    touches_count = Column(Integer, nullable=False, default=1)
    last_touch_date = Column(TIMESTAMP, nullable=True)
    is_active = Column(Boolean, default=True)
    level_source = Column(String(50), nullable=True)  # PIVOT, FIBONACCI, MANUAL
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = ({"schema": "public"},)


class TechnicalAnalysisSummary(Base):
    """
    Modèle pour stocker un résumé de l'analyse technique.
    """
    __tablename__ = "technical_analysis_summary"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    analysis_date = Column(TIMESTAMP, nullable=False, index=True)
    composite_signal = Column(String(10), nullable=False)  # BUY, SELL, HOLD
    signal_strength = Column(DECIMAL(3, 2), nullable=False)  # 0-1
    confidence_level = Column(DECIMAL(3, 2), nullable=False)  # 0-1
    total_indicators = Column(Integer, nullable=False)
    bullish_signals = Column(Integer, nullable=False, default=0)
    bearish_signals = Column(Integer, nullable=False, default=0)
    neutral_signals = Column(Integer, nullable=False, default=0)
    patterns_detected = Column(Integer, nullable=False, default=0)
    support_levels = Column(Integer, nullable=False, default=0)
    resistance_levels = Column(Integer, nullable=False, default=0)
    analysis_details = Column(JSON, nullable=True)  # Détails de l'analyse
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = ({"schema": "public"},)
