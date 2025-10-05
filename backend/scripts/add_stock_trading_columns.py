#!/usr/bin/env python3
"""
Script pour ajouter les colonnes de trading de titres à la table wallet_transactions
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine
from sqlalchemy import text

def add_stock_trading_columns():
    """Ajoute les colonnes nécessaires pour le trading de titres"""
    
    try:
        with engine.connect() as conn:
            # Ajouter les colonnes pour le trading de titres
            conn.execute(text("""
                ALTER TABLE wallet_transactions 
                ADD COLUMN IF NOT EXISTS symbol VARCHAR(20),
                ADD COLUMN IF NOT EXISTS quantity NUMERIC(15, 6),
                ADD COLUMN IF NOT EXISTS price NUMERIC(15, 6),
                ADD COLUMN IF NOT EXISTS fees NUMERIC(15, 2) DEFAULT 0.00;
            """))
            
            # Mettre à jour l'enum pour inclure les nouveaux types
            conn.execute(text("""
                ALTER TYPE wallettransactiontype ADD VALUE IF NOT EXISTS 'BUY_STOCK';
            """))
            
            conn.execute(text("""
                ALTER TYPE wallettransactiontype ADD VALUE IF NOT EXISTS 'SELL_STOCK';
            """))
            
            conn.commit()
            print("✅ Colonnes de trading de titres ajoutées avec succès")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'ajout des colonnes: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = add_stock_trading_columns()
    if success:
        print("Migration terminée avec succès")
    else:
        print("Migration échouée")
        sys.exit(1)
