#!/usr/bin/env python3
"""
Script de test pour simuler la logique du screener
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.database import MLModels, SymbolMetadata
from app.services.ml_service import MLService
from app.models.schemas import ScreenerRequest
from decimal import Decimal

def test_screener_logic():
    """Test de la logique du screener"""
    
    print("🔍 Test de la logique du screener")
    print("=" * 60)
    
    # Paramètres de test
    target_return_percentage = 5.0
    time_horizon_days = 10
    risk_tolerance = 0.5
    confidence_threshold = 0.7
    
    print(f"📊 Paramètres de test:")
    print(f"  - Rendement attendu: {target_return_percentage}%")
    print(f"  - Horizon temporel: {time_horizon_days} jours")
    print(f"  - Tolérance au risque: {risk_tolerance}")
    print(f"  - Seuil de confiance: {confidence_threshold}")
    
    db = next(get_db())
    try:
        # Récupérer quelques symboles
        symbols = db.query(SymbolMetadata.symbol).filter(
            SymbolMetadata.is_active == True
        ).limit(3).all()
        
        symbol_list = [s[0] for s in symbols]
        print(f"\n🎯 Symboles de test: {symbol_list}")
        
        # Simuler l'entraînement des modèles
        ml_service = MLService(db=db)
        successful_models = 0
        
        for symbol in symbol_list:
            print(f"\n🤖 Entraînement pour {symbol}...")
            
            # Créer des paramètres de cible
            from app.models.database import TargetParameters
            target_param = TargetParameters(
                user_id="test_user",
                parameter_name=f"test_{symbol}_{target_return_percentage}%_{time_horizon_days}d",
                target_return_percentage=Decimal(str(target_return_percentage)),
                time_horizon_days=time_horizon_days,
                risk_tolerance="medium",
                is_active=True
            )
            
            db.add(target_param)
            db.commit()
            db.refresh(target_param)
            
            print(f"   ✅ Paramètres créés: ID={target_param.id}")
            
            # Entraîner un modèle
            result = ml_service.train_classification_model(symbol, target_param, db)
            
            if "error" not in result:
                successful_models += 1
                print(f"   ✅ Modèle entraîné: {result.get('model_name', 'N/A')}")
                print(f"      Accuracy: {result.get('accuracy', 0):.3f}")
            else:
                print(f"   ❌ Erreur: {result['error']}")
        
        print(f"\n📊 {successful_models}/{len(symbol_list)} modèles entraînés avec succès")
        
        # Simuler la récupération des modèles pour les prédictions
        print(f"\n🔍 Récupération des modèles pour les prédictions...")
        
        # Récupérer les modèles avec les paramètres spécifiques
        active_models = db.query(MLModels).filter(
            MLModels.is_active == True,
            MLModels.symbol.in_(symbol_list)
        ).all()
        
        print(f"📊 {len(active_models)} modèles actifs trouvés")
        
        # Filtrer par les paramètres de la recherche
        filtered_models = []
        for model in active_models:
            params = model.model_parameters
            if params and isinstance(params, dict):
                model_target_return = params.get('target_return_percentage')
                model_time_horizon = params.get('time_horizon_days')
                
                print(f"   🤖 {model.model_name}")
                print(f"      Paramètres: {model_target_return}% sur {model_time_horizon} jours")
                
                # Vérifier si les paramètres correspondent
                if (str(model_target_return) == str(target_return_percentage) and 
                    model_time_horizon == time_horizon_days):
                    filtered_models.append(model)
                    print(f"      ✅ Correspond aux paramètres de recherche")
                else:
                    print(f"      ❌ Ne correspond pas aux paramètres de recherche")
        
        print(f"\n🎯 {len(filtered_models)} modèles trouvés avec les paramètres {target_return_percentage}% sur {time_horizon_days} jours")
        
        # Simuler les prédictions
        if filtered_models:
            print(f"\n🔮 Simulation des prédictions...")
            
            opportunities_found = 0
            from datetime import date
            today = date.today()
            
            for model in filtered_models:
                print(f"\n   🤖 Prédiction pour {model.symbol}...")
                
                # Faire une prédiction
                prediction_result = ml_service.predict(
                    symbol=model.symbol,
                    model_id=model.id,
                    date=today,
                    db=db
                )
                
                if prediction_result and "error" not in prediction_result:
                    prediction = prediction_result["prediction"]
                    confidence = prediction_result["confidence"]
                    
                    print(f"      Prédiction: {prediction}")
                    print(f"      Confiance: {confidence:.1%}")
                    
                    # Vérifier si c'est une opportunité
                    if prediction == 1.0 and confidence >= confidence_threshold:
                        opportunities_found += 1
                        print(f"      ✅ OPPORTUNITÉ DÉTECTÉE!")
                    else:
                        print(f"      ❌ Pas d'opportunité (Confiance: {confidence:.1%}, Seuil: {confidence_threshold:.1%})")
                else:
                    print(f"      ❌ Erreur de prédiction: {prediction_result.get('error', 'Erreur inconnue') if prediction_result else 'Pas de résultat'}")
            
            print(f"\n🎉 {opportunities_found} opportunités trouvées sur {len(filtered_models)} modèles")
        else:
            print(f"\n❌ Aucun modèle trouvé pour les prédictions")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Démarrage du test de la logique du screener")
    
    test_screener_logic()
    
    print("\n🏁 Test terminé")
