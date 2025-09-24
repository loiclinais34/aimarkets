#!/usr/bin/env python3
"""
Script pour vérifier le schéma SQLAlchemy en cache
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from sqlalchemy import text
from sqlalchemy import inspect

def check_sqlalchemy_schema():
    """Vérifie le schéma selon SQLAlchemy"""
    db = next(get_db())
    
    try:
        # Vérifier le schéma actuel avec SQLAlchemy inspector
        inspector = inspect(db.bind)
        columns = inspector.get_columns('technical_indicators', schema='public')
        
        print('🔍 Schéma actuel selon SQLAlchemy:')
        problematic = []
        
        for col in columns:
            if col['type'].__class__.__name__ == 'NUMERIC':
                precision = getattr(col['type'], 'precision', None)
                scale = getattr(col['type'], 'scale', None)
                if precision and precision <= 5:
                    problematic.append((col['name'], precision, scale))
                print(f'  {col["name"]}: {col["type"]} (precision: {precision}, scale: {scale})')
        
        if problematic:
            print(f'\n⚠️ Colonnes problématiques détectées: {len(problematic)}')
            for name, prec, scale in problematic:
                print(f'  - {name}: DECIMAL({prec},{scale})')
        else:
            print('\n✅ Aucune colonne problématique détectée')
        
        return problematic
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return []
    finally:
        db.close()

def force_schema_refresh():
    """Force le rafraîchissement du schéma SQLAlchemy"""
    print("\n🔄 Tentative de rafraîchissement du schéma...")
    
    db = next(get_db())
    
    try:
        # Vider le cache de métadonnées SQLAlchemy
        db.bind.clear_compiled_cache()
        
        # Forcer la reconnexion
        db.close()
        
        print("✅ Cache SQLAlchemy vidé et reconnexion forcée")
        
    except Exception as e:
        print(f"❌ Erreur lors du rafraîchissement: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Vérification du schéma SQLAlchemy")
    print("=" * 50)
    
    # Vérifier le schéma
    problematic = check_sqlalchemy_schema()
    
    if problematic:
        print("\n🔄 Tentative de rafraîchissement...")
        force_schema_refresh()
        
        print("\n🔍 Vérification après rafraîchissement:")
        check_sqlalchemy_schema()
