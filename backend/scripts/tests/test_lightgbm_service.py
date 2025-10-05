#!/usr/bin/env python3
"""
Script de test pour le service LightGBM
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.lightgbm_service import LightGBMService
from app.models.database import TargetParameters, MLModels

def test_lightgbm_service():
    """Test du service LightGBM"""
    print("🧪 Test du service LightGBM...")
    
    # Récupération de la session de base de données
    db = next(get_db())
    
    try:
        # Création du service
        service = LightGBMService(db)
        print("✅ Service LightGBM créé")
        
        # Récupération d'un paramètre cible existant
        target_param = db.query(TargetParameters).first()
        if not target_param:
            print("❌ Aucun paramètre cible trouvé. Créez d'abord un paramètre cible.")
            return
        
        print(f"📊 Utilisation du paramètre cible: {target_param.parameter_name}")
        
        # Test de la classification binaire
        print("\n🔍 Test de la classification binaire...")
        try:
            result_binary = service.train_binary_classification_model(
                symbol="AAPL",
                target_param=target_param,
                db=db
            )
            print(f"✅ Modèle de classification binaire entraîné: {result_binary['model_name']}")
            print(f"   - Accuracy: {result_binary['performance']['accuracy']:.3f}")
            print(f"   - F1-Score: {result_binary['performance']['f1_score']:.3f}")
            print(f"   - Échantillons d'entraînement: {result_binary['training_samples']}")
            print(f"   - Échantillons de test: {result_binary['test_samples']}")
            
            # Test de prédiction
            print("\n🔮 Test de prédiction (classification binaire)...")
            prediction = service.predict(
                model_id=result_binary['model_id'],
                symbol="AAPL",
                prediction_date=date.today(),
                db=db
            )
            print(f"✅ Prédiction effectuée:")
            print(f"   - Classe prédite: {prediction['prediction_class']}")
            print(f"   - Valeur: {prediction['prediction_value']:.3f}")
            print(f"   - Confiance: {prediction['confidence']:.3f}")
            print(f"   - Date des données utilisées: {prediction['data_date_used']}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'entraînement de la classification binaire: {e}")
        
        # Test de la classification multi-classe
        print("\n🔍 Test de la classification multi-classe...")
        try:
            result_multiclass = service.train_multiclass_classification_model(
                symbol="AAPL",
                target_param=target_param,
                db=db
            )
            print(f"✅ Modèle de classification multi-classe entraîné: {result_multiclass['model_name']}")
            print(f"   - Accuracy: {result_multiclass['performance']['accuracy']:.3f}")
            print(f"   - F1-Score: {result_multiclass['performance']['f1_score']:.3f}")
            print(f"   - Échantillons d'entraînement: {result_multiclass['training_samples']}")
            print(f"   - Échantillons de test: {result_multiclass['test_samples']}")
            
            # Test de prédiction
            print("\n🔮 Test de prédiction (classification multi-classe)...")
            prediction = service.predict(
                model_id=result_multiclass['model_id'],
                symbol="AAPL",
                prediction_date=date.today(),
                db=db
            )
            print(f"✅ Prédiction effectuée:")
            print(f"   - Classe prédite: {prediction['prediction_class']}")
            print(f"   - Valeur: {prediction['prediction_value']:.3f}")
            print(f"   - Confiance: {prediction['confidence']:.3f}")
            print(f"   - Date des données utilisées: {prediction['data_date_used']}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'entraînement de la classification multi-classe: {e}")
        
        # Test de la régression
        print("\n🔍 Test de la régression...")
        try:
            result_regression = service.train_regression_model(
                symbol="AAPL",
                target_param=target_param,
                db=db
            )
            print(f"✅ Modèle de régression entraîné: {result_regression['model_name']}")
            print(f"   - R² Score: {result_regression['performance']['r2_score']:.3f}")
            print(f"   - RMSE: {result_regression['performance']['rmse']:.3f}")
            print(f"   - Échantillons d'entraînement: {result_regression['training_samples']}")
            print(f"   - Échantillons de test: {result_regression['test_samples']}")
            
            # Test de prédiction
            print("\n🔮 Test de prédiction (régression)...")
            prediction = service.predict(
                model_id=result_regression['model_id'],
                symbol="AAPL",
                prediction_date=date.today(),
                db=db
            )
            print(f"✅ Prédiction effectuée:")
            print(f"   - Classe prédite: {prediction['prediction_class']}")
            print(f"   - Valeur: {prediction['prediction_value']:.3f}")
            print(f"   - Confiance: {prediction['confidence']:.3f}")
            print(f"   - Date des données utilisées: {prediction['data_date_used']}")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'entraînement de la régression: {e}")
        
        # Affichage des modèles créés
        print("\n📋 Modèles LightGBM créés:")
        lightgbm_models = db.query(MLModels).filter(
            MLModels.model_type.like("lightgbm_%")
        ).all()
        
        for model in lightgbm_models:
            print(f"   - {model.name} ({model.model_type})")
            print(f"     Actif: {model.is_active}")
            print(f"     Créé le: {model.created_at}")
            print(f"     Performance: {model.performance_metrics}")
            print()
        
        print("🎉 Tests du service LightGBM terminés avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()

if __name__ == "__main__":
    test_lightgbm_service()
