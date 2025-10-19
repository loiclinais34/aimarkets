#!/usr/bin/env python3
"""
Script pour générer les opportunités XGBoost complémentaires
Période: 2024-02-07 à 2025-10-17
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json
import pickle
from typing import List, Dict, Any
import xgboost as xgb
from xgboost import XGBClassifier, XGBRegressor

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
from app.models.ml_opportunities_xgboost import MLOpportunityXGBoost
from advanced_xgboost_ml_system import AdvancedXGBoostMLSystem

def get_available_dates_for_horizon(db, symbol: str, start_date: date, end_date: date, horizon_days: int) -> List[date]:
    """
    Récupère les dates pour lesquelles on peut générer des opportunités avec un horizon donné.
    On ne peut générer une opportunité que si on a le cours de clôture à l'horizon.
    """
    query = f"""
    SELECT DISTINCT h1.date as opportunity_date
    FROM historical_data h1
    JOIN historical_data h2 ON h1.symbol = h2.symbol 
        AND h2.date = h1.date + INTERVAL '{horizon_days} days'
    WHERE h1.symbol = '{symbol}'
        AND h1.date >= '{start_date}'
        AND h1.date <= '{end_date}'
        AND h2.date <= (SELECT MAX(date) FROM historical_data WHERE symbol = '{symbol}')
    ORDER BY h1.date
    """
    
    result = db.execute(text(query)).fetchall()
    return [row[0] for row in result]

def get_all_symbols(db) -> List[str]:
    """Récupère tous les symboles disponibles."""
    query = "SELECT DISTINCT symbol FROM historical_data ORDER BY symbol"
    result = db.execute(text(query)).fetchall()
    return [row[0] for row in result]

def generate_complementary_opportunities():
    """Génère les opportunités XGBoost pour la période complémentaire."""
    
    # Configuration de la base de données
    DATABASE_URL = settings.database_url
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Période complémentaire
        start_date = date(2024, 2, 7)  # Après la dernière opportunité existante
        end_date = date(2025, 10, 17)  # Dernière date disponible
        
        logger.info(f"🚀 Génération des opportunités complémentaires")
        logger.info(f"📅 Période: {start_date} → {end_date}")
        
        # Récupérer tous les symboles
        all_symbols = get_all_symbols(db)
        logger.info(f"📈 {len(all_symbols)} symboles à traiter")
        
        # Initialiser le système ML
        db_config = {
            'host': 'localhost',
            'port': '5432',
            'database': 'aimarkets',
            'user': 'loiclinais',
            'password': ''
        }
        ml_system = AdvancedXGBoostMLSystem(db_config)
        
        # Charger les modèles pré-entraînés
        try:
            with open('xgboost_models.pkl', 'rb') as f:
                models_data = pickle.load(f)
            ml_system.classifier = models_data['classifier']
            ml_system.regressor = models_data['regressor']
            ml_system.scaler = models_data['scaler']
            ml_system.label_encoder = models_data['label_encoder']
            logger.info("✅ Modèles XGBoost chargés avec succès")
        except FileNotFoundError:
            logger.error("❌ Fichier xgboost_models.pkl non trouvé. Veuillez d'abord entraîner les modèles.")
            return
        
        # Horizons à traiter
        horizons = [1, 7, 30]
        
        total_opportunities_generated = 0
        opportunities_to_store = []
        
        # Traiter chaque symbole
        for i, symbol in enumerate(all_symbols):
            logger.info(f"\n📊 Traitement de {symbol} ({i+1}/{len(all_symbols)})")
            
            # Pour chaque horizon, déterminer les dates disponibles
            for horizon in horizons:
                available_dates = get_available_dates_for_horizon(db, symbol, start_date, end_date, horizon)
                
                if not available_dates:
                    logger.info(f"  ⚠️ Aucune date disponible pour {symbol} avec horizon {horizon}d")
                    continue
                
                logger.info(f"  📅 Horizon {horizon}d: {len(available_dates)} dates disponibles")
                
                # Générer les opportunités pour chaque date disponible
                for opp_date in available_dates:
                    try:
                        # Récupérer les données pour cette date
                        query = f"""
                        SELECT ati.*, hd.open, hd.high, hd.low, hd.close, hd.volume
                        FROM advanced_technical_indicators ati
                        JOIN historical_data hd ON ati.symbol = hd.symbol AND ati.date = hd.date
                        WHERE ati.symbol = '{symbol}' 
                            AND ati.date = '{opp_date}'
                        ORDER BY ati.date DESC
                        LIMIT 1
                        """
                        
                        df = pd.read_sql(query, db.connection())
                        
                        if df.empty:
                            logger.warning(f"    ⚠️ Aucune donnée technique pour {symbol} le {opp_date}")
                            continue
                        
                        # Préparer les features
                        features = ml_system.prepare_features_for_prediction(df.iloc[0])
                        
                        if features is None:
                            logger.warning(f"    ⚠️ Impossible de préparer les features pour {symbol} le {opp_date}")
                            continue
                        
                        # Faire les prédictions
                        features_scaled = ml_system.scaler.transform([features])
                        prediction = ml_system.classifier.predict(features_scaled)[0]
                        probabilities = ml_system.classifier.predict_proba(features_scaled)[0]
                        predicted_return = ml_system.regressor.predict(features_scaled)[0]
                        
                        confidence = np.max(probabilities)
                        
                        # Filtrer les opportunités avec une confiance suffisante
                        if confidence >= 0.6:
                            opportunity = {
                                'symbol': symbol,
                                'date': opp_date,
                                'horizon_days': horizon,
                                'recommendation': prediction,
                                'confidence_level': float(confidence),
                                'potential_return': float(predicted_return),
                                'risk_score': float(1 - confidence),
                                'ml_model_name': 'xgboost_advanced_v1',
                                'ml_model_version': '1.0',
                                'technical_indicators': json.dumps({
                                    'rsi_14': float(df.iloc[0].get('rsi_14', 0) or 0) if pd.notna(df.iloc[0].get('rsi_14', 0)) else 0,
                                    'macd': float(df.iloc[0].get('macd', 0) or 0) if pd.notna(df.iloc[0].get('macd', 0)) else 0,
                                    'bb_position': float(df.iloc[0].get('bb_position', 0) or 0) if pd.notna(df.iloc[0].get('bb_position', 0)) else 0,
                                    'adx_14': float(df.iloc[0].get('adx_14', 0) or 0) if pd.notna(df.iloc[0].get('adx_14', 0)) else 0,
                                    'volume_sma_ratio': float(df.iloc[0].get('volume_sma_ratio', 0) or 0) if pd.notna(df.iloc[0].get('volume_sma_ratio', 0)) else 0
                                }),
                                'ml_features': json.dumps({
                                    'momentum_score': float(df.iloc[0].get('momentum_score', 0) or 0) if pd.notna(df.iloc[0].get('momentum_score', 0)) else 0,
                                    'trend_score': float(df.iloc[0].get('trend_score', 0) or 0) if pd.notna(df.iloc[0].get('trend_score', 0)) else 0,
                                    'bb_signal': float(df.iloc[0].get('bb_signal', 0) or 0) if pd.notna(df.iloc[0].get('bb_signal', 0)) else 0
                                })
                            }
                            
                            opportunities_to_store.append(opportunity)
                            total_opportunities_generated += 1
                            
                            if total_opportunities_generated % 1000 == 0:
                                logger.info(f"    📦 {total_opportunities_generated} opportunités générées...")
                    
                    except Exception as e:
                        logger.warning(f"    ⚠️ Erreur pour {symbol} le {opp_date}: {e}")
                        continue
                
                # Stockage par batch pour optimiser les performances
                if len(opportunities_to_store) >= 1000:
                    logger.info(f"💾 Stockage de {len(opportunities_to_store)} opportunités...")
                    
                    for opp_data in opportunities_to_store:
                        opportunity_obj = MLOpportunityXGBoost(**opp_data)
                        db.add(opportunity_obj)
                    
                    db.commit()
                    opportunities_to_store = []
                    logger.info(f"✅ {total_opportunities_generated} opportunités stockées")
        
        # Stocker les opportunités restantes
        if opportunities_to_store:
            logger.info(f"💾 Stockage final de {len(opportunities_to_store)} opportunités...")
            
            for opp_data in opportunities_to_store:
                opportunity_obj = MLOpportunityXGBoost(**opp_data)
                db.add(opportunity_obj)
            
            db.commit()
            logger.info(f"✅ Stockage final terminé")
        
        logger.info(f"\n🎉 GÉNÉRATION COMPLÉMENTAIRE TERMINÉE!")
        logger.info(f"📈 Total opportunités générées: {total_opportunities_generated}")
        logger.info(f"📅 Période couverte: {start_date} → {end_date}")
        logger.info(f"🏷️ Symboles traités: {len(all_symbols)}")
        logger.info(f"⏰ Horizons: {horizons}")
        
        # Vérification finale
        final_count = db.execute(text("SELECT COUNT(*) FROM ml_opportunities_xgboost")).scalar()
        logger.info(f"📊 Total opportunités en base: {final_count}")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la génération complémentaire: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_complementary_opportunities()