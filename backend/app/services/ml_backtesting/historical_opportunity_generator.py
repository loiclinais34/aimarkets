"""
Générateur d'opportunités historiques pour le backtesting ML
Utilise le même service d'analyse que les opportunités réelles
"""

from typing import List, Optional, Dict, Any
from datetime import date, datetime
from sqlalchemy.orm import Session
import logging

from app.models.database import HistoricalData
from app.models.historical_opportunities import HistoricalOpportunities
from app.services.advanced_analysis.advanced_trading_analysis import AdvancedTradingAnalysis

logger = logging.getLogger(__name__)


class HistoricalOpportunityGenerator:
    """
    Générateur d'opportunités historiques pour le backtesting ML
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.advanced_analysis = AdvancedTradingAnalysis()
    
    async def generate_opportunities_for_date(
        self, 
        target_date: date, 
        symbols: Optional[List[str]] = None,
        limit_symbols: Optional[int] = None
    ) -> List[HistoricalOpportunities]:
        """
        Génère des opportunités historiques pour une date donnée
        
        Args:
            target_date: Date pour laquelle générer les opportunités
            symbols: Liste des symboles à analyser (optionnel)
            limit_symbols: Limite du nombre de symboles à traiter
            
        Returns:
            Liste des opportunités historiques générées
        """
        try:
            logger.info(f"Génération d'opportunités historiques pour la date {target_date}")
            
            # Récupérer les symboles disponibles si non spécifiés
            if not symbols:
                symbols_query = self.db.query(HistoricalData.symbol).distinct()
                if limit_symbols:
                    symbols_query = symbols_query.limit(limit_symbols)
                symbols = [s[0] for s in symbols_query.all()]
            
            opportunities = []
            
            for symbol in symbols:
                try:
                    opportunity = await self._generate_opportunity_for_symbol_date(symbol, target_date)
                    if opportunity:
                        opportunities.append(opportunity)
                        logger.info(f"Opportunité générée pour {symbol} le {target_date}")
                except Exception as e:
                    logger.error(f"Erreur lors de la génération pour {symbol}: {e}")
                    continue
            
            # Sauvegarder en base de données
            if opportunities:
                self.db.add_all(opportunities)
                self.db.commit()
                logger.info(f"{len(opportunities)} opportunités historiques sauvegardées pour {target_date}")
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'opportunités pour {target_date}: {e}")
            self.db.rollback()
            return []
    
    async def _generate_opportunity_for_symbol_date(self, symbol: str, target_date: date) -> Optional[HistoricalOpportunities]:
        """
        Génère une opportunité pour un symbole à une date donnée
        """
        try:
            # Vérifier qu'il y a des données de prix pour cette date
            price_data = self.db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol,
                HistoricalData.date == target_date
            ).first()
            
            if not price_data:
                logger.warning(f"Aucune donnée de prix pour {symbol} le {target_date}")
                return None
            
            # Utiliser le service d'analyse avancée pour générer l'analyse
            # Ce service utilise exactement les mêmes calculs que les opportunités réelles
            analysis_result = await self.advanced_analysis.analyze_opportunity(
                symbol=symbol,
                time_horizon=30,
                include_ml=True,
                db=self.db,
                target_date=target_date
            )
            
            # Créer l'opportunité historique
            opportunity = HistoricalOpportunities(
                symbol=symbol,
                opportunity_date=target_date,
                generation_timestamp=datetime.now(),
                
                # Scores (utilisant les mêmes calculs que les opportunités réelles)
                technical_score=analysis_result.technical_score,
                sentiment_score=analysis_result.sentiment_score,
                market_score=analysis_result.market_score,
                ml_score=analysis_result.ml_score,
                composite_score=analysis_result.composite_score,
                
                # Recommandations (utilisant les mêmes logiques que les opportunités réelles)
                recommendation=analysis_result.recommendation,
                confidence_level=analysis_result.confidence_level,
                risk_level=analysis_result.risk_level,
                
                # Données contextuelles
                price_at_generation=price_data.close,
                volume_at_generation=price_data.volume,
                market_cap_at_generation=None,  # Pas disponible dans HistoricalData
                
                # Données détaillées des indicateurs (mêmes structures que les opportunités réelles)
                technical_indicators_data=analysis_result.technical_analysis,
                sentiment_indicators_data=analysis_result.sentiment_analysis,
                market_indicators_data=analysis_result.market_indicators,
                ml_indicators_data=analysis_result.ml_analysis
            )
            
            return opportunity
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'opportunité pour {symbol} le {target_date}: {e}")
            return None
    
    async def generate_opportunities_for_date_range(
        self, 
        start_date: date, 
        end_date: date,
        symbols: Optional[List[str]] = None,
        limit_symbols: Optional[int] = None
    ) -> List[HistoricalOpportunities]:
        """
        Génère des opportunités historiques pour une plage de dates
        
        Args:
            start_date: Date de début
            end_date: Date de fin
            symbols: Liste des symboles à analyser (optionnel)
            limit_symbols: Limite du nombre de symboles à traiter
            
        Returns:
            Liste des opportunités historiques générées
        """
        try:
            logger.info(f"Génération d'opportunités historiques du {start_date} au {end_date}")
            
            all_opportunities = []
            current_date = start_date
            
            while current_date <= end_date:
                # Générer les opportunités pour cette date
                date_opportunities = await self.generate_opportunities_for_date(
                    target_date=current_date,
                    symbols=symbols,
                    limit_symbols=limit_symbols
                )
                
                all_opportunities.extend(date_opportunities)
                
                # Passer à la date suivante
                from datetime import timedelta
                current_date += timedelta(days=1)
            
            logger.info(f"Génération terminée: {len(all_opportunities)} opportunités créées")
            return all_opportunities
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'opportunités pour la plage {start_date}-{end_date}: {e}")
            return []