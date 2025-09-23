-- Script d'initialisation de la base de données aimarkets

-- Extension pour les fonctions de corrélation
CREATE EXTENSION IF NOT EXISTS tablefunc;

-- Table des métadonnées des symboles
CREATE TABLE IF NOT EXISTS symbol_metadata (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL UNIQUE,
    company_name VARCHAR(255) NOT NULL,
    sector VARCHAR(100),
    industry VARCHAR(100),
    market_cap_category VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table des données historiques
CREATE TABLE IF NOT EXISTS historical_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10, 4) NOT NULL,
    high DECIMAL(10, 4) NOT NULL,
    low DECIMAL(10, 4) NOT NULL,
    close DECIMAL(10, 4) NOT NULL,
    volume BIGINT NOT NULL,
    vwap DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

-- Table des données de sentiment
CREATE TABLE IF NOT EXISTS sentiment_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    news_count INTEGER DEFAULT 0,
    news_sentiment_score DECIMAL(15, 8) DEFAULT 0.0,
    news_sentiment_std DECIMAL(15, 8) DEFAULT 0.0,
    news_positive_count INTEGER DEFAULT 0,
    news_negative_count INTEGER DEFAULT 0,
    news_neutral_count INTEGER DEFAULT 0,
    top_news_title TEXT,
    top_news_sentiment DECIMAL(15, 8),
    top_news_url TEXT,
    short_interest_ratio DECIMAL(15, 8),
    short_interest_volume BIGINT,
    short_interest_date DATE,
    short_volume BIGINT,
    short_exempt_volume BIGINT,
    total_volume BIGINT,
    short_volume_ratio DECIMAL(15, 8),
    sentiment_momentum_5d DECIMAL(15, 8),
    sentiment_momentum_20d DECIMAL(15, 8),
    sentiment_volatility_5d DECIMAL(15, 8),
    sentiment_relative_strength DECIMAL(15, 8),
    data_quality_score DECIMAL(3, 2) DEFAULT 0.5,
    processing_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

-- Table des indicateurs techniques
CREATE TABLE IF NOT EXISTS technical_indicators (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    -- Moyennes mobiles
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
    macd DECIMAL(10, 4),
    macd_signal DECIMAL(10, 4),
    macd_histogram DECIMAL(10, 4),
    stochastic_k DECIMAL(5, 2),
    stochastic_d DECIMAL(5, 2),
    williams_r DECIMAL(5, 2),
    roc DECIMAL(10, 4),
    cci DECIMAL(10, 4),
    -- Bollinger Bands
    bb_upper DECIMAL(10, 4),
    bb_middle DECIMAL(10, 4),
    bb_lower DECIMAL(10, 4),
    bb_width DECIMAL(10, 4),
    bb_position DECIMAL(5, 4),
    -- Volume
    obv DECIMAL(20, 0),
    volume_roc DECIMAL(10, 4),
    volume_sma_20 DECIMAL(20, 0),
    -- ATR
    atr_14 DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

-- Table des corrélations
CREATE TABLE IF NOT EXISTS correlation_matrices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    correlation_type VARCHAR(50) NOT NULL,
    variable1 VARCHAR(50) NOT NULL,
    variable2 VARCHAR(50) NOT NULL,
    correlation_value DECIMAL(5, 4) NOT NULL,
    correlation_method VARCHAR(20) DEFAULT 'pearson',
    window_size INTEGER DEFAULT 20,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date, correlation_type, variable1, variable2, correlation_method, window_size)
);

-- Table des corrélations cross-asset
CREATE TABLE IF NOT EXISTS cross_asset_correlations (
    id SERIAL PRIMARY KEY,
    symbol1 VARCHAR(10) NOT NULL,
    symbol2 VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    correlation_type VARCHAR(50) NOT NULL,
    correlation_value DECIMAL(5, 4) NOT NULL,
    correlation_method VARCHAR(20) DEFAULT 'pearson',
    window_size INTEGER DEFAULT 20,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol1, symbol2, date, correlation_type, correlation_method, window_size)
);

-- Table des features de corrélation
CREATE TABLE IF NOT EXISTS correlation_features (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    feature_value DECIMAL(15, 8) NOT NULL,
    feature_type VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date, feature_name)
);

-- Table des paramètres de cible de rentabilité
CREATE TABLE IF NOT EXISTS target_parameters (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) NOT NULL,
    parameter_name VARCHAR(100) NOT NULL,
    target_return_percentage DECIMAL(8, 4) NOT NULL, -- Ex: 1.5 pour 1.5%
    time_horizon_days INTEGER NOT NULL, -- Ex: 7 pour 7 jours
    risk_tolerance VARCHAR(20) DEFAULT 'medium', -- low, medium, high
    min_confidence_threshold DECIMAL(5, 4) DEFAULT 0.7, -- Seuil de confiance minimum
    max_drawdown_percentage DECIMAL(8, 4) DEFAULT 5.0, -- Drawdown maximum accepté
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, parameter_name)
);

