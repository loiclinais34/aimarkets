#!/usr/bin/env python3
"""
Script pour recalculer TOUS les indicateurs techniques manquants par batch
"""

import logging
import pandas as pd
import numpy as np
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

def fix_all_missing_indicators():
    """Corrige TOUS les indicateurs techniques manquants par batch."""
    
    # Configuration de la base de données
    DATABASE_URL = settings.database_url
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        logger.info("🔧 Début de la correction complète des indicateurs manquants")
        
        # Compter le total d'enregistrements à traiter
        count_query = """
        SELECT COUNT(*) 
        FROM advanced_technical_indicators
        WHERE bb_upper IS NOT NULL AND bb_lower IS NOT NULL
        """
        
        total_count = db.execute(text(count_query)).scalar()
        logger.info(f"📊 Total d'enregistrements à traiter: {total_count:,}")
        
        batch_size = 5000
        processed = 0
        
        while processed < total_count:
            logger.info(f"\n🔄 Traitement du batch {processed//batch_size + 1} (enregistrements {processed+1} à {min(processed+batch_size, total_count)})")
            
            # Récupérer le batch suivant
            query = f"""
            SELECT symbol, date, open, high, low, close, volume,
                   bb_upper, bb_middle, bb_lower,
                   rsi_14, stoch_k, willr_14, cci_14,
                   atr_14, stddev_20, bb_width,
                   sma_20, sma_50, ema_20, ema_50
            FROM advanced_technical_indicators
            WHERE bb_upper IS NOT NULL AND bb_lower IS NOT NULL
            ORDER BY symbol, date
            LIMIT {batch_size} OFFSET {processed}
            """
            
            df = pd.read_sql(query, db.connection())
            
            if df.empty:
                logger.info("✅ Aucune donnée restante à traiter")
                break
            
            logger.info(f"📈 Récupéré {len(df)} enregistrements pour ce batch")
            
            # Recalculer les indicateurs manquants
            # bb_position et bb_squeeze
            if 'bb_upper' in df.columns and 'bb_lower' in df.columns and 'close' in df.columns:
                df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
                df['bb_squeeze'] = (df['bb_upper'] - df['bb_lower']) / df['close']
            
            # Ratios de moyennes mobiles
            if 'sma_20' in df.columns and 'sma_50' in df.columns:
                df['sma_ratio_20_50'] = df['sma_20'] / df['sma_50']
            
            if 'ema_20' in df.columns and 'ema_50' in df.columns:
                df['ema_ratio_20_50'] = df['ema_20'] / df['ema_50']
            
            # Momentum composite
            momentum_cols = ['rsi_14', 'stoch_k', 'willr_14', 'cci_14']
            available_momentum = [col for col in momentum_cols if col in df.columns]
            if available_momentum:
                df['momentum_composite'] = df[available_momentum].mean(axis=1)
            
            # Volatilité composite
            volatility_cols = ['atr_14', 'stddev_20', 'bb_width']
            available_volatility = [col for col in volatility_cols if col in df.columns]
            if available_volatility:
                df['volatility_composite'] = df[available_volatility].mean(axis=1)
            
            # Force de tendance
            trend_cols = ['sma_ratio_20_50', 'ema_ratio_20_50']
            available_trend = [col for col in trend_cols if col in df.columns]
            if available_trend:
                df['trend_strength'] = df[available_trend].mean(axis=1)
            
            # Mettre à jour la base de données par batch
            logger.info("💾 Mise à jour de la base de données...")
            
            # Utiliser une mise à jour en masse plus efficace
            update_data = []
            for _, row in df.iterrows():
                update_data.append({
                    'symbol': row['symbol'],
                    'date': row['date'],
                    'bb_position': row.get('bb_position'),
                    'bb_squeeze': row.get('bb_squeeze'),
                    'sma_ratio_20_50': row.get('sma_ratio_20_50'),
                    'ema_ratio_20_50': row.get('ema_ratio_20_50'),
                    'momentum_composite': row.get('momentum_composite'),
                    'volatility_composite': row.get('volatility_composite'),
                    'trend_strength': row.get('trend_strength')
                })
            
            # Mise à jour par batch
            for data in update_data:
                update_query = """
                UPDATE advanced_technical_indicators 
                SET bb_position = :bb_position,
                    bb_squeeze = :bb_squeeze,
                    sma_ratio_20_50 = :sma_ratio_20_50,
                    ema_ratio_20_50 = :ema_ratio_20_50,
                    momentum_composite = :momentum_composite,
                    volatility_composite = :volatility_composite,
                    trend_strength = :trend_strength,
                    updated_at = CURRENT_TIMESTAMP
                WHERE symbol = :symbol AND date = :date
                """
                
                db.execute(text(update_query), data)
            
            db.commit()
            processed += len(df)
            
            logger.info(f"✅ Batch terminé. Total traité: {processed:,}/{total_count:,} ({processed/total_count*100:.1f}%)")
        
        # Vérification finale
        logger.info("\n📊 Vérification finale...")
        stats_query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(bb_position) as bb_position_count,
            COUNT(momentum_composite) as momentum_composite_count,
            COUNT(volatility_composite) as volatility_composite_count,
            COUNT(trend_strength) as trend_strength_count
        FROM advanced_technical_indicators
        """
        
        stats_final = db.execute(text(stats_query)).fetchone()
        logger.info(f"📊 État final:")
        logger.info(f"   Total: {stats_final[0]:,}")
        logger.info(f"   bb_position: {stats_final[1]:,}")
        logger.info(f"   momentum_composite: {stats_final[2]:,}")
        logger.info(f"   volatility_composite: {stats_final[3]:,}")
        logger.info(f"   trend_strength: {stats_final[4]:,}")
        
        logger.info("🎉 Correction complète des indicateurs terminée avec succès!")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la correction: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_all_missing_indicators()
