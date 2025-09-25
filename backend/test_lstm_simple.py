#!/usr/bin/env python3
"""
Test LSTM Simple et Sécurisé
============================
"""

import sys
import os

# Ajouter le chemin du backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_tensorflow_import():
    """Test d'import TensorFlow"""
    try:
        import tensorflow as tf
        print(f"✅ TensorFlow version: {tf.__version__}")
        
        # Configurer TensorFlow pour éviter les problèmes de mutex
        tf.config.experimental.enable_memory_growth()
        tf.config.threading.set_inter_op_parallelism_threads(1)
        tf.config.threading.set_intra_op_parallelism_threads(1)
        
        print("✅ TensorFlow configuré avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur TensorFlow: {e}")
        return False

def test_lstm_import():
    """Test d'import de notre classe LSTM"""
    try:
        from app.services.model_comparison_framework import LSTMModel, TENSORFLOW_AVAILABLE
        print(f"✅ LSTMModel importé avec succès")
        print(f"✅ TENSORFLOW_AVAILABLE: {TENSORFLOW_AVAILABLE}")
        return True
    except Exception as e:
        print(f"❌ Erreur d'import LSTMModel: {e}")
        return False

def test_lstm_creation():
    """Test de création d'un modèle LSTM"""
    try:
        from app.services.model_comparison_framework import LSTMModel
        
        lstm = LSTMModel(
            name="TestLSTM",
            parameters={
                'sequence_length': 10,  # Plus court pour le test
                'lstm_units': [32],     # Plus simple
                'dropout_rate': 0.2,
                'learning_rate': 0.001,
                'epochs': 2,            # Très peu d'epochs
                'batch_size': 8,
                'verbose': 0
            }
        )
        
        print(f"✅ Modèle LSTM créé: {lstm.name}")
        print(f"   Sequence length: {lstm.sequence_length}")
        print(f"   Paramètres: {lstm.parameters}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur création LSTM: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Test LSTM Simple et Sécurisé")
    print("=" * 40)
    
    tests = [
        ("TensorFlow Import", test_tensorflow_import),
        ("LSTM Import", test_lstm_import),
        ("LSTM Création", test_lstm_creation)
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

