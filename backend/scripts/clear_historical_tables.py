#!/usr/bin/env python3
"""
Script pour vider les tables historical_opportunities et historical_opportunities_validation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.historical_opportunities import HistoricalOpportunities, HistoricalOpportunityValidation
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_historical_tables():
    """Vide les tables historical_opportunities et historical_opportunities_validation"""
    
    db = next(get_db())
    
    try:
        logger.info("🗑️  Début du nettoyage des tables historiques")
        
        # Compter les enregistrements avant suppression
        count_opportunities = db.query(HistoricalOpportunities).count()
        count_validations = db.query(HistoricalOpportunityValidation).count()
        
        logger.info(f"📊 Enregistrements à supprimer:")
        logger.info(f"  • historical_opportunities: {count_opportunities}")
        logger.info(f"  • historical_opportunities_validation: {count_validations}")
        
        # Supprimer les validations d'abord (clé étrangère)
        logger.info("🗑️  Suppression des validations...")
        db.query(HistoricalOpportunityValidation).delete()
        
        # Supprimer les opportunités
        logger.info("🗑️  Suppression des opportunités...")
        db.query(HistoricalOpportunities).delete()
        
        # Valider les changements
        db.commit()
        
        # Vérifier que les tables sont vides
        count_opportunities_after = db.query(HistoricalOpportunities).count()
        count_validations_after = db.query(HistoricalOpportunityValidation).count()
        
        logger.info(f"✅ Tables vidées avec succès:")
        logger.info(f"  • historical_opportunities: {count_opportunities_after}")
        logger.info(f"  • historical_opportunities_validation: {count_validations_after}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du nettoyage: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """Fonction principale"""
    
    logger.info("🚀 Démarrage du nettoyage des tables historiques")
    
    success = clear_historical_tables()
    
    if success:
        logger.info("✅ Nettoyage terminé avec succès")
    else:
        logger.error("❌ Échec du nettoyage")
        sys.exit(1)


if __name__ == "__main__":
    main()
