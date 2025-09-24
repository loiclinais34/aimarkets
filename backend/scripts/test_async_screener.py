#!/usr/bin/env python3
"""
Test du système de screener asynchrone
"""
import sys
import os
import time
import requests
import json

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_async_screener():
    """Test du screener asynchrone"""
    base_url = "http://localhost:8000/api/v1/screener"
    
    # Paramètres du screener
    screener_params = {
        "target_return_percentage": 1.5,
        "time_horizon_days": 7,
        "risk_tolerance": 0.6
    }
    
    print("🚀 Test du screener asynchrone")
    print(f"📋 Paramètres: {screener_params}")
    
    # 1. Lancer le screener de manière asynchrone
    print("\n1️⃣ Lancement du screener asynchrone...")
    response = requests.post(f"{base_url}/run-async", json=screener_params)
    
    if response.status_code != 200:
        print(f"❌ Erreur lors du lancement: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    task_id = result["task_id"]
    print(f"✅ Screener lancé avec succès!")
    print(f"🆔 Task ID: {task_id}")
    
    # 2. Suivre la progression
    print("\n2️⃣ Suivi de la progression...")
    max_attempts = 60  # 5 minutes max
    attempt = 0
    
    while attempt < max_attempts:
        # Récupérer le statut
        status_response = requests.get(f"{base_url}/task/{task_id}/status")
        
        if status_response.status_code != 200:
            print(f"❌ Erreur lors de la récupération du statut: {status_response.status_code}")
            break
        
        status_data = status_response.json()
        state = status_data["state"]
        progress = status_data.get("progress", 0)
        status_message = status_data.get("status", "En cours...")
        
        print(f"📊 [{progress:3d}%] {status_message}")
        
        if state == "SUCCESS":
            print("🎉 Screener terminé avec succès!")
            result = status_data.get("result", {})
            print(f"📈 Résultats:")
            print(f"   - Symboles analysés: {result.get('total_symbols', 0)}")
            print(f"   - Modèles entraînés: {result.get('successful_models', 0)}")
            print(f"   - Opportunités trouvées: {result.get('total_opportunities_found', 0)}")
            print(f"   - Temps d'exécution: {result.get('execution_time_seconds', 0)}s")
            break
        elif state == "FAILURE":
            print(f"❌ Screener échoué: {status_message}")
            break
        elif state == "PENDING":
            print("⏳ En attente...")
        elif state == "PROGRESS":
            # Afficher des détails supplémentaires si disponibles
            meta = status_data.get("meta", {})
            if "current_symbol" in meta:
                print(f"   🔍 Traitement: {meta['current_symbol']}")
            if "trained_models" in meta and "total_symbols" in meta:
                print(f"   📊 Modèles entraînés: {meta['trained_models']}/{meta['total_symbols']}")
        
        time.sleep(5)  # Attendre 5 secondes
        attempt += 1
    
    if attempt >= max_attempts:
        print("⏰ Timeout atteint")

if __name__ == "__main__":
    test_async_screener()
