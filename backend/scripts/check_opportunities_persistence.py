#!/usr/bin/env python3
"""
Script pour vérifier la persistance des opportunités et les calculs récents
"""

import sys
import os
from datetime import datetime, date
from typing import List, Dict, Any

# Ajouter le chemin du backend au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.models.advanced_opportunities import AdvancedOpportunity

class OpportunitiesPersistenceChecker:
    """Vérificateur de persistance des opportunités"""
    
    def __init__(self):
        """Initialise le vérificateur"""
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.db = self.SessionLocal()
        
    def __del__(self):
        """Ferme la session de base de données"""
        if hasattr(self, 'db'):
            self.db.close()
    
    def check_opportunities_table(self) -> Dict[str, Any]:
        """Vérifie l'état de la table advanced_opportunities"""
        print("🔍 Vérification de la table advanced_opportunities")
        
        # Compter le total d'opportunités
        total_count = self.db.query(AdvancedOpportunity).count()
        
        # Compter par date
        date_counts = self.db.query(
            func.date(AdvancedOpportunity.updated_at).label('date'),
            func.count(AdvancedOpportunity.id).label('count')
        ).group_by(func.date(AdvancedOpportunity.updated_at)).order_by(
            func.date(AdvancedOpportunity.updated_at).desc()
        ).limit(10).all()
        
        # Compter par symbole
        symbol_counts = self.db.query(
            AdvancedOpportunity.symbol,
            func.count(AdvancedOpportunity.id).label('count')
        ).group_by(AdvancedOpportunity.symbol).order_by(
            func.count(AdvancedOpportunity.id).desc()
        ).limit(10).all()
        
        # Compter par recommandation
        recommendation_counts = self.db.query(
            AdvancedOpportunity.recommendation,
            func.count(AdvancedOpportunity.id).label('count')
        ).group_by(AdvancedOpportunity.recommendation).all()
        
        # Compter par niveau de risque
        risk_counts = self.db.query(
            AdvancedOpportunity.risk_level,
            func.count(AdvancedOpportunity.id).label('count')
        ).group_by(AdvancedOpportunity.risk_level).all()
        
        # Récupérer les dernières opportunités
        latest_opportunities = self.db.query(AdvancedOpportunity).order_by(
            AdvancedOpportunity.updated_at.desc()
        ).limit(5).all()
        
        print(f"📊 Total d'opportunités: {total_count}")
        
        print(f"\n📅 Opportunités par date (10 dernières):")
        for date_count in date_counts:
            print(f"  • {date_count.date}: {date_count.count} opportunités")
        
        print(f"\n🏢 Opportunités par symbole (top 10):")
        for symbol_count in symbol_counts:
            print(f"  • {symbol_count.symbol}: {symbol_count.count} opportunités")
        
        print(f"\n📈 Opportunités par recommandation:")
        for rec_count in recommendation_counts:
            print(f"  • {rec_count.recommendation}: {rec_count.count} opportunités")
        
        print(f"\n⚠️ Opportunités par niveau de risque:")
        for risk_count in risk_counts:
            print(f"  • {risk_count.risk_level}: {risk_count.count} opportunités")
        
        print(f"\n🕒 5 dernières opportunités:")
        for opp in latest_opportunities:
            print(f"  • {opp.symbol}: {opp.recommendation} (score: {opp.composite_score:.3f}) - {opp.updated_at}")
        
        return {
            "total_count": total_count,
            "date_counts": [{"date": str(dc.date), "count": dc.count} for dc in date_counts],
            "symbol_counts": [{"symbol": sc.symbol, "count": sc.count} for sc in symbol_counts],
            "recommendation_counts": [{"recommendation": rc.recommendation, "count": rc.count} for rc in recommendation_counts],
            "risk_counts": [{"risk_level": rc.risk_level, "count": rc.count} for rc in risk_counts],
            "latest_opportunities": [
                {
                    "symbol": opp.symbol,
                    "recommendation": opp.recommendation,
                    "composite_score": float(opp.composite_score),
                    "updated_at": opp.updated_at.isoformat()
                }
                for opp in latest_opportunities
            ]
        }
    
    def check_today_opportunities(self) -> Dict[str, Any]:
        """Vérifie les opportunités d'aujourd'hui"""
        print("\n🔍 Vérification des opportunités d'aujourd'hui")
        
        today = date.today()
        
        # Compter les opportunités d'aujourd'hui
        today_count = self.db.query(AdvancedOpportunity).filter(
            func.date(AdvancedOpportunity.updated_at) == today
        ).count()
        
        # Récupérer les opportunités d'aujourd'hui
        today_opportunities = self.db.query(AdvancedOpportunity).filter(
            func.date(AdvancedOpportunity.updated_at) == today
        ).order_by(AdvancedOpportunity.composite_score.desc()).all()
        
        print(f"📅 Opportunités d'aujourd'hui ({today}): {today_count}")
        
        if today_opportunities:
            print(f"\n🏆 Top 10 des opportunités d'aujourd'hui:")
            for i, opp in enumerate(today_opportunities[:10], 1):
                print(f"  {i}. {opp.symbol}: {opp.recommendation} (score: {opp.composite_score:.3f}, confiance: {opp.confidence_level:.3f})")
        else:
            print("❌ Aucune opportunité trouvée pour aujourd'hui")
        
        return {
            "today": today.isoformat(),
            "count": today_count,
            "opportunities": [
                {
                    "symbol": opp.symbol,
                    "recommendation": opp.recommendation,
                    "composite_score": float(opp.composite_score),
                    "confidence_level": float(opp.confidence_level),
                    "risk_level": opp.risk_level,
                    "updated_at": opp.updated_at.isoformat()
                }
                for opp in today_opportunities
            ]
        }
    
    def check_optimized_scores(self) -> Dict[str, Any]:
        """Vérifie si les scores optimisés sont présents"""
        print("\n🔍 Vérification des scores optimisés")
        
        # Vérifier les nouvelles catégories de recommandation
        new_recommendations = ["BUY_STRONG", "BUY_MODERATE", "BUY_WEAK", "SELL_STRONG", "SELL_MODERATE"]
        
        optimized_count = self.db.query(AdvancedOpportunity).filter(
            AdvancedOpportunity.recommendation.in_(new_recommendations)
        ).count()
        
        print(f"📊 Opportunités avec recommandations optimisées: {optimized_count}")
        
        # Vérifier les scores composite élevés (> 0.6)
        high_scores_count = self.db.query(AdvancedOpportunity).filter(
            AdvancedOpportunity.composite_score > 0.6
        ).count()
        
        print(f"📈 Opportunités avec score composite > 0.6: {high_scores_count}")
        
        # Vérifier les niveaux de confiance élevés (> 0.8)
        high_confidence_count = self.db.query(AdvancedOpportunity).filter(
            AdvancedOpportunity.confidence_level > 0.8
        ).count()
        
        print(f"🎯 Opportunités avec confiance > 0.8: {high_confidence_count}")
        
        return {
            "optimized_recommendations_count": optimized_count,
            "high_scores_count": high_scores_count,
            "high_confidence_count": high_confidence_count
        }

