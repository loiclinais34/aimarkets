#!/usr/bin/env python3
"""
Script de migration pour mettre à jour les tables ML
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import get_db

def migrate_ml_models():
    """Migre les tables ML pour supporter LightGBM"""
    print("🔄 Migration des tables ML...")
    
    db = next(get_db())
    
    try:
        # Vérifier si la colonne symbol existe déjà
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_models' 
            AND column_name = 'symbol'
        """))
        
        if not result.fetchone():
            print("➕ Ajout de la colonne symbol à ml_models...")
            db.execute(text("ALTER TABLE public.ml_models ADD COLUMN symbol VARCHAR(10)"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_ml_models_symbol ON public.ml_models(symbol)"))
        
        # Vérifier si la colonne target_parameter_id existe déjà
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_models' 
            AND column_name = 'target_parameter_id'
        """))
        
        if not result.fetchone():
            print("➕ Ajout de la colonne target_parameter_id à ml_models...")
            db.execute(text("ALTER TABLE public.ml_models ADD COLUMN target_parameter_id INTEGER"))
            db.execute(text("""
                ALTER TABLE public.ml_models 
                ADD CONSTRAINT fk_ml_models_target_parameter 
                FOREIGN KEY (target_parameter_id) 
                REFERENCES public.target_parameters(id)
            """))
        
        # Vérifier si la colonne performance_metrics existe déjà
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_models' 
            AND column_name = 'performance_metrics'
        """))
        
        if not result.fetchone():
            print("➕ Ajout de la colonne performance_metrics à ml_models...")
            db.execute(text("ALTER TABLE public.ml_models ADD COLUMN performance_metrics JSONB"))
        
        # Vérifier si la colonne created_by existe déjà
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_models' 
            AND column_name = 'created_by'
        """))
        
        if not result.fetchone():
            print("➕ Ajout de la colonne created_by à ml_models...")
            db.execute(text("ALTER TABLE public.ml_models ADD COLUMN created_by VARCHAR(100)"))
        
        # Renommer model_name en name si nécessaire
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_models' 
            AND column_name = 'model_name'
        """))
        
        if result.fetchone():
            print("🔄 Renommage de model_name en name...")
            db.execute(text("ALTER TABLE public.ml_models RENAME COLUMN model_name TO name"))
        
        # Mettre à jour la table ml_predictions
        print("🔄 Mise à jour de la table ml_predictions...")
        
        # Vérifier si la colonne prediction_date existe déjà
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_predictions' 
            AND column_name = 'prediction_date'
        """))
        
        if not result.fetchone():
            print("➕ Ajout de la colonne prediction_date à ml_predictions...")
            db.execute(text("ALTER TABLE public.ml_predictions ADD COLUMN prediction_date DATE"))
            db.execute(text("CREATE INDEX IF NOT EXISTS idx_ml_predictions_prediction_date ON public.ml_predictions(prediction_date)"))
        
        # Vérifier si la colonne prediction_class existe déjà
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_predictions' 
            AND column_name = 'prediction_class'
        """))
        
        if not result.fetchone():
            print("➕ Ajout de la colonne prediction_class à ml_predictions...")
            db.execute(text("ALTER TABLE public.ml_predictions ADD COLUMN prediction_class VARCHAR(50)"))
        
        # Vérifier si la colonne data_date_used existe déjà
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_predictions' 
            AND column_name = 'data_date_used'
        """))
        
        if not result.fetchone():
            print("➕ Ajout de la colonne data_date_used à ml_predictions...")
            db.execute(text("ALTER TABLE public.ml_predictions ADD COLUMN data_date_used DATE"))
        
        # Vérifier si la colonne created_by existe déjà
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_predictions' 
            AND column_name = 'created_by'
        """))
        
        if not result.fetchone():
            print("➕ Ajout de la colonne created_by à ml_predictions...")
            db.execute(text("ALTER TABLE public.ml_predictions ADD COLUMN created_by VARCHAR(100)"))
        
        # Supprimer les colonnes obsolètes si elles existent
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_predictions' 
            AND column_name = 'prediction_type'
        """))
        
        if result.fetchone():
            print("🗑️ Suppression de la colonne prediction_type...")
            db.execute(text("ALTER TABLE public.ml_predictions DROP COLUMN prediction_type"))
        
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_predictions' 
            AND column_name = 'features_used'
        """))
        
        if result.fetchone():
            print("🗑️ Suppression de la colonne features_used...")
            db.execute(text("ALTER TABLE public.ml_predictions DROP COLUMN features_used"))
        
        # Renommer date en prediction_date si nécessaire
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'ml_predictions' 
            AND column_name = 'date'
        """))
        
        if result.fetchone():
            # Vérifier si prediction_date existe déjà
            result2 = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'ml_predictions' 
                AND column_name = 'prediction_date'
            """))
            
            if result2.fetchone():
                print("🔄 Suppression de la colonne date (prediction_date existe déjà)...")
                db.execute(text("ALTER TABLE public.ml_predictions DROP COLUMN date"))
            else:
                print("🔄 Renommage de date en prediction_date...")
                db.execute(text("ALTER TABLE public.ml_predictions RENAME COLUMN date TO prediction_date"))
        
        db.commit()
        print("✅ Migration terminée avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    migrate_ml_models()
