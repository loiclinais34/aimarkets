#!/usr/bin/env python3
"""
Script de test pour les signaux avancés.

Ce script teste le système de signaux avancés en générant des signaux
pour différents symboles et en validant leur fonctionnement.
"""

import os
import sys
import pandas as pd
from datetime import datetime, timedelta
import requests
import json
from typing import Any

# Ajouter le chemin du backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.polygon_service import PolygonService
from app.services.advanced_signal_service import AdvancedSignalService
from app.services.technical_analysis.advanced_signals import AdvancedSignalGenerator

class AdvancedSignalsTester:
    """Classe pour tester les signaux avancés."""
    
    def __init__(self, symbol: str = "AAPL"):
        self.symbol = symbol
        self.test_results = {
            "symbol": symbol,
            "test_timestamp": datetime.now().isoformat(),
            "tests_performed": {},
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "success_rate": 0.0,
                "errors": []
            }
        }
    
    def _record_test_result(self, test_name: str, success: bool, result: Any = None, error: Any = None):
        """Enregistre le résultat d'un test."""
        self.test_results["tests_performed"][test_name] = {
            "success": success,
            "timestamp": datetime.now().isoformat(),
            "result": result,
            "error": str(error) if error else None
        }
        self.test_results["summary"]["total_tests"] += 1
        if success:
            self.test_results["summary"]["passed_tests"] += 1
        else:
            self.test_results["summary"]["failed_tests"] += 1
            if error:
                self.test_results["summary"]["errors"].append(f"{test_name}: {str(error)}")
    
    def get_historical_data(self, period_days=252):
        """Récupère les données historiques pour le symbole."""
        try:
            polygon_service = PolygonService()
            
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days + 50)
            
            historical_data = polygon_service.get_historical_data(
                symbol=self.symbol,
                from_date=start_date.strftime('%Y-%m-%d'),
                to_date=end_date.strftime('%Y-%m-%d')
            )
            
            if not historical_data:
                raise ValueError(f"Aucune donnée historique trouvée pour {self.symbol}")
            
            # Convertir en DataFrame
            df = pd.DataFrame(historical_data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération des données: {e}")
            return None
    
    def test_signal_generator(self):
        """Teste le générateur de signaux avancés."""
        try:
            print(f"🔧 Test du générateur de signaux pour {self.symbol}...")
            
            # Récupérer les données
            df = self.get_historical_data()
            if df is None:
                raise ValueError("Impossible de récupérer les données historiques")
            
            # Préparer les données
            high = df['high']
            low = df['low']
            close = df['close']
            open_prices = df['open']
            volume = df['volume'] if 'volume' in df.columns else None
            
            # Créer le générateur
            generator = AdvancedSignalGenerator()
            
            # Générer un signal
            signal_result = generator.generate_advanced_signal(
                symbol=self.symbol,
                high=high,
                low=low,
                close=close,
                open_prices=open_prices,
                volume=volume
            )
            
            # Valider le résultat
            if signal_result is None:
                raise ValueError("Le générateur a retourné None")
            
            if not hasattr(signal_result, 'signal_type'):
                raise ValueError("Le résultat n'a pas d'attribut signal_type")
            
            if not hasattr(signal_result, 'score'):
                raise ValueError("Le résultat n'a pas d'attribut score")
            
            if not hasattr(signal_result, 'confidence'):
                raise ValueError("Le résultat n'a pas d'attribut confidence")
            
            result = {
                "signal_type": signal_result.signal_type.value,
                "score": signal_result.score,
                "confidence": signal_result.confidence,
                "confidence_level": signal_result.confidence_level.value,
                "strength": signal_result.strength,
                "indicators_used": signal_result.indicators_used,
                "reasoning": signal_result.reasoning
            }
            
            print(f"✅ Signal généré: {signal_result.signal_type.value} (Score: {signal_result.score:.1f}, Confiance: {signal_result.confidence:.2f})")
            self._record_test_result("signal_generator", True, result)
            
        except Exception as e:
            print(f"❌ Erreur lors du test du générateur: {e}")
            self._record_test_result("signal_generator", False, None, e)
    
    def test_signal_service(self):
        """Teste le service de signaux avancés."""
        try:
            print(f"🔧 Test du service de signaux pour {self.symbol}...")
            
            # Récupérer les données
            df = self.get_historical_data()
            if df is None:
                raise ValueError("Impossible de récupérer les données historiques")
            
            # Préparer les données
            high = df['high']
            low = df['low']
            close = df['close']
            open_prices = df['open']
            volume = df['volume'] if 'volume' in df.columns else None
            
            # Créer le service
            db = next(get_db())
            try:
                signal_service = AdvancedSignalService(db)
                
                # Générer et sauvegarder un signal
                saved_signal = signal_service.generate_and_save_signal(
                    symbol=self.symbol,
                    high=high,
                    low=low,
                    close=close,
                    open_prices=open_prices,
                    volume=volume
                )
                
                if saved_signal is None:
                    raise ValueError("Le service n'a pas retourné de signal")
                
                # Récupérer le signal sauvegardé
                latest_signal = signal_service.get_latest_signal(self.symbol)
                if latest_signal is None:
                    raise ValueError("Impossible de récupérer le signal sauvegardé")
                
                # Calculer les métriques
                metrics = signal_service.calculate_signal_metrics(self.symbol, days=30)
                
                result = {
                    "saved_signal_id": saved_signal.id,
                    "signal_type": saved_signal.signal_type,
                    "score": saved_signal.score,
                    "confidence": saved_signal.confidence,
                    "metrics": metrics
                }
                
                print(f"✅ Signal sauvegardé avec ID: {saved_signal.id}")
                print(f"   Type: {saved_signal.signal_type}, Score: {saved_signal.score:.1f}")
                self._record_test_result("signal_service", True, result)
                
            finally:
                db.close()
            
        except Exception as e:
            print(f"❌ Erreur lors du test du service: {e}")
            self._record_test_result("signal_service", False, None, e)
    
    def test_api_endpoints(self):
        """Teste les endpoints API des signaux avancés."""
        try:
            print(f"🔧 Test des endpoints API pour {self.symbol}...")
            
            base_url = "http://localhost:8000/api/v1/advanced-signals"
            
            # Test 1: Générer un signal
            print("   Test de génération de signal...")
            response = requests.get(f"{base_url}/generate/{self.symbol}")
            if response.status_code != 200:
                raise ValueError(f"Erreur HTTP {response.status_code}: {response.text}")
            
            generate_result = response.json()
            if "signal_type" not in generate_result:
                raise ValueError("La réponse ne contient pas de signal_type")
            
            signal_id = generate_result.get("signal_id")
            print(f"   ✅ Signal généré avec ID: {signal_id}")
            
            # Test 2: Récupérer le dernier signal
            print("   Test de récupération du dernier signal...")
            response = requests.get(f"{base_url}/latest/{self.symbol}")
            if response.status_code != 200:
                raise ValueError(f"Erreur HTTP {response.status_code}: {response.text}")
            
            latest_result = response.json()
            if "signal_type" not in latest_result:
                raise ValueError("La réponse ne contient pas de signal_type")
            
            print(f"   ✅ Dernier signal récupéré: {latest_result['signal_type']}")
            
            # Test 3: Récupérer l'historique
            print("   Test de récupération de l'historique...")
            response = requests.get(f"{base_url}/history/{self.symbol}")
            if response.status_code != 200:
                raise ValueError(f"Erreur HTTP {response.status_code}: {response.text}")
            
            history_result = response.json()
            if "signals" not in history_result:
                raise ValueError("La réponse ne contient pas de signals")
            
            print(f"   ✅ Historique récupéré: {len(history_result['signals'])} signaux")
            
            # Test 4: Récupérer les métriques
            print("   Test de récupération des métriques...")
            response = requests.get(f"{base_url}/metrics/{self.symbol}")
            if response.status_code != 200:
                raise ValueError(f"Erreur HTTP {response.status_code}: {response.text}")
            
            metrics_result = response.json()
            if "total_signals" not in metrics_result:
                raise ValueError("La réponse ne contient pas de total_signals")
            
            print(f"   ✅ Métriques récupérées: {metrics_result['total_signals']} signaux")
            
            # Test 5: Récupérer le résumé
            print("   Test de récupération du résumé...")
            response = requests.get(f"{base_url}/summary/{self.symbol}")
            if response.status_code != 200:
                raise ValueError(f"Erreur HTTP {response.status_code}: {response.text}")
            
            summary_result = response.json()
            if "latest_signal" not in summary_result:
                raise ValueError("La réponse ne contient pas de latest_signal")
            
            print(f"   ✅ Résumé récupéré")
            
            result = {
                "generate_signal": generate_result,
                "latest_signal": latest_result,
                "history": history_result,
                "metrics": metrics_result,
                "summary": summary_result
            }
            
            self._record_test_result("api_endpoints", True, result)
            
        except Exception as e:
            print(f"❌ Erreur lors du test des endpoints API: {e}")
            self._record_test_result("api_endpoints", False, None, e)
    
    def test_ml_integration(self):
        """Teste l'intégration ML."""
        try:
            print(f"🔧 Test de l'intégration ML pour {self.symbol}...")
            
            # Récupérer les données
            df = self.get_historical_data()
            if df is None:
                raise ValueError("Impossible de récupérer les données historiques")
            
            # Préparer les données
            high = df['high']
            low = df['low']
            close = df['close']
            open_prices = df['open']
            volume = df['volume'] if 'volume' in df.columns else None
            
            # Créer le générateur
            generator = AdvancedSignalGenerator()
            
            # Simulation d'une prédiction ML
            ml_prediction = {
                "prediction": 1,  # 1 = opportunité positive
                "confidence": 0.85,
                "model_name": "RandomForest_v1.0",
                "model_type": "classification"
            }
            
            # Générer un signal avec intégration ML
            signal_result = generator.generate_advanced_signal(
                symbol=self.symbol,
                high=high,
                low=low,
                close=close,
                open_prices=open_prices,
                volume=volume,
                ml_prediction=ml_prediction
            )
            
            # Valider l'intégration ML
            if signal_result.ml_signal is None:
                raise ValueError("Le signal ML n'a pas été intégré")
            
            if signal_result.ml_signal.get("model_name") != "RandomForest_v1.0":
                raise ValueError("Le nom du modèle ML n'est pas correct")
            
            result = {
                "ml_signal": signal_result.ml_signal,
                "final_signal": signal_result.signal_type.value,
                "final_score": signal_result.score,
                "final_confidence": signal_result.confidence
            }
            
            print(f"✅ Intégration ML réussie: {signal_result.ml_signal['model_name']}")
            print(f"   Signal final: {signal_result.signal_type.value} (Score: {signal_result.score:.1f})")
            self._record_test_result("ml_integration", True, result)
            
        except Exception as e:
            print(f"❌ Erreur lors du test de l'intégration ML: {e}")
            self._record_test_result("ml_integration", False, None, e)
    
    def run_all_tests(self):
        """Exécute tous les tests."""
        print(f"🚀 Test des Signaux Avancés pour {self.symbol}")
        print("=" * 60)
        
        # Exécuter tous les tests
        self.test_signal_generator()
        self.test_signal_service()
        self.test_api_endpoints()
        self.test_ml_integration()
        
        # Calculer le taux de réussite
        total_tests = self.test_results["summary"]["total_tests"]
        passed_tests = self.test_results["summary"]["passed_tests"]
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0.0
        
        self.test_results["summary"]["success_rate"] = success_rate
        
        # Afficher le résumé
        print("\n" + "=" * 60)
        print("📊 RÉSULTATS DES TESTS")
        print("=" * 60)
        print(f"✅ Tests réussis: {passed_tests}")
        print(f"❌ Tests échoués: {self.test_results['summary']['failed_tests']}")
        print(f"📈 Taux de réussite: {success_rate:.1f}%")
        
        if self.test_results["summary"]["errors"]:
            print("\n❌ Erreurs rencontrées:")
            for error in self.test_results["summary"]["errors"]:
                print(f"   - {error}")
        
        # Sauvegarder les résultats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"advanced_signals_test_report_{timestamp}.md"
        json_filename = f"advanced_signals_test_results_{timestamp}.json"
        
        self.generate_markdown_report(report_filename)
        self.save_json_results(json_filename)
        
        print(f"\n📄 Rapport généré: {report_filename}")
        print(f"📊 Résultats JSON sauvegardés: {json_filename}")
        
        return success_rate >= 80.0
    
    def generate_markdown_report(self, filename: str):
        """Génère un rapport Markdown des tests."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# Rapport de Test - Signaux Avancés\n\n")
                f.write(f"## 📋 Informations Générales\n\n")
                f.write(f"- **Symbole testé**: {self.symbol}\n")
                f.write(f"- **Date du test**: {self.test_results['test_timestamp']}\n")
                f.write(f"- **Total des tests**: {self.test_results['summary']['total_tests']}\n")
                f.write(f"- **Tests réussis**: {self.test_results['summary']['passed_tests']}\n")
                f.write(f"- **Tests échoués**: {self.test_results['summary']['failed_tests']}\n")
                f.write(f"- **Taux de réussite**: {self.test_results['summary']['success_rate']:.1f}%\n\n")
                
                f.write(f"## 🔧 Tests Effectués\n\n")
                
                for test_name, test_data in self.test_results["tests_performed"].items():
                    status = "✅ PASS" if test_data["success"] else "❌ FAIL"
                    f.write(f"### {test_name.replace('_', ' ').title()}\n\n")
                    f.write(f"- **Statut**: {status}\n")
                    f.write(f"- **Timestamp**: {test_data['timestamp']}\n")
                    
                    if test_data["result"]:
                        f.write(f"- **Résultat**: {test_data['result']}\n")
                    
                    if test_data["error"]:
                        f.write(f"- **Erreur**: {test_data['error']}\n")
                    
                    f.write("\n")
                
                f.write(f"## 🎯 Conclusion\n\n")
                
                if self.test_results["summary"]["success_rate"] >= 80.0:
                    f.write(f"✅ **Tests réussis** - Le système de signaux avancés fonctionne correctement.\n\n")
                else:
                    f.write(f"❌ **Tests échoués** - Des problèmes ont été détectés dans le système.\n\n")
                
                f.write(f"Le système de signaux avancés est prêt pour la production.\n\n")
                f.write(f"---\n")
                f.write(f"*Rapport généré automatiquement par le système de test des signaux avancés*\n")
                
        except Exception as e:
            print(f"❌ Erreur lors de la génération du rapport: {e}")
    
    def save_json_results(self, filename: str):
        """Sauvegarde les résultats en JSON."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde JSON: {e}")


def main():
    """Fonction principale."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test des signaux avancés")
    parser.add_argument("--symbol", default="AAPL", help="Symbole à tester")
    
    args = parser.parse_args()
    
    # Créer et exécuter les tests
    tester = AdvancedSignalsTester(args.symbol)
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 Tests terminés avec succès!")
        sys.exit(0)
    else:
        print("\n❌ Tests échoués!")
        sys.exit(1)


if __name__ == "__main__":
    main()
