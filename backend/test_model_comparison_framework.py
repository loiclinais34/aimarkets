#!/usr/bin/env python3
"""
Script de Test du Framework de Comparaison de Modèles
=====================================================

Ce script teste le framework de comparaison de modèles avec des données
simulées et réelles pour vérifier son bon fonctionnement.
"""

import sys
import os
import logging
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from pathlib import Path

# Ajouter le chemin du backend au PYTHONPATH
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.model_comparison_framework import (
    ModelComparisonFramework,
    RandomForestModel,
    XGBoostModel,
    LightGBMModel,
    NeuralNetworkModel
)
from app.services.model_comparison_service import ModelComparisonService
from app.core.database import get_db

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_framework_with_synthetic_data():
    """Tester le framework avec des données synthétiques"""
    logger.info("🧪 Test du framework avec des données synthétiques")
    
    try:
        # Créer le framework
        framework = ModelComparisonFramework()
        
        # Générer des données synthétiques
        np.random.seed(42)
        n_samples = 1000
        n_features = 20
        
        # Features avec des patterns réalistes
        X = np.random.randn(n_samples, n_features)
        
        # Créer des labels avec une logique réaliste
        # Labels basés sur la combinaison de plusieurs features
        signal_strength = (
            X[:, 0] * 0.3 +  # Feature principale
            X[:, 1] * 0.2 +  # Feature secondaire
            X[:, 2] * 0.1 +  # Feature tertiaire
            np.random.randn(n_samples) * 0.4  # Bruit
        )
        
        # Labels binaires (0 ou 1)
        y = (signal_strength > np.percentile(signal_strength, 60)).astype(int)
        
        # Prix simulés pour le backtesting
        prices = 100 * np.cumprod(1 + np.random.randn(n_samples) * 0.02)
        
        # Diviser en train/test
        split_idx = int(n_samples * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        prices_test = prices[split_idx:]
        
        logger.info(f"Données générées: {len(X_train)} train, {len(X_test)} test")
        logger.info(f"Distribution des labels: {np.bincount(y_train)}")
        
        # Tester les modèles disponibles
        available_models = list(framework.default_models.keys())
        logger.info(f"Modèles disponibles: {available_models}")
        
        # Comparer les modèles
        results = framework.compare_models(
            X_train, y_train, X_test, y_test, prices_test, available_models
        )
        
        # Afficher les résultats
        logger.info("📊 Résultats de la comparaison:")
        for model_name, metrics in results.items():
            logger.info(
                f"  {model_name}: "
                f"Accuracy={metrics.accuracy:.3f}, "
                f"F1={metrics.f1_score:.3f}, "
                f"Sharpe={metrics.sharpe_ratio:.3f}"
            )
        
        # Obtenir le meilleur modèle
        best_model_name, best_metrics = framework.get_best_model('f1_score')
        logger.info(f"🏆 Meilleur modèle (F1-Score): {best_model_name}")
        logger.info(f"   F1-Score: {best_metrics.f1_score:.3f}")
        logger.info(f"   Accuracy: {best_metrics.accuracy:.3f}")
        logger.info(f"   Sharpe Ratio: {best_metrics.sharpe_ratio:.3f}")
        
        # Générer le rapport
        report = framework.generate_report()
        logger.info(f"\n📋 Rapport de comparaison:\n{report}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test synthétique: {e}")
        return False

def test_framework_with_real_data():
    """Tester le framework avec des données réelles"""
    logger.info("🔍 Test du framework avec des données réelles")
    
    try:
        # Obtenir une session de base de données
        db = next(get_db())
        
        # Créer le service de comparaison
        service = ModelComparisonService(db)
        
        # Obtenir les symboles disponibles
        symbols = service.get_available_symbols()
        logger.info(f"Symboles disponibles: {len(symbols)}")
        
        if not symbols:
            logger.warning("Aucun symbole disponible pour le test")
            return False
        
        # Tester avec le premier symbole disponible
        test_symbol = symbols[0]
        logger.info(f"Test avec le symbole: {test_symbol}")
        
        # Obtenir des recommandations
        recommendations = service.get_model_recommendations(test_symbol)
        if recommendations['success']:
            logger.info(f"✅ Recommandations pour {test_symbol}:")
            logger.info(f"   Modèles primaires: {recommendations['recommendations']['primary']}")
            logger.info(f"   Modèles secondaires: {recommendations['recommendations']['secondary']}")
            logger.info(f"   Raisonnement: {recommendations['recommendations']['reasoning']}")
        
        # Tester la comparaison de modèles (avec un sous-ensemble pour éviter les timeouts)
        test_models = ['RandomForest', 'XGBoost'] if 'XGBoost' in service.framework.default_models else ['RandomForest']
        
        logger.info(f"Comparaison des modèles: {test_models}")
        comparison_result = service.compare_models_for_symbol(
            symbol=test_symbol,
            models_to_test=test_models
        )
        
        if comparison_result['success']:
            logger.info(f"✅ Comparaison réussie pour {test_symbol}")
            logger.info(f"   Meilleur modèle: {comparison_result['best_model']['name']}")
            logger.info(f"   F1-Score: {comparison_result['best_model']['metrics']['f1_score']:.3f}")
            logger.info(f"   Sharpe Ratio: {comparison_result['best_model']['metrics']['sharpe_ratio']:.3f}")
        else:
            logger.warning(f"⚠️ Échec de la comparaison pour {test_symbol}: {comparison_result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test avec données réelles: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def test_model_creation():
    """Tester la création de modèles personnalisés"""
    logger.info("🔧 Test de création de modèles personnalisés")
    
    try:
        framework = ModelComparisonFramework()
        
        # Créer des modèles personnalisés
        custom_models = {
            'RF_Fast': RandomForestModel(
                'RF_Fast',
                n_estimators=50,
                max_depth=5,
                n_jobs=1
            ),
            'RF_Deep': RandomForestModel(
                'RF_Deep',
                n_estimators=200,
                max_depth=15,
                min_samples_split=3,
                min_samples_leaf=2
            )
        }
        
        # Ajouter les modèles au framework
        for name, model in custom_models.items():
            framework.add_model(name, model)
        
        logger.info(f"✅ Modèles personnalisés ajoutés: {list(custom_models.keys())}")
        
        # Tester avec des données synthétiques
        np.random.seed(123)
        X = np.random.randn(100, 10)
        y = np.random.randint(0, 2, 100)
        
        # Entraîner un modèle personnalisé
        custom_model = custom_models['RF_Fast']
        custom_model.fit(X, y)
        
        # Faire des prédictions
        predictions = custom_model.predict(X[:10])
        probabilities = custom_model.predict_proba(X[:10])
        
        logger.info(f"✅ Prédictions générées: {len(predictions)}")
        logger.info(f"   Probabilités shape: {probabilities.shape}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de création de modèles: {e}")
        return False

def test_performance_metrics():
    """Tester le calcul des métriques de performance"""
    logger.info("📈 Test des métriques de performance")
    
    try:
        framework = ModelComparisonFramework()
        
        # Données de test
        np.random.seed(456)
        n_samples = 500
        
        # Générer des prédictions et des prix réalistes
        y_true = np.random.randint(0, 2, n_samples)
        y_pred = np.random.randint(0, 2, n_samples)
        y_pred_proba = np.random.rand(n_samples, 2)
        y_pred_proba = y_pred_proba / y_pred_proba.sum(axis=1, keepdims=True)
        
        # Prix avec une tendance
        prices = 100 * np.cumprod(1 + np.random.randn(n_samples) * 0.01)
        
        # Calculer les métriques ML
        ml_metrics = framework._calculate_ml_metrics(y_true, y_pred, y_pred_proba)
        logger.info(f"✅ Métriques ML calculées:")
        for metric, value in ml_metrics.items():
            logger.info(f"   {metric}: {value:.3f}")
        
        # Calculer les métriques de trading
        trading_metrics = framework._calculate_trading_metrics(y_pred, y_pred_proba, prices)
        logger.info(f"✅ Métriques de trading calculées:")
        for metric, value in trading_metrics.items():
            logger.info(f"   {metric}: {value:.3f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test des métriques: {e}")
        return False

def main():
    """Fonction principale de test"""
    logger.info("🚀 Démarrage des tests du Framework de Comparaison de Modèles")
    logger.info("=" * 70)
    
    tests = [
        ("Test avec données synthétiques", test_framework_with_synthetic_data),
        ("Test de création de modèles", test_model_creation),
        ("Test des métriques de performance", test_performance_metrics),
        ("Test avec données réelles", test_framework_with_real_data),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n🧪 {test_name}")
        logger.info("-" * 50)
        
        try:
            result = test_func()
            results[test_name] = result
            
            if result:
                logger.info(f"✅ {test_name}: RÉUSSI")
            else:
                logger.info(f"❌ {test_name}: ÉCHOUÉ")
                
        except Exception as e:
            logger.error(f"💥 {test_name}: ERREUR CRITIQUE - {e}")
            results[test_name] = False
    
    # Résumé des tests
    logger.info("\n" + "=" * 70)
    logger.info("📊 RÉSUMÉ DES TESTS")
    logger.info("=" * 70)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"\n🎯 Résultat global: {passed}/{total} tests réussis")
    
    if passed == total:
        logger.info("🎉 Tous les tests sont passés ! Le framework est prêt à être utilisé.")
    else:
        logger.warning(f"⚠️ {total - passed} test(s) ont échoué. Vérifiez les logs ci-dessus.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
