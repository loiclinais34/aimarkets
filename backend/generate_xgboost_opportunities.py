#!/usr/bin/env python3
"""
Script pour générer des opportunités ML à grande échelle avec XGBoost et TA-Lib
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import logging
from typing import List, Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the advanced ML system
from advanced_xgboost_ml_system import AdvancedXGBoostMLSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('xgboost_opportunities_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def generate_xgboost_opportunities():
    """Génère des opportunités ML avec XGBoost pour tous les symboles."""
    logger.info("🚀 Démarrage de la génération d'opportunités XGBoost...")
    
    # Configuration de la base de données
    db_config = {
        'host': 'localhost',
        'port': '5432',
        'database': 'aimarkets',
        'user': 'loiclinais',
        'password': 'password'
    }
    
    try:
        # Initialiser le système ML
        ml_system = AdvancedXGBoostMLSystem(db_config)
        
        # D'abord, entraîner les modèles avec toutes les données disponibles
        logger.info("📊 Entraînement des modèles avec toutes les données...")
        ml_system.run_full_pipeline(
            symbols=None,  # Tous les symboles
            train_models=True,
            generate_opportunities=False
        )
        
        # Ensuite, générer des opportunités pour tous les symboles
        logger.info("🎯 Génération d'opportunités pour tous les symboles...")
        
        # Traiter par batch pour éviter les problèmes de mémoire
        batch_size = 20
        all_symbols = ml_system.symbols
        
        total_opportunities = 0
        
        for i in range(0, len(all_symbols), batch_size):
            batch_symbols = all_symbols[i:i+batch_size]
            logger.info(f"📊 Traitement du batch {i//batch_size + 1}/{(len(all_symbols) + batch_size - 1)//batch_size}: {len(batch_symbols)} symboles")
            
            # Générer les opportunités pour ce batch
            opportunities = ml_system.generate_opportunities(batch_symbols)
            
            if opportunities:
                # Stocker les opportunités
                ml_system.store_opportunities(opportunities)
                total_opportunities += len(opportunities)
                logger.info(f"✅ Batch terminé: {len(opportunities)} opportunités générées")
            else:
                logger.warning(f"⚠️ Aucune opportunité générée pour ce batch")
        
        logger.info(f"🎉 Génération terminée! Total: {total_opportunities} opportunités générées")
        
        # Vérifier les résultats
        logger.info("📊 Vérification des résultats...")
        query = "SELECT COUNT(*) as total, COUNT(DISTINCT symbol) as symbols FROM ml_opportunities_xgboost"
        result = pd.read_sql(query, ml_system.engine)
        
        logger.info(f"📈 Résultats finaux:")
        logger.info(f"  Total opportunités: {result['total'].iloc[0]}")
        logger.info(f"  Symboles couverts: {result['symbols'].iloc[0]}")
        
        # Statistiques par recommandation
        rec_query = """
        SELECT recommendation, COUNT(*) as count, AVG(confidence_level) as avg_confidence
        FROM ml_opportunities_xgboost 
        GROUP BY recommendation 
        ORDER BY count DESC
        """
        rec_stats = pd.read_sql(rec_query, ml_system.engine)
        
        logger.info("📊 Distribution des recommandations:")
        for _, row in rec_stats.iterrows():
            logger.info(f"  {row['recommendation']}: {row['count']} ({row['avg_confidence']:.3f} confiance moyenne)")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération d'opportunités: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    generate_xgboost_opportunities()
