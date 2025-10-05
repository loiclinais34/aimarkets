#!/usr/bin/env python3
"""
Script de test pour générer des opportunités sur des données réelles
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


async def test_generation_with_real_data():
    """Test de génération avec des données réelles"""
    
    logger.info("🧪 Test de génération d'opportunités avec des données réelles")
    
    # Obtenir une session de base de données
    db = next(get_db())
    
    try:
        # Créer le générateur
        generator = HistoricalOpportunityGenerator(db)
        
        # Vérifier quelles données sont disponibles
        from app.models.database import HistoricalData, TechnicalIndicators, SentimentIndicators
        from app.models.market_indicators import MarketIndicators
        
        # Vérifier les données historiques disponibles
        historical_count = db.query(HistoricalData).count()
        logger.info(f"Données historiques disponibles: {historical_count} enregistrements")
        
        # Vérifier les indicateurs techniques
        technical_count = db.query(TechnicalIndicators).count()
        logger.info(f"Indicateurs techniques disponibles: {technical_count} enregistrements")
        
        # Vérifier les indicateurs de sentiment
        sentiment_count = db.query(SentimentIndicators).count()
        logger.info(f"Indicateurs de sentiment disponibles: {sentiment_count} enregistrements")
        
        # Vérifier les indicateurs de marché
        market_count = db.query(MarketIndicators).count()
        logger.info(f"Indicateurs de marché disponibles: {market_count} enregistrements")
        
        # Récupérer les symboles disponibles
        symbols = db.query(HistoricalData.symbol).distinct().limit(10).all()
        available_symbols = [s[0] for s in symbols]
        logger.info(f"Symboles disponibles: {available_symbols}")
        
        # Récupérer les dates disponibles
        latest_date = db.query(HistoricalData.date).order_by(HistoricalData.date.desc()).first()
        if latest_date:
            logger.info(f"Date la plus récente: {latest_date[0]}")
        
        # Choisir une date de test (il y a 30 jours)
        test_date = date.today() - timedelta(days=30)
        logger.info(f"Date de test choisie: {test_date}")
        
        # Vérifier quelles données sont disponibles pour cette date
        historical_for_date = db.query(HistoricalData).filter(
            HistoricalData.date == test_date
        ).count()
        logger.info(f"Données historiques pour {test_date}: {historical_for_date} enregistrements")
        
        technical_for_date = db.query(TechnicalIndicators).filter(
            TechnicalIndicators.date <= test_date
        ).count()
        logger.info(f"Indicateurs techniques avant {test_date}: {technical_for_date} enregistrements")
        
        sentiment_for_date = db.query(SentimentIndicators).filter(
            SentimentIndicators.date <= test_date
        ).count()
        logger.info(f"Indicateurs de sentiment avant {test_date}: {sentiment_for_date} enregistrements")
        
        market_for_date = db.query(MarketIndicators).filter(
            MarketIndicators.analysis_date <= test_date
        ).count()
        logger.info(f"Indicateurs de marché avant {test_date}: {market_for_date} enregistrements")
        
        # Générer des opportunités pour quelques symboles
        test_symbols = available_symbols[:5]  # Prendre les 5 premiers symboles
        logger.info(f"Génération d'opportunités pour: {test_symbols}")
        
        opportunities = await generator.generate_opportunities_for_date(
            target_date=test_date,
            symbols=test_symbols,
            limit_symbols=5
        )
        
        logger.info(f"✅ {len(opportunities)} opportunités générées")
        
        # Afficher les détails des opportunités
        for i, opp in enumerate(opportunities):
            logger.info(f"  {i+1}. {opp.symbol}:")
            logger.info(f"     - Recommandation: {opp.recommendation}")
            logger.info(f"     - Score composite: {opp.composite_score:.3f}")
            logger.info(f"     - Confiance: {opp.confidence_level}")
            logger.info(f"     - Risque: {opp.risk_level}")
            logger.info(f"     - Prix: ${opp.price_at_generation}")
        
        return opportunities
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


async def test_validation_with_real_data():
    """Test de validation avec des données réelles"""
    
    logger.info("🧪 Test de validation avec des données réelles")
    
    # Obtenir une session de base de données
    db = next(get_db())
    
    try:
        # Récupérer les opportunités générées précédemment
        from app.models.historical_opportunities import HistoricalOpportunities
        
        opportunities = db.query(HistoricalOpportunities).limit(3).all()
        
        if not opportunities:
            logger.warning("Aucune opportunité trouvée pour la validation")
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
        
        # Afficher les résultats
        for result in results:
            logger.info(f"  - {result['symbol']} ({result['opportunity_date']}):")
            logger.info(f"    Score de performance: {result.get('performance_score', 'N/A')}")
            
            validation_results = result.get('validation_results', {})
            for period, data in validation_results.items():
                logger.info(f"    {period}:")
                logger.info(f"      - Rendement réel: {data.get('actual_return', 'N/A')}")
                logger.info(f"      - Rendement prédit: {data.get('predicted_return', 'N/A')}")
                logger.info(f"      - Recommandation correcte: {data.get('recommendation_correct', 'N/A')}")
                logger.info(f"      - Catégorie: {data.get('performance_category', 'N/A')}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la validation: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


async def test_api_endpoints():
    """Test des endpoints API avec des données réelles"""
    
    logger.info("🧪 Test des endpoints API")
    
    try:
        import requests
        
        base_url = "http://localhost:8000/api/v1/ml-backtesting"
        
        # Test de génération d'opportunités via API
        test_date = (date.today() - timedelta(days=30)).isoformat()
        
        payload = {
            "target_date": test_date,
            "symbols": ["AAPL", "MSFT", "GOOGL"],
            "limit_symbols": 3
        }
        
        logger.info(f"Test de génération via API pour {test_date}")
        response = requests.post(f"{base_url}/generate-opportunities", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Génération via API: {result['message']}")
        else:
            logger.warning(f"⚠️ Erreur API: {response.status_code} - {response.text}")
        
        # Test de backtest rapide via API
        payload = {
            "test_date": test_date,
            "symbols": ["AAPL"],
            "limit_symbols": 1
        }
        
        logger.info(f"Test de backtest rapide via API")
        response = requests.post(f"{base_url}/quick-backtest", json=payload)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Backtest rapide: {result['status']}")
            if result['status'] == 'success':
                logger.info(f"  - Opportunités: {result.get('opportunities_count', 0)}")
        else:
            logger.warning(f"⚠️ Erreur API: {response.status_code} - {response.text}")
        
        # Test des statistiques
        response = requests.get(f"{base_url}/stats")
        if response.status_code == 200:
            stats = response.json()
            logger.info(f"✅ Statistiques: {stats['stats']['total_opportunities']} opportunités")
        else:
            logger.warning(f"⚠️ Erreur statistiques: {response.status_code}")
        
    except requests.exceptions.ConnectionError:
        logger.warning("⚠️ Serveur API non disponible")
    except Exception as e:
        logger.error(f"❌ Erreur lors du test API: {e}")


async def main():
    """Fonction principale de test"""
    
    logger.info("🚀 Démarrage des tests avec données réelles")
    
    try:
        # Test 1: Génération d'opportunités
        opportunities = await test_generation_with_real_data()
        
        # Test 2: Validation des opportunités
        if opportunities:
            await test_validation_with_real_data()
        
        # Test 3: Endpoints API
        await test_api_endpoints()
        
        logger.info("✅ Tous les tests terminés avec succès!")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors des tests: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
