from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal


# === SCHÉMAS POUR LES MÉTADONNÉES DES SYMBOLES ===

class SymbolMetadataBase(BaseModel):
    symbol: str = Field(..., description="Symbole de l'action")
    company_name: str = Field(..., description="Nom de l'entreprise")
    sector: Optional[str] = Field(None, description="Secteur d'activité")
    industry: Optional[str] = Field(None, description="Industrie")
    market_cap_category: Optional[str] = Field(None, description="Catégorie de capitalisation boursière")
    is_active: bool = Field(default=True, description="Symbole actif")


class SymbolMetadataCreate(SymbolMetadataBase):
    pass


class SymbolMetadataUpdate(BaseModel):
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap_category: Optional[str] = None
    is_active: Optional[bool] = None


class SymbolMetadata(SymbolMetadataBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === SCHÉMAS POUR LES PARAMÈTRES DE CIBLE ===

class TargetParameterBase(BaseModel):
    user_id: str = Field(..., description="ID de l'utilisateur")
    parameter_name: str = Field(..., description="Nom du paramètre de cible")
    target_return_percentage: float = Field(..., ge=0, le=100, description="Rendement cible en pourcentage")
    time_horizon_days: int = Field(..., ge=1, le=365, description="Horizon temporel en jours")
    risk_tolerance: str = Field(default="medium", description="Tolérance au risque (low, medium, high)")
    min_confidence_threshold: float = Field(default=0.7, ge=0, le=1, description="Seuil de confiance minimum")
    max_drawdown_percentage: float = Field(default=5.0, ge=0, le=50, description="Drawdown maximum accepté")

    @validator('risk_tolerance')
    def validate_risk_tolerance(cls, v):
        if v not in ['low', 'medium', 'high']:
            raise ValueError('risk_tolerance doit être low, medium ou high')
        return v


class TargetParameterCreate(TargetParameterBase):
    pass


class TargetParameterUpdate(BaseModel):
    parameter_name: Optional[str] = None
    target_return_percentage: Optional[float] = Field(None, ge=0, le=100)
    time_horizon_days: Optional[int] = Field(None, ge=1, le=365)
    risk_tolerance: Optional[str] = None
    min_confidence_threshold: Optional[float] = Field(None, ge=0, le=1)
    max_drawdown_percentage: Optional[float] = Field(None, ge=0, le=50)
    is_active: Optional[bool] = None

    @validator('risk_tolerance')
    def validate_risk_tolerance(cls, v):
        if v is not None and v not in ['low', 'medium', 'high']:
            raise ValueError('risk_tolerance doit être low, medium ou high')
        return v


class TargetParameter(TargetParameterBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === SCHÉMAS POUR LES MODÈLES ML ===

class MLModelBase(BaseModel):
    model_name: str = Field(..., description="Nom du modèle")
    model_type: str = Field(..., description="Type de modèle (classification, regression)")
    model_version: str = Field(..., description="Version du modèle")
    symbol: str = Field(..., description="Symbole de l'actif")
    model_parameters: Dict[str, Any] = Field(..., description="Paramètres du modèle")
    training_data_start: Optional[date] = None
    training_data_end: Optional[date] = None
    validation_score: Optional[float] = Field(None, ge=0, le=1)
    test_score: Optional[float] = Field(None, ge=0, le=1)
    model_path: Optional[str] = None
    is_active: bool = Field(default=False, description="Modèle actif")


class MLModelCreate(MLModelBase):
    pass


class MLModel(MLModelBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === SCHÉMAS POUR LES PRÉDICTIONS ===

class MLPredictionBase(BaseModel):
    symbol: str = Field(..., description="Symbole de l'actif")
    prediction_date: date = Field(..., description="Date de la prédiction")
    model_id: int = Field(..., description="ID du modèle utilisé")
    prediction_type: str = Field(..., description="Type de prédiction")
    prediction_value: float = Field(..., description="Valeur de la prédiction")
    confidence: float = Field(..., ge=0, le=1, description="Niveau de confiance")
    features_used: Optional[List[str]] = Field(None, description="Features utilisées")
    screener_run_id: Optional[int] = Field(None, description="ID du run de screener qui a généré cette prédiction")


class MLPredictionCreate(MLPredictionBase):
    pass


class MLPrediction(MLPredictionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# === SCHÉMAS POUR LES CALCULS DE PRIX CIBLE ===

class TargetPriceCalculation(BaseModel):
    current_price: float = Field(..., gt=0, description="Prix actuel")
    target_return_percentage: float = Field(..., ge=0, le=100, description="Rendement cible en pourcentage")
    time_horizon_days: int = Field(..., ge=1, le=365, description="Horizon temporel en jours")
    target_price: float = Field(..., description="Prix cible calculé")
    expected_return: float = Field(..., description="Rendement attendu en pourcentage")
    daily_return: float = Field(..., description="Rendement quotidien équivalent")


# === SCHÉMAS POUR L'ENTRAÎNEMENT DES MODÈLES ===

class ModelTrainingRequest(BaseModel):
    symbol: str = Field(..., description="Symbole de l'actif")
    target_parameter_id: int = Field(..., description="ID du paramètre de cible")
    model_type: str = Field(..., description="Type de modèle (classification, regression)")
    test_size: float = Field(default=0.2, ge=0.1, le=0.5, description="Proportion des données de test")
    random_state: int = Field(default=42, description="Seed pour la reproductibilité")


class ModelTrainingResponse(BaseModel):
    model_id: int
    model_name: str
    model_type: str
    performance_metrics: Dict[str, float]
    feature_importance: Dict[str, float]
    training_data_info: Dict[str, Any]
    message: str


# === SCHÉMAS POUR LES PRÉDICTIONS ===

class PredictionRequest(BaseModel):
    symbol: str = Field(..., description="Symbole de l'actif")
    model_id: int = Field(..., description="ID du modèle")
    prediction_date: date = Field(..., description="Date de prédiction")


class PredictionResponse(BaseModel):
    symbol: str
    prediction_date: date
    prediction: float
    confidence: float
    prediction_type: str
    model_name: str
    features_used: List[str]
    data_date_used: Optional[date] = Field(None, description="Date des données réellement utilisées pour la prédiction")


# === SCHÉMAS POUR LES PERFORMANCES DES MODÈLES ===

class ModelPerformance(BaseModel):
    model_id: int
    model_name: str
    model_type: str
    validation_score: Optional[float]
    test_score: Optional[float]
    training_period: Dict[str, Optional[str]]
    recent_predictions_count: int
    is_active: bool


# === SCHÉMAS POUR LES DONNÉES HISTORIQUES ===

class HistoricalDataBase(BaseModel):
    symbol: str = Field(..., description="Symbole de l'actif")
    data_date: date = Field(..., alias="date", description="Date")
    open: float = Field(..., gt=0, description="Prix d'ouverture")
    high: float = Field(..., gt=0, description="Prix le plus haut")
    low: float = Field(..., gt=0, description="Prix le plus bas")
    close: float = Field(..., gt=0, description="Prix de clôture")
    volume: int = Field(..., ge=0, description="Volume")
    vwap: Optional[float] = Field(None, gt=0, description="Volume Weighted Average Price")


class HistoricalDataSchema(HistoricalDataBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === SCHÉMAS POUR LES INDICATEURS TECHNIQUES ===

class TechnicalIndicatorsBase(BaseModel):
    symbol: str = Field(..., description="Symbole de l'actif")
    data_date: date = Field(..., alias="date", description="Date")
    
    # Moyennes mobiles
    sma_5: Optional[float] = None
    sma_10: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_5: Optional[float] = None
    ema_10: Optional[float] = None
    ema_20: Optional[float] = None
    ema_50: Optional[float] = None
    ema_200: Optional[float] = None
    
    # Indicateurs de momentum
    rsi_14: Optional[float] = Field(None, ge=0, le=100)
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    stochastic_k: Optional[float] = Field(None, ge=0, le=100)
    stochastic_d: Optional[float] = Field(None, ge=0, le=100)
    williams_r: Optional[float] = Field(None, ge=-100, le=0)
    roc: Optional[float] = None
    cci: Optional[float] = None
    
    # Bollinger Bands
    bb_upper: Optional[float] = None
    bb_middle: Optional[float] = None
    bb_lower: Optional[float] = None
    bb_width: Optional[float] = None
    bb_position: Optional[float] = Field(None, ge=0, le=1)
    
    # Volume
    obv: Optional[float] = None
    volume_roc: Optional[float] = None
    volume_sma_20: Optional[float] = None
    
    # ATR
    atr_14: Optional[float] = None


class TechnicalIndicatorsSchema(TechnicalIndicatorsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === SCHÉMAS POUR LES INDICATEURS DE SENTIMENT ===

class SentimentIndicatorsBase(BaseModel):
    symbol: str = Field(..., description="Symbole de l'actif")
    data_date: date = Field(..., alias="date", description="Date")
    
    # Base Sentiment Indicators
    sentiment_score_normalized: Optional[float] = Field(None, ge=0, le=100)
    
    # Sentiment Momentum
    sentiment_momentum_1d: Optional[float] = None
    sentiment_momentum_3d: Optional[float] = None
    sentiment_momentum_7d: Optional[float] = None
    sentiment_momentum_14d: Optional[float] = None
    
    # Sentiment Volatility
    sentiment_volatility_3d: Optional[float] = None
    sentiment_volatility_7d: Optional[float] = None
    sentiment_volatility_14d: Optional[float] = None
    sentiment_volatility_30d: Optional[float] = None
    
    # Sentiment Moving Averages
    sentiment_sma_3: Optional[float] = None
    sentiment_sma_7: Optional[float] = None
    sentiment_sma_14: Optional[float] = None
    sentiment_sma_30: Optional[float] = None
    sentiment_ema_3: Optional[float] = None
    sentiment_ema_7: Optional[float] = None
    sentiment_ema_14: Optional[float] = None
    sentiment_ema_30: Optional[float] = None
    
    # Sentiment Oscillators
    sentiment_rsi_14: Optional[float] = Field(None, ge=0, le=100)
    sentiment_macd: Optional[float] = None
    sentiment_macd_signal: Optional[float] = None
    sentiment_macd_histogram: Optional[float] = None
    
    # News Volume Indicators
    news_volume_sma_7: Optional[float] = None
    news_volume_sma_14: Optional[float] = None
    news_volume_sma_30: Optional[float] = None
    news_volume_roc_7d: Optional[float] = None
    news_volume_roc_14d: Optional[float] = None
    
    # Sentiment Distribution Ratios
    news_positive_ratio: Optional[float] = Field(None, ge=0, le=1)
    news_negative_ratio: Optional[float] = Field(None, ge=0, le=1)
    news_neutral_ratio: Optional[float] = Field(None, ge=0, le=1)
    news_sentiment_quality: Optional[float] = None
    
    # Composite Sentiment Indicators
    sentiment_strength_index: Optional[float] = None
    market_sentiment_index: Optional[float] = None
    sentiment_divergence: Optional[float] = None
    sentiment_acceleration: Optional[float] = None
    sentiment_trend_strength: Optional[float] = None
    sentiment_quality_index: Optional[float] = None
    sentiment_risk_score: Optional[float] = None


class SentimentIndicatorsSchema(SentimentIndicatorsBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === SCHÉMAS POUR LES RÉPONSES GÉNÉRIQUES ===

class MessageResponse(BaseModel):
    message: str
    success: bool = True
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseModel):
    message: str
    success: bool = False
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


# === SCHÉMAS POUR LA PAGINATION ===

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int


# === SCHÉMAS POUR LES STATISTIQUES ===

class StatisticsResponse(BaseModel):
    total_symbols: int
    total_historical_records: int
    total_technical_indicators: int
    total_sentiment_indicators: int
    total_ml_models: int
    total_predictions: int
    data_coverage: Dict[str, Any]
    last_updated: datetime


# Schemas pour les Screeners
class ScreenerConfigBase(BaseModel):
    name: str = Field(..., description="Nom de la configuration du screener")
    target_return_percentage: float = Field(..., description="Rendement attendu en pourcentage")
    time_horizon_days: int = Field(..., description="Horizon temporel en jours")
    risk_tolerance: float = Field(..., description="Tolérance au risque (0.1 à 1.0)")
    confidence_threshold: float = Field(..., description="Seuil de confiance calculé")
    created_by: str = Field(..., description="Utilisateur créateur")

class ScreenerConfigCreate(ScreenerConfigBase):
    pass

class ScreenerConfigUpdate(BaseModel):
    name: Optional[str] = None
    target_return_percentage: Optional[float] = None
    time_horizon_days: Optional[int] = None
    risk_tolerance: Optional[float] = None
    confidence_threshold: Optional[float] = None
    is_active: Optional[bool] = None

class ScreenerConfig(ScreenerConfigBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ScreenerRunBase(BaseModel):
    screener_config_id: int = Field(..., description="ID de la configuration du screener")
    run_date: date = Field(..., description="Date d'exécution")
    total_symbols: int = Field(..., description="Nombre total de symboles analysés")
    successful_models: int = Field(..., description="Nombre de modèles entraînés avec succès")
    opportunities_found: int = Field(..., description="Nombre d'opportunités trouvées")
    execution_time_seconds: int = Field(..., description="Temps d'exécution en secondes")
    status: str = Field(..., description="Statut de l'exécution")

class ScreenerRunCreate(ScreenerRunBase):
    pass

class ScreenerRun(ScreenerRunBase):
    id: int
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScreenerResultBase(BaseModel):
    screener_run_id: int = Field(..., description="ID de l'exécution du screener")
    symbol: str = Field(..., description="Symbole de l'actif")
    model_id: int = Field(..., description="ID du modèle utilisé")
    prediction: float = Field(..., description="Valeur de la prédiction")
    confidence: float = Field(..., description="Niveau de confiance")
    rank: int = Field(..., description="Rang dans les résultats")

class ScreenerResultCreate(ScreenerResultBase):
    pass

class ScreenerResult(ScreenerResultBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScreenerRequest(BaseModel):
    target_return_percentage: float = Field(..., description="Rendement attendu en pourcentage")
    time_horizon_days: int = Field(..., description="Horizon temporel en jours")
    risk_tolerance: float = Field(..., description="Tolérance au risque (0.1 à 1.0)")

class ScreenerResponse(BaseModel):
    screener_run_id: int
    total_symbols: int
    successful_models: int
    opportunities_found: int
    execution_time_seconds: int
    results: List[Dict[str, Any]]


# === SCHÉMAS POUR LES SESSIONS DE RECHERCHE ===

class SearchSessionBase(BaseModel):
    target_return_percentage: float = Field(..., ge=0, le=100, description="Rendement cible en pourcentage")
    time_horizon_days: int = Field(..., ge=1, le=365, description="Horizon temporel en jours")
    risk_tolerance: float = Field(..., ge=0.1, le=1.0, description="Tolérance au risque")
    confidence_threshold: float = Field(..., ge=0.5, le=0.95, description="Seuil de confiance")


class SearchSessionCreate(SearchSessionBase):
    pass


class SearchSessionUpdate(BaseModel):
    status: Optional[str] = None
    total_opportunities: Optional[int] = None


class SearchSession(SearchSessionBase):
    id: int
    search_id: str
    status: str
    total_opportunities: int
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SearchSessionWithResults(SearchSession):
    opportunities: List[Dict[str, Any]] = []
    models: List[Dict[str, Any]] = []
    stats: Dict[str, Any] = {}


class SearchOpportunityResponse(BaseModel):
    search_id: str
    status: str
    total_opportunities: int
    opportunities: List[Dict[str, Any]]
    search_parameters: Dict[str, Any]
    created_at: datetime
    completed_at: Optional[datetime] = None