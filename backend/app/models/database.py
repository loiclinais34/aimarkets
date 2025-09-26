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
    sentiment_reasoning = Column(TEXT)
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
    bb_position = Column(DECIMAL(10, 4))
    
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
    
    # Relation avec MLModels
    ml_models = relationship("MLModels", back_populates="target_parameter")
    
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
    
    # Relation avec TargetParameters
    target_parameter = relationship("TargetParameters", back_populates="ml_models")
    
    # Relation avec BacktestRun
    backtest_runs = relationship("BacktestRun", back_populates="model")
    
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
    screener_run_id = Column(Integer, ForeignKey('public.screener_runs.id'), nullable=True, index=True)
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


class ScreenerConfig(Base):
    __tablename__ = "screener_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    target_return_percentage = Column(DECIMAL(5, 2), nullable=False)
    time_horizon_days = Column(Integer, nullable=False)
    risk_tolerance = Column(DECIMAL(3, 2), nullable=False)  # 0.1 to 1.0
    confidence_threshold = Column(DECIMAL(3, 2), nullable=False)  # Calculated from risk_tolerance
    is_active = Column(BOOLEAN, default=True)
    created_by = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    __table_args__ = ({"schema": "public"},)


class ScreenerRun(Base):
    __tablename__ = "screener_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    screener_config_id = Column(Integer, ForeignKey('public.screener_configs.id'), nullable=False)
    run_date = Column(Date, nullable=False, index=True)
    total_symbols = Column(Integer, nullable=False)
    successful_models = Column(Integer, nullable=False)
    opportunities_found = Column(Integer, nullable=False)
    execution_time_seconds = Column(Integer, nullable=False)
    status = Column(String(50), nullable=False)  # 'running', 'completed', 'failed'
    error_message = Column(TEXT)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = ({"schema": "public"},)


class ScreenerResult(Base):
    __tablename__ = "screener_results"
    
    id = Column(Integer, primary_key=True, index=True)
    screener_run_id = Column(Integer, ForeignKey('public.screener_runs.id'), nullable=False)
    symbol = Column(String(10), nullable=False, index=True)
    model_id = Column(Integer, ForeignKey('public.ml_models.id'), nullable=False)
    prediction = Column(DECIMAL(10, 6), nullable=False)
    confidence = Column(DECIMAL(5, 4), nullable=False)
    rank = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = ({"schema": "public"},)


# ==================== BACKTESTING MODELS ====================

class BacktestRun(Base):
    __tablename__ = "backtest_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(TEXT)
    model_id = Column(Integer, ForeignKey('public.ml_models.id'), nullable=False)
    strategy_id = Column(Integer, ForeignKey('public.trading_strategies.id'), nullable=True)
    start_date = Column(Date, nullable=False, index=True)
    end_date = Column(Date, nullable=False, index=True)
    initial_capital = Column(DECIMAL(15, 2), nullable=False, default=100000.00)
    position_size_percentage = Column(DECIMAL(5, 2), nullable=False, default=10.00)  # % of capital per trade
    commission_rate = Column(DECIMAL(5, 4), nullable=False, default=0.001)  # 0.1% commission
    slippage_rate = Column(DECIMAL(5, 4), nullable=False, default=0.0005)  # 0.05% slippage
    confidence_threshold = Column(DECIMAL(3, 2), nullable=False, default=0.60)  # Minimum confidence for trades
    max_positions = Column(Integer, nullable=False, default=10)  # Maximum concurrent positions
    status = Column(String(50), nullable=False, default='pending')  # 'pending', 'running', 'completed', 'failed'
    created_by = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
    error_message = Column(TEXT)
    
    # Relationships
    model = relationship("MLModels", back_populates="backtest_runs")
    trades = relationship("BacktestTrade", back_populates="backtest_run")
    metrics = relationship("BacktestMetrics", back_populates="backtest_run")
    strategy = relationship("TradingStrategy", back_populates="backtest_runs")
    strategy_performance = relationship("StrategyPerformance", back_populates="backtest_run")
    
    __table_args__ = ({"schema": "public"},)


