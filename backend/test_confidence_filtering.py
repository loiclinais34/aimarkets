#!/usr/bin/env python3
"""
Script de test pour vérifier la logique de filtrage par confiance
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.database import MLModels, ScreenerResult
from sqlalchemy.orm import Session

def test_confidence_filtering():
    """Test de la logique de filtrage par confiance"""
    
    print("🔍 Test de la logique de filtrage par confiance")
    print("=" * 60)
    
    db = next(get_db())
    try:
        # Récupérer quelques modèles récents
        recent_models = db.query(MLModels).filter(
            MLModels.is_active == True
        ).limit(5).all()
        
        print(f"📊 {len(recent_models)} modèles récents trouvés")
        
        for model in recent_models:
            print(f"\n🤖 Modèle: {model.model_name}")
            print(f"   Symbole: {model.symbol}")
            print(f"   Type: {model.model_type}")
            
            # Simuler une prédiction
            confidence = 0.85  # 85% de confiance
            prediction = 1.0   # Prédiction positive
            
            print(f"   Prédiction simulée: {prediction}")
            print(f"   Confiance simulée: {confidence:.1%}")
            
            # Test avec différents seuils de confiance
            thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
            
            for threshold in thresholds:
                is_opportunity = prediction == 1.0 and confidence >= threshold
                status = "✅ OPPORTUNITÉ" if is_opportunity else "❌ Rejetée"
                print(f"   Seuil {threshold:.1%}: {status}")
        
        # Vérifier les résultats de screener existants
        print(f"\n📋 Vérification des résultats de screener existants")
        screener_results = db.query(ScreenerResult).limit(10).all()
        
        print(f"📊 {len(screener_results)} résultats de screener trouvés")
        
        for result in screener_results:
            print(f"\n🎯 {result.symbol}")
            print(f"   Prédiction: {result.prediction}")
            print(f"   Confiance: {result.confidence:.1%}")
            print(f"   Rang: #{result.rank}")
            
            # Vérifier si ce résultat passerait les filtres
            thresholds = [0.5, 0.6, 0.7, 0.8, 0.9]
            
            for threshold in thresholds:
                would_pass = result.prediction == 1.0 and result.confidence >= threshold
                status = "✅ Passerait" if would_pass else "❌ Rejeté"
                print(f"   Seuil {threshold:.1%}: {status}")
        
        # Statistiques des confiances
        print(f"\n📊 Statistiques des confiances")
        all_confidences = [r.confidence for r in screener_results]
        
        if all_confidences:
            avg_confidence = sum(all_confidences) / len(all_confidences)
            min_confidence = min(all_confidences)
            max_confidence = max(all_confidences)
            
            print(f"   Confiance moyenne: {avg_confidence:.1%}")
            print(f"   Confiance minimale: {min_confidence:.1%}")
            print(f"   Confiance maximale: {max_confidence:.1%}")
            
            # Compter les opportunités par seuil
            for threshold in [0.5, 0.6, 0.7, 0.8, 0.9]:
                count = sum(1 for r in screener_results 
                           if r.prediction == 1.0 and r.confidence >= threshold)
                print(f"   Seuil {threshold:.1%}: {count} opportunités")
        
    finally:
        db.close()

def test_prediction_logic():
    """Test de la logique de prédiction"""
    
    print(f"\n🧮 Test de la logique de prédiction")
    print("-" * 40)
    
    # Simuler différents scénarios
    scenarios = [
        {"prediction": 1.0, "confidence": 0.95, "threshold": 0.7, "expected": True},
        {"prediction": 1.0, "confidence": 0.65, "threshold": 0.7, "expected": False},
        {"prediction": 0.0, "confidence": 0.95, "threshold": 0.7, "expected": False},
        {"prediction": 1.0, "confidence": 0.75, "threshold": 0.7, "expected": True},
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        prediction = scenario["prediction"]
        confidence = scenario["confidence"]
        threshold = scenario["threshold"]
        expected = scenario["expected"]
        
        result = prediction == 1.0 and confidence >= threshold
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        print(f"   Scénario {i}: {status}")
        print(f"      Prédiction: {prediction}, Confiance: {confidence:.1%}, Seuil: {threshold:.1%}")
        print(f"      Résultat: {result}, Attendu: {expected}")

if __name__ == "__main__":
    print("🚀 Démarrage des tests de filtrage par confiance")
    
    test_confidence_filtering()
    test_prediction_logic()
    
    print("\n🏁 Tests terminés")
