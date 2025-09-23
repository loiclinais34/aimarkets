#!/usr/bin/env python3
"""
Test de connexion PostgreSQL pour AIMarkets
"""

import psycopg2
import sys
from datetime import datetime
import os
from urllib.parse import quote_plus

def test_postgresql_connection():
    """Tester la connexion à PostgreSQL"""
    try:
        # Configuration PostgreSQL depuis .env
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'aimarkets',
            'user': 'loiclinais',
            'password': 'MonCoeur1703@'
        }
        
        print("🔄 Test de connexion à PostgreSQL...")
        print(f"   Host: {db_config['host']}")
        print(f"   Port: {db_config['port']}")
        print(f"   Database: {db_config['database']}")
        print(f"   User: {db_config['user']}")
        
        # Connexion à PostgreSQL
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Test de connexion
        print("\n📡 Test de connexion...")
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   ✅ Connexion réussie")
        print(f"   📊 Version: {version}")
        
        # Test de création de base de données
        print("\n🗄️  Test de création de base de données...")
        try:
            # Vérifier si la base existe
            cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'aimarkets';")
            if cursor.fetchone():
                print("   ✅ Base de données 'aimarkets' existe déjà")
            else:
                print("   ℹ️  Base de données 'aimarkets' n'existe pas encore")
        except psycopg2.Error as e:
            print(f"   ⚠️  Note: {e}")
        
        # Test de création de table
        print("\n📋 Test de création de table...")
        test_table_sql = """
        CREATE TABLE IF NOT EXISTS test_aimarkets (
            id SERIAL PRIMARY KEY,
            test_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        cursor.execute(test_table_sql)
        print("   ✅ Table de test créée")
        
        # Test d'insertion
        print("\n💾 Test d'insertion...")
        test_message = f"Test AIMarkets - {datetime.now().isoformat()}"
        cursor.execute(
            "INSERT INTO test_aimarkets (test_message) VALUES (%s);",
            (test_message,)
        )
        print(f"   ✅ Insertion: {test_message}")
        
        # Test de sélection
        print("\n🔍 Test de sélection...")
        cursor.execute("SELECT * FROM test_aimarkets ORDER BY id DESC LIMIT 1;")
        result = cursor.fetchone()
        print(f"   ✅ Sélection: ID={result[0]}, Message={result[1]}, Date={result[2]}")
        
        # Test de suppression
        print("\n🗑️  Test de suppression...")
        cursor.execute("DELETE FROM test_aimarkets WHERE test_message = %s;", (test_message,))
        deleted_count = cursor.rowcount
        print(f"   ✅ Suppression: {deleted_count} enregistrement(s)")
        
        # Informations sur les bases de données
        print("\n📊 Informations sur les bases de données:")
        cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false;")
        databases = cursor.fetchall()
        print("   Bases de données disponibles:")
        for db in databases:
            print(f"     - {db[0]}")
        
        # Informations sur les tables
        print("\n📋 Informations sur les tables:")
        cursor.execute("""
            SELECT table_name, table_type 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        if tables:
            print("   Tables dans le schéma public:")
            for table in tables:
                print(f"     - {table[0]} ({table[1]})")
        else:
            print("   Aucune table dans le schéma public")
        
        # Nettoyage
        cursor.execute("DROP TABLE IF EXISTS test_aimarkets;")
        print("\n🧹 Table de test supprimée")
        
        # Commit et fermeture
        conn.commit()
        cursor.close()
        conn.close()
        
        print("\n🎉 Tous les tests PostgreSQL ont réussi !")
        return True
        
    except psycopg2.OperationalError as e:
        print(f"❌ Erreur de connexion PostgreSQL: {e}")
        print("   Vérifiez que PostgreSQL est démarré et accessible")
        return False
    except psycopg2.Error as e:
        print(f"❌ Erreur PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    success = test_postgresql_connection()
    sys.exit(0 if success else 1)
