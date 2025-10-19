#!/usr/bin/env python3
"""
Script de surveillance pour la génération complémentaire des opportunités XGBoost
"""

import time
import psutil
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import des modules locaux
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

def monitor_complementary_generation():
    """Surveille la génération complémentaire des opportunités XGBoost."""
    
    # Configuration de la base de données
    DATABASE_URL = settings.database_url
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    logger.info("🔍 Démarrage de la surveillance de la génération complémentaire XGBoost...")
    
    # Trouver le processus principal
    main_process = None
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline']) if proc.info['cmdline'] else ''
            if 'generate_complementary_xgboost_opportunities.py' in cmdline:
                main_process = proc
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if not main_process:
        logger.warning("⚠️ Processus de génération complémentaire non trouvé. Surveillance générale...")
    
    start_time = datetime.now()
    last_count = 0
    
    try:
        while True:
            current_time = datetime.now()
            elapsed = current_time - start_time
            
            # Vérifier le processus principal
            if main_process:
                try:
                    cpu_percent = main_process.cpu_percent()
                    memory_info = main_process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    status = main_process.status()
                    
                    logger.info(f"🔄 Processus principal - PID: {main_process.pid}, CPU: {cpu_percent:.1f}%, RAM: {memory_mb:.1f}MB, Status: {status}")
                except psutil.NoSuchProcess:
                    logger.info("✅ Processus de génération complémentaire terminé")
                    break
                except psutil.AccessDenied:
                    logger.warning("⚠️ Accès refusé au processus principal")
            
            # Vérifier les statistiques de la base de données
            try:
                db = SessionLocal()
                
                # Compter les opportunités totales
                total_count = db.execute(text("SELECT COUNT(*) FROM ml_opportunities_xgboost")).scalar()
                
                # Compter les opportunités de la période complémentaire (2024-02-07 à 2025-10-17)
                complementary_count = db.execute(text("""
                    SELECT COUNT(*) FROM ml_opportunities_xgboost 
                    WHERE date >= '2024-02-07' AND date <= '2025-10-17'
                """)).scalar()
                
                # Statistiques par horizon
                horizon_stats = db.execute(text("""
                    SELECT horizon_days, COUNT(*) as count 
                    FROM ml_opportunities_xgboost 
                    WHERE date >= '2024-02-07' AND date <= '2025-10-17'
                    GROUP BY horizon_days 
                    ORDER BY horizon_days
                """)).fetchall()
                
                # Statistiques par recommandation
                rec_stats = db.execute(text("""
                    SELECT recommendation, COUNT(*) as count, AVG(confidence_level) as avg_confidence
                    FROM ml_opportunities_xgboost 
                    WHERE date >= '2024-02-07' AND date <= '2025-10-17'
                    GROUP BY recommendation 
                    ORDER BY count DESC
                """)).fetchall()
                
                # Période couverte
                date_range = db.execute(text("""
                    SELECT MIN(date) as min_date, MAX(date) as max_date
                    FROM ml_opportunities_xgboost 
                    WHERE date >= '2024-02-07' AND date <= '2025-10-17'
                """)).fetchone()
                
                db.close()
                
                # Calculer le taux de génération
                new_opportunities = total_count - last_count
                rate_per_minute = new_opportunities / max(elapsed.total_seconds() / 60, 1)
                
                logger.info(f"\n📊 STATISTIQUES COMPLÉMENTAIRES - {current_time.strftime('%H:%M:%S')}")
                logger.info(f"⏱️  Temps écoulé: {elapsed}")
                logger.info(f"📈 Opportunités totales: {total_count:,}")
                logger.info(f"🆕 Opportunités complémentaires: {complementary_count:,}")
                logger.info(f"📊 Nouvelle génération: +{new_opportunities} (taux: {rate_per_minute:.1f}/min)")
                
                if date_range and date_range[0]:
                    logger.info(f"📅 Période complémentaire: {date_range[0]} → {date_range[1]}")
                
                logger.info(f"⏰ Par horizon:")
                for horizon, count in horizon_stats:
                    logger.info(f"   {horizon}j: {count:,} opportunités")
                
                logger.info(f"🎯 Par recommandation:")
                for rec, count, avg_conf in rec_stats:
                    logger.info(f"   {rec}: {count:,} opportunités (confiance: {avg_conf:.3f})")
                
                last_count = total_count
                
            except Exception as e:
                logger.error(f"❌ Erreur lors de la vérification de la base: {e}")
            
            # Attendre avant la prochaine vérification
            time.sleep(30)  # Vérification toutes les 30 secondes
            
    except KeyboardInterrupt:
        logger.info("\n🛑 Surveillance arrêtée par l'utilisateur")
    except Exception as e:
        logger.error(f"❌ Erreur dans la surveillance: {e}")
    
    # Statistiques finales
    try:
        db = SessionLocal()
        final_total = db.execute(text("SELECT COUNT(*) FROM ml_opportunities_xgboost")).scalar()
        final_complementary = db.execute(text("""
            SELECT COUNT(*) FROM ml_opportunities_xgboost 
            WHERE date >= '2024-02-07' AND date <= '2025-10-17'
        """)).scalar()
        db.close()
        
        logger.info(f"\n🎉 SURVEILLANCE TERMINÉE")
        logger.info(f"📈 Total final: {final_total:,} opportunités")
        logger.info(f"🆕 Complémentaires générées: {final_complementary:,}")
        logger.info(f"⏱️  Temps total: {datetime.now() - start_time}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors des statistiques finales: {e}")

if __name__ == "__main__":
    monitor_complementary_generation()
