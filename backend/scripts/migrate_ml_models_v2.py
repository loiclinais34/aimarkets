#!/usr/bin/env python3
"""
Script de migration pour ajouter model_version et renommer name en model_name
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text, inspect
from app.core.config import settings

def migrate_ml_models_v2():
    """Migration pour ajouter model_version et renommer name en model_name"""
    print("🔄 Migration des modèles ML v2...")
    
    # Connexion à la base de données
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        try:
            # Vérifier si la colonne model_version existe
            inspector = inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('ml_models')]
            
            print(f"Colonnes actuelles: {columns}")
            
            # Ajouter model_version si elle n'existe pas
            if 'model_version' not in columns:
                print("➕ Ajout de la colonne model_version...")
                conn.execute(text("ALTER TABLE ml_models ADD COLUMN model_version VARCHAR(20) DEFAULT 'v1.0'"))
                conn.commit()
                print("✅ Colonne model_version ajoutée")
            else:
                print("✅ Colonne model_version existe déjà")
            
            # Renommer name en model_name si nécessaire
            if 'name' in columns and 'model_name' not in columns:
                print("🔄 Renommage de name en model_name...")
                conn.execute(text("ALTER TABLE ml_models RENAME COLUMN name TO model_name"))
                conn.commit()
                print("✅ Colonne name renommée en model_name")
            elif 'model_name' in columns:
                print("✅ Colonne model_name existe déjà")
            
            # Mettre à jour les enregistrements existants avec model_version
            print("🔄 Mise à jour des enregistrements existants...")
            result = conn.execute(text("""
                UPDATE ml_models 
                SET model_version = 'v1.0' 
                WHERE model_version IS NULL OR model_version = ''
            """))
            conn.commit()
            print(f"✅ {result.rowcount} enregistrements mis à jour")
            
            # Vérifier le résultat
            result = conn.execute(text("SELECT COUNT(*) FROM ml_models"))
            count = result.scalar()
            print(f"📊 Total des modèles: {count}")
            
            if count > 0:
                result = conn.execute(text("SELECT model_name, model_version FROM ml_models LIMIT 5"))
                models = result.fetchall()
                print("📋 Exemples de modèles:")
                for model in models:
                    print(f"   - {model[0]} (version: {model[1]})")
            
            print("🎉 Migration terminée avec succès!")
            
        except Exception as e:
            print(f"❌ Erreur lors de la migration: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    migrate_ml_models_v2()
