#!/usr/bin/env python3
"""
Script de surveillance pour la correction des indicateurs techniques
"""

import time
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os

# Ajouter le chemin du backend
backend_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(backend_path)

from app.core.config import settings

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def monitor_indicator_fix():
    """Surveille la correction des indicateurs techniques."""
    
    # Configuration de la base de données
    DATABASE_URL = settings.database_url
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    logger.info("🔍 Démarrage de la surveillance de la correction des indicateurs...")
    
    start_time = datetime.now()
    last_bb_count = 0
    
    try:
        while True:
            current_time = datetime.now()
            elapsed = current_time - start_time
            
            # Vérifier les statistiques de la base de données
            try:
                db = SessionLocal()
                
                # Compter les indicateurs corrigés
                stats_query = """
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(bb_position) as bb_position_count,
                    COUNT(momentum_composite) as momentum_composite_count,
                    COUNT(volatility_composite) as volatility_composite_count,
                    COUNT(trend_strength) as trend_strength_count
                FROM advanced_technical_indicators
                """
                
                stats = db.execute(text(stats_query)).fetchone()
                
                # Compter les enregistrements avec BB disponibles
                bb_available_query = """
                SELECT COUNT(*) 
                FROM advanced_technical_indicators
                WHERE bb_upper IS NOT NULL AND bb_lower IS NOT NULL
                """
                
                bb_available = db.execute(text(bb_available_query)).scalar()
                
                db.close()
                
                # Calculer le taux de progression
                new_bb_count = stats[1] - last_bb_count
                bb_progress = (stats[1] / bb_available * 100) if bb_available > 0 else 0
                
                logger.info(f"\n📊 SURVEILLANCE INDICATEURS - {current_time.strftime('%H:%M:%S')}")
                logger.info(f"⏱️  Temps écoulé: {elapsed}")
                logger.info(f"📈 Total enregistrements: {stats[0]:,}")
                logger.info(f"🎯 BB disponibles: {bb_available:,}")
                logger.info(f"✅ bb_position: {stats[1]:,} ({bb_progress:.1f}%)")
                logger.info(f"✅ momentum_composite: {stats[2]:,}")
                logger.info(f"✅ volatility_composite: {stats[3]:,}")
                logger.info(f"✅ trend_strength: {stats[4]:,}")
                
                if new_bb_count > 0:
                    logger.info(f"🔄 Nouveaux bb_position: +{new_bb_count}")
                
                # Vérifier si la correction est terminée
                if stats[1] >= bb_available:
                    logger.info("🎉 Correction terminée !")
                    break
                
                last_bb_count = stats[1]
                
            except Exception as e:
                logger.error(f"❌ Erreur lors de la vérification: {e}")
            
            # Attendre avant la prochaine vérification
            time.sleep(10)  # Vérification toutes les 10 secondes
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Surveillance arrêtée par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur dans la surveillance: {e}")
    
    # Statistiques finales
    try:
        db = SessionLocal()
        final_stats = db.execute(text(stats_query)).fetchone()
        db.close()
        
        logger.info(f"\n🎉 SURVEILLANCE TERMINÉE")
        logger.info(f"📈 Total final: {final_stats[0]:,}")
        logger.info(f"✅ bb_position: {final_stats[1]:,}")
        logger.info(f"✅ momentum_composite: {final_stats[2]:,}")
        logger.info(f"✅ volatility_composite: {final_stats[3]:,}")
        logger.info(f"✅ trend_strength: {final_stats[4]:,}")
        logger.info(f"⏱️  Temps total: {datetime.now() - start_time}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors des statistiques finales: {e}")

if __name__ == "__main__":
    monitor_indicator_fix()
