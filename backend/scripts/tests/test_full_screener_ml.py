#!/usr/bin/env python3
"""
Script de test pour le screener complet ML
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1/screener"

def test_full_screener_ml():
    print("🚀 Test du screener complet ML...")
    
    try:
        # Paramètres de test
        params = {
            "target_return_percentage": 1.5,
            "time_horizon_days": 7,
            "risk_tolerance": 0.6
        }
        
        print("📤 Lancement du screener complet ML...")
        response = requests.post(f"{BASE_URL}/run-full-ml", json=params)
        response.raise_for_status()
        task_info = response.json()
        task_id = task_info.get("task_id")
        print(f"✅ Screener complet ML lancé. Task ID: {task_id}")
        
        # Attendre la completion
        print("⏳ Attente de la completion...")
        max_attempts = 120  # Plus de temps pour l'entraînement ML
        for attempt in range(max_attempts):
            time.sleep(5)  # Vérification toutes les 5 secondes
            response = requests.get(f"{BASE_URL}/task/{task_id}/status")
            response.raise_for_status()
            status = response.json()
            
            print(f"📊 Tentative {attempt + 1}: État = {status['state']}, Progression = {status.get('progress', 0)}%")
            
            if status['state'] == 'SUCCESS':
                print("🎉 Screener complet ML terminé avec succès!")
                
                # Vérifier la structure des données
                result = status.get('result', {})
                actual_result = result.get('result', result)
                
                print(f"📋 Résultats:")
                print(f"   - Symboles analysés: {actual_result.get('total_symbols', 0)}")
                print(f"   - Modèles ML entraînés: {actual_result.get('successful_models', 0)}")
                print(f"   - Opportunités trouvées: {actual_result.get('total_opportunities_found', 0)}")
                print(f"   - Temps d'exécution: {actual_result.get('execution_time_seconds', 0)}s")
                
                # Afficher les opportunités
                results = actual_result.get('results', [])
                print(f"🎯 Opportunités ML trouvées ({len(results)}):")
                for i, opp in enumerate(results[:10]):  # Afficher les 10 premières
                    print(f"   {i+1}. {opp['symbol']} ({opp['company_name']}) - Confiance: {opp['confidence']:.1%}")
                
                if len(results) > 10:
                    print(f"   ... et {len(results) - 10} autres opportunités")
                
                return True
                
            elif status['state'] == 'FAILURE':
                print(f"❌ Screener complet ML échoué: {status.get('status', 'Erreur inconnue')}")
                return False
        
        print("⏰ Timeout: Le screener complet ML n'a pas terminé dans les temps")
        return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = test_full_screener_ml()
    if success:
        print("\n🎉 Test du screener complet ML réussi!")
    else:
        print("\n❌ Test du screener complet ML échoué.")
