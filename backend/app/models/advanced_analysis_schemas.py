from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class AnalysisRequest(BaseModel):
    """Requête d'analyse avancée"""
    symbol: str = Field(..., description="Symbole à analyser")
    time_horizon: int = Field(default=30, ge=1, le=365, description="Horizon temporel en jours")
    include_ml: bool = Field(default=True, description="Inclure l'analyse ML")
    analysis_types: List[str] = Field(default=["technical", "sentiment", "market"], description="Types d'analyse")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper()

class AnalysisResponse(BaseModel):
    """Réponse d'analyse avancée"""
    symbol: str
    analysis_date: datetime
    technical_score: float
    sentiment_score: float
    market_score: float
    composite_score: float
    confidence_level: float
    recommendation: str
    risk_level: str
    technical_analysis: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    market_indicators: Dict[str, Any]
    ml_analysis: Optional[Dict[str, Any]] = None

class HybridSearchRequest(BaseModel):
    """Requête de recherche hybride"""
    symbols: List[str] = Field(..., description="Liste des symboles à analyser")
    analysis_types: List[str] = Field(default=["technical", "sentiment"], description="Types d'analyse à effectuer")
    time_horizon: int = Field(default=30, ge=1, le=365, description="Horizon temporel en jours")
    weights: Optional[Dict[str, float]] = Field(default=None, description="Poids pour le scoring hybride")
    
    @validator('symbols')
    def validate_symbols(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Au moins un symbole doit être fourni')
        return [symbol.upper() for symbol in v]

class HybridAnalysisRequest(BaseModel):
    """Requête d'analyse hybride"""
    symbol: str = Field(..., description="Symbole à analyser")
    ml_analysis: Dict[str, Any] = Field(..., description="Analyse ML")
    conventional_analysis: Dict[str, Any] = Field(..., description="Analyse conventionnelle")
    weights: Optional[Dict[str, float]] = Field(default=None, description="Poids pour le scoring")

class HybridAnalysisResponse(BaseModel):
    """Réponse d'analyse hybride"""
    symbol: str
    ml_score: float
    conventional_score: float
    hybrid_score: float
    confidence: float
    convergence_factor: float
    recommendation: str
    analysis_date: datetime

class CompositeAnalysisRequest(BaseModel):
    """Requête d'analyse composite"""
    symbol: str = Field(..., description="Symbole à analyser")
    analysis_types: List[str] = Field(default=["technical", "sentiment", "market", "ml"])
    time_horizon: int = Field(default=30, ge=1, le=365)
    weights: Optional[Dict[str, float]] = Field(default=None)

class CompositeAnalysisResponse(BaseModel):
    """Réponse d'analyse composite"""
    symbol: str
    composite_score: float
    confidence_level: float
    recommendation: str
    risk_level: str
    individual_scores: Dict[str, float]
    analysis_date: datetime

class ScoringWeights(BaseModel):
    """Poids pour le scoring"""
    technical: float = Field(default=0.25, ge=0.0, le=1.0)
    sentiment: float = Field(default=0.25, ge=0.0, le=1.0)
    market: float = Field(default=0.25, ge=0.0, le=1.0)
    ml: float = Field(default=0.25, ge=0.0, le=1.0)
    
    @validator('technical', 'sentiment', 'market', 'ml')
    def validate_weights_sum(cls, v, values):
        total = sum(values.values()) if values else 0
        if total > 1.0:
            raise ValueError('La somme des poids ne peut pas dépasser 1.0')
        return v

class HybridScoringWeights(BaseModel):
    """Poids pour le scoring hybride"""
    ml: float = Field(default=0.4, ge=0.0, le=1.0)
    technical: float = Field(default=0.2, ge=0.0, le=1.0)
    sentiment: float = Field(default=0.2, ge=0.0, le=1.0)
    market: float = Field(default=0.2, ge=0.0, le=1.0)

class AdvancedAnalysisConfig(BaseModel):
    """Configuration pour l'analyse avancée"""
    default_time_horizon: int = Field(default=30)
    default_weights: ScoringWeights = Field(default_factory=ScoringWeights)
    enable_ml_analysis: bool = Field(default=True)
    enable_technical_analysis: bool = Field(default=True)
    enable_sentiment_analysis: bool = Field(default=True)
    enable_market_analysis: bool = Field(default=True)

class Recommendation(str, Enum):
    """Types de recommandations"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

class RiskLevel(str, Enum):
    """Niveaux de risque"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"

class AnalysisType(str, Enum):
    """Types d'analyse"""
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"
    MARKET = "market"
    ML = "ml"

