#!/usr/bin/env python3
"""
Script pour supprimer l'ancienne colonne hybrid_score de la table advanced_opportunities
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

def drop_hybrid_score_column():
    """Supprime la colonne hybrid_score de la table advanced_opportunities"""
    
    try:
        with engine.connect() as conn:
            # Commencer une transaction
            trans = conn.begin()
            
            try:
                logger.info("Starting removal of hybrid_score column")
                
                # Supprimer la colonne hybrid_score
                drop_column_sql = "ALTER TABLE advanced_opportunities DROP COLUMN IF EXISTS hybrid_score;"
                conn.execute(text(drop_column_sql))
                
                # Valider la transaction
                trans.commit()
                logger.info("hybrid_score column removed successfully")
                
            except Exception as e:
                logger.error(f"Error during column removal: {e}")
                trans.rollback()
                raise
                
    except Exception as e:
        logger.error(f"Failed to remove hybrid_score column: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = drop_hybrid_score_column()
    if success:
        print("✅ hybrid_score column removed successfully")
    else:
        print("❌ Failed to remove hybrid_score column")
        sys.exit(1)
