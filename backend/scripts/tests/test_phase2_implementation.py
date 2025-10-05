#!/usr/bin/env python3
"""
Script de test pour la Phase 2: Amélioration du scoring
Teste les nouvelles validations, niveaux de confiance et améliorations du scoring
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


class Phase2Tester:
    """Testeur pour la Phase 2 d'amélioration du scoring"""
    
    def __init__(self, db: Session):
        self.db = db
        self.analysis_service = AdvancedTradingAnalysis()
        self.results = {}
    
    def test_composite_score_formula_fix(self) -> Dict:
        """Teste la correction de la formule de composite_score"""
        logger.info("🧮 Test de la correction de la formule de composite_score")
        
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
            # Calculer le score composite avec la formule corrigée
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
            "formula_fixed": all(r["in_range"] for r in results)
        }
    
    def test_technical_validation(self) -> Dict:
        """Teste les règles de validation technique"""
        logger.info("🔧 Test des règles de validation technique")
        
        # Cas de test pour la validation technique
        test_cases = [
            {
                "name": "Validation réussie",
                "indicators": {
                    "rsi_14": 45.0,
                    "macd": 0.5,
                    "macd_signal": 0.3,
                    "sma_20": 100.0,
                    "close": 105.0,
                    "volume": 1000000,
                    "volume_sma_20": 800000
                },
                "expected_valid": True
            },
            {
                "name": "RSI extrême",
                "indicators": {
                    "rsi_14": 85.0,  # RSI trop élevé
                    "macd": 0.5,
                    "macd_signal": 0.3,
                    "sma_20": 100.0,
                    "close": 105.0,
                    "volume": 1000000,
                    "volume_sma_20": 800000
                },
                "expected_valid": False
            },
            {
                "name": "MACD négatif",
                "indicators": {
                    "rsi_14": 45.0,
                    "macd": 0.2,
                    "macd_signal": 0.3,  # MACD en dessous du signal
                    "sma_20": 100.0,
                    "close": 105.0,
                    "volume": 1000000,
                    "volume_sma_20": 800000
                },
                "expected_valid": False
            },
            {
                "name": "Prix en dessous de SMA",
                "indicators": {
                    "rsi_14": 45.0,
                    "macd": 0.5,
                    "macd_signal": 0.3,
                    "sma_20": 100.0,
                    "close": 95.0,  # Prix en dessous de SMA
                    "volume": 1000000,
                    "volume_sma_20": 800000
                },
                "expected_valid": False
            },
            {
                "name": "Volume faible",
                "indicators": {
                    "rsi_14": 45.0,
                    "macd": 0.5,
                    "macd_signal": 0.3,
                    "sma_20": 100.0,
                    "close": 105.0,
                    "volume": 500000,
                    "volume_sma_20": 800000  # Volume en dessous de la moyenne
                },
                "expected_valid": False
            }
        ]
        
        results = []
        for case in test_cases:
            # Tester la validation technique
            validation = self.analysis_service._validate_technical_indicators(case["indicators"])
            
            # Vérifier si la validation est correcte
            correct = validation["overall_valid"] == case["expected_valid"]
            
            results.append({
                "case": case["name"],
                "indicators": case["indicators"],
                "validation": validation,
                "expected_valid": case["expected_valid"],
                "correct": correct
            })
        
        return {
            "test_cases": results,
            "validation_working": all(r["correct"] for r in results)
        }
    
    def test_sentiment_validation(self) -> Dict:
        """Teste les règles de validation sentiment"""
        logger.info("💭 Test des règles de validation sentiment")
        
        # Cas de test pour la validation sentiment
        test_cases = [
            {
                "name": "Validation réussie",
                "indicators": {
                    "sentiment_score_normalized": 0.7,
                    "confidence": 0.8
                },
                "expected_valid": True
            },
            {
                "name": "Score sentiment faible",
                "indicators": {
                    "sentiment_score_normalized": 0.3,  # Score trop faible
                    "confidence": 0.8
                },
                "expected_valid": False
            },
            {
                "name": "Confiance faible",
                "indicators": {
                    "sentiment_score_normalized": 0.7,
                    "confidence": 0.4  # Confiance trop faible
                },
                "expected_valid": False
            },
            {
                "name": "Score et confiance faibles",
                "indicators": {
                    "sentiment_score_normalized": 0.3,
                    "confidence": 0.4
                },
                "expected_valid": False
            }
        ]
        
        results = []
        for case in test_cases:
            # Tester la validation sentiment
            validation = self.analysis_service._validate_sentiment_indicators(case["indicators"])
            
            # Vérifier si la validation est correcte
            correct = validation["overall_valid"] == case["expected_valid"]
            
            results.append({
                "case": case["name"],
                "indicators": case["indicators"],
                "validation": validation,
                "expected_valid": case["expected_valid"],
                "correct": correct
            })
        
        return {
            "test_cases": results,
            "validation_working": all(r["correct"] for r in results)
        }
    
    def test_market_validation(self) -> Dict:
        """Teste les règles de validation marché"""
        logger.info("📈 Test des règles de validation marché")
        
        # Cas de test pour la validation marché
        test_cases = [
            {
                "name": "Validation réussie",
                "indicators": {
                    "market_regime": "bullish",
                    "volatility_percentile": 50.0,
                    "correlation_strength": "strong"
                },
                "expected_valid": True
            },
            {
                "name": "Régime bearish",
                "indicators": {
                    "market_regime": "bearish",  # Régime défavorable
                    "volatility_percentile": 50.0,
                    "correlation_strength": "strong"
                },
                "expected_valid": False
            },
            {
                "name": "Volatilité extrême",
                "indicators": {
                    "market_regime": "bullish",
                    "volatility_percentile": 90.0,  # Volatilité trop élevée
                    "correlation_strength": "strong"
                },
                "expected_valid": False
            },
            {
                "name": "Corrélation faible",
                "indicators": {
                    "market_regime": "bullish",
                    "volatility_percentile": 50.0,
                    "correlation_strength": "weak"  # Corrélation faible
                },
                "expected_valid": False
            }
        ]
        
        results = []
        for case in test_cases:
            # Tester la validation marché
            validation = self.analysis_service._validate_market_indicators(case["indicators"])
            
            # Vérifier si la validation est correcte
            correct = validation["overall_valid"] == case["expected_valid"]
            
            results.append({
                "case": case["name"],
                "indicators": case["indicators"],
                "validation": validation,
                "expected_valid": case["expected_valid"],
                "correct": correct
            })
        
        return {
            "test_cases": results,
            "validation_working": all(r["correct"] for r in results)
        }
    
    def test_confidence_level_integration(self) -> Dict:
        """Teste l'intégration des niveaux de confiance"""
        logger.info("🎯 Test de l'intégration des niveaux de confiance")
        
        # Cas de test pour les niveaux de confiance
        test_cases = [
            {
                "name": "Confiance élevée",
                "technical_score": 0.8,
                "sentiment_score": 0.7,
                "market_score": 0.6,
                "technical_indicators": {
                    "rsi_14": 45.0,
                    "macd": 0.5,
                    "macd_signal": 0.3,
                    "sma_20": 100.0,
                    "close": 105.0,
                    "volume": 1000000,
                    "volume_sma_20": 800000
                },
                "sentiment_indicators": {
                    "sentiment_score_normalized": 0.7,
                    "confidence": 0.8
                },
                "market_indicators": {
                    "market_regime": "bullish",
                    "volatility_percentile": 50.0,
                    "correlation_strength": "strong"
                },
                "expected_confidence_range": (0.7, 1.0)
            },
            {
                "name": "Confiance moyenne",
                "technical_score": 0.6,
                "sentiment_score": 0.5,
                "market_score": 0.4,
                "technical_indicators": {
                    "rsi_14": 45.0,
                    "macd": 0.5,
                    "macd_signal": 0.3,
                    "sma_20": 100.0,
                    "close": 105.0,
                    "volume": 1000000,
                    "volume_sma_20": 800000
                },
                "sentiment_indicators": {
                    "sentiment_score_normalized": 0.5,
                    "confidence": 0.6
                },
                "market_indicators": {
                    "market_regime": "sideways",
                    "volatility_percentile": 60.0,
                    "correlation_strength": "medium"
                },
                "expected_confidence_range": (0.4, 0.7)
            },
            {
                "name": "Confiance faible",
                "technical_score": 0.3,
                "sentiment_score": 0.2,
                "market_score": 0.1,
                "technical_indicators": {
                    "rsi_14": 85.0,  # RSI extrême
                    "macd": 0.2,
                    "macd_signal": 0.3,
                    "sma_20": 100.0,
                    "close": 95.0,
                    "volume": 500000,
                    "volume_sma_20": 800000
                },
                "sentiment_indicators": {
                    "sentiment_score_normalized": 0.3,
                    "confidence": 0.4
                },
                "market_indicators": {
                    "market_regime": "bearish",
                    "volatility_percentile": 90.0,
                    "correlation_strength": "weak"
                },
                "expected_confidence_range": (0.1, 0.4)
            }
        ]
        
        results = []
        for case in test_cases:
            # Tester le calcul de confiance
            confidence = self.analysis_service._calculate_confidence_level(
                case["technical_score"], case["sentiment_score"], case["market_score"], 0.0,
                0.0, 0.0, 0.0, 0.0, 0.0,
                technical_indicators=case["technical_indicators"],
                sentiment_indicators=case["sentiment_indicators"],
                market_indicators=case["market_indicators"]
            )
            
            # Vérifier si la confiance est dans la plage attendue
            in_range = case["expected_confidence_range"][0] <= confidence <= case["expected_confidence_range"][1]
            
            results.append({
                "case": case["name"],
                "technical_score": case["technical_score"],
                "sentiment_score": case["sentiment_score"],
                "market_score": case["market_score"],
                "confidence": confidence,
                "expected_range": case["expected_confidence_range"],
                "in_range": in_range
            })
        
        return {
            "test_cases": results,
            "confidence_integration_working": all(r["in_range"] for r in results)
        }
    
    async def test_real_symbol_analysis(self) -> Dict:
        """Teste l'analyse sur un symbole réel avec les améliorations Phase 2"""
        logger.info("📊 Test d'analyse sur symbole réel (Phase 2)")
        
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
        """Exécute tous les tests de la Phase 2"""
        logger.info("🚀 Démarrage des tests complets de la Phase 2")
        
        try:
            self.results = {
                "composite_score_fix_test": self.test_composite_score_formula_fix(),
                "technical_validation_test": self.test_technical_validation(),
                "sentiment_validation_test": self.test_sentiment_validation(),
                "market_validation_test": self.test_market_validation(),
                "confidence_integration_test": self.test_confidence_level_integration(),
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
        
        composite_test = self.results["composite_score_fix_test"]
        tech_validation_test = self.results["technical_validation_test"]
        sent_validation_test = self.results["sentiment_validation_test"]
        market_validation_test = self.results["market_validation_test"]
        confidence_test = self.results["confidence_integration_test"]
        real_test = self.results["real_symbol_test"]
        
        print("\n" + "="*80)
        print("🧪 RÉSULTATS DES TESTS - PHASE 2: AMÉLIORATION DU SCORING")
        print("="*80)
        
        print(f"\n🧮 TEST DE LA CORRECTION DE LA FORMULE COMPOSITE_SCORE:")
        print(f"  • Formule corrigée: {'✅' if composite_test['formula_fixed'] else '❌'}")
        for case in composite_test["test_cases"]:
            status = "✅" if case["in_range"] else "❌"
            print(f"    {status} {case['case']}: {case['composite_score']:.3f} (attendu: {case['expected_range']})")
        
        print(f"\n🔧 TEST DE LA VALIDATION TECHNIQUE:")
        print(f"  • Validation fonctionnelle: {'✅' if tech_validation_test['validation_working'] else '❌'}")
        for case in tech_validation_test["test_cases"]:
            status = "✅" if case["correct"] else "❌"
            print(f"    {status} {case['case']}: Validation {'réussie' if case['validation']['overall_valid'] else 'échouée'}")
        
        print(f"\n💭 TEST DE LA VALIDATION SENTIMENT:")
        print(f"  • Validation fonctionnelle: {'✅' if sent_validation_test['validation_working'] else '❌'}")
        for case in sent_validation_test["test_cases"]:
            status = "✅" if case["correct"] else "❌"
            print(f"    {status} {case['case']}: Validation {'réussie' if case['validation']['overall_valid'] else 'échouée'}")
        
        print(f"\n📈 TEST DE LA VALIDATION MARCHÉ:")
        print(f"  • Validation fonctionnelle: {'✅' if market_validation_test['validation_working'] else '❌'}")
        for case in market_validation_test["test_cases"]:
            status = "✅" if case["correct"] else "❌"
            print(f"    {status} {case['case']}: Validation {'réussie' if case['validation']['overall_valid'] else 'échouée'}")
        
        print(f"\n🎯 TEST DE L'INTÉGRATION DE LA CONFIANCE:")
        print(f"  • Intégration fonctionnelle: {'✅' if confidence_test['confidence_integration_working'] else '❌'}")
        for case in confidence_test["test_cases"]:
            status = "✅" if case["in_range"] else "❌"
            print(f"    {status} {case['case']}: {case['confidence']:.3f} (attendu: {case['expected_range']})")
        
        print(f"\n📊 TEST D'ANALYSE RÉELLE:")
        print(f"  • Analyses réussies: {real_test['successful_analyses']}/{len(real_test['symbol_analyses'])}")
        for case in real_test["symbol_analyses"]:
            if case.get("analysis_successful", False):
                print(f"    ✅ {case['symbol']}: {case['recommendation']} (score: {case['composite_score']:.3f}, confiance: {case['confidence_level']:.3f})")
            else:
                print(f"    ❌ {case['symbol']}: {case.get('error', 'Erreur inconnue')}")
        
        # Résumé global
        all_tests_passed = (
            composite_test['formula_fixed'] and
            tech_validation_test['validation_working'] and
            sent_validation_test['validation_working'] and
            market_validation_test['validation_working'] and
            confidence_test['confidence_integration_working'] and
            real_test['successful_analyses'] > 0
        )
        
        print(f"\n🎉 RÉSULTAT GLOBAL:")
        print(f"  • Phase 2 implémentée avec succès: {'✅' if all_tests_passed else '❌'}")
        
        print("\n" + "="*80)


def main():
    """Fonction principale"""
    
    logger.info("🚀 Démarrage des tests de la Phase 2")
    
    db = next(get_db())
    
    try:
        # Créer le testeur
        tester = Phase2Tester(db)
        
        # Exécuter les tests
        results = asyncio.run(tester.run_complete_test())
        
        # Afficher le résumé
        tester.print_summary()
        
        # Sauvegarder les résultats
        output_file = os.path.join(os.path.dirname(__file__), "phase2_test_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📁 Résultats de test sauvegardés dans {output_file}")
        logger.info("✅ Tests de la Phase 2 terminés avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution des tests: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
