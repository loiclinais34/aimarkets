"""
Service de détection de bulles spéculatives
Phase 1 : Indicateurs fondamentaux et momentum
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta, date
from decimal import Decimal
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.database import HistoricalData, TechnicalIndicators
from app.models.bubble_indicators import BubbleIndicators
from app.services.financial_ratios_service import FinancialRatiosService

logger = logging.getLogger(__name__)


class BubbleDetectionService:
    """
    Service pour détecter les bulles spéculatives sur les valeurs technologiques
    """
    
    def __init__(self, db: Session = None):
        self.db = db
        self.logger = logging.getLogger(__name__)
        self.ratios_service = FinancialRatiosService()
        
        # Seuils de classification de bulle
        self.BUBBLE_THRESHOLDS = {
            'NORMAL': 30,
            'WATCH': 50,
            'RISK': 70,
            'PROBABLE': 85,
            'CRITICAL': 100
        }
        
        # Pondération des scores
        self.WEIGHTS = {
            'valuation': 0.30,
            'momentum': 0.25,
            'statistical': 0.25,
            'sentiment': 0.20
        }
        
        # Moyennes sectorielles de référence (Technology)
        # Ces valeurs seront calculées dynamiquement, mais on définit des valeurs par défaut
        self.TECH_SECTOR_AVERAGES = {
            'pe_ratio': 30.0,
            'ps_ratio': 10.0,
            'pb_ratio': 15.0,
            'peg_ratio': 2.0
        }
    
    def analyze_bubble_risk(
        self,
        symbol: str,
        analysis_date: date = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Analyse complète du risque de bulle pour un symbole
        
        Args:
            symbol: Symbole du titre
            analysis_date: Date d'analyse (par défaut aujourd'hui)
            db: Session de base de données
            
        Returns:
            Dict avec tous les indicateurs de bulle
        """
        if db is None:
            db = self.db
            
        if analysis_date is None:
            analysis_date = date.today()
        
        try:
            self.logger.info(f"Analyse de bulle pour {symbol} à la date {analysis_date}")
            
            # Calculer les différents scores
            valuation_score, valuation_details = self._calculate_valuation_score(symbol, analysis_date, db)
            momentum_score, momentum_details = self._calculate_momentum_score(symbol, analysis_date, db)
            statistical_score, statistical_details = self._calculate_statistical_score(symbol, analysis_date, db)
            sentiment_score, sentiment_details = self._calculate_sentiment_score(symbol, analysis_date, db)
            
            # Calculer le score composite
            bubble_score = (
                valuation_score * self.WEIGHTS['valuation'] +
                momentum_score * self.WEIGHTS['momentum'] +
                statistical_score * self.WEIGHTS['statistical'] +
                sentiment_score * self.WEIGHTS['sentiment']
            )
            
            # Déterminer le niveau de bulle
            bubble_level = self._determine_bubble_level(bubble_score)
            
            result = {
                'symbol': symbol,
                'analysis_date': analysis_date,
                'bubble_score': float(bubble_score),
                'bubble_level': bubble_level,
                'scores': {
                    'valuation': float(valuation_score),
                    'momentum': float(momentum_score),
                    'statistical': float(statistical_score),
                    'sentiment': float(sentiment_score)
                },
                'details': {
                    'valuation': valuation_details,
                    'momentum': momentum_details,
                    'statistical': statistical_details,
                    'sentiment': sentiment_details
                }
            }
            
            self.logger.info(f"Score de bulle pour {symbol}: {bubble_score:.2f} ({bubble_level})")
            return result
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'analyse de bulle pour {symbol}: {e}")
            return {
                'symbol': symbol,
                'analysis_date': analysis_date,
                'error': str(e),
                'bubble_score': 0,
                'bubble_level': 'UNKNOWN'
            }
    
    def _calculate_valuation_score(
        self,
        symbol: str,
        analysis_date: date,
        db: Session
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calcule le score de valorisation (0-100)
        Basé sur P/E, P/S, P/B ratios vs historique et secteur
        
        Utilise les ratios financiers réels de yfinance
        """
        try:
            # Récupérer les ratios financiers (cache ou fetch)
            ratios = self.ratios_service.get_or_fetch_ratios(symbol, db, max_age_days=7)
            
            if 'error' in ratios:
                self.logger.warning(f"Impossible de récupérer les ratios pour {symbol}, utilisation du proxy prix")
                # Fallback sur le proxy prix
                return self._calculate_valuation_score_proxy(symbol, analysis_date, db)
            
            # Extraire les ratios
            pe_ratio = ratios.get('pe_ratio')
            ps_ratio = ratios.get('ps_ratio')
            pb_ratio = ratios.get('pb_ratio')
            peg_ratio = ratios.get('peg_ratio')
            
            # Si aucun ratio disponible, utiliser le proxy
            if all(r is None for r in [pe_ratio, ps_ratio, pb_ratio]):
                self.logger.warning(f"Aucun ratio disponible pour {symbol}, utilisation du proxy prix")
                return self._calculate_valuation_score_proxy(symbol, analysis_date, db)
            
            # Calculer le score basé sur les ratios vs moyennes sectorielles
            score = 0.0
            details = {
                'pe_ratio': pe_ratio,
                'ps_ratio': ps_ratio,
                'pb_ratio': pb_ratio,
                'peg_ratio': peg_ratio,
                'sector': ratios.get('sector'),
                'industry': ratios.get('industry')
            }
            
            # Score P/E (max 35 points)
            if pe_ratio is not None and pe_ratio > 0:
                pe_avg = self.TECH_SECTOR_AVERAGES['pe_ratio']
                pe_deviation_pct = ((pe_ratio - pe_avg) / pe_avg) * 100
                details['pe_vs_sector_pct'] = round(pe_deviation_pct, 2)
                
                if pe_ratio > pe_avg * 1.5:  # 50% au-dessus de la moyenne
                    score += min(35, (pe_ratio / pe_avg - 1) * 50)
            
            # Score P/S (max 35 points)
            if ps_ratio is not None and ps_ratio > 0:
                ps_avg = self.TECH_SECTOR_AVERAGES['ps_ratio']
                ps_deviation_pct = ((ps_ratio - ps_avg) / ps_avg) * 100
                details['ps_vs_sector_pct'] = round(ps_deviation_pct, 2)
                
                if ps_ratio > ps_avg * 1.5:
                    score += min(35, (ps_ratio / ps_avg - 1) * 50)
            
            # Score P/B (max 30 points)
            if pb_ratio is not None and pb_ratio > 0:
                pb_avg = self.TECH_SECTOR_AVERAGES['pb_ratio']
                pb_deviation_pct = ((pb_ratio - pb_avg) / pb_avg) * 100
                details['pb_vs_sector_pct'] = round(pb_deviation_pct, 2)
                
                if pb_ratio > pb_avg * 1.5:
                    score += min(30, (pb_ratio / pb_avg - 1) * 40)
            
            # Bonus PEG ratio (si > 2, signe de surévaluation)
            if peg_ratio is not None and peg_ratio > 2:
                score += min(20, (peg_ratio - 2) * 10)
                details['peg_note'] = 'PEG > 2 indique une possible surévaluation'
            
            score = min(100, score)
            details['method'] = 'real_financial_ratios'
            
            return score, details
            
        except Exception as e:
            self.logger.error(f"Erreur calcul score valorisation pour {symbol}: {e}")
            return 50.0, {'error': str(e)}
    
    def _calculate_valuation_score_proxy(
        self,
        symbol: str,
        analysis_date: date,
        db: Session
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calcule le score de valorisation avec un proxy prix (fallback)
        """
        try:
            # Récupérer les données historiques
            historical_data = db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol,
                HistoricalData.date <= analysis_date
            ).order_by(HistoricalData.date.desc()).limit(365).all()
            
            if not historical_data or len(historical_data) < 30:
                return 50.0, {'status': 'insufficient_data'}
            
            # Utiliser un proxy basé sur le prix actuel vs moyenne historique
            current_price = float(historical_data[0].close)
            historical_prices = [float(h.close) for h in historical_data]
            
            avg_price_30d = np.mean(historical_prices[:30])
            avg_price_180d = np.mean(historical_prices[:min(180, len(historical_prices))])
            avg_price_365d = np.mean(historical_prices)
            
            # Calculer les écarts en %
            price_vs_30d = ((current_price - avg_price_30d) / avg_price_30d) * 100
            price_vs_180d = ((current_price - avg_price_180d) / avg_price_180d) * 100
            price_vs_365d = ((current_price - avg_price_365d) / avg_price_365d) * 100
            
            # Score basé sur la surévaluation relative
            score = 0.0
            
            if price_vs_30d > 20:
                score += min(30, price_vs_30d / 2)
            if price_vs_180d > 30:
                score += min(35, price_vs_180d / 2)
            if price_vs_365d > 40:
                score += min(35, price_vs_365d / 2)
            
            score = min(100, score)
            
            details = {
                'method': 'price_proxy_fallback',
                'current_price': current_price,
                'price_vs_30d_pct': round(price_vs_30d, 2),
                'price_vs_180d_pct': round(price_vs_180d, 2),
                'price_vs_365d_pct': round(price_vs_365d, 2)
            }
            
            return score, details
            
        except Exception as e:
            self.logger.error(f"Erreur calcul score valorisation proxy pour {symbol}: {e}")
            return 50.0, {'error': str(e)}
    
    def _calculate_momentum_score(
        self,
        symbol: str,
        analysis_date: date,
        db: Session
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calcule le score de momentum (0-100)
        Basé sur la croissance des prix, RSI, distance aux moyennes mobiles
        """
        try:
            # Récupérer les données historiques
            historical_data = db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol,
                HistoricalData.date <= analysis_date
            ).order_by(HistoricalData.date.desc()).limit(200).all()
            
            if not historical_data or len(historical_data) < 50:
                return 50.0, {'status': 'insufficient_data'}
            
            # Récupérer les indicateurs techniques
            latest_indicators = db.query(TechnicalIndicators).filter(
                TechnicalIndicators.symbol == symbol,
                TechnicalIndicators.date <= analysis_date
            ).order_by(TechnicalIndicators.date.desc()).first()
            
            current_price = float(historical_data[0].close)
            prices = [float(h.close) for h in historical_data]
            
            # Calculer les croissances de prix
            price_30d_ago = prices[min(30, len(prices)-1)]
            price_90d_ago = prices[min(90, len(prices)-1)]
            price_180d_ago = prices[min(180, len(prices)-1)]
            
            growth_30d = ((current_price - price_30d_ago) / price_30d_ago) * 100
            growth_90d = ((current_price - price_90d_ago) / price_90d_ago) * 100
            growth_180d = ((current_price - price_180d_ago) / price_180d_ago) * 100
            
            # Calculer l'accélération (dérivée seconde)
            acceleration = growth_30d - (growth_90d / 3)  # Approximation
            
            # Calculer les moyennes mobiles
            sma_50 = np.mean(prices[:min(50, len(prices))])
            sma_200 = np.mean(prices[:min(200, len(prices))])
            
            distance_sma50 = ((current_price - sma_50) / sma_50) * 100
            distance_sma200 = ((current_price - sma_200) / sma_200) * 100
            
            # RSI
            rsi = float(latest_indicators.rsi_14) if latest_indicators and latest_indicators.rsi_14 else 50.0
            
            # Calculer le score de momentum
            score = 0.0
            
            # Contribution de la croissance (max 40 points)
            if growth_30d > 20:
                score += min(15, growth_30d / 2)
            if growth_90d > 30:
                score += min(15, growth_90d / 3)
            if growth_180d > 50:
                score += min(10, growth_180d / 5)
            
            # Contribution de l'accélération (max 20 points)
            if acceleration > 10:
                score += min(20, acceleration)
            
            # Contribution de la distance aux SMA (max 20 points)
            if distance_sma50 > 10:
                score += min(10, distance_sma50)
            if distance_sma200 > 20:
                score += min(10, distance_sma200 / 2)
            
            # Contribution du RSI (max 20 points)
            if rsi > 70:
                score += min(20, (rsi - 70) * 2)
            
            score = min(100, score)
            
            details = {
                'growth_30d_pct': round(growth_30d, 2),
                'growth_90d_pct': round(growth_90d, 2),
                'growth_180d_pct': round(growth_180d, 2),
                'price_acceleration': round(acceleration, 4),
                'distance_from_sma50_pct': round(distance_sma50, 2),
                'distance_from_sma200_pct': round(distance_sma200, 2),
                'rsi_14d': round(rsi, 2),
                'sma_50': round(sma_50, 2),
                'sma_200': round(sma_200, 2)
            }
            
            return score, details
            
        except Exception as e:
            self.logger.error(f"Erreur calcul score momentum pour {symbol}: {e}")
            return 50.0, {'error': str(e)}
    
    def _calculate_statistical_score(
        self,
        symbol: str,
        analysis_date: date,
        db: Session
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calcule le score statistique (0-100)
        Basé sur les anomalies statistiques (z-score, volatilité, etc.)
        
        TODO Phase 2: Implémenter GSADF test, Markov regime, etc.
        """
        try:
            # Récupérer les données historiques
            historical_data = db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol,
                HistoricalData.date <= analysis_date
            ).order_by(HistoricalData.date.desc()).limit(200).all()
            
            if not historical_data or len(historical_data) < 60:
                return 50.0, {'status': 'insufficient_data'}
            
            prices = [float(h.close) for h in historical_data]
            current_price = prices[0]
            
            # Calculer le z-score du prix
            mean_price = np.mean(prices)
            std_price = np.std(prices)
            price_zscore = (current_price - mean_price) / std_price if std_price > 0 else 0
            
            # Calculer les rendements
            returns = [(prices[i] - prices[i+1]) / prices[i+1] for i in range(len(prices)-1)]
            
            # Volatilité actuelle (30 jours) vs historique (180 jours)
            recent_volatility = np.std(returns[:30]) if len(returns) >= 30 else 0
            historical_volatility = np.std(returns) if returns else 0
            volatility_ratio = recent_volatility / historical_volatility if historical_volatility > 0 else 1
            
            # Asymétrie (skewness) et kurtosis des rendements
            returns_skewness = float(pd.Series(returns).skew()) if len(returns) > 2 else 0
            returns_kurtosis = float(pd.Series(returns).kurtosis()) if len(returns) > 2 else 0
            
            # Calculer le score
            score = 0.0
            
            # Contribution du z-score (max 30 points)
            if price_zscore > 2:
                score += min(30, (price_zscore - 2) * 10)
            
            # Contribution de la volatilité (max 30 points)
            if volatility_ratio > 1.5:
                score += min(30, (volatility_ratio - 1.5) * 20)
            
            # Contribution de l'asymétrie négative (max 20 points)
            if returns_skewness < -0.5:
                score += min(20, abs(returns_skewness + 0.5) * 20)
            
            # Contribution du kurtosis élevé (max 20 points)
            if returns_kurtosis > 3:
                score += min(20, (returns_kurtosis - 3) * 5)
            
            score = min(100, score)
            
            details = {
                'price_zscore': round(price_zscore, 4),
                'volatility_ratio': round(volatility_ratio, 4),
                'recent_volatility': round(recent_volatility, 6),
                'historical_volatility': round(historical_volatility, 6),
                'returns_skewness': round(returns_skewness, 4),
                'returns_kurtosis': round(returns_kurtosis, 4),
                'note': 'Phase 1: Métriques de base. GSADF et régimes de Markov à implémenter en Phase 2.'
            }
            
            return score, details
            
        except Exception as e:
            self.logger.error(f"Erreur calcul score statistique pour {symbol}: {e}")
            return 50.0, {'error': str(e)}
    
    def _calculate_sentiment_score(
        self,
        symbol: str,
        analysis_date: date,
        db: Session
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calcule le score de sentiment (0-100)
        Basé sur les données de sentiment existantes
        
        TODO Phase 3: Ajouter détection FOMO, corrélation sectorielle
        """
        try:
            from app.models.database import SentimentData
            
            # Récupérer les données de sentiment récentes
            sentiment_data = db.query(SentimentData).filter(
                SentimentData.symbol == symbol,
                SentimentData.date <= analysis_date
            ).order_by(SentimentData.date.desc()).limit(30).all()
            
            if not sentiment_data or len(sentiment_data) < 7:
                return 50.0, {'status': 'insufficient_data'}
            
            sentiments = [float(s.news_sentiment_score) if s.news_sentiment_score else 0.5 for s in sentiment_data]
            current_sentiment = sentiments[0]
            avg_sentiment = np.mean(sentiments)
            
            # Compter les jours consécutifs avec sentiment extrême (>0.8)
            extreme_days = 0
            for s in sentiments:
                if s > 0.8:
                    extreme_days += 1
                else:
                    break
            
            # Calculer le score
            score = 0.0
            
            # Contribution du sentiment actuel (max 40 points)
            if current_sentiment > 0.7:
                score += min(40, (current_sentiment - 0.7) * 100)
            
            # Contribution du sentiment moyen (max 30 points)
            if avg_sentiment > 0.7:
                score += min(30, (avg_sentiment - 0.7) * 75)
            
            # Contribution des jours extrêmes (max 30 points)
            if extreme_days > 3:
                score += min(30, extreme_days * 5)
            
            score = min(100, score)
            
            details = {
                'current_sentiment': round(current_sentiment, 4),
                'avg_sentiment_30d': round(avg_sentiment, 4),
                'extreme_sentiment_days': extreme_days,
                'note': 'Phase 1: Sentiment de base. Divergence fondamentaux et FOMO à ajouter en Phase 3.'
            }
            
            return score, details
            
        except Exception as e:
            self.logger.error(f"Erreur calcul score sentiment pour {symbol}: {e}")
            return 50.0, {'error': str(e)}
    
    def _determine_bubble_level(self, bubble_score: float) -> str:
        """Détermine le niveau de bulle en fonction du score"""
        if bubble_score < self.BUBBLE_THRESHOLDS['NORMAL']:
            return 'NORMAL'
        elif bubble_score < self.BUBBLE_THRESHOLDS['WATCH']:
            return 'WATCH'
        elif bubble_score < self.BUBBLE_THRESHOLDS['RISK']:
            return 'RISK'
        elif bubble_score < self.BUBBLE_THRESHOLDS['PROBABLE']:
            return 'PROBABLE'
        else:
            return 'CRITICAL'
    
    def save_bubble_indicators(self, bubble_data: Dict[str, Any], db: Session) -> BubbleIndicators:
        """Sauvegarde les indicateurs de bulle dans la base de données"""
        try:
            # Vérifier si un enregistrement existe déjà pour cette date et ce symbole
            existing = db.query(BubbleIndicators).filter(
                BubbleIndicators.symbol == bubble_data['symbol'],
                BubbleIndicators.analysis_date == bubble_data['analysis_date']
            ).first()
            
            if existing:
                # Mettre à jour
                existing.bubble_score = bubble_data['bubble_score']
                existing.bubble_level = bubble_data['bubble_level']
                existing.valuation_score = bubble_data['scores']['valuation']
                existing.momentum_score = bubble_data['scores']['momentum']
                existing.statistical_score = bubble_data['scores']['statistical']
                existing.sentiment_score = bubble_data['scores']['sentiment']
                existing.valuation_details = bubble_data['details']['valuation']
                existing.momentum_details = bubble_data['details']['momentum']
                existing.statistical_details = bubble_data['details']['statistical']
                existing.sentiment_details = bubble_data['details']['sentiment']
                existing.updated_at = datetime.now()
                
                # Mettre à jour les champs individuels si disponibles
                self._update_individual_fields(existing, bubble_data['details'])
                
                db.commit()
                self.logger.info(f"Indicateurs de bulle mis à jour pour {bubble_data['symbol']}")
                return existing
            else:
                # Créer un nouvel enregistrement
                new_indicator = BubbleIndicators(
                    symbol=bubble_data['symbol'],
                    analysis_date=bubble_data['analysis_date'],
                    bubble_score=bubble_data['bubble_score'],
                    bubble_level=bubble_data['bubble_level'],
                    valuation_score=bubble_data['scores']['valuation'],
                    momentum_score=bubble_data['scores']['momentum'],
                    statistical_score=bubble_data['scores']['statistical'],
                    sentiment_score=bubble_data['scores']['sentiment'],
                    valuation_details=bubble_data['details']['valuation'],
                    momentum_details=bubble_data['details']['momentum'],
                    statistical_details=bubble_data['details']['statistical'],
                    sentiment_details=bubble_data['details']['sentiment']
                )
                
                # Mettre à jour les champs individuels si disponibles
                self._update_individual_fields(new_indicator, bubble_data['details'])
                
                db.add(new_indicator)
                db.commit()
                self.logger.info(f"Nouveaux indicateurs de bulle créés pour {bubble_data['symbol']}")
                return new_indicator
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des indicateurs de bulle: {e}")
            db.rollback()
            raise
    
    def _update_individual_fields(self, indicator: BubbleIndicators, details: Dict[str, Any]):
        """Met à jour les champs individuels de l'indicateur"""
        # Champs de valorisation
        val_details = details.get('valuation', {})
        
        # Ratios financiers
        if 'pe_ratio' in val_details and val_details['pe_ratio'] is not None:
            indicator.pe_ratio = val_details.get('pe_ratio')
        if 'ps_ratio' in val_details and val_details['ps_ratio'] is not None:
            indicator.ps_ratio = val_details.get('ps_ratio')
        if 'pb_ratio' in val_details and val_details['pb_ratio'] is not None:
            indicator.pb_ratio = val_details.get('pb_ratio')
        if 'peg_ratio' in val_details and val_details['peg_ratio'] is not None:
            indicator.peg_ratio = val_details.get('peg_ratio')
        
        # Écarts vs secteur
        if 'pe_vs_sector_pct' in val_details:
            indicator.pe_vs_sector_avg = val_details.get('pe_vs_sector_pct')
        if 'ps_vs_sector_pct' in val_details:
            indicator.ps_vs_sector_avg = val_details.get('ps_vs_sector_pct')
        if 'pb_vs_sector_pct' in val_details:
            indicator.pb_vs_sector_avg = val_details.get('pb_vs_sector_pct')
        
        # Fallback pour les proxys prix (méthode ancienne)
        if 'price_vs_30d_pct' in val_details:
            indicator.price_growth_30d = val_details.get('price_vs_30d_pct')
        if 'price_vs_180d_pct' in val_details:
            indicator.price_growth_180d = val_details.get('price_vs_180d_pct')
        
        # Champs de momentum
        mom_details = details.get('momentum', {})
        if 'growth_30d_pct' in mom_details:
            indicator.price_growth_30d = mom_details.get('growth_30d_pct')
        if 'growth_90d_pct' in mom_details:
            indicator.price_growth_90d = mom_details.get('growth_90d_pct')
        if 'growth_180d_pct' in mom_details:
            indicator.price_growth_180d = mom_details.get('growth_180d_pct')
        if 'price_acceleration' in mom_details:
            indicator.price_acceleration = mom_details.get('price_acceleration')
        if 'distance_from_sma50_pct' in mom_details:
            indicator.distance_from_sma50 = mom_details.get('distance_from_sma50_pct')
        if 'distance_from_sma200_pct' in mom_details:
            indicator.distance_from_sma200 = mom_details.get('distance_from_sma200_pct')
        if 'rsi_14d' in mom_details:
            indicator.rsi_14d = mom_details.get('rsi_14d')
        
        # Champs statistiques
        stat_details = details.get('statistical', {})
        if 'price_zscore' in stat_details:
            indicator.price_zscore = stat_details.get('price_zscore')
        if 'volatility_ratio' in stat_details:
            indicator.volatility_ratio = stat_details.get('volatility_ratio')
        if 'returns_skewness' in stat_details:
            indicator.returns_skewness = stat_details.get('returns_skewness')
        if 'returns_kurtosis' in stat_details:
            indicator.returns_kurtosis = stat_details.get('returns_kurtosis')
        
        # Champs de sentiment
        sent_details = details.get('sentiment', {})
        if 'extreme_sentiment_days' in sent_details:
            indicator.sentiment_extreme_days = sent_details.get('extreme_sentiment_days')
