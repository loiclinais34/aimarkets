#!/usr/bin/env python3
"""
Test complet de l'infrastructure d'analyse de trading avancée.
"""

import sys
import os
import json
import requests
from datetime import datetime
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_api_endpoints():
    """Test des endpoints API."""
    base_url = "http://localhost:8000"
    results = {
        "timestamp": datetime.now().isoformat(),
        "endpoints_tested": {},
        "summary": {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "success_rate": 0.0
        }
    }
    
    # Liste des endpoints à tester
    endpoints = [
        {
            "name": "technical_analysis_signals",
            "url": f"{base_url}/api/v1/technical-analysis/signals/AAPL",
            "method": "GET"
        },
        {
            "name": "sentiment_analysis_garch",
            "url": f"{base_url}/api/v1/sentiment-analysis/garch/AAPL",
            "method": "GET"
        },
        {
            "name": "market_indicators_volatility",
            "url": f"{base_url}/api/v1/market-indicators/volatility/AAPL",
            "method": "GET"
        }
    ]
    
    print("🔍 Test des endpoints API...")
    
    for endpoint in endpoints:
        try:
            print(f"  Testing {endpoint['name']}...")
            response = requests.get(endpoint['url'], timeout=30)
            
            results["summary"]["total_tests"] += 1
            
            if response.status_code == 200:
                results["endpoints_tested"][endpoint['name']] = {
                    "status": "success",
                    "status_code": response.status_code,
                    "response_size": len(response.text),
                    "timestamp": datetime.now().isoformat()
                }
                results["summary"]["passed_tests"] += 1
                print(f"    ✅ Success: {response.status_code}")
            else:
                results["endpoints_tested"][endpoint['name']] = {
                    "status": "error",
                    "status_code": response.status_code,
                    "error": response.text[:200],
                    "timestamp": datetime.now().isoformat()
                }
                results["summary"]["failed_tests"] += 1
                print(f"    ❌ Error: {response.status_code} - {response.text[:100]}")
                
        except Exception as e:
            results["summary"]["total_tests"] += 1
            results["summary"]["failed_tests"] += 1
            results["endpoints_tested"][endpoint['name']] = {
                "status": "exception",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            print(f"    ❌ Exception: {str(e)}")
    
    # Calculer le taux de succès
    if results["summary"]["total_tests"] > 0:
        results["summary"]["success_rate"] = (results["summary"]["passed_tests"] / results["summary"]["total_tests"]) * 100
    
    return results

def test_services():
    """Test des services directement."""
    print("🔍 Test des services...")
    
    try:
        from app.services.polygon_service import PolygonService
        from app.services.technical_analysis import TechnicalIndicators, CandlestickPatterns, SupportResistanceAnalyzer, SignalGenerator
        from app.services.sentiment_analysis import GARCHModels, MonteCarloSimulation, MarkovChainAnalysis, VolatilityForecaster
        from app.services.market_indicators import VolatilityIndicators, CorrelationAnalyzer, MomentumIndicators
        
        print("  ✅ Tous les services importés avec succès")
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur d'importation des services: {e}")
        return False

def test_data_retrieval():
    """Test de récupération des données."""
    print("🔍 Test de récupération des données...")
    
    try:
        from app.services.polygon_service import PolygonService
        import pandas as pd
        from datetime import datetime, timedelta
        
        polygon_service = PolygonService()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        data = polygon_service.get_historical_data(
            symbol="AAPL",
            from_date=start_date.strftime('%Y-%m-%d'),
            to_date=end_date.strftime('%Y-%m-%d')
        )
        
        if data and len(data) > 0:
            print(f"  ✅ Données récupérées: {len(data)} enregistrements")
            
            # Test de conversion en DataFrame
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            print(f"  ✅ DataFrame créé: {len(df)} lignes, {len(df.columns)} colonnes")
            return True
        else:
            print("  ❌ Aucune donnée récupérée")
            return False
            
    except Exception as e:
        print(f"  ❌ Erreur de récupération des données: {e}")
        return False

def test_technical_analysis():
    """Test de l'analyse technique."""
    print("🔍 Test de l'analyse technique...")
    
    try:
        from app.services.polygon_service import PolygonService
        from app.services.technical_analysis import TechnicalIndicators
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Récupérer les données
        polygon_service = PolygonService()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        data = polygon_service.get_historical_data(
            symbol="AAPL",
            from_date=start_date.strftime('%Y-%m-%d'),
            to_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not data:
            print("  ❌ Aucune donnée pour le test")
            return False
        
        # Convertir en DataFrame
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Test des indicateurs
        rsi = TechnicalIndicators.rsi(df['close'], period=14)
        macd_result = TechnicalIndicators.macd(df['close'])
        bb_result = TechnicalIndicators.bollinger_bands(df['close'])
        
        print(f"  ✅ RSI calculé: {len(rsi)} valeurs")
        print(f"  ✅ MACD calculé: {len(macd_result['macd'])} valeurs")
        print(f"  ✅ Bollinger Bands calculées: {len(bb_result['upper'])} valeurs")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Erreur d'analyse technique: {e}")
        return False

def main():
    """Fonction principale de test."""
    print("🚀 Test complet de l'infrastructure d'analyse de trading avancée")
    print("=" * 70)
    
    # Test des services
    services_ok = test_services()
    
    # Test de récupération des données
    data_ok = test_data_retrieval()
    
    # Test de l'analyse technique
    technical_ok = test_technical_analysis()
    
    # Test des endpoints API
    api_results = test_api_endpoints()
    
    # Résumé
    print("\n" + "=" * 70)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 70)
    
    print(f"Services: {'✅ OK' if services_ok else '❌ ÉCHEC'}")
    print(f"Données: {'✅ OK' if data_ok else '❌ ÉCHEC'}")
    print(f"Analyse technique: {'✅ OK' if technical_ok else '❌ ÉCHEC'}")
    print(f"Endpoints API: {api_results['summary']['passed_tests']}/{api_results['summary']['total_tests']} réussis ({api_results['summary']['success_rate']:.1f}%)")
    
    # Sauvegarder les résultats
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"infrastructure_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump({
            "services_test": services_ok,
            "data_test": data_ok,
            "technical_analysis_test": technical_ok,
            "api_endpoints_test": api_results
        }, f, indent=2)
    
    print(f"\n📁 Résultats sauvegardés dans: {results_file}")
    
    # Déterminer le succès global
    global_success = services_ok and data_ok and technical_ok and api_results['summary']['success_rate'] > 50
    
    print(f"\n🎯 RÉSULTAT GLOBAL: {'✅ SUCCÈS' if global_success else '❌ ÉCHEC'}")
    
    return global_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
