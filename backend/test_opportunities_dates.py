#!/usr/bin/env python3
"""
Test script pour vérifier les dates des opportunités
"""

import requests
import json
from datetime import datetime
from collections import defaultdict

def test_opportunities_dates():
    """Test des dates des opportunités"""
    
    print("🔍 Test des dates des opportunités")
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
        
        # Analyser les dates
        dates_analysis = {
            'with_date': 0,
            'without_date': 0,
            'unique_dates': set(),
            'date_range': {'min': None, 'max': None}
        }
        
        for opp in opportunities:
            if opp['prediction_date']:
                dates_analysis['with_date'] += 1
                date_obj = datetime.fromisoformat(opp['prediction_date'].replace('Z', '+00:00'))
                dates_analysis['unique_dates'].add(date_obj.date())
                
                if dates_analysis['date_range']['min'] is None or date_obj < dates_analysis['date_range']['min']:
                    dates_analysis['date_range']['min'] = date_obj
                if dates_analysis['date_range']['max'] is None or date_obj > dates_analysis['date_range']['max']:
                    dates_analysis['date_range']['max'] = date_obj
            else:
                dates_analysis['without_date'] += 1
        
        print(f"\n📅 Analyse des dates:")
        print(f"   • Avec date: {dates_analysis['with_date']}")
        print(f"   • Sans date: {dates_analysis['without_date']}")
        print(f"   • Dates uniques: {len(dates_analysis['unique_dates'])}")
        
        if dates_analysis['date_range']['min'] and dates_analysis['date_range']['max']:
            print(f"   • Période: {dates_analysis['date_range']['min'].strftime('%Y-%m-%d')} à {dates_analysis['date_range']['max'].strftime('%Y-%m-%d')}")
        
        # Grouper par symbole et analyser les dates les plus récentes
        print(f"\n📈 Dates les plus récentes par symbole:")
        print("-" * 40)
        
        grouped = defaultdict(list)
        for opp in opportunities:
            grouped[opp['symbol']].append(opp)
        
        for symbol, symbol_opportunities in list(grouped.items())[:10]:  # Top 10
            company_name = symbol_opportunities[0]['company_name']
            
            # Trouver la date la plus récente
            latest_date = None
            for opp in symbol_opportunities:
                if opp['prediction_date']:
                    date_obj = datetime.fromisoformat(opp['prediction_date'].replace('Z', '+00:00'))
                    if latest_date is None or date_obj > latest_date:
                        latest_date = date_obj
            
            if latest_date:
                print(f"🏢 {symbol} - {company_name}")
                print(f"   📅 Dernière opportunité: {latest_date.strftime('%Y-%m-%d %H:%M')}")
                print(f"   📊 {len(symbol_opportunities)} opportunités")
            else:
                print(f"🏢 {symbol} - {company_name}")
                print(f"   📅 Aucune date disponible")
                print(f"   📊 {len(symbol_opportunities)} opportunités")
            print()
        
        # Vérifier la cohérence des dates
        print("🔍 Vérification de la cohérence des dates:")
        print("-" * 40)
        
        inconsistent_symbols = []
        for symbol, symbol_opportunities in grouped.items():
            dates = [opp['prediction_date'] for opp in symbol_opportunities if opp['prediction_date']]
            if len(set(dates)) > 1:
                inconsistent_symbols.append(symbol)
        
        if inconsistent_symbols:
            print(f"⚠️  {len(inconsistent_symbols)} symboles avec des dates incohérentes:")
            for symbol in inconsistent_symbols[:5]:  # Afficher les 5 premiers
                print(f"   • {symbol}")
        else:
            print("✅ Toutes les dates sont cohérentes par symbole")
        
        print("\n✅ Test terminé avec succès!")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")

if __name__ == "__main__":
    test_opportunities_dates()
