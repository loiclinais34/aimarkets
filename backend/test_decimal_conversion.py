#!/usr/bin/env python3
"""
Script de test pour vérifier la conversion Decimal
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.database import TargetParameters
from decimal import Decimal

def test_decimal_conversion():
    """Test de la conversion Decimal"""
    
    print("🔍 Test de la conversion Decimal")
    print("=" * 60)
    
    # Test des conversions
    test_values = [5.0, 5, "5.0", "5"]
    
    for value in test_values:
        print(f"📊 Valeur originale: {value} (type: {type(value)})")
        
        # Conversion en Decimal
        decimal_value = Decimal(str(value))
        print(f"   Decimal: {decimal_value} (type: {type(decimal_value)})")
        
        # Test de création d'un TargetParameters
        db = next(get_db())
        try:
            target_param = TargetParameters(
                user_id="test_user",
                parameter_name=f"test_{value}%_10d",
                target_return_percentage=decimal_value,
                time_horizon_days=10,
                risk_tolerance="medium",
                is_active=True
            )
            
            db.add(target_param)
            db.commit()
            db.refresh(target_param)
            
            print(f"   ✅ TargetParameters créé: ID={target_param.id}")
            print(f"   📊 target_return_percentage: {target_param.target_return_percentage} (type: {type(target_param.target_return_percentage)})")
            
            # Vérifier le nom du modèle qui serait généré
            model_name = f"classification_TEST_target_TEST_{target_param.target_return_percentage}%_{target_param.time_horizon_days}d"
            print(f"   🤖 Nom du modèle: {model_name}")
            
            # Nettoyer
            db.delete(target_param)
            db.commit()
            
        except Exception as e:
            print(f"   ❌ Erreur: {str(e)}")
        finally:
            db.close()
        
        print()

if __name__ == "__main__":
    print("🚀 Démarrage du test de conversion Decimal")
    
    test_decimal_conversion()
    
    print("\n🏁 Test terminé")
