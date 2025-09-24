#!/usr/bin/env python3
"""
Script pour diagnostiquer et corriger les problèmes de précision PostgreSQL
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from sqlalchemy import text
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def check_column_precisions():
    """Vérifie les précisions des colonnes problématiques"""
    print("🔍 Vérification des précisions des colonnes...")
    
    db = next(get_db())
    
    try:
        # Vérifier les colonnes de technical_indicators
        query = text("""
            SELECT column_name, data_type, numeric_precision, numeric_scale
            FROM information_schema.columns 
            WHERE table_name = 'technical_indicators' 
            AND table_schema = 'public'
            AND data_type = 'numeric'
            ORDER BY column_name;
        """)
        
        result = db.execute(query).fetchall()
        
        print("\n📊 Colonnes DECIMAL dans technical_indicators:")
        problematic_columns = []
        
        for row in result:
            col_name, data_type, precision, scale = row
            print(f"   {col_name}: {data_type}({precision},{scale})")
            
            # Identifier les colonnes problématiques
            if precision <= 5:
                problematic_columns.append((col_name, precision, scale))
        
        if problematic_columns:
            print(f"\n⚠️ {len(problematic_columns)} colonnes avec précision insuffisante:")
            for col_name, precision, scale in problematic_columns:
                print(f"   - {col_name}: DECIMAL({precision},{scale})")
        
        return problematic_columns
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return []
    finally:
        db.close()

def fix_column_precisions():
    """Corrige les précisions des colonnes problématiques"""
    print("\n🔧 Correction des précisions des colonnes...")
    
    # Définir les nouvelles précisions pour chaque colonne problématique
    column_fixes = {
        'obv': 'DECIMAL(15, 0)',  # Valeurs entières très grandes
        'volume_sma_20': 'DECIMAL(15, 2)',  # Moyennes de volume
        'volume_roc': 'DECIMAL(10, 4)',  # Pourcentages de variation
        'bb_width': 'DECIMAL(10, 4)',  # Largeur des Bollinger Bands
        'bb_position': 'DECIMAL(10, 4)',  # Position dans les Bollinger Bands
        'atr_14': 'DECIMAL(10, 4)',  # Average True Range
        'macd': 'DECIMAL(10, 4)',  # MACD values
        'macd_signal': 'DECIMAL(10, 4)',  # MACD signal
        'macd_histogram': 'DECIMAL(10, 4)',  # MACD histogram
        'cci': 'DECIMAL(10, 4)',  # Commodity Channel Index
        'roc': 'DECIMAL(10, 4)',  # Rate of Change
        'williams_r': 'DECIMAL(10, 4)',  # Williams %R
        'stochastic_k': 'DECIMAL(10, 4)',  # Stochastic %K
        'stochastic_d': 'DECIMAL(10, 4)',  # Stochastic %D
        'rsi_14': 'DECIMAL(10, 4)',  # RSI (peut dépasser 100 dans certains cas)
    }
    
    db = next(get_db())
    
    try:
        # Commencer une transaction
        db.begin()
        
        print("🔄 Application des corrections...")
        
        for column_name, new_type in column_fixes.items():
            try:
                # Vérifier si la colonne existe
                check_query = text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'technical_indicators' 
                    AND table_schema = 'public'
                    AND column_name = '{column_name}';
                """)
                
                exists = db.execute(check_query).fetchone()
                
                if exists:
                    print(f"   🔧 Modification de {column_name} vers {new_type}...")
                    
                    alter_query = text(f"""
                        ALTER TABLE public.technical_indicators 
                        ALTER COLUMN {column_name} TYPE {new_type};
                    """)
                    
                    db.execute(alter_query)
                    print(f"   ✅ {column_name} modifié avec succès")
                else:
                    print(f"   ⚠️ Colonne {column_name} non trouvée")
                    
            except Exception as e:
                print(f"   ❌ Erreur pour {column_name}: {e}")
                continue
        
        # Valider les changements
        db.commit()
        print("\n✅ Toutes les modifications ont été appliquées avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        db.rollback()
        print("🔄 Transaction annulée")
    finally:
        db.close()

def test_calculations():
    """Teste quelques calculs pour vérifier que les valeurs rentrent dans les nouvelles précisions"""
    print("\n🧪 Test des calculs avec les nouvelles précisions...")
    
    db = next(get_db())
    
    try:
        # Tester quelques valeurs typiques
        test_values = {
            'obv': 628043525,
            'volume_sma_20': 72166437.7,
            'volume_roc': -5.451684157949731,
            'bb_width': 19.549075547225968,
            'bb_position': 82.0642997449946,
            'atr_14': 3.275357142857138,
            'macd': -1.0098182658667594,
            'rsi_14': 80.29490616621985
        }
        
        print("📊 Test des valeurs:")
        for col_name, value in test_values.items():
            print(f"   {col_name}: {value}")
        
        # Essayer d'insérer une valeur de test
        test_query = text("""
            INSERT INTO public.technical_indicators 
            (symbol, date, obv, volume_sma_20, volume_roc, bb_width, bb_position, atr_14, macd, rsi_14)
            VALUES ('TEST', CURRENT_DATE, :obv, :volume_sma_20, :volume_roc, :bb_width, :bb_position, :atr_14, :macd, :rsi_14);
        """)
        
        db.execute(test_query, test_values)
        
        # Supprimer l'enregistrement de test
        cleanup_query = text("DELETE FROM public.technical_indicators WHERE symbol = 'TEST';")
        db.execute(cleanup_query)
        
        db.commit()
        print("✅ Test d'insertion réussi!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """Fonction principale"""
    print("🔧 Script de correction des précisions PostgreSQL")
    print("=" * 60)
    
    # Étape 1: Vérifier les précisions actuelles
    problematic_columns = check_column_precisions()
    
    if not problematic_columns:
        print("\n✅ Aucun problème de précision détecté!")
        return
    
    # Étape 2: Corriger les précisions
    fix_column_precisions()
    
    # Étape 3: Tester les calculs
    test_calculations()
    
    print("\n" + "=" * 60)
    print("🎉 Correction terminée!")
    print("\n💡 Vous pouvez maintenant relancer le recalcul des indicateurs:")
    print("   python3 force_recalculate_indicators.py")

if __name__ == "__main__":
    main()
