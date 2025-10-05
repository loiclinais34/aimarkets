#!/usr/bin/env python3
"""
Script pour déboguer la génération des opportunités du jour
"""

import sys
import os
from datetime import datetime, date
from typing import Dict, Any
import json

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.advanced_opportunities import AdvancedOpportunity
from app.services.advanced_analysis.advanced_trading_analysis import AdvancedTradingAnalysis

class DailyOpportunitiesDebugger:
    """Débogueur de la génération des opportunités du jour"""
    
    def __init__(self):
        """Initialise le débogueur"""
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        self.analyzer = AdvancedTradingAnalysis()
        
    def __del__(self):
        """Ferme la session de base de données"""
        if hasattr(self, 'db'):
            self.db.close()
    
    def check_today_opportunities(self) -> Dict[str, Any]:
        """Vérifie les opportunités d'aujourd'hui"""
        print("🔍 Vérification des opportunités d'aujourd'hui...")
        
        today_opps = self.db.query(AdvancedOpportunity).filter(
            func.date(AdvancedOpportunity.analysis_date) == date.today()
        ).all()
        
        analysis = {
            "total_opportunities": len(today_opps),
            "opportunities": [],
            "issues": []
        }
        
        for opp in today_opps:
            opp_data = {
                "symbol": opp.symbol,
                "analysis_date": opp.analysis_date.isoformat() if opp.analysis_date else None,
                "updated_at": opp.updated_at.isoformat() if opp.updated_at else None,
                "recommendation": opp.recommendation,
                "risk_level": opp.risk_level,
                "composite_score": float(opp.composite_score) if opp.composite_score else None,
                "technical_score": float(opp.technical_score) if opp.technical_score else None,
                "sentiment_score": float(opp.sentiment_score) if opp.sentiment_score else None,
                "market_score": float(opp.market_score) if opp.market_score else None,
                "ml_score": float(opp.ml_score) if opp.ml_score else None,
                "candlestick_score": float(opp.candlestick_score) if opp.candlestick_score else None,
                "garch_score": float(opp.garch_score) if opp.garch_score else None,
                "monte_carlo_score": float(opp.monte_carlo_score) if opp.monte_carlo_score else None,
                "markov_score": float(opp.markov_score) if opp.markov_score else None,
                "volatility_score": float(opp.volatility_score) if opp.volatility_score else None,
                "confidence_level": float(opp.confidence_level) if opp.confidence_level else None
            }
            
            analysis["opportunities"].append(opp_data)
            
            # Vérifier les problèmes
            if opp.recommendation == "HOLD" and opp.risk_level == "HIGH":
                analysis["issues"].append(f"{opp.symbol}: Toutes les opportunités sont HOLD avec risque HIGH")
            
            if opp.composite_score and float(opp.composite_score) < 0.5:
                analysis["issues"].append(f"{opp.symbol}: Score composite faible ({opp.composite_score})")
        
        return analysis
    
    def test_single_opportunity_generation(self, symbol: str = "AAPL") -> Dict[str, Any]:
        """Teste la génération d'une opportunité pour un symbole"""
        print(f"🧪 Test de génération d'opportunité pour {symbol}...")
        
        try:
            # Générer une opportunité
            import asyncio
            result = asyncio.run(self.analyzer.analyze_opportunity(
                symbol=symbol,
                time_horizon=30,
                include_ml=True,
                db=self.db
            ))
            
            return {
                "success": True,
                "symbol": symbol,
                "result": {
                    "recommendation": result.recommendation,
                    "risk_level": result.risk_level,
                    "composite_score": result.composite_score,
                    "technical_score": result.technical_score,
                    "sentiment_score": result.sentiment_score,
                    "market_score": result.market_score,
                    "ml_score": result.ml_score,
                    "candlestick_score": result.candlestick_score,
                    "garch_score": result.garch_score,
                    "monte_carlo_score": result.monte_carlo_score,
                    "markov_score": result.markov_score,
                    "volatility_score": result.volatility_score,
                    "confidence_level": result.confidence_level
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "symbol": symbol,
                "error": str(e)
            }
    
    def check_optimization_thresholds(self) -> Dict[str, Any]:
        """Vérifie si les seuils d'optimisation sont appliqués"""
        print("🎯 Vérification des seuils d'optimisation...")
        
        today_opps = self.db.query(AdvancedOpportunity).filter(
            func.date(AdvancedOpportunity.analysis_date) == date.today()
        ).all()
        
        thresholds = {
            "technical_threshold": 0.533,
            "composite_threshold": 0.651,
            "confidence_threshold": 0.6
        }
        
        analysis = {
            "thresholds": thresholds,
            "compliance": {
                "meets_technical": 0,
                "meets_composite": 0,
                "meets_confidence": 0,
                "meets_all": 0
            },
            "total_opportunities": len(today_opps)
        }
        
        for opp in today_opps:
            if opp.technical_score and float(opp.technical_score) >= thresholds["technical_threshold"]:
                analysis["compliance"]["meets_technical"] += 1
            
            if opp.composite_score and float(opp.composite_score) >= thresholds["composite_threshold"]:
                analysis["compliance"]["meets_composite"] += 1
            
            if opp.confidence_level and float(opp.confidence_level) >= thresholds["confidence_threshold"]:
                analysis["compliance"]["meets_confidence"] += 1
            
            # Vérifier si toutes les conditions sont remplies
            if (opp.technical_score and float(opp.technical_score) >= thresholds["technical_threshold"] and
                opp.composite_score and float(opp.composite_score) >= thresholds["composite_threshold"] and
                opp.confidence_level and float(opp.confidence_level) >= thresholds["confidence_threshold"]):
                analysis["compliance"]["meets_all"] += 1
        
        return analysis
    
    def run_complete_debug(self) -> Dict[str, Any]:
        """Exécute le débogage complet"""
        print("🚀 Démarrage du débogage de la génération des opportunités du jour")
        print("=" * 80)
        
        # Vérifier les opportunités d'aujourd'hui
        today_analysis = self.check_today_opportunities()
        
        # Vérifier les seuils d'optimisation
        threshold_analysis = self.check_optimization_thresholds()
        
        # Test de génération d'une opportunité
        test_result = self.test_single_opportunity_generation("AAPL")
        
        results = {
            "debug_date": datetime.now().isoformat(),
            "today_opportunities": today_analysis,
            "optimization_thresholds": threshold_analysis,
            "single_generation_test": test_result
        }
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Affiche un résumé du débogage"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DU DÉBOGAGE DES OPPORTUNITÉS DU JOUR")
        print("=" * 80)
        
        # Opportunités d'aujourd'hui
        today = results["today_opportunities"]
        print(f"📈 OPPORTUNITÉS D'AUJOURD'HUI: {today['total_opportunities']}")
        
        if today["issues"]:
            print(f"\n⚠️ PROBLÈMES IDENTIFIÉS:")
            for issue in today["issues"]:
                print(f"  • {issue}")
        
        # Seuils d'optimisation
        thresholds = results["optimization_thresholds"]
        print(f"\n🎯 CONFORMITÉ AUX SEUILS D'OPTIMISATION:")
        print(f"  • Seuil technique (≥0.533): {thresholds['compliance']['meets_technical']}/{thresholds['total_opportunities']}")
        print(f"  • Seuil composite (≥0.651): {thresholds['compliance']['meets_composite']}/{thresholds['total_opportunities']}")
        print(f"  • Seuil confiance (≥0.6): {thresholds['compliance']['meets_confidence']}/{thresholds['total_opportunities']}")
        print(f"  • Tous les seuils: {thresholds['compliance']['meets_all']}/{thresholds['total_opportunities']}")
        
        # Test de génération
        test = results["single_generation_test"]
        if test["success"]:
            print(f"\n✅ TEST DE GÉNÉRATION: OK")
            print(f"  • Symbole: {test['symbol']}")
            print(f"  • Recommandation: {test['result']['recommendation']}")
            print(f"  • Score composite: {test['result']['composite_score']}")
        else:
            print(f"\n❌ TEST DE GÉNÉRATION: ÉCHEC")
            print(f"  • Erreur: {test['error']}")

def main():
    """Fonction principale"""
    debugger = DailyOpportunitiesDebugger()
    
    try:
        # Exécuter le débogage complet
        results = debugger.run_complete_debug()
        
        # Afficher le résumé
        debugger.print_summary(results)
        
        # Sauvegarder les résultats
        filename = "daily_opportunities_debug.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📁 Résultats sauvegardés dans {filename}")
        print(f"\n✅ Débogage terminé avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors du débogage: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        del debugger

if __name__ == "__main__":
    main()
