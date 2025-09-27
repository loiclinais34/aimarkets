"""
Service d'Analyse Combinée Avancée
Phase 4: Intégration et Optimisation

Ce service orchestre tous les services d'analyse développés dans les phases précédentes :
- Analyse technique (Phase 1)
- Indicateurs de marché (Phase 2) 
- Analyse de sentiment (Phase 3)
- Intégration ML existante
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
    ml_score: float
    composite_score: float
    confidence_level: float
    recommendation: str
    risk_level: str
    technical_analysis: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    market_indicators: Dict[str, Any]
    ml_analysis: Dict[str, Any]

class AdvancedTradingAnalysis:
    """
    Service d'analyse combinée avancée
    
    Orchestre tous les services d'analyse pour fournir une vue complète
    des opportunités d'investissement.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    async def analyze_opportunity(
        self, 
        symbol: str, 
        time_horizon: int = 30,
        include_ml: bool = True,
        db: Session = None
    ) -> AnalysisResult:
        """
        Analyse complète d'une opportunité d'investissement
        
        Args:
            symbol: Symbole à analyser
            time_horizon: Horizon temporel en jours
            include_ml: Inclure l'analyse ML
            db: Session de base de données
            
        Returns:
            AnalysisResult: Résultat complet de l'analyse
        """
        try:
            self.logger.info(f"Starting comprehensive analysis for {symbol}")
            
            # Analyse technique simplifiée
            technical_score, technical_analysis = await self._analyze_technical(symbol, db)
            
            # Analyse de sentiment simplifiée
            sentiment_score, sentiment_analysis = await self._analyze_sentiment(symbol, db)
            
            # Analyse de marché simplifiée
            market_score, market_indicators = await self._analyze_market(symbol, db)
            
            # Analyse ML (si demandée)
            ml_score = 0.5  # Score neutre par défaut
            ml_analysis = {}
            if include_ml:
                ml_score, ml_analysis = await self._analyze_ml(symbol, db)
            
            # Calcul du score composite
            composite_score = self._calculate_composite_score(
                technical_score, sentiment_score, market_score, ml_score
            )
            
            # Détermination de la recommandation et du niveau de risque
            recommendation, risk_level = self._determine_recommendation(composite_score)
            confidence_level = self._calculate_confidence_level(
                technical_score, sentiment_score, market_score, ml_score
            )
            
            result = AnalysisResult(
                symbol=symbol,
                analysis_date=datetime.now(),
                technical_score=technical_score,
                sentiment_score=sentiment_score,
                market_score=market_score,
                ml_score=ml_score,
                composite_score=composite_score,
                confidence_level=confidence_level,
                recommendation=recommendation,
                risk_level=risk_level,
                technical_analysis=technical_analysis,
                sentiment_analysis=sentiment_analysis,
                market_indicators=market_indicators,
                ml_analysis=ml_analysis
            )
            
            self.logger.info(f"Analysis completed for {symbol}: {recommendation}")
            return result
            
        except Exception as e:
            self.logger.error(f"Error analyzing {symbol}: {e}")
            raise
    
    async def _analyze_technical(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse technique simplifiée"""
        try:
            # Récupérer les indicateurs techniques depuis la base
            indicators = db.query(TechnicalIndicators)\
                .filter(TechnicalIndicators.symbol == symbol)\
                .order_by(TechnicalIndicators.date.desc())\
                .limit(1)\
                .first()
            
            if not indicators:
                return 0.5, {"status": "no_data", "message": "No technical indicators found"}
            
            # Score basé sur les indicateurs disponibles
            score = 0.5  # Score neutre par défaut
            
            # Analyse simplifiée des indicateurs
            analysis = {
                "rsi": getattr(indicators, 'rsi', None),
                "macd": getattr(indicators, 'macd', None),
                "bollinger_upper": getattr(indicators, 'bollinger_upper', None),
                "bollinger_lower": getattr(indicators, 'bollinger_lower', None),
                "score": score
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in technical analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_sentiment(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse de sentiment simplifiée"""
        try:
            # Récupérer les indicateurs de sentiment depuis la base
            indicators = db.query(SentimentIndicators)\
                .filter(SentimentIndicators.symbol == symbol)\
                .order_by(SentimentIndicators.date.desc())\
                .limit(1)\
                .first()
            
            if not indicators:
                return 0.5, {"status": "no_data", "message": "No sentiment indicators found"}
            
            # Score basé sur les indicateurs disponibles
            score = 0.5  # Score neutre par défaut
            
            # Analyse simplifiée des indicateurs
            analysis = {
                "sentiment_score": getattr(indicators, 'sentiment_score', None),
                "confidence": getattr(indicators, 'confidence', None),
                "score": score
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in sentiment analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_market(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse de marché simplifiée"""
        try:
            # Récupérer les indicateurs de marché depuis la base
            indicators = db.query(MarketIndicators)\
                .filter(MarketIndicators.symbol == symbol)\
                .order_by(MarketIndicators.analysis_date.desc())\
                .limit(1)\
                .first()
            
            if not indicators:
                return 0.5, {"status": "no_data", "message": "No market indicators found"}
            
            # Score basé sur les indicateurs disponibles
            score = 0.5  # Score neutre par défaut
            
            # Analyse simplifiée des indicateurs
            analysis = {
                "indicator_type": getattr(indicators, 'indicator_type', None),
                "indicator_value": getattr(indicators, 'indicator_value', None),
                "score": score
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in market analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_ml(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse ML simplifiée"""
        try:
            # Pour l'instant, retourner un score neutre
            # TODO: Intégrer avec le service ML existant
            score = 0.5
            analysis = {
                "ml_score": score,
                "note": "ML analysis not yet implemented"
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in ML analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    def _calculate_composite_score(
        self, 
        technical_score: float, 
        sentiment_score: float, 
        market_score: float, 
        ml_score: float
    ) -> float:
        """Calcule le score composite"""
        # Poids égaux pour tous les types d'analyse
        weights = {
            'technical': 0.25,
            'sentiment': 0.25,
            'market': 0.25,
            'ml': 0.25
        }
        
        composite_score = (
            technical_score * weights['technical'] +
            sentiment_score * weights['sentiment'] +
            market_score * weights['market'] +
            ml_score * weights['ml']
        )
        
        return round(composite_score, 3)
    
    def _determine_recommendation(self, composite_score: float) -> Tuple[str, str]:
        """Détermine la recommandation et le niveau de risque"""
        if composite_score >= 0.8:
            return "STRONG_BUY", "LOW"
        elif composite_score >= 0.6:
            return "BUY", "MEDIUM"
        elif composite_score >= 0.4:
            return "HOLD", "MEDIUM"
        elif composite_score >= 0.2:
            return "SELL", "HIGH"
        else:
            return "STRONG_SELL", "VERY_HIGH"
    
    def _calculate_confidence_level(
        self, 
        technical_score: float, 
        sentiment_score: float, 
        market_score: float, 
        ml_score: float
    ) -> float:
        """Calcule le niveau de confiance"""
        # Confiance basée sur la cohérence des scores
        scores = [technical_score, sentiment_score, market_score, ml_score]
        score_std = np.std(scores)
        
        # Plus la variance est faible, plus la confiance est élevée
        confidence = max(0.1, 1.0 - score_std)
        return round(confidence, 3)
    
    def get_analysis_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """Retourne un résumé de l'analyse"""
        return {
            "symbol": result.symbol,
            "composite_score": result.composite_score,
            "confidence_level": result.confidence_level,
            "recommendation": result.recommendation,
            "risk_level": result.risk_level,
            "score_breakdown": {
                "technical": result.technical_score,
                "sentiment": result.sentiment_score,
                "market": result.market_score,
                "ml": result.ml_score
            }
        }