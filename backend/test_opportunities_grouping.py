#!/usr/bin/env python3
"""
Test script pour vérifier le regroupement des opportunités par symbole
"""

import requests
import json
from collections import defaultdict

def test_opportunities_grouping():
    """Test du regroupement des opportunités par symbole"""
    
    print("🔍 Test du regroupement des opportunités par symbole")
    print("=" * 60)
    
    try:
        # Récupérer les opportunités
        response = requests.get("http://localhost:8000/api/v1/screener/latest-opportunities")
        
        if response.status_code != 200:
            print(f"❌ Erreur API: {response.status_code}")
            return
        
        opportunities = response.json()
        print(f"📊 {len(opportunities)} opportunités récupérées")
        
        if not opportunities:
            print("⚠️  Aucune opportunité trouvée")
            return
        
        # Grouper par symbole
        grouped = defaultdict(list)
        for opp in opportunities:
            grouped[opp['symbol']].append(opp)
        
        print(f"\n📈 {len(grouped)} symboles uniques trouvés:")
        print("-" * 40)
        
        # Afficher les statistiques par symbole
        for symbol, symbol_opportunities in grouped.items():
            company_name = symbol_opportunities[0]['company_name']
            best_confidence = max(opp['confidence'] for opp in symbol_opportunities)
            best_model = max(symbol_opportunities, key=lambda x: x['confidence'])['model_name']
            total_opportunities = len(symbol_opportunities)
            
            print(f"🏢 {symbol} - {company_name}")
            print(f"   📊 {total_opportunities} opportunité{'s' if total_opportunities > 1 else ''}")
            print(f"   🎯 Meilleur score: {best_confidence:.3f} ({best_model})")
            print(f"   📅 Périodes: {set(opp['time_horizon'] for opp in symbol_opportunities)}")
            print(f"   💰 Rendements: {set(opp['target_return'] for opp in symbol_opportunities)}")
            print()
        
        # Vérifier la cohérence des données
        print("🔍 Vérification de la cohérence des données:")
        print("-" * 40)
        
        for symbol, symbol_opportunities in grouped.items():
            # Vérifier que toutes les opportunités ont le même symbole
            symbols = set(opp['symbol'] for opp in symbol_opportunities)
            if len(symbols) > 1:
                print(f"❌ {symbol}: Symboles incohérents: {symbols}")
            
            # Vérifier que toutes les opportunités ont le même nom d'entreprise
            company_names = set(opp['company_name'] for opp in symbol_opportunities)
            if len(company_names) > 1:
                print(f"❌ {symbol}: Noms d'entreprise incohérents: {company_names}")
            
            # Vérifier les modèles
            models = set(opp['model_name'] for opp in symbol_opportunities)
            print(f"✅ {symbol}: {len(models)} modèle{'s' if len(models) > 1 else ''} unique{'s' if len(models) > 1 else ''}")
        
        print("\n✅ Test terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")

if __name__ == "__main__":
    test_opportunities_grouping()
