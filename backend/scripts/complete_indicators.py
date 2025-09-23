#!/usr/bin/env python3
"""
Script complet pour calculer TOUS les indicateurs techniques
Version complète avec tous les indicateurs manquants
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

def calculate_complete_indicators(symbols: list, limit_per_symbol: int = 200):
    """Calculer TOUS les indicateurs techniques pour plusieurs symboles"""
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='aimarkets',
        user='loiclinais',
        password='MonCoeur1703@'
    )
    
    total_processed = 0
    total_errors = 0
    
    print(f"🔄 Traitement de {len(symbols)} symboles avec TOUS les indicateurs...")
    
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
            
            print(f"   📈 {len(df)} enregistrements à traiter")
            
            # === MOYENNES MOBILES ===
            print("   🔄 Calcul des moyennes mobiles...")
            df['sma_5'] = df['close'].rolling(window=5).mean()
            df['sma_10'] = df['close'].rolling(window=10).mean()
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['sma_200'] = df['close'].rolling(window=200).mean()
            
            df['ema_5'] = df['close'].ewm(span=5).mean()
            df['ema_10'] = df['close'].ewm(span=10).mean()
            df['ema_20'] = df['close'].ewm(span=20).mean()
            df['ema_50'] = df['close'].ewm(span=50).mean()
            df['ema_200'] = df['close'].ewm(span=200).mean()
            
            # === INDICATEURS DE MOMENTUM ===
            print("   🔄 Calcul des indicateurs de momentum...")
            
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
            
            # Stochastic Oscillator
            lowest_low = df['low'].rolling(window=14).min()
            highest_high = df['high'].rolling(window=14).max()
            df['stochastic_k'] = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
            df['stochastic_d'] = df['stochastic_k'].rolling(window=3).mean()
            
            # Williams %R
            df['williams_r'] = -100 * ((highest_high - df['close']) / (highest_high - lowest_low))
            
            # Rate of Change (ROC)
            df['roc'] = ((df['close'] - df['close'].shift(10)) / df['close'].shift(10)) * 100
            
            # Commodity Channel Index (CCI)
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            sma_tp = typical_price.rolling(window=20).mean()
            mad = typical_price.rolling(window=20).apply(lambda x: np.mean(np.abs(x - x.mean())))
            df['cci'] = (typical_price - sma_tp) / (0.015 * mad)
            
            # === BOLLINGER BANDS ===
            print("   🔄 Calcul des Bollinger Bands...")
            sma_20 = df['close'].rolling(window=20).mean()
            std_20 = df['close'].rolling(window=20).std()
            df['bb_upper'] = sma_20 + (std_20 * 2)
            df['bb_middle'] = sma_20
            df['bb_lower'] = sma_20 - (std_20 * 2)
            df['bb_width'] = df['bb_upper'] - df['bb_lower']
            df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # === INDICATEURS DE VOLUME ===
            print("   🔄 Calcul des indicateurs de volume...")
            
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
            df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
            
            # === ATR ===
            print("   🔄 Calcul de l'ATR...")
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
            
            print(f"   ✅ {len(df)} enregistrements valides après calcul")
            
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
            
            # Insérer les données
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
            
            print(f"   ✅ {len(data_to_insert)} indicateurs complets calculés et sauvegardés")
            total_processed += len(data_to_insert)
            
        except Exception as e:
            print(f"   ❌ Erreur pour {symbol}: {e}")
            total_errors += 1
            conn.rollback()
    
    print(f"\n📊 Résumé du traitement complet:")
    print(f"   Symboles traités: {len(symbols)}")
    print(f"   Indicateurs calculés: {total_processed}")
    print(f"   Erreurs: {total_errors}")
    
    conn.close()

def main():
    """Fonction principale"""
    if len(sys.argv) > 1:
        limit = int(sys.argv[1])
    else:
        limit = 5
    
    symbols = get_symbols(limit)
    if not symbols:
        print("Aucun symbole trouvé")
        return
    
    print(f"Symboles à traiter: {', '.join(symbols)}")
    
    start_time = time.time()
    calculate_complete_indicators(symbols)
    end_time = time.time()
    
    print(f"\n⏱️ Temps total: {end_time - start_time:.2f} secondes")

if __name__ == "__main__":
    main()
