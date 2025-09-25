#!/usr/bin/env python3
"""
Script pour corriger les problèmes de sérialisation NumPy
"""

import numpy as np

def convert_numpy_types(obj):
    """Convertit les types NumPy en types Python natifs pour la sérialisation"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj

# Test de la fonction
if __name__ == "__main__":
    # Test avec différents types NumPy
    test_data = {
        "accuracy": np.float64(0.95),
        "f1_score": np.float32(0.87),
        "training_time": np.int64(120),
        "predictions": np.array([1, 0, 1, 0]),
        "nested": {
            "value": np.float64(0.5),
            "array": np.array([1, 2, 3])
        }
    }
    
    print("Données originales:", test_data)
    converted = convert_numpy_types(test_data)
    print("Données converties:", converted)
    print("Types:", {k: type(v) for k, v in converted.items()})