def main():
    """Fonction principale"""
    print("🚀 Vérification de la persistance des opportunités")
    print("=" * 60)
    
    checker = OpportunitiesPersistenceChecker()
    
    try:
        # Vérification générale
        general_stats = checker.check_opportunities_table()
        
        # Vérification d'aujourd'hui
        today_stats = checker.check_today_opportunities()
        
        # Vérification des scores optimisés
        optimized_stats = checker.check_optimized_scores()
        
        # Résumé
        print("\n" + "=" * 60)
        print("RÉSUMÉ")
        print("=" * 60)
        
        print(f"📊 Total d'opportunités: {general_stats['total_count']}")
        print(f"📅 Opportunités d'aujourd'hui: {today_stats['count']}")
        print(f"🎯 Recommandations optimisées: {optimized_stats['optimized_recommendations_count']}")
        print(f"📈 Scores élevés (>0.6): {optimized_stats['high_scores_count']}")
        print(f"🎯 Confiance élevée (>0.8): {optimized_stats['high_confidence_count']}")
        
        if today_stats['count'] == 0:
            print("\n⚠️ ATTENTION: Aucune opportunité générée aujourd'hui!")
            print("💡 Suggestion: Utiliser l'endpoint /generate-daily-opportunities pour générer de nouvelles opportunités")
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        del checker

if __name__ == "__main__":
    main()
