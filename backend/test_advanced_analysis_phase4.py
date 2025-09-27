#!/usr/bin/env python3
"""
Test de l'Analyse Avancée - Phase 4
Test du service d'analyse combinée et du scoring hybride
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Ajouter le chemin du backend
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.services.advanced_analysis import AdvancedTradingAnalysis, HybridScoringSystem, CompositeScoringEngine
from app.services.advanced_analysis.composite_scoring import AnalysisType

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_advanced_analysis():
    """Test du service d'analyse avancée"""
    try:
        logger.info("🧪 Test du service d'analyse avancée")
        
        # Initialiser le service
        analyzer = AdvancedTradingAnalysis()
        
        # Test avec AAPL
        symbol = "AAPL"
        logger.info(f"Analyse de {symbol}...")
        
        # Effectuer l'analyse complète
        result = await analyzer.analyze_opportunity(
            symbol=symbol,
            time_horizon=30,
            include_ml=True
        )
        
        # Afficher les résultats
        logger.info(f"✅ Analyse terminée pour {symbol}")
        logger.info(f"   Score composite: {result.composite_score:.3f}")
        logger.info(f"   Niveau de confiance: {result.confidence_level:.3f}")
        logger.info(f"   Recommandation: {result.recommendation}")
        logger.info(f"   Niveau de risque: {result.risk_level}")
        
        # Afficher le breakdown des scores
        logger.info("   Breakdown des scores:")
        logger.info(f"     - Technique: {result.technical_score:.3f}")
        logger.info(f"     - Sentiment: {result.sentiment_score:.3f}")
        logger.info(f"     - Marché: {result.market_score:.3f}")
        
        # Obtenir le résumé
        summary = analyzer.get_analysis_summary(result)
        logger.info(f"   Résumé: {summary}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test d'analyse avancée: {e}")
        return False

async def test_hybrid_scoring():
    """Test du système de scoring hybride"""
    try:
        logger.info("🧪 Test du système de scoring hybride")
        
        # Initialiser le système
        scorer = HybridScoringSystem()
        
        # Données de test
        ml_analysis = {
            'ml_score': 0.75,
            'ml_confidence': 0.8,
            'ml_recommendation': 'BUY'
        }
        
        conventional_analysis = {
            'symbol': 'AAPL',
            'composite_score': 0.65,
            'confidence_level': 0.7,
            'recommendation': 'BUY'
        }
        
        # Calculer le score hybride
        hybrid_score = scorer.calculate_hybrid_score(ml_analysis, conventional_analysis)
        
        # Afficher les résultats
        logger.info(f"✅ Score hybride calculé")
        logger.info(f"   Score hybride: {hybrid_score.hybrid_score:.3f}")
        logger.info(f"   Confiance: {hybrid_score.confidence:.3f}")
        logger.info(f"   Facteur de convergence: {hybrid_score.convergence_factor:.3f}")
        logger.info(f"   Recommandation: {hybrid_score.recommendation}")
        
        # Afficher le breakdown
        logger.info("   Breakdown des scores:")
        logger.info(f"     - ML: {hybrid_score.ml_score:.3f}")
        logger.info(f"     - Conventionnel: {hybrid_score.conventional_score:.3f}")
        
        # Afficher les poids
        weights = scorer.get_scoring_weights()
        logger.info(f"   Poids: {weights}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de scoring hybride: {e}")
        return False

