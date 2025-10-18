-- Create table for ML-generated opportunities
CREATE TABLE IF NOT EXISTS ml_opportunities (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    horizon_days INTEGER NOT NULL,
    recommendation VARCHAR(20) NOT NULL,
    confidence_level DECIMAL(5,4) NOT NULL,
    potential_return DECIMAL(8,4),
    risk_score DECIMAL(5,4),
    ml_model_name VARCHAR(100),
    ml_model_version VARCHAR(20),
    technical_indicators JSONB,
    ml_features JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_ml_opportunities_symbol_date ON ml_opportunities (symbol, date);
CREATE INDEX IF NOT EXISTS idx_ml_opportunities_horizon ON ml_opportunities (horizon_days);
CREATE INDEX IF NOT EXISTS idx_ml_opportunities_recommendation ON ml_opportunities (recommendation);
CREATE INDEX IF NOT EXISTS idx_ml_opportunities_confidence ON ml_opportunities (confidence_level);

-- Add comments
COMMENT ON TABLE ml_opportunities IS 'ML-generated trading opportunities with sophisticated models';
COMMENT ON COLUMN ml_opportunities.horizon_days IS 'Prediction horizon in days (1, 7, 30)';
COMMENT ON COLUMN ml_opportunities.confidence_level IS 'ML model confidence score (0-1)';
COMMENT ON COLUMN ml_opportunities.potential_return IS 'Predicted return for the horizon';
COMMENT ON COLUMN ml_opportunities.risk_score IS 'Risk assessment score (0-1)';
COMMENT ON COLUMN ml_opportunities.technical_indicators IS 'Technical indicators used for prediction';
COMMENT ON COLUMN ml_opportunities.ml_features IS 'ML features used for prediction';
