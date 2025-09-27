"""
Service pour la gestion des signaux avancés.

Ce service gère la persistance, la récupération et l'analyse
des signaux avancés dans la base de données.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
import logging

from ..models.advanced_signals import (
    AdvancedSignal, SignalPerformance, SignalMetrics, 
    SignalConfiguration, SignalBacktest
)
from .technical_analysis.advanced_signals import AdvancedSignalGenerator, SignalResult, SignalType, ConfidenceLevel

logger = logging.getLogger(__name__)


class AdvancedSignalService:
    """
    Service pour la gestion des signaux avancés.
    
    Ce service fournit des méthodes pour :
    - Sauvegarder et récupérer les signaux
    - Calculer les métriques de performance
    - Gérer les configurations
    - Effectuer des backtests
    """
    
    def __init__(self, db: Session):
        """
        Initialise le service.
        
        Args:
            db: Session de base de données
        """
        self.db = db
        self.signal_generator = AdvancedSignalGenerator()
    
    def save_signal(self, signal_result: SignalResult, symbol: str) -> AdvancedSignal:
        """
        Sauvegarde un signal dans la base de données.
        
        Args:
            signal_result: Résultat du signal à sauvegarder
            symbol: Symbole associé au signal
            
        Returns:
            Signal sauvegardé
        """
        try:
            # Créer l'entrée de signal
            signal = AdvancedSignal(
                symbol=symbol,
                signal_type=signal_result.signal_type.value,
                score=signal_result.score,
                confidence=signal_result.confidence,
                confidence_level=signal_result.confidence_level.value,
                strength=signal_result.strength,
                risk_level=signal_result.risk_level,
                time_horizon=signal_result.time_horizon,
                reasoning=signal_result.reasoning,
                indicators_used=signal_result.indicators_used,
                individual_signals=[
                    {
                        "signal": s.get("signal"),
                        "strength": s.get("strength"),
                        "score": s.get("score"),
                        "indicator": s.get("indicator"),
                        "reasoning": s.get("reasoning")
                    } for s in signal_result.individual_signals
                ],
                ml_signal=signal_result.ml_signal
            )
            
            self.db.add(signal)
            self.db.commit()
            self.db.refresh(signal)
            
            logger.info(f"Signal sauvegardé pour {symbol}: {signal_result.signal_type.value}")
            return signal
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du signal pour {symbol}: {e}")
            self.db.rollback()
            raise
    
    def get_signals(self, symbol: Optional[str] = None, 
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   signal_type: Optional[str] = None,
                   limit: int = 100) -> List[AdvancedSignal]:
        """
        Récupère les signaux selon les critères spécifiés.
        
        Args:
            symbol: Symbole à filtrer (optionnel)
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)
            signal_type: Type de signal à filtrer (optionnel)
            limit: Nombre maximum de résultats
            
        Returns:
            Liste des signaux correspondants
        """
        try:
            query = self.db.query(AdvancedSignal)
            
            if symbol:
                query = query.filter(AdvancedSignal.symbol == symbol)
            
            if start_date:
                query = query.filter(AdvancedSignal.created_at >= start_date)
            
            if end_date:
                query = query.filter(AdvancedSignal.created_at <= end_date)
            
            if signal_type:
                query = query.filter(AdvancedSignal.signal_type == signal_type)
            
            query = query.order_by(desc(AdvancedSignal.created_at)).limit(limit)
            
            return query.all()
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des signaux: {e}")
            return []
    
    def get_latest_signal(self, symbol: str) -> Optional[AdvancedSignal]:
        """
        Récupère le dernier signal pour un symbole.
        
        Args:
            symbol: Symbole à rechercher
            
        Returns:
            Dernier signal ou None
        """
        try:
            return self.db.query(AdvancedSignal)\
                .filter(AdvancedSignal.symbol == symbol)\
                .order_by(desc(AdvancedSignal.created_at))\
                .first()
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du dernier signal pour {symbol}: {e}")
            return None
    
    def calculate_signal_metrics(self, symbol: str, days: int = 30) -> Dict[str, Any]:
        """
        Calcule les métriques de performance des signaux pour un symbole.
        
        Args:
            symbol: Symbole à analyser
            days: Nombre de jours pour l'analyse
            
        Returns:
            Dictionnaire des métriques
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Récupérer les signaux de la période
            signals = self.db.query(AdvancedSignal)\
                .filter(and_(
                    AdvancedSignal.symbol == symbol,
                    AdvancedSignal.created_at >= start_date
                ))\
                .all()
            
            if not signals:
                return {}
            
            # Calculer les métriques de base
            total_signals = len(signals)
            buy_signals = len([s for s in signals if s.signal_type.startswith('BUY')])
            sell_signals = len([s for s in signals if s.signal_type.startswith('SELL')])
            hold_signals = len([s for s in signals if s.signal_type == 'HOLD'])
            strong_buy_signals = len([s for s in signals if s.signal_type == 'STRONG_BUY'])
            strong_sell_signals = len([s for s in signals if s.signal_type == 'STRONG_SELL'])
            
            # Métriques moyennes
            avg_confidence = sum(s.confidence for s in signals) / total_signals
            avg_score = sum(s.score for s in signals) / total_signals
            avg_strength = sum(s.strength for s in signals) / total_signals
            
            # Distribution des niveaux de confiance
            confidence_levels = {}
            for signal in signals:
                level = signal.confidence_level
                confidence_levels[level] = confidence_levels.get(level, 0) + 1
            
            # Distribution des types de signaux
            signal_types = {}
            for signal in signals:
                signal_type = signal.signal_type
                signal_types[signal_type] = signal_types.get(signal_type, 0) + 1
            
            return {
                "symbol": symbol,
                "period_days": days,
                "total_signals": total_signals,
                "buy_signals": buy_signals,
                "sell_signals": sell_signals,
                "hold_signals": hold_signals,
                "strong_buy_signals": strong_buy_signals,
                "strong_sell_signals": strong_sell_signals,
                "buy_ratio": buy_signals / total_signals if total_signals > 0 else 0.0,
                "sell_ratio": sell_signals / total_signals if total_signals > 0 else 0.0,
                "hold_ratio": hold_signals / total_signals if total_signals > 0 else 0.0,
                "avg_confidence": avg_confidence,
                "avg_score": avg_score,
                "avg_strength": avg_strength,
                "confidence_levels": confidence_levels,
                "signal_types": signal_types,
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des métriques pour {symbol}: {e}")
            return {}
    
    def save_signal_metrics(self, symbol: str, metrics: Dict[str, Any], 
                           period_start: datetime, period_end: datetime) -> SignalMetrics:
        """
        Sauvegarde les métriques de signaux dans la base de données.
        
        Args:
            symbol: Symbole associé
            metrics: Métriques à sauvegarder
            period_start: Début de la période
            period_end: Fin de la période
            
        Returns:
            Métriques sauvegardées
        """
        try:
            signal_metrics = SignalMetrics(
                symbol=symbol,
                period_start=period_start,
                period_end=period_end,
                total_signals=metrics.get("total_signals", 0),
                buy_signals=metrics.get("buy_signals", 0),
                sell_signals=metrics.get("sell_signals", 0),
                hold_signals=metrics.get("hold_signals", 0),
                strong_buy_signals=metrics.get("strong_buy_signals", 0),
                strong_sell_signals=metrics.get("strong_sell_signals", 0),
                avg_confidence=metrics.get("avg_confidence", 0.0),
                avg_score=metrics.get("avg_score", 0.0),
                avg_strength=metrics.get("avg_strength", 0.0),
                metrics_data=metrics
            )
            
            self.db.add(signal_metrics)
            self.db.commit()
            self.db.refresh(signal_metrics)
            
            logger.info(f"Métriques sauvegardées pour {symbol}")
            return signal_metrics
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des métriques pour {symbol}: {e}")
            self.db.rollback()
            raise
    
    def get_signal_performance(self, symbol: str, days: int = 30) -> List[SignalPerformance]:
        """
        Récupère les performances des signaux pour un symbole.
        
        Args:
            symbol: Symbole à analyser
            days: Nombre de jours pour l'analyse
            
        Returns:
            Liste des performances
        """
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            return self.db.query(SignalPerformance)\
                .filter(and_(
                    SignalPerformance.symbol == symbol,
                    SignalPerformance.created_at >= start_date
                ))\
                .order_by(desc(SignalPerformance.created_at))\
                .all()
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des performances pour {symbol}: {e}")
            return []
    
    def update_signal_performance(self, signal_id: int, entry_price: float,
                                exit_price: float, entry_date: datetime,
                                exit_date: datetime) -> SignalPerformance:
        """
        Met à jour la performance d'un signal.
        
        Args:
            signal_id: ID du signal
            entry_price: Prix d'entrée
            exit_price: Prix de sortie
            entry_date: Date d'entrée
            exit_date: Date de sortie
            
        Returns:
            Performance mise à jour
        """
        try:
            # Calculer les métriques de performance
            return_pct = ((exit_price - entry_price) / entry_price) * 100
            holding_period = (exit_date - entry_date).days
            was_profitable = return_pct > 0
            
            # Récupérer le signal original
            signal = self.db.query(AdvancedSignal).filter(AdvancedSignal.id == signal_id).first()
            if not signal:
                raise ValueError(f"Signal avec ID {signal_id} non trouvé")
            
            # Créer ou mettre à jour la performance
            performance = self.db.query(SignalPerformance)\
                .filter(SignalPerformance.signal_id == signal_id)\
                .first()
            
            if performance:
                performance.entry_price = entry_price
                performance.exit_price = exit_price
                performance.entry_date = entry_date
                performance.exit_date = exit_date
                performance.return_percentage = return_pct
                performance.holding_period_days = holding_period
                performance.was_profitable = was_profitable
            else:
                performance = SignalPerformance(
                    signal_id=signal_id,
                    symbol=signal.symbol,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    entry_date=entry_date,
                    exit_date=exit_date,
                    return_percentage=return_pct,
                    holding_period_days=holding_period,
                    was_profitable=was_profitable
                )
                self.db.add(performance)
            
            self.db.commit()
            self.db.refresh(performance)
            
            logger.info(f"Performance mise à jour pour le signal {signal_id}: {return_pct:.2f}%")
            return performance
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de la performance: {e}")
            self.db.rollback()
            raise
    
    def get_signal_configurations(self) -> List[SignalConfiguration]:
        """
        Récupère toutes les configurations de signaux.
        
        Returns:
            Liste des configurations
        """
        try:
            return self.db.query(SignalConfiguration)\
                .filter(SignalConfiguration.is_active == True)\
                .order_by(desc(SignalConfiguration.created_at))\
                .all()
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des configurations: {e}")
            return []
    
    def save_signal_configuration(self, name: str, description: str,
                                weights: Dict[str, float],
                                scoring_thresholds: Dict[str, float],
                                confidence_thresholds: Dict[str, float],
                                ml_integration: Optional[Dict[str, Any]] = None,
                                created_by: Optional[str] = None) -> SignalConfiguration:
        """
        Sauvegarde une nouvelle configuration de signaux.
        
        Args:
            name: Nom de la configuration
            description: Description
            weights: Poids des indicateurs
            scoring_thresholds: Seuils de scoring
            confidence_thresholds: Seuils de confiance
            ml_integration: Configuration ML (optionnel)
            created_by: Créateur (optionnel)
            
        Returns:
            Configuration sauvegardée
        """
        try:
            configuration = SignalConfiguration(
                name=name,
                description=description,
                weights=weights,
                scoring_thresholds=scoring_thresholds,
                confidence_thresholds=confidence_thresholds,
                ml_integration=ml_integration,
                created_by=created_by
            )
            
            self.db.add(configuration)
            self.db.commit()
            self.db.refresh(configuration)
            
            logger.info(f"Configuration sauvegardée: {name}")
            return configuration
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de la configuration: {e}")
            self.db.rollback()
            raise
    
    def generate_and_save_signal(self, symbol: str, high: pd.Series, low: pd.Series,
                               close: pd.Series, open_prices: pd.Series,
                               volume: Optional[pd.Series] = None,
                               ml_prediction: Optional[Dict[str, Any]] = None) -> AdvancedSignal:
        """
        Génère un signal avancé et le sauvegarde dans la base de données.
        
        Args:
            symbol: Symbole à analyser
            high: Série des prix hauts
            low: Série des prix bas
            close: Série des prix de clôture
            open_prices: Série des prix d'ouverture
            volume: Série des volumes (optionnel)
            ml_prediction: Prédiction ML (optionnel)
            
        Returns:
            Signal sauvegardé
        """
        try:
            # Générer le signal
            signal_result = self.signal_generator.generate_advanced_signal(
                symbol=symbol,
                high=high,
                low=low,
                close=close,
                open_prices=open_prices,
                volume=volume,
                ml_prediction=ml_prediction
            )
            
            # Sauvegarder le signal
            saved_signal = self.save_signal(signal_result, symbol)
            
            return saved_signal
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération et sauvegarde du signal pour {symbol}: {e}")
            raise
    
    def get_signal_summary(self, symbol: str, days: int = 7) -> Dict[str, Any]:
        """
        Récupère un résumé des signaux pour un symbole.
        
        Args:
            symbol: Symbole à analyser
            days: Nombre de jours pour l'analyse
            
        Returns:
            Résumé des signaux
        """
        try:
            # Récupérer le dernier signal
            latest_signal = self.get_latest_signal(symbol)
            
            # Calculer les métriques
            metrics = self.calculate_signal_metrics(symbol, days)
            
            # Récupérer les signaux récents
            recent_signals = self.get_signals(symbol=symbol, limit=10)
            
            return {
                "symbol": symbol,
                "latest_signal": {
                    "signal_type": latest_signal.signal_type if latest_signal else None,
                    "score": latest_signal.score if latest_signal else None,
                    "confidence": latest_signal.confidence if latest_signal else None,
                    "confidence_level": latest_signal.confidence_level if latest_signal else None,
                    "strength": latest_signal.strength if latest_signal else None,
                    "reasoning": latest_signal.reasoning if latest_signal else None,
                    "created_at": latest_signal.created_at.isoformat() if latest_signal else None
                },
                "metrics": metrics,
                "recent_signals": [
                    {
                        "signal_type": s.signal_type,
                        "score": s.score,
                        "confidence": s.confidence,
                        "created_at": s.created_at.isoformat()
                    } for s in recent_signals
                ],
                "summary_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du résumé pour {symbol}: {e}")
            return {}
