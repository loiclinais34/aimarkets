"""
Modèles pour la détection de bulles spéculatives
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Date, JSON, Index, DECIMAL
from sqlalchemy.sql import func
from app.core.database import Base


class BubbleIndicators(Base):
    """
    Modèle pour stocker les indicateurs de bulle spéculative
    """
    __tablename__ = "bubble_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    analysis_date = Column(Date, nullable=False, index=True)
    
    # Score composite de bulle (0-100)
    bubble_score = Column(DECIMAL(5, 2), nullable=False)
    bubble_level = Column(String(20), nullable=False)  # NORMAL, WATCH, RISK, PROBABLE, CRITICAL
    
    # Scores par catégorie (0-100)
    valuation_score = Column(DECIMAL(5, 2), nullable=False)
    momentum_score = Column(DECIMAL(5, 2), nullable=False)
    statistical_score = Column(DECIMAL(5, 2), nullable=False)
    sentiment_score = Column(DECIMAL(5, 2), nullable=False)
    
    # Indicateurs de valorisation
    pe_ratio = Column(DECIMAL(10, 2), nullable=True)
    ps_ratio = Column(DECIMAL(10, 2), nullable=True)
    pb_ratio = Column(DECIMAL(10, 2), nullable=True)
    peg_ratio = Column(DECIMAL(10, 2), nullable=True)
    
    # Écarts par rapport aux moyennes historiques
    pe_vs_historical_avg = Column(DECIMAL(10, 2), nullable=True)  # % écart
    ps_vs_historical_avg = Column(DECIMAL(10, 2), nullable=True)
    pb_vs_historical_avg = Column(DECIMAL(10, 2), nullable=True)
    
    # Écarts par rapport au secteur
    pe_vs_sector_avg = Column(DECIMAL(10, 2), nullable=True)
    ps_vs_sector_avg = Column(DECIMAL(10, 2), nullable=True)
    pb_vs_sector_avg = Column(DECIMAL(10, 2), nullable=True)
    
    # Indicateurs de momentum
    price_growth_30d = Column(DECIMAL(10, 4), nullable=True)  # % gain sur 30 jours
    price_growth_90d = Column(DECIMAL(10, 4), nullable=True)  # % gain sur 90 jours
    price_growth_180d = Column(DECIMAL(10, 4), nullable=True)  # % gain sur 180 jours
    price_acceleration = Column(DECIMAL(10, 6), nullable=True)  # Dérivée seconde
    
    distance_from_sma50 = Column(DECIMAL(10, 4), nullable=True)  # % écart avec SMA 50
    distance_from_sma200 = Column(DECIMAL(10, 4), nullable=True)  # % écart avec SMA 200
    rsi_14d = Column(DECIMAL(5, 2), nullable=True)
    days_above_rsi_80 = Column(Integer, nullable=True)  # Nombre de jours consécutifs avec RSI > 80
    
    # Indicateurs de volume
    volume_vs_avg = Column(DECIMAL(10, 4), nullable=True)  # Ratio volume actuel / moyenne 30j
    volume_trend = Column(String(20), nullable=True)  # INCREASING, STABLE, DECREASING
    volume_acceleration = Column(DECIMAL(10, 6), nullable=True)
    
    # Indicateurs statistiques
    gsadf_statistic = Column(DECIMAL(10, 4), nullable=True)  # Test GSADF pour bulle explosive
    price_zscore = Column(DECIMAL(10, 4), nullable=True)  # Z-score du prix normalisé
    volatility_ratio = Column(DECIMAL(10, 4), nullable=True)  # Volatilité actuelle / historique
    
    sharpe_ratio = Column(DECIMAL(10, 4), nullable=True)
    returns_skewness = Column(DECIMAL(10, 4), nullable=True)  # Asymétrie des rendements
    returns_kurtosis = Column(DECIMAL(10, 4), nullable=True)  # Kurtosis (queues épaisses)
    
    # Régime de marché
    market_regime = Column(String(20), nullable=True)  # NORMAL, BUBBLE, CRASH
    regime_probability = Column(DECIMAL(5, 4), nullable=True)  # Probabilité du régime actuel
    days_in_regime = Column(Integer, nullable=True)  # Durée dans le régime actuel
    
    # Corrélation sectorielle
    sector_correlation = Column(DECIMAL(5, 4), nullable=True)  # Corrélation avec secteur tech
    sector_correlation_strength = Column(String(20), nullable=True)  # LOW, MEDIUM, HIGH
    
    # Sentiment et comportement
    sentiment_extreme_days = Column(Integer, nullable=True)  # Jours consécutifs avec sentiment > 0.8
    sentiment_fundamental_divergence = Column(DECIMAL(10, 4), nullable=True)  # Divergence sentiment/fondamentaux
    
    # Métadonnées détaillées (JSON)
    valuation_details = Column(JSON, nullable=True)
    momentum_details = Column(JSON, nullable=True)
    statistical_details = Column(JSON, nullable=True)
    sentiment_details = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Index pour requêtes fréquentes
    __table_args__ = (
        Index('idx_bubble_symbol_date', 'symbol', 'analysis_date'),
        Index('idx_bubble_score', 'bubble_score'),
        Index('idx_bubble_level', 'bubble_level'),
        Index('idx_bubble_date', 'analysis_date'),
    )
    
    def __repr__(self):
        return f"<BubbleIndicators(symbol={self.symbol}, date={self.analysis_date}, score={self.bubble_score}, level={self.bubble_level})>"
