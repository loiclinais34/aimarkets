#!/usr/bin/env python3
"""
Script de test pour valider les performances de l'opportunité FANG
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import date, timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ml_backtesting.opportunity_validator import OpportunityValidator
from app.models.historical_opportunities import HistoricalOpportunities
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_fang_validation():
    """Test de validation des performances pour FANG"""
    
    logger.info("🧪 Test de validation des performances pour FANG")
    
    # Obtenir une session de base de données
    db = next(get_db())
    
    try:
        # Récupérer l'opportunité FANG générée
        fang_opportunity = db.query(HistoricalOpportunities).filter(
            HistoricalOpportunities.symbol == 'FANG'
        ).first()
        
        if not fang_opportunity:
            logger.error("Aucune opportunité FANG trouvée")
            return None
        
        logger.info(f"Opportunité FANG trouvée:")
        logger.info(f"  - Date: {fang_opportunity.opportunity_date}")
        logger.info(f"  - Recommandation: {fang_opportunity.recommendation}")
        logger.info(f"  - Score composite: {fang_opportunity.composite_score}")
        logger.info(f"  - Prix à la génération: ${fang_opportunity.price_at_generation}")
        
        # Créer le validateur
        validator = OpportunityValidator(db)
        
        # Valider les performances sur différentes périodes
        validation_periods = [1, 7, 30]  # 1 jour, 1 semaine, 1 mois
        
        logger.info(f"Validation des performances sur {len(validation_periods)} périodes...")
        
        results = await validator.validate_opportunities_batch(
            opportunities=[fang_opportunity],
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


async def test_validation_via_api():
    """Test de validation via l'API"""
    
    logger.info("🧪 Test de validation via l'API")
    
    try:
        import requests
        
        base_url = "http://localhost:8000/api/v1/ml-backtesting"
        
        # Test de validation via API
        payload = {
            "opportunity_ids": [1],  # ID de l'opportunité FANG
            "validation_periods": [1, 7, 30]
        }
        
        logger.info("Test de validation via API")
        response = requests.post(f"{base_url}/validate-opportunities", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Validation via API: {result['status']}")
            if result['status'] == 'success':
                logger.info(f"  - Opportunités validées: {result.get('validated_count', 0)}")
                logger.info(f"  - Périodes: {result.get('validation_periods', [])}")
        else:
            logger.warning(f"⚠️ Erreur API: {response.status_code} - {response.text}")
        
    except requests.exceptions.ConnectionError:
        logger.warning("⚠️ Serveur API non disponible")
    except Exception as e:
        logger.error(f"❌ Erreur lors du test API: {e}")


async def main():
    """Fonction principale de test"""
    
    logger.info("🚀 Test de validation des performances pour FANG")
    
    try:
        # Test 1: Validation directe
        results = await test_fang_validation()
        
        # Test 2: Validation via API
        await test_validation_via_api()
        
        if results:
            logger.info("✅ Tests de validation terminés avec succès!")
        else:
            logger.warning("⚠️ Aucun résultat de validation")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors des tests: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
