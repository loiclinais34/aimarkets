#!/usr/bin/env python3
"""
Script de test pour détecter des opportunités avec des paramètres plus permissifs
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.ml_service import MLService
from app.models.database import TargetParameters, SymbolMetadata
from decimal import Decimal
from datetime import date

def test_opportunity_detection():
    """Test de détection d'opportunités avec des paramètres permissifs"""
    
    print("🔍 Test de détection d'opportunités")
    print("=" * 60)
    
    # Paramètres plus permissifs pour trouver des opportunités
    target_return_percentage = 1.0  # 1% au lieu de 5%
    time_horizon_days = 30  # 30 jours au lieu de 10
    confidence_threshold = 0.5  # 50% au lieu de 70%
    
    print(f"📊 Paramètres permissifs:")
    print(f"  - Rendement attendu: {target_return_percentage}%")
    print(f"  - Horizon temporel: {time_horizon_days} jours")
    print(f"  - Seuil de confiance: {confidence_threshold:.1%}")
    
    db = next(get_db())
    try:
        # Récupérer quelques symboles
        symbols = db.query(SymbolMetadata.symbol).filter(
            SymbolMetadata.is_active == True
        ).limit(5).all()
        
        symbol_list = [s[0] for s in symbols]
        print(f"\n🎯 Symboles de test: {symbol_list}")
        
        # Initialiser le service ML
        ml_service = MLService(db=db)
        opportunities_found = 0
        
        for symbol in symbol_list:
            print(f"\n🤖 Test pour {symbol}...")
            
            # Créer des paramètres de cible
            target_param = TargetParameters(
                user_id="test_opportunity_user",
                parameter_name=f"test_opportunity_{symbol}_{target_return_percentage}%_{time_horizon_days}d",
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
                model_id = result.get('model_id')
                print(f"   ✅ Modèle entraîné: {result.get('model_name', 'N/A')}")
                print(f"      Accuracy: {result.get('accuracy', 0):.3f}")
                
                # Faire une prédiction
                prediction_result = ml_service.predict(
                    symbol=symbol,
                    model_id=model_id,
                    date=date.today(),
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
                        print(f"      🎉 OPPORTUNITÉ DÉTECTÉE!")
                    else:
                        print(f"      ❌ Pas d'opportunité (Confiance: {confidence:.1%}, Seuil: {confidence_threshold:.1%})")
                else:
                    print(f"      ❌ Erreur de prédiction: {prediction_result.get('error', 'Erreur inconnue') if prediction_result else 'Pas de résultat'}")
            else:
                print(f"   ❌ Erreur d'entraînement: {result['error']}")
        
        print(f"\n🎉 {opportunities_found} opportunités trouvées sur {len(symbol_list)} symboles")
        
        # Vérifier les modèles en base avec ces paramètres
        print(f"\n📋 Vérification des modèles en base...")
        from app.models.database import MLModels
        models = db.query(MLModels).filter(
            MLModels.is_active == True,
            MLModels.symbol.in_(symbol_list)
        ).all()
        
        matching_models = []
        for model in models:
            params = model.model_parameters
            if params and isinstance(params, dict):
                model_target_return = params.get('target_return_percentage')
                model_time_horizon = params.get('time_horizon_days')
                
                if (str(model_target_return) == str(target_return_percentage) and 
                    model_time_horizon == time_horizon_days):
                    matching_models.append(model)
        
        print(f"📊 {len(matching_models)} modèles trouvés avec les paramètres {target_return_percentage}% sur {time_horizon_days} jours")
        
        for model in matching_models:
            print(f"   🤖 {model.model_name}")
            print(f"      Symbole: {model.symbol}")
            print(f"      Performance: {model.performance_metrics}")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Démarrage du test de détection d'opportunités")
    
    test_opportunity_detection()
    
    print("\n🏁 Test terminé")
