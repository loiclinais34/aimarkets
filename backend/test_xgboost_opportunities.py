#!/usr/bin/env python3
"""
Script simple pour générer et stocker des opportunités XGBoost de test
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
        logging.FileHandler('test_xgboost_opportunities.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_xgboost_opportunities():
    """Teste la génération d'opportunités XGBoost avec un petit échantillon."""
    logger.info("🧪 Test de génération d'opportunités XGBoost...")
    
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
        
        # Test avec seulement 3 symboles
        test_symbols = ['AAPL', 'MSFT', 'GOOGL']
        
        logger.info(f"📊 Test avec {len(test_symbols)} symboles: {test_symbols}")
        
        # Générer les opportunités
        opportunities = ml_system.generate_opportunities(test_symbols)
        
        if opportunities:
            logger.info(f"✅ {len(opportunities)} opportunités générées")
            
            # Stocker les opportunités
            ml_system.store_opportunities(opportunities)
            
            logger.info("💾 Opportunités stockées avec succès!")
            
            # Vérifier les résultats
            query = "SELECT COUNT(*) as total FROM ml_opportunities_xgboost"
            result = pd.read_sql(query, ml_system.engine)
            
            logger.info(f"📈 Total opportunités en base: {result['total'].iloc[0]}")
            
            # Afficher quelques exemples
            sample_query = """
            SELECT symbol, recommendation, confidence_level, potential_return
            FROM ml_opportunities_xgboost 
            ORDER BY confidence_level DESC 
            LIMIT 5
            """
            sample_results = pd.read_sql(sample_query, ml_system.engine)
            
            logger.info("🎯 Top 5 opportunités par confiance:")
            for _, row in sample_results.iterrows():
                logger.info(f"  {row['symbol']}: {row['recommendation']} (confiance: {row['confidence_level']:.3f}, retour: {row['potential_return']:.3f})")
            
        else:
            logger.warning("⚠️ Aucune opportunité générée")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    test_xgboost_opportunities()
