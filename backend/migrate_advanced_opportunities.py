#!/usr/bin/env python3
"""
Script de migration pour ajouter les nouveaux champs à la table advanced_opportunities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.core.database import engine
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def migrate_advanced_opportunities():
    """Ajoute les nouveaux champs à la table advanced_opportunities"""
    
    # Liste des nouveaux champs à ajouter
    new_columns = [
        "candlestick_score FLOAT NOT NULL DEFAULT 0.5",
        "garch_score FLOAT NOT NULL DEFAULT 0.5", 
        "monte_carlo_score FLOAT NOT NULL DEFAULT 0.5",
        "markov_score FLOAT NOT NULL DEFAULT 0.5",
        "volatility_score FLOAT NOT NULL DEFAULT 0.5",
        "composite_score FLOAT NOT NULL DEFAULT 0.5",
        "candlestick_analysis JSON",
        "garch_analysis JSON",
        "monte_carlo_analysis JSON", 
        "markov_analysis JSON",
        "volatility_analysis JSON"
    ]
    
    # Supprimer l'ancien index sur hybrid_score s'il existe
    drop_index_sql = """
    DROP INDEX IF EXISTS idx_hybrid_score;
    """
    
    # Créer le nouvel index sur composite_score
    create_index_sql = """
    CREATE INDEX IF NOT EXISTS idx_composite_score ON advanced_opportunities (composite_score);
    """
    
    try:
        with engine.connect() as conn:
            # Commencer une transaction
            trans = conn.begin()
            
            try:
                logger.info("Starting migration of advanced_opportunities table")
                
                # Supprimer l'ancien index
                logger.info("Dropping old hybrid_score index")
                conn.execute(text(drop_index_sql))
                
                # Ajouter chaque nouveau champ
                for column_def in new_columns:
                    column_name = column_def.split()[0]
                    logger.info(f"Adding column: {column_name}")
                    
                    alter_sql = f"ALTER TABLE advanced_opportunities ADD COLUMN {column_def};"
                    conn.execute(text(alter_sql))
                
                # Créer le nouvel index
                logger.info("Creating new composite_score index")
                conn.execute(text(create_index_sql))
                
                # Valider la transaction
                trans.commit()
                logger.info("Migration completed successfully")
                
            except Exception as e:
                logger.error(f"Error during migration: {e}")
                trans.rollback()
                raise
                
    except Exception as e:
        logger.error(f"Failed to migrate advanced_opportunities table: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = migrate_advanced_opportunities()
    if success:
        print("✅ Migration completed successfully")
    else:
        print("❌ Migration failed")
        sys.exit(1)
