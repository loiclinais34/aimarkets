#!/usr/bin/env python3
"""
Script de migration pour ajouter le support multi-devises
"""

import sys
import os
from datetime import datetime

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import get_settings

def migrate_database():
    """Migre la base de données pour ajouter le support multi-devises"""
    
    settings = get_settings()
    engine = create_engine(settings.database_url)
    
    print("🔄 Début de la migration multi-devises...")
    
    with engine.connect() as conn:
        try:
            # Commencer une transaction
            trans = conn.begin()
            
            print("📋 Création de la table exchange_rates...")
            
            # Créer la table exchange_rates
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS exchange_rates (
                    id SERIAL PRIMARY KEY,
                    from_currency VARCHAR(3) NOT NULL,
                    to_currency VARCHAR(3) NOT NULL,
                    pair VARCHAR(7) NOT NULL,
                    rate NUMERIC(10, 6) NOT NULL,
                    inverse_rate NUMERIC(10, 6) NOT NULL,
                    source VARCHAR(50) NOT NULL DEFAULT 'api',
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_fetched_at TIMESTAMP
                );
            """))
            
            # Créer les index
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_exchange_rates_from_currency 
                ON exchange_rates(from_currency);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_exchange_rates_to_currency 
                ON exchange_rates(to_currency);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_exchange_rates_pair 
                ON exchange_rates(pair);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_exchange_rates_pair_active 
                ON exchange_rates(pair, is_active);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_exchange_rates_updated_at 
                ON exchange_rates(updated_at);
            """))
            
            print("📋 Ajout du champ currency à la table positions...")
            
            # Ajouter le champ currency à la table positions
            conn.execute(text("""
                ALTER TABLE positions 
                ADD COLUMN IF NOT EXISTS currency VARCHAR(3) NOT NULL DEFAULT 'USD';
            """))
            
            print("📋 Ajout du champ currency à la table position_transactions...")
            
            # Ajouter le champ currency à la table position_transactions
            conn.execute(text("""
                ALTER TABLE position_transactions 
                ADD COLUMN IF NOT EXISTS currency VARCHAR(3) NOT NULL DEFAULT 'USD';
            """))
            
            print("📋 Ajout des index pour les champs currency...")
            
            # Ajouter les index pour les champs currency
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_positions_currency 
                ON positions(currency);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_position_transactions_currency 
                ON position_transactions(currency);
            """))
            
            print("📋 Ajout des index composites pour symbol + currency...")
            
            # Ajouter les index composites
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_positions_symbol_currency 
                ON positions(symbol, currency);
            """))
            
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_positions_portfolio_symbol_currency 
                ON positions(portfolio_id, symbol, currency);
            """))
            
            print("📋 Création de la contrainte unique pour exchange_rates...")
            
            # Créer une contrainte unique sur from_currency, to_currency
            conn.execute(text("""
                ALTER TABLE exchange_rates 
                ADD CONSTRAINT unique_currency_pair 
                UNIQUE (from_currency, to_currency);
            """))
            
            print("📋 Insertion des taux de change de base...")
            
            # Insérer des taux de change de base (1:1 pour USD)
            conn.execute(text("""
                INSERT INTO exchange_rates (from_currency, to_currency, pair, rate, inverse_rate, source, is_active, created_at, updated_at)
                VALUES 
                    ('USD', 'USD', 'USD/USD', 1.000000, 1.000000, 'identity', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                    ('EUR', 'EUR', 'EUR/EUR', 1.000000, 1.000000, 'identity', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
                    ('GBP', 'GBP', 'GBP/GBP', 1.000000, 1.000000, 'identity', true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT (from_currency, to_currency) DO NOTHING;
            """))
            
            # Valider la transaction
            trans.commit()
            
            print("✅ Migration multi-devises terminée avec succès!")
            print("📊 Tables créées/modifiées:")
            print("   - exchange_rates (nouvelle table)")
            print("   - positions.currency (nouveau champ)")
            print("   - position_transactions.currency (nouveau champ)")
            print("   - Index créés pour optimiser les requêtes")
            
        except Exception as e:
            # Annuler la transaction en cas d'erreur
            trans.rollback()
            print(f"❌ Erreur lors de la migration: {e}")
            raise

def verify_migration():
    """Vérifie que la migration a été appliquée correctement"""
    
    settings = get_settings()
    engine = create_engine(settings.database_url)
    
    print("\n🔍 Vérification de la migration...")
    
    with engine.connect() as conn:
        # Vérifier la table exchange_rates
        result = conn.execute(text("""
            SELECT COUNT(*) FROM exchange_rates;
        """)).fetchone()
        print(f"📊 Lignes dans exchange_rates: {result[0]}")
        
        # Vérifier le champ currency dans positions
        result = conn.execute(text("""
            SELECT COUNT(*) FROM positions WHERE currency = 'USD';
        """)).fetchone()
        print(f"📊 Positions avec currency USD: {result[0]}")
        
        # Vérifier le champ currency dans position_transactions
        result = conn.execute(text("""
            SELECT COUNT(*) FROM position_transactions WHERE currency = 'USD';
        """)).fetchone()
        print(f"📊 Transactions avec currency USD: {result[0]}")
        
        print("✅ Vérification terminée!")

if __name__ == "__main__":
    try:
        migrate_database()
        verify_migration()
        print("\n🎉 Migration multi-devises complétée avec succès!")
        
    except Exception as e:
        print(f"\n💥 Erreur fatale: {e}")
        sys.exit(1)
