#!/usr/bin/env python3
"""
Script de test pour vérifier l'API PLTR et diagnostiquer le problème frontend
"""

import requests
import json

def test_pltr_api_detailed():
    base_url = "http://localhost:8000/api/v1/backtesting"
    
    print("🔍 Diagnostic détaillé de l'API PLTR")
    print("=" * 60)
    
    # 1. Test de la liste des symboles
    print("1. Test de la liste des symboles...")
    try:
        response = requests.get(f"{base_url}/symbols", timeout=10)
        if response.status_code == 200:
            data = response.json()
            pltr_symbol = None
            for symbol in data.get('symbols', []):
                if symbol['symbol'] == 'PLTR':
                    pltr_symbol = symbol
                    break
            
            if pltr_symbol:
                print(f"✅ PLTR trouvé: {pltr_symbol['prediction_count']} prédictions, {pltr_symbol['model_count']} modèles")
            else:
                print("❌ PLTR non trouvé dans la liste des symboles")
                return False
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False
    
    # 2. Test de la récupération des modèles PLTR
    print("\n2. Test de la récupération des modèles PLTR...")
    try:
        response = requests.get(f"{base_url}/symbols/PLTR/models", timeout=30)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            print(f"✅ {len(models)} modèles récupérés pour PLTR")
            
            # Analyser les modèles
            if models:
                prediction_counts = [m['prediction_count'] for m in models]
                max_predictions = max(prediction_counts)
                min_predictions = min(prediction_counts)
                avg_predictions = sum(prediction_counts) / len(prediction_counts)
                
                print(f"📊 Statistiques des prédictions:")
                print(f"   - Maximum: {max_predictions}")
                print(f"   - Minimum: {min_predictions}")
                print(f"   - Moyenne: {avg_predictions:.1f}")
                
                # Trouver les modèles avec le plus de prédictions
                top_models = sorted(models, key=lambda x: x['prediction_count'], reverse=True)[:5]
                print(f"\n🏆 Top 5 modèles avec le plus de prédictions:")
                for i, model in enumerate(top_models, 1):
                    print(f"   {i}. {model['name']} - {model['prediction_count']} prédictions")
                
                return True
            else:
                print("❌ Aucun modèle retourné")
                return False
        else:
            print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    success = test_pltr_api_detailed()
    if success:
        print("\n🎉 L'API fonctionne parfaitement ! Le problème vient du frontend.")
        print("💡 Solutions possibles:")
        print("   1. Vider le cache du navigateur (Ctrl+F5)")
        print("   2. Redémarrer le serveur frontend")
        print("   3. Vérifier la console du navigateur pour les erreurs JavaScript")
    else:
        print("\n💥 Des erreurs ont été détectées dans l'API.")
