#!/usr/bin/env python3
"""
Script pour tester directement les logs détaillés
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.tasks.full_screener_ml_web_tasks import MLWebService
from app.models.schemas import ScreenerRequest
from datetime import datetime

def test_detailed_logs():
    """Tester les logs détaillés directement"""
    print("🔧 Test des logs détaillés...")
    
    db = SessionLocal()
    try:
        # Créer une instance du service
        ml_service = MLWebService()
        print(f"✅ MLWebService créé: {type(ml_service)}")
        
        # Créer une requête de test
        request = ScreenerRequest(
            target_return_percentage=2.0,
            time_horizon_days=14,
            risk_tolerance=0.6
        )
        print(f"✅ ScreenerRequest créé: {request}")
        
        # Tester get_active_symbols
        print("🔍 Test de get_active_symbols...")
        symbols = ml_service.get_active_symbols(db, limit=5)
        print(f"📊 Symboles récupérés: {len(symbols)}")
        print(f"📊 Premiers symboles: {symbols}")
        
        # Tester create_target_parameter pour un symbole
        if symbols:
            symbol = symbols[0]
            print(f"🔧 Test de create_target_parameter pour {symbol}...")
            target_param = ml_service.create_target_parameter(db, symbol, request, "test_user")
            print(f"✅ Target parameter créé: {target_param.id}")
            
            # Tester train_model_for_symbol
            print(f"🔧 Test de train_model_for_symbol pour {symbol}...")
            success = ml_service.train_model_for_symbol(db, symbol, target_param)
            print(f"📊 Résultat entraînement: {success}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_detailed_logs()
