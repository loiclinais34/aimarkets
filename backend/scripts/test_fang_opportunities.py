#!/usr/bin/env python3
"""
Script de test pour générer des opportunités avec FANG (qui a des données complètes)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ml_backtesting.historical_opportunity_generator import HistoricalOpportunityGenerator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_fang_opportunities():
    """Test de génération d'opportunités pour FANG"""
    
    logger.info("🧪 Test de génération d'opportunités pour FANG")
    
    # Obtenir une session de base de données
    db = next(get_db())
    
    try:
        # Créer le générateur
        generator = HistoricalOpportunityGenerator(db)
        
        # Tester avec une date récente (2025-09-26)
        test_date = date(2025, 9, 26)
        logger.info(f"Date de test: {test_date}")
        
        # Générer des opportunités pour FANG
        opportunities = await generator.generate_opportunities_for_date(
            target_date=test_date,
            symbols=["FANG"],
            limit_symbols=1
        )
        
        logger.info(f"✅ {len(opportunities)} opportunités générées pour FANG")
        
        # Afficher les détails
        for opp in opportunities:
            logger.info(f"  - Symbole: {opp.symbol}")
            logger.info(f"  - Date: {opp.opportunity_date}")
            logger.info(f"  - Recommandation: {opp.recommendation}")
            logger.info(f"  - Score composite: {opp.composite_score:.3f}")
            logger.info(f"  - Score technique: {opp.technical_score:.3f}")
            logger.info(f"  - Score sentiment: {opp.sentiment_score:.3f}")
            logger.info(f"  - Score marché: {opp.market_score:.3f}")
            logger.info(f"  - Confiance: {opp.confidence_level}")
            logger.info(f"  - Risque: {opp.risk_level}")
            logger.info(f"  - Prix: ${opp.price_at_generation}")
            logger.info(f"  - Volume: {opp.volume_at_generation}")
        
        return opportunities
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


async def main():
    """Fonction principale de test"""
    
    logger.info("🚀 Test de génération d'opportunités pour FANG")
    
    try:
        opportunities = await test_fang_opportunities()
        
        if opportunities:
            logger.info("✅ Test réussi!")
        else:
            logger.warning("⚠️ Aucune opportunité générée")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
