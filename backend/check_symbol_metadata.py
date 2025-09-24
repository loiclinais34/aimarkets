#!/usr/bin/env python3
"""
Script pour vérifier les métadonnées de symboles
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.database import SymbolMetadata, HistoricalData

def check_symbol_metadata():
    """Vérifier les métadonnées de symboles"""
    print("🔍 Vérification des métadonnées de symboles...")
    
    db = SessionLocal()
    try:
        # Vérifier les métadonnées de symboles
        metadata_count = db.query(SymbolMetadata).count()
        print(f"📊 Nombre de métadonnées de symboles: {metadata_count}")
        
        # Vérifier les métadonnées actives
        active_metadata_count = db.query(SymbolMetadata).filter(SymbolMetadata.is_active == True).count()
        print(f"📊 Nombre de métadonnées actives: {active_metadata_count}")
        
        # Vérifier les symboles avec données historiques
        symbols_with_data = db.query(HistoricalData.symbol).distinct().all()
        print(f"📊 Symboles avec données historiques: {len(symbols_with_data)}")
        
        # Afficher quelques exemples
        if symbols_with_data:
            print(f"📊 Premiers symboles: {[s[0] for s in symbols_with_data[:10]]}")
        
        # Vérifier si les métadonnées existent pour ces symboles
        if symbols_with_data:
            first_symbol = symbols_with_data[0][0]
            metadata = db.query(SymbolMetadata).filter(SymbolMetadata.symbol == first_symbol).first()
            if metadata:
                print(f"📊 Métadonnées pour {first_symbol}: {metadata.company_name}, actif: {metadata.is_active}")
            else:
                print(f"❌ Pas de métadonnées pour {first_symbol}")
        
        # Créer des métadonnées manquantes si nécessaire
        if metadata_count == 0:
            print("🔧 Création des métadonnées manquantes...")
            for symbol_data in symbols_with_data[:10]:  # Créer pour les 10 premiers
                symbol = symbol_data[0]
                metadata = SymbolMetadata(
                    symbol=symbol,
                    company_name=f"{symbol} Corporation",
                    sector="Technology",
                    is_active=True
                )
                db.add(metadata)
            db.commit()
            print("✅ Métadonnées créées")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    check_symbol_metadata()
