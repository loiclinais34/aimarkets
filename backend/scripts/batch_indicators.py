#!/usr/bin/env python3
"""
Script pour calculer les indicateurs techniques en batch
Traite plusieurs symboles de manière efficace
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, date
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_values
import time

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings

def get_symbols(limit: int = 10):
    """Récupérer la liste des symboles"""
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='aimarkets',
        user='loiclinais',
        password='MonCoeur1703@'
    )
    
    try:
        query = """
        SELECT DISTINCT symbol 
        FROM historical_data 
        ORDER BY symbol 
        LIMIT %s
        """
        
        cursor = conn.cursor()
        cursor.execute(query, (limit,))
        symbols = [row[0] for row in cursor.fetchall()]
        
        return symbols
    
    finally:
        conn.close()

def calculate_indicators_batch(symbols: list, limit_per_symbol: int = 100):
    """Calculer les indicateurs pour plusieurs symboles"""
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='aimarkets',
        user='loiclinais',
        password='MonCoeur1703@'
    )
    
    total_processed = 0
    total_errors = 0
    
    print(f"🔄 Traitement de {len(symbols)} symboles...")
    
    for i, symbol in enumerate(symbols, 1):
        try:
            print(f"\n📊 [{i}/{len(symbols)}] Traitement de {symbol}...")
            
            # Récupérer les données historiques
            query = """
            SELECT date, open, high, low, close, volume, vwap
            FROM historical_data 
            WHERE symbol = %s 
            ORDER BY date DESC
            LIMIT %s
            """
            
            df = pd.read_sql(query, conn, params=[symbol, limit_per_symbol])
            
            if df.empty:
                print(f"   ⚠️ Aucune donnée trouvée pour {symbol}")
                continue
            
            # Trier par date croissante pour les calculs
            df = df.sort_values('date').reset_index(drop=True)
            
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
                print(f"   ⚠️ Aucune donnée valide après calcul pour {symbol}")
                continue
            
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
            
            print(f"   ✅ {len(data_to_insert)} indicateurs calculés et sauvegardés")
            total_processed += len(data_to_insert)
            
        except Exception as e:
            print(f"   ❌ Erreur pour {symbol}: {e}")
            total_errors += 1
            conn.rollback()
    
    print(f"\n📊 Résumé du traitement:")
    print(f"   Symboles traités: {len(symbols)}")
    print(f"   Indicateurs calculés: {total_processed}")
    print(f"   Erreurs: {total_errors}")
    
    conn.close()

def main():
    """Fonction principale"""
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
    else:
        limit = 10
    
    symbols = get_symbols(limit)
    if not symbols:
        print("Aucun symbole trouvé")
        return
    
    print(f"Symboles à traiter: {', '.join(symbols)}")
    
    start_time = time.time()
    calculate_indicators_batch(symbols)
    end_time = time.time()
    
    print(f"\n⏱️ Temps total: {end_time - start_time:.2f} secondes")

if __name__ == "__main__":
    main()
