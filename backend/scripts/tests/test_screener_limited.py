#!/usr/bin/env python3
"""
Test du screener avec un nombre limité de symboles
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_screener_limited():
    """Test du screener avec des paramètres conservateurs"""
    
    print("🧪 Test du screener (version limitée)...")
    
    # Configuration du screener avec seuil élevé pour obtenir des résultats
    screener_request = {
        "target_return_percentage": 0.5,  # 0.5% seulement (plus facile à atteindre)
        "time_horizon_days": 14,          # Sur 14 jours (plus de temps)
        "risk_tolerance": 0.3             # Très conservateur (seuil de confiance élevé)
    }
    
    print(f"📋 Paramètres du screener (conservateurs):")
    print(f"   - Rendement attendu: {screener_request['target_return_percentage']}%")
    print(f"   - Horizon temporel: {screener_request['time_horizon_days']} jours")
    print(f"   - Tolérance au risque: {screener_request['risk_tolerance']} (très conservateur)")
    print(f"   - Seuil de confiance calculé: ~87%")
    
    # Lancer le screener
    print("\n🚀 Lancement du screener...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/screener/run",
            json=screener_request,
            headers={"Content-Type": "application/json"},
            timeout=600  # 10 minutes timeout
        )
        
        execution_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"✅ Screener terminé en {execution_time:.1f}s")
            print(f"📊 Résultats:")
            print(f"   - Symboles analysés: {result['total_symbols']}")
            print(f"   - Modèles entraînés: {result['successful_models']}")
            print(f"   - Opportunités trouvées: {result['opportunities_found']}")
            print(f"   - Temps d'exécution serveur: {result['execution_time_seconds']}s")
            
            if result['results']:
                print(f"\n🎯 Opportunités trouvées:")
                for i, opportunity in enumerate(result['results']):
                    print(f"   {i+1}. {opportunity['symbol']} ({opportunity['company_name']})")
                    print(f"      Confiance: {opportunity['confidence']:.1%}")
                    print(f"      Prédiction: {opportunity['prediction']:.3f}")
                    print(f"      Modèle: {opportunity['model_name']}")
                    print()
            else:
                print(f"\n⚠️ Aucune opportunité trouvée avec ces paramètres")
                print(f"💡 Suggestions:")
                print(f"   - Réduire le rendement attendu (< 0.5%)")
                print(f"   - Augmenter l'horizon temporel (> 14 jours)")
                print(f"   - Augmenter la tolérance au risque (> 0.3)")
            
            return True
            
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Détail: {error_detail}")
            except:
                print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏰ Timeout après {execution_time:.1f}s")
        return False
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        return False

if __name__ == "__main__":
    print("🎯 Test du screener AIMarkets (version conservatrice)")
    print("=" * 60)
    
    # Attendre que l'API soit prête
    print("⏳ Attente de l'API...")
    time.sleep(5)
    
    # Test du screener
    if test_screener_limited():
        print("\n🎉 Test du screener terminé!")
    else:
        print("\n💥 Test du screener échoué!")
        exit(1)
