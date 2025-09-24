#!/usr/bin/env python3
"""
Script de test pour le système de recalcul des indicateurs
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.indicators_recalculation_service import IndicatorsRecalculationService
from app.core.database import get_db
from datetime import date, timedelta

def test_indicators_recalculation():
    """Test du service de recalcul des indicateurs"""
    print("🔧 Test du service de recalcul des indicateurs...")
    
    # Obtenir une session de base de données
    db = next(get_db())
    
    try:
        indicators_service = IndicatorsRecalculationService(db)
        
        # Test 1: Recalcul des indicateurs techniques pour un symbole
        print("\n1. Test recalcul des indicateurs techniques...")
        test_symbol = "AAPL"  # Utiliser un symbole qui existe probablement
        
        result = indicators_service.recalculate_technical_indicators(test_symbol)
        print(f"   Résultat: {result['success']}")
        if result['success']:
            print(f"   Dates traitées: {result['processed_dates']}")
            print(f"   Total dates: {result['total_dates']}")
        else:
            print(f"   Erreur: {result['error']}")
        
        # Test 2: Recalcul des indicateurs de sentiment
        print("\n2. Test recalcul des indicateurs de sentiment...")
        result = indicators_service.recalculate_sentiment_indicators(test_symbol)
        print(f"   Résultat: {result['success']}")
        if result['success']:
            print(f"   Dates traitées: {result['processed_dates']}")
            print(f"   Total dates: {result['total_dates']}")
        else:
            print(f"   Erreur: {result['error']}")
        
        # Test 3: Recalcul des corrélations
        print("\n3. Test recalcul des corrélations...")
        test_symbols = ["AAPL", "MSFT", "GOOGL"]  # Symboles de test
        result = indicators_service.recalculate_correlations(test_symbols)
        print(f"   Résultat: {result['success']}")
        if result['success']:
            print(f"   Corrélations traitées: {result['processed_correlations']}")
            print(f"   Symboles: {result['symbols_count']}")
        else:
            print(f"   Erreur: {result['error']}")
        
        # Test 4: Recalcul complet
        print("\n4. Test recalcul complet...")
        result = indicators_service.recalculate_all_indicators(test_symbols)
        print(f"   Résultat global: {result['success']}")
        print(f"   Symboles traités: {result['symbols_processed']}")
        print(f"   Indicateurs techniques: {result['technical_indicators']['success']} succès, {result['technical_indicators']['failed']} échecs")
        print(f"   Indicateurs de sentiment: {result['sentiment_indicators']['success']} succès, {result['sentiment_indicators']['failed']} échecs")
        print(f"   Corrélations: {result['correlations']['success']} succès, {result['correlations']['failed']} échecs")
        
        if result['errors']:
            print(f"   Erreurs: {len(result['errors'])}")
            for error in result['errors'][:3]:  # Afficher les 3 premières erreurs
                print(f"     - {error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        return False
    finally:
        db.close()

def test_api_endpoints():
    """Test des endpoints API"""
    print("\n🌐 Test des endpoints API...")
    
    import requests
    
    base_url = "http://localhost:8000"
    
    # Test 1: Statut des indicateurs
    print("\n1. Test endpoint /api/v1/indicators/status/AAPL...")
    try:
        response = requests.get(f"{base_url}/api/v1/indicators/status/AAPL", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Statut récupéré: {data['data']['overall_status']}")
            print(f"   Indicateurs techniques: {data['data']['technical_indicators']['count']}")
            print(f"   Indicateurs de sentiment: {data['data']['sentiment_indicators']['count']}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
    
    # Test 2: Recalcul des indicateurs techniques
    print("\n2. Test endpoint /api/v1/indicators/recalculate-technical/AAPL...")
    try:
        response = requests.post(f"{base_url}/api/v1/indicators/recalculate-technical/AAPL", timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Recalcul réussi: {data['data']['processed_dates']} dates")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            print(f"   Détail: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")
    
    # Test 3: Recalcul des corrélations
    print("\n3. Test endpoint /api/v1/indicators/recalculate-correlations...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/indicators/recalculate-correlations",
            json=["AAPL", "MSFT"],  # Envoyer directement la liste
            timeout=30
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Corrélations recalculées: {data['data']['processed_correlations']}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            print(f"   Détail: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")

def test_integration_with_data_update():
    """Test de l'intégration avec le service de mise à jour des données"""
    print("\n🔄 Test de l'intégration avec la mise à jour des données...")
    
    import requests
    
    base_url = "http://localhost:8000"
    
    # Test de mise à jour des données historiques (qui devrait déclencher le recalcul automatique)
    print("\n1. Test mise à jour des données historiques avec recalcul automatique...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/data-update/update-historical/AAPL",
            json={"force_update": True},
            timeout=60
        )
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Mise à jour réussie: {data['data']['total_records']} enregistrements")
            print(f"   Indicateurs recalculés: {data['data']['indicators_recalculated']}")
            if data['data']['indicators_recalculated']:
                print(f"   Dates d'indicateurs traitées: {data['data']['indicators_processed_dates']}")
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            print(f"   Détail: {response.text}")
    except Exception as e:
        print(f"   ❌ Erreur de connexion: {e}")

def main():
    """Fonction principale de test"""
    print("🚀 Test du système de recalcul des indicateurs")
    print("=" * 60)
    
    # Test 1: Service de recalcul
    try:
        success = test_indicators_recalculation()
        print(f"\n✅ Tests du service de recalcul terminés ({'Succès' if success else 'Échec'})")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests du service: {e}")
    
    # Test 2: Endpoints API
    try:
        test_api_endpoints()
        print("\n✅ Tests des endpoints API terminés")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests API: {e}")
    
    # Test 3: Intégration
    try:
        test_integration_with_data_update()
        print("\n✅ Tests d'intégration terminés")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests d'intégration: {e}")
    
    print("\n" + "=" * 60)
    print("🎯 Résumé:")
    print("   1. Service de recalcul des indicateurs créé")
    print("   2. Intégration automatique avec la mise à jour des données")
    print("   3. Endpoints API pour le recalcul manuel")
    print("   4. Recalcul des indicateurs techniques, de sentiment et des corrélations")
    print("   5. Gestion robuste des erreurs et logging détaillé")

if __name__ == "__main__":
    main()
