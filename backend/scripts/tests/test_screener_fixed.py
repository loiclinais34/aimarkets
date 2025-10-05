#!/usr/bin/env python3
"""
Test du screener avec les corrections appliquées
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_screener_fixed():
    """Test du screener avec des paramètres très permissifs"""
    
    print("🧪 Test du screener (version corrigée)...")
    
    # Configuration du screener très permissive pour obtenir des résultats
    screener_request = {
        "target_return_percentage": 0.1,  # 0.1% seulement (très facile à atteindre)
        "time_horizon_days": 30,          # Sur 30 jours (beaucoup de temps)
        "risk_tolerance": 0.9             # Très agressif (seuil de confiance bas)
    }
    
    print(f"📋 Paramètres du screener (très permissifs):")
    print(f"   - Rendement attendu: {screener_request['target_return_percentage']}%")
    print(f"   - Horizon temporel: {screener_request['time_horizon_days']} jours")
    print(f"   - Tolérance au risque: {screener_request['risk_tolerance']} (très agressif)")
    print(f"   - Seuil de confiance calculé: ~50%")
    
    # Lancer le screener
    print("\n🚀 Lancement du screener...")
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/screener/run",
            json=screener_request,
            headers={"Content-Type": "application/json"},
            timeout=900  # 15 minutes timeout
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
                for i, opportunity in enumerate(result['results'][:10]):  # Limiter à 10 pour l'affichage
                    print(f"   {i+1}. {opportunity['symbol']} ({opportunity['company_name']})")
                    print(f"      Confiance: {opportunity['confidence']:.1%}")
                    print(f"      Prédiction: {opportunity['prediction']:.3f}")
                    print(f"      Modèle: {opportunity['model_name']}")
                    print()
                
                if len(result['results']) > 10:
                    print(f"   ... et {len(result['results']) - 10} autres opportunités")
            else:
                print(f"\n⚠️ Aucune opportunité trouvée avec ces paramètres")
                print(f"💡 Cela peut indiquer:")
                print(f"   - Les données historiques ne sont pas suffisantes")
                print(f"   - Les modèles ne sont pas assez performants")
                print(f"   - Les conditions de marché actuelles ne favorisent pas les opportunités")
            
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
    print("🎯 Test du screener AIMarkets (version corrigée)")
    print("=" * 60)
    
    # Attendre que l'API soit prête
    print("⏳ Attente de l'API...")
    time.sleep(5)
    
    # Test du screener
    if test_screener_fixed():
        print("\n🎉 Test du screener terminé avec succès!")
    else:
        print("\n💥 Test du screener échoué!")
        exit(1)
