#!/usr/bin/env python3
"""
Script de test pour le screener
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_screener_simple():
    """Test simple du screener avec des paramètres de base"""
    
    print("🧪 Test du screener d'opportunités...")
    
    # Configuration du screener
    screener_request = {
        "target_return_percentage": 1.5,  # 1.5% de rendement
        "time_horizon_days": 7,           # Sur 7 jours
        "risk_tolerance": 0.7             # Tolérance au risque modérée
    }
    
    print(f"📋 Paramètres du screener:")
    print(f"   - Rendement attendu: {screener_request['target_return_percentage']}%")
    print(f"   - Horizon temporel: {screener_request['time_horizon_days']} jours")
    print(f"   - Tolérance au risque: {screener_request['risk_tolerance']}")
    
    # Lancer le screener
    print("\n🚀 Lancement du screener...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/screener/run",
            json=screener_request,
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minutes timeout
        )
        
        execution_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Screener terminé en {execution_time:.1f}s")
            print(f"📊 Résultats:")
            print(f"   - Symboles analysés: {result['total_symbols']}")
            print(f"   - Modèles entraînés: {result['successful_models']}")
            print(f"   - Opportunités trouvées: {result['opportunities_found']}")
            print(f"   - Temps d'exécution: {result['execution_time_seconds']}s")
            
            if result['results']:
                print(f"\n🎯 Top 5 opportunités:")
                for i, opportunity in enumerate(result['results'][:5]):
                    print(f"   {i+1}. {opportunity['symbol']} ({opportunity['company_name']})")
                    print(f"      Confiance: {opportunity['confidence']:.1%}")
                    print(f"      Prédiction: {opportunity['prediction']:.3f}")
            else:
                print(f"\n⚠️ Aucune opportunité trouvée avec ces paramètres")
            
            return True
            
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout après {execution_time:.1f}s")
        return False
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def test_screener_stats():
    """Test des statistiques du screener"""
    
    print("\n📈 Récupération des statistiques...")
    
    try:
        response = requests.get(f"{BASE_URL}/screener/stats")
        
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Statistiques récupérées:")
            print(f"   - Exécutions totales: {stats['total_runs']}")
            print(f"   - Exécutions réussies: {stats['completed_runs']}")
            print(f"   - Taux de succès: {stats['success_rate']:.1f}%")
            print(f"   - Opportunités trouvées: {stats['total_opportunities_found']}")
            
            return True
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

def test_health_check():
    """Vérification de la santé de l'API"""
    
    print("🔍 Vérification de l'API...")
    
    try:
        response = requests.get(f"http://localhost:8000/health")
        
        if response.status_code == 200:
            health = response.json()
            print(f"✅ API opérationnelle:")
            print(f"   - Status: {health['status']}")
            print(f"   - Version: {health['version']}")
            return True
        else:
            print(f"❌ API non disponible (HTTP {response.status_code})")
            return False
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎯 Test du système de screener AIMarkets")
    print("=" * 50)
    
    # Vérification de l'API
    if not test_health_check():
        exit(1)
    
    # Test des statistiques initiales
    test_screener_stats()
    
    # Test du screener
    if test_screener_simple():
        print("\n🎉 Test du screener réussi!")
        
        # Statistiques finales
        test_screener_stats()
    else:
        print("\n💥 Test du screener échoué!")
        exit(1)
