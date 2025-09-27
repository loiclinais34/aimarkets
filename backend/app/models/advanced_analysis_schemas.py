"""
Schémas Pydantic pour l'Analyse Avancée
Phase 4: Intégration et Optimisation

Schémas de validation et sérialisation pour l'API d'analyse avancée.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum

class AnalysisTypeEnum(str, Enum):
    """Types d'analyse disponibles"""
    TECHNICAL = "technical"
    SENTIMENT = "sentiment"
    MARKET = "market"
    ML = "ml"
    HYBRID = "hybrid"

class RiskLevelEnum(str, Enum):
    """Niveaux de risque"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

class RecommendationEnum(str, Enum):
    """Types de recommandation"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"

# Schémas de base
class AnalysisRequest(BaseModel):
    """Requête d'analyse"""
    symbol: str = Field(..., description="Symbole à analyser")
    time_horizon: int = Field(30, ge=1, le=365, description="Horizon temporel en jours")
    include_ml: bool = Field(True, description="Inclure l'analyse ML")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v or len(v) < 1:
            raise ValueError('Le symbole ne peut pas être vide')
        return v.upper()

class AnalysisResponse(BaseModel):
    """Réponse d'analyse"""
    success: bool
    symbol: str
    analysis_date: datetime
    time_horizon: int
    summary: Dict[str, Any]
    detailed_analysis: Dict[str, Any]

class HybridAnalysisRequest(BaseModel):
    """Requête d'analyse hybride"""
    symbol: str = Field(..., description="Symbole à analyser")
    ml_analysis: Dict[str, Any] = Field(..., description="Analyse ML")
    conventional_analysis: Dict[str, Any] = Field(..., description="Analyse conventionnelle")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v or len(v) < 1:
            raise ValueError('Le symbole ne peut pas être vide')
        return v.upper()

class HybridScoreResponse(BaseModel):
    """Réponse de score hybride"""
    success: bool
    symbol: str
    analysis_date: datetime
    hybrid_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    convergence_factor: float = Field(..., ge=0.0, le=1.0)
    recommendation: RecommendationEnum
    score_breakdown: Dict[str, float]
    scoring_weights: Dict[str, float]

class CompositeAnalysisRequest(BaseModel):
    """Requête d'analyse composite"""
    analyses: Dict[str, Dict[str, Any]] = Field(..., description="Analyses par type")
    custom_weights: Optional[Dict[str, float]] = Field(None, description="Poids personnalisés")
    
    @validator('custom_weights')
    def validate_weights(cls, v):
        if v:
            total_weight = sum(v.values())
            if abs(total_weight - 1.0) > 0.01:
                raise ValueError('La somme des poids doit être égale à 1.0')
        return v

class CompositeScoreResponse(BaseModel):
    """Réponse de score composite"""
    success: bool
    symbol: str
    analysis_date: datetime
    overall_score: float = Field(..., ge=0.0, le=1.0)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevelEnum
    recommendation: RecommendationEnum
    score_breakdown: Dict[str, float]
    analysis_quality: Dict[str, float]
    convergence_metrics: Dict[str, float]

class AnalysisSummary(BaseModel):
    """Résumé d'analyse"""
    symbol: str
    analysis_date: datetime
    composite_score: float = Field(..., ge=0.0, le=1.0)
    confidence_level: float = Field(..., ge=0.0, le=1.0)
    recommendation: RecommendationEnum
    risk_level: RiskLevelEnum
    score_breakdown: Dict[str, float]
    weights: Dict[str, float]

class ScoringConfiguration(BaseModel):
    """Configuration du scoring"""
    hybrid_scoring: Dict[str, float]
    composite_scoring: Dict[str, Any]

class UpdateScoringConfigRequest(BaseModel):
    """Requête de mise à jour de la configuration du scoring"""
    hybrid_scoring: Optional[Dict[str, float]] = None
    composite_scoring: Optional[Dict[str, Any]] = None
    
    @validator('hybrid_scoring')
    def validate_hybrid_weights(cls, v):
        if v:
            if 'ml_weight' in v and 'conventional_weight' in v:
                total = v['ml_weight'] + v['conventional_weight']
                if abs(total - 1.0) > 0.01:
                    raise ValueError('La somme des poids ML et conventionnel doit être égale à 1.0')
        return v

class HealthCheckResponse(BaseModel):
    """Réponse de vérification de santé"""
    success: bool
    status: str
    services: Dict[str, str]
    timestamp: datetime
    error: Optional[str] = None

# Schémas pour les analyses détaillées
class TechnicalAnalysisDetail(BaseModel):
    """Détails de l'analyse technique"""
    signals: Dict[str, Any]
    candlestick_patterns: Dict[str, Any]
    support_resistance: Dict[str, Any]
    data_points: int
    analysis_period: str

class SentimentAnalysisDetail(BaseModel):
    """Détails de l'analyse de sentiment"""
    garch_analysis: Dict[str, Any]
    monte_carlo_analysis: Dict[str, Any]
    markov_analysis: Dict[str, Any]
    volatility_forecast: Dict[str, Any]
    data_points: int
    analysis_period: str

class MarketIndicatorsDetail(BaseModel):
    """Détails des indicateurs de marché"""
    volatility_indicators: Dict[str, Any]
    momentum_indicators: Dict[str, Any]
    data_points: int
    analysis_period: str

class MLAnalysisDetail(BaseModel):
    """Détails de l'analyse ML"""
    ml_score: float = Field(..., ge=0.0, le=1.0)
    ml_confidence: float = Field(..., ge=0.0, le=1.0)
    ml_recommendation: RecommendationEnum
    note: Optional[str] = None

class DetailedAnalysisResponse(BaseModel):
    """Réponse d'analyse détaillée"""
    technical: TechnicalAnalysisDetail
    sentiment: SentimentAnalysisDetail
    market: MarketIndicatorsDetail
    ml: Optional[MLAnalysisDetail] = None

# Schémas pour les métriques de convergence
class ConvergenceMetrics(BaseModel):
    """Métriques de convergence"""
    convergence_score: float = Field(..., ge=0.0, le=1.0)
    score_std: float = Field(..., ge=0.0)
    score_range: float = Field(..., ge=0.0)
    score_count: int = Field(..., ge=1)

class AnalysisQuality(BaseModel):
    """Qualité des analyses"""
    technical: float = Field(..., ge=0.0, le=1.0)
    sentiment: float = Field(..., ge=0.0, le=1.0)
    market: float = Field(..., ge=0.0, le=1.0)
    ml: float = Field(..., ge=0.0, le=1.0)

# Schémas pour les erreurs
class AnalysisError(BaseModel):
    """Erreur d'analyse"""
    error_type: str
    error_message: str
    error_details: Optional[Dict[str, Any]] = None
    timestamp: datetime

class ErrorResponse(BaseModel):
    """Réponse d'erreur"""
    success: bool = False
    error: AnalysisError
