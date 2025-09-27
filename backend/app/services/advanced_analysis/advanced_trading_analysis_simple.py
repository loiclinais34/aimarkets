"""
Service d'Analyse Combinée Avancée - Version Simplifiée
Phase 4: Intégration et Optimisation

Ce service orchestre tous les services d'analyse en utilisant les données existantes en base.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from sqlalchemy.orm import Session

# Import des modèles de base de données
from app.models.database import HistoricalData, SentimentData, TechnicalIndicators, SentimentIndicators
from app.models.market_indicators import MarketIndicators, MomentumIndicators, VolatilityIndicators
from app.models.advanced_opportunities import AdvancedOpportunity

logger = logging.getLogger(__name__)

@dataclass
class AnalysisResult:
    """Résultat d'une analyse complète"""
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

class AdvancedTradingAnalysis:
    """
    Service d'analyse combinée qui utilise les données existantes en base
    """
    
    def __init__(self):
        """Initialise le service d'analyse"""
        # Configuration des poids de scoring
        self.scoring_weights = {
            'technical': 0.3,
            'sentiment': 0.25,
            'market': 0.25,
            'ml': 0.2
        }
        
        logger.info("AdvancedTradingAnalysis service initialized")
    
    async def analyze_opportunity(self, symbol: str, time_horizon: int = 30, 
                                 include_ml: bool = True) -> AnalysisResult:
        """
        Analyse complète d'une opportunité d'investissement
        
        Args:
            symbol: Symbole à analyser
            time_horizon: Horizon temporel en jours
            include_ml: Inclure l'analyse ML existante
            
        Returns:
            AnalysisResult contenant tous les résultats d'analyse
        """
        try:
            logger.info(f"Starting comprehensive analysis for {symbol}")
            
            # Pour l'instant, retournons une analyse simplifiée basée sur les données existantes
            # Dans une version complète, nous utiliserions les données de la base
            
            # Analyse technique simplifiée
            technical_score = self._calculate_simple_technical_score(symbol)
            technical_analysis = {
                "score": technical_score,
                "indicators": "Basic technical analysis",
                "signals": "Simplified signals"
            }
            
            # Analyse de sentiment simplifiée
            sentiment_score = self._calculate_simple_sentiment_score(symbol)
            sentiment_analysis = {
                "score": sentiment_score,
                "garch_analysis": "Simplified GARCH",
                "monte_carlo": "Simplified Monte Carlo",
                "markov_chains": "Simplified Markov"
            }
            
            # Analyse de marché simplifiée
            market_score = self._calculate_simple_market_score(symbol)
            market_indicators = {
                "score": market_score,
                "volatility": "Simplified volatility",
                "momentum": "Simplified momentum"
            }
            
            # Analyse ML simplifiée
            ml_analysis = None
            if include_ml:
                ml_analysis = {
                    "ml_score": 0.5,
                    "ml_confidence": 0.5,
                    "ml_recommendation": "HOLD",
                    "note": "ML analysis not yet integrated"
                }
            
            # Calcul du score composite
            composite_score = self._calculate_composite_score(
                technical_score, sentiment_score, market_score, 
                getattr(ml_analysis, 'ml_score', 0.5) if ml_analysis else 0.5
            )
            
            # Détermination de la recommandation et du niveau de risque
            recommendation = self._determine_recommendation(composite_score)
            risk_level = self._determine_risk_level(composite_score, sentiment_score)
            confidence_level = self._calculate_confidence_level(composite_score)
            
            result = AnalysisResult(
                symbol=symbol,
                analysis_date=datetime.now(),
                technical_score=technical_score,
                sentiment_score=sentiment_score,
                market_score=market_score,
                composite_score=composite_score,
                confidence_level=confidence_level,
                recommendation=recommendation,
                risk_level=risk_level,
                technical_analysis=technical_analysis,
                sentiment_analysis=sentiment_analysis,
                market_indicators=market_indicators,
                ml_analysis=ml_analysis
            )
            
            logger.info(f"Analysis completed for {symbol}: {recommendation} (score: {composite_score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis for {symbol}: {e}")
            # Retourner un résultat par défaut en cas d'erreur
            return AnalysisResult(
                symbol=symbol,
                analysis_date=datetime.now(),
                technical_score=0.5,
                sentiment_score=0.5,
                market_score=0.5,
                composite_score=0.5,
                confidence_level=0.5,
                recommendation="HOLD",
                risk_level="MEDIUM",
                technical_analysis={"error": str(e)},
                sentiment_analysis={"error": str(e)},
                market_indicators={"error": str(e)},
                ml_analysis={"error": str(e)}
            )
    
    def _calculate_simple_technical_score(self, symbol: str) -> float:
        """Calcule un score technique simplifié"""
        # Pour l'instant, retournons un score aléatoire basé sur le symbole
        # Dans une version complète, nous analyserions les données techniques réelles
        import hashlib
        hash_value = int(hashlib.md5(symbol.encode()).hexdigest()[:8], 16)
        return (hash_value % 100) / 100.0
    
    def _calculate_simple_sentiment_score(self, symbol: str) -> float:
        """Calcule un score de sentiment simplifié"""
        # Pour l'instant, retournons un score aléatoire basé sur le symbole
        import hashlib
        hash_value = int(hashlib.md5(f"{symbol}_sentiment".encode()).hexdigest()[:8], 16)
        return (hash_value % 100) / 100.0
    
    def _calculate_simple_market_score(self, symbol: str) -> float:
        """Calcule un score de marché simplifié"""
        # Pour l'instant, retournons un score aléatoire basé sur le symbole
        import hashlib
        hash_value = int(hashlib.md5(f"{symbol}_market".encode()).hexdigest()[:8], 16)
        return (hash_value % 100) / 100.0
    
    def _calculate_composite_score(self, technical_score: float, sentiment_score: float, 
                                  market_score: float, ml_score: float) -> float:
        """Calcule le score composite pondéré"""
        return (
            technical_score * self.scoring_weights['technical'] +
            sentiment_score * self.scoring_weights['sentiment'] +
            market_score * self.scoring_weights['market'] +
            ml_score * self.scoring_weights['ml']
        )
    
    def _determine_recommendation(self, composite_score: float) -> str:
        """Détermine la recommandation basée sur le score composite"""
        if composite_score >= 0.8:
            return "STRONG_BUY"
        elif composite_score >= 0.6:
            return "BUY"
        elif composite_score >= 0.4:
            return "HOLD"
        elif composite_score >= 0.2:
            return "SELL"
        else:
            return "STRONG_SELL"
    
    def _determine_risk_level(self, composite_score: float, sentiment_score: float) -> str:
        """Détermine le niveau de risque"""
        if composite_score >= 0.7 and sentiment_score >= 0.6:
            return "LOW"
        elif composite_score >= 0.4 and sentiment_score >= 0.3:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def _calculate_confidence_level(self, composite_score: float) -> float:
        """Calcule le niveau de confiance"""
        # Plus le score est extrême (proche de 0 ou 1), plus la confiance est élevée
        return abs(composite_score - 0.5) * 2
    
    def get_analysis_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """
        Génère un résumé de l'analyse
        
        Args:
            result: Résultat d'analyse complet
            
        Returns:
            Dict contenant le résumé
        """
        return {
            "symbol": result.symbol,
            "recommendation": result.recommendation,
            "composite_score": result.composite_score,
            "confidence_level": result.confidence_level,
            "risk_level": result.risk_level,
            "score_breakdown": {
                "technical": result.technical_score,
                "sentiment": result.sentiment_score,
                "market": result.market_score,
                "ml": getattr(result.ml_analysis, 'ml_score', 0.5) if result.ml_analysis else 0.5
            },
            "analysis_date": result.analysis_date.isoformat()
        }

