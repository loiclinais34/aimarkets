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

# Import des services existants
from ..technical_analysis.signals import SignalGenerator
from ..technical_analysis.indicators import TechnicalIndicators
from ..technical_analysis.patterns import CandlestickPatterns
from ..technical_analysis.support_resistance import SupportResistanceAnalyzer
from ..sentiment_analysis.garch_models import GARCHModels
from ..sentiment_analysis.monte_carlo import MonteCarloSimulation
from ..sentiment_analysis.markov_chains import MarkovChainAnalysis
from ..sentiment_analysis.volatility_forecasting import VolatilityForecaster
from ..market_indicators.volatility import VolatilityIndicators
from ..market_indicators.momentum import MomentumIndicators

# Import des services ML existants
from ..ml_service import MLService
from ..search_session_service import SearchSessionService

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
        """Initialise tous les services d'analyse"""
        # Services d'analyse technique
        self.signal_generator = SignalGenerator()
        self.technical_indicators = TechnicalIndicators()
        self.candlestick_patterns = CandlestickPatterns()
        self.support_resistance = SupportResistanceAnalyzer()
        
        # Services d'analyse de sentiment
        self.garch_models = GARCHModels()
        self.monte_carlo = MonteCarloSimulation()
        self.markov_chains = MarkovChainAnalysis()
        self.volatility_forecaster = VolatilityForecaster()
        
        # Services d'indicateurs de marché
        self.volatility_indicators = VolatilityIndicators()
        self.momentum_indicators = MomentumIndicators()
        
        # Services ML existants
        self.ml_service = MLService()
        # Note: SearchSessionService nécessite une session DB, sera initialisé lors de l'utilisation
        
        # Configuration des poids pour le scoring composite
        self.scoring_weights = {
            'technical': 0.35,      # 35% pour l'analyse technique
            'sentiment': 0.30,      # 30% pour l'analyse de sentiment
            'market': 0.25,         # 25% pour les indicateurs de marché
            'ml': 0.10             # 10% pour l'analyse ML existante
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
            AnalysisResult: Résultat complet de l'analyse
        """
        try:
            logger.info(f"Starting comprehensive analysis for {symbol}")
            
            # 1. Analyse technique
            technical_analysis = await self._analyze_technical(symbol, time_horizon)
            technical_score = self._calculate_technical_score(technical_analysis)
            
            # 2. Analyse de sentiment
            sentiment_analysis = await self._analyze_sentiment(symbol, time_horizon)
            sentiment_score = self._calculate_sentiment_score(sentiment_analysis)
            
            # 3. Indicateurs de marché
            market_indicators = await self._analyze_market_indicators(symbol, time_horizon)
            market_score = self._calculate_market_score(market_indicators)
            
            # 4. Analyse ML (optionnelle)
            ml_analysis = None
            ml_score = 0.0
            if include_ml:
                ml_analysis = await self._analyze_ml(symbol)
                ml_score = self._calculate_ml_score(ml_analysis)
            
            # 5. Calcul du score composite
            composite_score = self._calculate_composite_score(
                technical_score, sentiment_score, market_score, ml_score
            )
            
            # 6. Calcul du niveau de confiance
            confidence_level = self._calculate_confidence_level(
                technical_score, sentiment_score, market_score, ml_score
            )
            
            # 7. Génération de recommandation
            recommendation = self._generate_recommendation(composite_score, confidence_level)
            
            # 8. Évaluation du risque
            risk_level = self._assess_risk_level(sentiment_analysis, market_indicators)
            
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
            
            logger.info(f"Analysis completed for {symbol}: Score={composite_score:.3f}, Confidence={confidence_level:.3f}")
            return result
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis for {symbol}: {e}")
            raise
    
    async def _analyze_technical(self, symbol: str, time_horizon: int) -> Dict[str, Any]:
        """Analyse technique complète"""
        try:
            # Récupérer les données historiques depuis la base
            from ...models.database import HistoricalData
            from ...core.database import get_db
            
            db = next(get_db())
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_horizon * 2)  # Plus de données pour les calculs
            
            historical_records = db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol,
                HistoricalData.date >= start_date.date(),
                HistoricalData.date <= end_date.date()
            ).order_by(HistoricalData.date).all()
            
            if not historical_records:
                raise ValueError(f"No historical data found for {symbol}")
            
            # Convertir en DataFrame
            data = []
            for record in historical_records:
                data.append({
                    'date': record.date,
                    'open': float(record.open),
                    'high': float(record.high),
                    'low': float(record.low),
                    'close': float(record.close),
                    'volume': int(record.volume)
                })
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Calculer les indicateurs techniques
            technical_signals = self.signal_generator.generate_composite_signals(df)
            
            # Détecter les patterns de chandeliers
            candlestick_patterns = self.candlestick_patterns.detect_all_patterns(df)
            
            # Identifier les niveaux de support/résistance
            support_resistance = self.support_resistance.identify_levels(df)
            
            db.close()
            
            return {
                'signals': technical_signals,
                'candlestick_patterns': candlestick_patterns,
                'support_resistance': support_resistance,
                'data_points': len(df),
                'analysis_period': f"{df.index[0].date()} to {df.index[-1].date()}"
            }
            
        except Exception as e:
            logger.error(f"Error in technical analysis for {symbol}: {e}")
            return {'error': str(e)}
    
    async def _analyze_sentiment(self, symbol: str, time_horizon: int) -> Dict[str, Any]:
        """Analyse de sentiment complète"""
        try:
            # Récupérer les données historiques depuis la base
            from ...models.database import HistoricalData
            from ...core.database import get_db
            
            db = next(get_db())
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_horizon * 2)
            
            historical_records = db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol,
                HistoricalData.date >= start_date.date(),
                HistoricalData.date <= end_date.date()
            ).order_by(HistoricalData.date).all()
            
            if not historical_records:
                raise ValueError(f"No historical data found for {symbol}")
            
            # Convertir en DataFrame
            data = []
            for record in historical_records:
                data.append({
                    'date': record.date,
                    'open': float(record.open),
                    'high': float(record.high),
                    'low': float(record.low),
                    'close': float(record.close),
                    'volume': int(record.volume)
                })
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Calculer les rendements
            returns = df['close'].pct_change().dropna()
            
            if len(returns) < 50:
                raise ValueError(f"Insufficient data for sentiment analysis: {len(returns)} points")
            
            # Analyse GARCH
            garch_analysis = self.garch_models.comprehensive_analysis(returns)
            
            # Simulation Monte Carlo
            current_price = float(df['close'].iloc[-1])
            drift = float(returns.mean() * 252)
            volatility = float(returns.std() * (252 ** 0.5))
            monte_carlo_analysis = self.monte_carlo.comprehensive_monte_carlo_analysis(
                current_price, volatility, drift, time_horizon, 10000
            )
            
            # Analyse Markov
            markov_analysis = self.markov_chains.comprehensive_markov_analysis(returns)
            
            # Prédiction de volatilité
            volatility_forecast = self.volatility_forecaster.comprehensive_volatility_forecast(returns, time_horizon)
            
            db.close()
            
            return {
                'garch_analysis': garch_analysis,
                'monte_carlo_analysis': monte_carlo_analysis,
                'markov_analysis': markov_analysis,
                'volatility_forecast': volatility_forecast,
                'data_points': len(returns),
                'analysis_period': f"{returns.index[0].date()} to {returns.index[-1].date()}"
            }
            
        except Exception as e:
            logger.error(f"Error in sentiment analysis for {symbol}: {e}")
            return {'error': str(e)}
    
    async def _analyze_market_indicators(self, symbol: str, time_horizon: int) -> Dict[str, Any]:
        """Analyse des indicateurs de marché"""
        try:
            # Récupérer les données historiques depuis la base
            from ...models.database import HistoricalData
            from ...core.database import get_db
            
            db = next(get_db())
            end_date = datetime.now()
            start_date = end_date - timedelta(days=time_horizon * 2)
            
            historical_records = db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol,
                HistoricalData.date >= start_date.date(),
                HistoricalData.date <= end_date.date()
            ).order_by(HistoricalData.date).all()
            
            if not historical_records:
                raise ValueError(f"No historical data found for {symbol}")
            
            # Convertir en DataFrame
            data = []
            for record in historical_records:
                data.append({
                    'date': record.date,
                    'open': float(record.open),
                    'high': float(record.high),
                    'low': float(record.low),
                    'close': float(record.close),
                    'volume': int(record.volume)
                })
            
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # Calculer les indicateurs de volatilité
            volatility_indicators = self.volatility_indicators.calculate_all_indicators(df)
            
            # Calculer les indicateurs de momentum
            momentum_indicators = self.momentum_indicators.calculate_all_indicators(df)
            
            db.close()
            
            return {
                'volatility_indicators': volatility_indicators,
                'momentum_indicators': momentum_indicators,
                'data_points': len(df),
                'analysis_period': f"{df.index[0].date()} to {df.index[-1].date()}"
            }
            
        except Exception as e:
            logger.error(f"Error in market indicators analysis for {symbol}: {e}")
            return {'error': str(e)}
    
    async def _analyze_ml(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Analyse ML existante"""
        try:
            # Utiliser le service ML existant pour analyser le symbole
            # Note: Cette partie nécessitera une adaptation selon l'API ML existante
            logger.info(f"ML analysis for {symbol} - placeholder implementation")
            
            # Pour l'instant, retourner une structure vide
            # TODO: Intégrer avec le système ML existant
            return {
                'ml_score': 0.5,  # Placeholder
                'ml_confidence': 0.5,  # Placeholder
                'ml_recommendation': 'HOLD',  # Placeholder
                'note': 'ML analysis not yet integrated'
            }
            
        except Exception as e:
            logger.error(f"Error in ML analysis for {symbol}: {e}")
            return None
    
    def _calculate_technical_score(self, technical_analysis: Dict[str, Any]) -> float:
        """Calcule le score technique (0-1)"""
        if 'error' in technical_analysis:
            return 0.0
        
        try:
            signals = technical_analysis.get('signals', {})
            patterns = technical_analysis.get('candlestick_patterns', {})
            support_resistance = technical_analysis.get('support_resistance', {})
            
            # Score basé sur les signaux techniques
            signal_score = 0.0
            if signals:
                # Logique de scoring basée sur les signaux
                # Plus de signaux positifs = score plus élevé
                signal_score = min(1.0, len(signals.get('buy_signals', [])) / 10.0)
            
            # Score basé sur les patterns
            pattern_score = 0.0
            if patterns:
                # Logique de scoring basée sur les patterns
                bullish_patterns = len([p for p in patterns.values() if p.get('sentiment') == 'bullish'])
                pattern_score = min(1.0, bullish_patterns / 5.0)
            
            # Score basé sur support/résistance
            sr_score = 0.5  # Score neutre par défaut
            if support_resistance:
                # Logique de scoring basée sur les niveaux
                # TODO: Implémenter la logique de scoring SR
                pass
            
            # Score composite technique
            technical_score = (signal_score * 0.5 + pattern_score * 0.3 + sr_score * 0.2)
            return min(1.0, max(0.0, technical_score))
            
        except Exception as e:
            logger.error(f"Error calculating technical score: {e}")
            return 0.0
    
    def _calculate_sentiment_score(self, sentiment_analysis: Dict[str, Any]) -> float:
        """Calcule le score de sentiment (0-1)"""
        if 'error' in sentiment_analysis:
            return 0.0
        
        try:
            garch_analysis = sentiment_analysis.get('garch_analysis', {})
            monte_carlo_analysis = sentiment_analysis.get('monte_carlo_analysis', {})
            markov_analysis = sentiment_analysis.get('markov_analysis', {})
            volatility_forecast = sentiment_analysis.get('volatility_forecast', {})
            
            # Score basé sur GARCH
            garch_score = 0.5  # Score neutre par défaut
            if garch_analysis and 'model_comparison' in garch_analysis:
                # Logique de scoring basée sur les métriques GARCH
                # TODO: Implémenter la logique de scoring GARCH
                pass
            
            # Score basé sur Monte Carlo
            mc_score = 0.5  # Score neutre par défaut
            if monte_carlo_analysis and 'risk_metrics' in monte_carlo_analysis:
                # Logique de scoring basée sur VaR et Expected Shortfall
                # TODO: Implémenter la logique de scoring Monte Carlo
                pass
            
            # Score basé sur Markov
            markov_score = 0.5  # Score neutre par défaut
            if markov_analysis and 'current_state' in markov_analysis:
                # Logique de scoring basée sur l'état de marché
                # TODO: Implémenter la logique de scoring Markov
                pass
            
            # Score basé sur la prédiction de volatilité
            volatility_score = 0.5  # Score neutre par défaut
            if volatility_forecast:
                # Logique de scoring basée sur la prédiction de volatilité
                # TODO: Implémenter la logique de scoring volatilité
                pass
            
            # Score composite sentiment
            sentiment_score = (garch_score * 0.3 + mc_score * 0.3 + markov_score * 0.2 + volatility_score * 0.2)
            return min(1.0, max(0.0, sentiment_score))
            
        except Exception as e:
            logger.error(f"Error calculating sentiment score: {e}")
            return 0.0
    
    def _calculate_market_score(self, market_indicators: Dict[str, Any]) -> float:
        """Calcule le score des indicateurs de marché (0-1)"""
        if 'error' in market_indicators:
            return 0.0
        
        try:
            volatility_indicators = market_indicators.get('volatility_indicators', {})
            momentum_indicators = market_indicators.get('momentum_indicators', {})
            
            # Score basé sur les indicateurs de volatilité
            volatility_score = 0.5  # Score neutre par défaut
            if volatility_indicators:
                # Logique de scoring basée sur les indicateurs de volatilité
                # TODO: Implémenter la logique de scoring volatilité
                pass
            
            # Score basé sur les indicateurs de momentum
            momentum_score = 0.5  # Score neutre par défaut
            if momentum_indicators:
                # Logique de scoring basée sur les indicateurs de momentum
                # TODO: Implémenter la logique de scoring momentum
                pass
            
            # Score composite marché
            market_score = (volatility_score * 0.4 + momentum_score * 0.6)
            return min(1.0, max(0.0, market_score))
            
        except Exception as e:
            logger.error(f"Error calculating market score: {e}")
            return 0.0
    
    def _calculate_ml_score(self, ml_analysis: Optional[Dict[str, Any]]) -> float:
        """Calcule le score ML (0-1)"""
        if not ml_analysis:
            return 0.0
        
        try:
            return float(ml_analysis.get('ml_score', 0.0))
        except Exception as e:
            logger.error(f"Error calculating ML score: {e}")
            return 0.0
    
    def _calculate_composite_score(self, technical_score: float, sentiment_score: float, 
                                 market_score: float, ml_score: float) -> float:
        """Calcule le score composite pondéré"""
        try:
            weights = self.scoring_weights
            
            composite_score = (
                technical_score * weights['technical'] +
                sentiment_score * weights['sentiment'] +
                market_score * weights['market'] +
                ml_score * weights['ml']
            )
            
            return min(1.0, max(0.0, composite_score))
            
        except Exception as e:
            logger.error(f"Error calculating composite score: {e}")
            return 0.0
    
    def _calculate_confidence_level(self, technical_score: float, sentiment_score: float,
                                  market_score: float, ml_score: float) -> float:
        """Calcule le niveau de confiance basé sur la convergence des scores"""
        try:
            scores = [technical_score, sentiment_score, market_score]
            if ml_score > 0:
                scores.append(ml_score)
            
            # Calculer l'écart-type des scores
            scores_array = np.array(scores)
            std_dev = np.std(scores_array)
            
            # Plus l'écart-type est faible, plus la confiance est élevée
            # Normaliser entre 0 et 1
            confidence = max(0.0, 1.0 - std_dev)
            
            return min(1.0, confidence)
            
        except Exception as e:
            logger.error(f"Error calculating confidence level: {e}")
            return 0.0
    
    def _generate_recommendation(self, composite_score: float, confidence_level: float) -> str:
        """Génère une recommandation basée sur le score composite et la confiance"""
        try:
            # Seuils de recommandation
            if composite_score >= 0.7 and confidence_level >= 0.6:
                return "STRONG_BUY"
            elif composite_score >= 0.6 and confidence_level >= 0.5:
                return "BUY"
            elif composite_score >= 0.4 and confidence_level >= 0.4:
                return "HOLD"
            elif composite_score >= 0.3:
                return "SELL"
            else:
                return "STRONG_SELL"
                
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return "HOLD"
    
    def _assess_risk_level(self, sentiment_analysis: Dict[str, Any], 
                          market_indicators: Dict[str, Any]) -> str:
        """Évalue le niveau de risque"""
        try:
            # Logique d'évaluation du risque basée sur l'analyse de sentiment et les indicateurs de marché
            # TODO: Implémenter la logique d'évaluation du risque
            
            # Pour l'instant, retourner un niveau de risque neutre
            return "MEDIUM"
            
        except Exception as e:
            logger.error(f"Error assessing risk level: {e}")
            return "HIGH"
    
    def get_analysis_summary(self, result: AnalysisResult) -> Dict[str, Any]:
        """Retourne un résumé de l'analyse"""
        return {
            'symbol': result.symbol,
            'analysis_date': result.analysis_date.isoformat(),
            'composite_score': result.composite_score,
            'confidence_level': result.confidence_level,
            'recommendation': result.recommendation,
            'risk_level': result.risk_level,
            'score_breakdown': {
                'technical': result.technical_score,
                'sentiment': result.sentiment_score,
                'market': result.market_score,
                'ml': result.ml_analysis.get('ml_score', 0.0) if result.ml_analysis else 0.0
            },
            'weights': self.scoring_weights
        }
