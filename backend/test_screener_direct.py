#!/usr/bin/env python3
"""
Script pour tester directement le screener ML avec nos corrections
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.tasks.full_screener_ml_web_tasks import run_full_screener_ml_web
from app.models.schemas import ScreenerRequest
from datetime import datetime

def test_screener_directly():
    """Tester le screener directement sans Celery"""
    print("🔧 Test direct du screener ML...")
    
    # Créer une requête de test
    request_dict = {
        "target_return_percentage": 2.0,
        "time_horizon_days": 14,
        "risk_tolerance": 0.6
    }
    
    print(f"✅ Requête créée: {request_dict}")
    
    try:
        # Appeler directement la fonction (sans Celery)
        print("🚀 Lancement du screener ML...")
        result = run_full_screener_ml_web(request_dict, "test_user", max_symbols=3)
        
        print("🎉 Screener terminé !")
        print(f"📊 Résultat: {result}")
        
        if result and result.get('successful_models', 0) > 0:
            print("✅ Le screener ML fonctionne correctement !")
        else:
            print("⚠️  Aucun modèle entraîné - vérifier les données")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_screener_directly()
