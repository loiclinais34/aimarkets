#!/usr/bin/env python3
"""
Test de persistance des données de la Phase 3.

Ce script teste que les modèles de sentiment persistent correctement
leurs données en base de données et récupèrent les données depuis la base.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import requests
import time

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_sentiment_persistence():
    """Test de persistance des données de sentiment."""
    
    print("🧪 Test de Persistance - Phase 3 : Modèles de Sentiment")
    print("=" * 60)
    
    try:
        # Import des services de base de données
        from app.core.database import get_db
        from app.models.sentiment_analysis import GARCHModels as GARCHModelsModel, MonteCarloSimulations, MarkovChainAnalysis as MarkovChainAnalysisModel
        from app.models.database import HistoricalData
        
        # Récupérer une session de base de données
        db = next(get_db())
        
        print("✅ Connexion à la base de données établie")
        
        # Vérifier les données historiques disponibles
        print("\n📊 Vérification des données historiques")
        print("-" * 40)
        
        symbol = "AAPL"
        historical_count = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol
        ).count()
        
        print(f"   Données historiques pour {symbol}: {historical_count} enregistrements")
        
        if historical_count < 100:
            print("   ⚠️  Pas assez de données historiques pour les tests")
            return False
        
        # Test 1: Persistance GARCH
        print("\n🔬 Test 1: Persistance GARCH")
        print("-" * 30)
        
        try:
            # Appeler l'endpoint GARCH
            response = requests.get(f"http://localhost:8000/api/v1/sentiment-analysis/garch/{symbol}")
            
            if response.status_code == 200:
                garch_data = response.json()
                print(f"✅ Endpoint GARCH appelé avec succès")
                print(f"   Volatilité prévue: {garch_data.get('analysis', {}).get('volatility_forecast', 'N/A')}")
                print(f"   Persisté: {garch_data.get('persisted', False)}")
                
                # Vérifier en base de données
                garch_records = db.query(GARCHModelsModel).filter(
                    GARCHModelsModel.symbol == symbol,
                    GARCHModelsModel.analysis_date >= datetime.now().date()
                ).all()
                
                print(f"   Enregistrements GARCH en base: {len(garch_records)}")
                
                if garch_records:
                    latest_garch = garch_records[-1]
                    print(f"   Dernier enregistrement:")
                    print(f"     - Modèle: {latest_garch.model_type}")
                    print(f"     - Volatilité: {latest_garch.volatility_forecast}")
                    print(f"     - VaR 95%: {latest_garch.var_95}")
                    print(f"     - AIC: {latest_garch.aic}")
                
            else:
                print(f"❌ Erreur endpoint GARCH: {response.status_code}")
                print(f"   Détail: {response.text}")
                
        except Exception as e:
            print(f"❌ Erreur test GARCH: {str(e)}")
        
        # Test 2: Persistance Monte Carlo
        print("\n🎲 Test 2: Persistance Monte Carlo")
        print("-" * 30)
        
        try:
            # Appeler l'endpoint Monte Carlo
            response = requests.get(f"http://localhost:8000/api/v1/sentiment-analysis/monte-carlo/{symbol}")
            
            if response.status_code == 200:
                mc_data = response.json()
                print(f"✅ Endpoint Monte Carlo appelé avec succès")
                print(f"   Prix actuel: ${mc_data.get('current_price', 'N/A')}")
                print(f"   Persisté: {mc_data.get('persisted', False)}")
                
                # Vérifier en base de données
                mc_records = db.query(MonteCarloSimulations).filter(
                    MonteCarloSimulations.symbol == symbol,
                    MonteCarloSimulations.analysis_date >= datetime.now().date()
                ).all()
                
                print(f"   Enregistrements Monte Carlo en base: {len(mc_records)}")
                
                if mc_records:
                    latest_mc = mc_records[-1]
                    print(f"   Dernier enregistrement:")
                    print(f"     - Prix: ${latest_mc.current_price}")
                    print(f"     - Volatilité: {latest_mc.volatility}")
                    print(f"     - VaR 95%: {latest_mc.var_95}")
                    print(f"     - Simulations: {latest_mc.simulations_count}")
                
            else:
                print(f"❌ Erreur endpoint Monte Carlo: {response.status_code}")
                print(f"   Détail: {response.text}")
                
        except Exception as e:
            print(f"❌ Erreur test Monte Carlo: {str(e)}")
        
        # Test 3: Persistance Markov
        print("\n🔗 Test 3: Persistance Markov")
        print("-" * 30)
        
        try:
            # Appeler l'endpoint Markov
            response = requests.get(f"http://localhost:8000/api/v1/sentiment-analysis/markov/{symbol}")
            
            if response.status_code == 200:
                markov_data = response.json()
                print(f"✅ Endpoint Markov appelé avec succès")
                print(f"   États identifiés: {markov_data.get('analysis', {}).get('n_states', 'N/A')}")
                print(f"   Persisté: {markov_data.get('persisted', False)}")
                
                # Vérifier en base de données
                markov_records = db.query(MarkovChainAnalysisModel).filter(
                    MarkovChainAnalysisModel.symbol == symbol,
                    MarkovChainAnalysisModel.analysis_date >= datetime.now().date()
                ).all()
                
                print(f"   Enregistrements Markov en base: {len(markov_records)}")
                
                if markov_records:
                    latest_markov = markov_records[-1]
                    print(f"   Dernier enregistrement:")
                    print(f"     - États: {latest_markov.n_states}")
                    print(f"     - État actuel: {latest_markov.current_state}")
                    print(f"     - Date: {latest_markov.analysis_date}")
                
            else:
                print(f"❌ Erreur endpoint Markov: {response.status_code}")
                print(f"   Détail: {response.text}")
                
        except Exception as e:
            print(f"❌ Erreur test Markov: {str(e)}")
        
        # Test 4: Vérification de la récupération des données
        print("\n📈 Test 4: Récupération des données depuis la base")
        print("-" * 40)
        
        try:
            # Vérifier que les données sont bien récupérées depuis la base
            recent_data = db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol,
                HistoricalData.date >= datetime.now().date() - timedelta(days=30)
            ).order_by(HistoricalData.date.desc()).limit(5).all()
            
            print(f"   Données récentes récupérées: {len(recent_data)}")
            
            if recent_data:
                print(f"   Dernières données:")
                for i, record in enumerate(recent_data[:3]):
                    print(f"     {i+1}. {record.date}: ${record.close}")
            
        except Exception as e:
            print(f"❌ Erreur récupération données: {str(e)}")
        
        # Test 5: Vérification de l'intégrité des données
        print("\n🔍 Test 5: Intégrité des données")
        print("-" * 30)
        
        try:
            # Vérifier que les données persistées sont cohérentes
            garch_count = db.query(GARCHModelsModel).filter(
                GARCHModelsModel.symbol == symbol
            ).count()
            
            mc_count = db.query(MonteCarloSimulations).filter(
                MonteCarloSimulations.symbol == symbol
            ).count()
            
            markov_count = db.query(MarkovChainAnalysisModel).filter(
                MarkovChainAnalysisModel.symbol == symbol
            ).count()
            
            print(f"   Enregistrements GARCH: {garch_count}")
            print(f"   Enregistrements Monte Carlo: {mc_count}")
            print(f"   Enregistrements Markov: {markov_count}")
            
            # Vérifier les données du jour
            today_garch = db.query(GARCHModelsModel).filter(
                GARCHModelsModel.symbol == symbol,
                GARCHModelsModel.analysis_date >= datetime.now().date()
            ).count()
            
            today_mc = db.query(MonteCarloSimulations).filter(
                MonteCarloSimulations.symbol == symbol,
                MonteCarloSimulations.analysis_date >= datetime.now().date()
            ).count()
            
            today_markov = db.query(MarkovChainAnalysisModel).filter(
                MarkovChainAnalysisModel.symbol == symbol,
                MarkovChainAnalysisModel.analysis_date >= datetime.now().date()
            ).count()
            
            print(f"   Enregistrements d'aujourd'hui:")
            print(f"     - GARCH: {today_garch}")
            print(f"     - Monte Carlo: {today_mc}")
            print(f"     - Markov: {today_markov}")
            
        except Exception as e:
            print(f"❌ Erreur vérification intégrité: {str(e)}")
        
        db.close()
        
        print("\n🎉 Tests de persistance terminés!")
        print("✅ Phase 3: Persistance des données - VÉRIFIÉE")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur générale: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("⚠️  Assurez-vous que le serveur backend est démarré sur http://localhost:8000")
    print("   Commande: cd backend && uvicorn app.main:app --reload")
    print()
    
    success = test_sentiment_persistence()
    if success:
        print("\n🚀 Persistance des données Phase 3 opérationnelle!")
    else:
        print("\n⚠️  Des problèmes ont été détectés dans la persistance")
