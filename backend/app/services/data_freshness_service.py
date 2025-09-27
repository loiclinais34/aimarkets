"""
Service de vérification de la fraîcheur des données
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import logging

from app.core.database import get_db
from app.models.database import HistoricalData, SentimentData, TechnicalIndicators, SentimentIndicators
from app.models.market_indicators import MarketIndicators

logger = logging.getLogger(__name__)

class DataFreshnessService:
    """Service pour vérifier la fraîcheur des données"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_data_freshness_summary(self) -> Dict[str, any]:
        """
        Obtient un résumé de la fraîcheur de toutes les données
        
        Returns:
            Dict contenant les informations de fraîcheur
        """
        try:
            summary = {
                "timestamp": datetime.now().isoformat(),
                "historical_data": self._check_historical_data_freshness(),
                "sentiment_data": self._check_sentiment_data_freshness(),
                "technical_indicators": self._check_technical_indicators_freshness(),
                "sentiment_indicators": self._check_sentiment_indicators_freshness(),
                "market_indicators": self._check_market_indicators_freshness(),
                "recommendations": self._generate_recommendations()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error checking data freshness: {e}")
            return {"error": str(e)}
    
    def _check_historical_data_freshness(self) -> Dict[str, any]:
        """Vérifie la fraîcheur des données historiques"""
        try:
            # Dernière date de données historiques
            latest_date = self.db.query(func.max(HistoricalData.date)).scalar()
            
            # Nombre total de symboles avec données
            total_symbols = self.db.query(func.count(func.distinct(HistoricalData.symbol))).scalar()
            
            # Symboles avec données récentes (derniers 5 jours)
            recent_cutoff = datetime.now().date() - timedelta(days=5)
            recent_symbols = self.db.query(func.count(func.distinct(HistoricalData.symbol)))\
                .filter(HistoricalData.date >= recent_cutoff)\
                .scalar()
            
            return {
                "latest_date": latest_date.isoformat() if latest_date else None,
                "total_symbols": total_symbols,
                "recent_symbols": recent_symbols,
                "freshness_score": self._calculate_freshness_score(latest_date),
                "needs_update": self._needs_update(latest_date, days_threshold=1)
            }
            
        except Exception as e:
            logger.error(f"Error checking historical data freshness: {e}")
            return {"error": str(e)}
    
    def _check_sentiment_data_freshness(self) -> Dict[str, any]:
        """Vérifie la fraîcheur des données de sentiment"""
        try:
            latest_date = self.db.query(func.max(SentimentData.date)).scalar()
            total_symbols = self.db.query(func.count(func.distinct(SentimentData.symbol))).scalar()
            
            recent_cutoff = datetime.now().date() - timedelta(days=2)
            recent_symbols = self.db.query(func.count(func.distinct(SentimentData.symbol)))\
                .filter(SentimentData.date >= recent_cutoff)\
                .scalar()
            
            return {
                "latest_date": latest_date.isoformat() if latest_date else None,
                "total_symbols": total_symbols,
                "recent_symbols": recent_symbols,
                "freshness_score": self._calculate_freshness_score(latest_date),
                "needs_update": self._needs_update(latest_date, days_threshold=1)
            }
            
        except Exception as e:
            logger.error(f"Error checking sentiment data freshness: {e}")
            return {"error": str(e)}
    
    def _check_technical_indicators_freshness(self) -> Dict[str, any]:
        """Vérifie la fraîcheur des indicateurs techniques"""
        try:
            latest_date = self.db.query(func.max(TechnicalIndicators.date)).scalar()
            total_symbols = self.db.query(func.count(func.distinct(TechnicalIndicators.symbol))).scalar()
            
            recent_cutoff = datetime.now().date() - timedelta(days=1)
            recent_symbols = self.db.query(func.count(func.distinct(TechnicalIndicators.symbol)))\
                .filter(TechnicalIndicators.date >= recent_cutoff)\
                .scalar()
            
            return {
                "latest_date": latest_date.isoformat() if latest_date else None,
                "total_symbols": total_symbols,
                "recent_symbols": recent_symbols,
                "freshness_score": self._calculate_freshness_score(latest_date),
                "needs_update": self._needs_update(latest_date, days_threshold=1)
            }
            
        except Exception as e:
            logger.error(f"Error checking technical indicators freshness: {e}")
            return {"error": str(e)}
    
    def _check_sentiment_indicators_freshness(self) -> Dict[str, any]:
        """Vérifie la fraîcheur des indicateurs de sentiment"""
        try:
            latest_date = self.db.query(func.max(SentimentIndicators.date)).scalar()
            total_symbols = self.db.query(func.count(func.distinct(SentimentIndicators.symbol))).scalar()
            
            recent_cutoff = datetime.now().date() - timedelta(days=1)
            recent_symbols = self.db.query(func.count(func.distinct(SentimentIndicators.symbol)))\
                .filter(SentimentIndicators.date >= recent_cutoff)\
                .scalar()
            
            return {
                "latest_date": latest_date.isoformat() if latest_date else None,
                "total_symbols": total_symbols,
                "recent_symbols": recent_symbols,
                "freshness_score": self._calculate_freshness_score(latest_date),
                "needs_update": self._needs_update(latest_date, days_threshold=1)
            }
            
        except Exception as e:
            logger.error(f"Error checking sentiment indicators freshness: {e}")
            return {"error": str(e)}
    
    def _check_market_indicators_freshness(self) -> Dict[str, any]:
        """Vérifie la fraîcheur des indicateurs de marché"""
        try:
            latest_date = self.db.query(func.max(MarketIndicators.created_at)).scalar()
            total_indicators = self.db.query(func.count(MarketIndicators.id)).scalar()
            
            recent_cutoff = datetime.now() - timedelta(days=1)
            recent_indicators = self.db.query(func.count(MarketIndicators.id))\
                .filter(MarketIndicators.created_at >= recent_cutoff)\
                .scalar()
            
            return {
                "latest_date": latest_date.isoformat() if latest_date else None,
                "total_indicators": total_indicators,
                "recent_indicators": recent_indicators,
                "freshness_score": self._calculate_freshness_score(latest_date),
                "needs_update": self._needs_update(latest_date, days_threshold=1)
            }
            
        except Exception as e:
            logger.error(f"Error checking market indicators freshness: {e}")
            return {"error": str(e)}
    
    def _calculate_freshness_score(self, latest_date: Optional[datetime]) -> float:
        """Calcule un score de fraîcheur (0-1)"""
        if not latest_date:
            return 0.0
        
        if isinstance(latest_date, datetime):
            days_ago = (datetime.now() - latest_date).days
        else:
            days_ago = (datetime.now().date() - latest_date).days
        
        if days_ago == 0:
            return 1.0
        elif days_ago <= 1:
            return 0.8
        elif days_ago <= 3:
            return 0.6
        elif days_ago <= 7:
            return 0.4
        else:
            return max(0.0, 1.0 - (days_ago / 30))
    
    def _needs_update(self, latest_date: Optional[datetime], days_threshold: int = 1) -> bool:
        """Détermine si les données ont besoin d'être mises à jour"""
        if not latest_date:
            return True
        
        if isinstance(latest_date, datetime):
            days_ago = (datetime.now() - latest_date).days
        else:
            days_ago = (datetime.now().date() - latest_date).days
        
        return days_ago > days_threshold
    
    def _generate_recommendations(self) -> List[str]:
        """Génère des recommandations basées sur la fraîcheur des données"""
        recommendations = []
        
        # Cette méthode sera implémentée après avoir vérifié toutes les données
        # Pour l'instant, retournons des recommandations génériques
        
        recommendations.append("Vérifier la fraîcheur des données historiques")
        recommendations.append("Calculer les indicateurs techniques manquants")
        recommendations.append("Mettre à jour les indicateurs de sentiment")
        recommendations.append("Recalculer les indicateurs de marché")
        
        return recommendations
    
    def get_symbols_needing_update(self, data_type: str = "all") -> List[str]:
        """
        Obtient la liste des symboles qui ont besoin d'être mis à jour
        
        Args:
            data_type: Type de données à vérifier ("historical", "sentiment", "technical", "all")
        
        Returns:
            Liste des symboles nécessitant une mise à jour
        """
        try:
            symbols_needing_update = []
            
            if data_type in ["historical", "all"]:
                # Symboles avec données historiques obsolètes
                recent_cutoff = datetime.now().date() - timedelta(days=1)
                stale_symbols = self.db.query(HistoricalData.symbol)\
                    .filter(HistoricalData.date < recent_cutoff)\
                    .distinct()\
                    .all()
                symbols_needing_update.extend([s[0] for s in stale_symbols])
            
            if data_type in ["sentiment", "all"]:
                # Symboles avec données de sentiment obsolètes
                recent_cutoff = datetime.now().date() - timedelta(days=1)
                stale_symbols = self.db.query(SentimentData.symbol)\
                    .filter(SentimentData.date < recent_cutoff)\
                    .distinct()\
                    .all()
                symbols_needing_update.extend([s[0] for s in stale_symbols])
            
            # Retourner les symboles uniques
            return list(set(symbols_needing_update))
            
        except Exception as e:
            logger.error(f"Error getting symbols needing update: {e}")
            return []
