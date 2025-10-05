#!/usr/bin/env python3
"""
Script de vérification de la qualité des indicateurs de sentiment
Vérifie que tous les indicateurs de sentiment sont correctement calculés
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

def check_sentiment_indicators_quality():
    """Vérifier la qualité des indicateurs de sentiment"""
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='aimarkets',
        user='loiclinais',
        password='MonCoeur1703@'
    )
    
    try:
        print("🔍 Vérification de la qualité des indicateurs de sentiment...")
        
        # 1. Vérifier la structure de la table
        print("\n📋 1. Structure de la table sentiment_indicators:")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'sentiment_indicators' 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("   Colonnes disponibles:")
        for col in columns:
            print(f"     - {col[0]} ({col[1]}) - Nullable: {col[2]}")
        
        # 2. Vérifier les données par symbole
        print("\n📊 2. Données par symbole:")
        cursor.execute("""
            SELECT symbol, COUNT(*) as count, 
                   MIN(date) as min_date, MAX(date) as max_date
            FROM sentiment_indicators 
            GROUP BY symbol 
            ORDER BY symbol
        """)
        
        symbols_data = cursor.fetchall()
        for symbol_data in symbols_data:
            print(f"   {symbol_data[0]}: {symbol_data[1]} enregistrements ({symbol_data[2]} à {symbol_data[3]})")
        
        # 3. Vérifier les indicateurs manquants par symbole
        print("\n❌ 3. Indicateurs manquants par symbole:")
        
        # Liste des indicateurs attendus
        expected_indicators = [
            'sentiment_score_normalized', 'sentiment_momentum_1d', 'sentiment_momentum_3d', 
            'sentiment_momentum_7d', 'sentiment_momentum_14d', 'sentiment_volatility_3d', 
            'sentiment_volatility_7d', 'sentiment_volatility_14d', 'sentiment_volatility_30d',
            'sentiment_sma_3', 'sentiment_sma_7', 'sentiment_sma_14', 'sentiment_sma_30',
            'sentiment_ema_3', 'sentiment_ema_7', 'sentiment_ema_14', 'sentiment_ema_30',
            'sentiment_rsi_14', 'sentiment_macd', 'sentiment_macd_signal', 'sentiment_macd_histogram',
            'news_volume_sma_7', 'news_volume_sma_14', 'news_volume_sma_30', 'news_volume_roc_7d', 'news_volume_roc_14d',
            'news_positive_ratio', 'news_negative_ratio', 'news_neutral_ratio', 'news_sentiment_quality',
            'short_interest_momentum_5d', 'short_interest_momentum_10d', 'short_interest_momentum_20d',
            'short_interest_volatility_7d', 'short_interest_volatility_14d', 'short_interest_volatility_30d',
            'short_interest_sma_7', 'short_interest_sma_14', 'short_interest_sma_30',
            'short_volume_momentum_5d', 'short_volume_momentum_10d', 'short_volume_momentum_20d',
            'short_volume_volatility_7d', 'short_volume_volatility_14d', 'short_volume_volatility_30d',
            'sentiment_strength_index', 'market_sentiment_index', 'sentiment_divergence', 'sentiment_acceleration',
            'sentiment_trend_strength', 'sentiment_quality_index', 'sentiment_risk_score'
        ]
        
        for symbol_data in symbols_data:
            symbol = symbol_data[0]
            print(f"\n   📈 {symbol}:")
            
            # Vérifier chaque indicateur
            for indicator in expected_indicators:
                cursor.execute(f"""
                    SELECT COUNT(*) as total,
                           COUNT({indicator}) as non_null,
                           COUNT(*) - COUNT({indicator}) as null_count
                    FROM sentiment_indicators 
                    WHERE symbol = %s
                """, (symbol,))
                
                result = cursor.fetchone()
                total = result[0]
                non_null = result[1]
                null_count = result[2]
                
                if null_count > 0:
                    percentage = (null_count / total) * 100
                    print(f"     ❌ {indicator}: {null_count}/{total} manquants ({percentage:.1f}%)")
                else:
                    print(f"     ✅ {indicator}: {non_null}/{total} calculés")
        
        # 4. Vérifier la cohérence des données
        print("\n🔍 4. Vérification de la cohérence des données:")
        
        # Vérifier les valeurs aberrantes
        cursor.execute("""
            SELECT symbol, 
                   COUNT(*) as total,
                   COUNT(CASE WHEN sentiment_score_normalized < 0 OR sentiment_score_normalized > 100 THEN 1 END) as sentiment_abnormal,
                   COUNT(CASE WHEN sentiment_rsi_14 < 0 OR sentiment_rsi_14 > 100 THEN 1 END) as rsi_abnormal,
                   COUNT(CASE WHEN news_positive_ratio < 0 OR news_positive_ratio > 1 THEN 1 END) as positive_ratio_abnormal,
                   COUNT(CASE WHEN news_negative_ratio < 0 OR news_negative_ratio > 1 THEN 1 END) as negative_ratio_abnormal
            FROM sentiment_indicators 
            GROUP BY symbol
        """)
        
        consistency_data = cursor.fetchall()
        for data in consistency_data:
            symbol = data[0]
            total = data[1]
            sentiment_abnormal = data[2]
            rsi_abnormal = data[3]
            positive_ratio_abnormal = data[4]
            negative_ratio_abnormal = data[5]
            
            print(f"   📊 {symbol}:")
            if sentiment_abnormal > 0:
                print(f"     ⚠️ Sentiment normalisé anormal: {sentiment_abnormal} valeurs")
            if rsi_abnormal > 0:
                print(f"     ⚠️ RSI anormal: {rsi_abnormal} valeurs")
            if positive_ratio_abnormal > 0:
                print(f"     ⚠️ Ratio positif anormal: {positive_ratio_abnormal} valeurs")
            if negative_ratio_abnormal > 0:
                print(f"     ⚠️ Ratio négatif anormal: {negative_ratio_abnormal} valeurs")
            
            if sentiment_abnormal == 0 and rsi_abnormal == 0 and positive_ratio_abnormal == 0 and negative_ratio_abnormal == 0:
                print(f"     ✅ Toutes les valeurs sont cohérentes")
        
        # 5. Vérifier les indicateurs non calculés
        print("\n📋 5. Indicateurs non calculés dans la table:")
        
        # Vérifier quels indicateurs sont NULL pour tous les symboles
        for indicator in expected_indicators:
            cursor.execute(f"""
                SELECT COUNT(*) as total,
                       COUNT({indicator}) as non_null
                FROM sentiment_indicators
            """)
            
            result = cursor.fetchone()
            total = result[0]
            non_null = result[1]
            
            if non_null == 0:
                print(f"   ❌ {indicator}: Aucune valeur calculée")
            elif non_null < total:
                percentage = (non_null / total) * 100
                print(f"   ⚠️ {indicator}: {non_null}/{total} calculés ({percentage:.1f}%)")
            else:
                print(f"   ✅ {indicator}: {non_null}/{total} calculés (100%)")
        
        # 6. Afficher un échantillon de données
        print("\n📊 6. Échantillon de données (AAPL - 5 dernières dates):")
        cursor.execute("""
            SELECT date, sentiment_score_normalized, sentiment_momentum_7d, sentiment_volatility_14d, 
                   sentiment_rsi_14, sentiment_macd, news_positive_ratio, sentiment_strength_index, 
                   market_sentiment_index, sentiment_risk_score
            FROM sentiment_indicators 
            WHERE symbol = 'AAPL'
            ORDER BY date DESC
            LIMIT 5
        """)
        
        sample_data = cursor.fetchall()
        if sample_data:
            print("   Date       | SentNorm | Mom7d   | Vol14d  | RSI     | MACD    | PosRatio | StrIdx   | MktIdx   | RiskIdx")
            print("   " + "-" * 100)
            for row in sample_data:
                date_str = row[0].strftime('%Y-%m-%d')
                sent_norm = f"{row[1]:.2f}" if row[1] else "NULL"
                mom7d = f"{row[2]:.3f}" if row[2] else "NULL"
                vol14d = f"{row[3]:.3f}" if row[3] else "NULL"
                rsi = f"{row[4]:.1f}" if row[4] else "NULL"
                macd = f"{row[5]:.3f}" if row[5] else "NULL"
                pos_ratio = f"{row[6]:.3f}" if row[6] else "NULL"
                str_idx = f"{row[7]:.2f}" if row[7] else "NULL"
                mkt_idx = f"{row[8]:.2f}" if row[8] else "NULL"
                risk_idx = f"{row[9]:.3f}" if row[9] else "NULL"
                
                print(f"   {date_str} | {sent_norm:>8} | {mom7d:>7} | {vol14d:>7} | {rsi:>7} | {macd:>7} | {pos_ratio:>8} | {str_idx:>8} | {mkt_idx:>8} | {risk_idx:>8}")
        
        # 7. Recommandations
        print("\n💡 7. Recommandations:")
        
        # Compter les indicateurs manquants
        missing_indicators = []
        for indicator in expected_indicators:
            cursor.execute(f"""
                SELECT COUNT(*) as total,
                       COUNT({indicator}) as non_null
                FROM sentiment_indicators
            """)
            
            result = cursor.fetchone()
            total = result[0]
            non_null = result[1]
            
            if non_null == 0:
                missing_indicators.append(indicator)
        
        if missing_indicators:
            print(f"   ❌ Indicateurs complètement manquants: {', '.join(missing_indicators)}")
            print(f"   🔧 Action requise: Mettre à jour le script de calcul pour inclure ces indicateurs")
        else:
            print(f"   ✅ Tous les indicateurs de sentiment de base sont calculés")
        
        # Vérifier les indicateurs partiellement calculés
        partial_indicators = []
        for indicator in expected_indicators:
            cursor.execute(f"""
                SELECT COUNT(*) as total,
                       COUNT({indicator}) as non_null
                FROM sentiment_indicators
            """)
            
            result = cursor.fetchone()
            total = result[0]
            non_null = result[1]
            
            if 0 < non_null < total:
                percentage = (non_null / total) * 100
                partial_indicators.append(f"{indicator} ({percentage:.1f}%)")
        
        if partial_indicators:
            print(f"   ⚠️ Indicateurs partiellement calculés: {', '.join(partial_indicators)}")
            print(f"   🔧 Action requise: Vérifier les conditions de calcul pour ces indicateurs")
        
        print(f"\n✅ Vérification terminée")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
    
    finally:
        conn.close()

def main():
    """Fonction principale"""
    check_sentiment_indicators_quality()

if __name__ == "__main__":
    main()
