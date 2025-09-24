#!/usr/bin/env python3
"""
Test direct de la méthode get_active_symbols
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.tasks.full_screener_ml_web_tasks import MLWebService

def test_get_active_symbols():
    """Tester la méthode get_active_symbols"""
    print("🔍 Test de get_active_symbols...")
    
    db = SessionLocal()
    try:
        ml_service = MLWebService()
        
        # Test sans limite
        print("🔧 Test sans limite...")
        symbols = ml_service.get_active_symbols(db)
        print(f"📊 Symboles retournés: {len(symbols)}")
        if symbols:
            print(f"📊 Premiers symboles: {symbols[:5]}")
        else:
            print("❌ Aucun symbole retourné")
        
        # Test avec limite
        print("🔧 Test avec limite de 5...")
        symbols_limited = ml_service.get_active_symbols(db, limit=5)
        print(f"📊 Symboles limités: {len(symbols_limited)}")
        if symbols_limited:
            print(f"📊 Symboles limités: {symbols_limited}")
        
        # Vérifier directement la requête
        print("🔧 Test requête directe...")
        from app.models.database import SymbolMetadata
        query_result = db.query(SymbolMetadata.symbol).filter(
            SymbolMetadata.is_active == True
        ).order_by(SymbolMetadata.symbol.asc()).limit(5).all()
        print(f"📊 Requête directe: {[row[0] for row in query_result]}")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_get_active_symbols()