async def test_composite_scoring():
    """Test du moteur de scoring composite"""
    try:
        logger.info("🧪 Test du moteur de scoring composite")
        
        # Initialiser le moteur
        engine = CompositeScoringEngine()
        
        # Données de test
        analyses = {
            AnalysisType.TECHNICAL: {
                'symbol': 'AAPL',
                'signals': {'buy_signals': [1, 2, 3], 'sell_signals': [1]},
                'candlestick_patterns': {'hammer': {'sentiment': 'bullish'}},
                'support_resistance': {'support': [100, 105]},
                'data_points': 100
            },
            AnalysisType.SENTIMENT: {
                'symbol': 'AAPL',
                'garch_analysis': {'model_comparison': {}},
                'monte_carlo_analysis': {'risk_metrics': {}},
                'markov_analysis': {'current_state': 1},
                'volatility_forecast': {},
                'data_points': 200
            },
            AnalysisType.MARKET: {
                'symbol': 'AAPL',
                'volatility_indicators': {'historical_volatility': 0.2},
                'momentum_indicators': {'price_momentum': 0.1},
                'data_points': 100
            },
            AnalysisType.ML: {
                'symbol': 'AAPL',
                'ml_score': 0.7,
                'ml_confidence': 0.8
            }
        }
        
        # Calculer le score composite
        composite_score = engine.calculate_composite_score(analyses)
        
        # Afficher les résultats
        logger.info(f"✅ Score composite calculé")
        logger.info(f"   Score global: {composite_score.overall_score:.3f}")
        logger.info(f"   Niveau de confiance: {composite_score.confidence_level:.3f}")
        logger.info(f"   Niveau de risque: {composite_score.risk_level.value}")
        logger.info(f"   Recommandation: {composite_score.recommendation}")
        
        # Afficher le breakdown
        logger.info("   Breakdown des scores:")
        for analysis_type, score in composite_score.score_breakdown.items():
            logger.info(f"     - {analysis_type}: {score:.3f}")
        
        # Afficher la qualité des analyses
        logger.info("   Qualité des analyses:")
        for analysis_type, quality in composite_score.analysis_quality.items():
            logger.info(f"     - {analysis_type}: {quality:.3f}")
        
        # Afficher les métriques de convergence
        logger.info("   Métriques de convergence:")
        for metric, value in composite_score.convergence_metrics.items():
            logger.info(f"     - {metric}: {value:.3f}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de scoring composite: {e}")
        return False

async def test_scoring_configuration():
    """Test de la configuration du scoring"""
    try:
        logger.info("🧪 Test de la configuration du scoring")
        
        # Test du scoring hybride
        hybrid_scorer = HybridScoringSystem()
        
        # Mettre à jour les poids
        success = hybrid_scorer.update_scoring_weights(0.3, 0.7)
        logger.info(f"✅ Mise à jour des poids hybride: {success}")
        
        # Vérifier les nouveaux poids
        weights = hybrid_scorer.get_scoring_weights()
        logger.info(f"   Nouveaux poids: {weights}")
        
        # Test du scoring composite
        composite_engine = CompositeScoringEngine()
        
        # Obtenir la configuration
        config = composite_engine.get_scoring_configuration()
        logger.info(f"✅ Configuration composite récupérée")
        logger.info(f"   Poids par défaut: {config['default_weights']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test de configuration: {e}")
        return False

async def main():
    """Fonction principale de test"""
    logger.info("🚀 Démarrage des tests de l'analyse avancée - Phase 4")
    
    tests = [
        ("Service d'Analyse Avancée", test_advanced_analysis),
        ("Système de Scoring Hybride", test_hybrid_scoring),
        ("Moteur de Scoring Composite", test_composite_scoring),
        ("Configuration du Scoring", test_scoring_configuration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✅ {test_name}: SUCCÈS")
            else:
                logger.error(f"❌ {test_name}: ÉCHEC")
                
        except Exception as e:
            logger.error(f"❌ {test_name}: ERREUR - {e}")
            results.append((test_name, False))
    
    # Résumé des résultats
    logger.info(f"\n{'='*50}")
    logger.info("RÉSUMÉ DES TESTS")
    logger.info(f"{'='*50}")
    
    success_count = 0
    for test_name, result in results:
        status = "✅ SUCCÈS" if result else "❌ ÉCHEC"
        logger.info(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    logger.info(f"\nRésultat global: {success_count}/{len(results)} tests réussis")
    
    if success_count == len(results):
        logger.info("🎉 Tous les tests sont passés avec succès!")
        return True
    else:
        logger.error("⚠️ Certains tests ont échoué")
        return False

if __name__ == "__main__":
    # Exécuter les tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
