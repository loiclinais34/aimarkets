#!/usr/bin/env python3
"""
Script simplifié pour calculer et stocker les corrélations
Version robuste avec gestion d'erreurs améliorée
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

def safe_correlation(x, y, method='pearson'):
    """Calculer une corrélation de manière sécurisée"""
    try:
        # Nettoyer les données
        x_clean = pd.Series(x).dropna()
        y_clean = pd.Series(y).dropna()
        
        # S'assurer que les deux séries ont la même longueur
        min_len = min(len(x_clean), len(y_clean))
        if min_len < 2:
            return None
        
        x_clean = x_clean.iloc[:min_len]
        y_clean = y_clean.iloc[:min_len]
        
        # Calculer la corrélation
        if method == 'pearson':
            corr, _ = pearsonr(x_clean, y_clean)
        elif method == 'spearman':
            corr, _ = spearmanr(x_clean, y_clean)
        elif method == 'kendall':
            corr, _ = kendalltau(x_clean, y_clean)
        else:
            return None
        
        return corr if not np.isnan(corr) else None
        
    except Exception as e:
        return None

def calculate_correlations_for_symbol(symbol: str, limit_per_symbol: int = 200):
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
        SELECT date, sma_5, sma_20, ema_5, ema_20, rsi_14, macd, 
               stochastic_k, williams_r, roc, cci, bb_position, 
               obv, volume_roc, atr_14
        FROM technical_indicators 
        WHERE symbol = %s 
        ORDER BY date DESC
        LIMIT %s
        """
        
        df_technical = pd.read_sql(query_technical, conn, params=[symbol, limit_per_symbol])
        
        # Récupérer les indicateurs de sentiment
        query_sentiment = """
        SELECT date, sentiment_score_normalized, sentiment_momentum_7d, 
               sentiment_volatility_14d, sentiment_rsi_14, sentiment_macd, 
               news_positive_ratio, news_negative_ratio, sentiment_strength_index, 
               market_sentiment_index, sentiment_risk_score
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
        
        print(f"   📊 {len(df)} enregistrements fusionnés")
        
        # === CORRÉLATIONS INTER-VARIABLES ===
        print(f"   🔄 Calcul des corrélations inter-variables...")
        
        correlations = {}
        
        # 1. Corrélations Prix-Volume
        price_volume_pairs = [
            ('close', 'volume'),
            ('close', 'obv'),
            ('close', 'volume_roc'),
            ('vwap', 'volume'),
            ('vwap', 'obv')
        ]
        
        for price_col, volume_col in price_volume_pairs:
            if price_col in df.columns and volume_col in df.columns:
                for method in ['pearson', 'spearman', 'kendall']:
                    corr = safe_correlation(df[price_col], df[volume_col], method)
                    if corr is not None:
                        correlations[f'{price_col}_{volume_col}_{method}'] = corr
        
        # 2. Corrélations Technique-Sentiment
        technical_sentiment_pairs = [
            ('rsi_14', 'sentiment_score_normalized'),
            ('rsi_14', 'sentiment_rsi_14'),
            ('macd', 'sentiment_macd'),
            ('stochastic_k', 'sentiment_score_normalized'),
            ('williams_r', 'sentiment_score_normalized'),
            ('roc', 'sentiment_momentum_7d'),
            ('cci', 'sentiment_score_normalized'),
            ('bb_position', 'sentiment_volatility_14d')
        ]
        
        for tech_col, sent_col in technical_sentiment_pairs:
            if tech_col in df.columns and sent_col in df.columns:
                for method in ['pearson', 'spearman']:
                    corr = safe_correlation(df[tech_col], df[sent_col], method)
                    if corr is not None:
                        correlations[f'{tech_col}_{sent_col}_{method}'] = corr
        
        # 3. Corrélations Sentiment-Volume
        sentiment_volume_pairs = [
            ('sentiment_score_normalized', 'volume'),
            ('sentiment_score_normalized', 'obv'),
            ('sentiment_momentum_7d', 'volume'),
            ('news_positive_ratio', 'volume'),
            ('news_negative_ratio', 'volume')
        ]
        
        for sent_col, vol_col in sentiment_volume_pairs:
            if sent_col in df.columns and vol_col in df.columns:
                for method in ['pearson', 'spearman']:
                    corr = safe_correlation(df[sent_col], df[vol_col], method)
                    if corr is not None:
                        correlations[f'{sent_col}_{vol_col}_{method}'] = corr
        
        # 4. Corrélations Temporelles (avec lag)
        temporal_pairs = [
            ('close', 'sentiment_score_normalized'),
            ('volume', 'sentiment_score_normalized'),
            ('close', 'sentiment_momentum_7d'),
            ('volume', 'sentiment_momentum_7d')
        ]
        
        for price_col, sent_col in temporal_pairs:
            if price_col in df.columns and sent_col in df.columns:
                for lag in [1, 3, 7]:
                    if len(df) > lag:
                        # Prix vs Sentiment avec lag
                        corr = safe_correlation(df[price_col].iloc[lag:], 
                                              df[sent_col].iloc[:-lag], 'pearson')
                        if corr is not None:
                            correlations[f'{price_col}_{sent_col}_lag{lag}'] = corr
        
        # 5. Corrélations Rolling
        rolling_pairs = [
            ('close', 'sentiment_score_normalized'),
            ('volume', 'sentiment_score_normalized')
        ]
        
        for price_col, sent_col in rolling_pairs:
            if price_col in df.columns and sent_col in df.columns:
                for window in [5, 10, 20]:
                    if len(df) > window:
                        try:
                            rolling_corr = df[price_col].rolling(window=window).corr(df[sent_col])
                            mean_corr = rolling_corr.mean()
                            if not np.isnan(mean_corr):
                                correlations[f'rolling_{price_col}_{sent_col}_{window}d'] = mean_corr
                        except:
                            pass
        
        # 6. Corrélations Cross-Asset (approximation avec moyenne du marché)
        try:
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
                    corr_market_price = safe_correlation(df_with_market['close'], 
                                                       df_with_market['market_close'], 'pearson')
                    if corr_market_price is not None:
                        correlations['market_correlation_price'] = corr_market_price
                    
                    corr_market_volume = safe_correlation(df_with_market['volume'], 
                                                        df_with_market['market_volume'], 'pearson')
                    if corr_market_volume is not None:
                        correlations['market_correlation_volume'] = corr_market_volume
        except:
            pass
        
        # 7. Corrélations Composites
        try:
            # Score composite technique
            if 'rsi_14' in df.columns and 'macd' in df.columns and 'stochastic_k' in df.columns:
                technical_score = (df['rsi_14'] + df['macd'] + df['stochastic_k']) / 3
                corr_tech_price = safe_correlation(technical_score, df['close'], 'pearson')
                if corr_tech_price is not None:
                    correlations['technical_score_price_correlation'] = corr_tech_price
            
            # Score composite sentiment
            if 'sentiment_score_normalized' in df.columns and 'news_positive_ratio' in df.columns:
                sentiment_score = (df['sentiment_score_normalized'] + df['news_positive_ratio'] * 100) / 2
                corr_sent_price = safe_correlation(sentiment_score, df['close'], 'pearson')
                if corr_sent_price is not None:
                    correlations['sentiment_score_price_correlation'] = corr_sent_price
        except:
            pass
        
        print(f"   📊 {len(correlations)} corrélations calculées")
        
        # === PRÉPARATION DES DONNÉES POUR L'INSERTION ===
        print(f"   🔄 Préparation des données pour l'insertion...")
        
        # Créer un enregistrement par date avec toutes les corrélations
        data_to_insert = []
        for date_val in df['date'].unique():
            correlation_data = {
                'symbol': symbol,
                'date': date_val,
                **correlations
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
                close_volume_pearson DECIMAL(10, 6),
                close_volume_spearman DECIMAL(10, 6),
                close_volume_kendall DECIMAL(10, 6),
                close_obv_pearson DECIMAL(10, 6),
                close_obv_spearman DECIMAL(10, 6),
                close_obv_kendall DECIMAL(10, 6),
                close_volume_roc_pearson DECIMAL(10, 6),
                close_volume_roc_spearman DECIMAL(10, 6),
                close_volume_roc_kendall DECIMAL(10, 6),
                vwap_volume_pearson DECIMAL(10, 6),
                vwap_volume_spearman DECIMAL(10, 6),
                vwap_volume_kendall DECIMAL(10, 6),
                vwap_obv_pearson DECIMAL(10, 6),
                vwap_obv_spearman DECIMAL(10, 6),
                vwap_obv_kendall DECIMAL(10, 6),
                -- Corrélations Technique-Sentiment
                rsi_14_sentiment_score_normalized_pearson DECIMAL(10, 6),
                rsi_14_sentiment_score_normalized_spearman DECIMAL(10, 6),
                rsi_14_sentiment_rsi_14_pearson DECIMAL(10, 6),
                rsi_14_sentiment_rsi_14_spearman DECIMAL(10, 6),
                macd_sentiment_macd_pearson DECIMAL(10, 6),
                macd_sentiment_macd_spearman DECIMAL(10, 6),
                stochastic_k_sentiment_score_normalized_pearson DECIMAL(10, 6),
                stochastic_k_sentiment_score_normalized_spearman DECIMAL(10, 6),
                williams_r_sentiment_score_normalized_pearson DECIMAL(10, 6),
                williams_r_sentiment_score_normalized_spearman DECIMAL(10, 6),
                roc_sentiment_momentum_7d_pearson DECIMAL(10, 6),
                roc_sentiment_momentum_7d_spearman DECIMAL(10, 6),
                cci_sentiment_score_normalized_pearson DECIMAL(10, 6),
                cci_sentiment_score_normalized_spearman DECIMAL(10, 6),
                bb_position_sentiment_volatility_14d_pearson DECIMAL(10, 6),
                bb_position_sentiment_volatility_14d_spearman DECIMAL(10, 6),
                -- Corrélations Sentiment-Volume
                sentiment_score_normalized_volume_pearson DECIMAL(10, 6),
                sentiment_score_normalized_volume_spearman DECIMAL(10, 6),
                sentiment_score_normalized_obv_pearson DECIMAL(10, 6),
                sentiment_score_normalized_obv_spearman DECIMAL(10, 6),
                sentiment_momentum_7d_volume_pearson DECIMAL(10, 6),
                sentiment_momentum_7d_volume_spearman DECIMAL(10, 6),
                news_positive_ratio_volume_pearson DECIMAL(10, 6),
                news_positive_ratio_volume_spearman DECIMAL(10, 6),
                news_negative_ratio_volume_pearson DECIMAL(10, 6),
                news_negative_ratio_volume_spearman DECIMAL(10, 6),
                -- Corrélations Temporelles
                close_sentiment_score_normalized_lag1 DECIMAL(10, 6),
                close_sentiment_score_normalized_lag3 DECIMAL(10, 6),
                close_sentiment_score_normalized_lag7 DECIMAL(10, 6),
                volume_sentiment_score_normalized_lag1 DECIMAL(10, 6),
                volume_sentiment_score_normalized_lag3 DECIMAL(10, 6),
                volume_sentiment_score_normalized_lag7 DECIMAL(10, 6),
                close_sentiment_momentum_7d_lag1 DECIMAL(10, 6),
                close_sentiment_momentum_7d_lag3 DECIMAL(10, 6),
                close_sentiment_momentum_7d_lag7 DECIMAL(10, 6),
                volume_sentiment_momentum_7d_lag1 DECIMAL(10, 6),
                volume_sentiment_momentum_7d_lag3 DECIMAL(10, 6),
                volume_sentiment_momentum_7d_lag7 DECIMAL(10, 6),
                -- Corrélations Rolling
                rolling_close_sentiment_score_normalized_5d DECIMAL(10, 6),
                rolling_close_sentiment_score_normalized_10d DECIMAL(10, 6),
                rolling_close_sentiment_score_normalized_20d DECIMAL(10, 6),
                rolling_volume_sentiment_score_normalized_5d DECIMAL(10, 6),
                rolling_volume_sentiment_score_normalized_10d DECIMAL(10, 6),
                rolling_volume_sentiment_score_normalized_20d DECIMAL(10, 6),
                -- Corrélations Cross-Asset
                market_correlation_price DECIMAL(10, 6),
                market_correlation_volume DECIMAL(10, 6),
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
                (symbol, date, close_volume_pearson, close_volume_spearman, close_volume_kendall,
                 close_obv_pearson, close_obv_spearman, close_obv_kendall,
                 close_volume_roc_pearson, close_volume_roc_spearman, close_volume_roc_kendall,
                 vwap_volume_pearson, vwap_volume_spearman, vwap_volume_kendall,
                 vwap_obv_pearson, vwap_obv_spearman, vwap_obv_kendall,
                 rsi_14_sentiment_score_normalized_pearson, rsi_14_sentiment_score_normalized_spearman,
                 rsi_14_sentiment_rsi_14_pearson, rsi_14_sentiment_rsi_14_spearman,
                 macd_sentiment_macd_pearson, macd_sentiment_macd_spearman,
                 stochastic_k_sentiment_score_normalized_pearson, stochastic_k_sentiment_score_normalized_spearman,
                 williams_r_sentiment_score_normalized_pearson, williams_r_sentiment_score_normalized_spearman,
                 roc_sentiment_momentum_7d_pearson, roc_sentiment_momentum_7d_spearman,
                 cci_sentiment_score_normalized_pearson, cci_sentiment_score_normalized_spearman,
                 bb_position_sentiment_volatility_14d_pearson, bb_position_sentiment_volatility_14d_spearman,
                 sentiment_score_normalized_volume_pearson, sentiment_score_normalized_volume_spearman,
                 sentiment_score_normalized_obv_pearson, sentiment_score_normalized_obv_spearman,
                 sentiment_momentum_7d_volume_pearson, sentiment_momentum_7d_volume_spearman,
                 news_positive_ratio_volume_pearson, news_positive_ratio_volume_spearman,
                 news_negative_ratio_volume_pearson, news_negative_ratio_volume_spearman,
                 close_sentiment_score_normalized_lag1, close_sentiment_score_normalized_lag3, close_sentiment_score_normalized_lag7,
                 volume_sentiment_score_normalized_lag1, volume_sentiment_score_normalized_lag3, volume_sentiment_score_normalized_lag7,
                 close_sentiment_momentum_7d_lag1, close_sentiment_momentum_7d_lag3, close_sentiment_momentum_7d_lag7,
                 volume_sentiment_momentum_7d_lag1, volume_sentiment_momentum_7d_lag3, volume_sentiment_momentum_7d_lag7,
                 rolling_close_sentiment_score_normalized_5d, rolling_close_sentiment_score_normalized_10d, rolling_close_sentiment_score_normalized_20d,
                 rolling_volume_sentiment_score_normalized_5d, rolling_volume_sentiment_score_normalized_10d, rolling_volume_sentiment_score_normalized_20d,
                 market_correlation_price, market_correlation_volume,
                 technical_score_price_correlation, sentiment_score_price_correlation)
                VALUES %s
                ON CONFLICT (symbol, date) DO UPDATE SET
                    close_volume_pearson = EXCLUDED.close_volume_pearson,
                    close_volume_spearman = EXCLUDED.close_volume_spearman,
                    close_volume_kendall = EXCLUDED.close_volume_kendall,
                    close_obv_pearson = EXCLUDED.close_obv_pearson,
                    close_obv_spearman = EXCLUDED.close_obv_spearman,
                    close_obv_kendall = EXCLUDED.close_obv_kendall,
                    close_volume_roc_pearson = EXCLUDED.close_volume_roc_pearson,
                    close_volume_roc_spearman = EXCLUDED.close_volume_roc_spearman,
                    close_volume_roc_kendall = EXCLUDED.close_volume_roc_kendall,
                    vwap_volume_pearson = EXCLUDED.vwap_volume_pearson,
                    vwap_volume_spearman = EXCLUDED.vwap_volume_spearman,
                    vwap_volume_kendall = EXCLUDED.vwap_volume_kendall,
                    vwap_obv_pearson = EXCLUDED.vwap_obv_pearson,
                    vwap_obv_spearman = EXCLUDED.vwap_obv_spearman,
                    vwap_obv_kendall = EXCLUDED.vwap_obv_kendall,
                    rsi_14_sentiment_score_normalized_pearson = EXCLUDED.rsi_14_sentiment_score_normalized_pearson,
                    rsi_14_sentiment_score_normalized_spearman = EXCLUDED.rsi_14_sentiment_score_normalized_spearman,
                    rsi_14_sentiment_rsi_14_pearson = EXCLUDED.rsi_14_sentiment_rsi_14_pearson,
                    rsi_14_sentiment_rsi_14_spearman = EXCLUDED.rsi_14_sentiment_rsi_14_spearman,
                    macd_sentiment_macd_pearson = EXCLUDED.macd_sentiment_macd_pearson,
                    macd_sentiment_macd_spearman = EXCLUDED.macd_sentiment_macd_spearman,
                    stochastic_k_sentiment_score_normalized_pearson = EXCLUDED.stochastic_k_sentiment_score_normalized_pearson,
                    stochastic_k_sentiment_score_normalized_spearman = EXCLUDED.stochastic_k_sentiment_score_normalized_spearman,
                    williams_r_sentiment_score_normalized_pearson = EXCLUDED.williams_r_sentiment_score_normalized_pearson,
                    williams_r_sentiment_score_normalized_spearman = EXCLUDED.williams_r_sentiment_score_normalized_spearman,
                    roc_sentiment_momentum_7d_pearson = EXCLUDED.roc_sentiment_momentum_7d_pearson,
                    roc_sentiment_momentum_7d_spearman = EXCLUDED.roc_sentiment_momentum_7d_spearman,
                    cci_sentiment_score_normalized_pearson = EXCLUDED.cci_sentiment_score_normalized_pearson,
                    cci_sentiment_score_normalized_spearman = EXCLUDED.cci_sentiment_score_normalized_spearman,
                    bb_position_sentiment_volatility_14d_pearson = EXCLUDED.bb_position_sentiment_volatility_14d_pearson,
                    bb_position_sentiment_volatility_14d_spearman = EXCLUDED.bb_position_sentiment_volatility_14d_spearman,
                    sentiment_score_normalized_volume_pearson = EXCLUDED.sentiment_score_normalized_volume_pearson,
                    sentiment_score_normalized_volume_spearman = EXCLUDED.sentiment_score_normalized_volume_spearman,
                    sentiment_score_normalized_obv_pearson = EXCLUDED.sentiment_score_normalized_obv_pearson,
                    sentiment_score_normalized_obv_spearman = EXCLUDED.sentiment_score_normalized_obv_spearman,
                    sentiment_momentum_7d_volume_pearson = EXCLUDED.sentiment_momentum_7d_volume_pearson,
                    sentiment_momentum_7d_volume_spearman = EXCLUDED.sentiment_momentum_7d_volume_spearman,
                    news_positive_ratio_volume_pearson = EXCLUDED.news_positive_ratio_volume_pearson,
                    news_positive_ratio_volume_spearman = EXCLUDED.news_positive_ratio_volume_spearman,
                    news_negative_ratio_volume_pearson = EXCLUDED.news_negative_ratio_volume_pearson,
                    news_negative_ratio_volume_spearman = EXCLUDED.news_negative_ratio_volume_spearman,
                    close_sentiment_score_normalized_lag1 = EXCLUDED.close_sentiment_score_normalized_lag1,
                    close_sentiment_score_normalized_lag3 = EXCLUDED.close_sentiment_score_normalized_lag3,
                    close_sentiment_score_normalized_lag7 = EXCLUDED.close_sentiment_score_normalized_lag7,
                    volume_sentiment_score_normalized_lag1 = EXCLUDED.volume_sentiment_score_normalized_lag1,
                    volume_sentiment_score_normalized_lag3 = EXCLUDED.volume_sentiment_score_normalized_lag3,
                    volume_sentiment_score_normalized_lag7 = EXCLUDED.volume_sentiment_score_normalized_lag7,
                    close_sentiment_momentum_7d_lag1 = EXCLUDED.close_sentiment_momentum_7d_lag1,
                    close_sentiment_momentum_7d_lag3 = EXCLUDED.close_sentiment_momentum_7d_lag3,
                    close_sentiment_momentum_7d_lag7 = EXCLUDED.close_sentiment_momentum_7d_lag7,
                    volume_sentiment_momentum_7d_lag1 = EXCLUDED.volume_sentiment_momentum_7d_lag1,
                    volume_sentiment_momentum_7d_lag3 = EXCLUDED.volume_sentiment_momentum_7d_lag3,
                    volume_sentiment_momentum_7d_lag7 = EXCLUDED.volume_sentiment_momentum_7d_lag7,
                    rolling_close_sentiment_score_normalized_5d = EXCLUDED.rolling_close_sentiment_score_normalized_5d,
                    rolling_close_sentiment_score_normalized_10d = EXCLUDED.rolling_close_sentiment_score_normalized_10d,
                    rolling_close_sentiment_score_normalized_20d = EXCLUDED.rolling_close_sentiment_score_normalized_20d,
                    rolling_volume_sentiment_score_normalized_5d = EXCLUDED.rolling_volume_sentiment_score_normalized_5d,
                    rolling_volume_sentiment_score_normalized_10d = EXCLUDED.rolling_volume_sentiment_score_normalized_10d,
                    rolling_volume_sentiment_score_normalized_20d = EXCLUDED.rolling_volume_sentiment_score_normalized_20d,
                    market_correlation_price = EXCLUDED.market_correlation_price,
                    market_correlation_volume = EXCLUDED.market_correlation_volume,
                    technical_score_price_correlation = EXCLUDED.technical_score_price_correlation,
                    sentiment_score_price_correlation = EXCLUDED.sentiment_score_price_correlation
                """
                
                # Préparer les données pour l'insertion
                insert_data = []
                for data in data_to_insert:
                    insert_data.append((
                        data['symbol'],
                        data['date'],
                        data.get('close_volume_pearson'),
                        data.get('close_volume_spearman'),
                        data.get('close_volume_kendall'),
                        data.get('close_obv_pearson'),
                        data.get('close_obv_spearman'),
                        data.get('close_obv_kendall'),
                        data.get('close_volume_roc_pearson'),
                        data.get('close_volume_roc_spearman'),
                        data.get('close_volume_roc_kendall'),
                        data.get('vwap_volume_pearson'),
                        data.get('vwap_volume_spearman'),
                        data.get('vwap_volume_kendall'),
                        data.get('vwap_obv_pearson'),
                        data.get('vwap_obv_spearman'),
                        data.get('vwap_obv_kendall'),
                        data.get('rsi_14_sentiment_score_normalized_pearson'),
                        data.get('rsi_14_sentiment_score_normalized_spearman'),
                        data.get('rsi_14_sentiment_rsi_14_pearson'),
                        data.get('rsi_14_sentiment_rsi_14_spearman'),
                        data.get('macd_sentiment_macd_pearson'),
                        data.get('macd_sentiment_macd_spearman'),
                        data.get('stochastic_k_sentiment_score_normalized_pearson'),
                        data.get('stochastic_k_sentiment_score_normalized_spearman'),
                        data.get('williams_r_sentiment_score_normalized_pearson'),
                        data.get('williams_r_sentiment_score_normalized_spearman'),
                        data.get('roc_sentiment_momentum_7d_pearson'),
                        data.get('roc_sentiment_momentum_7d_spearman'),
                        data.get('cci_sentiment_score_normalized_pearson'),
                        data.get('cci_sentiment_score_normalized_spearman'),
                        data.get('bb_position_sentiment_volatility_14d_pearson'),
                        data.get('bb_position_sentiment_volatility_14d_spearman'),
                        data.get('sentiment_score_normalized_volume_pearson'),
                        data.get('sentiment_score_normalized_volume_spearman'),
                        data.get('sentiment_score_normalized_obv_pearson'),
                        data.get('sentiment_score_normalized_obv_spearman'),
                        data.get('sentiment_momentum_7d_volume_pearson'),
                        data.get('sentiment_momentum_7d_volume_spearman'),
                        data.get('news_positive_ratio_volume_pearson'),
                        data.get('news_positive_ratio_volume_spearman'),
                        data.get('news_negative_ratio_volume_pearson'),
                        data.get('news_negative_ratio_volume_spearman'),
                        data.get('close_sentiment_score_normalized_lag1'),
                        data.get('close_sentiment_score_normalized_lag3'),
                        data.get('close_sentiment_score_normalized_lag7'),
                        data.get('volume_sentiment_score_normalized_lag1'),
                        data.get('volume_sentiment_score_normalized_lag3'),
                        data.get('volume_sentiment_score_normalized_lag7'),
                        data.get('close_sentiment_momentum_7d_lag1'),
                        data.get('close_sentiment_momentum_7d_lag3'),
                        data.get('close_sentiment_momentum_7d_lag7'),
                        data.get('volume_sentiment_momentum_7d_lag1'),
                        data.get('volume_sentiment_momentum_7d_lag3'),
                        data.get('volume_sentiment_momentum_7d_lag7'),
                        data.get('rolling_close_sentiment_score_normalized_5d'),
                        data.get('rolling_close_sentiment_score_normalized_10d'),
                        data.get('rolling_close_sentiment_score_normalized_20d'),
                        data.get('rolling_volume_sentiment_score_normalized_5d'),
                        data.get('rolling_volume_sentiment_score_normalized_10d'),
                        data.get('rolling_volume_sentiment_score_normalized_20d'),
                        data.get('market_correlation_price'),
                        data.get('market_correlation_volume'),
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
