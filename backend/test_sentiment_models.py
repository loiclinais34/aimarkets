#!/usr/bin/env python3
"""
Test des modèles de sentiment pour la Phase 3.

Ce script teste les modèles GARCH, Monte Carlo et Markov Chain
pour s'assurer qu'ils fonctionnent correctement.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sentiment_models():
    """Test complet des modèles de sentiment."""
    
    print("🧪 Test des Modèles de Sentiment - Phase 3")
    print("=" * 50)
    
    try:
        # Import des services
        from app.services.sentiment_analysis import GARCHModels, MonteCarloSimulation, MarkovChainAnalysis, VolatilityForecaster
        from app.services.polygon_service import PolygonService
        
        print("✅ Services importés avec succès")
        
        # Récupération des données de test
        data_service = PolygonService()
        symbol = "AAPL"
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        print(f"📊 Récupération des données pour {symbol}...")
        historical_data = data_service.get_historical_data(
            symbol=symbol,
            from_date=start_date.strftime('%Y-%m-%d'),
            to_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not historical_data or len(historical_data) < 100:
            print("❌ Pas assez de données historiques")
            return False
        
        # Conversion en DataFrame
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        df = df.sort_index()
        
        # Convertir toutes les colonnes numériques en float pour éviter les problèmes de type
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: float(x) if x is not None else None)
        
        print(f"✅ {len(df)} jours de données récupérées")
        
        # Test 1: Modèles GARCH
        print("\n🔬 Test 1: Modèles GARCH")
        print("-" * 30)
        
        try:
            garch_analyzer = GARCHModels()
            
            # Test GARCH standard
            garch_result = garch_analyzer.fit_garch(df['close'], model_type="GARCH")
            print(f"✅ GARCH: Volatilité prévue = {garch_result['volatility_forecast']:.4f}")
            print(f"   VaR 95% = {garch_result['var_95']:.4f}")
            print(f"   VaR 99% = {garch_result['var_99']:.4f}")
            
            # Test EGARCH
            egarch_result = garch_analyzer.fit_garch(df['close'], model_type="EGARCH")
            print(f"✅ EGARCH: Volatilité prévue = {egarch_result['volatility_forecast']:.4f}")
            
            # Test GJR-GARCH
            gjr_result = garch_analyzer.fit_garch(df['close'], model_type="GJR-GARCH")
            print(f"✅ GJR-GARCH: Volatilité prévue = {gjr_result['volatility_forecast']:.4f}")
            
        except Exception as e:
            print(f"❌ Erreur GARCH: {str(e)}")
            return False
        
        # Test 2: Simulation Monte Carlo
        print("\n🎲 Test 2: Simulation Monte Carlo")
        print("-" * 30)
        
        try:
            mc_simulator = MonteCarloSimulation()
            
            # Calculer les paramètres
            returns = df['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)  # Volatilité annualisée
            drift = returns.mean() * 252  # Dérive annualisée
            
            # Simulation
            paths = mc_simulator.simulate_price_paths(
                current_price=float(df['close'].iloc[-1]),
                volatility=volatility,
                drift=drift,
                time_horizon=30,
                simulations=10000
            )
            
            # Calculer VaR
            var_95 = mc_simulator.calculate_var(paths, 0.05)
            var_99 = mc_simulator.calculate_var(paths, 0.01)
            
            print(f"✅ Monte Carlo: {len(paths)} simulations générées")
            print(f"   Prix actuel = ${df['close'].iloc[-1]:.2f}")
            print(f"   Volatilité = {volatility:.4f}")
            print(f"   VaR 95% = {var_95:.4f}")
            print(f"   VaR 99% = {var_99:.4f}")
            
            # Test de stress
            stress_result = mc_simulator.stress_test(paths, stress_scenarios={
                'market_crash': -0.2,
                'volatility_spike': 2.0
            })
            print(f"   Stress test: {len(stress_result)} scénarios testés")
            
        except Exception as e:
            print(f"❌ Erreur Monte Carlo: {str(e)}")
            return False
        
        # Test 3: Chaînes de Markov
        print("\n🔗 Test 3: Chaînes de Markov")
        print("-" * 30)
        
        try:
            markov_analyzer = MarkovChainAnalysis()
            
            # Identifier les états de marché
            states_result = markov_analyzer.identify_market_states(returns, n_states=3)
            print(f"✅ États identifiés: {states_result['n_states']} états")
            print(f"   États: {states_result['state_labels']}")
            
            # Calculer la matrice de transition
            transition_matrix = markov_analyzer.calculate_transition_matrix(
                states_result['states']
            )
            print(f"✅ Matrice de transition calculée: {transition_matrix['transition_matrix'].shape}")
            
            # Prédire l'état futur
            current_state = states_result['states'].iloc[-1]
            future_state = markov_analyzer.predict_future_states(
                transition_matrix['transition_matrix'], current_state, horizon=5
            )
            print(f"✅ État futur prédit: {future_state['most_likely_states'].iloc[-1]}")
            
        except Exception as e:
            print(f"❌ Erreur Markov: {str(e)}")
            return False
        
        # Test 4: Prévision de volatilité
        print("\n📈 Test 4: Prévision de Volatilité")
        print("-" * 30)
        
        try:
            vol_forecaster = VolatilityForecaster()
            
            # Test simple de détection de changement de régime
            regime_forecast = vol_forecaster.forecast_volatility_regime_switching(returns, horizon=5)
            print(f"✅ Prévision avec changement de régime: {regime_forecast.get('regime_forecast', 'N/A')}")
            
        except Exception as e:
            print(f"❌ Erreur prévision volatilité: {str(e)}")
            return False
        
        # Test 5: Analyse complète
        print("\n🎯 Test 5: Analyse Complète")
        print("-" * 30)
        
        try:
            # Test simple de calcul de VaR
            var_95 = mc_simulator.calculate_var(paths, 0.05)
            var_99 = mc_simulator.calculate_var(paths, 0.01)
            print(f"✅ Analyse Monte Carlo complète:")
            print(f"   VaR 95%: {var_95:.4f}")
            print(f"   VaR 99%: {var_99:.4f}")
            
        except Exception as e:
            print(f"❌ Erreur analyse complète: {str(e)}")
            return False
        
        print("\n🎉 Tous les tests des modèles de sentiment sont passés avec succès!")
        print("✅ Phase 3: Modèles de Sentiment - OPÉRATIONNELS")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sentiment_models()
    if success:
        print("\n🚀 Phase 3 prête pour l'intégration!")
    else:
        print("\n⚠️  Des problèmes ont été détectés dans la Phase 3")
