#!/usr/bin/env python3
"""
Script pour tester directement le screener ML sans Celery
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.tasks.full_screener_ml_web_tasks import MLWebService
from app.models.schemas import ScreenerRequest
from datetime import datetime, date

def test_screener_without_celery():
    """Tester le screener sans Celery"""
    print("🔧 Test du screener ML sans Celery...")
    
    db = SessionLocal()
    try:
        # Créer une requête de test
        request = ScreenerRequest(
            target_return_percentage=2.0,
            time_horizon_days=14,
            risk_tolerance=0.6
        )
        
        print(f"✅ Requête créée: {request}")
        
        # Créer le service ML
        ml_service = MLWebService()
        print("✅ MLWebService créé")
        
        # Récupérer les symboles (limité à 3 pour le test)
        symbols = ml_service.get_active_symbols(db, limit=3)
        print(f"📊 Symboles récupérés: {symbols}")
        
        if not symbols:
            print("❌ Aucun symbole trouvé")
            return
        
        # Phase 1: Entraînement des modèles
        print("🚀 Phase 1: Entraînement des modèles...")
        successful_models = 0
        
        for i, symbol in enumerate(symbols):
            print(f"🔧 Entraînement {symbol} ({i+1}/{len(symbols)})...")
            
            try:
                # Créer les paramètres cibles
                target_param = ml_service.create_target_parameter(db, symbol, request, "test_user")
                print(f"✅ Target parameter créé pour {symbol}: {target_param.id}")
                
                # Entraîner le modèle
                success = ml_service.train_model_for_symbol(db, symbol, target_param)
                if success:
                    successful_models += 1
                    print(f"✅ Modèle entraîné avec succès pour {symbol}")
                else:
                    print(f"❌ Échec de l'entraînement pour {symbol}")
                    
            except Exception as e:
                print(f"❌ Erreur pour {symbol}: {e}")
                continue
        
        print(f"📊 Résultat entraînement: {successful_models}/{len(symbols)} modèles")
        
        # Phase 2: Prédictions
        if successful_models > 0:
            print("🚀 Phase 2: Prédictions...")
            opportunities_found = 0
            
            # Récupérer les modèles entraînés
            from app.models.database import MLModels
            trained_models = db.query(MLModels).filter(
                MLModels.symbol.in_(symbols),
                MLModels.is_active == True
            ).all()
            
            for model in trained_models:
                try:
                    prediction_result = ml_service.predict_for_model(db, model, request)
                    if prediction_result and prediction_result.get('success'):
                        prediction = prediction_result['prediction']
                        confidence = prediction_result['confidence']
                        
                        if prediction == 1.0 and confidence >= request.risk_tolerance:
                            opportunities_found += 1
                            print(f"🎯 {model.symbol}: Opportunité trouvée! Confiance: {confidence:.1%}")
                        else:
                            print(f"⏭️ {model.symbol}: Pas d'opportunité (Confiance: {confidence:.1%})")
                    else:
                        print(f"❌ {model.symbol}: Échec de la prédiction")
                        
                except Exception as e:
                    print(f"❌ Erreur prédiction pour {model.symbol}: {e}")
                    continue
            
            print(f"🎉 Screener terminé: {opportunities_found} opportunités trouvées")
        else:
            print("❌ Aucun modèle entraîné - impossible de faire des prédictions")
            
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_screener_without_celery()
