#!/usr/bin/env python3
"""
Script de Test pour le Modèle LSTM
==================================

Ce script teste l'implémentation du modèle LSTM dans notre framework
de comparaison de modèles.
"""

import sys
import os
import logging
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd

# Ajouter le chemin du backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.model_comparison_service import ModelComparisonService
from app.services.model_comparison_framework import LSTMModel, TENSORFLOW_AVAILABLE

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_lstm_availability():
    """Tester la disponibilité de TensorFlow"""
    logger.info("=== Test de Disponibilité TensorFlow ===")
    
    if TENSORFLOW_AVAILABLE:
        logger.info("✅ TensorFlow est disponible")
        try:
            import tensorflow as tf
            logger.info(f"Version TensorFlow: {tf.__version__}")
            logger.info(f"GPU disponible: {tf.config.list_physical_devices('GPU')}")
            return True
        except Exception as e:
            logger.error(f"❌ Erreur TensorFlow: {e}")
            return False
    else:
        logger.error("❌ TensorFlow n'est pas disponible")
        logger.info("Installez avec: pip install tensorflow")
        return False

def test_lstm_model_creation():
    """Tester la création d'un modèle LSTM"""
    logger.info("\n=== Test de Création du Modèle LSTM ===")
    
    if not TENSORFLOW_AVAILABLE:
        logger.warning("TensorFlow non disponible, test ignoré")
        return False
    
    try:
        # Créer un modèle LSTM simple
        lstm_model = LSTMModel(
            name="TestLSTM",
            parameters={
                'sequence_length': 30,
                'lstm_units': [64, 32],
                'dropout_rate': 0.2,
                'learning_rate': 0.001,
                'epochs': 5,  # Peu d'epochs pour le test
                'batch_size': 16,
                'patience': 3
            }
        )
        
        logger.info("✅ Modèle LSTM créé avec succès")
        logger.info(f"Sequence length: {lstm_model.sequence_length}")
        logger.info(f"Paramètres: {lstm_model.parameters}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création du modèle: {e}")
        return False

