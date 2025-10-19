#!/usr/bin/env python3
"""
Script d'analyse exhaustive de la qualité des données dans advanced_technical_indicators
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

def analyze_data_quality():
    """Analyse exhaustive de la qualité des données."""
    
    # Configuration de la base de données
    DATABASE_URL = settings.database_url
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    
    try:
        logger.info("🔍 Début de l'analyse exhaustive de la qualité des données")
        
        # 1. Statistiques générales
        logger.info("\n📊 STATISTIQUES GÉNÉRALES")
        general_stats = db.execute(text("""
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT symbol) as unique_symbols,
                MIN(date) as earliest_date,
                MAX(date) as latest_date,
                COUNT(DISTINCT date) as unique_dates
            FROM advanced_technical_indicators
        """)).fetchone()
        
        logger.info(f"   Total enregistrements: {general_stats[0]:,}")
        logger.info(f"   Symboles uniques: {general_stats[1]}")
        logger.info(f"   Période: {general_stats[2]} → {general_stats[3]}")
        logger.info(f"   Dates uniques: {general_stats[4]}")
        
        # 2. Analyse par groupe d'indicateurs
        logger.info("\n📈 ANALYSE PAR GROUPE D'INDICATEURS")
        
        # Données OHLCV de base
        ohlcv_stats = db.execute(text("""
            SELECT 
                COUNT(open) as open_count,
                COUNT(high) as high_count,
                COUNT(low) as low_count,
                COUNT(close) as close_count,
                COUNT(volume) as volume_count
            FROM advanced_technical_indicators
        """)).fetchone()
        
        logger.info(f"   📊 Données OHLCV:")
        logger.info(f"      Open: {ohlcv_stats[0]:,} ({ohlcv_stats[0]/general_stats[0]*100:.1f}%)")
        logger.info(f"      High: {ohlcv_stats[1]:,} ({ohlcv_stats[1]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Low: {ohlcv_stats[2]:,} ({ohlcv_stats[2]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Close: {ohlcv_stats[3]:,} ({ohlcv_stats[3]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Volume: {ohlcv_stats[4]:,} ({ohlcv_stats[4]/general_stats[0]*100:.1f}%)")
        
        # Moyennes mobiles simples
        sma_stats = db.execute(text("""
            SELECT 
                COUNT(sma_5) as sma_5_count,
                COUNT(sma_10) as sma_10_count,
                COUNT(sma_20) as sma_20_count,
                COUNT(sma_50) as sma_50_count,
                COUNT(sma_100) as sma_100_count,
                COUNT(sma_200) as sma_200_count
            FROM advanced_technical_indicators
        """)).fetchone()
        
        logger.info(f"   📈 Moyennes mobiles simples (SMA):")
        logger.info(f"      SMA 5: {sma_stats[0]:,} ({sma_stats[0]/general_stats[0]*100:.1f}%)")
        logger.info(f"      SMA 10: {sma_stats[1]:,} ({sma_stats[1]/general_stats[0]*100:.1f}%)")
        logger.info(f"      SMA 20: {sma_stats[2]:,} ({sma_stats[2]/general_stats[0]*100:.1f}%)")
        logger.info(f"      SMA 50: {sma_stats[3]:,} ({sma_stats[3]/general_stats[0]*100:.1f}%)")
        logger.info(f"      SMA 100: {sma_stats[4]:,} ({sma_stats[4]/general_stats[0]*100:.1f}%)")
        logger.info(f"      SMA 200: {sma_stats[5]:,} ({sma_stats[5]/general_stats[0]*100:.1f}%)")
        
        # Moyennes mobiles exponentielles
        ema_stats = db.execute(text("""
            SELECT 
                COUNT(ema_5) as ema_5_count,
                COUNT(ema_10) as ema_10_count,
                COUNT(ema_20) as ema_20_count,
                COUNT(ema_50) as ema_50_count,
                COUNT(ema_100) as ema_100_count,
                COUNT(ema_200) as ema_200_count
            FROM advanced_technical_indicators
        """)).fetchone()
        
        logger.info(f"   📈 Moyennes mobiles exponentielles (EMA):")
        logger.info(f"      EMA 5: {ema_stats[0]:,} ({ema_stats[0]/general_stats[0]*100:.1f}%)")
        logger.info(f"      EMA 10: {ema_stats[1]:,} ({ema_stats[1]/general_stats[0]*100:.1f}%)")
        logger.info(f"      EMA 20: {ema_stats[2]:,} ({ema_stats[2]/general_stats[0]*100:.1f}%)")
        logger.info(f"      EMA 50: {ema_stats[3]:,} ({ema_stats[3]/general_stats[0]*100:.1f}%)")
        logger.info(f"      EMA 100: {ema_stats[4]:,} ({ema_stats[4]/general_stats[0]*100:.1f}%)")
        logger.info(f"      EMA 200: {ema_stats[5]:,} ({ema_stats[5]/general_stats[0]*100:.1f}%)")
        
        # Bollinger Bands
        bb_stats = db.execute(text("""
            SELECT 
                COUNT(bb_upper) as bb_upper_count,
                COUNT(bb_middle) as bb_middle_count,
                COUNT(bb_lower) as bb_lower_count,
                COUNT(bb_width) as bb_width_count,
                COUNT(bb_percent) as bb_percent_count,
                COUNT(bb_position) as bb_position_count,
                COUNT(bb_squeeze) as bb_squeeze_count
            FROM advanced_technical_indicators
        """)).fetchone()
        
        logger.info(f"   📊 Bollinger Bands:")
        logger.info(f"      BB Upper: {bb_stats[0]:,} ({bb_stats[0]/general_stats[0]*100:.1f}%)")
        logger.info(f"      BB Middle: {bb_stats[1]:,} ({bb_stats[1]/general_stats[0]*100:.1f}%)")
        logger.info(f"      BB Lower: {bb_stats[2]:,} ({bb_stats[2]/general_stats[0]*100:.1f}%)")
        logger.info(f"      BB Width: {bb_stats[3]:,} ({bb_stats[3]/general_stats[0]*100:.1f}%)")
        logger.info(f"      BB Percent: {bb_stats[4]:,} ({bb_stats[4]/general_stats[0]*100:.1f}%)")
        logger.info(f"      BB Position: {bb_stats[5]:,} ({bb_stats[5]/general_stats[0]*100:.1f}%)")
        logger.info(f"      BB Squeeze: {bb_stats[6]:,} ({bb_stats[6]/general_stats[0]*100:.1f}%)")
        
        # Indicateurs de momentum
        momentum_stats = db.execute(text("""
            SELECT 
                COUNT(rsi_14) as rsi_14_count,
                COUNT(rsi_21) as rsi_21_count,
                COUNT(stoch_k) as stoch_k_count,
                COUNT(stoch_d) as stoch_d_count,
                COUNT(willr_14) as willr_14_count,
                COUNT(cci_14) as cci_14_count,
                COUNT(macd) as macd_count,
                COUNT(macd_signal) as macd_signal_count,
                COUNT(macd_hist) as macd_hist_count
            FROM advanced_technical_indicators
        """)).fetchone()
        
        logger.info(f"   🎯 Indicateurs de momentum:")
        logger.info(f"      RSI 14: {momentum_stats[0]:,} ({momentum_stats[0]/general_stats[0]*100:.1f}%)")
        logger.info(f"      RSI 21: {momentum_stats[1]:,} ({momentum_stats[1]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Stochastic K: {momentum_stats[2]:,} ({momentum_stats[2]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Stochastic D: {momentum_stats[3]:,} ({momentum_stats[3]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Williams %R: {momentum_stats[4]:,} ({momentum_stats[4]/general_stats[0]*100:.1f}%)")
        logger.info(f"      CCI 14: {momentum_stats[5]:,} ({momentum_stats[5]/general_stats[0]*100:.1f}%)")
        logger.info(f"      MACD: {momentum_stats[6]:,} ({momentum_stats[6]/general_stats[0]*100:.1f}%)")
        logger.info(f"      MACD Signal: {momentum_stats[7]:,} ({momentum_stats[7]/general_stats[0]*100:.1f}%)")
        logger.info(f"      MACD Histogram: {momentum_stats[8]:,} ({momentum_stats[8]/general_stats[0]*100:.1f}%)")
        
        # Indicateurs de volatilité
        volatility_stats = db.execute(text("""
            SELECT 
                COUNT(atr_14) as atr_14_count,
                COUNT(atr_20) as atr_20_count,
                COUNT(stddev_20) as stddev_20_count,
                COUNT(stddev_50) as stddev_50_count,
                COUNT(var_20) as var_20_count,
                COUNT(var_50) as var_50_count
            FROM advanced_technical_indicators
        """)).fetchone()
        
        logger.info(f"   📊 Indicateurs de volatilité:")
        logger.info(f"      ATR 14: {volatility_stats[0]:,} ({volatility_stats[0]/general_stats[0]*100:.1f}%)")
        logger.info(f"      ATR 20: {volatility_stats[1]:,} ({volatility_stats[1]/general_stats[0]*100:.1f}%)")
        logger.info(f"      StdDev 20: {volatility_stats[2]:,} ({volatility_stats[2]/general_stats[0]*100:.1f}%)")
        logger.info(f"      StdDev 50: {volatility_stats[3]:,} ({volatility_stats[3]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Variance 20: {volatility_stats[4]:,} ({volatility_stats[4]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Variance 50: {volatility_stats[5]:,} ({volatility_stats[5]/general_stats[0]*100:.1f}%)")
        
        # Indicateurs de volume
        volume_stats = db.execute(text("""
            SELECT 
                COUNT(obv) as obv_count,
                COUNT(ad) as ad_count,
                COUNT(adosc) as adosc_count,
                COUNT(mfi_14) as mfi_14_count,
                COUNT(vpt) as vpt_count,
                COUNT(wad) as wad_count
            FROM advanced_technical_indicators
        """)).fetchone()
        
        logger.info(f"   📈 Indicateurs de volume:")
        logger.info(f"      OBV: {volume_stats[0]:,} ({volume_stats[0]/general_stats[0]*100:.1f}%)")
        logger.info(f"      AD: {volume_stats[1]:,} ({volume_stats[1]/general_stats[0]*100:.1f}%)")
        logger.info(f"      ADOSC: {volume_stats[2]:,} ({volume_stats[2]/general_stats[0]*100:.1f}%)")
        logger.info(f"      MFI 14: {volume_stats[3]:,} ({volume_stats[3]/general_stats[0]*100:.1f}%)")
        logger.info(f"      VPT: {volume_stats[4]:,} ({volume_stats[4]/general_stats[0]*100:.1f}%)")
        logger.info(f"      WAD: {volume_stats[5]:,} ({volume_stats[5]/general_stats[0]*100:.1f}%)")
        
        # Indicateurs composites
        composite_stats = db.execute(text("""
            SELECT 
                COUNT(momentum_composite) as momentum_composite_count,
                COUNT(volatility_composite) as volatility_composite_count,
                COUNT(trend_strength) as trend_strength_count,
                COUNT(sma_ratio_20_50) as sma_ratio_count,
                COUNT(ema_ratio_20_50) as ema_ratio_count
            FROM advanced_technical_indicators
        """)).fetchone()
        
        logger.info(f"   🎯 Indicateurs composites:")
        logger.info(f"      Momentum Composite: {composite_stats[0]:,} ({composite_stats[0]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Volatility Composite: {composite_stats[1]:,} ({composite_stats[1]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Trend Strength: {composite_stats[2]:,} ({composite_stats[2]/general_stats[0]*100:.1f}%)")
        logger.info(f"      SMA Ratio 20/50: {composite_stats[3]:,} ({composite_stats[3]/general_stats[0]*100:.1f}%)")
        logger.info(f"      EMA Ratio 20/50: {composite_stats[4]:,} ({composite_stats[4]/general_stats[0]*100:.1f}%)")
        
        # Patterns de chandeliers
        pattern_stats = db.execute(text("""
            SELECT 
                COUNT(cdl_doji) as cdl_doji_count,
                COUNT(cdl_hammer) as cdl_hammer_count,
                COUNT(cdl_hangingman) as cdl_hangingman_count,
                COUNT(cdl_engulfing) as cdl_engulfing_count,
                COUNT(cdl_morningstar) as cdl_morningstar_count,
                COUNT(cdl_eveningstar) as cdl_eveningstar_count
            FROM advanced_technical_indicators
        """)).fetchone()
        
        logger.info(f"   🕯️ Patterns de chandeliers:")
        logger.info(f"      Doji: {pattern_stats[0]:,} ({pattern_stats[0]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Hammer: {pattern_stats[1]:,} ({pattern_stats[1]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Hanging Man: {pattern_stats[2]:,} ({pattern_stats[2]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Engulfing: {pattern_stats[3]:,} ({pattern_stats[3]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Morning Star: {pattern_stats[4]:,} ({pattern_stats[4]/general_stats[0]*100:.1f}%)")
        logger.info(f"      Evening Star: {pattern_stats[5]:,} ({pattern_stats[5]/general_stats[0]*100:.1f}%)")
        
        # 3. Analyse des colonnes complètement vides
        logger.info("\n❌ COLONNES COMPLÈTEMENT VIDES")
        
        empty_columns_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'advanced_technical_indicators' 
        AND column_name NOT IN ('id', 'symbol', 'date', 'created_at', 'updated_at')
        ORDER BY column_name
        """
        
        columns = db.execute(text(empty_columns_query)).fetchall()
        empty_columns = []
        
        for col in columns:
            col_name = col[0]
            count_query = f"SELECT COUNT({col_name}) FROM advanced_technical_indicators"
            count = db.execute(text(count_query)).scalar()
            
            if count == 0:
                empty_columns.append(col_name)
                logger.info(f"   ❌ {col_name}: 0 enregistrements")
        
        if not empty_columns:
            logger.info("   ✅ Aucune colonne complètement vide")
        
        # 4. Analyse par symbole
        logger.info("\n📊 ANALYSE PAR SYMBOLE")
        
        symbol_stats = db.execute(text("""
            SELECT 
                symbol,
                COUNT(*) as total_records,
                COUNT(close) as close_count,
                COUNT(rsi_14) as rsi_count,
                COUNT(macd) as macd_count,
                COUNT(bb_position) as bb_position_count,
                MIN(date) as earliest_date,
                MAX(date) as latest_date
            FROM advanced_technical_indicators
            GROUP BY symbol
            ORDER BY total_records DESC
            LIMIT 10
        """)).fetchall()
        
        logger.info("   Top 10 symboles par nombre d'enregistrements:")
        for stat in symbol_stats:
            logger.info(f"      {stat[0]}: {stat[1]:,} enregistrements ({stat[2]:,} close, {stat[3]:,} RSI, {stat[4]:,} MACD, {stat[5]:,} BB)")
            logger.info(f"         Période: {stat[6]} → {stat[7]}")
        
        # 5. Recommandations
        logger.info("\n💡 RECOMMANDATIONS")
        
        # Calculer le pourcentage moyen de remplissage
        all_columns_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'advanced_technical_indicators' 
        AND column_name NOT IN ('id', 'symbol', 'date', 'created_at', 'updated_at')
        AND data_type IN ('numeric', 'bigint', 'integer')
        ORDER BY column_name
        """
        
        all_columns = db.execute(text(all_columns_query)).fetchall()
        total_fill_rate = 0
        filled_columns = 0
        
        for col in all_columns:
            col_name = col[0]
            count_query = f"SELECT COUNT({col_name}) FROM advanced_technical_indicators"
            count = db.execute(text(count_query)).scalar()
            fill_rate = count / general_stats[0] * 100
            total_fill_rate += fill_rate
            filled_columns += 1
        
        avg_fill_rate = total_fill_rate / filled_columns if filled_columns > 0 else 0
        
        logger.info(f"   📊 Taux de remplissage moyen: {avg_fill_rate:.1f}%")
        
        if avg_fill_rate < 50:
            logger.info("   ⚠️ Taux de remplissage faible - Recommandation: Recalculer tous les indicateurs")
        elif avg_fill_rate < 80:
            logger.info("   ⚠️ Taux de remplissage moyen - Recommandation: Compléter les indicateurs manquants")
        else:
            logger.info("   ✅ Taux de remplissage bon - Qualité des données acceptable")
        
        if empty_columns:
            logger.info(f"   🔧 Action requise: Calculer {len(empty_columns)} indicateurs manquants")
        
        logger.info("\n🎉 Analyse de qualité des données terminée!")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    analyze_data_quality()
