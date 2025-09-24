#!/usr/bin/env python3
"""
Script pour diagnostiquer les problèmes de schéma SQLAlchemy
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.models.database import TechnicalIndicators
from sqlalchemy import inspect
from sqlalchemy import text
import pandas as pd
import numpy as np

def check_table_schema():
    """Vérifie le schéma de la table technical_indicators"""
    print("🔍 Vérification du schéma de la table technical_indicators...")
    
    db = next(get_db())
    
    try:
        # Utiliser SQLAlchemy inspector pour obtenir le schéma
        inspector = inspect(db.bind)
        columns = inspector.get_columns('technical_indicators', schema='public')
        
        print("\n📊 Schéma de la table technical_indicators:")
        print("   Colonne | Type | Nullable | Default")
        print("   " + "-" * 50)
        
        for col in columns:
            col_name = col['name']
            col_type = str(col['type'])
            nullable = col['nullable']
            default = col['default']
            
            print(f"   {col_name:<15} | {col_type:<15} | {nullable:<8} | {default}")
        
        return columns
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification du schéma: {e}")
        return []
    finally:
        db.close()

def check_sample_data():
    """Vérifie les données existantes dans la table"""
    print("\n📋 Vérification des données existantes...")
    
    db = next(get_db())
    
    try:
        # Récupérer un échantillon de données
        query = text("""
            SELECT symbol, date, sma_5, sma_10, rsi_14, obv, volume_sma_20
            FROM public.technical_indicators 
            WHERE symbol = 'AAPL'
            ORDER BY date DESC
            LIMIT 3;
        """)
        
        result = db.execute(query).fetchall()
        
        if result:
            print("   📊 Échantillon de données existantes (AAPL):")
            for row in result:
                print(f"   {row.symbol} | {row.date} | SMA5: {row.sma_5} | RSI: {row.rsi_14} | OBV: {row.obv}")
        else:
            print("   ⚠️ Aucune donnée trouvée pour AAPL")
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des données: {e}")
        return []
    finally:
        db.close()

def test_data_conversion():
    """Teste la conversion des données calculées"""
    print("\n🧪 Test de conversion des données calculées...")
    
    # Simuler des données calculées comme dans le service
    test_indicators = {
        'symbol': 'TEST',
        'date': '2025-09-24',
        'sma_5': 143.808,
        'sma_10': 141.103,
        'sma_20': 135.779,
        'sma_50': None,
        'sma_200': None,
        'ema_5': 143.3832328986291,
        'ema_10': 141.45693115426712,
        'ema_20': 139.14975748506018,
        'ema_50': None,
        'ema_200': None,
        'rsi_14': 80.29490616621985,
        'macd': None,
        'macd_signal': None,
        'macd_histogram': None,
        'stochastic_k': 82.46869409660107,
        'stochastic_d': 84.51032171962409,
        'williams_r': -17.531305903398934,
        'roc': 6.7154796242881325,
        'cci': 101.4481929051025,
        'bb_upper': 149.05076964363397,
        'bb_middle': 135.779,
        'bb_lower': 122.50723035636602,
        'bb_width': 19.549075547225968,
        'bb_position': 82.0642997449946,
        'obv': 628043525,
        'volume_roc': -5.451684157949731,
        'volume_sma_20': 72166437.7,
        'atr_14': 3.275357142857138
    }
    
    print("   📊 Données de test:")
    for key, value in test_indicators.items():
        if value is not None:
            print(f"   {key}: {value} (type: {type(value).__name__})")
    
    # Convertir les types numpy
    converted_indicators = convert_numpy_types(test_indicators)
    
    print("\n   🔄 Après conversion:")
    for key, value in converted_indicators.items():
        if value is not None:
            print(f"   {key}: {value} (type: {type(value).__name__})")
    
    return converted_indicators

def convert_numpy_types(indicators):
    """Convertit les types numpy en types Python natifs"""
    import numpy as np
    
    converted = {}
    for key, value in indicators.items():
        if value is None:
            converted[key] = None
        elif isinstance(value, (np.integer, np.int64, np.int32)):
            converted[key] = int(value)
        elif isinstance(value, (np.floating, np.float64, np.float32)):
            converted[key] = float(value)
        elif isinstance(value, np.ndarray):
            converted[key] = float(value.item()) if value.size > 0 else None
        else:
            converted[key] = value
    
    return converted

def test_insertion():
    """Teste l'insertion d'un enregistrement de test"""
    print("\n💾 Test d'insertion d'un enregistrement de test...")
    
    db = next(get_db())
    
    try:
        # Préparer les données de test
        test_data = test_data_conversion()
        
        # Créer un objet TechnicalIndicators
        test_record = TechnicalIndicators(**test_data)
        
        print("   📝 Objet TechnicalIndicators créé:")
        print(f"   Symbol: {test_record.symbol}")
        print(f"   Date: {test_record.date}")
        print(f"   SMA5: {test_record.sma_5}")
        print(f"   RSI: {test_record.rsi_14}")
        print(f"   OBV: {test_record.obv}")
        
        # Essayer d'ajouter à la session
        db.add(test_record)
        
        # Vérifier les changements en attente
        print("   🔍 Changements en attente:")
        print(f"   Nouveau: {test_record in db.new}")
        print(f"   Modifié: {test_record in db.dirty}")
        
        # Valider l'insertion
        db.commit()
        print("   ✅ Insertion réussie!")
        
        # Supprimer l'enregistrement de test
        db.delete(test_record)
        db.commit()
        print("   🗑️ Enregistrement de test supprimé")
        
    except Exception as e:
        print(f"   ❌ Erreur lors de l'insertion: {e}")
        print(f"   Type d'erreur: {type(e).__name__}")
        db.rollback()
        
        # Afficher plus de détails sur l'erreur
        if hasattr(e, 'orig'):
            print(f"   Erreur PostgreSQL: {e.orig}")
        
    finally:
        db.close()

def check_required_fields():
    """Vérifie les champs obligatoires"""
    print("\n🔍 Vérification des champs obligatoires...")
    
    db = next(get_db())
    
    try:
        # Vérifier les contraintes NOT NULL
        query = text("""
            SELECT column_name, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'technical_indicators' 
            AND table_schema = 'public'
            AND is_nullable = 'NO'
            ORDER BY column_name;
        """)
        
        result = db.execute(query).fetchall()
        
        print("   📋 Champs obligatoires (NOT NULL):")
        for row in result:
            print(f"   - {row.column_name} (défaut: {row.column_default})")
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return []
    finally:
        db.close()

def main():
    """Fonction principale"""
    print("🔧 Script de diagnostic des problèmes SQLAlchemy")
    print("=" * 60)
    
    # Étape 1: Vérifier le schéma
    schema = check_table_schema()
    
    # Étape 2: Vérifier les données existantes
    sample_data = check_sample_data()
    
    # Étape 3: Vérifier les champs obligatoires
    required_fields = check_required_fields()
    
    # Étape 4: Tester la conversion des données
    converted_data = test_data_conversion()
    
    # Étape 5: Tester l'insertion
    test_insertion()
    
    print("\n" + "=" * 60)
    print("🎯 Diagnostic terminé!")
    
    if schema and sample_data is not None:
        print("✅ Le schéma et les données semblent corrects")
    else:
        print("⚠️ Des problèmes ont été détectés")

if __name__ == "__main__":
    main()
