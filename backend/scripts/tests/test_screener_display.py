#!/usr/bin/env python3
"""
Script de test pour vérifier que les résultats du screener s'affichent correctement
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1/screener"

def test_screener_results_display():
    print("🔍 Test de l'affichage des résultats du screener...")
    
    try:
        # Lancer un screener de démonstration
        params = {
            "target_return_percentage": 1.5,
            "time_horizon_days": 7,
            "risk_tolerance": 0.6
        }
        
        print("📤 Lancement du screener de démonstration...")
        response = requests.post(f"{BASE_URL}/run-demo", json=params)
        response.raise_for_status()
        task_info = response.json()
        task_id = task_info.get("task_id")
        print(f"✅ Screener lancé. Task ID: {task_id}")
        
        # Attendre la completion
        print("⏳ Attente de la completion...")
        max_attempts = 30
        for attempt in range(max_attempts):
            time.sleep(2)
            response = requests.get(f"{BASE_URL}/task/{task_id}/status")
            response.raise_for_status()
            status = response.json()
            
            print(f"📊 Tentative {attempt + 1}: État = {status['state']}, Progression = {status.get('progress', 0)}%")
            
            if status['state'] == 'SUCCESS':
                print("🎉 Screener terminé avec succès!")
                
                # Vérifier la structure des données
                result = status.get('result', {})
                actual_result = result.get('result', result)
                
                print(f"📋 Structure des données:")
                print(f"   - État: {status['state']}")
                print(f"   - Résultat principal: {list(result.keys())}")
                print(f"   - Résultat réel: {list(actual_result.keys())}")
                
                # Vérifier les résultats
                results = actual_result.get('results', [])
                print(f"🎯 Opportunités trouvées: {len(results)}")
                
                for i, opp in enumerate(results):
                    print(f"   {i+1}. {opp['symbol']} ({opp['company_name']})")
                    print(f"      - Confiance: {opp['confidence']:.1%}")
                    print(f"      - Prédiction: {opp['prediction']}")
                    print(f"      - Rang: #{opp['rank']}")
                
                # Vérifier que les données sont dans le bon format pour le frontend
                if len(results) > 0:
                    print("✅ Les données sont correctement structurées pour l'affichage frontend!")
                    return True
                else:
                    print("⚠️ Aucune opportunité trouvée")
                    return False
                    
            elif status['state'] == 'FAILURE':
                print(f"❌ Screener échoué: {status.get('status', 'Erreur inconnue')}")
                return False
        
        print("⏰ Timeout: Le screener n'a pas terminé dans les temps")
        return False
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = test_screener_results_display()
    if success:
        print("\n🎉 Test réussi! Les résultats devraient maintenant s'afficher dans le frontend.")
    else:
        print("\n❌ Test échoué. Vérifiez les logs pour plus de détails.")
