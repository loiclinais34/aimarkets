#!/usr/bin/env python3
"""
Script de debug pour vérifier les modèles dans le screener
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.database import MLModels, SymbolMetadata
from sqlalchemy.orm import Session

def debug_screener_models():
    """Debug des modèles dans le screener"""
    
    print("🔍 Debug des modèles dans le screener")
    print("=" * 60)
    
    db = next(get_db())
    try:
        # Récupérer les symboles disponibles
        symbols = db.query(SymbolMetadata.symbol).filter(
            SymbolMetadata.is_active == True
        ).limit(5).all()
        
        symbol_list = [s[0] for s in symbols]
        print(f"📊 Symboles de test: {symbol_list}")
        
        # Vérifier les modèles actifs pour ces symboles
        active_models = db.query(MLModels).filter(
            MLModels.is_active == True,
            MLModels.symbol.in_(symbol_list)
        ).all()
        
        print(f"📊 {len(active_models)} modèles actifs trouvés pour ces symboles")
        
        for model in active_models:
            print(f"   🤖 {model.model_name}")
            print(f"      Symbole: {model.symbol}")
            print(f"      Type: {model.model_type}")
            print(f"      Chemin: {model.model_path}")
            print(f"      Actif: {model.is_active}")
            print(f"      Performance: {model.performance_metrics}")
            print()
        
        # Vérifier tous les modèles actifs
        all_active_models = db.query(MLModels).filter(
            MLModels.is_active == True
        ).limit(10).all()
        
        print(f"📊 {len(all_active_models)} modèles actifs au total (échantillon)")
        
        for model in all_active_models:
            print(f"   🤖 {model.model_name}")
            print(f"      Symbole: {model.symbol}")
            print(f"      Chemin: {model.model_path}")
            print()
        
        # Vérifier les modèles avec des paramètres spécifiques
        print(f"\n📊 Modèles avec paramètres spécifiques (5% sur 10 jours)")
        specific_models = db.query(MLModels).filter(
            MLModels.is_active == True
        ).all()
        
        matching_models = []
        for model in specific_models:
            params = model.model_parameters
            if params and isinstance(params, dict):
                target_return = params.get('target_return_percentage')
                time_horizon = params.get('time_horizon_days')
                
                if target_return == "5.0" and time_horizon == 10:
                    matching_models.append(model)
        
        print(f"📊 {len(matching_models)} modèles avec 5% sur 10 jours")
        
        for model in matching_models[:5]:  # Afficher les 5 premiers
            print(f"   🤖 {model.model_name}")
            print(f"      Symbole: {model.symbol}")
            print(f"      Chemin: {model.model_path}")
            print(f"      Performance: {model.performance_metrics}")
            print()
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Démarrage du debug des modèles du screener")
    
    debug_screener_models()
    
    print("\n🏁 Debug terminé")
