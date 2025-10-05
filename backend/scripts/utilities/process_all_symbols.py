#!/usr/bin/env python3
"""
Script pour traiter TOUS les symboles et calculer les indicateurs techniques
Version optimisée pour traiter l'ensemble du dataset
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
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings

# Lock pour les opérations de base de données
db_lock = threading.Lock()

def get_all_symbols():
    """Récupérer TOUS les symboles disponibles"""
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
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        symbols = [row[0] for row in cursor.fetchall()]
        
        return symbols
    
    finally:
        conn.close()

def calculate_indicators_for_symbol(symbol: str, limit_per_symbol: int = 500):
    """Calculer TOUS les indicateurs techniques pour un symbole"""
    
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
        ORDER BY date DESC
        LIMIT %s
        """
        
        df = pd.read_sql(query, conn, params=[symbol, limit_per_symbol])
        
        if df.empty:
            return symbol, 0, f"Aucune donnée trouvée"
        
        # Trier par date croissante pour les calculs
        df = df.sort_values('date').reset_index(drop=True)
        
        # === MOYENNES MOBILES ===
        df['sma_5'] = df['close'].rolling(window=5, min_periods=1).mean()
        df['sma_10'] = df['close'].rolling(window=10, min_periods=1).mean()
        df['sma_20'] = df['close'].rolling(window=20, min_periods=1).mean()
        df['sma_50'] = df['close'].rolling(window=50, min_periods=1).mean()
        df['sma_200'] = df['close'].rolling(window=200, min_periods=1).mean()
        
        df['ema_5'] = df['close'].ewm(span=5, min_periods=1).mean()
        df['ema_10'] = df['close'].ewm(span=10, min_periods=1).mean()
        df['ema_20'] = df['close'].ewm(span=20, min_periods=1).mean()
        df['ema_50'] = df['close'].ewm(span=50, min_periods=1).mean()
        df['ema_200'] = df['close'].ewm(span=200, min_periods=1).mean()
        
        # === INDICATEURS DE MOMENTUM ===
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_12 = df['close'].ewm(span=12, min_periods=1).mean()
        ema_26 = df['close'].ewm(span=26, min_periods=1).mean()
        df['macd'] = ema_12 - ema_26
        df['macd_signal'] = df['macd'].ewm(span=9, min_periods=1).mean()
        df['macd_histogram'] = df['macd'] - df['macd_signal']
        
        # Stochastic Oscillator
        lowest_low = df['low'].rolling(window=14, min_periods=1).min()
        highest_high = df['high'].rolling(window=14, min_periods=1).max()
        df['stochastic_k'] = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
        df['stochastic_d'] = df['stochastic_k'].rolling(window=3, min_periods=1).mean()
        
        # Williams %R
        df['williams_r'] = -100 * ((highest_high - df['close']) / (highest_high - lowest_low))
        
        # Rate of Change (ROC)
        df['roc'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
        
        # Commodity Channel Index (CCI)
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = typical_price.rolling(window=20, min_periods=1).mean()
        mad = typical_price.rolling(window=20, min_periods=1).apply(lambda x: np.mean(np.abs(x - x.mean())))
        df['cci'] = (typical_price - sma_tp) / (0.015 * mad)
        
        # === BOLLINGER BANDS ===
        sma_20 = df['close'].rolling(window=20, min_periods=1).mean()
        std_20 = df['close'].rolling(window=20, min_periods=1).std()
        df['bb_upper'] = sma_20 + (std_20 * 2)
        df['bb_middle'] = sma_20
        df['bb_lower'] = sma_20 - (std_20 * 2)
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # === INDICATEURS DE VOLUME ===
        # On-Balance Volume (OBV)
        obv = np.zeros(len(df))
        obv[0] = df['volume'].iloc[0]
        
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv[i] = obv[i-1] + df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv[i] = obv[i-1] - df['volume'].iloc[i]
            else:
                obv[i] = obv[i-1]
        
        df['obv'] = obv
        
        # Volume Rate of Change
        df['volume_roc'] = ((df['volume'] - df['volume'].shift(10)) / df['volume'].shift(10)) * 100
        
        # Volume Moving Average
        df['volume_sma_20'] = df['volume'].rolling(window=20, min_periods=1).mean()
        
        # === ATR ===
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr_14'] = df['tr'].rolling(window=14, min_periods=1).mean()
        
        # Nettoyer les données
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.drop('tr', axis=1)
        
        # Préparer les données pour l'insertion
        data_to_insert = []
        for _, row in df.iterrows():
            data_to_insert.append((
                symbol,
                row['date'],
                # Moyennes mobiles
                row.get('sma_5'),
                row.get('sma_10'),
                row.get('sma_20'),
                row.get('sma_50'),
                row.get('sma_200'),
                # Moyennes mobiles exponentielles
                row.get('ema_5'),
                row.get('ema_10'),
                row.get('ema_20'),
                row.get('ema_50'),
                row.get('ema_200'),
                # Indicateurs de momentum
                row.get('rsi_14'),
                row.get('macd'),
                row.get('macd_signal'),
                row.get('macd_histogram'),
                row.get('stochastic_k'),
                row.get('stochastic_d'),
                row.get('williams_r'),
                row.get('roc'),
                row.get('cci'),
                # Bollinger Bands
                row.get('bb_upper'),
                row.get('bb_middle'),
                row.get('bb_lower'),
                row.get('bb_width'),
                row.get('bb_position'),
                # Volume
                row.get('obv'),
                row.get('volume_roc'),
                row.get('volume_sma_20'),
                # ATR
                row.get('atr_14')
            ))
        
        # Insérer les données avec lock pour éviter les conflits
        with db_lock:
            insert_query = """
            INSERT INTO technical_indicators 
            (symbol, date, sma_5, sma_10, sma_20, sma_50, sma_200, 
             ema_5, ema_10, ema_20, ema_50, ema_200,
             rsi_14, macd, macd_signal, macd_histogram, 
             stochastic_k, stochastic_d, williams_r, roc, cci,
             bb_upper, bb_middle, bb_lower, bb_width, bb_position,
             obv, volume_roc, volume_sma_20, atr_14)
            VALUES %s
            ON CONFLICT (symbol, date) DO UPDATE SET
                sma_5 = EXCLUDED.sma_5,
                sma_10 = EXCLUDED.sma_10,
                sma_20 = EXCLUDED.sma_20,
                sma_50 = EXCLUDED.sma_50,
                sma_200 = EXCLUDED.sma_200,
                ema_5 = EXCLUDED.ema_5,
                ema_10 = EXCLUDED.ema_10,
                ema_20 = EXCLUDED.ema_20,
                ema_50 = EXCLUDED.ema_50,
                ema_200 = EXCLUDED.ema_200,
                rsi_14 = EXCLUDED.rsi_14,
                macd = EXCLUDED.macd,
                macd_signal = EXCLUDED.macd_signal,
                macd_histogram = EXCLUDED.macd_histogram,
                stochastic_k = EXCLUDED.stochastic_k,
                stochastic_d = EXCLUDED.stochastic_d,
                williams_r = EXCLUDED.williams_r,
                roc = EXCLUDED.roc,
                cci = EXCLUDED.cci,
                bb_upper = EXCLUDED.bb_upper,
                bb_middle = EXCLUDED.bb_middle,
                bb_lower = EXCLUDED.bb_lower,
                bb_width = EXCLUDED.bb_width,
                bb_position = EXCLUDED.bb_position,
                obv = EXCLUDED.obv,
                volume_roc = EXCLUDED.volume_roc,
                volume_sma_20 = EXCLUDED.volume_sma_20,
                atr_14 = EXCLUDED.atr_14
            """
            
            cursor = conn.cursor()
            execute_values(cursor, insert_query, data_to_insert)
            conn.commit()
        
        return symbol, len(data_to_insert), "Succès"
        
    except Exception as e:
        return symbol, 0, f"Erreur: {e}"
    
    finally:
        conn.close()

def process_symbols_batch(symbols: list, batch_size: int = 10):
    """Traiter les symboles par batch avec parallélisation"""
    
    total_processed = 0
    total_errors = 0
    results = []
    
    print(f"🔄 Traitement de {len(symbols)} symboles par batch de {batch_size}...")
    
    # Traiter par batch
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(symbols) + batch_size - 1) // batch_size
        
        print(f"\n📊 Batch {batch_num}/{total_batches}: {', '.join(batch)}")
        
        # Traitement parallèle du batch
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            future_to_symbol = {
                executor.submit(calculate_indicators_for_symbol, symbol): symbol 
                for symbol in batch
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result_symbol, count, status = future.result()
                    results.append((result_symbol, count, status))
                    
                    if count > 0:
                        print(f"   ✅ {result_symbol}: {count} indicateurs calculés")
                        total_processed += count
                    else:
                        print(f"   ❌ {result_symbol}: {status}")
                        total_errors += 1
                        
                except Exception as e:
                    print(f"   ❌ {symbol}: Erreur inattendue: {e}")
                    total_errors += 1
    
    return results, total_processed, total_errors

def main():
    """Fonction principale"""
    print("🚀 Démarrage du traitement de TOUS les symboles...")
    
    # Récupérer tous les symboles
    symbols = get_all_symbols()
    if not symbols:
        print("❌ Aucun symbole trouvé")
        return
    
    print(f"📈 {len(symbols)} symboles à traiter")
    
    start_time = time.time()
    
    # Traiter par batch
    results, total_processed, total_errors = process_symbols_batch(symbols, batch_size=5)
    
    end_time = time.time()
    
    # Résumé final
    print(f"\n📊 Résumé final:")
    print(f"   Symboles traités: {len(symbols)}")
    print(f"   Indicateurs calculés: {total_processed}")
    print(f"   Erreurs: {total_errors}")
    print(f"   Temps total: {end_time - start_time:.2f} secondes")
    print(f"   Temps moyen par symbole: {(end_time - start_time) / len(symbols):.2f} secondes")
    
    # Statistiques par symbole
    print(f"\n📈 Statistiques par symbole:")
    for symbol, count, status in results:
        if count > 0:
            print(f"   ✅ {symbol}: {count} indicateurs")
        else:
            print(f"   ❌ {symbol}: {status}")

if __name__ == "__main__":
    main()
