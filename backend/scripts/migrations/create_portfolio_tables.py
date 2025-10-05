#!/usr/bin/env python3
"""
Script pour créer les tables de gestion des portefeuilles, wallets et authentification
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import engine, Base
from app.models.users import User, UserSession, PasswordReset
from app.models.wallets import Wallet, WalletTransaction
from app.models.portfolios import (
    Portfolio, 
    Position, 
    PortfolioTransaction, 
    PositionTransaction, 
    PortfolioPerformance
)

def create_tables():
    """Créer toutes les tables nécessaires pour la gestion des portefeuilles"""
    try:
        print("🚀 Création des tables de gestion des portefeuilles...")
        
        # Créer les tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Tables créées avec succès:")
        print("   - users (authentification)")
        print("   - user_sessions (sessions utilisateur)")
        print("   - password_resets (réinitialisation de mot de passe)")
        print("   - wallets (comptes de trésorerie)")
        print("   - wallet_transactions (transactions des wallets)")
        print("   - portfolios (portefeuilles)")
        print("   - positions (positions de titres)")
        print("   - portfolio_transactions (transactions de portefeuille)")
        print("   - position_transactions (transactions de positions)")
        print("   - portfolio_performance (historique de performance)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des tables: {e}")
        return False

def verify_tables():
    """Vérifier que les tables ont été créées correctement"""
    try:
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        required_tables = [
            'users',
            'user_sessions', 
            'password_resets',
            'wallets',
            'wallet_transactions',
            'portfolios',
            'positions',
            'portfolio_transactions',
            'position_transactions',
            'portfolio_performance'
        ]
        
        print("\n📊 Vérification des tables créées:")
        for table in required_tables:
            if table in existing_tables:
                print(f"   ✅ {table}")
            else:
                print(f"   ❌ {table} - MANQUANTE")
                
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if not missing_tables:
            print(f"\n🎉 Toutes les {len(required_tables)} tables ont été créées avec succès!")
            return True
        else:
            print(f"\n⚠️  {len(missing_tables)} table(s) manquante(s): {missing_tables}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("CRÉATION DES TABLES DE GESTION DES PORTEFEUILLES")
    print("=" * 60)
    
    # Créer les tables
    if create_tables():
        # Vérifier les tables
        verify_tables()
    else:
        print("❌ Échec de la création des tables")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("TERMINÉ")
    print("=" * 60)
