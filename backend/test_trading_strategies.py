#!/usr/bin/env python3
"""
Script de test pour le système de stratégies de trading
"""

import sys
import os
from datetime import datetime, date, timedelta
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.services.trading_strategy_service import TradingStrategyService
from app.services.predefined_strategies import PredefinedStrategies, StrategyInitializer
from app.services.backtesting_service import BacktestingService
from app.models.database import MLModels, MLPredictions, BacktestRun

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_strategy_system():
    """Tester le système de stratégies complet"""
    db = SessionLocal()
    
    try:
        logger.info("🧪 Début des tests du système de stratégies")
        
        # 1. Tester la création d'une stratégie prédéfinie
        logger.info("📋 Test de création d'une stratégie prédéfinie...")
        strategy_service = TradingStrategyService(db)
        
        momentum_strategy = PredefinedStrategies.get_momentum_strategy()
        
        result = strategy_service.create_strategy(
            name=momentum_strategy["name"],
            description=momentum_strategy["description"],
            strategy_type=momentum_strategy["strategy_type"],
            parameters=momentum_strategy["parameters"],
            rules=momentum_strategy["rules"],
            created_by="test_script"
        )
        
        if not result["success"]:
            logger.error(f"❌ Erreur lors de la création de la stratégie: {result['error']}")
            return False
        
        strategy_id = result["strategy_id"]
        logger.info(f"✅ Stratégie créée avec l'ID: {strategy_id}")
        
        # 2. Tester la récupération de la stratégie
        logger.info("📖 Test de récupération de la stratégie...")
        strategy_result = strategy_service.get_strategy(strategy_id)
        
        if not strategy_result["success"]:
            logger.error(f"❌ Erreur lors de la récupération: {strategy_result['error']}")
            return False
        
        strategy_data = strategy_result["strategy"]
        rules_data = strategy_result["rules"]
        
        logger.info(f"✅ Stratégie récupérée: {strategy_data['name']}")
        logger.info(f"✅ {len(rules_data)} règles trouvées")
        
        # 3. Tester l'ajout d'une règle
        logger.info("➕ Test d'ajout d'une règle...")
        rule_result = strategy_service.add_strategy_rule(
            strategy_id=strategy_id,
            rule_type="risk_management",
            rule_name="Max Loss Rule",
            rule_condition="current_return < -0.08",
            rule_action="CLOSE_POSITION",
            priority=1
        )
        
        if not rule_result["success"]:
            logger.error(f"❌ Erreur lors de l'ajout de la règle: {rule_result['error']}")
            return False
        
        logger.info(f"✅ Règle ajoutée avec l'ID: {rule_result['rule_id']}")
        
        # 4. Tester la récupération des stratégies
        logger.info("📋 Test de récupération des stratégies...")
        strategies_result = strategy_service.get_strategies()
        
        if not strategies_result["success"]:
            logger.error(f"❌ Erreur lors de la récupération des stratégies: {strategies_result['error']}")
            return False
        
        logger.info(f"✅ {len(strategies_result['strategies'])} stratégies trouvées")
        
        # 5. Tester l'initialisation des stratégies prédéfinies
        logger.info("🚀 Test d'initialisation des stratégies prédéfinies...")
        initializer = StrategyInitializer(strategy_service)
        
        init_result = initializer.initialize_strategy_by_type("conservative")
        
        if not init_result["success"]:
            logger.error(f"❌ Erreur lors de l'initialisation: {init_result['error']}")
            return False
        
        conservative_strategy_id = init_result["strategy_id"]
        logger.info(f"✅ Stratégie conservative initialisée avec l'ID: {conservative_strategy_id}")
        
        # 6. Tester le backtesting avec une stratégie
        logger.info("🎯 Test de backtesting avec stratégie...")
        
        # Trouver un modèle avec des prédictions
        predictions = db.query(MLPredictions).filter(
            MLPredictions.prediction_value >= 1.0
        ).limit(1).all()
        
        if not predictions:
            logger.error("❌ Aucune prédiction trouvée pour le test")
            return False
        
        test_model_id = predictions[0].model_id
        prediction_dates = [pred.prediction_date for pred in predictions if pred.prediction_date]
        
        if not prediction_dates:
            logger.error("❌ Aucune date valide trouvée")
            return False
        
        start_date = min(prediction_dates)
        end_date = start_date + timedelta(days=7)
        
        # Créer un backtest avec stratégie
        backtesting_service = BacktestingService(db)
        
        backtest_result = backtesting_service.create_backtest_run(
            name=f"Test Strategy Backtesting {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            description="Test automatique du backtesting avec stratégie",
            model_id=test_model_id,
            strategy_id=strategy_id,
            start_date=start_date,
            end_date=end_date,
            initial_capital=100000.0,
            position_size_percentage=10.0,
            commission_rate=0.001,
            slippage_rate=0.0005,
            confidence_threshold=0.60,
            max_positions=5,
            created_by="test_script"
        )
        
        if not backtest_result["success"]:
            logger.error(f"❌ Erreur lors de la création du backtest: {backtest_result['error']}")
            return False
        
        backtest_run_id = backtest_result["backtest_run_id"]
        logger.info(f"✅ Backtest créé avec l'ID: {backtest_run_id}")
        
        # Exécuter le backtesting
        logger.info("🚀 Exécution du backtesting avec stratégie...")
        run_result = backtesting_service.run_backtest(backtest_run_id)
        
        if not run_result["success"]:
            logger.error(f"❌ Erreur lors de l'exécution: {run_result['error']}")
            return False
        
        logger.info("✅ Backtesting avec stratégie exécuté avec succès")
        logger.info(f"📊 Résultats:")
        logger.info(f"   - Total trades: {run_result['total_trades']}")
        logger.info(f"   - Capital final: ${run_result['final_capital']:,.2f}")
        logger.info(f"   - Retour total: {run_result['total_return']:.2f}%")
        
        # 7. Tester l'évaluation des règles
        logger.info("📊 Test d'évaluation des règles...")
        
        # Récupérer les résultats du backtest
        results = backtesting_service.get_backtest_results(backtest_run_id)
        
        if results["success"] and results["trades"]:
            trades = results["trades"]
            equity_curve = results["equity_curve"]
            
            rule_eval_result = strategy_service.evaluate_strategy_rules(
                strategy_id, trades, equity_curve
            )
            
            if rule_eval_result["success"]:
                logger.info("✅ Évaluation des règles réussie")
                for rule_name, effectiveness in rule_eval_result["rule_effectiveness"].items():
                    logger.info(f"   - {rule_name}: {effectiveness.get('effectiveness_score', 0):.2f}")
            else:
                logger.warning(f"⚠️ Erreur lors de l'évaluation des règles: {rule_eval_result['error']}")
        
        # 8. Test de suppression
        logger.info("🗑️ Test de suppression de la stratégie...")
        
        # Supprimer d'abord le backtest pour éviter les contraintes
        db.query(BacktestRun).filter(BacktestRun.id == backtest_run_id).delete()
        db.commit()
        
        delete_result = strategy_service.delete_strategy(strategy_id)
        
        if not delete_result["success"]:
            logger.error(f"❌ Erreur lors de la suppression: {delete_result['error']}")
            return False
        
        logger.info("✅ Stratégie supprimée avec succès")
        
        logger.info("🎉 Tests du système de stratégies terminés avec succès!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur inattendue lors des tests: {e}")
        return False
    finally:
        db.close()


