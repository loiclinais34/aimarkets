#!/usr/bin/env python3
"""
Script de test pour la régénération des opportunités historiques sur une période courte
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.database import HistoricalData
from app.models.historical_opportunities import HistoricalOpportunities, HistoricalOpportunityValidation
from app.services.ml_backtesting.historical_opportunity_generator import HistoricalOpportunityGenerator
from app.services.ml_backtesting.opportunity_validator import OpportunityValidator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_historical_opportunities_tables(db: Session) -> dict:
    """
    Vide les tables historical_opportunities et historical_opportunities_validation
    """
    logger.info("🗑️ Vidage des tables historical_opportunities")
    
    try:
        # Compter les enregistrements avant suppression
        opportunities_count = db.query(HistoricalOpportunities).count()
        validations_count = db.query(HistoricalOpportunityValidation).count()
        
        logger.info(f"Enregistrements à supprimer:")
        logger.info(f"  - historical_opportunities: {opportunities_count}")
        logger.info(f"  - historical_opportunities_validation: {validations_count}")
        
        # Supprimer les validations d'abord (clé étrangère)
        db.query(HistoricalOpportunityValidation).delete()
        
        # Supprimer les opportunités
        db.query(HistoricalOpportunities).delete()
        
        # Commit des suppressions
        db.commit()
        
        logger.info("✅ Tables vidées avec succès")
        
        return {
            "opportunities_deleted": opportunities_count,
            "validations_deleted": validations_count
        }
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du vidage des tables: {e}")
        db.rollback()
        raise


def get_all_symbols(db: Session) -> list[str]:
    """Récupère tous les symboles disponibles"""
    symbols = db.query(HistoricalData.symbol).distinct().all()
    return [symbol[0] for symbol in symbols]


async def generate_historical_opportunities_for_date_range(
    start_date: date,
    end_date: date,
    symbols: list[str] = None,
    db: Session = None
) -> dict:
    """
    Génère les opportunités historiques pour une plage de dates
    """
    if db is None:
        db = next(get_db())
    
    if symbols is None:
        symbols = get_all_symbols(db)
    
    results = {
        "start_date": start_date,
        "end_date": end_date,
        "total_symbols": len(symbols),
        "processed_symbols": 0,
        "successful_symbols": 0,
        "failed_symbols": 0,
        "total_opportunities_created": 0,
        "errors": []
    }
    
    # Créer le générateur d'opportunités
    generator = HistoricalOpportunityGenerator(db)
    
    current_date = start_date
    while current_date <= end_date:
        logger.info(f"Traitement de la date: {current_date}")
        
        for symbol in symbols:
            try:
                # Vérifier qu'il y a des données historiques pour cette date
                historical_data = db.query(HistoricalData)\
                    .filter(
                        HistoricalData.symbol == symbol,
                        HistoricalData.date <= current_date
                    )\
                    .order_by(HistoricalData.date.desc())\
                    .limit(1)\
                    .first()
                
                if not historical_data:
                    logger.warning(f"Pas de données historiques pour {symbol} jusqu'au {current_date}")
                    continue
                
                # Générer l'opportunité pour cette date
                opportunity = await generator._generate_opportunity_for_symbol_date(
                    symbol=symbol,
                    target_date=current_date
                )
                
                if opportunity:
                    # Sauvegarder l'opportunité en base de données
                    db.add(opportunity)
                    results["total_opportunities_created"] += 1
                    results["successful_symbols"] += 1
                else:
                    results["failed_symbols"] += 1
                    results["errors"].append(f"{symbol} - {current_date}: Échec de génération")
                
                results["processed_symbols"] += 1
                
            except Exception as e:
                logger.error(f"Erreur pour {symbol} le {current_date}: {e}")
                results["failed_symbols"] += 1
                results["errors"].append(f"{symbol} - {current_date}: {str(e)}")
                results["processed_symbols"] += 1
        
        # Commit pour chaque date
        db.commit()
        current_date += timedelta(days=1)
    
    return results


def verify_results(db: Session) -> dict:
    """
    Vérifie les résultats de la régénération
    """
    logger.info("🔍 Vérification des résultats")
    
    try:
        # Compter les opportunités
        total_opportunities = db.query(HistoricalOpportunities).count()
        
        # Vérifier les colonnes importantes
        market_score_05 = db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.market_score == 0.5)\
            .count()
        
        price_1_day_null = db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.price_1_day_later.is_(None))\
            .count()
        
        return_1_day_null = db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.return_1_day.is_(None))\
            .count()
        
        rec_correct_1d_null = db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.recommendation_correct_1_day.is_(None))\
            .count()
        
        # Vérifier quelques exemples récents
        recent_opportunities = db.query(HistoricalOpportunities)\
            .order_by(HistoricalOpportunities.opportunity_date.desc())\
            .limit(3)\
            .all()
        
        verification_results = {
            "total_opportunities": total_opportunities,
            "market_score_05": market_score_05,
            "price_1_day_null": price_1_day_null,
            "return_1_day_null": return_1_day_null,
            "rec_correct_1d_null": rec_correct_1d_null,
            "recent_examples": []
        }
        
        for opp in recent_opportunities:
            verification_results["recent_examples"].append({
                "symbol": opp.symbol,
                "date": opp.opportunity_date,
                "technical_score": opp.technical_score,
                "sentiment_score": opp.sentiment_score,
                "market_score": opp.market_score,
                "composite_score": opp.composite_score,
                "recommendation": opp.recommendation,
                "price_1_day_later": opp.price_1_day_later,
                "return_1_day": opp.return_1_day,
                "recommendation_correct_1_day": opp.recommendation_correct_1_day
            })
        
        return verification_results
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification: {e}")
        raise


async def main():
    """Fonction principale"""
    
    logger.info("🚀 Démarrage du test de régénération des opportunités historiques")
    
    # Définir la plage de dates (seulement 2 jours pour le test)
    start_date = date(2025, 9, 25)
    end_date = date(2025, 9, 26)
    
    db = next(get_db())
    
    try:
        # Étape 1: Vider les tables existantes
        clear_results = clear_historical_opportunities_tables(db)
        
        # Étape 2: Générer les nouvelles opportunités
        generation_results = await generate_historical_opportunities_for_date_range(
            start_date=start_date,
            end_date=end_date,
            symbols=None,  # Tous les symboles
            db=db
        )
        
        # Étape 3: Vérifier les résultats
        verification_results = verify_results(db)
        
        logger.info("🎉 Test terminé!")
        logger.info(f"  - Période: {start_date} à {end_date}")
        logger.info(f"  - Opportunités générées: {generation_results['total_opportunities_created']}")
        logger.info(f"  - Total final: {verification_results['total_opportunities']}")
        
        # Vérifier la qualité des données
        if verification_results['market_score_05'] > 0:
            logger.warning(f"⚠️ Il reste {verification_results['market_score_05']} market scores à 0.5")
        
        if verification_results['price_1_day_null'] > 0:
            logger.info(f"ℹ️ {verification_results['price_1_day_null']} colonnes price_1_day_later vides (normal avant validation)")
        
        if verification_results['return_1_day_null'] > 0:
            logger.info(f"ℹ️ {verification_results['return_1_day_null']} colonnes return_1_day vides (normal avant validation)")
        
        if verification_results['rec_correct_1d_null'] > 0:
            logger.info(f"ℹ️ {verification_results['rec_correct_1d_null']} colonnes recommendation_correct_1_day vides (normal avant validation)")
        
        # Afficher quelques exemples
        logger.info("Exemples récents:")
        for example in verification_results['recent_examples']:
            logger.info(f"  {example['symbol']} - {example['date']}:")
            logger.info(f"    Technical: {example['technical_score']}, Sentiment: {example['sentiment_score']}, Market: {example['market_score']}")
            logger.info(f"    Composite: {example['composite_score']}, Recommendation: {example['recommendation']}")
            logger.info(f"    Price 1d: {example['price_1_day_later']}, Return 1d: {example['return_1_day']}")
            logger.info(f"    Rec correct 1d: {example['recommendation_correct_1_day']}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
