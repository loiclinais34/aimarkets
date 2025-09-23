#!/usr/bin/env python3
"""
Test de connexion Redis pour AIMarkets
"""

import redis
import sys
from datetime import datetime

def test_redis_connection():
    """Tester la connexion à Redis"""
    try:
        # Configuration Redis
        redis_config = {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'decode_responses': True,
            'socket_connect_timeout': 5,
            'socket_timeout': 5
        }
        
        print("🔄 Test de connexion à Redis...")
        print(f"   Host: {redis_config['host']}")
        print(f"   Port: {redis_config['port']}")
        print(f"   DB: {redis_config['db']}")
        
        # Connexion à Redis
        r = redis.Redis(**redis_config)
        
        # Test PING
        print("\n📡 Test PING...")
        response = r.ping()
        print(f"   ✅ PING: {response}")
        
        # Test SET/GET
        print("\n💾 Test SET/GET...")
        test_key = "aimarkets_test"
        test_value = f"Test AIMarkets - {datetime.now().isoformat()}"
        
        r.set(test_key, test_value)
        print(f"   ✅ SET: {test_key} = {test_value}")
        
        retrieved_value = r.get(test_key)
        print(f"   ✅ GET: {test_key} = {retrieved_value}")
        
        # Test DELETE
        print("\n🗑️  Test DELETE...")
        deleted = r.delete(test_key)
        print(f"   ✅ DELETE: {deleted} clé(s) supprimée(s)")
        
        # Test avec expiration
        print("\n⏰ Test avec expiration...")
        r.setex("aimarkets_temp", 5, "Expiration test")
        ttl = r.ttl("aimarkets_temp")
        print(f"   ✅ SETEX: TTL = {ttl} secondes")
        
        # Nettoyer
        r.delete("aimarkets_temp")
        
        # Informations Redis
        print("\n📊 Informations Redis:")
        info = r.info()
        print(f"   Version: {info.get('redis_version')}")
        print(f"   Mode: {info.get('redis_mode')}")
        print(f"   Mémoire utilisée: {info.get('used_memory_human')}")
        print(f"   Clients connectés: {info.get('connected_clients')}")
        print(f"   Commandes traitées: {info.get('total_commands_processed')}")
        
        print("\n🎉 Tous les tests Redis ont réussi !")
        return True
        
    except redis.ConnectionError as e:
        print(f"❌ Erreur de connexion Redis: {e}")
        return False
    except redis.TimeoutError as e:
        print(f"❌ Timeout Redis: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur Redis: {e}")
        return False

if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)
