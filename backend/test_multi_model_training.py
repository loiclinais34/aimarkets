#!/usr/bin/env python3
"""
Script de test pour entraîner des modèles multi-algorithmes (RandomForest, XGBoost, LightGBM)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.ml_service import MLService
from app.models.database import TargetParameters
from sqlalchemy.orm import Session

def test_multi_model_training():
    """Test d'entraînement de modèles multi-algorithmes"""
    
    # Obtenir une session de base de données
    db = next(get_db())
    ml_service = MLService(db=db)
    
    # Symboles de test
    test_symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    # Paramètres de test
    target_return = 5.0
    time_horizon = 30
    
    print("🚀 Début du test d'entraînement multi-modèles")
    print(f"📊 Symboles: {', '.join(test_symbols)}")
    print(f"🎯 Objectif: {target_return}% sur {time_horizon} jours")
    print()
    
    results = {}
    
    for symbol in test_symbols:
        print(f"\n{'='*50}")
        print(f"🤖 Entraînement pour {symbol}")
        print(f"{'='*50}")
        
        try:
            # Créer ou récupérer les paramètres cibles
            target_param = db.query(TargetParameters).filter(
                TargetParameters.target_return_percentage == target_return,
                TargetParameters.time_horizon_days == time_horizon
            ).first()
            
            if not target_param:
                print(f"⚠️ Paramètres cibles non trouvés pour {target_return}%/{time_horizon}d")
                continue
            
            # Entraîner plusieurs modèles
            training_results = ml_service.train_multiple_models(
                symbol=symbol,
                target_param=target_param,
                algorithms=['RandomForest', 'XGBoost', 'LightGBM'],
                db=db
            )
            
            results[symbol] = training_results
            
            print(f"\n📈 Résultats pour {symbol}:")
            for algorithm, result in training_results.items():
                if "error" not in result:
                    print(f"  ✅ {algorithm}: Accuracy={result['accuracy']:.3f}, F1={result['f1_score']:.3f}")
                else:
                    print(f"  ❌ {algorithm}: {result['error']}")
                    
        except Exception as e:
            print(f"❌ Erreur pour {symbol}: {str(e)}")
            continue
    
    print(f"\n{'='*50}")
    print("📊 RÉSUMÉ DES RÉSULTATS")
    print(f"{'='*50}")
    
    for symbol, training_results in results.items():
        print(f"\n{symbol}:")
        for algorithm, result in training_results.items():
            if "error" not in result:
                print(f"  {algorithm}: Model ID {result['model_id']}, Accuracy {result['accuracy']:.3f}")
    
    print(f"\n✅ Test terminé ! {len(results)} symboles traités")
    
    return results

if __name__ == "__main__":
    test_multi_model_training()
