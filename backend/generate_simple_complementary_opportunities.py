#!/usr/bin/env python3
"""
Script simplifié pour générer les opportunités XGBoost complémentaires
Période: 2024-02-07 à 2025-10-17
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

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

def get_available_dates_for_horizon(db, symbol: str, start_date: date, end_date: date, horizon_days: int) -> list:
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

def get_all_symbols(db) -> list:
    """Récupère tous les symboles disponibles."""
    query = "SELECT DISTINCT symbol FROM historical_data ORDER BY symbol"
    result = db.execute(text(query)).fetchall()
    return [row[0] for row in result]

def generate_simple_opportunities():
    """Génère des opportunités simples basées sur des règles techniques."""
    
    # Configuration de la base de données
    DATABASE_URL = settings.database_url
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        # Période complémentaire
        start_date = date(2024, 2, 7)  # Après la dernière opportunité existante
        end_date = date(2025, 10, 17)  # Dernière date disponible
        
        logger.info(f"🚀 Génération des opportunités complémentaires (règles simples)")
        logger.info(f"📅 Période: {start_date} → {end_date}")
        
        # Récupérer tous les symboles
        all_symbols = get_all_symbols(db)
        logger.info(f"📈 {len(all_symbols)} symboles à traiter")
        
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
                        
                        row = df.iloc[0]
                        
                        # Règles simples basées sur les indicateurs techniques
                        rsi = row.get('rsi_14', 50)
                        macd = row.get('macd', 0)
                        bb_position = row.get('bb_position', 0.5)
                        adx = row.get('adx_14', 20)
                        
                        # Logique de recommandation simple
                        recommendation = "HOLD"
                        confidence = 0.6
                        potential_return = 0.01
                        
                        if rsi < 30 and macd > 0 and bb_position < 0.2:
                            recommendation = "BUY_STRONG"
                            confidence = 0.85
                            potential_return = 0.05
                        elif rsi < 40 and macd > 0:
                            recommendation = "BUY_WEAK"
                            confidence = 0.75
                            potential_return = 0.03
                        elif rsi > 70 and macd < 0 and bb_position > 0.8:
                            recommendation = "SELL_STRONG"
                            confidence = 0.85
                            potential_return = -0.05
                        elif rsi > 60 and macd < 0:
                            recommendation = "SELL_WEAK"
                            confidence = 0.75
                            potential_return = -0.03
                        
                        # Ajuster selon l'horizon
                        if horizon == 1:
                            potential_return *= 0.3
                        elif horizon == 7:
                            potential_return *= 0.7
                        # horizon == 30 garde le potentiel complet
                        
                        opportunity = {
                            'symbol': symbol,
                            'date': opp_date,
                            'horizon_days': horizon,
                            'recommendation': recommendation,
                            'confidence_level': float(confidence),
                            'potential_return': float(potential_return),
                            'risk_score': float(1 - confidence),
                            'ml_model_name': 'simple_rules_v1',
                            'ml_model_version': '1.0',
                            'technical_indicators': json.dumps({
                                'rsi_14': float(rsi) if pd.notna(rsi) else 50,
                                'macd': float(macd) if pd.notna(macd) else 0,
                                'bb_position': float(bb_position) if pd.notna(bb_position) else 0.5,
                                'adx_14': float(adx) if pd.notna(adx) else 20,
                                'volume_sma_ratio': float(row.get('volume_sma_ratio', 1)) if pd.notna(row.get('volume_sma_ratio', 1)) else 1
                            }),
                            'ml_features': json.dumps({
                                'momentum_score': float(rsi / 100) if pd.notna(rsi) else 0.5,
                                'trend_score': float(macd) if pd.notna(macd) else 0,
                                'bb_signal': float(bb_position) if pd.notna(bb_position) else 0.5
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
    generate_simple_opportunities()
