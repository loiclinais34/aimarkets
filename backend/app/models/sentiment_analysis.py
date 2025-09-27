"""
Modèles de base de données pour l'analyse de sentiment.

Ce module définit les modèles SQLAlchemy pour stocker
les résultats d'analyse de sentiment et de volatilité.
"""

from sqlalchemy import Column, Integer, String, DECIMAL, TIMESTAMP, Boolean, Text, JSON
from sqlalchemy.sql import func
from .database import Base


class SentimentAnalysis(Base):
    """
    Modèle pour stocker les résultats d'analyse de sentiment.
    """
    __tablename__ = "sentiment_analysis"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    model_type = Column(String(50), nullable=False)  # GARCH, MonteCarlo, Markov
    analysis_date = Column(TIMESTAMP, nullable=False, index=True)
    volatility_forecast = Column(DECIMAL(10, 6), nullable=True)
    var_95 = Column(DECIMAL(10, 6), nullable=True)  # Value at Risk 95%
    var_99 = Column(DECIMAL(10, 6), nullable=True)  # Value at Risk 99%
    expected_shortfall_95 = Column(DECIMAL(10, 6), nullable=True)
    expected_shortfall_99 = Column(DECIMAL(10, 6), nullable=True)
    market_state = Column(String(20), nullable=True)  # BULL, BEAR, SIDEWAYS
    confidence = Column(DECIMAL(3, 2), nullable=False)
    model_parameters = Column(JSON, nullable=True)  # Paramètres du modèle
    model_metrics = Column(JSON, nullable=True)  # Métriques du modèle (AIC, BIC, etc.)
    analysis_results = Column(JSON, nullable=True)  # Résultats détaillés
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = ({"schema": "public"},)


class GARCHModels(Base):
    """
    Modèle pour stocker les résultats des modèles GARCH.
    """
    __tablename__ = "garch_models"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    model_type = Column(String(50), nullable=False)  # GARCH, EGARCH, GJR-GARCH
    analysis_date = Column(TIMESTAMP, nullable=False, index=True)
    volatility_forecast = Column(DECIMAL(10, 6), nullable=False)
    var_95 = Column(DECIMAL(10, 6), nullable=False)
    var_99 = Column(DECIMAL(10, 6), nullable=False)
    aic = Column(DECIMAL(10, 4), nullable=True)
    bic = Column(DECIMAL(10, 4), nullable=True)
    log_likelihood = Column(DECIMAL(10, 4), nullable=True)
    model_parameters = Column(JSON, nullable=True)  # Paramètres du modèle
    residuals = Column(JSON, nullable=True)  # Résidus du modèle
    conditional_volatility = Column(JSON, nullable=True)  # Volatilité conditionnelle
    is_best_model = Column(Boolean, default=False)  # Meilleur modèle selon AIC
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = ({"schema": "public"},)


class MonteCarloSimulations(Base):
    """
    Modèle pour stocker les résultats des simulations Monte Carlo.
    """
    __tablename__ = "monte_carlo_simulations"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    analysis_date = Column(TIMESTAMP, nullable=False, index=True)
    current_price = Column(DECIMAL(10, 4), nullable=False)
    volatility = Column(DECIMAL(10, 6), nullable=False)
    drift = Column(DECIMAL(10, 6), nullable=False)
    time_horizon = Column(Integer, nullable=False)  # en jours
    simulations_count = Column(Integer, nullable=False)
    var_95 = Column(DECIMAL(10, 6), nullable=False)
    var_99 = Column(DECIMAL(10, 6), nullable=False)
    expected_shortfall_95 = Column(DECIMAL(10, 6), nullable=False)
    expected_shortfall_99 = Column(DECIMAL(10, 6), nullable=False)
    mean_return = Column(DECIMAL(10, 6), nullable=True)
    std_return = Column(DECIMAL(10, 6), nullable=True)
    min_return = Column(DECIMAL(10, 6), nullable=True)
    max_return = Column(DECIMAL(10, 6), nullable=True)
    probability_positive_return = Column(DECIMAL(3, 2), nullable=True)
    stress_test_results = Column(JSON, nullable=True)  # Résultats des tests de stress
    tail_risk_analysis = Column(JSON, nullable=True)  # Analyse des risques de queue
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = ({"schema": "public"},)


class MarkovChainAnalysis(Base):
    """
    Modèle pour stocker les résultats d'analyse des chaînes de Markov.
    """
    __tablename__ = "markov_chain_analysis"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    analysis_date = Column(TIMESTAMP, nullable=False, index=True)
    n_states = Column(Integer, nullable=False)
    current_state = Column(Integer, nullable=False)
    state_probabilities = Column(JSON, nullable=True)  # Probabilités d'état
    transition_matrix = Column(JSON, nullable=True)  # Matrice de transition
    stationary_probabilities = Column(JSON, nullable=True)  # Probabilités stationnaires
    regime_changes = Column(JSON, nullable=True)  # Changements de régime détectés
    future_state_predictions = Column(JSON, nullable=True)  # Prédictions d'états futurs
    state_analysis = Column(JSON, nullable=True)  # Analyse des états
    model_parameters = Column(JSON, nullable=True)  # Paramètres du modèle
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = ({"schema": "public"},)


class VolatilityForecasts(Base):
    """
    Modèle pour stocker les prédictions de volatilité.
    """
    __tablename__ = "volatility_forecasts"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    analysis_date = Column(TIMESTAMP, nullable=False, index=True)
    forecast_method = Column(String(50), nullable=False)  # ensemble, regime_switching, monte_carlo
    horizon = Column(Integer, nullable=False)  # Horizon de prédiction en jours
    current_volatility = Column(DECIMAL(10, 6), nullable=False)
    forecast_volatility = Column(DECIMAL(10, 6), nullable=False)  # Volatilité moyenne prévue
    volatility_forecasts = Column(JSON, nullable=True)  # Prédictions détaillées
    confidence_intervals = Column(JSON, nullable=True)  # Intervalles de confiance
    model_weights = Column(JSON, nullable=True)  # Poids des modèles (pour ensemble)
    uncertainty = Column(DECIMAL(10, 6), nullable=True)  # Incertitude de la prédiction
    risk_level = Column(String(20), nullable=True)  # Niveau de risque
    volatility_trend = Column(DECIMAL(10, 6), nullable=True)  # Tendance de volatilité
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())

    __table_args__ = ({"schema": "public"},)
