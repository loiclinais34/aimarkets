#!/usr/bin/env python3
"""
Script de vérification de la qualité des indicateurs techniques
Vérifie que tous les indicateurs sont correctement calculés
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

def check_indicators_quality():
    """Vérifier la qualité des indicateurs techniques"""
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='aimarkets',
        user='loiclinais',
        password='MonCoeur1703@'
    )
    
    try:
        print("🔍 Vérification de la qualité des indicateurs techniques...")
        
        # 1. Vérifier la structure de la table
        print("\n📋 1. Structure de la table technical_indicators:")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'technical_indicators' 
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
            FROM technical_indicators 
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
            'sma_5', 'sma_10', 'sma_20', 'sma_50', 'sma_200',
            'ema_5', 'ema_10', 'ema_20', 'ema_50', 'ema_200',
            'rsi_14', 'macd', 'macd_signal', 'macd_histogram',
            'stochastic_k', 'stochastic_d', 'williams_r', 'roc', 'cci',
            'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_position',
            'obv', 'volume_roc', 'volume_sma_20', 'atr_14'
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
                    FROM technical_indicators 
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
                   COUNT(CASE WHEN rsi_14 < 0 OR rsi_14 > 100 THEN 1 END) as rsi_abnormal,
                   COUNT(CASE WHEN macd IS NULL THEN 1 END) as macd_null,
                   COUNT(CASE WHEN bb_upper < bb_lower THEN 1 END) as bb_inverted,
                   COUNT(CASE WHEN atr_14 < 0 THEN 1 END) as atr_negative
            FROM technical_indicators 
            GROUP BY symbol
        """)
        
        consistency_data = cursor.fetchall()
        for data in consistency_data:
            symbol = data[0]
            total = data[1]
            rsi_abnormal = data[2]
            macd_null = data[3]
            bb_inverted = data[4]
            atr_negative = data[5]
            
            print(f"   📊 {symbol}:")
            if rsi_abnormal > 0:
                print(f"     ⚠️ RSI anormal: {rsi_abnormal} valeurs")
            if macd_null > 0:
                print(f"     ⚠️ MACD NULL: {macd_null} valeurs")
            if bb_inverted > 0:
                print(f"     ⚠️ Bollinger Bands inversées: {bb_inverted} valeurs")
            if atr_negative > 0:
                print(f"     ⚠️ ATR négatif: {atr_negative} valeurs")
            
            if rsi_abnormal == 0 and macd_null == 0 and bb_inverted == 0 and atr_negative == 0:
                print(f"     ✅ Toutes les valeurs sont cohérentes")
        
        # 5. Vérifier les indicateurs non calculés
        print("\n📋 5. Indicateurs non calculés dans la table:")
        
        # Vérifier quels indicateurs sont NULL pour tous les symboles
        for indicator in expected_indicators:
            cursor.execute(f"""
                SELECT COUNT(*) as total,
                       COUNT({indicator}) as non_null
                FROM technical_indicators
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
            SELECT date, sma_5, sma_20, ema_5, ema_20, rsi_14, macd, 
                   bb_upper, bb_middle, bb_lower, atr_14
            FROM technical_indicators 
            WHERE symbol = 'AAPL'
            ORDER BY date DESC
            LIMIT 5
        """)
        
        sample_data = cursor.fetchall()
        if sample_data:
            print("   Date       | SMA5  | SMA20 | EMA5  | EMA20 | RSI   | MACD  | BB_U  | BB_M  | BB_L  | ATR")
            print("   " + "-" * 85)
            for row in sample_data:
                date_str = row[0].strftime('%Y-%m-%d')
                sma5 = f"{row[1]:.2f}" if row[1] else "NULL"
                sma20 = f"{row[2]:.2f}" if row[2] else "NULL"
                ema5 = f"{row[3]:.2f}" if row[3] else "NULL"
                ema20 = f"{row[4]:.2f}" if row[4] else "NULL"
                rsi = f"{row[5]:.1f}" if row[5] else "NULL"
                macd = f"{row[6]:.3f}" if row[6] else "NULL"
                bb_u = f"{row[7]:.2f}" if row[7] else "NULL"
                bb_m = f"{row[8]:.2f}" if row[8] else "NULL"
                bb_l = f"{row[9]:.2f}" if row[9] else "NULL"
                atr = f"{row[10]:.2f}" if row[10] else "NULL"
                
                print(f"   {date_str} | {sma5:>5} | {sma20:>5} | {ema5:>5} | {ema20:>5} | {rsi:>5} | {macd:>5} | {bb_u:>5} | {bb_m:>5} | {bb_l:>5} | {atr:>5}")
        
        # 7. Recommandations
        print("\n💡 7. Recommandations:")
        
        # Compter les indicateurs manquants
        missing_indicators = []
        for indicator in expected_indicators:
            cursor.execute(f"""
                SELECT COUNT(*) as total,
                       COUNT({indicator}) as non_null
                FROM technical_indicators
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
            print(f"   ✅ Tous les indicateurs de base sont calculés")
        
        # Vérifier les indicateurs partiellement calculés
        partial_indicators = []
        for indicator in expected_indicators:
            cursor.execute(f"""
                SELECT COUNT(*) as total,
                       COUNT({indicator}) as non_null
                FROM technical_indicators
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
    check_indicators_quality()

if __name__ == "__main__":
    main()
