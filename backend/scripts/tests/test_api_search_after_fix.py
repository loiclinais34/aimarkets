#!/usr/bin/env python3
"""
Script pour tester l'API de recherche après correction de l'erreur de syntaxe
"""

import sys
import os
import requests
import json
from datetime import datetime
from typing import Dict, Any

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class APISearchTester:
    """Testeur de l'API de recherche après correction"""
    
    def __init__(self):
        """Initialise le testeur"""
        self.base_url = "http://localhost:8000"
        self.search_endpoint = f"{self.base_url}/api/v1/advanced-analysis/opportunities/search"
        
    def test_search_endpoint(self) -> Dict[str, Any]:
        """Teste l'endpoint de recherche d'opportunités"""
        print("🔍 Test de l'endpoint de recherche d'opportunités...")
        
        # Paramètres de test
        params = {
            "min_score": 0.2,
            "max_risk": "HIGH",
            "limit": 10,
            "sort_by": "composite_score",
            "sort_order": "desc"
        }
        
        try:
            response = requests.get(self.search_endpoint, params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Recherche réussie: {len(data.get('opportunities', []))} opportunités trouvées")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "opportunities_count": len(data.get('opportunities', [])),
                    "data": data
                }
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de connexion: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def test_generate_endpoint(self) -> Dict[str, Any]:
        """Teste l'endpoint de génération d'opportunités"""
        print("🔧 Test de l'endpoint de génération d'opportunités...")
        
        generate_endpoint = f"{self.base_url}/api/v1/advanced-analysis/generate-daily-opportunities"
        
        # Paramètres de test
        params = {
            "limit_symbols": 5,
            "time_horizon": 30,
            "include_ml": True
        }
        
        try:
            response = requests.post(generate_endpoint, params=params, timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Génération réussie: {data.get('summary', {}).get('total_opportunities_generated', 0)} opportunités générées")
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "generated_count": data.get('summary', {}).get('total_opportunities_generated', 0),
                    "data": data
                }
            else:
                print(f"❌ Erreur HTTP {response.status_code}: {response.text}")
                return {
                    "success": False,
                    "status_code": response.status_code,
                    "error": response.text
                }
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur de connexion: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_complete_test(self) -> Dict[str, Any]:
        """Exécute le test complet"""
        print("🚀 Démarrage du test de l'API après correction")
        print("=" * 80)
        
        # Test de l'endpoint de recherche
        search_result = self.test_search_endpoint()
        
        # Test de l'endpoint de génération
        generate_result = self.test_generate_endpoint()
        
        # Résumé des résultats
        results = {
            "test_date": datetime.now().isoformat(),
            "search_endpoint_test": search_result,
            "generate_endpoint_test": generate_result,
            "overall_success": search_result.get("success", False) and generate_result.get("success", False)
        }
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Affiche un résumé des résultats"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DU TEST DE L'API APRÈS CORRECTION")
        print("=" * 80)
        
        # Test de recherche
        search_test = results["search_endpoint_test"]
        if search_test.get("success"):
            print(f"✅ ENDPOINT DE RECHERCHE: OK")
            print(f"  • Status: {search_test['status_code']}")
            print(f"  • Opportunités trouvées: {search_test['opportunities_count']}")
        else:
            print(f"❌ ENDPOINT DE RECHERCHE: ÉCHEC")
            print(f"  • Status: {search_test.get('status_code', 'N/A')}")
            print(f"  • Erreur: {search_test.get('error', 'N/A')}")
        
        # Test de génération
        generate_test = results["generate_endpoint_test"]
        if generate_test.get("success"):
            print(f"✅ ENDPOINT DE GÉNÉRATION: OK")
            print(f"  • Status: {generate_test['status_code']}")
            print(f"  • Opportunités générées: {generate_test['generated_count']}")
        else:
            print(f"❌ ENDPOINT DE GÉNÉRATION: ÉCHEC")
            print(f"  • Status: {generate_test.get('status_code', 'N/A')}")
            print(f"  • Erreur: {generate_test.get('error', 'N/A')}")
        
        # Statut global
        if results["overall_success"]:
            print(f"\n🎯 STATUT GLOBAL: ✅ TOUS LES TESTS RÉUSSIS")
            print("   L'API fonctionne correctement avec les optimisations")
        else:
            print(f"\n🎯 STATUT GLOBAL: ❌ CERTAINS TESTS ONT ÉCHOUÉ")
            print("   Vérifiez les erreurs ci-dessus")

def main():
    """Fonction principale"""
    tester = APISearchTester()
    
    try:
        # Exécuter le test complet
        results = tester.run_complete_test()
        
        # Afficher le résumé
        tester.print_summary(results)
        
        # Sauvegarder les résultats
        filename = "api_search_after_fix_test.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📁 Résultats sauvegardés dans {filename}")
        print(f"\n✅ Test terminé avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
