"""
Modèles de base de données pour les signaux avancés.

Ce module définit les modèles SQLAlchemy pour stocker l'historique
des signaux, leurs performances et les métriques associées.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

Base = declarative_base()


class AdvancedSignal(Base):
    """
    Modèle pour stocker les signaux avancés générés.
    """
    __tablename__ = "advanced_signals"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    signal_type = Column(String(20), nullable=False)  # STRONG_BUY, BUY, etc.
    score = Column(Float, nullable=False)  # 0-100
    confidence = Column(Float, nullable=False)  # 0-1
    confidence_level = Column(String(20), nullable=False)  # VERY_HIGH, HIGH, etc.
    strength = Column(Float, nullable=False)  # 0-1
    risk_level = Column(String(20), nullable=False, default="MEDIUM")
    time_horizon = Column(String(20), nullable=False, default="SHORT_TERM")
    reasoning = Column(Text, nullable=True)
    indicators_used = Column(JSON, nullable=True)  # Liste des indicateurs utilisés
    individual_signals = Column(JSON, nullable=True)  # Détails des signaux individuels
    ml_signal = Column(JSON, nullable=True)  # Signal ML intégré
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    signal_performance = relationship("SignalPerformance", back_populates="signal")

    __table_args__ = ({"schema": "public"},)


class SignalPerformance(Base):
    """
    Modèle pour stocker les performances des signaux.
    """
    __tablename__ = "signal_performance"

    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, ForeignKey('public.advanced_signals.id'), nullable=False)
    symbol = Column(String(10), nullable=False, index=True)
    entry_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    entry_date = Column(DateTime, nullable=True)
    exit_date = Column(DateTime, nullable=True)
    return_percentage = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    holding_period_days = Column(Integer, nullable=True)
    was_profitable = Column(Boolean, nullable=True)
    performance_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    signal = relationship("AdvancedSignal", back_populates="signal_performance")

    __table_args__ = ({"schema": "public"},)


class SignalMetrics(Base):
    """
    Modèle pour stocker les métriques agrégées des signaux.
    """
    __tablename__ = "signal_metrics"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    total_signals = Column(Integer, nullable=False, default=0)
    buy_signals = Column(Integer, nullable=False, default=0)
    sell_signals = Column(Integer, nullable=False, default=0)
    hold_signals = Column(Integer, nullable=False, default=0)
    strong_buy_signals = Column(Integer, nullable=False, default=0)
    strong_sell_signals = Column(Integer, nullable=False, default=0)
    avg_confidence = Column(Float, nullable=False, default=0.0)
    avg_score = Column(Float, nullable=False, default=0.0)
    avg_strength = Column(Float, nullable=False, default=0.0)
    profitable_signals = Column(Integer, nullable=False, default=0)
    total_return = Column(Float, nullable=False, default=0.0)
    max_drawdown = Column(Float, nullable=False, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=False, default=0.0)
    avg_holding_period = Column(Float, nullable=True)
    metrics_data = Column(JSON, nullable=True)  # Métriques supplémentaires
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = ({"schema": "public"},)


class SignalConfiguration(Base):
    """
    Modèle pour stocker les configurations des générateurs de signaux.
    """
    __tablename__ = "signal_configurations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    weights = Column(JSON, nullable=False)  # Poids des indicateurs
    scoring_thresholds = Column(JSON, nullable=False)  # Seuils de scoring
    confidence_thresholds = Column(JSON, nullable=False)  # Seuils de confiance
    ml_integration = Column(JSON, nullable=True)  # Configuration ML
    is_active = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(100), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = ({"schema": "public"},)


class SignalBacktest(Base):
    """
    Modèle pour stocker les résultats de backtesting des signaux.
    """
    __tablename__ = "signal_backtests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    symbol = Column(String(10), nullable=False, index=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False, default=10000.0)
    final_capital = Column(Float, nullable=True)
    total_return = Column(Float, nullable=True)
    annualized_return = Column(Float, nullable=True)
    max_drawdown = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    win_rate = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    total_trades = Column(Integer, nullable=True)
    winning_trades = Column(Integer, nullable=True)
    losing_trades = Column(Integer, nullable=True)
    avg_win = Column(Float, nullable=True)
    avg_loss = Column(Float, nullable=True)
    largest_win = Column(Float, nullable=True)
    largest_loss = Column(Float, nullable=True)
    avg_holding_period = Column(Float, nullable=True)
    backtest_data = Column(JSON, nullable=True)  # Données détaillées du backtest
    configuration_id = Column(Integer, ForeignKey('public.signal_configurations.id'), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relations
    configuration = relationship("SignalConfiguration")

    __table_args__ = ({"schema": "public"},)
