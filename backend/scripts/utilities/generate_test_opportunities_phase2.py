#!/usr/bin/env python3
"""
Script pour générer des opportunités historiques de test avec les améliorations Phase 1 et 2
Génère des opportunités pour 20 titres depuis mai 2025
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.ml_backtesting.historical_opportunity_generator import HistoricalOpportunityGenerator
from app.services.ml_backtesting.opportunity_validator import OpportunityValidator
from app.models.database import HistoricalData
from app.models.historical_opportunities import HistoricalOpportunities, HistoricalOpportunityValidation
import logging
from typing import Dict, List
import json
from datetime import datetime, date, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Phase2TestGenerator:
    """Générateur de test pour les améliorations Phase 1 et 2"""
    
    def __init__(self, db: Session):
        self.db = db
        self.generator = HistoricalOpportunityGenerator(db)
        self.validator = OpportunityValidator(db)
        self.results = {}
    
    def get_test_symbols(self) -> List[str]:
        """Retourne la liste des 20 symboles de test"""
        # Symboles représentatifs de différentes capitalisations et secteurs
        return [
            # Tech Giants
            "AAPL", "MSFT", "GOOGL", "AMZN", "META",
            # Semiconductor
            "NVDA", "AMD", "INTC", "TSM", "AVGO",
            # Finance
            "JPM", "BAC", "WFC", "GS", "MS",
            # Healthcare
            "JNJ", "PFE", "UNH", "ABBV", "MRK"
        ]
    
    def get_date_range(self) -> tuple:
        """Retourne la plage de dates pour le test (mai 2025)"""
        start_date = date(2025, 5, 1)
        end_date = date(2025, 5, 31)
        return start_date, end_date
    
    async def generate_opportunities_for_symbols(self) -> Dict:
        """Génère des opportunités pour tous les symboles de test"""
        logger.info("🚀 Démarrage de la génération d'opportunités de test")
        
        symbols = self.get_test_symbols()
        start_date, end_date = self.get_date_range()
        
        logger.info(f"📊 Configuration du test:")
        logger.info(f"  • Symboles: {len(symbols)}")
        logger.info(f"  • Période: {start_date} à {end_date}")
        logger.info(f"  • Jours ouvrés estimés: ~22")
        logger.info(f"  • Opportunités estimées: ~{len(symbols) * 22}")
        
        results = {
            "symbols_processed": [],
            "total_opportunities": 0,
            "errors": [],
            "start_time": datetime.now().isoformat()
        }
        
        for symbol in symbols:
            try:
                logger.info(f"📈 Traitement de {symbol}...")
                
                # Vérifier que des données historiques existent pour ce symbole
                has_data = self.db.query(HistoricalData).filter(
                    HistoricalData.symbol == symbol,
                    HistoricalData.date >= start_date,
                    HistoricalData.date <= end_date
                ).first() is not None
                
                if not has_data:
                    logger.warning(f"⚠️  Aucune donnée historique pour {symbol} sur la période")
                    results["errors"].append(f"{symbol}: Pas de données historiques")
                    continue
                
                # Générer les opportunités pour ce symbole
                symbol_opportunities = 0
                current_date = start_date
                
                while current_date <= end_date:
                    try:
                        # Générer une opportunité pour cette date
                        opportunity = await self.generator._generate_opportunity_for_symbol_date(
                            symbol=symbol,
                            target_date=current_date
                        )
                        
                        if opportunity:
                            # Sauvegarder l'opportunité
                            self.db.add(opportunity)
                            self.db.commit()
                            symbol_opportunities += 1
                        
                    except Exception as e:
                        logger.warning(f"⚠️  Erreur pour {symbol} le {current_date}: {e}")
                        results["errors"].append(f"{symbol} {current_date}: {str(e)}")
                        # Rollback en cas d'erreur
                        self.db.rollback()
                    
                    # Passer au jour suivant
                    current_date += timedelta(days=1)
                
                results["symbols_processed"].append({
                    "symbol": symbol,
                    "opportunities_generated": symbol_opportunities
                })
                
                results["total_opportunities"] += symbol_opportunities
                
                logger.info(f"✅ {symbol}: {symbol_opportunities} opportunités générées")
                
            except Exception as e:
                logger.error(f"❌ Erreur lors du traitement de {symbol}: {e}")
                results["errors"].append(f"{symbol}: {str(e)}")
        
        results["end_time"] = datetime.now().isoformat()
        results["duration"] = (
            datetime.fromisoformat(results["end_time"]) - 
            datetime.fromisoformat(results["start_time"])
        ).total_seconds()
        
        return results
    
    async def validate_opportunities(self) -> Dict:
        """Valide les performances des opportunités générées"""
        logger.info("🔍 Démarrage de la validation des opportunités")
        
        try:
            # Récupérer toutes les opportunités générées
            opportunities = self.db.query(HistoricalOpportunities).all()
            
            # Valider toutes les opportunités
            validation_results = await self.validator.validate_opportunities_batch(opportunities)
            
            return {
                "validation_successful": True,
                "validation_results": validation_results,
                "validation_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de la validation: {e}")
            return {
                "validation_successful": False,
                "error": str(e),
                "validation_time": datetime.now().isoformat()
            }
    
    def analyze_results(self) -> Dict:
        """Analyse les résultats de la génération et validation"""
        logger.info("📊 Analyse des résultats")
        
        try:
            # Compter les opportunités générées
            total_opportunities = self.db.query(HistoricalOpportunities).count()
            
            # Compter les validations
            total_validations = self.db.query(HistoricalOpportunityValidation).count()
            
            # Analyser les recommandations
            recommendations = self.db.query(HistoricalOpportunities.recommendation).all()
            recommendation_counts = {}
            for rec in recommendations:
                rec_type = rec[0] if rec[0] else "UNKNOWN"
                recommendation_counts[rec_type] = recommendation_counts.get(rec_type, 0) + 1
            
            # Analyser les niveaux de risque
            risk_levels = self.db.query(HistoricalOpportunities.risk_level).all()
            risk_counts = {}
            for risk in risk_levels:
                risk_type = risk[0] if risk[0] else "UNKNOWN"
                risk_counts[risk_type] = risk_counts.get(risk_type, 0) + 1
            
            # Analyser les scores composites
            composite_scores = self.db.query(HistoricalOpportunities.composite_score).all()
            scores = [float(score[0]) for score in composite_scores if score[0] is not None]
            
            score_stats = {
                "count": len(scores),
                "mean": np.mean(scores) if scores else 0,
                "std": np.std(scores) if scores else 0,
                "min": np.min(scores) if scores else 0,
                "max": np.max(scores) if scores else 0,
                "median": np.median(scores) if scores else 0
            }
            
            # Analyser les niveaux de confiance
            confidence_levels = self.db.query(HistoricalOpportunities.confidence_level).all()
            confidences = [float(conf[0]) for conf in confidence_levels if conf[0] is not None]
            
            confidence_stats = {
                "count": len(confidences),
                "mean": np.mean(confidences) if confidences else 0,
                "std": np.std(confidences) if confidences else 0,
                "min": np.min(confidences) if confidences else 0,
                "max": np.max(confidences) if confidences else 0,
                "median": np.median(confidences) if confidences else 0
            }
            
            return {
                "total_opportunities": total_opportunities,
                "total_validations": total_validations,
                "recommendation_distribution": recommendation_counts,
                "risk_level_distribution": risk_counts,
                "composite_score_stats": score_stats,
                "confidence_level_stats": confidence_stats,
                "analysis_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse: {e}")
            return {
                "error": str(e),
                "analysis_time": datetime.now().isoformat()
            }
    
    async def run_complete_test(self) -> Dict:
        """Exécute le test complet"""
        logger.info("🚀 Démarrage du test complet Phase 2")
        
        try:
            # Générer les opportunités
            generation_results = await self.generate_opportunities_for_symbols()
            
            # Valider les opportunités
            validation_results = await self.validate_opportunities()
            
            # Analyser les résultats
            analysis_results = self.analyze_results()
            
            # Consolider les résultats
            complete_results = {
                "generation": generation_results,
                "validation": validation_results,
                "analysis": analysis_results,
                "test_completed": True,
                "test_timestamp": datetime.now().isoformat()
            }
            
            return complete_results
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du test complet: {e}")
            return {
                "test_completed": False,
                "error": str(e),
                "test_timestamp": datetime.now().isoformat()
            }
    
    def print_summary(self, results: Dict):
        """Affiche un résumé des résultats"""
        if not results.get("test_completed", False):
            logger.error("❌ Test non terminé avec succès")
            return
        
        generation = results["generation"]
        validation = results["validation"]
        analysis = results["analysis"]
        
        print("\n" + "="*80)
        print("🧪 RÉSULTATS DU TEST PHASE 2 - GÉNÉRATION D'OPPORTUNITÉS")
        print("="*80)
        
        print(f"\n📊 GÉNÉRATION:")
        print(f"  • Symboles traités: {len(generation['symbols_processed'])}")
        print(f"  • Opportunités générées: {generation['total_opportunities']}")
        print(f"  • Durée: {generation['duration']:.2f} secondes")
        print(f"  • Erreurs: {len(generation['errors'])}")
        
        if generation['errors']:
            print("  • Détail des erreurs:")
            for error in generation['errors'][:5]:  # Afficher les 5 premières erreurs
                print(f"    - {error}")
        
        print(f"\n🔍 VALIDATION:")
        print(f"  • Validation réussie: {'✅' if validation['validation_successful'] else '❌'}")
        if not validation['validation_successful']:
            print(f"  • Erreur: {validation.get('error', 'Inconnue')}")
        
        print(f"\n📈 ANALYSE:")
        print(f"  • Opportunités totales: {analysis['total_opportunities']}")
        print(f"  • Validations totales: {analysis['total_validations']}")
        
        print(f"\n🎯 DISTRIBUTION DES RECOMMANDATIONS:")
        for rec_type, count in analysis['recommendation_distribution'].items():
            percentage = (count / analysis['total_opportunities']) * 100 if analysis['total_opportunities'] > 0 else 0
            print(f"  • {rec_type}: {count} ({percentage:.1f}%)")
        
        print(f"\n⚠️  DISTRIBUTION DES NIVEAUX DE RISQUE:")
        for risk_type, count in analysis['risk_level_distribution'].items():
            percentage = (count / analysis['total_opportunities']) * 100 if analysis['total_opportunities'] > 0 else 0
            print(f"  • {risk_type}: {count} ({percentage:.1f}%)")
        
        print(f"\n📊 STATISTIQUES DES SCORES COMPOSITES:")
        stats = analysis['composite_score_stats']
        print(f"  • Moyenne: {stats['mean']:.3f}")
        print(f"  • Médiane: {stats['median']:.3f}")
        print(f"  • Écart-type: {stats['std']:.3f}")
        print(f"  • Min: {stats['min']:.3f}")
        print(f"  • Max: {stats['max']:.3f}")
        
        print(f"\n🎯 STATISTIQUES DES NIVEAUX DE CONFIANCE:")
        conf_stats = analysis['confidence_level_stats']
        print(f"  • Moyenne: {conf_stats['mean']:.3f}")
        print(f"  • Médiane: {conf_stats['median']:.3f}")
        print(f"  • Écart-type: {conf_stats['std']:.3f}")
        print(f"  • Min: {conf_stats['min']:.3f}")
        print(f"  • Max: {conf_stats['max']:.3f}")
        
        print("\n" + "="*80)


def main():
    """Fonction principale"""
    
    logger.info("🚀 Démarrage du test de génération d'opportunités Phase 2")
    
    db = next(get_db())
    
    try:
        # Créer le générateur de test
        test_generator = Phase2TestGenerator(db)
        
        # Exécuter le test complet
        results = asyncio.run(test_generator.run_complete_test())
        
        # Afficher le résumé
        test_generator.print_summary(results)
        
        # Sauvegarder les résultats
        output_file = os.path.join(os.path.dirname(__file__), "phase2_test_generation_results.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"📁 Résultats de test sauvegardés dans {output_file}")
        logger.info("✅ Test de génération Phase 2 terminé avec succès")
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'exécution du test: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