def test_lstm_with_synthetic_data():
    """Tester LSTM avec des données synthétiques"""
    logger.info("\n=== Test LSTM avec Données Synthétiques ===")
    
    if not TENSORFLOW_AVAILABLE:
        logger.warning("TensorFlow non disponible, test ignoré")
        return False
    
    try:
        # Créer des données synthétiques
        np.random.seed(42)
        n_samples = 1000
        n_features = 10
        
        # Données temporelles avec patterns
        dates = pd.date_range(start='2020-01-01', periods=n_samples, freq='D')
        
        # Features avec tendance et saisonnalité
        X_data = np.random.randn(n_samples, n_features)
        
        # Ajouter une tendance temporelle
        trend = np.linspace(0, 2, n_samples).reshape(-1, 1)
        X_data[:, 0] += trend.flatten()
        
        # Ajouter de la saisonnalité
        seasonal = np.sin(2 * np.pi * np.arange(n_samples) / 30).reshape(-1, 1)
        X_data[:, 1] += seasonal.flatten()
        
        # Target avec dépendance temporelle
        y_data = np.zeros(n_samples)
        for i in range(30, n_samples):
            # Signal basé sur les moyennes mobiles
            ma_short = np.mean(X_data[i-5:i, 0])
            ma_long = np.mean(X_data[i-20:i, 0])
            
            if ma_short > ma_long and X_data[i, 1] > 0:
                y_data[i] = 1
        
        # Créer DataFrame
        feature_names = [f'feature_{i}' for i in range(n_features)]
        X_df = pd.DataFrame(X_data, columns=feature_names, index=dates)
        y_series = pd.Series(y_data, index=dates)
        
        logger.info(f"Données créées: {X_df.shape}, Target: {y_series.shape}")
        logger.info(f"Proportion de classe 1: {y_series.mean():.3f}")
        
        # Diviser en train/test
        split_idx = int(0.8 * len(X_df))
        X_train = X_df[:split_idx]
        y_train = y_series[:split_idx]
        X_test = X_df[split_idx:]
        y_test = y_series[split_idx:]
        
        # Créer et entraîner le modèle LSTM
        lstm_model = LSTMModel(
            name="SyntheticLSTM",
            parameters={
                'sequence_length': 20,
                'lstm_units': [32, 16],
                'dropout_rate': 0.2,
                'learning_rate': 0.001,
                'epochs': 10,
                'batch_size': 16,
                'patience': 5,
                'verbose': 0
            }
        )
        
        logger.info("Début de l'entraînement LSTM...")
        training_info = lstm_model.fit(X_train, y_train, validation_split=0.2)
        
        logger.info(f"✅ Entraînement terminé:")
        logger.info(f"   Epochs: {training_info['best_epoch']}")
        logger.info(f"   Loss finale: {training_info['final_loss']:.4f}")
        logger.info(f"   Val Loss: {training_info['final_val_loss']:.4f}")
        logger.info(f"   Accuracy finale: {training_info['final_accuracy']:.4f}")
        
        # Prédictions
        logger.info("Génération des prédictions...")
        y_pred = lstm_model.predict(X_test)
        y_pred_proba = lstm_model.predict_proba(X_test)
        
        # Métriques
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        # Ajuster pour la séquence
        y_test_adjusted = y_test[lstm_model.sequence_length:]
        y_pred_adjusted = y_pred[lstm_model.sequence_length:]
        
        accuracy = accuracy_score(y_test_adjusted, (y_pred_adjusted > 0.5).astype(int))
        precision = precision_score(y_test_adjusted, (y_pred_adjusted > 0.5).astype(int), zero_division=0)
        recall = recall_score(y_test_adjusted, (y_pred_adjusted > 0.5).astype(int), zero_division=0)
        f1 = f1_score(y_test_adjusted, (y_pred_adjusted > 0.5).astype(int), zero_division=0)
        
        logger.info(f"✅ Métriques sur le test:")
        logger.info(f"   Accuracy: {accuracy:.4f}")
        logger.info(f"   Precision: {precision:.4f}")
        logger.info(f"   Recall: {recall:.4f}")
        logger.info(f"   F1-Score: {f1:.4f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test avec données synthétiques: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lstm_in_framework():
    """Tester LSTM dans le framework de comparaison"""
    logger.info("\n=== Test LSTM dans le Framework ===")
    
    if not TENSORFLOW_AVAILABLE:
        logger.warning("TensorFlow non disponible, test ignoré")
        return False
    
    try:
        # Obtenir une session de base de données
        db = next(get_db())
        service = ModelComparisonService(db)
        
        # Tester avec un symbole qui a des données
        symbol = "AAPL"  # Apple comme exemple
        
        logger.info(f"Test de comparaison avec LSTM pour {symbol}")
        
        # Comparer seulement LSTM pour le test
        models_to_test = ['LSTM']
        
        result = service.compare_models_for_symbol(
            symbol=symbol,
            models_to_test=models_to_test,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )
        
        if result['success']:
            logger.info("✅ Comparaison LSTM réussie")
            
            # Afficher les résultats
            lstm_results = result['results'].get('LSTM')
            if lstm_results:
                logger.info(f"Accuracy: {lstm_results.accuracy:.4f}")
                logger.info(f"F1-Score: {lstm_results.f1_score:.4f}")
                logger.info(f"Sharpe Ratio: {lstm_results.sharpe_ratio:.4f}")
                logger.info(f"Total Return: {lstm_results.total_return:.4f}")
            
            return True
        else:
            logger.error(f"❌ Échec de la comparaison: {result.get('error', 'Erreur inconnue')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du test dans le framework: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    """Fonction principale de test"""
    logger.info("🚀 Début des Tests LSTM")
    
    tests = [
        ("Disponibilité TensorFlow", test_lstm_availability),
        ("Création du Modèle", test_lstm_model_creation),
        ("Test avec Données Synthétiques", test_lstm_with_synthetic_data),
        ("Test dans le Framework", test_lstm_in_framework)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name}: RÉUSSI")
            else:
                logger.warning(f"⚠️  {test_name}: ÉCHEC")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERREUR - {e}")
            results.append((test_name, False))
    
    # Résumé
    logger.info(f"\n{'='*50}")
    logger.info("RÉSUMÉ DES TESTS")
    logger.info(f"{'='*50}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHEC"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nRésultat global: {passed}/{total} tests réussis")
    
    if passed == total:
        logger.info("🎉 Tous les tests LSTM sont passés avec succès!")
    else:
        logger.warning(f"⚠️  {total - passed} test(s) ont échoué")

if __name__ == "__main__":
    main()
