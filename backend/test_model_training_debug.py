#!/usr/bin/env python3
"""
Script de debug pour l'entraînement des modèles
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.ml_service import MLService
from app.models.database import TargetParameters, SymbolMetadata
from decimal import Decimal

def test_model_training_debug():
    """Test de debug pour l'entraînement des modèles"""
    
    print("🔍 Debug de l'entraînement des modèles")
    print("=" * 60)
    
    db = next(get_db())
    try:
        # Récupérer un symbole pour le test
        symbol_record = db.query(SymbolMetadata).first()
        if not symbol_record:
            print("❌ Aucun symbole trouvé dans la base de données")
            return
        
        symbol = symbol_record.symbol
        print(f"🎯 Test avec le symbole: {symbol}")
        
        # Créer des paramètres de cible
        target_param = TargetParameters(
            user_id="debug_user",
            parameter_name=f"debug_{symbol}_5.0%_10d",
            target_return_percentage=Decimal("5.0"),
            time_horizon_days=10,
            risk_tolerance="medium",
            is_active=True
        )
        
        db.add(target_param)
        db.commit()
        db.refresh(target_param)
        
        print(f"✅ Paramètres créés: ID={target_param.id}")
        
        # Initialiser le service ML
        ml_service = MLService(db=db)
        
        # Tester la création des données d'entraînement
        print(f"\n📊 Création des données d'entraînement...")
        df = ml_service.create_labels_for_training(symbol, target_param, db)
        
        if df.empty:
            print("❌ Aucune donnée d'entraînement créée")
            return
        
        print(f"✅ {len(df)} échantillons d'entraînement créés")
        print(f"📊 Échantillons positifs: {df['target_achieved'].sum()}")
        print(f"📊 Taux de positifs: {df['target_achieved'].mean()*100:.1f}%")
        
        # Tester l'entraînement d'un modèle
        print(f"\n🤖 Test d'entraînement RandomForest...")
        result = ml_service.train_classification_model(symbol, target_param, db)
        
        if "error" in result:
            print(f"❌ Erreur d'entraînement: {result['error']}")
        else:
            print(f"✅ Modèle entraîné avec succès")
            print(f"   Accuracy: {result.get('accuracy', 0):.3f}")
            print(f"   F1 Score: {result.get('f1_score', 0):.3f}")
            print(f"   Model ID: {result.get('model_id', 'N/A')}")
        
        # Tester l'entraînement multiple
        print(f"\n🤖 Test d'entraînement multiple...")
        results = ml_service.train_multiple_models(
            symbol=symbol,
            target_param=target_param,
            algorithms=['RandomForest'],
            db=db
        )
        
        print(f"📊 Résultats d'entraînement multiple:")
        for algorithm, result in results.items():
            if "error" in result:
                print(f"   ❌ {algorithm}: {result['error']}")
            else:
                print(f"   ✅ {algorithm}: Accuracy={result.get('accuracy', 0):.3f}")
        
        # Vérifier les modèles en base
        print(f"\n📋 Vérification des modèles en base...")
        from app.models.database import MLModels
        models = db.query(MLModels).filter(
            MLModels.symbol == symbol,
            MLModels.target_parameter_id == target_param.id
        ).all()
        
        print(f"📊 {len(models)} modèles trouvés pour {symbol}")
        for model in models:
            print(f"   🤖 {model.model_name}")
            print(f"      Type: {model.model_type}")
            print(f"      Actif: {model.is_active}")
            print(f"      Performance: {model.performance_metrics}")
        
    finally:
        db.close()

def test_prediction_debug():
    """Test de debug pour les prédictions"""
    
    print(f"\n🔍 Debug des prédictions")
    print("-" * 40)
    
    db = next(get_db())
    try:
        from app.models.database import MLModels
        from datetime import date
        
        # Récupérer un modèle actif
        model = db.query(MLModels).filter(
            MLModels.is_active == True
        ).first()
        
        if not model:
            print("❌ Aucun modèle actif trouvé")
            return
        
        print(f"🎯 Test de prédiction avec: {model.model_name}")
        print(f"   Symbole: {model.symbol}")
        print(f"   Type: {model.model_type}")
        
        # Initialiser le service ML
        ml_service = MLService(db=db)
        
        # Tester la prédiction
        print(f"\n🔮 Test de prédiction...")
        prediction_result = ml_service.predict(
            symbol=model.symbol,
            model_id=model.id,
            date=date.today(),
            db=db
        )
        
        if prediction_result and "error" not in prediction_result:
            print(f"✅ Prédiction réussie")
            print(f"   Prédiction: {prediction_result.get('prediction', 'N/A')}")
            print(f"   Confiance: {prediction_result.get('confidence', 'N/A'):.1%}")
        else:
            print(f"❌ Erreur de prédiction: {prediction_result.get('error', 'Erreur inconnue') if prediction_result else 'Pas de résultat'}")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Démarrage du debug de l'entraînement des modèles")
    
    test_model_training_debug()
    test_prediction_debug()
    
    print("\n🏁 Debug terminé")
