#!/usr/bin/env python3
"""
Script de migration pour créer les tables de screener
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import settings

def create_screener_tables():
    """Crée les tables nécessaires pour les screeners"""
    
    # Connexion à la base de données
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        # Démarrer une transaction
        trans = conn.begin()
        
        try:
            print("🚀 Création des tables de screener...")
            
            # Table screener_configs
            print("📋 Création de la table screener_configs...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS public.screener_configs (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    target_return_percentage DECIMAL(5,2) NOT NULL,
                    time_horizon_days INTEGER NOT NULL,
                    risk_tolerance DECIMAL(3,2) NOT NULL,
                    confidence_threshold DECIMAL(3,2) NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_by VARCHAR(100) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Table screener_runs
            print("🏃 Création de la table screener_runs...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS public.screener_runs (
                    id SERIAL PRIMARY KEY,
                    screener_config_id INTEGER NOT NULL,
                    run_date DATE NOT NULL,
                    total_symbols INTEGER NOT NULL,
                    successful_models INTEGER NOT NULL,
                    opportunities_found INTEGER NOT NULL,
                    execution_time_seconds INTEGER NOT NULL,
                    status VARCHAR(50) NOT NULL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (screener_config_id) REFERENCES public.screener_configs(id)
                );
            """))
            
            # Table screener_results
            print("📊 Création de la table screener_results...")
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS public.screener_results (
                    id SERIAL PRIMARY KEY,
                    screener_run_id INTEGER NOT NULL,
                    symbol VARCHAR(10) NOT NULL,
                    model_id INTEGER NOT NULL,
                    prediction DECIMAL(10,6) NOT NULL,
                    confidence DECIMAL(5,4) NOT NULL,
                    rank INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (screener_run_id) REFERENCES public.screener_runs(id),
                    FOREIGN KEY (model_id) REFERENCES public.ml_models(id)
                );
            """))
            
            # Créer les index pour améliorer les performances
            print("🔍 Création des index...")
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_screener_runs_run_date ON public.screener_runs(run_date);
                CREATE INDEX IF NOT EXISTS idx_screener_runs_status ON public.screener_runs(status);
                CREATE INDEX IF NOT EXISTS idx_screener_results_symbol ON public.screener_results(symbol);
                CREATE INDEX IF NOT EXISTS idx_screener_results_rank ON public.screener_results(rank);
            """))
            
            # Valider la transaction
            trans.commit()
            print("✅ Tables de screener créées avec succès!")
            
        except Exception as e:
            # Annuler la transaction en cas d'erreur
            trans.rollback()
            print(f"❌ Erreur lors de la création des tables: {str(e)}")
            raise e

def verify_tables():
    """Vérifie que les tables ont été créées correctement"""
    
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        print("🔍 Vérification des tables...")
        
        # Vérifier screener_configs
        result = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'screener_configs';
        """))
        if result.scalar() == 0:
            print("❌ Table screener_configs non trouvée")
            return False
        
        # Vérifier screener_runs
        result = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'screener_runs';
        """))
        if result.scalar() == 0:
            print("❌ Table screener_runs non trouvée")
            return False
        
        # Vérifier screener_results
        result = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'screener_results';
        """))
        if result.scalar() == 0:
            print("❌ Table screener_results non trouvée")
            return False
        
        print("✅ Toutes les tables de screener sont présentes")
        return True

if __name__ == "__main__":
    try:
        create_screener_tables()
        verify_tables()
        print("🎉 Migration des tables de screener terminée avec succès!")
        
    except Exception as e:
        print(f"💥 Erreur lors de la migration: {str(e)}")
        sys.exit(1)
