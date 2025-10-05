#!/usr/bin/env python3
"""
Script de test pour les opportunités historiques
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
from app.services.ml_backtesting.backtesting_pipeline import BacktestingPipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_historical_opportunity_generation():
    """Test de génération d'opportunités historiques"""
    
    logger.info("🧪 Test de génération d'opportunités historiques")
    
    # Obtenir une session de base de données
    db = next(get_db())
    
    try:
        # Créer le générateur
        generator = HistoricalOpportunityGenerator(db)
        
        # Test avec une date récente (il y a 30 jours)
        test_date = date.today() - timedelta(days=30)
        
        logger.info(f"Génération d'opportunités pour le {test_date}")
        
        # Générer des opportunités pour quelques symboles
        opportunities = await generator.generate_opportunities_for_date(
            target_date=test_date,
            symbols=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"],
            limit_symbols=5
        )
        
        logger.info(f"✅ {len(opportunities)} opportunités générées")
        
        # Afficher quelques détails
        for opp in opportunities[:3]:
            logger.info(f"  - {opp.symbol}: {opp.recommendation} (score: {opp.composite_score:.3f})")
        
        return opportunities
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        raise
    finally:
        db.close()


async def test_opportunity_validation():
    """Test de validation des opportunités"""
    
    logger.info("🧪 Test de validation des opportunités")
    
    # Obtenir une session de base de données
    db = next(get_db())
    
    try:
        # Récupérer quelques opportunités existantes
        from app.models.historical_opportunities import HistoricalOpportunities
        
        opportunities = db.query(HistoricalOpportunities).limit(3).all()
        
        if not opportunities:
            logger.warning("Aucune opportunité trouvée pour le test")
            return
        
        logger.info(f"Validation de {len(opportunities)} opportunités")
        
        # Créer le validateur
        validator = OpportunityValidator(db)
        
        # Valider les opportunités
        results = await validator.validate_opportunities_batch(
            opportunities=opportunities,
            validation_periods=[1, 7, 30]
        )
        
        logger.info(f"✅ {len(results)} opportunités validées")
        
        # Afficher quelques résultats
        for result in results[:2]:
            logger.info(f"  - {result['symbol']}: performance_score = {result.get('performance_score', 'N/A')}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        raise
    finally:
        db.close()


async def test_backtesting_pipeline():
    """Test du pipeline de backtesting complet"""
    
    logger.info("🧪 Test du pipeline de backtesting")
    
    # Obtenir une session de base de données
    db = next(get_db())
    
    try:
        # Créer le pipeline
        pipeline = BacktestingPipeline(db)
        
        # Test rapide sur une date
        test_date = date.today() - timedelta(days=60)
        
        logger.info(f"Backtest rapide pour le {test_date}")
        
        # Exécuter le backtest rapide
        results = await pipeline.run_quick_backtest(
            test_date=test_date,
            symbols=["AAPL", "MSFT"],
            limit_symbols=2
        )
        
        logger.info(f"✅ Backtest terminé: {results['status']}")
        
        if results['status'] == 'success':
            logger.info(f"  - Opportunités générées: {results['opportunities_count']}")
            logger.info(f"  - Analyse: {len(results.get('analysis_results', {}))}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        raise
    finally:
        db.close()


async def test_api_endpoints():
    """Test des endpoints API"""
    
    logger.info("🧪 Test des endpoints API")
    
    try:
        import requests
        
        base_url = "http://localhost:8000/api/v1/ml-backtesting"
        
        # Test de l'endpoint de statistiques
        logger.info("Test de l'endpoint /stats")
        response = requests.get(f"{base_url}/stats")
        
        if response.status_code == 200:
            stats = response.json()
            logger.info(f"✅ Stats récupérées: {stats['stats']['total_opportunities']} opportunités")
        else:
            logger.warning(f"⚠️ Endpoint /stats non disponible (status: {response.status_code})")
        
        # Test de l'endpoint de backtest rapide
        logger.info("Test de l'endpoint /quick-backtest")
        
        test_date = (date.today() - timedelta(days=30)).isoformat()
        payload = {
            "test_date": test_date,
            "symbols": ["AAPL"],
            "limit_symbols": 1
        }
        
        response = requests.post(f"{base_url}/quick-backtest", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Backtest rapide: {result['status']}")
        else:
            logger.warning(f"⚠️ Endpoint /quick-backtest non disponible (status: {response.status_code})")
        
    except requests.exceptions.ConnectionError:
        logger.warning("⚠️ Serveur API non disponible - test des endpoints ignoré")
    except Exception as e:
        logger.error(f"❌ Erreur lors du test des endpoints: {e}")


async def main():
    """Fonction principale de test"""
    
    logger.info("🚀 Démarrage des tests des opportunités historiques")
    
    try:
        # Test 1: Génération d'opportunités
        opportunities = await test_historical_opportunity_generation()
        
        # Test 2: Validation des opportunités
        if opportunities:
            await test_opportunity_validation()
        
        # Test 3: Pipeline de backtesting
        await test_backtesting_pipeline()
        
        # Test 4: Endpoints API
        await test_api_endpoints()
        
        logger.info("✅ Tous les tests terminés avec succès!")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors des tests: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
