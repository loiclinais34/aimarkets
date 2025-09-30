#!/usr/bin/env python3
"""
Script de test pour valider les performances avec des données historiques disponibles
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ml_backtesting.historical_opportunity_generator import HistoricalOpportunityGenerator
from app.services.ml_backtesting.opportunity_validator import OpportunityValidator
from app.models.historical_opportunities import HistoricalOpportunities
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_validation_with_historical_data():
    """Test de validation avec des données historiques disponibles"""
    
    logger.info("🧪 Test de validation avec des données historiques")
    
    # Obtenir une session de base de données
    db = next(get_db())
    
    try:
        # Générer une opportunité pour une date avec des données futures disponibles
        # Utiliser 2025-09-22 comme date d'opportunité (données jusqu'au 26/09)
        opportunity_date = date(2025, 9, 22)
        
        logger.info(f"Génération d'opportunité pour FANG le {opportunity_date}")
        
        # Créer le générateur
        generator = HistoricalOpportunityGenerator(db)
        
        # Générer l'opportunité
        opportunities = await generator.generate_opportunities_for_date(
            target_date=opportunity_date,
            symbols=["FANG"],
            limit_symbols=1
        )
        
        if not opportunities:
            logger.error("Aucune opportunité générée")
            return None
        
        opportunity = opportunities[0]
        logger.info(f"Opportunité générée:")
        logger.info(f"  - Date: {opportunity.opportunity_date}")
        logger.info(f"  - Recommandation: {opportunity.recommendation}")
        logger.info(f"  - Score composite: {opportunity.composite_score}")
        logger.info(f"  - Prix: ${opportunity.price_at_generation}")
        
        # Valider les performances sur des périodes avec des données disponibles
        # 1 jour = 2025-09-23, 2 jours = 2025-09-24, 4 jours = 2025-09-26
        validation_periods = [1, 2, 4]
        
        logger.info(f"Validation des performances sur {len(validation_periods)} périodes...")
        
        # Créer le validateur
        validator = OpportunityValidator(db)
        
        results = await validator.validate_opportunities_batch(
            opportunities=[opportunity],
            validation_periods=validation_periods
        )
        
        logger.info(f"✅ {len(results)} validations effectuées")
        
        # Afficher les résultats détaillés
        for result in results:
            logger.info(f"  - ID: {result['opportunity_id']}")
            logger.info(f"  - Symbole: {result['symbol']}")
            logger.info(f"  - Date d'opportunité: {result['opportunity_date']}")
            logger.info(f"  - Score de performance: {result.get('performance_score', 'N/A')}")
            
            validation_results = result.get('validation_results', {})
            for period, data in validation_results.items():
                logger.info(f"    {period}:")
                logger.info(f"      - Rendement réel: {data.get('actual_return', 'N/A')}%")
                logger.info(f"      - Rendement prédit: {data.get('predicted_return', 'N/A')}%")
                logger.info(f"      - Recommandation correcte: {data.get('recommendation_correct', 'N/A')}")
                logger.info(f"      - Catégorie de performance: {data.get('performance_category', 'N/A')}")
                logger.info(f"      - Prix final: ${data.get('final_price', 'N/A')}")
                logger.info(f"      - Sharpe ratio: {data.get('sharpe_ratio', 'N/A')}")
                logger.info(f"      - Max drawdown: {data.get('max_drawdown', 'N/A')}%")
                logger.info(f"      - Volatilité: {data.get('volatility', 'N/A')}%")
                logger.info(f"      - Beta: {data.get('beta', 'N/A')}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la validation: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


async def main():
    """Fonction principale de test"""
    
    logger.info("🚀 Test de validation avec des données historiques")
    
    try:
        results = await test_validation_with_historical_data()
        
        if results:
            logger.info("✅ Test de validation terminé avec succès!")
        else:
            logger.warning("⚠️ Aucun résultat de validation")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