class BacktestTrade(Base):
    __tablename__ = "backtest_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_run_id = Column(Integer, ForeignKey('public.backtest_runs.id'), nullable=False)
    symbol = Column(String(10), nullable=False, index=True)
    entry_date = Column(Date, nullable=False, index=True)
    exit_date = Column(Date, nullable=False, index=True)
    entry_price = Column(DECIMAL(10, 4), nullable=False)
    exit_price = Column(DECIMAL(10, 4), nullable=False)
    quantity = Column(Integer, nullable=False)
    position_type = Column(String(10), nullable=False)  # 'long', 'short'
    entry_confidence = Column(DECIMAL(5, 4), nullable=False)
    exit_reason = Column(String(50), nullable=False)  # 'target_hit', 'stop_loss', 'timeout', 'signal_reversal'
    gross_pnl = Column(DECIMAL(15, 2), nullable=False)
    commission = Column(DECIMAL(10, 2), nullable=False)
    slippage = Column(DECIMAL(10, 2), nullable=False)
    net_pnl = Column(DECIMAL(15, 2), nullable=False)
    return_percentage = Column(DECIMAL(8, 4), nullable=False)
    holding_days = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    backtest_run = relationship("BacktestRun", back_populates="trades")
    
    __table_args__ = ({"schema": "public"},)


class BacktestMetrics(Base):
    __tablename__ = "backtest_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_run_id = Column(Integer, ForeignKey('public.backtest_runs.id'), nullable=False, unique=True)
    
    # Performance Metrics
    total_return = Column(DECIMAL(10, 4), nullable=False)  # Total return percentage
    annualized_return = Column(DECIMAL(10, 4), nullable=False)
    total_trades = Column(Integer, nullable=False)
    winning_trades = Column(Integer, nullable=False)
    losing_trades = Column(Integer, nullable=False)
    win_rate = Column(DECIMAL(10, 4), nullable=False)  # Percentage of winning trades
    
    # Risk Metrics
    max_drawdown = Column(DECIMAL(10, 4), nullable=False)  # Maximum drawdown percentage
    max_drawdown_duration = Column(Integer, nullable=False)  # Days in max drawdown
    volatility = Column(DECIMAL(10, 4), nullable=False)  # Annualized volatility
    sharpe_ratio = Column(DECIMAL(10, 4), nullable=False)
    sortino_ratio = Column(DECIMAL(10, 4), nullable=False)
    
    # Trade Metrics
    avg_return_per_trade = Column(DECIMAL(10, 4), nullable=False)
    avg_winning_trade = Column(DECIMAL(10, 4), nullable=False)
    avg_losing_trade = Column(DECIMAL(10, 4), nullable=False)
    profit_factor = Column(DECIMAL(15, 4), nullable=False)  # Gross profit / Gross loss
    avg_holding_period = Column(DECIMAL(10, 2), nullable=False)  # Average days per trade
    
    # Capital Metrics
    final_capital = Column(DECIMAL(15, 2), nullable=False)
    max_capital = Column(DECIMAL(15, 2), nullable=False)
    min_capital = Column(DECIMAL(15, 2), nullable=False)
    
    # Additional Metrics
    calmar_ratio = Column(DECIMAL(15, 4), nullable=False)  # Annualized return / Max drawdown
    recovery_factor = Column(DECIMAL(15, 4), nullable=False)  # Net profit / Max drawdown
    expectancy = Column(DECIMAL(10, 4), nullable=False)  # Expected value per trade
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    backtest_run = relationship("BacktestRun", back_populates="metrics")
    
    __table_args__ = ({"schema": "public"},)


