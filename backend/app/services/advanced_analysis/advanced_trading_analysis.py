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
        """Analyse technique robuste basée sur l'historique des indicateurs avec scoring multi-dimensionnel"""
        try:
            # Récupérer l'historique des indicateurs techniques (60 jours pour les Z-scores)
            # Filtrer par la date de dernière mise à jour pour ne garder que les derniers calculs
            from sqlalchemy import func
            
            # Récupérer la date de dernière mise à jour pour ce symbole
            max_updated_at = db.query(func.max(TechnicalIndicators.updated_at))\
                .filter(TechnicalIndicators.symbol == symbol)\
                .scalar()
            
            if not max_updated_at:
                return 0.5, {"status": "no_data", "message": "No technical indicators found"}
            
            # Récupérer les indicateurs avec la dernière mise à jour
            indicators_history = db.query(TechnicalIndicators)\
                .filter(TechnicalIndicators.symbol == symbol)\
                .filter(TechnicalIndicators.updated_at == max_updated_at)\
                .order_by(TechnicalIndicators.date.desc())\
                .limit(60)\
                .all()
            
            if not indicators_history:
                return 0.5, {"status": "no_data", "message": "No technical indicators found"}
            
            # Récupérer l'historique des prix (60 jours)
            price_history = db.query(HistoricalData)\
                .filter(HistoricalData.symbol == symbol)\
                .order_by(HistoricalData.date.desc())\
                .limit(60)\
                .all()
            
            if not price_history:
                return 0.5, {"status": "no_price_data", "message": "No price history found"}
            
            # Convertir en DataFrame pour les calculs
            import pandas as pd
            
            # Créer DataFrame des indicateurs
            indicators_df = pd.DataFrame([{
                'date': ind.date,
                'rsi_14': float(ind.rsi_14) if ind.rsi_14 is not None else None,
                'macd': float(ind.macd) if ind.macd is not None else None,
                'macd_signal': float(ind.macd_signal) if ind.macd_signal is not None else None,
                'macd_histogram': float(ind.macd_histogram) if ind.macd_histogram is not None else None,
                'bb_upper': float(ind.bb_upper) if ind.bb_upper is not None else None,
                'bb_lower': float(ind.bb_lower) if ind.bb_lower is not None else None,
                'bb_middle': float(ind.bb_middle) if ind.bb_middle is not None else None,
                'sma_20': float(ind.sma_20) if ind.sma_20 is not None else None,
                'sma_50': float(ind.sma_50) if ind.sma_50 is not None else None,
                'sma_200': float(ind.sma_200) if ind.sma_200 is not None else None,
                'ema_20': float(ind.ema_20) if ind.ema_20 is not None else None,
                'ema_50': float(ind.ema_50) if ind.ema_50 is not None else None,
                'williams_r': float(ind.williams_r) if ind.williams_r is not None else None,
                'atr_14': float(ind.atr_14) if ind.atr_14 is not None else None,
                'obv': float(ind.obv) if ind.obv is not None else None,
                'volume_sma_20': float(ind.volume_sma_20) if ind.volume_sma_20 is not None else None,
                'stochastic_k': float(ind.stochastic_k) if ind.stochastic_k is not None else None,
                'stochastic_d': float(ind.stochastic_d) if ind.stochastic_d is not None else None,
                'roc': float(ind.roc) if ind.roc is not None else None,
                'bb_width': float(ind.bb_width) if ind.bb_width is not None else None
            } for ind in indicators_history])
            
            # Créer DataFrame des prix
            price_df = pd.DataFrame([{
                'date': price.date,
                'close': float(price.close),
                'volume': float(price.volume) if price.volume is not None else None
            } for price in price_history])
            
            # Trier par date (plus ancien en premier)
            indicators_df = indicators_df.sort_values('date').reset_index(drop=True)
            price_df = price_df.sort_values('date').reset_index(drop=True)
            
            # Calculer les scores avec l'historique
            trend_score = self._calculate_trend_score_with_history(indicators_df, price_df)
            momentum_score = self._calculate_momentum_score_with_history(indicators_df)
            obos_score = self._calculate_obos_score_with_history(indicators_df, price_df)
            volume_score = self._calculate_volume_score_with_history(indicators_df, price_df)
            volatility_score = self._calculate_volatility_structure_score_with_history(indicators_df, price_df)
            
            # Score composite technique (0-100)
            technical_score = (
                trend_score * 0.30 +      # 30% - Tendance
                momentum_score * 0.25 +   # 25% - Momentum
                obos_score * 0.20 +       # 20% - Overbought/Oversold
                volume_score * 0.15 +     # 15% - Volume
                volatility_score * 0.10   # 10% - Structure/Volatilité
            )
            
            # Normalisation (0-1)
            normalized_score = technical_score / 100.0
            
            # Données les plus récentes pour l'analyse
            latest_indicators = indicators_df.iloc[-1]
            latest_price = price_df.iloc[-1]
            
            # Analyse détaillée des indicateurs
            analysis = {
                "trend_score": trend_score,
                "momentum_score": momentum_score,
                "obos_score": obos_score,
                "volume_score": volume_score,
                "volatility_score": volatility_score,
                "composite_technical_score": technical_score,
                "rsi_14": latest_indicators['rsi_14'],
                "macd": latest_indicators['macd'],
                "macd_signal": latest_indicators['macd_signal'],
                "macd_histogram": latest_indicators['macd_histogram'],
                "bb_upper": latest_indicators['bb_upper'],
                "bb_lower": latest_indicators['bb_lower'],
                "bb_middle": latest_indicators['bb_middle'],
                "sma_20": latest_indicators['sma_20'],
                "sma_50": latest_indicators['sma_50'],
                "sma_200": latest_indicators['sma_200'],
                "ema_20": latest_indicators['ema_20'],
                "ema_50": latest_indicators['ema_50'],
                "williams_r": latest_indicators['williams_r'],
                "atr_14": latest_indicators['atr_14'],
                "obv": latest_indicators['obv'],
                "current_price": latest_price['close'],
                "current_volume": latest_price['volume'],
                "score": normalized_score
            }
            
            return normalized_score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in technical analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_sentiment(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse de sentiment basée sur les vrais indicateurs"""
        try:
            # Récupérer la date de dernière mise à jour pour ce symbole
            from sqlalchemy import func
            max_updated_at = db.query(func.max(SentimentIndicators.updated_at))\
                .filter(SentimentIndicators.symbol == symbol)\
                .scalar()
            
            if not max_updated_at:
                return 0.5, {"status": "no_data", "message": "No sentiment indicators found"}
            
            # Récupérer les indicateurs de sentiment depuis la base avec la dernière mise à jour
            # Chercher les données les plus récentes non-neutres (différentes de 50.0)
            indicators = db.query(SentimentIndicators)\
                .filter(SentimentIndicators.symbol == symbol)\
                .filter(SentimentIndicators.updated_at == max_updated_at)\
                .filter(SentimentIndicators.sentiment_score_normalized != 50.0)\
                .order_by(SentimentIndicators.date.desc())\
                .limit(1)\
                .first()
            
            # Si pas de données non-neutres, prendre les plus récentes avec la dernière mise à jour
            if not indicators:
                indicators = db.query(SentimentIndicators)\
                    .filter(SentimentIndicators.symbol == symbol)\
                    .filter(SentimentIndicators.updated_at == max_updated_at)\
                    .order_by(SentimentIndicators.date.desc())\
                    .limit(1)\
                    .first()
            
            if not indicators:
                return 0.5, {"status": "no_data", "message": "No sentiment indicators found"}
            
            # Calculer un score basé sur les indicateurs réels
            score = 0.5  # Score neutre par défaut
            
            # Utiliser le score normalisé s'il existe
            if indicators.sentiment_score_normalized is not None:
                # Convertir de 0,100 vers 0,1
                normalized_score = float(indicators.sentiment_score_normalized) / 100.0
                score = normalized_score
            
            # Calculer la confiance basée sur la volatilité
            confidence = 0.5
            if indicators.sentiment_volatility_7d is not None:
                # Plus la volatilité est faible, plus la confiance est élevée
                volatility = abs(float(indicators.sentiment_volatility_7d))
                confidence = max(0.1, min(1.0, 1.0 - volatility))
            
            # Analyse détaillée des indicateurs
            analysis = {
                "sentiment_score": float(indicators.sentiment_score_normalized) if indicators.sentiment_score_normalized is not None else None,
                "sentiment_momentum_1d": float(indicators.sentiment_momentum_1d) if indicators.sentiment_momentum_1d is not None else None,
                "sentiment_momentum_7d": float(indicators.sentiment_momentum_7d) if indicators.sentiment_momentum_7d is not None else None,
                "sentiment_volatility_7d": float(indicators.sentiment_volatility_7d) if indicators.sentiment_volatility_7d is not None else None,
                "confidence": confidence,
                "score": score,
                "data_date": indicators.date.isoformat()
            }
            
            return score, analysis
            
        except Exception as e:
            self.logger.error(f"Error in sentiment analysis for {symbol}: {e}")
            return 0.5, {"error": str(e)}
    
    async def _analyze_market(self, symbol: str, db: Session) -> Tuple[float, Dict[str, Any]]:
        """Analyse de marché basée sur les vrais indicateurs"""
        try:
            # Récupérer la date de dernière création pour ce symbole
            from sqlalchemy import func
            max_created_at = db.query(func.max(MarketIndicators.created_at))\
                .filter(MarketIndicators.symbol == symbol)\
                .scalar()
            
            if not max_created_at:
                return 0.5, {"status": "no_data", "message": "No market indicators found"}
            
            # Récupérer les indicateurs de marché depuis la base avec la dernière création
            indicators = db.query(MarketIndicators)\
                .filter(MarketIndicators.symbol == symbol)\
                .filter(MarketIndicators.created_at == max_created_at)\
                .order_by(MarketIndicators.analysis_date.desc())\
                .limit(10)\
                .all()
            
            if not indicators:
                return 0.5, {"status": "no_data", "message": "No market indicators found"}
            
            # Calculer un score basé sur les indicateurs réels
            score = 0.5  # Score neutre par défaut
            market_data = {}
            signals = []
            
            # Analyser les différents types d'indicateurs
            for indicator in indicators:
                indicator_type = indicator.indicator_type
                value = float(indicator.indicator_value)
                market_data[indicator_type] = value
                
                # Analyser RSI (indicateur technique de marché)
                if indicator_type == "RSI_14D":
                    if value < 30:
                        signals.append("RSI oversold (bullish)")
                        score += 0.15
                    elif value > 70:
                        signals.append("RSI overbought (bearish)")
                        score -= 0.15
                    elif 40 <= value <= 60:
                        signals.append("RSI neutral")
                        score += 0.05
                
                # Analyser le ratio de volume
                elif indicator_type == "VOLUME_RATIO":
                    if value > 1.5:
                        signals.append("High volume activity")
                        score += 0.1
                    elif value < 0.5:
                        signals.append("Low volume activity")
                        score -= 0.05
                
                # Analyser le momentum
                elif indicator_type == "MOMENTUM_20D":
                    if value > 0.05:
                        signals.append("Strong positive momentum")
                        score += 0.1
                    elif value < -0.05:
                        signals.append("Strong negative momentum")
                        score -= 0.1
                
                # Analyser la volatilité
                elif indicator_type == "VOLATILITY_20D":
                    if value < 0.15:
                        signals.append("Low volatility (stable)")
                        score += 0.05
                    elif value > 0.3:
                        signals.append("High volatility (risky)")
                        score -= 0.1
            
            # Normaliser le score entre 0 et 1
            score = max(0.0, min(1.0, score))
            
            # Analyse détaillée des indicateurs
            analysis = {
                "indicators": market_data,
                "indicator_count": len(indicators),
                "latest_date": indicators[0].analysis_date.isoformat() if indicators else None,
                "signals": signals,
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
            # Récupérer la date de dernière création pour ce symbole
            from sqlalchemy import func
            max_created_at = db.query(func.max(CandlestickPatterns.created_at))\
                .filter(CandlestickPatterns.symbol == symbol)\
                .scalar()
            
            if not max_created_at:
                return 0.5, {"status": "no_data", "message": "No candlestick patterns found"}
            
            # Récupérer les patterns de candlesticks depuis la base avec la dernière création
            patterns = db.query(CandlestickPatterns)\
                .filter(CandlestickPatterns.symbol == symbol)\
                .filter(CandlestickPatterns.created_at == max_created_at)\
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
            # Récupérer la date de dernière création pour ce symbole
            from sqlalchemy import func
            max_created_at = db.query(func.max(GARCHModels.created_at))\
                .filter(GARCHModels.symbol == symbol)\
                .scalar()
            
            if not max_created_at:
                return 0.5, {"status": "no_data", "message": "No GARCH models found"}
            
            # Récupérer les modèles GARCH depuis la base avec la dernière création
            models = db.query(GARCHModels)\
                .filter(GARCHModels.symbol == symbol)\
                .filter(GARCHModels.created_at == max_created_at)\
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
            # Récupérer la date de dernière création pour ce symbole
            from sqlalchemy import func
            max_created_at = db.query(func.max(MonteCarloSimulations.created_at))\
                .filter(MonteCarloSimulations.symbol == symbol)\
                .scalar()
            
            if not max_created_at:
                return 0.5, {"status": "no_data", "message": "No Monte Carlo simulations found"}
            
            # Récupérer les simulations Monte Carlo depuis la base avec la dernière création
            simulations = db.query(MonteCarloSimulations)\
                .filter(MonteCarloSimulations.symbol == symbol)\
                .filter(MonteCarloSimulations.created_at == max_created_at)\
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
            # Récupérer la date de dernière création pour ce symbole
            from sqlalchemy import func
            max_created_at = db.query(func.max(MarkovChainAnalysis.created_at))\
                .filter(MarkovChainAnalysis.symbol == symbol)\
                .scalar()
            
            if not max_created_at:
                return 0.5, {"status": "no_data", "message": "No Markov chain analysis found"}
            
            # Récupérer l'analyse Markov depuis la base avec la dernière création
            analysis = db.query(MarkovChainAnalysis)\
                .filter(MarkovChainAnalysis.symbol == symbol)\
                .filter(MarkovChainAnalysis.created_at == max_created_at)\
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
            # Récupérer la date de dernière mise à jour pour ce symbole
            from sqlalchemy import func
            max_updated_at = db.query(func.max(VolatilityIndicators.updated_at))\
                .filter(VolatilityIndicators.symbol == symbol)\
                .scalar()
            
            if not max_updated_at:
                return 0.5, {"status": "no_data", "message": "No volatility indicators found"}
            
            # Récupérer les indicateurs de volatilité depuis la base avec la dernière mise à jour
            volatility = db.query(VolatilityIndicators)\
                .filter(VolatilityIndicators.symbol == symbol)\
                .filter(VolatilityIndicators.updated_at == max_updated_at)\
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
        """Calcule le score composite avec méthode robuste multi-dimensionnelle"""
        
        # Scores normalisés (0-100)
        scores = {
            'technical': technical_score * 100,
            'sentiment': sentiment_score * 100,
            'market': market_score * 100,
            'ml': ml_score * 100,
            'candlestick': candlestick_score * 100,
            'garch': garch_score * 100,
            'monte_carlo': monte_carlo_score * 100,
            'markov': markov_score * 100,
            'volatility': volatility_score * 100
        }
        
        # Poids adaptatifs basés sur la cohérence des signaux
        base_weights = {
            'technical': 0.30,      # Poids principal pour l'analyse technique
            'sentiment': 0.15,      # Sentiment important mais variable
            'market': 0.15,         # Contexte de marché
            'ml': 0.02,             # ML pour la prédiction
            'candlestick': 0.10,    # Patterns de prix
            'garch': 0.08,          # Volatilité prévue
            'monte_carlo': 0.08,    # Simulations de risque
            'markov': 0.07,         # Régimes de marché
            'volatility': 0.05      # Volatilité actuelle
        }
        
        # Calcul de la cohérence des signaux (écart-type des scores)
        score_values = list(scores.values())
        signal_consistency = 1.0 - (np.std(score_values) / 100.0)  # Plus cohérent = plus de confiance
        
        # Ajustement des poids basé sur la cohérence
        adjusted_weights = {}
        for key, base_weight in base_weights.items():
            # Si le signal est cohérent avec les autres, augmenter son poids
            if scores[key] > 50:  # Signal positif
                consistency_bonus = signal_consistency * 0.1
            else:  # Signal négatif
                consistency_bonus = signal_consistency * 0.05
            
            adjusted_weights[key] = base_weight + consistency_bonus
        
        # Normaliser les poids
        total_weight = sum(adjusted_weights.values())
        for key in adjusted_weights:
            adjusted_weights[key] /= total_weight
        
        # Score composite pondéré
        composite_score = sum(scores[key] * adjusted_weights[key] for key in scores)
        
        # Application de règles de prudence (overrides)
        composite_score = self._apply_safety_overrides(composite_score, scores)
        
        # Normalisation finale (0-1)
        return round(composite_score / 100.0, 3)
    
    def _apply_safety_overrides(self, composite_score: float, scores: Dict[str, float]) -> float:
        """Applique des règles de prudence pour éviter les signaux extrêmes non justifiés"""
        
        # Règle 1: Si volatilité très élevée ET sentiment négatif, réduire le score
        if scores['volatility'] < 30 and scores['sentiment'] < 40:
            composite_score *= 0.8  # Réduction de 20%
        
        # Règle 2: Si Monte Carlo très négatif ET GARCH très volatil, réduire le score
        if scores['monte_carlo'] < 30 and scores['garch'] < 30:
            composite_score *= 0.85  # Réduction de 15%
        
        # Règle 3: Si technique très positive mais marché très négatif, modérer
        if scores['technical'] > 70 and scores['market'] < 30:
            composite_score = (composite_score + 50) / 2  # Moyenne avec neutre
        
        # Règle 4: Si tous les signaux sont extrêmes dans le même sens, renforcer
        positive_signals = sum(1 for s in scores.values() if s > 60)
        negative_signals = sum(1 for s in scores.values() if s < 40)
        
        if positive_signals >= 6:  # 6+ signaux positifs
            composite_score = min(95, composite_score * 1.1)  # Boost de 10%, max 95
        elif negative_signals >= 6:  # 6+ signaux négatifs
            composite_score = max(5, composite_score * 0.9)   # Réduction de 10%, min 5
        
        return composite_score
    
    def _calculate_trend_score(self, indicators, current_price: float) -> float:
        """Calcule le score de tendance (0-100)"""
        points = 0
        
        # Prix vs SMA 200 (20 points)
        if indicators.sma_200 and current_price > float(indicators.sma_200):
            points += 20
        
        # SMA 50 vs SMA 200 (15 points)
        if indicators.sma_50 and indicators.sma_200 and float(indicators.sma_50) > float(indicators.sma_200):
            points += 15
        
        # SMA 20 vs SMA 50 (10 points)
        if indicators.sma_20 and indicators.sma_50 and float(indicators.sma_20) > float(indicators.sma_50):
            points += 10
        
        # EMA 20 vs EMA 50 (5 points)
        if indicators.ema_20 and indicators.ema_50 and float(indicators.ema_20) > float(indicators.ema_50):
            points += 5
        
        # MACD positif (10 points)
        if indicators.macd and float(indicators.macd) > 0:
            points += 10
        
        # MACD histogram positif (10 points)
        if indicators.macd_histogram and float(indicators.macd_histogram) > 0:
            points += 10
        
        # Position dans les Bollinger Bands (10 points)
        if (indicators.bb_upper and indicators.bb_lower and 
            indicators.bb_middle and current_price > float(indicators.bb_middle)):
            bb_position = (current_price - float(indicators.bb_lower)) / (float(indicators.bb_upper) - float(indicators.bb_lower))
            if bb_position > 0.5:
                points += 10
        
        return min(100, points)
    
    def _calculate_momentum_score(self, indicators) -> float:
        """Calcule le score de momentum (0-100)"""
        points = 0
        
        # RSI (30 points max)
        if indicators.rsi_14:
            rsi = float(indicators.rsi_14)
            if 50 < rsi < 70:
                points += 30
            elif rsi >= 70:
                points += 20
            elif 45 < rsi <= 50:
                points += 10
        
        # MACD slope (20 points max)
        if indicators.macd_histogram:
            histogram = float(indicators.macd_histogram)
            if histogram > 0:
                points += 20
            elif abs(histogram) < 0.001:  # Proche de zéro
                points += 10
        
        # ROC (20 points max) - Approximation basée sur RSI
        if indicators.rsi_14:
            rsi = float(indicators.rsi_14)
            if rsi > 55:  # Momentum positif
                points += 20
            elif rsi > 50:
                points += 10
        
        # Stochastic (10 points max) - Approximation
        if indicators.rsi_14:
            rsi = float(indicators.rsi_14)
            if 50 < rsi < 70:  # Momentum modéré
                points += 10
        
        return min(100, points)
    
    def _calculate_obos_score(self, indicators, current_price: float) -> float:
        """Calcule le score Overbought/Oversold (0-100)"""
        points = 0
        
        # RSI (40 points max)
        if indicators.rsi_14:
            rsi = float(indicators.rsi_14)
            if rsi < 30:
                points += 40
            elif 30 <= rsi < 40:
                points += 25
            elif 40 <= rsi < 50:
                points += 10
        
        # Williams %R (30 points max)
        if indicators.williams_r:
            wr = float(indicators.williams_r)
            if wr < -80:
                points += 30
            elif -80 <= wr < -60:
                points += 15
        
        # Position Bollinger Bands (30 points max)
        if (indicators.bb_upper and indicators.bb_lower and 
            indicators.bb_middle):
            bb_position = (current_price - float(indicators.bb_lower)) / (float(indicators.bb_upper) - float(indicators.bb_lower))
            if bb_position < 0.1:
                points += 30
            elif 0.1 <= bb_position < 0.3:
                points += 15
        
        return min(100, points)
    
    def _calculate_volume_score(self, indicators, current_price_data) -> float:
        """Calcule le score de volume (0-100)"""
        points = 0
        
        # OBV direction (40 points max)
        if indicators.obv:
            # Approximation basée sur le volume actuel
            if current_price_data.volume and indicators.volume_sma_20:
                if float(current_price_data.volume) > float(indicators.volume_sma_20):
                    points += 40
                else:
                    points += 20
        
        # Volume momentum (40 points max)
        if (current_price_data.volume and indicators.volume_sma_20 and 
            indicators.bb_middle and float(current_price_data.close) > float(indicators.bb_middle)):
            volume_ratio = float(current_price_data.volume) / float(indicators.volume_sma_20)
            if volume_ratio > 1.2:
                points += 40
            elif volume_ratio > 1.1:
                points += 20
        
        # Volume vs moyenne (20 points max)
        if current_price_data.volume and indicators.volume_sma_20:
            if float(current_price_data.volume) > float(indicators.volume_sma_20):
                points += 20
        
        return min(100, points)
    
    def _calculate_volatility_structure_score(self, indicators, current_price: float) -> float:
        """Calcule le score de structure/volatilité (0-100)"""
        points = 0
        
        # Breakout (50 points max)
        if (indicators.bb_upper and indicators.bb_lower and 
            indicators.bb_middle and indicators.atr_14):
            bb_width = (float(indicators.bb_upper) - float(indicators.bb_lower)) / float(indicators.bb_middle)
            atr_ratio = float(indicators.atr_14) / float(indicators.bb_middle)
            
            # Breakout avec volatilité élevée
            if bb_width > 0.1 and current_price > float(indicators.bb_upper):
                points += 50
            elif bb_width > 0.1 and current_price > float(indicators.bb_middle):
                points += 30
        
        # Range trading (30 points max)
        if (indicators.bb_upper and indicators.bb_lower and 
            indicators.bb_middle):
            bb_width = (float(indicators.bb_upper) - float(indicators.bb_lower)) / float(indicators.bb_middle)
            bb_position = (current_price - float(indicators.bb_lower)) / (float(indicators.bb_upper) - float(indicators.bb_lower))
            
            if bb_width < 0.05 and bb_position < 0.3:  # Range étroit, position basse
                points += 30
        
        # Risk premium (pénalité)
        if indicators.atr_14 and indicators.rsi_14:
            atr_ratio = float(indicators.atr_14) / current_price
            if atr_ratio > 0.02 and float(indicators.rsi_14) > 70:  # Haute volatilité + survente
                points -= 20
        
        return max(0, min(100, points))
    
    def _calculate_trend_score_with_history(self, indicators_df, price_df) -> float:
        """Calcule le score de tendance avec historique (0-100)"""
        if len(indicators_df) == 0 or len(price_df) == 0:
            return 50.0
        
        # Utiliser les données les plus récentes
        latest_indicators = indicators_df.iloc[-1]
        latest_price = price_df.iloc[-1]
        
        points = 0
        
        # Prix vs SMA 200 (20 points)
        if pd.notna(latest_indicators['sma_200']) and latest_price['close'] > latest_indicators['sma_200']:
            points += 20
        
        # SMA 50 vs SMA 200 (15 points)
        if (pd.notna(latest_indicators['sma_50']) and pd.notna(latest_indicators['sma_200']) and 
            latest_indicators['sma_50'] > latest_indicators['sma_200']):
            points += 15
        
        # SMA 20 vs SMA 50 (10 points)
        if (pd.notna(latest_indicators['sma_20']) and pd.notna(latest_indicators['sma_50']) and 
            latest_indicators['sma_20'] > latest_indicators['sma_50']):
            points += 10
        
        # EMA 20 vs EMA 50 (5 points)
        if (pd.notna(latest_indicators['ema_20']) and pd.notna(latest_indicators['ema_50']) and 
            latest_indicators['ema_20'] > latest_indicators['ema_50']):
            points += 5
        
        # MACD positif (10 points)
        if pd.notna(latest_indicators['macd']) and latest_indicators['macd'] > 0:
            points += 10
        
        # MACD histogram positif (10 points)
        if pd.notna(latest_indicators['macd_histogram']) and latest_indicators['macd_histogram'] > 0:
            points += 10
        
        # Position dans les Bollinger Bands (10 points)
        if (pd.notna(latest_indicators['bb_upper']) and pd.notna(latest_indicators['bb_lower']) and 
            pd.notna(latest_indicators['bb_middle']) and latest_price['close'] > latest_indicators['bb_middle']):
            bb_position = (latest_price['close'] - latest_indicators['bb_lower']) / (latest_indicators['bb_upper'] - latest_indicators['bb_lower'])
            if bb_position > 0.5:
                points += 10
        
        return min(100, points)
    
    def _calculate_momentum_score_with_history(self, indicators_df) -> float:
        """Calcule le score de momentum avec historique (0-100)"""
        if len(indicators_df) == 0:
            return 50.0
        
        latest_indicators = indicators_df.iloc[-1]
        points = 0
        
        # RSI (30 points max)
        if pd.notna(latest_indicators['rsi_14']):
            rsi = latest_indicators['rsi_14']
            if 50 < rsi < 70:
                points += 30
            elif rsi >= 70:
                points += 20
            elif 45 < rsi <= 50:
                points += 10
        
        # MACD slope (20 points max) - calculer la pente
        if len(indicators_df) >= 2 and pd.notna(latest_indicators['macd_histogram']):
            prev_histogram = indicators_df.iloc[-2]['macd_histogram']
            if pd.notna(prev_histogram):
                macd_slope = latest_indicators['macd_histogram'] - prev_histogram
                if macd_slope > 0:
                    points += 20
                elif abs(macd_slope) < 0.001:
                    points += 10
        
        # ROC (20 points max) - utiliser le ROC calculé
        if pd.notna(latest_indicators['roc']):
            roc = latest_indicators['roc']
            if roc > 0.5:
                points += 20
            elif roc > 0:
                points += 10
        
        # Stochastic (10 points max)
        if (pd.notna(latest_indicators['stochastic_k']) and pd.notna(latest_indicators['stochastic_d'])):
            if latest_indicators['stochastic_k'] > latest_indicators['stochastic_d']:
                points += 10
        
        return min(100, points)
    
    def _calculate_obos_score_with_history(self, indicators_df, price_df) -> float:
        """Calcule le score Overbought/Oversold avec historique (0-100)"""
        if len(indicators_df) == 0 or len(price_df) == 0:
            return 50.0
        
        latest_indicators = indicators_df.iloc[-1]
        latest_price = price_df.iloc[-1]
        points = 0
        
        # RSI (40 points max)
        if pd.notna(latest_indicators['rsi_14']):
            rsi = latest_indicators['rsi_14']
            if rsi < 30:
                points += 40
            elif 30 <= rsi < 40:
                points += 25
            elif 40 <= rsi < 50:
                points += 10
        
        # Williams %R (30 points max)
        if pd.notna(latest_indicators['williams_r']):
            wr = latest_indicators['williams_r']
            if wr < -80:
                points += 30
            elif -80 <= wr < -60:
                points += 15
        
        # Position Bollinger Bands (30 points max)
        if (pd.notna(latest_indicators['bb_upper']) and pd.notna(latest_indicators['bb_lower']) and 
            pd.notna(latest_indicators['bb_middle'])):
            bb_position = (latest_price['close'] - latest_indicators['bb_lower']) / (latest_indicators['bb_upper'] - latest_indicators['bb_lower'])
            if bb_position < 0.1:
                points += 30
            elif 0.1 <= bb_position < 0.3:
                points += 15
        
        return min(100, points)
    
    def _calculate_volume_score_with_history(self, indicators_df, price_df) -> float:
        """Calcule le score de volume avec historique (0-100)"""
        if len(indicators_df) == 0 or len(price_df) == 0:
            return 50.0
        
        latest_indicators = indicators_df.iloc[-1]
        latest_price = price_df.iloc[-1]
        points = 0
        
        # OBV direction (40 points max)
        if pd.notna(latest_indicators['obv']) and len(indicators_df) >= 20:
            obv_sma20 = indicators_df['obv'].rolling(20, min_periods=1).mean().iloc[-1]
            if pd.notna(obv_sma20):
                if latest_indicators['obv'] > obv_sma20:
                    points += 40
                else:
                    points += 20
        
        # Volume momentum (40 points max)
        if (pd.notna(latest_price['volume']) and pd.notna(latest_indicators['volume_sma_20']) and 
            pd.notna(latest_indicators['bb_middle']) and latest_price['close'] > latest_indicators['bb_middle']):
            volume_ratio = latest_price['volume'] / latest_indicators['volume_sma_20']
            if volume_ratio > 1.2:
                points += 40
            elif volume_ratio > 1.1:
                points += 20
        
        # Volume vs moyenne (20 points max)
        if pd.notna(latest_price['volume']) and pd.notna(latest_indicators['volume_sma_20']):
            if latest_price['volume'] > latest_indicators['volume_sma_20']:
                points += 20
        
        return min(100, points)
    
    def _calculate_volatility_structure_score_with_history(self, indicators_df, price_df) -> float:
        """Calcule le score de structure/volatilité avec historique (0-100)"""
        if len(indicators_df) == 0 or len(price_df) == 0:
            return 50.0
        
        latest_indicators = indicators_df.iloc[-1]
        latest_price = price_df.iloc[-1]
        points = 0
        
        # Breakout (50 points max)
        if (pd.notna(latest_indicators['bb_upper']) and pd.notna(latest_indicators['bb_lower']) and 
            pd.notna(latest_indicators['bb_middle']) and pd.notna(latest_indicators['atr_14'])):
            bb_width = (latest_indicators['bb_upper'] - latest_indicators['bb_lower']) / latest_indicators['bb_middle']
            
            # Breakout avec volatilité élevée
            if bb_width > 0.1 and latest_price['close'] > latest_indicators['bb_upper']:
                points += 50
            elif bb_width > 0.1 and latest_price['close'] > latest_indicators['bb_middle']:
                points += 30
        
        # Range trading (30 points max)
        if (pd.notna(latest_indicators['bb_upper']) and pd.notna(latest_indicators['bb_lower']) and 
            pd.notna(latest_indicators['bb_middle'])):
            bb_width = (latest_indicators['bb_upper'] - latest_indicators['bb_lower']) / latest_indicators['bb_middle']
            bb_position = (latest_price['close'] - latest_indicators['bb_lower']) / (latest_indicators['bb_upper'] - latest_indicators['bb_lower'])
            
            if bb_width < 0.05 and bb_position < 0.3:  # Range étroit, position basse
                points += 30
        
        # Risk premium (pénalité)
        if pd.notna(latest_indicators['atr_14']) and pd.notna(latest_indicators['rsi_14']):
            atr_ratio = latest_indicators['atr_14'] / latest_price['close']
            if atr_ratio > 0.02 and latest_indicators['rsi_14'] > 70:  # Haute volatilité + survente
                points -= 20
        
        return max(0, min(100, points))
    
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
        """Calcule le niveau de confiance basé sur la qualité des données"""
        try:
            # Calculer la confiance basée sur la cohérence des scores
            scores = [technical_score, sentiment_score, market_score, ml_score,
                     candlestick_score, garch_score, monte_carlo_score, markov_score, volatility_score]
            
            # Écart-type des scores (plus faible = plus cohérent = plus de confiance)
            score_std = np.std(scores)
            
            # Confiance de base basée sur la cohérence
            base_confidence = max(0.1, 1.0 - score_std)
            
            # Bonus pour les scores élevés (indique une forte conviction)
            high_scores = sum(1 for score in scores if score > 0.7)
            conviction_bonus = high_scores * 0.05
            
            # Bonus pour les scores faibles (indique une forte conviction négative)
            low_scores = sum(1 for score in scores if score < 0.3)
            conviction_bonus += low_scores * 0.05
            
            # Confiance finale
            confidence = min(1.0, base_confidence + conviction_bonus)
            
            return round(confidence, 3)
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence level: {e}")
            return 0.5
    
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