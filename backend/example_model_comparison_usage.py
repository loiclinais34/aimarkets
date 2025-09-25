#!/usr/bin/env python3
"""
Exemple d'Utilisation du Framework de Comparaison de Modèles
============================================================

Ce script démontre comment utiliser le framework de comparaison de modèles
pour analyser différents symboles et sélectionner les meilleurs modèles.
"""

import sys
import os
import logging
from datetime import datetime, date, timedelta
from pathlib import Path

# Ajouter le chemin du backend au PYTHONPATH
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.services.model_comparison_service import ModelComparisonService
from app.core.database import get_db

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def example_single_symbol_analysis():
    """Exemple d'analyse d'un symbole unique"""
    logger.info("🔍 Exemple d'analyse d'un symbole unique")
    logger.info("=" * 60)
    
    try:
        # Obtenir une session de base de données
        db = next(get_db())
        
        # Créer le service de comparaison
        service = ModelComparisonService(db)
        
        # Analyser AAPL (Apple)
        symbol = "AAPL"
        logger.info(f"Analyse du symbole: {symbol}")
        
        # 1. Obtenir des recommandations
        logger.info("\n1️⃣ Obtention des recommandations...")
        recommendations = service.get_model_recommendations(symbol)
        
        if recommendations['success']:
            analysis = recommendations['analysis']
            recs = recommendations['recommendations']
            
            logger.info(f"   📊 Analyse du symbole:")
            logger.info(f"      Volatilité: {analysis['volatility']:.3f} ({analysis['volatility_class']})")
            logger.info(f"      Tendance: {analysis['trend']:.3f} ({analysis['trend_class']})")
            logger.info(f"      Volume moyen: {analysis['avg_volume']:,.0f}")
            
            logger.info(f"   🎯 Recommandations:")
            logger.info(f"      Modèles primaires: {recs['primary']}")
            logger.info(f"      Modèles secondaires: {recs['secondary']}")
            logger.info(f"      À éviter: {recs['avoid']}")
            
            for reason in recs['reasoning']:
                logger.info(f"      💡 {reason}")
        
        # 2. Comparer les modèles recommandés
        logger.info("\n2️⃣ Comparaison des modèles...")
        
        # Utiliser les modèles recommandés ou par défaut
        models_to_test = recommendations['recommendations']['primary'] if recommendations['success'] else ['RandomForest']
        
        # Ajouter quelques modèles supplémentaires pour la comparaison
        additional_models = ['LightGBM', 'NeuralNetwork']
        for model in additional_models:
            if model not in models_to_test and model in service.framework.default_models:
                models_to_test.append(model)
        
        logger.info(f"   Modèles à tester: {models_to_test}")
        
        # Comparer les modèles
        comparison_result = service.compare_models_for_symbol(
            symbol=symbol,
            models_to_test=models_to_test,
            start_date=date.today() - timedelta(days=365),  # 1 an de données
            end_date=date.today()
        )
        
        if comparison_result['success']:
            logger.info(f"   ✅ Comparaison réussie!")
            
            # Afficher les résultats détaillés
            results = comparison_result['results']
            logger.info(f"\n   📈 Résultats détaillés:")
            logger.info(f"   {'Modèle':<20} {'Accuracy':<10} {'F1-Score':<10} {'Sharpe':<10} {'Return':<10}")
            logger.info(f"   {'-'*20} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
            
            for model_name, metrics in results.items():
                logger.info(
                    f"   {model_name:<20} "
                    f"{metrics.accuracy:<10.3f} "
                    f"{metrics.f1_score:<10.3f} "
                    f"{metrics.sharpe_ratio:<10.3f} "
                    f"{metrics.total_return:<10.3f}"
                )
            
            # Afficher le meilleur modèle
            best_model = comparison_result['best_model']
            logger.info(f"\n   🏆 Meilleur modèle: {best_model['name']}")
            logger.info(f"      F1-Score: {best_model['metrics']['f1_score']:.3f}")
            logger.info(f"      Accuracy: {best_model['metrics']['accuracy']:.3f}")
            logger.info(f"      Sharpe Ratio: {best_model['metrics']['sharpe_ratio']:.3f}")
            logger.info(f"      Total Return: {best_model['metrics']['total_return']:.3f}")
            
            # Informations sur les données
            data_info = comparison_result['data_info']
            logger.info(f"\n   📊 Informations sur les données:")
            logger.info(f"      Échantillons d'entraînement: {data_info['train_samples']}")
            logger.info(f"      Échantillons de test: {data_info['test_samples']}")
            logger.info(f"      Nombre de features: {data_info['features']}")
            
        else:
            logger.warning(f"   ⚠️ Échec de la comparaison: {comparison_result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def example_multiple_symbols_analysis():
    """Exemple d'analyse de plusieurs symboles"""
    logger.info("\n🔍 Exemple d'analyse de plusieurs symboles")
    logger.info("=" * 60)
    
    try:
        # Obtenir une session de base de données
        db = next(get_db())
        
        # Créer le service de comparaison
        service = ModelComparisonService(db)
        
        # Sélectionner quelques symboles populaires
        symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        
        # Vérifier quels symboles sont disponibles
        available_symbols = service.get_available_symbols()
        symbols_to_test = [s for s in symbols if s in available_symbols]
        
        if not symbols_to_test:
            logger.warning("Aucun des symboles sélectionnés n'est disponible")
            return False
        
        logger.info(f"Symboles à analyser: {symbols_to_test}")
        
        # Comparer les modèles sur plusieurs symboles
        logger.info("\n🔄 Comparaison multi-symboles...")
        
        multi_result = service.compare_models_for_multiple_symbols(
            symbols=symbols_to_test,
            models_to_test=['RandomForest', 'LightGBM']  # Limiter pour éviter les timeouts
        )
        
        if multi_result['success']:
            summary = multi_result['summary']
            logger.info(f"✅ Analyse multi-symboles terminée!")
            logger.info(f"   Symboles analysés: {summary['successful_symbols']}/{summary['total_symbols']}")
            logger.info(f"   Taux de succès: {summary['success_rate']:.1%}")
            
            # Afficher les victoires par modèle
            model_wins = multi_result['model_wins']
            if model_wins:
                logger.info(f"\n🏆 Victoires par modèle:")
                for model, wins in sorted(model_wins.items(), key=lambda x: x[1], reverse=True):
                    logger.info(f"   {model}: {wins} victoire(s)")
            
            # Afficher les métriques moyennes
            avg_metrics = multi_result['model_avg_metrics']
            if avg_metrics:
                logger.info(f"\n📊 Métriques moyennes par modèle:")
                logger.info(f"   {'Modèle':<15} {'Accuracy':<12} {'F1-Score':<12} {'Sharpe':<12}")
                logger.info(f"   {'-'*15} {'-'*12} {'-'*12} {'-'*12}")
                
                for model_name, metrics in avg_metrics.items():
                    logger.info(
                        f"   {model_name:<15} "
                        f"{metrics['accuracy']['mean']:<12.3f} "
                        f"{metrics['f1_score']['mean']:<12.3f} "
                        f"{metrics['sharpe_ratio']['mean']:<12.3f}"
                    )
            
            # Afficher les symboles qui ont échoué
            failed_symbols = multi_result['failed_symbols']
            if failed_symbols:
                logger.warning(f"\n⚠️ Symboles ayant échoué: {failed_symbols}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse multi-symboles: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def example_custom_model_creation():
    """Exemple de création de modèles personnalisés"""
    logger.info("\n🔧 Exemple de création de modèles personnalisés")
    logger.info("=" * 60)
    
    try:
        from app.services.model_comparison_framework import (
            ModelComparisonFramework, 
            RandomForestModel
        )
        
        # Créer le framework
        framework = ModelComparisonFramework()
        
        # Créer des modèles personnalisés avec différents paramètres
        custom_models = {
            'RF_Conservative': RandomForestModel(
                'RF_Conservative',
                n_estimators=50,
                max_depth=5,
                min_samples_split=10,
                min_samples_leaf=5
            ),
            'RF_Aggressive': RandomForestModel(
                'RF_Aggressive',
                n_estimators=300,
                max_depth=20,
                min_samples_split=2,
                min_samples_leaf=1
            ),
            'RF_Balanced': RandomForestModel(
                'RF_Balanced',
                n_estimators=150,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2
            )
        }
        
        # Ajouter les modèles au framework
        for name, model in custom_models.items():
            framework.add_model(name, model)
            logger.info(f"✅ Modèle {name} ajouté")
        
        # Tester avec des données synthétiques
        import numpy as np
        np.random.seed(42)
        
        X_train = np.random.randn(500, 15)
        y_train = np.random.randint(0, 2, 500)
        X_test = np.random.randn(100, 15)
        y_test = np.random.randint(0, 2, 100)
        prices = np.random.randn(100) * 100 + 100
        
        # Comparer les modèles personnalisés
        logger.info("\n🔄 Comparaison des modèles personnalisés...")
        
        results = framework.compare_models(
            X_train, y_train, X_test, y_test, prices,
            models_to_test=list(custom_models.keys())
        )
        
        # Afficher les résultats
        logger.info(f"\n📈 Résultats des modèles personnalisés:")
        logger.info(f"   {'Modèle':<20} {'Accuracy':<10} {'F1-Score':<10} {'Sharpe':<10}")
        logger.info(f"   {'-'*20} {'-'*10} {'-'*10} {'-'*10}")
        
        for model_name, metrics in results.items():
            logger.info(
                f"   {model_name:<20} "
                f"{metrics.accuracy:<10.3f} "
                f"{metrics.f1_score:<10.3f} "
                f"{metrics.sharpe_ratio:<10.3f}"
            )
        
        # Obtenir le meilleur modèle
        best_model_name, best_metrics = framework.get_best_model('f1_score')
        logger.info(f"\n🏆 Meilleur modèle personnalisé: {best_model_name}")
        logger.info(f"   F1-Score: {best_metrics.f1_score:.3f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de la création de modèles personnalisés: {e}")
        return False

def example_model_recommendations():
    """Exemple d'utilisation des recommandations de modèles"""
    logger.info("\n🎯 Exemple d'utilisation des recommandations")
    logger.info("=" * 60)
    
    try:
        # Obtenir une session de base de données
        db = next(get_db())
        
        # Créer le service de comparaison
        service = ModelComparisonService(db)
        
        # Analyser différents types de symboles
        symbol_types = {
            'Tech_Giant': 'AAPL',
            'Growth_Stock': 'TSLA', 
            'Value_Stock': 'BRK.B',
            'Volatile_Stock': 'NVDA',
            'Stable_Stock': 'JNJ'
        }
        
        available_symbols = service.get_available_symbols()
        
        for stock_type, symbol in symbol_types.items():
            if symbol not in available_symbols:
                logger.info(f"⚠️ {symbol} non disponible, passage au suivant...")
                continue
            
            logger.info(f"\n📊 Analyse de {symbol} ({stock_type})...")
            
            recommendations = service.get_model_recommendations(symbol)
            
            if recommendations['success']:
                analysis = recommendations['analysis']
                recs = recommendations['recommendations']
                
                logger.info(f"   Volatilité: {analysis['volatility']:.3f} ({analysis['volatility_class']})")
                logger.info(f"   Tendance: {analysis['trend']:.3f} ({analysis['trend_class']})")
                logger.info(f"   Recommandé: {recs['primary']}")
                
                if recs['avoid']:
                    logger.info(f"   À éviter: {recs['avoid']}")
            else:
                logger.warning(f"   ⚠️ Échec de l'analyse: {recommendations.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'analyse des recommandations: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def main():
    """Fonction principale avec exemples d'utilisation"""
    logger.info("🚀 Exemples d'Utilisation du Framework de Comparaison de Modèles")
    logger.info("=" * 80)
    
    examples = [
        ("Analyse d'un symbole unique", example_single_symbol_analysis),
        ("Analyse de plusieurs symboles", example_multiple_symbols_analysis),
        ("Création de modèles personnalisés", example_custom_model_creation),
        ("Utilisation des recommandations", example_model_recommendations),
    ]
    
    results = {}
    
    for example_name, example_func in examples:
        logger.info(f"\n{'='*80}")
        logger.info(f"🧪 {example_name}")
        logger.info(f"{'='*80}")
        
        try:
            result = example_func()
            results[example_name] = result
            
            if result:
                logger.info(f"✅ {example_name}: RÉUSSI")
            else:
                logger.info(f"❌ {example_name}: ÉCHOUÉ")
                
        except Exception as e:
            logger.error(f"💥 {example_name}: ERREUR CRITIQUE - {e}")
            results[example_name] = False
    
    # Résumé des exemples
    logger.info(f"\n{'='*80}")
    logger.info("📊 RÉSUMÉ DES EXEMPLES")
    logger.info(f"{'='*80}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for example_name, result in results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        logger.info(f"  {example_name}: {status}")
    
    logger.info(f"\n🎯 Résultat global: {passed}/{total} exemples réussis")
    
    if passed == total:
        logger.info("🎉 Tous les exemples sont passés ! Le framework est prêt à être utilisé.")
    else:
        logger.warning(f"⚠️ {total - passed} exemple(s) ont échoué. Vérifiez les logs ci-dessus.")
    
    logger.info(f"\n📚 Prochaines étapes:")
    logger.info(f"   1. Intégrer le framework dans le frontend")
    logger.info(f"   2. Ajouter des modèles avancés (LSTM, Transformer)")
    logger.info(f"   3. Implémenter des méthodes d'ensemble")
    logger.info(f"   4. Optimiser les performances pour de gros datasets")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