def test_predefined_strategies():
    """Tester les stratégies prédéfinies"""
    try:
        logger.info("📋 Test des stratégies prédéfinies...")
        
        strategies = PredefinedStrategies.get_all_strategies()
        
        logger.info(f"✅ {len(strategies)} stratégies prédéfinies disponibles:")
        
        for strategy in strategies:
            logger.info(f"   - {strategy['name']} ({strategy['strategy_type']})")
            logger.info(f"     Description: {strategy['description']}")
            logger.info(f"     Règles: {len(strategy['rules'])}")
            logger.info(f"     Paramètres: {len(strategy['parameters'])}")
        
        # Tester une stratégie spécifique
        momentum = PredefinedStrategies.get_strategy_by_type("momentum")
        if momentum:
            logger.info(f"✅ Stratégie momentum récupérée: {momentum['name']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test des stratégies prédéfinies: {e}")
        return False


def test_api_endpoints():
    """Tester les endpoints API des stratégies"""
    import requests
    
    try:
        base_url = "http://localhost:8000/api/v1/strategies"
        
        logger.info("🌐 Test des endpoints API des stratégies...")
        
        # Test 1: Lister les stratégies
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            logger.info("✅ Endpoint GET /strategies fonctionne")
        else:
            logger.warning(f"⚠️ Endpoint GET /strategies retourne {response.status_code}")
        
        # Test 2: Récupérer les types prédéfinis
        response = requests.get(f"{base_url}/predefined/types")
        if response.status_code == 200:
            logger.info("✅ Endpoint GET /predefined/types fonctionne")
        else:
            logger.warning(f"⚠️ Endpoint GET /predefined/types retourne {response.status_code}")
        
        # Test 3: Récupérer une stratégie prédéfinie
        response = requests.get(f"{base_url}/predefined/momentum")
        if response.status_code == 200:
            logger.info("✅ Endpoint GET /predefined/momentum fonctionne")
        else:
            logger.warning(f"⚠️ Endpoint GET /predefined/momentum retourne {response.status_code}")
        
        logger.info("🌐 Tests des endpoints API terminés")
        
    except requests.exceptions.ConnectionError:
        logger.warning("⚠️ Impossible de tester les endpoints API (serveur non démarré)")
    except Exception as e:
        logger.error(f"❌ Erreur lors des tests API: {e}")


if __name__ == "__main__":
    print("🧪 Tests du système de stratégies de trading AIMarkets")
    print("=" * 60)
    
    # Test des stratégies prédéfinies
    success1 = test_predefined_strategies()
    
    if success1:
        print("\n✅ Tests des stratégies prédéfinies: SUCCÈS")
    else:
        print("\n❌ Tests des stratégies prédéfinies: ÉCHEC")
    
    # Test du système complet
    print("\n" + "=" * 60)
    success2 = test_strategy_system()
    
    if success2:
        print("\n✅ Tests du système de stratégies: SUCCÈS")
    else:
        print("\n❌ Tests du système de stratégies: ÉCHEC")
    
    # Test des endpoints API
    print("\n" + "=" * 60)
    test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("🏁 Tests terminés")
