#!/usr/bin/env python3
"""
Test simple d'import de LightGBM
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_lightgbm_import():
    """Test simple d'import de LightGBM"""
    print("🧪 Test d'import de LightGBM...")
    
    try:
        import lightgbm as lgb
        print("✅ LightGBM importé avec succès")
        print(f"   - Version: {lgb.__version__}")
        
        # Test de création d'un dataset simple
        import numpy as np
        X = np.random.rand(100, 10)
        y = np.random.randint(0, 2, 100)
        
        train_data = lgb.Dataset(X, label=y)
        print("✅ Dataset LightGBM créé avec succès")
        
        # Test de création d'un modèle simple
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'verbose': -1
        }
        
        model = lgb.train(params, train_data, num_boost_round=10)
        print("✅ Modèle LightGBM créé avec succès")
        
        # Test de prédiction
        prediction = model.predict(X[:5])
        print(f"✅ Prédiction effectuée: {prediction}")
        
        print("🎉 Tous les tests LightGBM ont réussi!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test LightGBM: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lightgbm_import()
