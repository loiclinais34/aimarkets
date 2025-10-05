#!/usr/bin/env python3
"""
Script de test pour la génération des opportunités du jour
Teste le nouvel endpoint /generate-daily-opportunities
"""

import asyncio
import sys
import os
import json
from datetime import datetime, date
from typing import List, Dict, Any

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.services.advanced_analysis.advanced_trading_analysis import AdvancedTradingAnalysis

class DailyOpportunitiesTester:
    """Testeur pour la génération des opportunités du jour"""
    
    def __init__(self):
        """Initialise le testeur"""
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        self.analyzer = AdvancedTradingAnalysis()
        
    def __del__(self):
        """Ferme la session de base de données"""
        if hasattr(self, 'db'):
            self.db.close()
    
    async def test_daily_generation_small_batch(self, symbols: List[str] = None) -> Dict[str, Any]:
        """Teste la génération sur un petit lot de symboles"""
        print("🧪 Test de génération des opportunités du jour (petit lot)")
        
        if not symbols:
            symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        
        print(f"📊 Analyse de {len(symbols)} symboles: {symbols}")
        
        opportunities = []
        errors = []
        
        for symbol in symbols:
            try:
                print(f"  🔍 Analyse de {symbol}...")
                
                # Effectuer l'analyse complète
                result = await self.analyzer.analyze_opportunity(
                    symbol=symbol,
                    time_horizon=30,
                    include_ml=True,
                    db=self.db
                )
                
                # Ajouter l'opportunité
                opportunities.append({
                    "symbol": symbol,
                    "analysis_date": result.analysis_date,
                    "recommendation": result.recommendation,
                    "risk_level": result.risk_level,
                    "composite_score": result.composite_score,
                    "confidence_level": result.confidence_level,
                    "scores": {
                        "technical": result.technical_score,
                        "sentiment": result.sentiment_score,
                        "market": result.market_score,
                        "ml": result.ml_score,
                        "candlestick": result.candlestick_score,
                        "garch": result.garch_score,
                        "monte_carlo": result.monte_carlo_score,
                        "markov": result.markov_score,
                        "volatility": result.volatility_score
                    }
                })
                
                print(f"    ✅ {symbol}: {result.recommendation} (score: {result.composite_score:.3f})")
                
            except Exception as e:
                print(f"    ❌ {symbol}: Erreur - {e}")
                errors.append({
                    "symbol": symbol,
                    "error": str(e)
                })
                continue
        
        # Trier par score composite
        opportunities.sort(key=lambda x: x["composite_score"], reverse=True)
        
        # Calculer les statistiques
        total_analyzed = len(opportunities)
        total_errors = len(errors)
        
        # Statistiques par recommandation
        recommendation_stats = {}
        for opp in opportunities:
            rec = opp["recommendation"]
            if rec not in recommendation_stats:
                recommendation_stats[rec] = 0
            recommendation_stats[rec] += 1
        
        # Statistiques par niveau de risque
        risk_stats = {}
        for opp in opportunities:
            risk = opp["risk_level"]
            if risk not in risk_stats:
                risk_stats[risk] = 0
            risk_stats[risk] += 1
        
        # Top 5 des meilleures opportunités
        top_opportunities = opportunities[:5]
        
        print(f"\n📈 Résultats du test:")
        print(f"  • Symboles analysés: {total_analyzed}")
        print(f"  • Erreurs: {total_errors}")
        print(f"  • Taux de succès: {round((total_analyzed / len(symbols)) * 100, 2)}%")
        
        print(f"\n📊 Statistiques par recommandation:")
        for rec, count in recommendation_stats.items():
            print(f"  • {rec}: {count}")
        
        print(f"\n⚠️ Statistiques par niveau de risque:")
        for risk, count in risk_stats.items():
            print(f"  • {risk}: {count}")
        
        print(f"\n🏆 Top 5 des meilleures opportunités:")
        for i, opp in enumerate(top_opportunities, 1):
            print(f"  {i}. {opp['symbol']}: {opp['recommendation']} (score: {opp['composite_score']:.3f}, confiance: {opp['confidence_level']:.3f})")
        
        if errors:
            print(f"\n❌ Erreurs rencontrées:")
            for error in errors:
                print(f"  • {error['symbol']}: {error['error']}")
        
        return {
            "status": "success",
            "generation_date": date.today().isoformat(),
            "summary": {
                "total_symbols_requested": len(symbols),
                "total_opportunities_generated": total_analyzed,
                "total_errors": total_errors,
                "success_rate": round((total_analyzed / len(symbols)) * 100, 2) if symbols else 0
            },
            "statistics": {
                "recommendations": recommendation_stats,
                "risk_levels": risk_stats,
                "average_composite_score": round(sum(opp["composite_score"] for opp in opportunities) / total_analyzed, 3) if total_analyzed > 0 else 0,
                "average_confidence": round(sum(opp["confidence_level"] for opp in opportunities) / total_analyzed, 3) if total_analyzed > 0 else 0
            },
            "top_opportunities": top_opportunities,
            "all_opportunities": opportunities,
            "errors": errors
        }
    
    async def test_daily_generation_large_batch(self, limit: int = 20) -> Dict[str, Any]:
        """Teste la génération sur un grand lot de symboles"""
        print(f"🧪 Test de génération des opportunités du jour (grand lot - {limit} symboles)")
        
        # Récupérer les symboles disponibles
        from app.models.database import HistoricalData
        
        symbol_query = self.db.query(HistoricalData.symbol).distinct().limit(limit)
        available_symbols = [row.symbol for row in symbol_query.all()]
        
        if not available_symbols:
            print("❌ Aucun symbole disponible")
            return {"status": "error", "message": "Aucun symbole disponible"}
        
        print(f"📊 Analyse de {len(available_symbols)} symboles disponibles")
        
        # Utiliser la même logique que le test petit lot
        return await self.test_daily_generation_small_batch(available_symbols)
    
    def save_test_results(self, results: Dict[str, Any], filename: str = None):
        """Sauvegarde les résultats du test"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"daily_opportunities_test_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"💾 Résultats sauvegardés dans: {filepath}")
        return filepath

async def main():
    """Fonction principale de test"""
    print("🚀 Démarrage des tests de génération des opportunités du jour")
    print("=" * 60)
    
    tester = DailyOpportunitiesTester()
    
    try:
        # Test 1: Petit lot de symboles populaires
        print("\n" + "=" * 60)
        print("TEST 1: Petit lot de symboles populaires")
        print("=" * 60)
        
        small_batch_results = await tester.test_daily_generation_small_batch()
        tester.save_test_results(small_batch_results, "daily_opportunities_small_batch.json")
        
        # Test 2: Grand lot de symboles disponibles
        print("\n" + "=" * 60)
        print("TEST 2: Grand lot de symboles disponibles")
        print("=" * 60)
        
        large_batch_results = await tester.test_daily_generation_large_batch(limit=20)
        tester.save_test_results(large_batch_results, "daily_opportunities_large_batch.json")
        
        # Résumé final
        print("\n" + "=" * 60)
        print("RÉSUMÉ FINAL")
        print("=" * 60)
        
        print(f"✅ Test petit lot: {small_batch_results['summary']['total_opportunities_generated']} opportunités générées")
        print(f"✅ Test grand lot: {large_batch_results['summary']['total_opportunities_generated']} opportunités générées")
        
        print(f"\n📊 Moyenne des scores composite:")
        print(f"  • Petit lot: {small_batch_results['statistics']['average_composite_score']}")
        print(f"  • Grand lot: {large_batch_results['statistics']['average_composite_score']}")
        
        print(f"\n🎯 Moyenne des niveaux de confiance:")
        print(f"  • Petit lot: {small_batch_results['statistics']['average_confidence']}")
        print(f"  • Grand lot: {large_batch_results['statistics']['average_confidence']}")
        
        print("\n🎉 Tests terminés avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors des tests: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        del tester

if __name__ == "__main__":
    asyncio.run(main())
