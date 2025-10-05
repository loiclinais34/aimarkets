#!/usr/bin/env python3
"""
Script pour corriger la génération des opportunités du jour
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

class DailyOpportunitiesFixer:
    """Correcteur de la génération des opportunités du jour"""
    
    def __init__(self):
        """Initialise le correcteur"""
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        self.analyzer = AdvancedTradingAnalysis()
        
    def __del__(self):
        """Ferme la session de base de données"""
        if hasattr(self, 'db'):
            self.db.close()
    
    def clear_today_opportunities(self):
        """Supprime les opportunités d'aujourd'hui"""
        print("🗑️ Suppression des opportunités d'aujourd'hui...")
        
        deleted_count = self.db.query(AdvancedOpportunity).filter(
            func.date(AdvancedOpportunity.analysis_date) == date.today()
        ).delete()
        
        self.db.commit()
        print(f"✅ {deleted_count} opportunités supprimées")
        
        return deleted_count
    
    def generate_optimized_opportunities(self, symbols: list = None, limit: int = 20):
        """Génère des opportunités optimisées"""
        print(f"🔧 Génération d'opportunités optimisées pour {limit} symboles...")
        
        if not symbols:
            # Récupérer les symboles disponibles
            from app.models.database import HistoricalData
            symbol_query = self.db.query(HistoricalData.symbol).distinct().limit(limit)
            symbols = [row.symbol for row in symbol_query.all()]
        
        opportunities = []
        errors = []
        
        for symbol in symbols:
            try:
                print(f"  📊 Analyse de {symbol}...")
                
                # Générer l'opportunité
                import asyncio
                result = asyncio.run(self.analyzer.analyze_opportunity(
                    symbol=symbol,
                    time_horizon=30,
                    include_ml=True,
                    db=self.db
                ))
                
                # Vérifier si l'opportunité passe les seuils ajustés
                if (result.technical_score >= 0.45 and 
                    result.composite_score >= 0.50 and 
                    result.confidence_level >= 0.6):
                    
                    # Créer l'opportunité en base
                    opportunity = AdvancedOpportunity(
                        symbol=symbol,
                        analysis_date=result.analysis_date,
                        recommendation=result.recommendation,
                        risk_level=result.risk_level,
                        composite_score=result.composite_score,
                        confidence_level=result.confidence_level,
                        technical_score=result.technical_score,
                        sentiment_score=result.sentiment_score,
                        market_score=result.market_score,
                        ml_score=result.ml_score,
                        candlestick_score=result.candlestick_score,
                        garch_score=result.garch_score,
                        monte_carlo_score=result.monte_carlo_score,
                        markov_score=result.markov_score,
                        volatility_score=result.volatility_score,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    
                    self.db.add(opportunity)
                    opportunities.append({
                        "symbol": symbol,
                        "recommendation": result.recommendation,
                        "composite_score": result.composite_score,
                        "technical_score": result.technical_score,
                        "confidence_level": result.confidence_level
                    })
                    
                    print(f"    ✅ {symbol}: {result.recommendation} (score: {result.composite_score:.3f})")
                else:
                    print(f"    ⚠️ {symbol}: Ne passe pas les seuils ajustés")
                    print(f"      - Technique: {result.technical_score:.3f} (seuil: 0.45)")
                    print(f"      - Composite: {result.composite_score:.3f} (seuil: 0.50)")
                    print(f"      - Confiance: {result.confidence_level:.3f} (seuil: 0.6)")
                
            except Exception as e:
                print(f"    ❌ Erreur pour {symbol}: {e}")
                errors.append({"symbol": symbol, "error": str(e)})
        
        # Sauvegarder en base
        try:
            self.db.commit()
            print(f"✅ {len(opportunities)} opportunités optimisées sauvegardées")
        except Exception as e:
            self.db.rollback()
            print(f"❌ Erreur lors de la sauvegarde: {e}")
            raise
        
        return {
            "opportunities": opportunities,
            "errors": errors,
            "total_generated": len(opportunities)
        }
    
    def run_fix(self):
        """Exécute la correction complète"""
        print("🚀 Démarrage de la correction de la génération des opportunités du jour")
        print("=" * 80)
        
        # Supprimer les opportunités d'aujourd'hui
        deleted_count = self.clear_today_opportunities()
        
        # Générer de nouvelles opportunités optimisées
        generation_result = self.generate_optimized_opportunities(limit=50)
        
        # Vérifier le résultat
        today_opps = self.db.query(AdvancedOpportunity).filter(
            func.date(AdvancedOpportunity.analysis_date) == date.today()
        ).all()
        
        results = {
            "fix_date": datetime.now().isoformat(),
            "deleted_opportunities": deleted_count,
            "generation_result": generation_result,
            "final_opportunities_count": len(today_opps),
            "success": len(today_opps) > 0
        }
        
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Affiche un résumé de la correction"""
        print("\n" + "=" * 80)
        print("📊 RÉSUMÉ DE LA CORRECTION DES OPPORTUNITÉS DU JOUR")
        print("=" * 80)
        
        print(f"🗑️ Opportunités supprimées: {results['deleted_opportunities']}")
        print(f"🔧 Opportunités générées: {results['generation_result']['total_generated']}")
        print(f"📈 Opportunités finales: {results['final_opportunities_count']}")
        
        if results['generation_result']['opportunities']:
            print(f"\n✅ OPPORTUNITÉS OPTIMISÉES GÉNÉRÉES:")
            for opp in results['generation_result']['opportunities']:
                print(f"  • {opp['symbol']}: {opp['recommendation']} (score: {opp['composite_score']:.3f})")
        
        if results['generation_result']['errors']:
            print(f"\n❌ ERREURS:")
            for error in results['generation_result']['errors']:
                print(f"  • {error['symbol']}: {error['error']}")
        
        if results['success']:
            print(f"\n🎯 CORRECTION: ✅ RÉUSSIE")
            print("   Les opportunités du jour utilisent maintenant les seuils optimisés")
        else:
            print(f"\n🎯 CORRECTION: ❌ ÉCHEC")
            print("   Aucune opportunité optimisée n'a été générée")

def main():
    """Fonction principale"""
    fixer = DailyOpportunitiesFixer()
    
    try:
        # Exécuter la correction
        results = fixer.run_fix()
        
        # Afficher le résumé
        fixer.print_summary(results)
        
        # Sauvegarder les résultats
        filename = "daily_opportunities_fix.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n📁 Résultats sauvegardés dans {filename}")
        print(f"\n✅ Correction terminée avec succès")
        
    except Exception as e:
        print(f"❌ Erreur lors de la correction: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        del fixer

if __name__ == "__main__":
    main()
