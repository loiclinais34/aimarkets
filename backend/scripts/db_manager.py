#!/usr/bin/env python3
"""
Script de gestion de la base de données AIMarkets
Permet de créer, initialiser, sauvegarder et restaurer la base de données
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Ajouter le répertoire parent au path pour importer les modules
sys.path.append(str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import engine, Base
from app.models.database import *


class DatabaseManager:
    def __init__(self):
        self.db_config = {
            'host': settings.db_host,
            'port': settings.db_port,
            'user': settings.db_user,
            'password': settings.db_password,
            'database': settings.db_name
        }
    
    def create_database(self):
        """Créer la base de données si elle n'existe pas"""
        try:
            # Connexion à PostgreSQL sans spécifier de base de données
            conn = psycopg2.connect(
                host=self.db_config['host'],
                port=self.db_config['port'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database='postgres'  # Connexion à la base par défaut
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            # Vérifier si la base de données existe
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.db_config['database'],)
            )
            
            if cursor.fetchone():
                print(f"✅ La base de données '{self.db_config['database']}' existe déjà")
            else:
                # Créer la base de données
                cursor.execute(f"CREATE DATABASE {self.db_config['database']}")
                print(f"✅ Base de données '{self.db_config['database']}' créée avec succès")
            
            cursor.close()
            conn.close()
            
        except psycopg2.Error as e:
            print(f"❌ Erreur lors de la création de la base de données: {e}")
            sys.exit(1)
    
    def create_tables(self):
        """Créer toutes les tables de la base de données"""
        try:
            print("🔄 Création des tables...")
            Base.metadata.create_all(bind=engine)
            print("✅ Toutes les tables ont été créées avec succès")
        except Exception as e:
            print(f"❌ Erreur lors de la création des tables: {e}")
            sys.exit(1)
    
    def drop_tables(self):
        """Supprimer toutes les tables de la base de données"""
        try:
            print("🔄 Suppression des tables...")
            Base.metadata.drop_all(bind=engine)
            print("✅ Toutes les tables ont été supprimées avec succès")
        except Exception as e:
            print(f"❌ Erreur lors de la suppression des tables: {e}")
            sys.exit(1)
    
    def reset_database(self):
        """Réinitialiser complètement la base de données"""
        print("🔄 Réinitialisation de la base de données...")
        self.drop_tables()
        self.create_tables()
        print("✅ Base de données réinitialisée avec succès")
    
    def backup_database(self, backup_path: str = None):
        """Sauvegarder la base de données"""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_aimarkets_{timestamp}.sql"
        
        try:
            print(f"🔄 Sauvegarde de la base de données vers {backup_path}...")
            
            # Commande pg_dump
            cmd = [
                'pg_dump',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['user'],
                '-d', self.db_config['database'],
                '-f', backup_path,
                '--verbose'
            ]
            
            # Définir le mot de passe via variable d'environnement
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Sauvegarde créée avec succès: {backup_path}")
            else:
                print(f"❌ Erreur lors de la sauvegarde: {result.stderr}")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            sys.exit(1)
    
    def restore_database(self, backup_path: str):
        """Restaurer la base de données depuis un fichier de sauvegarde"""
        if not os.path.exists(backup_path):
            print(f"❌ Le fichier de sauvegarde {backup_path} n'existe pas")
            sys.exit(1)
        
        try:
            print(f"🔄 Restauration de la base de données depuis {backup_path}...")
            
            # Commande psql
            cmd = [
                'psql',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['user'],
                '-d', self.db_config['database'],
                '-f', backup_path,
                '--verbose'
            ]
            
            # Définir le mot de passe via variable d'environnement
            env = os.environ.copy()
            env['PGPASSWORD'] = self.db_config['password']
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Base de données restaurée avec succès depuis {backup_path}")
            else:
                print(f"❌ Erreur lors de la restauration: {result.stderr}")
                sys.exit(1)
                
        except Exception as e:
            print(f"❌ Erreur lors de la restauration: {e}")
            sys.exit(1)
    
    def check_connection(self):
        """Vérifier la connexion à la base de données"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            cursor.close()
            conn.close()
            print(f"✅ Connexion à la base de données réussie")
            print(f"📊 Version PostgreSQL: {version}")
        except psycopg2.Error as e:
            print(f"❌ Erreur de connexion à la base de données: {e}")
            sys.exit(1)
    
    def show_tables(self):
        """Afficher la liste des tables de la base de données"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            cursor.close()
            conn.close()
            
            if tables:
                print("📋 Tables de la base de données:")
                for table_name, table_type in tables:
                    print(f"  - {table_name} ({table_type})")
            else:
                print("📋 Aucune table trouvée dans la base de données")
                
        except psycopg2.Error as e:
            print(f"❌ Erreur lors de la récupération des tables: {e}")
            sys.exit(1)
    
    def show_stats(self):
        """Afficher les statistiques de la base de données"""
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Statistiques générales
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_tuples,
                    n_dead_tup as dead_tuples
                FROM pg_stat_user_tables
                ORDER BY n_live_tup DESC;
            """)
            stats = cursor.fetchall()
            
            print("📊 Statistiques de la base de données:")
            print(f"{'Table':<25} {'Inserts':<10} {'Updates':<10} {'Deletes':<10} {'Live':<10} {'Dead':<10}")
            print("-" * 80)
            
            for stat in stats:
                schema, table, inserts, updates, deletes, live, dead = stat
                print(f"{table:<25} {inserts:<10} {updates:<10} {deletes:<10} {live:<10} {dead:<10}")
            
            cursor.close()
            conn.close()
            
        except psycopg2.Error as e:
            print(f"❌ Erreur lors de la récupération des statistiques: {e}")
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Gestionnaire de base de données AIMarkets")
    parser.add_argument('action', choices=[
        'create-db', 'create-tables', 'drop-tables', 'reset', 
        'backup', 'restore', 'check', 'tables', 'stats'
    ], help="Action à effectuer")
    parser.add_argument('--backup-path', help="Chemin du fichier de sauvegarde")
    parser.add_argument('--restore-path', help="Chemin du fichier de restauration")
    
    args = parser.parse_args()
    
    db_manager = DatabaseManager()
    
    if args.action == 'create-db':
        db_manager.create_database()
    elif args.action == 'create-tables':
        db_manager.create_tables()
    elif args.action == 'drop-tables':
        db_manager.drop_tables()
    elif args.action == 'reset':
        db_manager.reset_database()
    elif args.action == 'backup':
        db_manager.backup_database(args.backup_path)
    elif args.action == 'restore':
        if not args.restore_path:
            print("❌ Le chemin du fichier de restauration est requis")
            sys.exit(1)
        db_manager.restore_database(args.restore_path)
    elif args.action == 'check':
        db_manager.check_connection()
    elif args.action == 'tables':
        db_manager.show_tables()
    elif args.action == 'stats':
        db_manager.show_stats()


if __name__ == "__main__":
    main()
