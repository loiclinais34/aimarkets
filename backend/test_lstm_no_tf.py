#!/usr/bin/env python3
"""
Test LSTM sans TensorFlow
=========================
"""

import sys
import os

# Ajouter le chemin du backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_lstm_import_without_tensorflow():
    """Test d'import de notre classe LSTM sans TensorFlow"""
    try:
        # Simuler que TensorFlow n'est pas disponible
        import sys
        sys.modules['tensorflow'] = None
        
        from app.services.model_comparison_framework import LSTMModel, TENSORFLOW_AVAILABLE
        print(f"✅ LSTMModel importé avec succès")
        print(f"✅ TENSORFLOW_AVAILABLE: {TENSORFLOW_AVAILABLE}")
        
        # Tester la création du modèle
        lstm = LSTMModel(
            name="TestLSTM",
            parameters={
                'sequence_length': 30,
                'lstm_units': [64, 32],
                'dropout_rate': 0.2,
                'learning_rate': 0.001,
                'epochs': 10,
                'batch_size': 16
            }
        )
        
        print(f"✅ Modèle LSTM créé: {lstm.name}")
        print(f"   Sequence length: {lstm.sequence_length}")
        print(f"   Paramètres: {lstm.parameters}")
        
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_framework_integration():
    """Test d'intégration dans le framework"""
    try:
        from app.services.model_comparison_framework import ModelComparisonFramework
        
        framework = ModelComparisonFramework()
        print("✅ Framework créé avec succès")
        
        # Vérifier que LSTM est dans les modèles par défaut
        default_models = framework.default_models
        lstm_models = [name for name in default_models.keys() if 'LSTM' in name]
        
        print(f"✅ Modèles LSTM disponibles: {lstm_models}")
        
        return True
    except Exception as e:
        print(f"❌ Erreur framework: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test LSTM sans TensorFlow")
    print("=" * 30)
    
    tests = [
        ("LSTM Import sans TF", test_lstm_import_without_tensorflow),
        ("Framework Integration", test_framework_integration)
    ]
    
    for name, test_func in tests:
        print(f"\n{name}:")
        try:
            result = test_func()
            if result:
                print(f"✅ {name}: RÉUSSI")
            else:
                print(f"❌ {name}: ÉCHEC")
        except Exception as e:
            print(f"❌ {name}: ERREUR - {e}")
    
    print("\n🎉 Test terminé!")

