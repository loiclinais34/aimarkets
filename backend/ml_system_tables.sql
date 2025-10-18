-- ===========================================
-- TABLES POUR LE SYSTÈME ML SOPHISTIQUÉ
-- ===========================================

-- Table pour les indicateurs techniques avancés
CREATE TABLE IF NOT EXISTS advanced_technical_indicators (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    
    -- Indicateurs de tendance
    sma_5 DECIMAL(10, 4),
    sma_10 DECIMAL(10, 4),
    sma_20 DECIMAL(10, 4),
    sma_50 DECIMAL(10, 4),
    sma_200 DECIMAL(10, 4),
    ema_5 DECIMAL(10, 4),
    ema_10 DECIMAL(10, 4),
    ema_20 DECIMAL(10, 4),
    ema_50 DECIMAL(10, 4),
    ema_200 DECIMAL(10, 4),
    
    -- Indicateurs de momentum
    rsi_14 DECIMAL(5, 2),
    rsi_21 DECIMAL(5, 2),
    stochastic_k DECIMAL(5, 2),
    stochastic_d DECIMAL(5, 2),
    williams_r DECIMAL(5, 2),
    cci DECIMAL(8, 2),
    roc DECIMAL(8, 2),
    
    -- Indicateurs de volatilité
    bollinger_upper DECIMAL(10, 4),
    bollinger_middle DECIMAL(10, 4),
    bollinger_lower DECIMAL(10, 4),
    bollinger_width DECIMAL(8, 4),
    atr_14 DECIMAL(10, 4),
    volatility_20 DECIMAL(8, 4),
    
    -- Indicateurs de volume
    volume_sma_20 DECIMAL(15, 2),
    volume_ratio DECIMAL(8, 4),
    obv DECIMAL(15, 2),
    vwap DECIMAL(10, 4),
    
    -- Indicateurs MACD
    macd_line DECIMAL(10, 4),
    macd_signal DECIMAL(10, 4),
    macd_histogram DECIMAL(10, 4),
    
    -- Patterns de chandeliers
    doji BOOLEAN DEFAULT FALSE,
    hammer BOOLEAN DEFAULT FALSE,
    shooting_star BOOLEAN DEFAULT FALSE,
    engulfing_bullish BOOLEAN DEFAULT FALSE,
    engulfing_bearish BOOLEAN DEFAULT FALSE,
    
    -- Indicateurs de support/résistance
    support_level DECIMAL(10, 4),
    resistance_level DECIMAL(10, 4),
    pivot_point DECIMAL(10, 4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(symbol, date)
);

-- Table pour les features ML
CREATE TABLE IF NOT EXISTS ml_features (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    
    -- Features de prix
    price_change_1d DECIMAL(8, 4),
    price_change_5d DECIMAL(8, 4),
    price_change_20d DECIMAL(8, 4),
    price_volatility_20d DECIMAL(8, 4),
    
    -- Features techniques normalisées
    rsi_normalized DECIMAL(8, 4),
    macd_normalized DECIMAL(8, 4),
    bollinger_position DECIMAL(8, 4),
    volume_anomaly DECIMAL(8, 4),
    
    -- Features de marché
    market_cap_category VARCHAR(20), -- LARGE, MID, SMALL
    sector VARCHAR(50),
    beta DECIMAL(6, 4),
    
    -- Features de sentiment (si disponibles)
    sentiment_score DECIMAL(6, 4),
    news_sentiment DECIMAL(6, 4),
    social_sentiment DECIMAL(6, 4),
    
    -- Features de corrélation
    correlation_spy DECIMAL(6, 4),
    correlation_sector DECIMAL(6, 4),
    
    -- Features de timing
    day_of_week INTEGER,
    month INTEGER,
    quarter INTEGER,
    is_month_end BOOLEAN DEFAULT FALSE,
    is_quarter_end BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(symbol, date)
);

-- Table pour les modèles ML
CREATE TABLE IF NOT EXISTS ml_models_v2 (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL, -- RANDOM_FOREST, XGBOOST, LSTM, TRANSFORMER
    model_version VARCHAR(20) NOT NULL,
    
    -- Paramètres du modèle
    model_parameters JSONB,
    feature_columns JSONB,
    target_column VARCHAR(50),
    
    -- Métriques de performance
    training_score DECIMAL(6, 4),
    validation_score DECIMAL(6, 4),
    test_score DECIMAL(6, 4),
    cross_validation_scores JSONB,
    
    -- Métriques spécifiques au trading
    sharpe_ratio DECIMAL(8, 4),
    max_drawdown DECIMAL(8, 4),
    win_rate DECIMAL(6, 4),
    profit_factor DECIMAL(8, 4),
    
    -- Configuration d'entraînement
    training_data_start DATE,
    training_data_end DATE,
    validation_data_start DATE,
    validation_data_end DATE,
    test_data_start DATE,
    test_data_end DATE,
    
    -- Statut et métadonnées
    is_active BOOLEAN DEFAULT FALSE,
    is_production BOOLEAN DEFAULT FALSE,
    model_path TEXT,
    feature_importance JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(model_name, model_version)
);

-- Table pour les prédictions ML avancées
CREATE TABLE IF NOT EXISTS ml_predictions_v2 (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    model_id INTEGER REFERENCES ml_models_v2(id),
    
    -- Prédictions
    prediction_type VARCHAR(50) NOT NULL, -- PRICE_DIRECTION, RETURN_MAGNITUDE, VOLATILITY
    predicted_value DECIMAL(15, 8) NOT NULL,
    confidence DECIMAL(5, 4) NOT NULL,
    
    -- Prédictions probabilistes
    probability_buy_strong DECIMAL(5, 4),
    probability_buy_moderate DECIMAL(5, 4),
    probability_buy_weak DECIMAL(5, 4),
    probability_hold DECIMAL(5, 4),
    probability_sell_weak DECIMAL(5, 4),
    probability_sell_strong DECIMAL(5, 4),
    
    -- Features utilisées
    features_used JSONB,
    feature_values JSONB,
    
    -- Métadonnées
    prediction_horizon INTEGER, -- jours
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(symbol, date, model_id, prediction_type)
);

-- Table pour les simulations Monte Carlo
CREATE TABLE IF NOT EXISTS monte_carlo_simulations (
    id SERIAL PRIMARY KEY,
    simulation_name VARCHAR(100) NOT NULL,
    model_id INTEGER REFERENCES ml_models_v2(id),
    
    -- Paramètres de simulation
    simulation_parameters JSONB,
    num_simulations INTEGER NOT NULL,
    simulation_horizon INTEGER NOT NULL, -- jours
    
    -- Résultats de simulation
    results JSONB,
    statistics JSONB,
    
    -- Métriques de performance simulées
    avg_return DECIMAL(8, 4),
    std_return DECIMAL(8, 4),
    sharpe_ratio DECIMAL(8, 4),
    max_drawdown DECIMAL(8, 4),
    var_95 DECIMAL(8, 4),
    cvar_95 DECIMAL(8, 4),
    
    -- Configuration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'RUNNING', -- RUNNING, COMPLETED, FAILED
    
    UNIQUE(simulation_name, model_id)
);

-- Table pour les recommandations ML sophistiquées
CREATE TABLE IF NOT EXISTS ml_recommendations_v2 (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    model_id INTEGER REFERENCES ml_models_v2(id),
    
    -- Recommandation principale
    recommendation VARCHAR(20) NOT NULL, -- BUY_STRONG, BUY_MODERATE, etc.
    confidence DECIMAL(5, 4) NOT NULL,
    
    -- Prédictions détaillées
    predicted_return_1d DECIMAL(8, 4),
    predicted_return_5d DECIMAL(8, 4),
    predicted_return_20d DECIMAL(8, 4),
    predicted_volatility DECIMAL(8, 4),
    
    -- Niveaux de prix
    target_price DECIMAL(10, 4),
    stop_loss DECIMAL(10, 4),
    take_profit DECIMAL(10, 4),
    
    -- Métriques de risque
    risk_score DECIMAL(5, 4),
    reward_risk_ratio DECIMAL(8, 4),
    position_size DECIMAL(8, 4),
    
    -- Justification
    reasoning TEXT,
    key_factors JSONB,
    
    -- Validation
    is_validated BOOLEAN DEFAULT FALSE,
    validation_score DECIMAL(5, 4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(symbol, date, model_id)
);

-- Table pour les backtests avancés
CREATE TABLE IF NOT EXISTS advanced_backtests (
    id SERIAL PRIMARY KEY,
    backtest_name VARCHAR(100) NOT NULL,
    model_id INTEGER REFERENCES ml_models_v2(id),
    
    -- Configuration du backtest
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    initial_capital DECIMAL(15, 2) NOT NULL,
    transaction_costs DECIMAL(6, 4) DEFAULT 0.001,
    
    -- Résultats du backtest
    final_capital DECIMAL(15, 2),
    total_return DECIMAL(8, 4),
    annualized_return DECIMAL(8, 4),
    volatility DECIMAL(8, 4),
    sharpe_ratio DECIMAL(8, 4),
    sortino_ratio DECIMAL(8, 4),
    max_drawdown DECIMAL(8, 4),
    calmar_ratio DECIMAL(8, 4),
    
    -- Métriques de trading
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    win_rate DECIMAL(6, 4),
    avg_win DECIMAL(8, 4),
    avg_loss DECIMAL(8, 4),
    profit_factor DECIMAL(8, 4),
    
    -- Détails des trades
    trades_data JSONB,
    equity_curve JSONB,
    
    -- Configuration
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'RUNNING',
    
    UNIQUE(backtest_name, model_id)
);

-- Index pour optimiser les performances
CREATE INDEX IF NOT EXISTS idx_advanced_technical_indicators_symbol_date 
ON advanced_technical_indicators(symbol, date);

CREATE INDEX IF NOT EXISTS idx_ml_features_symbol_date 
ON ml_features(symbol, date);

CREATE INDEX IF NOT EXISTS idx_ml_predictions_v2_symbol_date 
ON ml_predictions_v2(symbol, date);

CREATE INDEX IF NOT EXISTS idx_ml_recommendations_v2_symbol_date 
ON ml_recommendations_v2(symbol, date);

CREATE INDEX IF NOT EXISTS idx_ml_recommendations_v2_recommendation 
ON ml_recommendations_v2(recommendation);

CREATE INDEX IF NOT EXISTS idx_advanced_backtests_model_id 
ON advanced_backtests(model_id);

-- Commentaires sur les tables
COMMENT ON TABLE advanced_technical_indicators IS 'Indicateurs techniques avancés calculés pour chaque symbole et date';
COMMENT ON TABLE ml_features IS 'Features normalisées pour les modèles ML';
COMMENT ON TABLE ml_models_v2 IS 'Modèles ML sophistiqués avec métriques de performance';
COMMENT ON TABLE ml_predictions_v2 IS 'Prédictions probabilistes des modèles ML';
COMMENT ON TABLE monte_carlo_simulations IS 'Simulations Monte Carlo pour tester les stratégies';
COMMENT ON TABLE ml_recommendations_v2 IS 'Recommandations sophistiquées basées sur ML';
COMMENT ON TABLE advanced_backtests IS 'Backtests avancés avec métriques détaillées';
