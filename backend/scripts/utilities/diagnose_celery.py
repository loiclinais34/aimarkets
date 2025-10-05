#!/usr/bin/env python3
"""
Script de diagnostic pour les tâches Celery
"""
import requests
import time
import json

BASE_URL = "http://localhost:8000/api/v1/screener"

def test_simple_task():
    print("🔍 Test de la tâche simple...")
    
    try:
        response = requests.post(f"{BASE_URL}/test-task")
        response.raise_for_status()
        task_info = response.json()
        task_id = task_info.get("task_id")
        print(f"✅ Tâche simple lancée. Task ID: {task_id}")
        
        # Attendre et vérifier le statut
        time.sleep(5)
        response = requests.get(f"{BASE_URL}/task/{task_id}/status")
        response.raise_for_status()
        status = response.json()
        print(f"📊 Statut: {status}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def test_demo_screener():
    print("\n🔍 Test du screener de démonstration...")
    
    try:
        params = {
            "target_return_percentage": 1.5,
            "time_horizon_days": 7,
            "risk_tolerance": 0.6
        }
        
        response = requests.post(f"{BASE_URL}/run-demo", json=params)
        response.raise_for_status()
        task_info = response.json()
        task_id = task_info.get("task_id")
        print(f"✅ Screener demo lancé. Task ID: {task_id}")
        
        # Attendre et vérifier le statut
        time.sleep(10)
        response = requests.get(f"{BASE_URL}/task/{task_id}/status")
        response.raise_for_status()
        status = response.json()
        print(f"📊 Statut: {status}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_simple_task()
    test_demo_screener()
