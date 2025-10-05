#!/usr/bin/env python3
"""
Script pour calculer et stocker les indicateurs de sentiment
Développe des indicateurs avancés basés sur les données de sentiment existantes
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
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
        FROM sentiment_data 
        ORDER BY symbol
        """
        
        cursor = conn.cursor()
        cursor.execute(query)
        symbols = [row[0] for row in cursor.fetchall()]
        
        return symbols
    
    finally:
        conn.close()

def calculate_sentiment_indicators_for_symbol(symbol: str, limit_per_symbol: int = 500):
    """Calculer les indicateurs de sentiment avancés pour un symbole"""
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='aimarkets',
        user='loiclinais',
        password='MonCoeur1703@'
    )
    
    try:
        # Récupérer les données de sentiment
        query = """
        SELECT date, news_count, news_sentiment_score, news_sentiment_std,
               news_positive_count, news_negative_count, news_neutral_count,
               top_news_sentiment, short_interest_ratio, short_volume_ratio,
               sentiment_momentum_5d, sentiment_momentum_20d, sentiment_volatility_5d,
               sentiment_relative_strength, data_quality_score
        FROM sentiment_data 
        WHERE symbol = %s 
        ORDER BY date DESC
        LIMIT %s
        """
        
        df = pd.read_sql(query, conn, params=[symbol, limit_per_symbol])
        
        if df.empty:
            return symbol, 0, f"Aucune donnée de sentiment trouvée"
        
        # Trier par date croissante pour les calculs
        df = df.sort_values('date').reset_index(drop=True)
        
        # === INDICATEURS DE SENTIMENT DE BASE ===
        print(f"   🔄 Calcul des indicateurs de sentiment pour {symbol}...")
        
        # 1. Sentiment Score Normalisé (0-100)
        df['sentiment_score_normalized'] = ((df['news_sentiment_score'] + 1) / 2) * 100
        
        # 2. Sentiment Momentum (différence sur différentes périodes)
        df['sentiment_momentum_1d'] = df['news_sentiment_score'].diff(1)
        df['sentiment_momentum_3d'] = df['news_sentiment_score'].diff(3)
        df['sentiment_momentum_7d'] = df['news_sentiment_score'].diff(7)
        df['sentiment_momentum_14d'] = df['news_sentiment_score'].diff(14)
        
        # 3. Sentiment Volatility (écart-type mobile)
        df['sentiment_volatility_3d'] = df['news_sentiment_score'].rolling(window=3, min_periods=1).std()
        df['sentiment_volatility_7d'] = df['news_sentiment_score'].rolling(window=7, min_periods=1).std()
        df['sentiment_volatility_14d'] = df['news_sentiment_score'].rolling(window=14, min_periods=1).std()
        df['sentiment_volatility_30d'] = df['news_sentiment_score'].rolling(window=30, min_periods=1).std()
        
        # 4. Sentiment Moving Averages
        df['sentiment_sma_3'] = df['news_sentiment_score'].rolling(window=3, min_periods=1).mean()
        df['sentiment_sma_7'] = df['news_sentiment_score'].rolling(window=7, min_periods=1).mean()
        df['sentiment_sma_14'] = df['news_sentiment_score'].rolling(window=14, min_periods=1).mean()
        df['sentiment_sma_30'] = df['news_sentiment_score'].rolling(window=30, min_periods=1).mean()
        
        df['sentiment_ema_3'] = df['news_sentiment_score'].ewm(span=3, min_periods=1).mean()
        df['sentiment_ema_7'] = df['news_sentiment_score'].ewm(span=7, min_periods=1).mean()
        df['sentiment_ema_14'] = df['news_sentiment_score'].ewm(span=14, min_periods=1).mean()
        df['sentiment_ema_30'] = df['news_sentiment_score'].ewm(span=30, min_periods=1).mean()
        
        # 5. Sentiment RSI (Relative Strength Index)
        delta = df['news_sentiment_score'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
        rs = gain / loss
        df['sentiment_rsi_14'] = 100 - (100 / (1 + rs))
        
        # 6. Sentiment MACD
        ema_12 = df['news_sentiment_score'].ewm(span=12, min_periods=1).mean()
        ema_26 = df['news_sentiment_score'].ewm(span=26, min_periods=1).mean()
        df['sentiment_macd'] = ema_12 - ema_26
        df['sentiment_macd_signal'] = df['sentiment_macd'].ewm(span=9, min_periods=1).mean()
        df['sentiment_macd_histogram'] = df['sentiment_macd'] - df['sentiment_macd_signal']
        
        # === INDICATEURS DE VOLUME DE SENTIMENT ===
        # 7. News Volume Indicators
        df['news_volume_sma_7'] = df['news_count'].rolling(window=7, min_periods=1).mean()
        df['news_volume_sma_14'] = df['news_count'].rolling(window=14, min_periods=1).mean()
        df['news_volume_sma_30'] = df['news_count'].rolling(window=30, min_periods=1).mean()
        
        df['news_volume_roc_7d'] = ((df['news_count'] - df['news_count'].shift(7)) / df['news_count'].shift(7)) * 100
        df['news_volume_roc_14d'] = ((df['news_count'] - df['news_count'].shift(14)) / df['news_count'].shift(14)) * 100
        
        # 8. News Sentiment Distribution
        df['news_positive_ratio'] = df['news_positive_count'] / (df['news_positive_count'] + df['news_negative_count'] + df['news_neutral_count'])
        df['news_negative_ratio'] = df['news_negative_count'] / (df['news_positive_count'] + df['news_negative_count'] + df['news_neutral_count'])
        df['news_neutral_ratio'] = df['news_neutral_count'] / (df['news_positive_count'] + df['news_negative_count'] + df['news_neutral_count'])
        
        # 9. News Sentiment Quality Score
        df['news_sentiment_quality'] = df['news_count'] * (1 - df['news_sentiment_std'])
        
        # === INDICATEURS DE SHORT INTEREST ===
        # 10. Short Interest Momentum
        df['short_interest_momentum_5d'] = df['short_interest_ratio'].diff(5)
        df['short_interest_momentum_10d'] = df['short_interest_ratio'].diff(10)
        df['short_interest_momentum_20d'] = df['short_interest_ratio'].diff(20)
        
        # 11. Short Interest Volatility
        df['short_interest_volatility_7d'] = df['short_interest_ratio'].rolling(window=7, min_periods=1).std()
        df['short_interest_volatility_14d'] = df['short_interest_ratio'].rolling(window=14, min_periods=1).std()
        df['short_interest_volatility_30d'] = df['short_interest_ratio'].rolling(window=30, min_periods=1).std()
        
        # 12. Short Interest Moving Averages
        df['short_interest_sma_7'] = df['short_interest_ratio'].rolling(window=7, min_periods=1).mean()
        df['short_interest_sma_14'] = df['short_interest_ratio'].rolling(window=14, min_periods=1).mean()
        df['short_interest_sma_30'] = df['short_interest_ratio'].rolling(window=30, min_periods=1).mean()
        
        # 13. Short Volume Indicators
        df['short_volume_momentum_5d'] = df['short_volume_ratio'].diff(5)
        df['short_volume_momentum_10d'] = df['short_volume_ratio'].diff(10)
        df['short_volume_momentum_20d'] = df['short_volume_ratio'].diff(20)
        
        df['short_volume_volatility_7d'] = df['short_volume_ratio'].rolling(window=7, min_periods=1).std()
        df['short_volume_volatility_14d'] = df['short_volume_ratio'].rolling(window=14, min_periods=1).std()
        df['short_volume_volatility_30d'] = df['short_volume_ratio'].rolling(window=30, min_periods=1).std()
        
        # === INDICATEURS COMPOSITES ===
        # 14. Sentiment Strength Index (combinaison de plusieurs facteurs)
        df['sentiment_strength_index'] = (
            df['sentiment_score_normalized'] * 0.4 +
            df['news_positive_ratio'] * 100 * 0.3 +
            (1 - df['news_negative_ratio']) * 100 * 0.3
        )
        
        # 15. Market Sentiment Index (combinaison news + short interest)
        df['market_sentiment_index'] = (
            df['sentiment_score_normalized'] * 0.6 +
            (1 - df['short_interest_ratio'] / 10) * 100 * 0.4  # Normaliser short interest
        )
        
        # 16. Sentiment Divergence (différence entre sentiment et momentum)
        df['sentiment_divergence'] = df['news_sentiment_score'] - df['sentiment_momentum_5d']
        
        # 17. Sentiment Acceleration (dérivée seconde du sentiment)
        df['sentiment_acceleration'] = df['sentiment_momentum_1d'].diff(1)
        
        # 18. Sentiment Trend Strength
        df['sentiment_trend_strength'] = abs(df['sentiment_momentum_7d']) / df['sentiment_volatility_7d']
        
        # 19. Sentiment Quality Index
        df['sentiment_quality_index'] = (
            df['data_quality_score'] * 0.4 +
            (1 - df['news_sentiment_std']) * 0.3 +
            (df['news_count'] / df['news_count'].rolling(window=30, min_periods=1).mean()) * 0.3
        )
        
        # 20. Sentiment Risk Score
        df['sentiment_risk_score'] = (
            df['sentiment_volatility_14d'] * 0.4 +
            df['short_interest_ratio'] * 0.3 +
            df['news_negative_ratio'] * 0.3
        )
        
        # Nettoyer les données
        df = df.replace([np.inf, -np.inf], np.nan)
        
        # Préparer les données pour l'insertion
        data_to_insert = []
        for _, row in df.iterrows():
            data_to_insert.append((
                symbol,
                row['date'],
                # Indicateurs de sentiment de base
                row.get('sentiment_score_normalized'),
                row.get('sentiment_momentum_1d'),
                row.get('sentiment_momentum_3d'),
                row.get('sentiment_momentum_7d'),
                row.get('sentiment_momentum_14d'),
                # Volatilité du sentiment
                row.get('sentiment_volatility_3d'),
                row.get('sentiment_volatility_7d'),
                row.get('sentiment_volatility_14d'),
                row.get('sentiment_volatility_30d'),
                # Moyennes mobiles du sentiment
                row.get('sentiment_sma_3'),
                row.get('sentiment_sma_7'),
                row.get('sentiment_sma_14'),
                row.get('sentiment_sma_30'),
                row.get('sentiment_ema_3'),
                row.get('sentiment_ema_7'),
                row.get('sentiment_ema_14'),
                row.get('sentiment_ema_30'),
                # RSI et MACD du sentiment
                row.get('sentiment_rsi_14'),
                row.get('sentiment_macd'),
                row.get('sentiment_macd_signal'),
                row.get('sentiment_macd_histogram'),
                # Indicateurs de volume de news
                row.get('news_volume_sma_7'),
                row.get('news_volume_sma_14'),
                row.get('news_volume_sma_30'),
                row.get('news_volume_roc_7d'),
                row.get('news_volume_roc_14d'),
                # Distribution du sentiment
                row.get('news_positive_ratio'),
                row.get('news_negative_ratio'),
                row.get('news_neutral_ratio'),
                row.get('news_sentiment_quality'),
                # Indicateurs de short interest
                row.get('short_interest_momentum_5d'),
                row.get('short_interest_momentum_10d'),
                row.get('short_interest_momentum_20d'),
                row.get('short_interest_volatility_7d'),
                row.get('short_interest_volatility_14d'),
                row.get('short_interest_volatility_30d'),
                row.get('short_interest_sma_7'),
                row.get('short_interest_sma_14'),
                row.get('short_interest_sma_30'),
                # Indicateurs de short volume
                row.get('short_volume_momentum_5d'),
                row.get('short_volume_momentum_10d'),
                row.get('short_volume_momentum_20d'),
                row.get('short_volume_volatility_7d'),
                row.get('short_volume_volatility_14d'),
                row.get('short_volume_volatility_30d'),
                # Indicateurs composites
                row.get('sentiment_strength_index'),
                row.get('market_sentiment_index'),
                row.get('sentiment_divergence'),
                row.get('sentiment_acceleration'),
                row.get('sentiment_trend_strength'),
                row.get('sentiment_quality_index'),
                row.get('sentiment_risk_score')
            ))
        
        # Insérer les données avec lock pour éviter les conflits
        with db_lock:
            insert_query = """
            INSERT INTO sentiment_indicators 
            (symbol, date, sentiment_score_normalized, sentiment_momentum_1d, sentiment_momentum_3d, 
             sentiment_momentum_7d, sentiment_momentum_14d, sentiment_volatility_3d, sentiment_volatility_7d, 
             sentiment_volatility_14d, sentiment_volatility_30d, sentiment_sma_3, sentiment_sma_7, 
             sentiment_sma_14, sentiment_sma_30, sentiment_ema_3, sentiment_ema_7, sentiment_ema_14, 
             sentiment_ema_30, sentiment_rsi_14, sentiment_macd, sentiment_macd_signal, sentiment_macd_histogram,
             news_volume_sma_7, news_volume_sma_14, news_volume_sma_30, news_volume_roc_7d, news_volume_roc_14d,
             news_positive_ratio, news_negative_ratio, news_neutral_ratio, news_sentiment_quality,
             short_interest_momentum_5d, short_interest_momentum_10d, short_interest_momentum_20d,
             short_interest_volatility_7d, short_interest_volatility_14d, short_interest_volatility_30d,
             short_interest_sma_7, short_interest_sma_14, short_interest_sma_30,
             short_volume_momentum_5d, short_volume_momentum_10d, short_volume_momentum_20d,
             short_volume_volatility_7d, short_volume_volatility_14d, short_volume_volatility_30d,
             sentiment_strength_index, market_sentiment_index, sentiment_divergence, sentiment_acceleration,
             sentiment_trend_strength, sentiment_quality_index, sentiment_risk_score)
            VALUES %s
            ON CONFLICT (symbol, date) DO UPDATE SET
                sentiment_score_normalized = EXCLUDED.sentiment_score_normalized,
                sentiment_momentum_1d = EXCLUDED.sentiment_momentum_1d,
                sentiment_momentum_3d = EXCLUDED.sentiment_momentum_3d,
                sentiment_momentum_7d = EXCLUDED.sentiment_momentum_7d,
                sentiment_momentum_14d = EXCLUDED.sentiment_momentum_14d,
                sentiment_volatility_3d = EXCLUDED.sentiment_volatility_3d,
                sentiment_volatility_7d = EXCLUDED.sentiment_volatility_7d,
                sentiment_volatility_14d = EXCLUDED.sentiment_volatility_14d,
                sentiment_volatility_30d = EXCLUDED.sentiment_volatility_30d,
                sentiment_sma_3 = EXCLUDED.sentiment_sma_3,
                sentiment_sma_7 = EXCLUDED.sentiment_sma_7,
                sentiment_sma_14 = EXCLUDED.sentiment_sma_14,
                sentiment_sma_30 = EXCLUDED.sentiment_sma_30,
                sentiment_ema_3 = EXCLUDED.sentiment_ema_3,
                sentiment_ema_7 = EXCLUDED.sentiment_ema_7,
                sentiment_ema_14 = EXCLUDED.sentiment_ema_14,
                sentiment_ema_30 = EXCLUDED.sentiment_ema_30,
                sentiment_rsi_14 = EXCLUDED.sentiment_rsi_14,
                sentiment_macd = EXCLUDED.sentiment_macd,
                sentiment_macd_signal = EXCLUDED.sentiment_macd_signal,
                sentiment_macd_histogram = EXCLUDED.sentiment_macd_histogram,
                news_volume_sma_7 = EXCLUDED.news_volume_sma_7,
                news_volume_sma_14 = EXCLUDED.news_volume_sma_14,
                news_volume_sma_30 = EXCLUDED.news_volume_sma_30,
                news_volume_roc_7d = EXCLUDED.news_volume_roc_7d,
                news_volume_roc_14d = EXCLUDED.news_volume_roc_14d,
                news_positive_ratio = EXCLUDED.news_positive_ratio,
                news_negative_ratio = EXCLUDED.news_negative_ratio,
                news_neutral_ratio = EXCLUDED.news_neutral_ratio,
                news_sentiment_quality = EXCLUDED.news_sentiment_quality,
                short_interest_momentum_5d = EXCLUDED.short_interest_momentum_5d,
                short_interest_momentum_10d = EXCLUDED.short_interest_momentum_10d,
                short_interest_momentum_20d = EXCLUDED.short_interest_momentum_20d,
                short_interest_volatility_7d = EXCLUDED.short_interest_volatility_7d,
                short_interest_volatility_14d = EXCLUDED.short_interest_volatility_14d,
                short_interest_volatility_30d = EXCLUDED.short_interest_volatility_30d,
                short_interest_sma_7 = EXCLUDED.short_interest_sma_7,
                short_interest_sma_14 = EXCLUDED.short_interest_sma_14,
                short_interest_sma_30 = EXCLUDED.short_interest_sma_30,
                short_volume_momentum_5d = EXCLUDED.short_volume_momentum_5d,
                short_volume_momentum_10d = EXCLUDED.short_volume_momentum_10d,
                short_volume_momentum_20d = EXCLUDED.short_volume_momentum_20d,
                short_volume_volatility_7d = EXCLUDED.short_volume_volatility_7d,
                short_volume_volatility_14d = EXCLUDED.short_volume_volatility_14d,
                short_volume_volatility_30d = EXCLUDED.short_volume_volatility_30d,
                sentiment_strength_index = EXCLUDED.sentiment_strength_index,
                market_sentiment_index = EXCLUDED.market_sentiment_index,
                sentiment_divergence = EXCLUDED.sentiment_divergence,
                sentiment_acceleration = EXCLUDED.sentiment_acceleration,
                sentiment_trend_strength = EXCLUDED.sentiment_trend_strength,
                sentiment_quality_index = EXCLUDED.sentiment_quality_index,
                sentiment_risk_score = EXCLUDED.sentiment_risk_score
            """
            
            cursor = conn.cursor()
            execute_values(cursor, insert_query, data_to_insert)
            conn.commit()
        
        return symbol, len(data_to_insert), "Succès"
        
    except Exception as e:
        return symbol, 0, f"Erreur: {e}"
    
    finally:
        conn.close()

def process_sentiment_symbols_batch(symbols: list, batch_size: int = 10):
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
                executor.submit(calculate_sentiment_indicators_for_symbol, symbol): symbol 
                for symbol in batch
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result_symbol, count, status = future.result()
                    results.append((result_symbol, count, status))
                    
                    if count > 0:
                        print(f"   ✅ {result_symbol}: {count} indicateurs de sentiment calculés")
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
    print("🚀 Démarrage du calcul des indicateurs de sentiment...")
    
    # Récupérer tous les symboles
    symbols = get_all_symbols()
    if not symbols:
        print("❌ Aucun symbole trouvé")
        return
    
    print(f"📈 {len(symbols)} symboles à traiter")
    
    start_time = time.time()
    
    # Traiter par batch
    results, total_processed, total_errors = process_sentiment_symbols_batch(symbols, batch_size=5)
    
    end_time = time.time()
    
    # Résumé final
    print(f"\n📊 Résumé final:")
    print(f"   Symboles traités: {len(symbols)}")
    print(f"   Indicateurs de sentiment calculés: {total_processed}")
    print(f"   Erreurs: {total_errors}")
    print(f"   Temps total: {end_time - start_time:.2f} secondes")
    print(f"   Temps moyen par symbole: {(end_time - start_time) / len(symbols):.2f} secondes")
    
    # Statistiques par symbole
    print(f"\n📈 Statistiques par symbole:")
    for symbol, count, status in results:
        if count > 0:
            print(f"   ✅ {symbol}: {count} indicateurs de sentiment")
        else:
            print(f"   ❌ {symbol}: {status}")

if __name__ == "__main__":
    main()
