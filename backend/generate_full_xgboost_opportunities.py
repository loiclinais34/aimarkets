import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.ml_opportunities_xgboost import MLOpportunityXGBoost
from advanced_xgboost_ml_system import AdvancedXGBoostMLSystem
from typing import List, Dict, Any
import pandas as pd
from datetime import datetime, date, timedelta
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = settings.database_url
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_ml_opportunities_xgboost_table(db):
    """Drops and recreates the ml_opportunities_xgboost table."""
    logger.info("🗑️ Suppression de la table ml_opportunities_xgboost existante...")
    db.execute(text("DROP TABLE IF EXISTS ml_opportunities_xgboost CASCADE"))
    db.commit()
    logger.info("🔨 Création de la nouvelle table ml_opportunities_xgboost...")
    MLOpportunityXGBoost.metadata.create_all(bind=engine)
    db.commit()
    logger.info("✅ Table ml_opportunities_xgboost créée avec succès.")

def store_opportunities_in_db(db, opportunities: List[Dict[str, Any]]):
    """Stores a list of opportunities in the database."""
    if not opportunities:
        logger.info("Aucune opportunité à stocker.")
        return

    logger.info(f"💾 Stockage de {len(opportunities)} opportunités...")
    batch_size = 1000
    total_stored = 0
    
    for i in range(0, len(opportunities), batch_size):
        batch = opportunities[i:i + batch_size]
        ml_opportunity_objects = []
        
        for opp_data in batch:
            # Ensure date is a date object
            if isinstance(opp_data['date'], pd.Timestamp):
                opp_data['date'] = opp_data['date'].date()
            
            ml_opportunity_objects.append(MLOpportunityXGBoost(
                symbol=opp_data['symbol'],
                date=opp_data['date'],
                horizon_days=opp_data['horizon_days'],
                recommendation=opp_data['recommendation'],
                confidence_level=opp_data['confidence_level'],
                potential_return=opp_data['potential_return'],
                risk_score=opp_data['risk_score'],
                ml_model_name=opp_data['ml_model_name'],
                ml_model_version=opp_data['ml_model_version'],
                technical_indicators=opp_data['technical_indicators'], # Already JSON string
                ml_features=opp_data['ml_features'], # Already JSON string
                created_at=datetime.utcnow()
            ))
        
        db.add_all(ml_opportunity_objects)
        db.commit()
        total_stored += len(ml_opportunity_objects)
        
        if i % 5000 == 0:  # Log progress every 5000 records
            logger.info(f"📦 {total_stored} opportunités stockées...")

    logger.info(f"✅ {total_stored} opportunités stockées avec succès")

