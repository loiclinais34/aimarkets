#!/usr/bin/env python3
"""
Script de test pour le screener réel
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1/screener"

def test_real_screener():
    print("🚀 Test du screener réel")
    
    # 1. Lancer le screener réel
    params = {
        "target_return_percentage": 1.5,
        "time_horizon_days": 7,
        "risk_tolerance": 0.6
    }
    print(f"📋 Paramètres: {params}")
    
    print("\n1️⃣ Lancement du screener réel...")
    try:
        response = requests.post(f"{BASE_URL}/run-real", json=params)
        response.raise_for_status()
        task_info = response.json()
        task_id = task_info.get("task_id")
        print(f"✅ Screener réel lancé. Task ID: {task_id}")
        print(f"   Statut initial: {task_info.get('status')}, Message: {task_info.get('message')}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors du lancement: {e}")
        if e.response:
            print(e.response.text)
        return
    
    if not task_id:
        print("❌ Pas de Task ID reçu.")
        return
    
    # 2. Suivre la progression de la tâche
    print("\n2️⃣ Suivi de la progression de la tâche...")
    status = ""
    progress = 0
    screener_run_id = None
    results = []
    
    start_time = time.time()
    last_progress = 0
    
    while status not in ["SUCCESS", "FAILURE"]:
        try:
            response = requests.get(f"{BASE_URL}/task/{task_id}/status")
            response.raise_for_status()
            task_status = response.json()
            
            status = task_status.get("state")
            meta = task_status.get("meta", {})
            progress = meta.get("progress", 0)
            current_status_message = meta.get("status", "En attente...")
            
            # Afficher seulement si la progression a changé significativement
            if progress - last_progress >= 5:
                print(f"   Progression: {progress}% - {current_status_message}")
                last_progress = progress
            
            if status == "SUCCESS":
                screener_run_id = meta.get("screener_run_id")
                results = meta.get("results", [])
                execution_time = time.time() - start_time
                print(f"✅ Tâche terminée avec succès en {execution_time:.1f} secondes")
                print(f"   Screener Run ID: {screener_run_id}")
                print(f"   Opportunités trouvées: {len(results)}")
                break
            elif status == "FAILURE":
                error_message = meta.get("error_message", "Erreur inconnue")
                print(f"❌ Tâche échouée. Erreur: {error_message}")
                break
            
            # Timeout après 10 minutes
            if time.time() - start_time > 600:
                print("⏰ Timeout après 10 minutes")
                break
                
            time.sleep(5)  # Attendre 5 secondes avant de vérifier à nouveau
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération du statut: {e}")
            if e.response:
                print(e.response.text)
            break
        except json.JSONDecodeError:
            print(f"❌ Erreur de décodage JSON pour le statut de la tâche {task_id}")
            break
    
    # 3. Récupérer les résultats finaux si la tâche a réussi
    if screener_run_id and status == "SUCCESS":
        print(f"\n3️⃣ Récupération des résultats finaux pour Screener Run ID: {screener_run_id}...")
        try:
            response = requests.get(f"{BASE_URL}/results/{screener_run_id}")
            response.raise_for_status()
            final_results = response.json()
            print(f"✅ Résultats finaux récupérés. {len(final_results)} opportunités.")
            
            if final_results:
                print("\n📊 Top 5 des opportunités:")
                for i, res in enumerate(final_results[:5]):
                    print(f"   {i+1}. {res['symbol']} - Confiance: {res['confidence']:.1%}")
            else:
                print("   Aucune opportunité trouvée avec les paramètres actuels.")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la récupération des résultats finaux: {e}")
            if e.response:
                print(e.response.text)
    
    print("\n🎉 Test du screener réel terminé.")

if __name__ == "__main__":
    test_real_screener()
