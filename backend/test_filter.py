#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.models.advanced_opportunities import AdvancedOpportunity
from sqlalchemy import desc

def test_recommendation_filter():
    db = next(get_db())
    
    print("=== Test du filtre de recommandation ===")
    
    # Test 1: Récupérer toutes les recommandations distinctes
    recommendations = db.query(AdvancedOpportunity.recommendation).distinct().all()
    print(f"Recommandations disponibles: {[r[0] for r in recommendations]}")
    
    # Test 2: Compter les BUY_WEAK
    buy_weak_count = db.query(AdvancedOpportunity).filter(AdvancedOpportunity.recommendation == "BUY_WEAK").count()
    print(f"Nombre d'opportunités BUY_WEAK: {buy_weak_count}")
    
    # Test 3: Requête exacte comme dans l'API
    print("\n=== Test de la requête API ===")
    query = db.query(AdvancedOpportunity)
    
    # Filtres de base
    min_score = 0.0
    max_risk = "HIGH"
    recommendations = "BUY_WEAK"
    limit = 3
    sort_by = "analysis_date"
    sort_order = "desc"
    
    print(f"Filtres appliqués:")
    print(f"  min_score: {min_score}")
    print(f"  max_risk: {max_risk}")
    print(f"  recommendations: {recommendations}")
    print(f"  limit: {limit}")
    print(f"  sort_by: {sort_by}")
    print(f"  sort_order: {sort_order}")
    
    # Filtrer par score composite minimum
    query = query.filter(AdvancedOpportunity.composite_score >= min_score)
    print(f"Après filtre score >= {min_score}: {query.count()} résultats")
    
    # Filtrer par niveau de risque
    risk_levels = ["LOW", "MEDIUM", "HIGH"]
    max_risk_index = risk_levels.index(max_risk)
    allowed_risks = risk_levels[:max_risk_index + 1]
    query = query.filter(AdvancedOpportunity.risk_level.in_(allowed_risks))
    print(f"Après filtre risque <= {max_risk}: {query.count()} résultats")
    
    # Filtres de recommandation
    if recommendations:
        rec_list = [rec.strip().upper() for rec in recommendations.split(",")]
        valid_recommendations = ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL", "BUY_WEAK", "BUY_MODERATE", "SELL_WEAK", "SELL_MODERATE", "SELL_STRONG"]
        rec_list = [rec for rec in rec_list if rec in valid_recommendations]
        print(f"Recommandations filtrées: {rec_list}")
        if rec_list:
            query = query.filter(AdvancedOpportunity.recommendation.in_(rec_list))
            print(f"Après filtre recommandation {rec_list}: {query.count()} résultats")
    
    # Tri
    if sort_by == "analysis_date":
        if sort_order == "desc":
            query = query.order_by(desc(AdvancedOpportunity.analysis_date))
        else:
            query = query.order_by(AdvancedOpportunity.analysis_date)
    elif sort_by == "composite_score":
        if sort_order == "desc":
            query = query.order_by(desc(AdvancedOpportunity.composite_score))
        else:
            query = query.order_by(AdvancedOpportunity.composite_score)
    
    # Limiter les résultats
    results = query.limit(limit).all()
    
    print(f"\nRésultats finaux ({len(results)}):")
    for result in results:
        print(f"  {result.symbol}: {result.recommendation} (score: {result.composite_score:.3f}, date: {result.analysis_date})")
    
    db.close()

if __name__ == "__main__":
    test_recommendation_filter()

