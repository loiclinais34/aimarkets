#!/usr/bin/env python3
"""
Script de debug pour vérifier les paramètres des modèles
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.database import MLModels

def debug_model_parameters():
    """Debug des paramètres des modèles"""
    
    print("🔍 Debug des paramètres des modèles")
    print("=" * 60)
    
    db = next(get_db())
    try:
        # Récupérer quelques modèles récents
        models = db.query(MLModels).filter(
            MLModels.is_active == True
        ).limit(10).all()
        
        print(f"📊 {len(models)} modèles trouvés")
        
        for model in models:
            print(f"\n🤖 {model.model_name}")
            print(f"   Symbole: {model.symbol}")
            
            params = model.model_parameters
            if params and isinstance(params, dict):
                target_return = params.get('target_return_percentage')
                time_horizon = params.get('time_horizon_days')
                
                print(f"   target_return_percentage: {target_return} (type: {type(target_return)})")
                print(f"   time_horizon_days: {time_horizon} (type: {type(time_horizon)})")
                
                # Test de comparaison
                test_values = [1.0, "1.0", 1, "1"]
                for test_val in test_values:
                    match = str(target_return) == str(test_val)
                    print(f"   str({target_return}) == str({test_val}): {match}")
            else:
                print(f"   ❌ Pas de paramètres")
        
        # Test spécifique avec les paramètres de la recherche
        print(f"\n🔍 Test avec paramètres de recherche (1.0% sur 30 jours)")
        
        target_return_percentage = 1.0
        time_horizon_days = 30
        
        matching_models = []
        for model in models:
            params = model.model_parameters
            if params and isinstance(params, dict):
                model_target_return = params.get('target_return_percentage')
                model_time_horizon = params.get('time_horizon_days')
                
                # Test de comparaison
                target_match = str(model_target_return) == str(target_return_percentage)
                horizon_match = model_time_horizon == time_horizon_days
                
                if target_match and horizon_match:
                    matching_models.append(model)
                    print(f"   ✅ {model.model_name} - Correspond")
                else:
                    print(f"   ❌ {model.model_name} - Ne correspond pas")
                    print(f"      target_return: {model_target_return} vs {target_return_percentage} ({target_match})")
                    print(f"      time_horizon: {model_time_horizon} vs {time_horizon_days} ({horizon_match})")
        
        print(f"\n🎯 {len(matching_models)} modèles correspondants trouvés")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Démarrage du debug des paramètres des modèles")
    
    debug_model_parameters()
    
    print("\n🏁 Debug terminé")
