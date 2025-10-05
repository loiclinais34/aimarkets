#!/usr/bin/env python3
"""
Script de test pour la Phase 1: Amélioration des seuils de décision
Teste les nouvelles pondérations, seuils et règles de validation
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.advanced_analysis.advanced_trading_analysis import AdvancedTradingAnalysis
import logging
from typing import Dict, List
import json
from datetime import datetime, date

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase1Tester:
    """Testeur pour la Phase 1 d'amélioration des seuils de décision"""
    
    def __init__(self, db: Session):
        self.db = db
        self.analysis_service = AdvancedTradingAnalysis()
        self.results = {}
    
    def test_composite_score_formula(self) -> Dict:
        """Teste la nouvelle formule de composite_score"""
        logger.info("🧮 Test de la nouvelle formule de composite_score")
        
        # Cas de test avec différents scores
        test_cases = [
            {
                "name": "Scores élevés",
                "technical": 0.8,
                "sentiment": 0.7,
                "market": 0.6,
                "expected_range": (0.65, 0.75)
            },
            {
                "name": "Scores moyens",
                "technical": 0.6,
                "sentiment": 0.5,
                "market": 0.4,
                "expected_range": (0.45, 0.55)
            },
            {
                "name": "Scores faibles",
                "technical": 0.3,
                "sentiment": 0.2,
                "market": 0.1,
                "expected_range": (0.15, 0.25)
            },
            {
                "name": "Scores mixtes",
                "technical": 0.9,
                "sentiment": 0.3,
                "market": 0.7,
                "expected_range": (0.60, 0.70)
            }
        ]
        
        results = []
        for case in test_cases:
            # Calculer le score composite avec la nouvelle formule
            composite_score = self.analysis_service._calculate_composite_score(
                case["technical"], case["sentiment"], case["market"], 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0  # Scores avancés désactivés
            )
            
            # Vérifier si le score est dans la plage attendue
            in_range = case["expected_range"][0] <= composite_score <= case["expected_range"][1]
            
            results.append({
                "case": case["name"],
                "technical": case["technical"],
                "sentiment": case["sentiment"],
                "market": case["market"],
                "composite_score": composite_score,
                "expected_range": case["expected_range"],
                "in_range": in_range
            })
        
        return {
            "test_cases": results,
            "formula_working": all(r["in_range"] for r in results)
        }
    
    def test_decision_thresholds(self) -> Dict:
        """Teste les nouveaux seuils de décision"""
        logger.info("🎯 Test des nouveaux seuils de décision")
        
        # Cas de test pour chaque catégorie
        test_cases = [
            {
                "name": "BUY_STRONG",
                "composite": 0.70,
                "technical": 0.65,
                "sentiment": 0.55,
                "market": 0.45,
                "confidence": 0.85,
                "expected_recommendation": "BUY_STRONG"
            },
            {
                "name": "BUY_MODERATE",
                "composite": 0.60,
                "technical": 0.55,
                "sentiment": 0.45,
                "market": 0.35,
                "confidence": 0.70,
                "expected_recommendation": "BUY_MODERATE"
            },
            {
                "name": "BUY_WEAK",
                "composite": 0.50,
                "technical": 0.45,
                "sentiment": 0.35,
                "market": 0.25,
                "confidence": 0.50,
                "expected_recommendation": "BUY_WEAK"
            },
            {
                "name": "HOLD",
                "composite": 0.40,
                "technical": 0.35,
                "sentiment": 0.25,
                "market": 0.15,
                "confidence": 0.30,
                "expected_recommendation": "HOLD"
            },
            {
                "name": "SELL_MODERATE",
                "composite": 0.30,
                "technical": 0.25,
                "sentiment": 0.15,
                "market": 0.05,
                "confidence": 0.20,
                "expected_recommendation": "SELL_MODERATE"
            },
            {
                "name": "SELL_STRONG",
                "composite": 0.20,
                "technical": 0.15,
                "sentiment": 0.05,
                "market": 0.0,
                "confidence": 0.10,
                "expected_recommendation": "SELL_STRONG"
            }
        ]
        
        results = []
        for case in test_cases:
            # Tester la détermination de recommandation
            recommendation, risk_level = self.analysis_service._determine_recommendation(
                case["composite"], case["technical"], case["sentiment"], 
                case["market"], case["confidence"]
            )
            
            # Vérifier si la recommandation est correcte
            correct = recommendation == case["expected_recommendation"]
            
            results.append({
                "case": case["name"],
                "composite": case["composite"],
                "technical": case["technical"],
                "sentiment": case["sentiment"],
                "market": case["market"],
                "confidence": case["confidence"],
                "recommendation": recommendation,
                "risk_level": risk_level,
                "expected": case["expected_recommendation"],
                "correct": correct
            })
        
        return {
            "test_cases": results,
            "thresholds_working": all(r["correct"] for r in results)
        }
    
    def test_validation_rules(self) -> Dict:
        """Teste les règles de validation"""
        logger.info("✅ Test des règles de validation")
        
        # Cas de test pour les règles de validation
        test_cases = [
            {
                "name": "BUY_STRONG - Validation réussie",
                "composite": 0.70,
                "technical": 0.65,
                "sentiment": 0.55,
                "market": 0.45,
                "confidence": 0.85,
                "expected_validation": True
            },
            {
                "name": "BUY_STRONG - Échec technique",
                "composite": 0.70,
                "technical": 0.55,  # Trop faible
                "sentiment": 0.55,
                "market": 0.45,
                "confidence": 0.85,
                "expected_validation": False
            },
            {
                "name": "BUY_STRONG - Échec confiance",
                "composite": 0.70,
                "technical": 0.65,
                "sentiment": 0.55,
                "market": 0.45,
                "confidence": 0.75,  # Trop faible
                "expected_validation": False
            },
            {
                "name": "BUY_MODERATE - Validation réussie",
                "composite": 0.60,
                "technical": 0.55,
                "sentiment": 0.45,
                "market": 0.35,
                "confidence": 0.70,
                "expected_validation": True
            },
            {
                "name": "BUY_WEAK - Validation réussie",
                "composite": 0.50,
                "technical": 0.45,
                "sentiment": 0.35,
                "market": 0.25,
                "confidence": 0.50,
                "expected_validation": True
            }
        ]
        
        results = []
        for case in test_cases:
            # Tester la validation
            validation = self.analysis_service._validate_buy_signals(
                case["composite"], case["technical"], case["sentiment"],
                case["market"], case["confidence"]
            )
            
            # Déterminer quelle catégorie devrait être validée
            if case["composite"] >= 0.65:
                expected_category = "BUY_STRONG"
            elif case["composite"] >= 0.55:
                expected_category = "BUY_MODERATE"
            elif case["composite"] >= 0.45:
                expected_category = "BUY_WEAK"
            else:
                expected_category = "NONE"
            
            # Vérifier la validation
            validation_passed = validation.get(expected_category, False) if expected_category != "NONE" else True
            correct = validation_passed == case["expected_validation"]
            
            results.append({
                "case": case["name"],
                "composite": case["composite"],
                "technical": case["technical"],
                "sentiment": case["sentiment"],
                "market": case["market"],
                "confidence": case["confidence"],
                "validation": validation,
                "expected_category": expected_category,
                "validation_passed": validation_passed,
                "expected_validation": case["expected_validation"],
                "correct": correct
            })
        
        return {
            "test_cases": results,
            "validation_working": all(r["correct"] for r in results)
        }
    
    async def test_real_symbol_analysis(self) -> Dict:
        """Teste l'analyse sur un symbole réel"""
        logger.info("📊 Test d'analyse sur symbole réel")
        
        # Test sur quelques symboles
        test_symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        results = []
        
        for symbol in test_symbols:
            try:
                # Analyser le symbole
                analysis_result = await self.analysis_service.analyze_opportunity(symbol, db=self.db)
                
                results.append({
                    "symbol": symbol,
                    "technical_score": analysis_result.technical_score,
                    "sentiment_score": analysis_result.sentiment_score,
                    "market_score": analysis_result.market_score,
                    "composite_score": analysis_result.composite_score,
                    "confidence_level": analysis_result.confidence_level,
                    "recommendation": analysis_result.recommendation,
                    "risk_level": analysis_result.risk_level,
                    "analysis_successful": True
                })
                
            except Exception as e:
                results.append({
                    "symbol": symbol,
                    "error": str(e),
                    "analysis_successful": False
                })
        
        return {
            "symbol_analyses": results,
            "successful_analyses": sum(1 for r in results if r.get("analysis_successful", False))
        }
    
    async def run_complete_test(self) -> Dict:
        """Exécute tous les tests de la Phase 1"""
        logger.info("🚀 Démarrage des tests complets de la Phase 1")
        
        try:
            self.results = {
                "composite_score_test": self.test_composite_score_formula(),
                "decision_thresholds_test": self.test_decision_thresholds(),
                "validation_rules_test": self.test_validation_rules(),
                "real_symbol_test": await self.test_real_symbol_analysis(),
                "test_timestamp": datetime.now().isoformat()
            }
            
            return self.results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors des tests: {e}")
            raise
    
    def print_summary(self):
        """Affiche un résumé des tests"""
        if not self.results:
            logger.warning("Aucun résultat de test à afficher")
            return
        
        composite_test = self.results["composite_score_test"]
        thresholds_test = self.results["decision_thresholds_test"]
        validation_test = self.results["validation_rules_test"]
        real_test = self.results["real_symbol_test"]
        
        print("\n" + "="*80)
        print("🧪 RÉSULTATS DES TESTS - PHASE 1: AMÉLIORATION DES SEUILS DE DÉCISION")
        print("="*80)
        
        print(f"\n🧮 TEST DE LA FORMULE COMPOSITE_SCORE:")
        print(f"  • Formule fonctionnelle: {'✅' if composite_test['formula_working'] else '❌'}")
        for case in composite_test["test_cases"]:
            status = "✅" if case["in_range"] else "❌"
            print(f"    {status} {case['case']}: {case['composite_score']:.3f} (attendu: {case['expected_range']})")
        
        print(f"\n🎯 TEST DES SEUILS DE DÉCISION:")
        print(f"  • Seuils fonctionnels: {'✅' if thresholds_test['thresholds_working'] else '❌'}")
        for case in thresholds_test["test_cases"]:
            status = "✅" if case["correct"] else "❌"
            print(f"    {status} {case['case']}: {case['recommendation']} (attendu: {case['expected']})")
        
        print(f"\n✅ TEST DES RÈGLES DE VALIDATION:")
        print(f"  • Validation fonctionnelle: {'✅' if validation_test['validation_working'] else '❌'}")
        for case in validation_test["test_cases"]:
            status = "✅" if case["correct"] else "❌"
            print(f"    {status} {case['case']}: Validation {'réussie' if case['validation_passed'] else 'échouée'}")
        
        print(f"\n📊 TEST D'ANALYSE RÉELLE:")
        print(f"  • Analyses réussies: {real_test['successful_analyses']}/{len(real_test['symbol_analyses'])}")
        for case in real_test["symbol_analyses"]:
            if case.get("analysis_successful", False):
                print(f"    ✅ {case['symbol']}: {case['recommendation']} (score: {case['composite_score']:.3f})")
            else:
                print(f"    ❌ {case['symbol']}: {case.get('error', 'Erreur inconnue')}")
        
        # Résumé global
        all_tests_passed = (
            composite_test['formula_working'] and
            thresholds_test['thresholds_working'] and
            validation_test['validation_working'] and
            real_test['successful_analyses'] > 0
        )
        
        print(f"\n🎉 RÉSULTAT GLOBAL:")
        print(f"  • Phase 1 implémentée avec succès: {'✅' if all_tests_passed else '❌'}")
        
        print("\n" + "="*80)


async def main():
    """Fonction principale"""
    
    logger.info("🚀 Démarrage des tests de la Phase 1")
    
    db = next(get_db())
    
    try:
        # Créer le testeur
        tester = Phase1Tester(db)
        
        # Exécuter les tests
        results = await tester.run_complete_test()
        
        # Afficher le résumé
        tester.print_summary()
        
        # Sauvegarder les résultats
        output_file = os.path.join(os.path.dirname(__file__), "phase1_test_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📁 Résultats de test sauvegardés dans {output_file}")
        logger.info("✅ Tests de la Phase 1 terminés avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution des tests: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())
