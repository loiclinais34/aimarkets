#!/usr/bin/env python3
"""
Test de la pipeline simplifiée - Base de données uniquement
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db
from app.models.database import HistoricalData, SentimentData, TechnicalIndicators, SentimentIndicators
from sqlalchemy import func
from datetime import datetime, timedelta

def test_simplified_pipeline():
    """Test de la pipeline simplifiée utilisant uniquement la base de données"""
    
    db = next(get_db())
    symbols = ["AAPL", "MSFT", "GOOGL"]
    
    print("🚀 Test de la Pipeline Simplifiée - Base de Données Uniquement")
    print(f"📊 Symboles: {symbols}")
    print("=" * 60)
    
    results = {
        "technical": {},
        "sentiment": {},
        "market": {}
    }
    
    for symbol in symbols:
        print(f"\n🔍 Analyse de {symbol}:")
        print("-" * 30)
        
        # 1. Vérifier les données historiques
        historical_count = db.query(func.count(HistoricalData.id))\
            .filter(HistoricalData.symbol == symbol).scalar()
        print(f"   📈 Données historiques: {historical_count} enregistrements")
        
        # 2. Vérifier les données de sentiment
        sentiment_count = db.query(func.count(SentimentData.id))\
            .filter(SentimentData.symbol == symbol).scalar()
        print(f"   📊 Données de sentiment: {sentiment_count} enregistrements")
        
        # 3. Vérifier les indicateurs techniques existants
        technical_count = db.query(func.count(TechnicalIndicators.id))\
            .filter(TechnicalIndicators.symbol == symbol).scalar()
        print(f"   🔧 Indicateurs techniques: {technical_count} enregistrements")
        
        # 4. Vérifier les indicateurs de sentiment existants
        sentiment_indicators_count = db.query(func.count(SentimentIndicators.id))\
            .filter(SentimentIndicators.symbol == symbol).scalar()
        print(f"   📈 Indicateurs de sentiment: {sentiment_indicators_count} enregistrements")
        
        # 5. Déterminer le statut
        technical_status = "✅ Disponible" if technical_count > 0 else "❌ Manquant"
        sentiment_status = "✅ Disponible" if sentiment_indicators_count > 0 else "❌ Manquant"
        market_status = "✅ Disponible"  # Simulation pour l'instant
        
        print(f"   🎯 Statut technique: {technical_status}")
        print(f"   🎯 Statut sentiment: {sentiment_status}")
        print(f"   🎯 Statut marché: {market_status}")
        
        results["technical"][symbol] = {
            "count": technical_count,
            "status": "available" if technical_count > 0 else "missing"
        }
        results["sentiment"][symbol] = {
            "count": sentiment_indicators_count,
            "status": "available" if sentiment_indicators_count > 0 else "missing"
        }
        results["market"][symbol] = {
            "count": 0,  # Simulation
            "status": "simulated"
        }
    
    print("\n📋 Résumé de la Pipeline:")
    print("=" * 60)
    
    # Résumé technique
    technical_available = sum(1 for s in results["technical"].values() if s["status"] == "available")
    print(f"🔧 Indicateurs Techniques: {technical_available}/{len(symbols)} disponibles")
    
    # Résumé sentiment
    sentiment_available = sum(1 for s in results["sentiment"].values() if s["status"] == "available")
    print(f"📊 Indicateurs de Sentiment: {sentiment_available}/{len(symbols)} disponibles")
    
    # Résumé marché
    print(f"🏪 Indicateurs de Marché: {len(symbols)}/{len(symbols)} simulés")
    
    print("\n🎯 Conclusion:")
    if technical_available == len(symbols) and sentiment_available == len(symbols):
        print("✅ Pipeline prête - Tous les indicateurs sont disponibles en base")
        print("💡 Les services peuvent retourner directement les données existantes")
    else:
        print("⚠️  Pipeline partielle - Certains indicateurs manquent")
        print("💡 Les services doivent calculer les indicateurs manquants")
    
    db.close()
    return results

if __name__ == "__main__":
    test_simplified_pipeline()

