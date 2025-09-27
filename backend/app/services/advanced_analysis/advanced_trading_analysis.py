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
    Service d'analyse combinée qui orchestre tous les services d'analyse
    """
    
    def __init__(self):
        """Initialise le service d'analyse simplifié"""
        # Configuration des poids pour le scoring composite
        self.scoring_weights = {
            'technical': 0.35,      # 35% pour l'analyse technique
            'sentiment': 0.30,      # 30% pour l'analyse de sentiment
            'market': 0.25,         # 25% pour les indicateurs de marché
            'ml': 0.10             # 10% pour l'analyse ML existante
        }
        
        logger.info("AdvancedTradingAnalysis service initialized (simplified version)")
    
    async def analyze_opportunity(self, symbol: str, time_horizon: int = 30, 
                                include_ml: bool = True) -> AnalysisResult:
        """
        Analyse simplifiée d'une opportunité d'investissement basée sur les données existantes
        
        Args:
            symbol: Symbole de l'actif à analyser
            time_horizon: Horizon temporel pour l'analyse en jours
            include_ml: Booléen pour inclure ou non l'analyse ML
            
        Returns:
            Un objet AnalysisResult contenant les résultats de l'analyse
        """
        logger.info(f"Starting comprehensive analysis for {symbol} with time horizon {time_horizon} days")
        
        from app.core.database import get_db
        db = next(get_db())
        
        try:
            # 1. Récupération des données historiques
            historical_data = db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol
            ).order_by(HistoricalData.date.desc()).limit(time_horizon * 2).all()
            
            if not historical_data:
                raise ValueError(f"No historical data found for {symbol}")
            
            # 2. Analyse simplifiée basée sur les données existantes
            technical_score = self._calculate_simple_technical_score(historical_data)
            sentiment_score = self._calculate_simple_sentiment_score(historical_data)
            market_score = self._calculate_simple_market_score(historical_data)
            
            # 3. Analyse ML (si incluse)
            ml_score = 0.5  # Score par défaut
            ml_analysis_result = None
            if include_ml:
                ml_score, ml_analysis_result = self._get_ml_score(symbol, db)
            
            # 4. Calcul du score composite
            composite_score = self._calculate_composite_score(
                technical_score, sentiment_score, market_score, ml_score
            )
            
            # 5. Détermination de la confiance et de la recommandation
            confidence_level = self._determine_confidence(
                technical_score, sentiment_score, market_score, ml_score
            )
            recommendation = self._determine_recommendation(composite_score, confidence_level)
            risk_level = self._determine_risk_level(composite_score, confidence_level)
            
            logger.info(f"Analysis completed for {symbol}: {recommendation} (score: {composite_score:.2f})")
            
            return AnalysisResult(
                symbol=symbol,
                analysis_date=datetime.now(),
                technical_score=technical_score,
                sentiment_score=sentiment_score,
                market_score=market_score,
                composite_score=composite_score,
                confidence_level=confidence_level,
                recommendation=recommendation,
                risk_level=risk_level,
                technical_analysis={"score": technical_score, "method": "simplified"},
                sentiment_analysis={"score": sentiment_score, "method": "simplified"},
                market_indicators={"score": market_score, "method": "simplified"},
                ml_analysis=ml_analysis_result
            )
            
        finally:
            db.close()
    
    def _calculate_simple_technical_score(self, historical_data: List[HistoricalData]) -> float:
        """Calcule un score technique simplifié basé sur les données historiques"""
        if len(historical_data) < 2:
            return 0.5
        
        # Calculer le rendement sur différentes périodes (convertir en float)
        prices = [float(hd.close) for hd in historical_data]
        
        # Rendement sur 5 jours
        if len(prices) >= 5:
            return_5d = (prices[0] - prices[4]) / prices[4]
        else:
            return_5d = 0
        
        # Rendement sur 20 jours
        if len(prices) >= 20:
            return_20d = (prices[0] - prices[19]) / prices[19]
        else:
            return_20d = 0
        
        # Score basé sur les rendements (normalisé entre 0 et 1)
        score = 0.5 + (return_5d * 0.3 + return_20d * 0.7) * 10  # Facteur d'amplification
        return max(0.0, min(1.0, score))
    
    def _calculate_simple_sentiment_score(self, historical_data: List[HistoricalData]) -> float:
        """Calcule un score de sentiment simplifié basé sur la volatilité"""
        if len(historical_data) < 10:
            return 0.5
        
        prices = [float(hd.close) for hd in historical_data[:10]]
        returns = [(prices[i] - prices[i+1]) / prices[i+1] for i in range(len(prices)-1)]
        
        # Calculer la volatilité
        volatility = np.std(returns)
        
        # Score inversement proportionnel à la volatilité (moins de volatilité = meilleur sentiment)
        score = max(0.0, min(1.0, 1.0 - volatility * 20))
        return score
    
    def _calculate_simple_market_score(self, historical_data: List[HistoricalData]) -> float:
        """Calcule un score de marché simplifié basé sur le volume et les prix"""
        if len(historical_data) < 5:
            return 0.5
        
        # Analyser le volume moyen (convertir en float)
        volumes = [float(hd.volume) for hd in historical_data[:5]]
        avg_volume = np.mean(volumes)
        
        # Score basé sur le volume (plus de volume = meilleur score de marché)
        volume_score = min(1.0, avg_volume / 1000000)  # Normaliser par 1M
        
        # Analyser la tendance des prix (convertir en float)
        prices = [float(hd.close) for hd in historical_data[:5]]
        price_trend = (prices[0] - prices[-1]) / prices[-1]
        trend_score = 0.5 + price_trend * 5  # Amplifier la tendance
        
        # Score composite
        score = (volume_score * 0.6 + trend_score * 0.4)
        return max(0.0, min(1.0, score))
    
    def _get_ml_score(self, symbol: str, db: Session) -> Tuple[float, Optional[Dict[str, Any]]]:
        """Récupère le score ML existant pour le symbole"""
        try:
            from app.models.database import MLModels
            
            # Récupérer le dernier modèle entraîné pour le symbole
            latest_model = db.query(MLModels).filter(
                MLModels.symbol == symbol
            ).order_by(MLModels.created_at.desc()).first()
            
            if latest_model:
                # Utiliser la précision du modèle comme score ML
                ml_score = latest_model.accuracy if latest_model.accuracy else 0.5
                ml_analysis = {
                    "model_name": latest_model.model_name,
                    "accuracy": latest_model.accuracy,
                    "f1_score": latest_model.f1_score
                }
                return ml_score, ml_analysis
            else:
                return 0.5, {"note": "No ML model found"}
                
        except Exception as e:
            logger.warning(f"Error getting ML score for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    def _calculate_composite_score(self, technical_score: float, sentiment_score: float, 
                                 market_score: float, ml_score: float) -> float:
        """Calcule le score composite final"""
        composite_score = (
            technical_score * self.scoring_weights['technical'] +
            sentiment_score * self.scoring_weights['sentiment'] +
            market_score * self.scoring_weights['market'] +
            ml_score * self.scoring_weights['ml']
        )
        
        return min(1.0, max(0.0, composite_score))
    
    def _determine_confidence(self, technical_score: float, sentiment_score: float, 
                            market_score: float, ml_score: float) -> float:
        """Détermine le niveau de confiance basé sur la convergence des scores"""
        scores = [technical_score, sentiment_score, market_score, ml_score]
        
        # Calculer l'écart-type des scores pour mesurer la convergence
        std_dev = np.std(scores)
        
        # Plus l'écart-type est faible, plus la confiance est élevée
        confidence = max(0.0, 1.0 - std_dev)
        
        return min(1.0, max(0.0, confidence))
    
    def _determine_recommendation(self, composite_score: float, confidence_level: float) -> str:
        """Détermine la recommandation finale"""
        if composite_score >= 0.7 and confidence_level >= 0.6:
            return "STRONG_BUY"
        elif composite_score >= 0.5 and confidence_level >= 0.4:
            return "BUY"
        elif composite_score <= 0.3 and confidence_level >= 0.6:
            return "STRONG_SELL"
        elif composite_score <= 0.5 and confidence_level >= 0.4:
            return "SELL"
        else:
            return "HOLD"
    
    def _determine_risk_level(self, composite_score: float, confidence_level: float) -> str:
        """Détermine le niveau de risque"""
        # Risque basé sur la confiance et le score
        if confidence_level >= 0.8 and 0.3 <= composite_score <= 0.7:
            return "LOW"
        elif confidence_level >= 0.6:
            return "MEDIUM"
        else:
            return "HIGH"
    
    def get_analysis_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """
        Génère un résumé de l'analyse pour l'affichage
        """
        return {
            "symbol": result.symbol,
            "analysis_date": result.analysis_date.isoformat(),
            "composite_score": result.composite_score,
            "confidence_level": result.confidence_level,
            "recommendation": result.recommendation,
            "risk_level": result.risk_level,
            "scores": {
                "technical": result.technical_score,
                "sentiment": result.sentiment_score,
                "market": result.market_score,
                "ml": result.ml_analysis.get('accuracy', 0.5) if result.ml_analysis else 0.5
            }
        }