def generate_historical_xgboost_opportunities():
    """Génère les opportunités XGBoost pour tous les symboles depuis le début de l'année 2025."""
    logger.info("🚀 Démarrage de la génération complète des opportunités XGBoost...")
    
    db = next(get_db())
    
    try:
        # Créer la table
        create_ml_opportunities_xgboost_table(db)
        
        # Initialiser le système ML
        logger.info("🤖 Initialisation du système XGBoost...")
        db_config = {
            'host': settings.db_host,
            'port': settings.db_port,
            'database': settings.db_name,
            'user': settings.db_user,
            'password': settings.db_password
        }
        ml_system = AdvancedXGBoostMLSystem(db_config)
        
        # Définir la période de génération (depuis le 1er janvier 2025)
        start_date = date(2025, 1, 1)
        end_date = date.today()
        
        logger.info(f"📅 Période de génération: {start_date} à {end_date}")
        logger.info(f"📊 Symboles à traiter: {len(ml_system.symbols)}")
        logger.info(f"⏰ Horizons: {ml_system.horizons}")
        
        # Étape 1: Entraîner les modèles sur les données historiques
        logger.info("🎯 Phase 1: Entraînement des modèles XGBoost...")
        start_time = time.time()
        
        # Récupérer les données pour l'entraînement (jusqu'à aujourd'hui - 30 jours pour avoir des targets)
        training_end_date = end_date - timedelta(days=30)
        training_data = ml_system.get_technical_indicators_data(
            symbols=None,  # Tous les symboles
            limit=None  # Toutes les données
        )
        
        if training_data.empty:
            logger.error("❌ Aucune donnée d'entraînement récupérée.")
            return
        
        logger.info(f"📊 Données d'entraînement: {len(training_data)} enregistrements")
        
        # Ajouter les features avancées
        training_data = ml_system.create_advanced_features(training_data)
        
        # Créer les variables cibles
        training_data = ml_system.create_targets(training_data)
        
        if training_data.empty:
            logger.error("❌ Aucune variable cible créée.")
            return
        
        # Préparer les données ML
        ml_data, X, feature_names = ml_system.prepare_ml_data(training_data)
        
        if ml_data.empty:
            logger.error("❌ Aucune donnée ML préparée")
            return
        
        y_classification = ml_data['target_recommendation']
        y_regression = ml_data['future_return_1d']
        
        # Entraîner les modèles
        models = ml_system.train_xgboost_models(X, y_classification, y_regression, feature_names)
        
        if not models:
            logger.error("❌ Échec de l'entraînement des modèles")
            return
        
        training_time = time.time() - start_time
        logger.info(f"✅ Modèles entraînés en {training_time:.2f} secondes")
        
        # Étape 2: Générer les opportunités pour tous les symboles
        logger.info("🎯 Phase 2: Génération des opportunités...")
        generation_start_time = time.time()
        
        all_opportunities = []
        batch_size = 20  # Traiter par lots de 20 symboles
        
        for i in range(0, len(ml_system.symbols), batch_size):
            batch_symbols = ml_system.symbols[i:i + batch_size]
            logger.info(f"📊 Traitement du lot {i//batch_size + 1}/{(len(ml_system.symbols) + batch_size - 1)//batch_size}: {len(batch_symbols)} symboles")
            
            # Générer les opportunités pour ce lot
            batch_opportunities = ml_system.generate_opportunities(
                symbols=batch_symbols,
                horizons=ml_system.horizons
            )
            
            all_opportunities.extend(batch_opportunities)
            
            # Stocker par lots pour éviter les problèmes de mémoire
            if len(all_opportunities) >= 5000:  # Stocker tous les 5000
                logger.info(f"💾 Stockage intermédiaire de {len(all_opportunities)} opportunités...")
                store_opportunities_in_db(db, all_opportunities)
                all_opportunities = []  # Reset
        
        # Stocker les dernières opportunités
        if all_opportunities:
            logger.info(f"💾 Stockage final de {len(all_opportunities)} opportunités...")
            store_opportunities_in_db(db, all_opportunities)
        
        generation_time = time.time() - generation_start_time
        total_time = time.time() - start_time
        
        # Statistiques finales
        total_opportunities = db.execute(text("SELECT COUNT(*) FROM ml_opportunities_xgboost")).scalar()
        unique_symbols = db.execute(text("SELECT COUNT(DISTINCT symbol) FROM ml_opportunities_xgboost")).scalar()
        date_range = db.execute(text("SELECT MIN(date), MAX(date) FROM ml_opportunities_xgboost")).fetchone()
        
        logger.info("\n" + "="*60)
        logger.info("🎉 GÉNÉRATION COMPLÈTE TERMINÉE!")
        logger.info("="*60)
        logger.info(f"⏱️  Temps total: {total_time:.2f} secondes")
        logger.info(f"🎯 Temps d'entraînement: {training_time:.2f} secondes")
        logger.info(f"📊 Temps de génération: {generation_time:.2f} secondes")
        logger.info(f"📈 Total opportunités générées: {total_opportunities:,}")
        logger.info(f"🏷️  Symboles uniques: {unique_symbols}")
        logger.info(f"📅 Période couverte: {date_range[0]} à {date_range[1]}")
        logger.info(f"⏰ Horizons: {ml_system.horizons}")
        
        # Top 5 opportunités par confiance
        top_opportunities = db.execute(text("""
            SELECT symbol, recommendation, confidence_level, potential_return, horizon_days
            FROM ml_opportunities_xgboost 
            ORDER BY confidence_level DESC 
            LIMIT 5
        """)).fetchall()
        
        logger.info("\n🏆 Top 5 opportunités par confiance:")
        for opp in top_opportunities:
            logger.info(f"  {opp[0]}: {opp[1]} (confiance: {opp[2]:.3f}, retour: {opp[3]:.3f}, horizon: {opp[4]}j)")
        
        logger.info("\n✅ Génération complète terminée avec succès!")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    generate_historical_xgboost_opportunities()