class BacktestEquityCurve(Base):
    __tablename__ = "backtest_equity_curves"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_run_id = Column(Integer, ForeignKey('public.backtest_runs.id'), nullable=False)
    date = Column(Date, nullable=False, index=True)
    equity_value = Column(DECIMAL(15, 2), nullable=False)
    drawdown = Column(DECIMAL(8, 4), nullable=False)  # Current drawdown percentage
    daily_return = Column(DECIMAL(8, 4), nullable=False)  # Daily return percentage
    cumulative_return = Column(DECIMAL(8, 4), nullable=False)  # Cumulative return percentage
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    __table_args__ = ({"schema": "public"},)


# ==================== TRADING STRATEGIES MODELS ====================

class TradingStrategy(Base):
    __tablename__ = "trading_strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(TEXT)
    strategy_type = Column(String(50), nullable=False)  # 'momentum', 'mean_reversion', 'breakout', 'scalping', 'swing'
    parameters = Column(JSON)  # Paramètres spécifiques à la stratégie
    is_active = Column(BOOLEAN, default=True)
    created_by = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    # Relationships
    backtest_runs = relationship("BacktestRun", back_populates="strategy")
    rules = relationship("StrategyRule", back_populates="strategy")
    parameters_rel = relationship("StrategyParameter", back_populates="strategy")
    performance = relationship("StrategyPerformance", back_populates="strategy")
    
    __table_args__ = ({"schema": "public"},)


class StrategyRule(Base):
    __tablename__ = "strategy_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey('public.trading_strategies.id'), nullable=False)
    rule_type = Column(String(50), nullable=False)  # 'entry', 'exit', 'position_sizing', 'risk_management'
    rule_name = Column(String(255), nullable=False)
    rule_condition = Column(TEXT, nullable=False)  # Condition logique
    rule_action = Column(TEXT, nullable=False)  # Action à exécuter
    priority = Column(Integer, nullable=False, default=1)  # Ordre d'exécution
    is_active = Column(BOOLEAN, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    strategy = relationship("TradingStrategy", back_populates="rules")
    
    __table_args__ = ({"schema": "public"},)


class StrategyParameter(Base):
    __tablename__ = "strategy_parameters"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey('public.trading_strategies.id'), nullable=False)
    parameter_name = Column(String(100), nullable=False)
    parameter_type = Column(String(50), nullable=False)  # 'float', 'int', 'boolean', 'string', 'choice'
    default_value = Column(TEXT, nullable=False)
    min_value = Column(DECIMAL(15, 4))
    max_value = Column(DECIMAL(15, 4))
    choices = Column(JSON)  # Pour les paramètres de type 'choice'
    description = Column(TEXT)
    is_required = Column(BOOLEAN, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    strategy = relationship("TradingStrategy", back_populates="parameters_rel")
    
    __table_args__ = ({"schema": "public"},)


class StrategyPerformance(Base):
    __tablename__ = "strategy_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_id = Column(Integer, ForeignKey('public.trading_strategies.id'), nullable=False)
    backtest_run_id = Column(Integer, ForeignKey('public.backtest_runs.id'), nullable=False)
    
    # Métriques spécifiques à la stratégie
    strategy_score = Column(DECIMAL(10, 4), nullable=False)  # Score global de la stratégie
    rule_effectiveness = Column(JSON)  # Efficacité de chaque règle
    parameter_sensitivity = Column(JSON)  # Sensibilité aux paramètres
    market_conditions = Column(JSON)  # Conditions de marché optimales
    
    # Métriques comparatives
    benchmark_return = Column(DECIMAL(10, 4))  # Retour du benchmark (S&P 500)
    alpha = Column(DECIMAL(10, 4))  # Alpha de la stratégie
    beta = Column(DECIMAL(10, 4))  # Beta de la stratégie
    information_ratio = Column(DECIMAL(10, 4))  # Ratio d'information
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    strategy = relationship("TradingStrategy", back_populates="performance")
    backtest_run = relationship("BacktestRun", back_populates="strategy_performance")
    
    __table_args__ = ({"schema": "public"},)
