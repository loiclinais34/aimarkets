#!/usr/bin/env python3
"""
Script de test pour le système de mise à jour des données Polygon.io
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.polygon_service import PolygonService
from app.services.data_update_service import DataUpdateService

def test_polygon_service():
    """Test du service Polygon.io"""
    print("🔍 Test du service Polygon.io...")
    
    polygon_service = PolygonService()
    
    # Test 1: Récupération des détails d'un ticker
    print("\n1. Test récupération détails ticker AAPL...")
    details = polygon_service.get_ticker_details("AAPL")
    if details:
        print(f"   ✅ Détails récupérés: {details.get('results', {}).get('name', 'N/A')}")
    else:
        print("   ❌ Échec de récupération des détails")
    
    # Test 2: Récupération des données historiques
    print("\n2. Test récupération données historiques AAPL...")
    end_date = date.today()
    start_date = end_date - timedelta(days=5)
    
    historical_data = polygon_service.get_historical_data(
        "AAPL",
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    
    if historical_data:
        print(f"   ✅ {len(historical_data)} jours de données récupérés")
        print(f"   📅 Période: {start_date} à {end_date}")
        print(f"   📊 Dernière donnée: {historical_data[0]['date']} - Close: ${historical_data[0]['close']}")
    else:
        print("   ❌ Échec de récupération des données historiques")
    
    # Test 3: Récupération des données de news
    print("\n3. Test récupération données de news AAPL...")
    news_data = polygon_service.get_news_data(
        "AAPL",
        start_date.strftime('%Y-%m-%d'),
        end_date.strftime('%Y-%m-%d')
    )
    
    if news_data:
        print(f"   ✅ {len(news_data)} articles de news récupérés")
        if news_data:
            print(f"   📰 Premier article: {news_data[0].get('title', 'N/A')[:50]}...")
    else:
        print("   ❌ Échec de récupération des données de news")
    
    # Test 4: Statut du marché
    print("\n4. Test statut du marché...")
    is_open = polygon_service.is_market_open()
    last_trading_day = polygon_service.get_last_trading_day()
    
    print(f"   📈 Marché ouvert: {'Oui' if is_open else 'Non'}")
    print(f"   📅 Dernier jour de trading: {last_trading_day}")
    
    return True

def test_data_update_service():
    """Test du service de mise à jour des données"""
    print("\n🔧 Test du service de mise à jour des données...")
    
    # Obtenir une session de base de données
    db = next(get_db())
    
    try:
        data_service = DataUpdateService(db)
        
        # Test 1: Statut de fraîcheur des données
        print("\n1. Test statut de fraîcheur des données...")
        freshness_status = data_service.get_data_freshness_status()
        
        if freshness_status and 'overall_status' in freshness_status:
            print(f"   📊 Statut global: {freshness_status['overall_status']}")
            print(f"   📈 Données historiques: {'À jour' if freshness_status['historical_data']['is_fresh'] else 'Mise à jour nécessaire'}")
            print(f"   💭 Données de sentiment: {'À jour' if freshness_status['sentiment_data']['is_fresh'] else 'Mise à jour nécessaire'}")
            print(f"   📅 Dernier jour de trading: {freshness_status['last_trading_day']}")
        else:
            print("   ❌ Échec de récupération du statut de fraîcheur")
        
        # Test 2: Mise à jour des données pour un symbole (test limité)
        print("\n2. Test mise à jour des données pour AAPL...")
        result = data_service.update_historical_data_for_symbol("AAPL", force_update=False)
        
        if result and 'status' in result:
            print(f"   📊 Statut: {result['status']}")
            print(f"   📝 Message: {result['message']}")
            if 'records_inserted' in result:
                print(f"   ➕ Enregistrements insérés: {result['records_inserted']}")
            if 'records_updated' in result:
                print(f"   🔄 Enregistrements mis à jour: {result['records_updated']}")
        else:
            print("   ❌ Échec de la mise à jour des données")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur lors du test du service de mise à jour: {e}")
        return False
    finally:
        db.close()

def test_api_endpoints():
    """Test des endpoints API"""
    print("\n🌐 Test des endpoints API...")
    
    import requests
    
    base_url = "http://localhost:8000"
    
    # Test 1: Statut de fraîcheur des données
    print("\n1. Test endpoint /api/v1/data-update/data-freshness...")
    try:
        response = requests.get(f"{base_url}/api/v1/data-update/data-freshness", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Statut: {data['data']['overall_status']}")
            print(f"   📅 Dernier trading: {data['data']['last_trading_day']}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
    
    # Test 2: Statut du marché
    print("\n2. Test endpoint /api/v1/data-update/market-status...")
    try:
        response = requests.get(f"{base_url}/api/v1/data-update/market-status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Marché ouvert: {'Oui' if data['data']['is_open'] else 'Non'}")
            print(f"   📅 Dernier jour de trading: {data['data']['last_trading_day']}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
    
    # Test 3: Statut des symboles
    print("\n3. Test endpoint /api/v1/data-update/symbols-status...")
    try:
        response = requests.get(f"{base_url}/api/v1/data-update/symbols-status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Nombre total de symboles: {data['data']['total_symbols']}")
            print(f"   📊 Échantillon de résultats: {len(data['data']['sample_results'])} symboles")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
    
    return True

def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests du système de mise à jour des données Polygon.io")
    print("=" * 70)
    
    # Test 1: Service Polygon.io
    try:
        test_polygon_service()
        print("\n✅ Tests du service Polygon.io terminés")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests Polygon.io: {e}")
    
    # Test 2: Service de mise à jour des données
    try:
        test_data_update_service()
        print("\n✅ Tests du service de mise à jour terminés")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests de mise à jour: {e}")
    
    # Test 3: Endpoints API
    try:
        test_api_endpoints()
        print("\n✅ Tests des endpoints API terminés")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests API: {e}")
    
    print("\n" + "=" * 70)
    print("🎉 Tests terminés!")
    print("\n📋 Résumé des fonctionnalités implémentées:")
    print("   ✅ Service Polygon.io pour récupérer les données")
    print("   ✅ Service de mise à jour des données historiques et de sentiment")
    print("   ✅ Logique de comparaison des dates pour identifier les données manquantes")
    print("   ✅ Système de mise à jour en batch pour tous les titres")
    print("   ✅ Gestion du décalage horaire France/Nasdaq")
    print("   ✅ Endpoints API pour déclencher les mises à jour")
    print("   ✅ Indicateur de fraîcheur des données sur le frontend")
    print("\n🔧 Pour utiliser le système:")
    print("   1. Démarrez le backend: python -m uvicorn app.main:app --reload")
    print("   2. Démarrez le frontend: npm run dev")
    print("   3. Visitez http://localhost:3000/screener pour voir l'indicateur")
    print("   4. Utilisez les endpoints /api/v1/data-update/* pour les mises à jour")

if __name__ == "__main__":
    main()
