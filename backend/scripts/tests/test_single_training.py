#!/usr/bin/env python3
"""
Test d'entraînement d'un seul modèle pour debug
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.services.ml_service import MLService
from app.models.database import TargetParameters, SymbolMetadata
from decimal import Decimal

def test_single_model_training():
    """Test l'entraînement d'un seul modèle"""
    
    # Obtenir une session de base de données
    db = next(get_db())
    ml_service = MLService(db=db)
    
    try:
        # Prendre le premier symbole disponible
        symbol_metadata = db.query(SymbolMetadata).filter(
            SymbolMetadata.is_active == True
        ).first()
        
        if not symbol_metadata:
            print("❌ Aucun symbole disponible")
            return False
        
        symbol = symbol_metadata.symbol
        print(f"🧪 Test d'entraînement pour {symbol} ({symbol_metadata.company_name})")
        
        # Créer ou récupérer les paramètres cibles
        target_param = db.query(TargetParameters).filter(
            TargetParameters.user_id == "test_screener",
            TargetParameters.parameter_name.like(f"%{symbol}%")
        ).first()
        
        if not target_param:
            print(f"📋 Création des paramètres cibles pour {symbol}")
            target_param = TargetParameters(
                user_id="test_screener",
                parameter_name=f"target_{symbol}_1.5%_7d",
                target_return_percentage=Decimal("1.5"),
                time_horizon_days=7,
                risk_tolerance="medium",
                is_active=True
            )
            db.add(target_param)
            db.commit()
            db.refresh(target_param)
        
        print(f"🎯 Paramètres cibles: ID={target_param.id}")
        
        # Tenter l'entraînement
        print(f"🚀 Entraînement du modèle de classification...")
        result = ml_service.train_classification_model(
            symbol=symbol,
            target_param=target_param,
            db=db
        )
        
        if result and "model_id" in result:
            print(f"✅ Modèle entraîné avec succès!")
            print(f"   - ID: {result['model_id']}")
            print(f"   - Nom: {result['model_name']}")
            print(f"   - Performance: {result.get('performance_metrics', {})}")
            return True
        else:
            print(f"❌ Échec de l'entraînement")
            print(f"   - Résultat: {result}")
            return False
            
    except Exception as e:
        print(f"💥 Erreur lors de l'entraînement: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🧪 Test d'entraînement d'un modèle unique")
    print("=" * 50)
    
    success = test_single_model_training()
    
    if success:
        print("\n🎉 Test réussi!")
    else:
        print("\n💥 Test échoué!")
        sys.exit(1)
