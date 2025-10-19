#!/usr/bin/env python3
"""
Script pour recalculer et corriger les indicateurs techniques manquants
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
from scripts.data_processing.talib_indicators import TALibIndicators

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_missing_indicators():
    """Corrige les indicateurs techniques manquants."""
    
    # Configuration de la base de données
    DATABASE_URL = settings.database_url
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        logger.info("🔧 Début de la correction des indicateurs manquants")
        
        # Vérifier l'état actuel
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
        logger.info(f"📊 État actuel:")
        logger.info(f"   Total: {stats[0]:,}")
        logger.info(f"   bb_position: {stats[1]:,}")
        logger.info(f"   momentum_composite: {stats[2]:,}")
        logger.info(f"   volatility_composite: {stats[3]:,}")
        logger.info(f"   trend_strength: {stats[4]:,}")
        
        # Récupérer les données pour recalculer les indicateurs manquants
        query = """
        SELECT symbol, date, open, high, low, close, volume,
               bb_upper, bb_middle, bb_lower,
               rsi_14, stoch_k, willr_14, cci_14,
               atr_14, stddev_20, bb_width,
               sma_20, sma_50, ema_20, ema_50
        FROM advanced_technical_indicators
        WHERE bb_upper IS NOT NULL AND bb_lower IS NOT NULL
        ORDER BY symbol, date
        LIMIT 1000
        """
        
        df = pd.read_sql(query, db.connection())
        logger.info(f"📈 Récupéré {len(df)} enregistrements pour correction")
        
        if df.empty:
            logger.warning("⚠️ Aucune donnée à corriger")
            return
        
        # Initialiser le calculateur TA-Lib
        talib_calc = TALibIndicators()
        
        # Recalculer les indicateurs manquants
        logger.info("🔄 Recalcul des indicateurs manquants...")
        
        # bb_position
        if 'bb_upper' in df.columns and 'bb_lower' in df.columns and 'close' in df.columns:
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            df['bb_squeeze'] = (df['bb_upper'] - df['bb_lower']) / df['close']
            logger.info("✅ bb_position et bb_squeeze recalculés")
        
        # Ratios de moyennes mobiles
        if 'sma_20' in df.columns and 'sma_50' in df.columns:
            df['sma_ratio_20_50'] = df['sma_20'] / df['sma_50']
            logger.info("✅ sma_ratio_20_50 recalculé")
        
        if 'ema_20' in df.columns and 'ema_50' in df.columns:
            df['ema_ratio_20_50'] = df['ema_20'] / df['ema_50']
            logger.info("✅ ema_ratio_20_50 recalculé")
        
        # Momentum composite
        momentum_cols = ['rsi_14', 'stoch_k', 'willr_14', 'cci_14']
        available_momentum = [col for col in momentum_cols if col in df.columns]
        if available_momentum:
            df['momentum_composite'] = df[available_momentum].mean(axis=1)
            logger.info(f"✅ momentum_composite recalculé avec {len(available_momentum)} indicateurs")
        
        # Volatilité composite
        volatility_cols = ['atr_14', 'stddev_20', 'bb_width']
        available_volatility = [col for col in volatility_cols if col in df.columns]
        if available_volatility:
            df['volatility_composite'] = df[available_volatility].mean(axis=1)
            logger.info(f"✅ volatility_composite recalculé avec {len(available_volatility)} indicateurs")
        
        # Force de tendance
        trend_cols = ['sma_ratio_20_50', 'ema_ratio_20_50']
        available_trend = [col for col in trend_cols if col in df.columns]
        if available_trend:
            df['trend_strength'] = df[available_trend].mean(axis=1)
            logger.info(f"✅ trend_strength recalculé avec {len(available_trend)} indicateurs")
        
        # Mettre à jour la base de données
        logger.info("💾 Mise à jour de la base de données...")
        
        for _, row in df.iterrows():
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
            
            db.execute(text(update_query), {
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
        
        db.commit()
        logger.info("✅ Mise à jour terminée")
        
        # Vérifier le résultat
        stats_after = db.execute(text(stats_query)).fetchone()
        logger.info(f"📊 État après correction:")
        logger.info(f"   Total: {stats_after[0]:,}")
        logger.info(f"   bb_position: {stats_after[1]:,}")
        logger.info(f"   momentum_composite: {stats_after[2]:,}")
        logger.info(f"   volatility_composite: {stats_after[3]:,}")
        logger.info(f"   trend_strength: {stats_after[4]:,}")
        
        logger.info("🎉 Correction des indicateurs terminée avec succès!")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la correction: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_missing_indicators()
