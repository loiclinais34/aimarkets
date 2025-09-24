#!/usr/bin/env python3
"""
Script de test pour diagnostiquer les erreurs de prédiction
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.services.ml_service import MLService
from app.models.database import MLModels
from datetime import date

def test_prediction():
    """Tester une prédiction pour diagnostiquer les erreurs"""
    db = SessionLocal()
    
    try:
        # Récupérer un modèle actif qui correspond aux paramètres du screener
        from app.models.database import TargetParameters
        model = db.query(MLModels).join(TargetParameters).filter(
            MLModels.is_active == True,
            MLModels.symbol == "AAPL",
            TargetParameters.target_return_percentage == 1.0,
            TargetParameters.time_horizon_days == 14
        ).first()
        
        if not model:
            print("❌ Aucun modèle AAPL trouvé")
            return
        
        print(f"✅ Modèle trouvé: {model.model_name} (ID: {model.id})")
        
        # Tester la prédiction
        ml_service = MLService(db)
        result = ml_service.predict(
            symbol="AAPL",
            model_id=model.id,
            date=date.today(),
            db=db
        )
        
        print(f"📊 Résultat prédiction: {result}")
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
    
    finally:
        db.close()

if __name__ == "__main__":
    test_prediction()
