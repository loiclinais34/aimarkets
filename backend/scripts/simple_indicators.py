#!/usr/bin/env python3
"""
Script simple pour calculer les indicateurs techniques
Version optimisée pour éviter les boucles infinies
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings

def calculate_indicators_simple(symbol: str, limit: int = 100):
    """Calculer les indicateurs techniques de manière simple et efficace"""
    
    # Connexion directe à PostgreSQL
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='aimarkets',
        user='loiclinais',
        password='MonCoeur1703@'
    )
    
    try:
        # Récupérer les données historiques
        query = """
        SELECT date, open, high, low, close, volume, vwap
        FROM historical_data 
        WHERE symbol = %s 
        ORDER BY date 
        LIMIT %s
        """
        
        df = pd.read_sql(query, conn, params=[symbol, limit])
        
        if df.empty:
            print(f"Aucune donnée trouvée pour {symbol}")
            return
        
        print(f"📊 Calcul des indicateurs pour {symbol} ({len(df)} enregistrements)")
        
        # Calculer les indicateurs de base
        df['sma_5'] = df['close'].rolling(window=5).mean()
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['ema_5'] = df['close'].ewm(span=5).mean()
        df['ema_20'] = df['close'].ewm(span=20).mean()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = df['close'].ewm(span=12).mean()
        ema_26 = df['close'].ewm(span=26).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Bollinger Bands
        sma_20 = df['close'].rolling(window=20).mean()
        std_20 = df['close'].rolling(window=20).std()
        df['bb_upper'] = sma_20 + (std_20 * 2)
        df['bb_middle'] = sma_20
        df['bb_lower'] = sma_20 - (std_20 * 2)
        
        # Volume indicators
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        
        # ATR
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr_14'] = df['tr'].rolling(window=14).mean()
        
        # Nettoyer les données
        df = df.dropna()
        df = df.drop('tr', axis=1)  # Supprimer la colonne temporaire
        
        if df.empty:
            print(f"Aucune donnée valide après calcul pour {symbol}")
            return
        
        # Préparer les données pour l'insertion
        data_to_insert = []
        for _, row in df.iterrows():
            data_to_insert.append((
                symbol,
                row['date'],
                row.get('sma_5'),
                row.get('sma_20'),
                row.get('ema_5'),
                row.get('ema_20'),
                row.get('rsi_14'),
                row.get('macd'),
                row.get('macd_signal'),
                row.get('macd_histogram'),
                row.get('bb_upper'),
                row.get('bb_middle'),
                row.get('bb_lower'),
                row.get('volume_sma_20'),
                row.get('atr_14')
            ))
        
        # Insérer les données
        insert_query = """
        INSERT INTO technical_indicators 
        (symbol, date, sma_5, sma_20, ema_5, ema_20, rsi_14, macd, macd_signal, macd_histogram, 
         bb_upper, bb_middle, bb_lower, volume_sma_20, atr_14)
        VALUES %s
        ON CONFLICT (symbol, date) DO UPDATE SET
            sma_5 = EXCLUDED.sma_5,
            sma_20 = EXCLUDED.sma_20,
            ema_5 = EXCLUDED.ema_5,
            ema_20 = EXCLUDED.ema_20,
            rsi_14 = EXCLUDED.rsi_14,
            macd = EXCLUDED.macd,
            macd_signal = EXCLUDED.macd_signal,
            macd_histogram = EXCLUDED.macd_histogram,
            bb_upper = EXCLUDED.bb_upper,
            bb_middle = EXCLUDED.bb_middle,
            bb_lower = EXCLUDED.bb_lower,
            volume_sma_20 = EXCLUDED.volume_sma_20,
            atr_14 = EXCLUDED.atr_14
        """
        
        cursor = conn.cursor()
        execute_values(cursor, insert_query, data_to_insert)
        conn.commit()
        
        print(f"✅ {len(data_to_insert)} indicateurs calculés et sauvegardés pour {symbol}")
        
    except Exception as e:
        print(f"❌ Erreur pour {symbol}: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def main():
    """Fonction principale"""
    if len(sys.argv) != 2:
        print("Usage: python3 simple_indicators.py <SYMBOL>")
        sys.exit(1)
    
    symbol = sys.argv[1].upper()
    calculate_indicators_simple(symbol)

if __name__ == "__main__":
    main()
