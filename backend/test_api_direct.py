#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.advanced_opportunities import AdvancedOpportunity
from sqlalchemy import desc

def test_api_logic():
    """Test direct de la logique de l'API"""
    db = next(get_db())
    
    print("=== Test direct de la logique API ===")
    
    # Paramètres exacts de l'API
    min_score = 0.0
    max_risk = "HIGH"
    limit = 2
    sort_by = "composite_score"
    sort_order = "desc"
    recommendations = "BUY_WEAK"
    
    # Construire la requête exactement comme dans l'API
    query = db.query(AdvancedOpportunity)
    
    # Filtrer par score composite minimum
    query = query.filter(AdvancedOpportunity.composite_score >= min_score)
    
    # Filtrer par niveau de risque
    risk_levels = ["LOW", "MEDIUM", "HIGH"]
    if max_risk in risk_levels:
        max_risk_index = risk_levels.index(max_risk)
        allowed_risks = risk_levels[:max_risk_index + 1]
        query = query.filter(AdvancedOpportunity.risk_level.in_(allowed_risks))
    
    # Filtres de recommandation - LOGIQUE EXACTE DE L'API
    if recommendations:
        try:
            rec_list = [rec.strip().upper() for rec in recommendations.split(",")]
            valid_recommendations = ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL", "BUY_WEAK", "BUY_MODERATE", "SELL_WEAK", "SELL_MODERATE", "SELL_STRONG"]
            rec_list = [rec for rec in rec_list if rec in valid_recommendations]
            print(f"Recommandations filtrées: {rec_list}")
            if rec_list:
                query = query.filter(AdvancedOpportunity.recommendation.in_(rec_list))
                print(f"Filtre recommandation appliqué: {rec_list}")
            else:
                print(f"Aucune recommandation valide trouvée dans: {recommendations}")
        except Exception as e:
            print(f"Erreur parsing recommandations {recommendations}: {e}")
    
    # Tri
    valid_sort_fields = {
        "composite_score": AdvancedOpportunity.composite_score,
        "confidence_level": AdvancedOpportunity.confidence_level,
        "analysis_date": AdvancedOpportunity.analysis_date,
        "updated_at": AdvancedOpportunity.updated_at,
        "technical_score": AdvancedOpportunity.technical_score,
        "sentiment_score": AdvancedOpportunity.sentiment_score,
        "market_score": AdvancedOpportunity.market_score
    }
    
    sort_field = valid_sort_fields.get(sort_by, AdvancedOpportunity.composite_score)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_field.asc())
    else:
        query = query.order_by(sort_field.desc())
    
    # Limiter les résultats
    opportunities = query.limit(limit).all()
    
    print(f"\nRésultats finaux ({len(opportunities)}):")
    for opp in opportunities:
        print(f"  {opp.symbol}: {opp.recommendation} (score: {opp.composite_score:.3f})")
    
    db.close()

if __name__ == "__main__":
    test_api_logic()

