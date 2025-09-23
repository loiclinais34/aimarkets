#!/usr/bin/env python3
"""
Script pour calculer et stocker les corrélations
Développe des corrélations inter-variables et cross-asset selon le plan
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
from scipy.stats import pearsonr, spearmanr, kendalltau
import warnings
warnings.filterwarnings('ignore')

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

def calculate_correlations_for_symbol(symbol: str, limit_per_symbol: int = 500):
    """Calculer les corrélations pour un symbole"""
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='aimarkets',
        user='loiclinais',
        password='MonCoeur1703@'
    )
    
    try:
        print(f"   🔄 Calcul des corrélations pour {symbol}...")
        
        # Récupérer les données historiques
        query_historical = """
        SELECT date, open, high, low, close, volume, vwap
        FROM historical_data 
        WHERE symbol = %s 
        ORDER BY date DESC
        LIMIT %s
        """
        
        df_historical = pd.read_sql(query_historical, conn, params=[symbol, limit_per_symbol])
        
        if df_historical.empty:
            return symbol, 0, f"Aucune donnée historique trouvée"
        
        # Récupérer les indicateurs techniques
        query_technical = """
        SELECT date, sma_5, sma_10, sma_20, sma_50, sma_200,
               ema_5, ema_10, ema_20, ema_50, ema_200,
               rsi_14, macd, macd_signal, macd_histogram,
               stochastic_k, stochastic_d, williams_r, roc, cci,
               bb_upper, bb_middle, bb_lower, bb_width, bb_position,
               obv, volume_roc, volume_sma_20, atr_14
        FROM technical_indicators 
        WHERE symbol = %s 
        ORDER BY date DESC
        LIMIT %s
        """
        
        df_technical = pd.read_sql(query_technical, conn, params=[symbol, limit_per_symbol])
        
        # Récupérer les indicateurs de sentiment
        query_sentiment = """
        SELECT date, sentiment_score_normalized, sentiment_momentum_7d, sentiment_volatility_14d,
               sentiment_rsi_14, sentiment_macd, news_positive_ratio, news_negative_ratio,
               sentiment_strength_index, market_sentiment_index, sentiment_risk_score, sentiment_quality_index
        FROM sentiment_indicators 
        WHERE symbol = %s 
        ORDER BY date DESC
        LIMIT %s
        """
        
        df_sentiment = pd.read_sql(query_sentiment, conn, params=[symbol, limit_per_symbol])
        
        # Fusionner les données
        df = df_historical.merge(df_technical, on='date', how='inner')
        df = df.merge(df_sentiment, on='date', how='inner')
        
        if df.empty:
            return symbol, 0, f"Aucune donnée fusionnée trouvée"
        
        # Trier par date croissante
        df = df.sort_values('date').reset_index(drop=True)
        
        # === CORRÉLATIONS INTER-VARIABLES ===
        print(f"   🔄 Calcul des corrélations inter-variables...")
        
        # 1. Corrélations Prix-Volume
        price_volume_correlations = {}
        price_cols = ['open', 'high', 'low', 'close', 'vwap']
        volume_cols = ['volume', 'obv', 'volume_roc', 'volume_sma_20']
        
        for price_col in price_cols:
            for volume_col in volume_cols:
                if price_col in df.columns and volume_col in df.columns:
                    # Pearson
                    corr_pearson, p_val_pearson = pearsonr(df[price_col].dropna(), df[volume_col].dropna())
                    # Spearman
                    corr_spearman, p_val_spearman = spearmanr(df[price_col].dropna(), df[volume_col].dropna())
                    # Kendall
                    corr_kendall, p_val_kendall = kendalltau(df[price_col].dropna(), df[volume_col].dropna())
                    
                    price_volume_correlations[f'{price_col}_{volume_col}_pearson'] = corr_pearson
                    price_volume_correlations[f'{price_col}_{volume_col}_spearman'] = corr_spearman
                    price_volume_correlations[f'{price_col}_{volume_col}_kendall'] = corr_kendall
        
        # 2. Corrélations Technique-Sentiment
        technical_sentiment_correlations = {}
        technical_cols = ['rsi_14', 'macd', 'stochastic_k', 'williams_r', 'roc', 'cci', 'bb_position']
        sentiment_cols = ['sentiment_score_normalized', 'sentiment_momentum_7d', 'sentiment_volatility_14d',
                         'sentiment_rsi_14', 'sentiment_macd', 'news_positive_ratio', 'news_negative_ratio']
        
        for tech_col in technical_cols:
            for sent_col in sentiment_cols:
                if tech_col in df.columns and sent_col in df.columns:
                    # Pearson
                    corr_pearson, p_val_pearson = pearsonr(df[tech_col].dropna(), df[sent_col].dropna())
                    # Spearman
                    corr_spearman, p_val_spearman = spearmanr(df[tech_col].dropna(), df[sent_col].dropna())
                    # Kendall
                    corr_kendall, p_val_kendall = kendalltau(df[tech_col].dropna(), df[sent_col].dropna())
                    
                    technical_sentiment_correlations[f'{tech_col}_{sent_col}_pearson'] = corr_pearson
                    technical_sentiment_correlations[f'{tech_col}_{sent_col}_spearman'] = corr_spearman
                    technical_sentiment_correlations[f'{tech_col}_{sent_col}_kendall'] = corr_kendall
        
        # 3. Corrélations Sentiment-Volume
        sentiment_volume_correlations = {}
        sentiment_cols = ['sentiment_score_normalized', 'sentiment_momentum_7d', 'news_positive_ratio', 'news_negative_ratio']
        volume_cols = ['volume', 'obv', 'volume_roc', 'volume_sma_20']
        
        for sent_col in sentiment_cols:
            for vol_col in volume_cols:
                if sent_col in df.columns and vol_col in df.columns:
                    # Pearson
                    corr_pearson, p_val_pearson = pearsonr(df[sent_col].dropna(), df[vol_col].dropna())
                    # Spearman
                    corr_spearman, p_val_spearman = spearmanr(df[sent_col].dropna(), df[vol_col].dropna())
                    # Kendall
                    corr_kendall, p_val_kendall = kendalltau(df[sent_col].dropna(), df[vol_col].dropna())
                    
                    sentiment_volume_correlations[f'{sent_col}_{vol_col}_pearson'] = corr_pearson
                    sentiment_volume_correlations[f'{sent_col}_{vol_col}_spearman'] = corr_spearman
                    sentiment_volume_correlations[f'{sent_col}_{vol_col}_kendall'] = corr_kendall
        
        # === CORRÉLATIONS TEMPORELLES ===
        print(f"   🔄 Calcul des corrélations temporelles...")
        
        # 4. Corrélations avec lag
        temporal_correlations = {}
        price_cols = ['close', 'volume']
        sentiment_cols = ['sentiment_score_normalized', 'sentiment_momentum_7d']
        
        for price_col in price_cols:
            for sent_col in sentiment_cols:
                if price_col in df.columns and sent_col in df.columns:
                    # Lag 1, 3, 7 jours
                    for lag in [1, 3, 7]:
                        if len(df) > lag:
                            # Prix vs Sentiment avec lag
                            corr_pearson, _ = pearsonr(df[price_col].iloc[lag:].dropna(), 
                                                     df[sent_col].iloc[:-lag].dropna())
                            corr_spearman, _ = spearmanr(df[price_col].iloc[lag:].dropna(), 
                                                       df[sent_col].iloc[:-lag].dropna())
                            
                            temporal_correlations[f'{price_col}_{sent_col}_lag{lag}_pearson'] = corr_pearson
                            temporal_correlations[f'{price_col}_{sent_col}_lag{lag}_spearman'] = corr_spearman
        
        # 5. Corrélations rolling
        rolling_correlations = {}
        window_sizes = [5, 10, 20]
        
        for window in window_sizes:
            if len(df) > window:
                # Rolling correlation entre prix et sentiment
                rolling_corr = df['close'].rolling(window=window).corr(df['sentiment_score_normalized'])
                rolling_correlations[f'rolling_corr_price_sentiment_{window}d'] = rolling_corr.mean()
                
                # Rolling correlation entre volume et sentiment
                rolling_corr_vol = df['volume'].rolling(window=window).corr(df['sentiment_score_normalized'])
                rolling_correlations[f'rolling_corr_volume_sentiment_{window}d'] = rolling_corr_vol.mean()
        
        # === CORRÉLATIONS CROSS-ASSET ===
        print(f"   🔄 Calcul des corrélations cross-asset...")
        
        # 6. Corrélations avec le marché (approximation avec moyenne des autres symboles)
        cross_asset_correlations = {}
        
        # Récupérer les données moyennes du marché
        query_market = """
        SELECT date, AVG(close) as market_close, AVG(volume) as market_volume
        FROM historical_data 
        WHERE symbol != %s AND date IN (
            SELECT date FROM historical_data WHERE symbol = %s ORDER BY date DESC LIMIT %s
        )
        GROUP BY date
        ORDER BY date DESC
        LIMIT %s
        """
        
        df_market = pd.read_sql(query_market, conn, params=[symbol, symbol, limit_per_symbol, limit_per_symbol])
        
        if not df_market.empty:
            # Fusionner avec les données du marché
            df_with_market = df.merge(df_market, on='date', how='inner')
            
            if not df_with_market.empty:
                # Corrélation avec le marché
                corr_market_price, _ = pearsonr(df_with_market['close'].dropna(), 
                                              df_with_market['market_close'].dropna())
                corr_market_volume, _ = pearsonr(df_with_market['volume'].dropna(), 
                                               df_with_market['market_volume'].dropna())
                
                cross_asset_correlations['market_correlation_price'] = corr_market_price
                cross_asset_correlations['market_correlation_volume'] = corr_market_volume
        
        # === CORRÉLATIONS MULTI-DIMENSIONNELLES ===
        print(f"   🔄 Calcul des corrélations multi-dimensionnelles...")
        
        # 7. Corrélations partielles (simplifiées)
        partial_correlations = {}
        
        # Corrélation partielle entre prix et sentiment, contrôlant pour le volume
        if 'close' in df.columns and 'sentiment_score_normalized' in df.columns and 'volume' in df.columns:
            try:
                # Calculer la corrélation partielle simplifiée
                # Corrélation entre prix et sentiment, en contrôlant pour le volume
                df_clean = df[['close', 'sentiment_score_normalized', 'volume']].dropna()
                if len(df_clean) > 10:
                    # Approximation de la corrélation partielle
                    corr_price_sent, _ = pearsonr(df_clean['close'], df_clean['sentiment_score_normalized'])
                    corr_price_vol, _ = pearsonr(df_clean['close'], df_clean['volume'])
                    corr_sent_vol, _ = pearsonr(df_clean['sentiment_score_normalized'], df_clean['volume'])
                    
                    # Formule de corrélation partielle
                    partial_corr_val = (corr_price_sent - corr_price_vol * corr_sent_vol) / \
                                     np.sqrt((1 - corr_price_vol**2) * (1 - corr_sent_vol**2))
                    partial_correlations['partial_corr_price_sentiment_volume'] = partial_corr_val
                else:
                    partial_correlations['partial_corr_price_sentiment_volume'] = None
            except:
                partial_correlations['partial_corr_price_sentiment_volume'] = None
        
        # 8. Corrélations composites
        composite_correlations = {}
        
        # Score composite technique
        if 'rsi_14' in df.columns and 'macd' in df.columns and 'stochastic_k' in df.columns:
            technical_score = (df['rsi_14'] + df['macd'] + df['stochastic_k']) / 3
            corr_tech_price, _ = pearsonr(technical_score.dropna(), df['close'].dropna())
            composite_correlations['technical_score_price_correlation'] = corr_tech_price
        
        # Score composite sentiment
        if 'sentiment_score_normalized' in df.columns and 'news_positive_ratio' in df.columns:
            sentiment_score = (df['sentiment_score_normalized'] + df['news_positive_ratio'] * 100) / 2
            corr_sent_price, _ = pearsonr(sentiment_score.dropna(), df['close'].dropna())
            composite_correlations['sentiment_score_price_correlation'] = corr_sent_price
        
        # === PRÉPARATION DES DONNÉES POUR L'INSERTION ===
        print(f"   🔄 Préparation des données pour l'insertion...")
        
        # Combiner toutes les corrélations
        all_correlations = {
            **price_volume_correlations,
            **technical_sentiment_correlations,
            **sentiment_volume_correlations,
            **temporal_correlations,
            **rolling_correlations,
            **cross_asset_correlations,
            **partial_correlations,
            **composite_correlations
        }
        
        # Préparer les données pour l'insertion
        data_to_insert = []
        for date_val in df['date'].unique():
            correlation_data = {
                'symbol': symbol,
                'date': date_val,
                **all_correlations
            }
            data_to_insert.append(correlation_data)
        
        # Insérer les données avec lock pour éviter les conflits
        with db_lock:
            # Créer la table si elle n'existe pas
            create_table_query = """
            CREATE TABLE IF NOT EXISTS correlation_analysis (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10) NOT NULL,
                date DATE NOT NULL,
                -- Corrélations Prix-Volume
                open_volume_pearson DECIMAL(10, 6),
                open_volume_spearman DECIMAL(10, 6),
                open_volume_kendall DECIMAL(10, 6),
                close_volume_pearson DECIMAL(10, 6),
                close_volume_spearman DECIMAL(10, 6),
                close_volume_kendall DECIMAL(10, 6),
                close_obv_pearson DECIMAL(10, 6),
                close_obv_spearman DECIMAL(10, 6),
                close_obv_kendall DECIMAL(10, 6),
                -- Corrélations Technique-Sentiment
                rsi_14_sentiment_score_normalized_pearson DECIMAL(10, 6),
                rsi_14_sentiment_score_normalized_spearman DECIMAL(10, 6),
                rsi_14_sentiment_score_normalized_kendall DECIMAL(10, 6),
                macd_sentiment_score_normalized_pearson DECIMAL(10, 6),
                macd_sentiment_score_normalized_spearman DECIMAL(10, 6),
                macd_sentiment_score_normalized_kendall DECIMAL(10, 6),
                -- Corrélations Sentiment-Volume
                sentiment_score_normalized_volume_pearson DECIMAL(10, 6),
                sentiment_score_normalized_volume_spearman DECIMAL(10, 6),
                sentiment_score_normalized_volume_kendall DECIMAL(10, 6),
                -- Corrélations Temporelles
                close_sentiment_score_normalized_lag1_pearson DECIMAL(10, 6),
                close_sentiment_score_normalized_lag1_spearman DECIMAL(10, 6),
                close_sentiment_score_normalized_lag3_pearson DECIMAL(10, 6),
                close_sentiment_score_normalized_lag3_spearman DECIMAL(10, 6),
                close_sentiment_score_normalized_lag7_pearson DECIMAL(10, 6),
                close_sentiment_score_normalized_lag7_spearman DECIMAL(10, 6),
                -- Corrélations Rolling
                rolling_corr_price_sentiment_5d DECIMAL(10, 6),
                rolling_corr_price_sentiment_10d DECIMAL(10, 6),
                rolling_corr_price_sentiment_20d DECIMAL(10, 6),
                rolling_corr_volume_sentiment_5d DECIMAL(10, 6),
                rolling_corr_volume_sentiment_10d DECIMAL(10, 6),
                rolling_corr_volume_sentiment_20d DECIMAL(10, 6),
                -- Corrélations Cross-Asset
                market_correlation_price DECIMAL(10, 6),
                market_correlation_volume DECIMAL(10, 6),
                -- Corrélations Partielles
                partial_corr_price_sentiment_volume DECIMAL(10, 6),
                -- Corrélations Composites
                technical_score_price_correlation DECIMAL(10, 6),
                sentiment_score_price_correlation DECIMAL(10, 6),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(symbol, date)
            )
            """
            
            cursor = conn.cursor()
            cursor.execute(create_table_query)
            conn.commit()
            
            # Insérer les données
            if data_to_insert:
                insert_query = """
                INSERT INTO correlation_analysis 
                (symbol, date, open_volume_pearson, open_volume_spearman, open_volume_kendall,
                 close_volume_pearson, close_volume_spearman, close_volume_kendall,
                 close_obv_pearson, close_obv_spearman, close_obv_kendall,
                 rsi_14_sentiment_score_normalized_pearson, rsi_14_sentiment_score_normalized_spearman, rsi_14_sentiment_score_normalized_kendall,
                 macd_sentiment_score_normalized_pearson, macd_sentiment_score_normalized_spearman, macd_sentiment_score_normalized_kendall,
                 sentiment_score_normalized_volume_pearson, sentiment_score_normalized_volume_spearman, sentiment_score_normalized_volume_kendall,
                 close_sentiment_score_normalized_lag1_pearson, close_sentiment_score_normalized_lag1_spearman,
                 close_sentiment_score_normalized_lag3_pearson, close_sentiment_score_normalized_lag3_spearman,
                 close_sentiment_score_normalized_lag7_pearson, close_sentiment_score_normalized_lag7_spearman,
                 rolling_corr_price_sentiment_5d, rolling_corr_price_sentiment_10d, rolling_corr_price_sentiment_20d,
                 rolling_corr_volume_sentiment_5d, rolling_corr_volume_sentiment_10d, rolling_corr_volume_sentiment_20d,
                 market_correlation_price, market_correlation_volume,
                 partial_corr_price_sentiment_volume, technical_score_price_correlation, sentiment_score_price_correlation)
                VALUES %s
                ON CONFLICT (symbol, date) DO UPDATE SET
                    open_volume_pearson = EXCLUDED.open_volume_pearson,
                    open_volume_spearman = EXCLUDED.open_volume_spearman,
                    open_volume_kendall = EXCLUDED.open_volume_kendall,
                    close_volume_pearson = EXCLUDED.close_volume_pearson,
                    close_volume_spearman = EXCLUDED.close_volume_spearman,
                    close_volume_kendall = EXCLUDED.close_volume_kendall,
                    close_obv_pearson = EXCLUDED.close_obv_pearson,
                    close_obv_spearman = EXCLUDED.close_obv_spearman,
                    close_obv_kendall = EXCLUDED.close_obv_kendall,
                    rsi_14_sentiment_score_normalized_pearson = EXCLUDED.rsi_14_sentiment_score_normalized_pearson,
                    rsi_14_sentiment_score_normalized_spearman = EXCLUDED.rsi_14_sentiment_score_normalized_spearman,
                    rsi_14_sentiment_score_normalized_kendall = EXCLUDED.rsi_14_sentiment_score_normalized_kendall,
                    macd_sentiment_score_normalized_pearson = EXCLUDED.macd_sentiment_score_normalized_pearson,
                    macd_sentiment_score_normalized_spearman = EXCLUDED.macd_sentiment_score_normalized_spearman,
                    macd_sentiment_score_normalized_kendall = EXCLUDED.macd_sentiment_score_normalized_kendall,
                    sentiment_score_normalized_volume_pearson = EXCLUDED.sentiment_score_normalized_volume_pearson,
                    sentiment_score_normalized_volume_spearman = EXCLUDED.sentiment_score_normalized_volume_spearman,
                    sentiment_score_normalized_volume_kendall = EXCLUDED.sentiment_score_normalized_volume_kendall,
                    close_sentiment_score_normalized_lag1_pearson = EXCLUDED.close_sentiment_score_normalized_lag1_pearson,
                    close_sentiment_score_normalized_lag1_spearman = EXCLUDED.close_sentiment_score_normalized_lag1_spearman,
                    close_sentiment_score_normalized_lag3_pearson = EXCLUDED.close_sentiment_score_normalized_lag3_pearson,
                    close_sentiment_score_normalized_lag3_spearman = EXCLUDED.close_sentiment_score_normalized_lag3_spearman,
                    close_sentiment_score_normalized_lag7_pearson = EXCLUDED.close_sentiment_score_normalized_lag7_pearson,
                    close_sentiment_score_normalized_lag7_spearman = EXCLUDED.close_sentiment_score_normalized_lag7_spearman,
                    rolling_corr_price_sentiment_5d = EXCLUDED.rolling_corr_price_sentiment_5d,
                    rolling_corr_price_sentiment_10d = EXCLUDED.rolling_corr_price_sentiment_10d,
                    rolling_corr_price_sentiment_20d = EXCLUDED.rolling_corr_price_sentiment_20d,
                    rolling_corr_volume_sentiment_5d = EXCLUDED.rolling_corr_volume_sentiment_5d,
                    rolling_corr_volume_sentiment_10d = EXCLUDED.rolling_corr_volume_sentiment_10d,
                    rolling_corr_volume_sentiment_20d = EXCLUDED.rolling_corr_volume_sentiment_20d,
                    market_correlation_price = EXCLUDED.market_correlation_price,
                    market_correlation_volume = EXCLUDED.market_correlation_volume,
                    partial_corr_price_sentiment_volume = EXCLUDED.partial_corr_price_sentiment_volume,
                    technical_score_price_correlation = EXCLUDED.technical_score_price_correlation,
                    sentiment_score_price_correlation = EXCLUDED.sentiment_score_price_correlation
                """
                
                # Préparer les données pour l'insertion
                insert_data = []
                for data in data_to_insert:
                    insert_data.append((
                        data['symbol'],
                        data['date'],
                        data.get('open_volume_pearson'),
                        data.get('open_volume_spearman'),
                        data.get('open_volume_kendall'),
                        data.get('close_volume_pearson'),
                        data.get('close_volume_spearman'),
                        data.get('close_volume_kendall'),
                        data.get('close_obv_pearson'),
                        data.get('close_obv_spearman'),
                        data.get('close_obv_kendall'),
                        data.get('rsi_14_sentiment_score_normalized_pearson'),
                        data.get('rsi_14_sentiment_score_normalized_spearman'),
                        data.get('rsi_14_sentiment_score_normalized_kendall'),
                        data.get('macd_sentiment_score_normalized_pearson'),
                        data.get('macd_sentiment_score_normalized_spearman'),
                        data.get('macd_sentiment_score_normalized_kendall'),
                        data.get('sentiment_score_normalized_volume_pearson'),
                        data.get('sentiment_score_normalized_volume_spearman'),
                        data.get('sentiment_score_normalized_volume_kendall'),
                        data.get('close_sentiment_score_normalized_lag1_pearson'),
                        data.get('close_sentiment_score_normalized_lag1_spearman'),
                        data.get('close_sentiment_score_normalized_lag3_pearson'),
                        data.get('close_sentiment_score_normalized_lag3_spearman'),
                        data.get('close_sentiment_score_normalized_lag7_pearson'),
                        data.get('close_sentiment_score_normalized_lag7_spearman'),
                        data.get('rolling_corr_price_sentiment_5d'),
                        data.get('rolling_corr_price_sentiment_10d'),
                        data.get('rolling_corr_price_sentiment_20d'),
                        data.get('rolling_corr_volume_sentiment_5d'),
                        data.get('rolling_corr_volume_sentiment_10d'),
                        data.get('rolling_corr_volume_sentiment_20d'),
                        data.get('market_correlation_price'),
                        data.get('market_correlation_volume'),
                        data.get('partial_corr_price_sentiment_volume'),
                        data.get('technical_score_price_correlation'),
                        data.get('sentiment_score_price_correlation')
                    ))
                
                execute_values(cursor, insert_query, insert_data)
                conn.commit()
        
        return symbol, len(data_to_insert), "Succès"
        
    except Exception as e:
        return symbol, 0, f"Erreur: {e}"
    
    finally:
        conn.close()

def process_correlation_symbols_batch(symbols: list, batch_size: int = 5):
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
                executor.submit(calculate_correlations_for_symbol, symbol): symbol 
                for symbol in batch
            }
            
            for future in as_completed(future_to_symbol):
                symbol = future_to_symbol[future]
                try:
                    result_symbol, count, status = future.result()
                    results.append((result_symbol, count, status))
                    
                    if count > 0:
                        print(f"   ✅ {result_symbol}: {count} corrélations calculées")
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
    print("🚀 Démarrage du calcul des corrélations...")
    
    # Récupérer tous les symboles
    symbols = get_all_symbols()
    if not symbols:
        print("❌ Aucun symbole trouvé")
        return
    
    print(f"📈 {len(symbols)} symboles à traiter")
    
    start_time = time.time()
    
    # Traiter par batch
    results, total_processed, total_errors = process_correlation_symbols_batch(symbols, batch_size=3)
    
    end_time = time.time()
    
    # Résumé final
    print(f"\n📊 Résumé final:")
    print(f"   Symboles traités: {len(symbols)}")
    print(f"   Corrélations calculées: {total_processed}")
    print(f"   Erreurs: {total_errors}")
    print(f"   Temps total: {end_time - start_time:.2f} secondes")
    print(f"   Temps moyen par symbole: {(end_time - start_time) / len(symbols):.2f} secondes")
    
    # Statistiques par symbole
    print(f"\n📈 Statistiques par symbole:")
    for symbol, count, status in results:
        if count > 0:
            print(f"   ✅ {symbol}: {count} corrélations")
        else:
            print(f"   ❌ {symbol}: {status}")

if __name__ == "__main__":
    main()
