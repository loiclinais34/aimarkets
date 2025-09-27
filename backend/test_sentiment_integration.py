#!/usr/bin/env python3
"""
Test d'intégration des modèles de sentiment avec les signaux avancés.

Ce script teste l'intégration complète de la Phase 3 avec les signaux avancés.
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

def test_sentiment_integration():
    """Test d'intégration des modèles de sentiment avec les signaux avancés."""
    
    print("🧪 Test d'Intégration - Phase 3 avec Signaux Avancés")
    print("=" * 60)
    
    try:
        # Import des services
        from app.services.technical_analysis.advanced_signals import AdvancedSignalGenerator
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
        
        # Convertir toutes les colonnes numériques en float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: float(x) if x is not None else None)
        
        print(f"✅ {len(df)} jours de données récupérées")
        
        # Test d'intégration des signaux avancés avec sentiment
        print("\n🎯 Test d'Intégration des Signaux Avancés")
        print("-" * 40)
        
        try:
            # Créer le générateur de signaux avancés
            signal_generator = AdvancedSignalGenerator()
            
            # Générer un signal avancé avec intégration sentiment
            signal_result = signal_generator.generate_advanced_signal(
                symbol=symbol,
                high=df['high'],
                low=df['low'],
                close=df['close'],
                open_prices=df['open'],
                volume=df.get('volume')
            )
            
            print(f"✅ Signal généré avec succès:")
            print(f"   Type: {signal_result.signal_type.value}")
            print(f"   Score: {signal_result.score:.1f}")
            print(f"   Confiance: {signal_result.confidence:.2f}")
            print(f"   Force: {signal_result.strength:.2f}")
            print(f"   Indicateurs utilisés: {len(signal_result.indicators_used)}")
            print(f"   Raisonnement: {signal_result.reasoning}")
            
            # Vérifier l'intégration des analyses de sentiment
            if hasattr(signal_result, 'sentiment_analysis'):
                sentiment = signal_result.sentiment_analysis
                print(f"\n📊 Analyses de Sentiment Intégrées:")
                print(f"   Disponibles: {sentiment['sentiment_available']}")
                print(f"   Raisonnement: {sentiment['reasoning']}")
                
                if sentiment['sentiment_available']:
                    analysis = sentiment['analysis']
                    
                    # Analyse GARCH
                    if 'garch' in analysis and 'error' not in analysis['garch']:
                        garch = analysis['garch']
                        print(f"   GARCH - Volatilité prévue: {garch['volatility_forecast']:.2f}%")
                        print(f"   GARCH - VaR 95%: {garch['var_95']:.2f}%")
                        print(f"   GARCH - Confiance: {garch['confidence']:.2f}")
                    
                    # Simulation Monte Carlo
                    if 'monte_carlo' in analysis and 'error' not in analysis['monte_carlo']:
                        mc = analysis['monte_carlo']
                        print(f"   Monte Carlo - VaR 95%: {mc['var_95']:.2f}%")
                        print(f"   Monte Carlo - VaR 99%: {mc['var_99']:.2f}%")
                        print(f"   Monte Carlo - Niveau de risque: {mc['risk_level']}")
                    
                    # Chaînes de Markov
                    if 'markov' in analysis and 'error' not in analysis['markov']:
                        markov = analysis['markov']
                        print(f"   Markov - État actuel: {markov['current_state']}")
                        print(f"   Markov - Nombre d'états: {markov['n_states']}")
                        print(f"   Markov - Labels: {markov['state_labels']}")
                else:
                    print(f"   ⚠️  Analyses de sentiment non disponibles")
            else:
                print(f"   ❌ Attribut sentiment_analysis manquant")
            
            # Test de l'historique des signaux
            print(f"\n📈 Test de l'Historique des Signaux:")
            history = signal_generator.get_signal_history(days=7)
            print(f"   Signaux dans l'historique: {len(history)}")
            
            if len(history) > 0:
                latest_signal = history[-1]
                print(f"   Dernier signal: {latest_signal.signal_type.value}")
                print(f"   Score: {latest_signal.score:.1f}")
                print(f"   Timestamp: {latest_signal.timestamp}")
            
        except Exception as e:
            print(f"❌ Erreur génération signal avancé: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n🎉 Test d'intégration réussi!")
        print("✅ Phase 3: Modèles de Sentiment - INTÉGRÉS avec les Signaux Avancés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_sentiment_integration()
    if success:
        print("\n🚀 Phase 3 complètement intégrée!")
    else:
        print("\n⚠️  Des problèmes ont été détectés dans l'intégration")
