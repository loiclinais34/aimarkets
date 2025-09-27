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
from app.models.technical_analysis import CandlestickPatterns
from app.models.sentiment_analysis import GARCHModels, MonteCarloSimulations, MarkovChainAnalysis
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
    candlestick_score: float
    garch_score: float
    monte_carlo_score: float
    markov_score: float
    volatility_score: float
    composite_score: float
    confidence_level: float
    recommendation: str
    risk_level: str
    technical_analysis: Dict[str, Any]
    sentiment_analysis: Dict[str, Any]
    market_indicators: Dict[str, Any]
    ml_analysis: Dict[str, Any]
    candlestick_analysis: Dict[str, Any]
    garch_analysis: Dict[str, Any]
    monte_carlo_analysis: Dict[str, Any]
    markov_analysis: Dict[str, Any]
    volatility_analysis: Dict[str, Any]

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
            
            # Analyse des patterns de candlesticks
            candlestick_score, candlestick_analysis = await self._analyze_candlestick_patterns(symbol, db)
            
            # Analyse des modèles GARCH
            garch_score, garch_analysis = await self._analyze_garch_models(symbol, db)
            
            # Analyse des simulations Monte Carlo
            monte_carlo_score, monte_carlo_analysis = await self._analyze_monte_carlo(symbol, db)
            
            # Analyse des chaînes de Markov
            markov_score, markov_analysis = await self._analyze_markov_chains(symbol, db)
            
            # Analyse de la volatilité
            volatility_score, volatility_analysis = await self._analyze_volatility(symbol, db)
            
            # Analyse ML (si demandée)
            ml_score = 0.5  # Score neutre par défaut
            ml_analysis = {}
            if include_ml:
                ml_score, ml_analysis = await self._analyze_ml(symbol, db)
            
            # Calcul du score composite
            composite_score = self._calculate_composite_score(
                technical_score, sentiment_score, market_score, ml_score,
                candlestick_score, garch_score, monte_carlo_score, markov_score, volatility_score
            )
            
            # Détermination de la recommandation et du niveau de risque
            recommendation, risk_level = self._determine_recommendation(composite_score)
            confidence_level = self._calculate_confidence_level(
                technical_score, sentiment_score, market_score, ml_score,
                candlestick_score, garch_score, monte_carlo_score, markov_score, volatility_score
            )
            
            result = AnalysisResult(
                symbol=symbol,
                analysis_date=datetime.now(),
                technical_score=technical_score,
                sentiment_score=sentiment_score,
                market_score=market_score,
                ml_score=ml_score,
                candlestick_score=candlestick_score,
                garch_score=garch_score,
                monte_carlo_score=monte_carlo_score,
                markov_score=markov_score,
                volatility_score=volatility_score,
                composite_score=composite_score,
                confidence_level=confidence_level,
                recommendation=recommendation,
                risk_level=risk_level,
                technical_analysis=technical_analysis,
                sentiment_analysis=sentiment_analysis,
                market_indicators=market_indicators,
                ml_analysis=ml_analysis,
                candlestick_analysis=candlestick_analysis,
                garch_analysis=garch_analysis,
                monte_carlo_analysis=monte_carlo_analysis,
                markov_analysis=markov_analysis,
                volatility_analysis=volatility_analysis
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
    
    async def _analyze_candlestick_patterns(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse des patterns de candlesticks"""
        try:
            # Récupérer les patterns de candlesticks depuis la base
            patterns = db.query(CandlestickPatterns)\
                .filter(CandlestickPatterns.symbol == symbol)\
                .order_by(CandlestickPatterns.created_at.desc())\
                .limit(10)\
                .all()
            
            if not patterns:
                return 0.5, {"status": "no_data", "message": "No candlestick patterns found"}
            
            # Calculer le score basé sur les patterns
            bullish_patterns = sum(1 for p in patterns if p.pattern_direction == 'BULLISH')
            bearish_patterns = sum(1 for p in patterns if p.pattern_direction == 'BEARISH')
            neutral_patterns = sum(1 for p in patterns if p.pattern_direction == 'NEUTRAL')
            
            total_patterns = len(patterns)
            if total_patterns == 0:
                score = 0.5
            else:
                # Score basé sur la proportion de patterns haussiers vs baissiers
                bullish_ratio = bullish_patterns / total_patterns
                bearish_ratio = bearish_patterns / total_patterns
                score = 0.5 + (bullish_ratio - bearish_ratio) * 0.3  # Score entre 0.2 et 0.8
            
            analysis = {
                "total_patterns": total_patterns,
                "bullish_patterns": bullish_patterns,
                "bearish_patterns": bearish_patterns,
                "neutral_patterns": neutral_patterns,
                "latest_patterns": [
                    {
                        "type": p.pattern_type,
                        "direction": p.pattern_direction,
                        "strength": float(p.pattern_strength)
                    } for p in patterns[:3]
                ],
                "score": score
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in candlestick analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_garch_models(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse des modèles GARCH"""
        try:
            # Récupérer les modèles GARCH depuis la base
            models = db.query(GARCHModels)\
                .filter(GARCHModels.symbol == symbol)\
                .order_by(GARCHModels.created_at.desc())\
                .limit(5)\
                .all()
            
            if not models:
                return 0.5, {"status": "no_data", "message": "No GARCH models found"}
            
            # Calculer le score basé sur la volatilité prévue
            best_model = next((m for m in models if m.is_best_model), models[0])
            volatility_forecast = float(best_model.volatility_forecast)
            
            # Score basé sur la volatilité (plus la volatilité est élevée, plus le risque est élevé)
            if volatility_forecast < 0.2:
                score = 0.8  # Faible volatilité = bon score
            elif volatility_forecast < 0.4:
                score = 0.6  # Volatilité modérée
            elif volatility_forecast < 0.6:
                score = 0.4  # Volatilité élevée
            else:
                score = 0.2  # Très haute volatilité
            
            analysis = {
                "volatility_forecast": volatility_forecast,
                "var_95": float(best_model.var_95),
                "var_99": float(best_model.var_99),
                "model_type": best_model.model_type,
                "aic": float(best_model.aic) if best_model.aic else None,
                "bic": float(best_model.bic) if best_model.bic else None,
                "total_models": len(models),
                "score": score
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in GARCH analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_monte_carlo(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse des simulations Monte Carlo"""
        try:
            # Récupérer les simulations Monte Carlo depuis la base
            simulations = db.query(MonteCarloSimulations)\
                .filter(MonteCarloSimulations.symbol == symbol)\
                .order_by(MonteCarloSimulations.created_at.desc())\
                .limit(1)\
                .first()
            
            if not simulations:
                return 0.5, {"status": "no_data", "message": "No Monte Carlo simulations found"}
            
            # Calculer le score basé sur la probabilité de rendement positif
            prob_positive = float(simulations.probability_positive_return)
            score = prob_positive  # Score direct basé sur la probabilité
            
            analysis = {
                "probability_positive_return": prob_positive,
                "var_95": float(simulations.var_95),
                "var_99": float(simulations.var_99),
                "expected_shortfall_95": float(simulations.expected_shortfall_95),
                "expected_shortfall_99": float(simulations.expected_shortfall_99),
                "mean_return": float(simulations.mean_return),
                "std_return": float(simulations.std_return),
                "simulations_count": simulations.simulations_count,
                "time_horizon": simulations.time_horizon,
                "score": score
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in Monte Carlo analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_markov_chains(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse des chaînes de Markov"""
        try:
            # Récupérer l'analyse Markov depuis la base
            analysis = db.query(MarkovChainAnalysis)\
                .filter(MarkovChainAnalysis.symbol == symbol)\
                .order_by(MarkovChainAnalysis.created_at.desc())\
                .first()
            
            if not analysis:
                return 0.5, {"status": "no_data", "message": "No Markov chain analysis found"}
            
            # Calculer le score basé sur l'état actuel
            current_state = analysis.current_state
            if current_state == 0:  # BULL
                score = 0.8
            elif current_state == 1:  # BEAR
                score = 0.2
            else:  # SIDEWAYS
                score = 0.5
            
            analysis_data = {
                "current_state": current_state,
                "state_probabilities": analysis.state_probabilities,
                "transition_matrix": analysis.transition_matrix,
                "stationary_probabilities": analysis.stationary_probabilities,
                "n_states": analysis.n_states,
                "score": score
            }
            
            return score, analysis_data
            
        except Exception as e:
            self.logger.error(f"Error in Markov analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_volatility(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse de la volatilité"""
        try:
            # Récupérer les indicateurs de volatilité depuis la base
            volatility = db.query(VolatilityIndicators)\
                .filter(VolatilityIndicators.symbol == symbol)\
                .order_by(VolatilityIndicators.created_at.desc())\
                .first()
            
            if not volatility:
                return 0.5, {"status": "no_data", "message": "No volatility indicators found"}
            
            # Calculer le score basé sur le niveau de risque
            risk_level = volatility.risk_level
            if risk_level == "LOW":
                score = 0.8
            elif risk_level == "MEDIUM":
                score = 0.6
            elif risk_level == "HIGH":
                score = 0.4
            else:  # VERY_HIGH
                score = 0.2
            
            analysis = {
                "current_volatility": float(volatility.current_volatility),
                "historical_volatility": float(volatility.historical_volatility),
                "volatility_ratio": float(volatility.volatility_ratio),
                "volatility_percentile": float(volatility.volatility_percentile),
                "risk_level": risk_level,
                "vix_value": float(volatility.vix_value),
                "regime_analysis": volatility.regime_analysis,
                "score": score
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in volatility analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    def _calculate_composite_score(
        self, 
        technical_score: float, 
        sentiment_score: float, 
        market_score: float, 
        ml_score: float,
        candlestick_score: float,
        garch_score: float,
        monte_carlo_score: float,
        markov_score: float,
        volatility_score: float
    ) -> float:
        """Calcule le score composite"""
        # Poids pour tous les types d'analyse
        weights = {
            'technical': 0.15,
            'sentiment': 0.15,
            'market': 0.15,
            'ml': 0.10,
            'candlestick': 0.10,
            'garch': 0.10,
            'monte_carlo': 0.10,
            'markov': 0.10,
            'volatility': 0.05
        }
        
        composite_score = (
            technical_score * weights['technical'] +
            sentiment_score * weights['sentiment'] +
            market_score * weights['market'] +
            ml_score * weights['ml'] +
            candlestick_score * weights['candlestick'] +
            garch_score * weights['garch'] +
            monte_carlo_score * weights['monte_carlo'] +
            markov_score * weights['markov'] +
            volatility_score * weights['volatility']
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
        ml_score: float,
        candlestick_score: float,
        garch_score: float,
        monte_carlo_score: float,
        markov_score: float,
        volatility_score: float
    ) -> float:
        """Calcule le niveau de confiance"""
        # Confiance basée sur la cohérence des scores
        scores = [technical_score, sentiment_score, market_score, ml_score,
                 candlestick_score, garch_score, monte_carlo_score, markov_score, volatility_score]
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
                "ml": result.ml_score,
                "candlestick": result.candlestick_score,
                "garch": result.garch_score,
                "monte_carlo": result.monte_carlo_score,
                "markov": result.markov_score,
                "volatility": result.volatility_score
            }
        }