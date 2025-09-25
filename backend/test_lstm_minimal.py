#!/usr/bin/env python3
"""
Test Minimal LSTM
==================
"""

import sys
import os

# Ajouter le chemin du backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_tensorflow():
    """Test simple de TensorFlow"""
    try:
        import tensorflow as tf
        print(f"✅ TensorFlow version: {tf.__version__}")
        return True
    except ImportError as e:
        print(f"❌ TensorFlow non disponible: {e}")
        return False

def test_lstm_import():
    """Test d'import de notre classe LSTM"""
    try:
        from app.services.model_comparison_framework import LSTMModel, TENSORFLOW_AVAILABLE
        print(f"✅ LSTMModel importé avec succès")
        print(f"✅ TENSORFLOW_AVAILABLE: {TENSORFLOW_AVAILABLE}")
        return True
    except ImportError as e:
        print(f"❌ Erreur d'import LSTMModel: {e}")
        return False

def test_lstm_creation():
    """Test de création d'un modèle LSTM"""
    try:
        from app.services.model_comparison_framework import LSTMModel
        
        lstm = LSTMModel(
            name="TestLSTM",
            parameters={
                'sequence_length': 30,
                'lstm_units': [64, 32],
                'dropout_rate': 0.2,
                'learning_rate': 0.001,
                'epochs': 5,
                'batch_size': 16
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
    print("🧪 Tests LSTM Minimaux")
    print("=" * 30)
    
    tests = [
        ("TensorFlow", test_tensorflow),
        ("Import LSTM", test_lstm_import),
        ("Création LSTM", test_lstm_creation)
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
