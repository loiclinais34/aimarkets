#!/usr/bin/env python3
"""
Script pour valider les performances des opportunités historiques
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.historical_opportunities import HistoricalOpportunities
from app.services.ml_backtesting.opportunity_validator import OpportunityValidator
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def validate_historical_opportunities(db: Session) -> dict:
    """
    Valide les performances des opportunités historiques
    
    Args:
        db: Session de base de données
    
    Returns:
        Résumé des validations
    """
    logger.info("🔍 Validation des performances des opportunités historiques")
    
    try:
        # Récupérer toutes les opportunités
        opportunities = db.query(HistoricalOpportunities).all()
        
        if not opportunities:
            logger.warning("Aucune opportunité à valider")
            return {"validated": 0, "errors": []}
        
        # Créer le validateur
        validator = OpportunityValidator(db)
        
        results = {
            "total_opportunities": len(opportunities),
            "validated": 0,
            "failed": 0,
            "errors": []
        }
        
        # Traiter par batch de 50 opportunités
        batch_size = 50
        
        for i in range(0, len(opportunities), batch_size):
            batch = opportunities[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(opportunities) - 1) // batch_size + 1
            
            logger.info(f"Validation du batch {batch_num}/{total_batches} ({len(batch)} opportunités)")
            
            for opportunity in batch:
                try:
                    # Valider l'opportunité pour toutes les périodes
                    result = await validator.validate_opportunity_performance(
                        opportunity=opportunity,
                        validation_periods=[1, 7, 30]
                    )
                    
                    results["validated"] += 1
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la validation de {opportunity.symbol} ({opportunity.opportunity_date}): {e}")
                    results["failed"] += 1
                    results["errors"].append(f"{opportunity.symbol} - {opportunity.opportunity_date}: {str(e)}")
            
            # Sauvegarder les modifications
            db.commit()
        
        logger.info(f"✅ Validation terminée: {results['validated']} opportunités validées")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la validation: {e}")
        db.rollback()
        raise


def verify_validation_results(db: Session) -> dict:
    """
    Vérifie les résultats de la validation
    
    Args:
        db: Session de base de données
    
    Returns:
        Résumé de vérification
    """
    logger.info("🔍 Vérification des résultats de validation")
    
    try:
        # Compter les opportunités
        total_opportunities = db.query(HistoricalOpportunities).count()
        
        # Vérifier les colonnes de performance
        price_1_day_filled = db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.price_1_day_later.isnot(None))\
            .count()
        
        return_1_day_filled = db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.return_1_day.isnot(None))\
            .count()
        
        rec_correct_1d_filled = db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.recommendation_correct_1_day.isnot(None))\
            .count()
        
        # Vérifier les colonnes 7 jours
        price_7_days_filled = db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.price_7_days_later.isnot(None))\
            .count()
        
        return_7_days_filled = db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.return_7_days.isnot(None))\
            .count()
        
        rec_correct_7d_filled = db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.recommendation_correct_7_days.isnot(None))\
            .count()
        
        # Vérifier les colonnes 30 jours
        price_30_days_filled = db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.price_30_days_later.isnot(None))\
            .count()
        
        return_30_days_filled = db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.return_30_days.isnot(None))\
            .count()
        
        rec_correct_30d_filled = db.query(HistoricalOpportunities)\
            .filter(HistoricalOpportunities.recommendation_correct_30_days.isnot(None))\
            .count()
        
        # Vérifier quelques exemples récents
        recent_opportunities = db.query(HistoricalOpportunities)\
            .order_by(HistoricalOpportunities.opportunity_date.desc())\
            .limit(3)\
            .all()
        
        verification_results = {
            "total_opportunities": total_opportunities,
            "price_1_day_filled": price_1_day_filled,
            "return_1_day_filled": return_1_day_filled,
            "rec_correct_1d_filled": rec_correct_1d_filled,
            "price_7_days_filled": price_7_days_filled,
            "return_7_days_filled": return_7_days_filled,
            "rec_correct_7d_filled": rec_correct_7d_filled,
            "price_30_days_filled": price_30_days_filled,
            "return_30_days_filled": return_30_days_filled,
            "rec_correct_30d_filled": rec_correct_30d_filled,
            "recent_examples": []
        }
        
        for opp in recent_opportunities:
            verification_results["recent_examples"].append({
                "symbol": opp.symbol,
                "date": opp.opportunity_date,
                "recommendation": opp.recommendation,
                "price_at_generation": opp.price_at_generation,
                "price_1_day_later": opp.price_1_day_later,
                "return_1_day": opp.return_1_day,
                "recommendation_correct_1_day": opp.recommendation_correct_1_day,
                "price_7_days_later": opp.price_7_days_later,
                "return_7_days": opp.return_7_days,
                "recommendation_correct_7_days": opp.recommendation_correct_7_days,
                "price_30_days_later": opp.price_30_days_later,
                "return_30_days": opp.return_30_days,
                "recommendation_correct_30_days": opp.recommendation_correct_30_days
            })
        
        return verification_results
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la vérification: {e}")
        raise


async def main():
    """Fonction principale"""
    
    logger.info("🚀 Démarrage de la validation des performances des opportunités historiques")
    
    db = next(get_db())
    
    try:
        # Étape 1: Valider les performances
        validation_results = await validate_historical_opportunities(db)
        
        # Étape 2: Vérifier les résultats
        verification_results = verify_validation_results(db)
        
        logger.info("🎉 Validation terminée!")
        logger.info(f"  - Opportunités validées: {validation_results['validated']}")
        logger.info(f"  - Échecs: {validation_results['failed']}")
        logger.info(f"  - Total: {verification_results['total_opportunities']}")
        
        # Vérifier la qualité des données
        logger.info("📊 Résultats de validation:")
        logger.info(f"  - Prix 1 jour: {verification_results['price_1_day_filled']}/{verification_results['total_opportunities']}")
        logger.info(f"  - Retour 1 jour: {verification_results['return_1_day_filled']}/{verification_results['total_opportunities']}")
        logger.info(f"  - Recommandation correcte 1 jour: {verification_results['rec_correct_1d_filled']}/{verification_results['total_opportunities']}")
        
        logger.info(f"  - Prix 7 jours: {verification_results['price_7_days_filled']}/{verification_results['total_opportunities']}")
        logger.info(f"  - Retour 7 jours: {verification_results['return_7_days_filled']}/{verification_results['total_opportunities']}")
        logger.info(f"  - Recommandation correcte 7 jours: {verification_results['rec_correct_7d_filled']}/{verification_results['total_opportunities']}")
        
        logger.info(f"  - Prix 30 jours: {verification_results['price_30_days_filled']}/{verification_results['total_opportunities']}")
        logger.info(f"  - Retour 30 jours: {verification_results['return_30_days_filled']}/{verification_results['total_opportunities']}")
        logger.info(f"  - Recommandation correcte 30 jours: {verification_results['rec_correct_30d_filled']}/{verification_results['total_opportunities']}")
        
        # Afficher quelques exemples
        logger.info("Exemples de validation:")
        for example in verification_results['recent_examples']:
            logger.info(f"  {example['symbol']} - {example['date']} ({example['recommendation']}):")
            logger.info(f"    Prix génération: {example['price_at_generation']}")
            logger.info(f"    1 jour: Prix {example['price_1_day_later']}, Retour {example['return_1_day']}, Correct {example['recommendation_correct_1_day']}")
            logger.info(f"    7 jours: Prix {example['price_7_days_later']}, Retour {example['return_7_days']}, Correct {example['recommendation_correct_7_days']}")
            logger.info(f"    30 jours: Prix {example['price_30_days_later']}, Retour {example['return_30_days']}, Correct {example['recommendation_correct_30_days']}")
        
        # Afficher les erreurs s'il y en a
        if validation_results['errors']:
            logger.warning(f"⚠️ {len(validation_results['errors'])} erreurs lors de la validation:")
            for error in validation_results['errors'][:5]:  # Afficher seulement les 5 premières
                logger.warning(f"  - {error}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
