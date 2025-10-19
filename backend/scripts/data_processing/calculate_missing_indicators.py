#!/usr/bin/env python3
"""
Script pour calculer les indicateurs techniques manquants
"""

import logging
import pandas as pd
import numpy as np
import talib
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

def calculate_missing_indicators():
    """Calcule les indicateurs techniques manquants."""
    
    # Configuration de la base de données
    DATABASE_URL = settings.database_url
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        logger.info("🔧 Début du calcul des indicateurs manquants")
        
        # Liste des indicateurs manquants identifiés
        missing_indicators = [
            'mfi_14',      # Money Flow Index
            'midpoint_20', # MidPoint
            'midprice_20', # MidPrice
            'obv_price_divergence', # OBV Price Divergence
            'sar',         # Parabolic SAR
            't3_20',       # T3 Moving Average
            'vpt',         # Volume Price Trend
            'wad'          # Williams Accumulation/Distribution
        ]
        
        logger.info(f"📊 Indicateurs à calculer: {len(missing_indicators)}")
        for indicator in missing_indicators:
            logger.info(f"   - {indicator}")
        
        # Récupérer les données nécessaires
        logger.info("\n📈 Récupération des données...")
        
        query = """
        SELECT symbol, date, open, high, low, close, volume, obv
        FROM advanced_technical_indicators
        WHERE close IS NOT NULL AND volume IS NOT NULL AND obv IS NOT NULL
        ORDER BY symbol, date
        """
        
        df = pd.read_sql(query, db.connection())
        logger.info(f"   Récupéré {len(df):,} enregistrements")
        
        if df.empty:
            logger.warning("⚠️ Aucune donnée à traiter")
            return
        
        # Convertir les colonnes en float
        for col in ['open', 'high', 'low', 'close', 'volume', 'obv']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculer les indicateurs manquants
        logger.info("\n🔄 Calcul des indicateurs...")
        
        # Money Flow Index (MFI)
        logger.info("   📊 Calcul du Money Flow Index (MFI)...")
        df['mfi_14'] = talib.MFI(df['high'], df['low'], df['close'], df['volume'], timeperiod=14)
        
        # MidPoint
        logger.info("   📊 Calcul du MidPoint...")
        df['midpoint_20'] = talib.MIDPOINT(df['close'], timeperiod=20)
        
        # MidPrice
        logger.info("   📊 Calcul du MidPrice...")
        df['midprice_20'] = talib.MIDPRICE(df['high'], df['low'], timeperiod=20)
        
        # Parabolic SAR
        logger.info("   📊 Calcul du Parabolic SAR...")
        df['sar'] = talib.SAR(df['high'], df['low'])
        
        # T3 Moving Average
        logger.info("   📊 Calcul du T3 Moving Average...")
        df['t3_20'] = talib.T3(df['close'], timeperiod=20)
        
        # Volume Price Trend (VPT) - Calcul manuel car VPT n'existe pas dans TA-Lib
        logger.info("   📊 Calcul du Volume Price Trend...")
        df['vpt'] = (df['close'].pct_change() * df['volume']).cumsum()
        
        # Williams Accumulation/Distribution (WAD) - Calcul manuel car WAD n'existe pas dans TA-Lib
        logger.info("   📊 Calcul du Williams A/D...")
        # WAD = Sum of (Close - True Low) when Close > Previous Close, else Sum of (Close - True High)
        df['true_low'] = df[['low', 'close']].min(axis=1)
        df['true_high'] = df[['high', 'close']].max(axis=1)
        df['wad'] = np.where(df['close'] > df['close'].shift(1), 
                            df['close'] - df['true_low'], 
                            df['close'] - df['true_high']).cumsum()
        
        # OBV Price Divergence (calcul personnalisé)
        logger.info("   📊 Calcul de l'OBV Price Divergence...")
        df['obv_price_divergence'] = df['obv'].pct_change() - df['close'].pct_change()
        
        # Mettre à jour la base de données
        logger.info("\n💾 Mise à jour de la base de données...")
        
        batch_size = 1000
        total_updated = 0
        
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i+batch_size]
            
            for _, row in batch_df.iterrows():
                update_query = """
                UPDATE advanced_technical_indicators 
                SET mfi_14 = :mfi_14,
                    midpoint_20 = :midpoint_20,
                    midprice_20 = :midprice_20,
                    obv_price_divergence = :obv_price_divergence,
                    sar = :sar,
                    t3_20 = :t3_20,
                    vpt = :vpt,
                    wad = :wad,
                    updated_at = CURRENT_TIMESTAMP
                WHERE symbol = :symbol AND date = :date
                """
                
                db.execute(text(update_query), {
                    'symbol': row['symbol'],
                    'date': row['date'],
                    'mfi_14': row.get('mfi_14'),
                    'midpoint_20': row.get('midpoint_20'),
                    'midprice_20': row.get('midprice_20'),
                    'obv_price_divergence': row.get('obv_price_divergence'),
                    'sar': row.get('sar'),
                    't3_20': row.get('t3_20'),
                    'vpt': row.get('vpt'),
                    'wad': row.get('wad')
                })
            
            total_updated += len(batch_df)
            logger.info(f"   ✅ Batch {i//batch_size + 1}: {len(batch_df)} enregistrements mis à jour ({total_updated:,}/{len(df):,})")
        
        db.commit()
        logger.info("✅ Mise à jour terminée")
        
        # Vérification finale
        logger.info("\n📊 Vérification finale...")
        
        for indicator in missing_indicators:
            count_query = f"SELECT COUNT({indicator}) FROM advanced_technical_indicators WHERE {indicator} IS NOT NULL"
            count = db.execute(text(count_query)).scalar()
            logger.info(f"   ✅ {indicator}: {count:,} enregistrements calculés")
        
        logger.info("🎉 Calcul des indicateurs manquants terminé avec succès!")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du calcul: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    calculate_missing_indicators()
