from sqlalchemy import Column, Integer, String, Date, DECIMAL, BIGINT, TEXT, BOOLEAN, JSON, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class SymbolMetadata(Base):
    __tablename__ = "symbol_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, unique=True, index=True)
    company_name = Column(String(255), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    market_cap_category = Column(String(50))
    is_active = Column(BOOLEAN, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = ({"schema": "public"},)


class HistoricalData(Base):
    __tablename__ = "historical_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(DECIMAL(10, 4), nullable=False)
    high = Column(DECIMAL(10, 4), nullable=False)
    low = Column(DECIMAL(10, 4), nullable=False)
    close = Column(DECIMAL(10, 4), nullable=False)
    volume = Column(BIGINT, nullable=False)
    vwap = Column(DECIMAL(10, 4))
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = ({"schema": "public"},)


class SentimentData(Base):
    __tablename__ = "sentiment_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    news_count = Column(Integer, default=0)
    news_sentiment_score = Column(DECIMAL(5, 4), default=0.0)
    news_sentiment_std = Column(DECIMAL(5, 4), default=0.0)
    news_positive_count = Column(Integer, default=0)
    news_negative_count = Column(Integer, default=0)
    news_neutral_count = Column(Integer, default=0)
    top_news_title = Column(TEXT)
    top_news_sentiment = Column(DECIMAL(5, 4))
    top_news_url = Column(TEXT)
    short_interest_ratio = Column(DECIMAL(10, 4))
    short_interest_volume = Column(BIGINT)
    short_interest_date = Column(Date)
    short_volume = Column(BIGINT)
    short_exempt_volume = Column(BIGINT)
    total_volume = Column(BIGINT)
    short_volume_ratio = Column(DECIMAL(5, 4))
    sentiment_momentum_5d = Column(DECIMAL(5, 4))
    sentiment_momentum_20d = Column(DECIMAL(5, 4))
    sentiment_volatility_5d = Column(DECIMAL(5, 4))
    sentiment_relative_strength = Column(DECIMAL(5, 4))
    data_quality_score = Column(DECIMAL(3, 2), default=0.5)
    processing_notes = Column(TEXT)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = ({"schema": "public"},)


class TechnicalIndicators(Base):
    __tablename__ = "technical_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Moyennes mobiles
    sma_5 = Column(DECIMAL(10, 4))
    sma_10 = Column(DECIMAL(10, 4))
    sma_20 = Column(DECIMAL(10, 4))
    sma_50 = Column(DECIMAL(10, 4))
    sma_200 = Column(DECIMAL(10, 4))
    ema_5 = Column(DECIMAL(10, 4))
    ema_10 = Column(DECIMAL(10, 4))
    ema_20 = Column(DECIMAL(10, 4))
    ema_50 = Column(DECIMAL(10, 4))
    ema_200 = Column(DECIMAL(10, 4))
    
    # Indicateurs de momentum
    rsi_14 = Column(DECIMAL(5, 2))
    macd = Column(DECIMAL(10, 4))
    macd_signal = Column(DECIMAL(10, 4))
    macd_histogram = Column(DECIMAL(10, 4))
    stochastic_k = Column(DECIMAL(5, 2))
    stochastic_d = Column(DECIMAL(5, 2))
    williams_r = Column(DECIMAL(5, 2))
    roc = Column(DECIMAL(10, 4))
    cci = Column(DECIMAL(10, 4))
    
    # Bollinger Bands
    bb_upper = Column(DECIMAL(10, 4))
    bb_middle = Column(DECIMAL(10, 4))
    bb_lower = Column(DECIMAL(10, 4))
    bb_width = Column(DECIMAL(10, 4))
    bb_position = Column(DECIMAL(5, 4))
    
    # Volume
    obv = Column(DECIMAL(20, 0))
    volume_roc = Column(DECIMAL(10, 4))
    volume_sma_20 = Column(DECIMAL(20, 0))
    
    # ATR
    atr_14 = Column(DECIMAL(10, 4))
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = ({"schema": "public"},)


class SentimentIndicators(Base):
    __tablename__ = "sentiment_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Base Sentiment Indicators
    sentiment_score_normalized = Column(DECIMAL(10, 4))
    
    # Sentiment Momentum
    sentiment_momentum_1d = Column(DECIMAL(10, 4))
    sentiment_momentum_3d = Column(DECIMAL(10, 4))
    sentiment_momentum_7d = Column(DECIMAL(10, 4))
    sentiment_momentum_14d = Column(DECIMAL(10, 4))
    
    # Sentiment Volatility
    sentiment_volatility_3d = Column(DECIMAL(10, 4))
    sentiment_volatility_7d = Column(DECIMAL(10, 4))
    sentiment_volatility_14d = Column(DECIMAL(10, 4))
    sentiment_volatility_30d = Column(DECIMAL(10, 4))
    
    # Sentiment Moving Averages
    sentiment_sma_3 = Column(DECIMAL(10, 4))
    sentiment_sma_7 = Column(DECIMAL(10, 4))
    sentiment_sma_14 = Column(DECIMAL(10, 4))
    sentiment_sma_30 = Column(DECIMAL(10, 4))
    sentiment_ema_3 = Column(DECIMAL(10, 4))
    sentiment_ema_7 = Column(DECIMAL(10, 4))
    sentiment_ema_14 = Column(DECIMAL(10, 4))
    sentiment_ema_30 = Column(DECIMAL(10, 4))
    
    # Sentiment Oscillators
    sentiment_rsi_14 = Column(DECIMAL(10, 4))
    sentiment_macd = Column(DECIMAL(10, 4))
    sentiment_macd_signal = Column(DECIMAL(10, 4))
    sentiment_macd_histogram = Column(DECIMAL(10, 4))
    
    # News Volume Indicators
    news_volume_sma_7 = Column(DECIMAL(10, 4))
    news_volume_sma_14 = Column(DECIMAL(10, 4))
    news_volume_sma_30 = Column(DECIMAL(10, 4))
    news_volume_roc_7d = Column(DECIMAL(10, 4))
    news_volume_roc_14d = Column(DECIMAL(10, 4))
    
    # Sentiment Distribution Ratios
    news_positive_ratio = Column(DECIMAL(10, 4))
    news_negative_ratio = Column(DECIMAL(10, 4))
    news_neutral_ratio = Column(DECIMAL(10, 4))
    news_sentiment_quality = Column(DECIMAL(10, 4))
    
    # Short Interest Indicators
    short_interest_momentum_5d = Column(DECIMAL(10, 4))
    short_interest_momentum_10d = Column(DECIMAL(10, 4))
    short_interest_momentum_20d = Column(DECIMAL(10, 4))
    short_interest_volatility_7d = Column(DECIMAL(10, 4))
    short_interest_volatility_14d = Column(DECIMAL(10, 4))
    short_interest_volatility_30d = Column(DECIMAL(10, 4))
    short_interest_sma_7 = Column(DECIMAL(10, 4))
    short_interest_sma_14 = Column(DECIMAL(10, 4))
    short_interest_sma_30 = Column(DECIMAL(10, 4))
    
    # Short Volume Indicators
    short_volume_momentum_5d = Column(DECIMAL(10, 4))
    short_volume_momentum_10d = Column(DECIMAL(10, 4))
    short_volume_momentum_20d = Column(DECIMAL(10, 4))
    short_volume_volatility_7d = Column(DECIMAL(10, 4))
    short_volume_volatility_14d = Column(DECIMAL(10, 4))
    short_volume_volatility_30d = Column(DECIMAL(10, 4))
    
    # Composite Sentiment Indicators
    sentiment_strength_index = Column(DECIMAL(10, 4))
    market_sentiment_index = Column(DECIMAL(10, 4))
    sentiment_divergence = Column(DECIMAL(10, 4))
    sentiment_acceleration = Column(DECIMAL(10, 4))
    sentiment_trend_strength = Column(DECIMAL(10, 4))
    sentiment_quality_index = Column(DECIMAL(10, 4))
    sentiment_risk_score = Column(DECIMAL(10, 4))
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = ({"schema": "public"},)


class CorrelationMatrices(Base):
    __tablename__ = "correlation_matrices"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    correlation_type = Column(String(50), nullable=False, index=True)
    variable1 = Column(String(50), nullable=False)
    variable2 = Column(String(50), nullable=False)
    correlation_value = Column(DECIMAL(5, 4), nullable=False)
    correlation_method = Column(String(20), default='pearson')
    window_size = Column(Integer, default=20)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = ({"schema": "public"},)


class CrossAssetCorrelations(Base):
    __tablename__ = "cross_asset_correlations"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol1 = Column(String(10), nullable=False, index=True)
    symbol2 = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    correlation_type = Column(String(50), nullable=False, index=True)
    correlation_value = Column(DECIMAL(5, 4), nullable=False)
    correlation_method = Column(String(20), default='pearson')
    window_size = Column(Integer, default=20)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = ({"schema": "public"},)


class CorrelationFeatures(Base):
    __tablename__ = "correlation_features"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    feature_name = Column(String(100), nullable=False)
    feature_value = Column(DECIMAL(15, 8), nullable=False)
    feature_type = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = ({"schema": "public"},)


class TargetParameters(Base):
    __tablename__ = "target_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    parameter_name = Column(String(100), nullable=False)
    target_return_percentage = Column(DECIMAL(8, 4), nullable=False)  # Ex: 1.5 pour 1.5%
    time_horizon_days = Column(Integer, nullable=False)  # Ex: 7 pour 7 jours
    risk_tolerance = Column(String(20), default='medium')  # low, medium, high
    min_confidence_threshold = Column(DECIMAL(5, 4), default=0.7)  # Seuil de confiance minimum
    max_drawdown_percentage = Column(DECIMAL(8, 4), default=5.0)  # Drawdown maximum accepté
    is_active = Column(BOOLEAN, default=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = ({"schema": "public"},)


class MLModels(Base):
    __tablename__ = "ml_models"
    
    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(100), nullable=False)
    model_type = Column(String(50), nullable=False)
    model_version = Column(String(20), nullable=False, default="v1.0")
    symbol = Column(String(10), nullable=False, index=True)
    target_parameter_id = Column(Integer, ForeignKey('public.target_parameters.id'), nullable=True)
    model_parameters = Column(JSON)
    performance_metrics = Column(JSON)
    model_path = Column(TEXT)
    is_active = Column(BOOLEAN, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    
    __table_args__ = ({"schema": "public"},)


class MLPredictions(Base):
    __tablename__ = "ml_predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey('public.ml_models.id'), nullable=True)
    symbol = Column(String(10), nullable=False, index=True)
    prediction_date = Column(Date, nullable=False, index=True)
    prediction_value = Column(DECIMAL(15, 8), nullable=False)
    prediction_class = Column(String(50), nullable=True)
    confidence = Column(DECIMAL(5, 4), nullable=False)
    data_date_used = Column(Date, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    created_by = Column(String(100), nullable=True)
    
    __table_args__ = ({"schema": "public"},)


class TradingSignals(Base):
    __tablename__ = "trading_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    signal_type = Column(String(10), nullable=False, index=True)
    confidence = Column(DECIMAL(5, 4), nullable=False, index=True)
    target_price = Column(DECIMAL(10, 4))
    stop_loss = Column(DECIMAL(10, 4))
    take_profit = Column(DECIMAL(10, 4))
    horizon_days = Column(Integer, default=1)
    model_id = Column(Integer, ForeignKey('public.ml_models.id'), nullable=True)
    reasoning = Column(TEXT)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = ({"schema": "public"},)


class CorrelationAlerts(Base):
    __tablename__ = "correlation_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    alert_type = Column(String(50), nullable=False, index=True)
    alert_message = Column(TEXT, nullable=False)
    correlation_value = Column(DECIMAL(5, 4))
    threshold_value = Column(DECIMAL(5, 4))
    severity = Column(String(20), default='medium', index=True)
    is_resolved = Column(BOOLEAN, default=False, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = ({"schema": "public"},)
