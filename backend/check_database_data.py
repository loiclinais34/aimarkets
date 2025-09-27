#!/usr/bin/env python3
"""
Test de vérification des données disponibles en base
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.models.database import HistoricalData, SentimentData, TechnicalIndicators, SentimentIndicators
from sqlalchemy import func

def check_database_data():
    """Vérifier les données disponibles en base"""
    
    db = next(get_db())
    
    print("🔍 Vérification des données disponibles en base de données")
    print("=" * 60)
    
    # Vérifier les données historiques
    print("\n📈 Données Historiques:")
    historical_count = db.query(func.count(HistoricalData.id)).scalar()
    print(f"   Total: {historical_count} enregistrements")
    
    symbols_historical = db.query(HistoricalData.symbol, func.count(HistoricalData.id))\
        .group_by(HistoricalData.symbol)\
        .order_by(func.count(HistoricalData.id).desc())\
        .limit(5).all()
    
    print("   Top 5 symboles:")
    for symbol, count in symbols_historical:
        print(f"     {symbol}: {count} enregistrements")
    
    # Vérifier les données de sentiment
    print("\n📊 Données de Sentiment:")
    sentiment_count = db.query(func.count(SentimentData.id)).scalar()
    print(f"   Total: {sentiment_count} enregistrements")
    
    if sentiment_count > 0:
        symbols_sentiment = db.query(SentimentData.symbol, func.count(SentimentData.id))\
            .group_by(SentimentData.symbol)\
            .order_by(func.count(SentimentData.id).desc())\
            .limit(5).all()
        
        print("   Top 5 symboles:")
        for symbol, count in symbols_sentiment:
            print(f"     {symbol}: {count} enregistrements")
    else:
        print("   ⚠️  Aucune donnée de sentiment disponible")
    
    # Vérifier les indicateurs techniques existants
    print("\n🔧 Indicateurs Techniques:")
    technical_count = db.query(func.count(TechnicalIndicators.id)).scalar()
    print(f"   Total: {technical_count} enregistrements")
    
    # Vérifier les indicateurs de sentiment existants
    print("\n📈 Indicateurs de Sentiment:")
    sentiment_indicators_count = db.query(func.count(SentimentIndicators.id)).scalar()
    print(f"   Total: {sentiment_indicators_count} enregistrements")
    
    print("\n🎯 Recommandations:")
    print("=" * 60)
    
    if historical_count == 0:
        print("❌ Aucune donnée historique - Impossible de calculer les indicateurs techniques")
    else:
        print("✅ Données historiques disponibles - Calcul des indicateurs techniques possible")
    
    if sentiment_count == 0:
        print("❌ Aucune donnée de sentiment - Impossible de calculer les indicateurs de sentiment")
        print("💡 Solution: Utiliser des données simulées ou calculer des indicateurs basés sur les prix")
    else:
        print("✅ Données de sentiment disponibles - Calcul des indicateurs de sentiment possible")
    
    db.close()

if __name__ == "__main__":
    check_database_data()