-- Table des modèles ML
CREATE TABLE IF NOT EXISTS ml_models (
    id SERIAL PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    model_type VARCHAR(50) NOT NULL,
    model_version VARCHAR(20) NOT NULL,
    model_parameters JSONB,
    training_data_start DATE,
    training_data_end DATE,
    validation_score DECIMAL(5, 4),
    test_score DECIMAL(5, 4),
    model_path TEXT,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_name, model_version)
);

-- Table des prédictions ML
CREATE TABLE IF NOT EXISTS ml_predictions (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    model_id INTEGER REFERENCES ml_models(id),
    prediction_type VARCHAR(50) NOT NULL,
    prediction_value DECIMAL(15, 8) NOT NULL,
    confidence DECIMAL(5, 4) NOT NULL,
    features_used JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date, model_id, prediction_type)
);

-- Table des signaux de trading
CREATE TABLE IF NOT EXISTS trading_signals (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    signal_type VARCHAR(10) NOT NULL, -- BUY, SELL, HOLD
    confidence DECIMAL(5, 4) NOT NULL,
    target_price DECIMAL(10, 4),
    stop_loss DECIMAL(10, 4),
    take_profit DECIMAL(10, 4),
    horizon_days INTEGER DEFAULT 1,
    model_id INTEGER REFERENCES ml_models(id),
    reasoning TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date, signal_type, model_id)
);

-- Table des alertes
CREATE TABLE IF NOT EXISTS correlation_alerts (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    alert_message TEXT NOT NULL,
    correlation_value DECIMAL(5, 4),
    threshold_value DECIMAL(5, 4),
    severity VARCHAR(20) DEFAULT 'medium',
    is_resolved BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index pour optimiser les performances
CREATE INDEX IF NOT EXISTS idx_historical_data_symbol_date ON historical_data(symbol, date);
CREATE INDEX IF NOT EXISTS idx_sentiment_data_symbol_date ON sentiment_data(symbol, date);
CREATE INDEX IF NOT EXISTS idx_technical_indicators_symbol_date ON technical_indicators(symbol, date);
CREATE INDEX IF NOT EXISTS idx_correlation_matrices_symbol_date ON correlation_matrices(symbol, date);
CREATE INDEX IF NOT EXISTS idx_cross_asset_correlations_symbols_date ON cross_asset_correlations(symbol1, symbol2, date);
CREATE INDEX IF NOT EXISTS idx_ml_predictions_symbol_date ON ml_predictions(symbol, date);
CREATE INDEX IF NOT EXISTS idx_trading_signals_symbol_date ON trading_signals(symbol, date);
CREATE INDEX IF NOT EXISTS idx_target_parameters_user_id ON target_parameters(user_id);
CREATE INDEX IF NOT EXISTS idx_target_parameters_active ON target_parameters(is_active);

-- Index pour les corrélations
CREATE INDEX IF NOT EXISTS idx_correlation_matrices_type ON correlation_matrices(correlation_type);
CREATE INDEX IF NOT EXISTS idx_correlation_matrices_variables ON correlation_matrices(variable1, variable2);
CREATE INDEX IF NOT EXISTS idx_cross_asset_correlations_type ON cross_asset_correlations(correlation_type);

-- Index pour les signaux
CREATE INDEX IF NOT EXISTS idx_trading_signals_type ON trading_signals(signal_type);
CREATE INDEX IF NOT EXISTS idx_trading_signals_confidence ON trading_signals(confidence);
CREATE INDEX IF NOT EXISTS idx_trading_signals_date ON trading_signals(date);

-- Index pour les métadonnées des symboles
CREATE INDEX IF NOT EXISTS idx_symbol_metadata_symbol ON symbol_metadata(symbol);
CREATE INDEX IF NOT EXISTS idx_symbol_metadata_sector ON symbol_metadata(sector);
CREATE INDEX IF NOT EXISTS idx_symbol_metadata_active ON symbol_metadata(is_active);

-- Index pour les alertes
CREATE INDEX IF NOT EXISTS idx_correlation_alerts_symbol_date ON correlation_alerts(symbol, date);
CREATE INDEX IF NOT EXISTS idx_correlation_alerts_type ON correlation_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_correlation_alerts_resolved ON correlation_alerts(is_resolved);

-- Fonction pour mettre à jour automatiquement updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers pour mettre à jour automatiquement updated_at
CREATE TRIGGER update_symbol_metadata_updated_at BEFORE UPDATE ON symbol_metadata FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_historical_data_updated_at BEFORE UPDATE ON historical_data FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_sentiment_data_updated_at BEFORE UPDATE ON sentiment_data FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_technical_indicators_updated_at BEFORE UPDATE ON technical_indicators FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_target_parameters_updated_at BEFORE UPDATE ON target_parameters FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_ml_models_updated_at BEFORE UPDATE ON ml_models FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
