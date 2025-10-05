#!/usr/bin/env python3
"""
Script pour mettre à jour la table wallet_transactions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from app.core.config import get_settings

def update_wallet_transactions_table():
    """Met à jour la table wallet_transactions avec le nouveau schéma"""
    
    settings = get_settings()
    engine = create_engine(settings.database_url)
    
    with engine.connect() as conn:
        try:
            print("🔄 Mise à jour de la table wallet_transactions...")
            
            # Supprimer la table existante
            conn.execute(text("DROP TABLE IF EXISTS wallet_transactions CASCADE;"))
            conn.commit()
            print("✅ Table wallet_transactions supprimée")
            
            # Créer la nouvelle table avec le bon schéma
            create_table_sql = """
            CREATE TABLE wallet_transactions (
                id SERIAL PRIMARY KEY,
                wallet_id INTEGER NOT NULL,
                transaction_type VARCHAR(20) NOT NULL,
                amount NUMERIC(15,2) NOT NULL,
                balance_after NUMERIC(15,2) NOT NULL,
                target_wallet_id INTEGER,
                reference VARCHAR(100),
                description VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (wallet_id) REFERENCES wallets(id) ON DELETE CASCADE
            );
            """
            
            conn.execute(text(create_table_sql))
            conn.commit()
            print("✅ Table wallet_transactions créée avec le nouveau schéma")
            
            # Créer les index
            conn.execute(text("CREATE INDEX idx_wallet_transactions_wallet_id ON wallet_transactions(wallet_id);"))
            conn.execute(text("CREATE INDEX idx_wallet_transactions_type ON wallet_transactions(transaction_type);"))
            conn.execute(text("CREATE INDEX idx_wallet_transactions_created_at ON wallet_transactions(created_at);"))
            conn.commit()
            print("✅ Index créés")
            
            print("🎉 Mise à jour terminée avec succès !")
            
        except Exception as e:
            print(f"❌ Erreur lors de la mise à jour: {e}")
            conn.rollback()
            raise

if __name__ == "__main__":
    update_wallet_transactions_table()
