"""
Script de test pour le service de détection de bulles
"""

import sys
sys.path.append('/Users/loiclinais/Documents/dev/aimarkets/backend')

from datetime import date
from app.core.database import SessionLocal
from app.services.bubble_detection import BubbleDetectionService
import json


def test_bubble_detection():
    """Test du service de détection de bulles sur quelques symboles"""
    
    db = SessionLocal()
    service = BubbleDetectionService(db)
    
    # Symboles à tester (mix de tech values)
    test_symbols = ['NVDA', 'TSLA', 'META', 'AAPL', 'GOOGL']
    
    print("=" * 80)
    print("TEST DE DÉTECTION DE BULLES")
    print("=" * 80)
    print()
    
    results = []
    
    for symbol in test_symbols:
        print(f"\n{'='*80}")
        print(f"Analyse de {symbol}")
        print(f"{'='*80}")
        
        # Analyser le risque de bulle
        bubble_data = service.analyze_bubble_risk(symbol, db=db)
        
        if 'error' not in bubble_data:
            # Afficher les résultats
            print(f"\n📊 SCORE DE BULLE: {bubble_data['bubble_score']:.2f}/100")
            print(f"🎯 NIVEAU: {bubble_data['bubble_level']}")
            print(f"\n📈 Scores par catégorie:")
            print(f"  • Valorisation: {bubble_data['scores']['valuation']:.2f}/100")
            print(f"  • Momentum:     {bubble_data['scores']['momentum']:.2f}/100")
            print(f"  • Statistique:  {bubble_data['scores']['statistical']:.2f}/100")
            print(f"  • Sentiment:    {bubble_data['scores']['sentiment']:.2f}/100")
            
            print(f"\n🔍 Détails Valorisation:")
            val_details = bubble_data['details']['valuation']
            if 'current_price' in val_details:
                print(f"  • Prix actuel: ${val_details['current_price']:.2f}")
                print(f"  • vs Moy 30j:  {val_details.get('price_vs_30d_pct', 0):.2f}%")
                print(f"  • vs Moy 180j: {val_details.get('price_vs_180d_pct', 0):.2f}%")
                print(f"  • vs Moy 365j: {val_details.get('price_vs_365d_pct', 0):.2f}%")
            
            print(f"\n🚀 Détails Momentum:")
            mom_details = bubble_data['details']['momentum']
            if 'growth_30d_pct' in mom_details:
                print(f"  • Croissance 30j:  {mom_details['growth_30d_pct']:.2f}%")
                print(f"  • Croissance 90j:  {mom_details['growth_90d_pct']:.2f}%")
                print(f"  • Croissance 180j: {mom_details['growth_180d_pct']:.2f}%")
                print(f"  • RSI 14j:         {mom_details['rsi_14d']:.2f}")
                print(f"  • vs SMA 50:       {mom_details['distance_from_sma50_pct']:.2f}%")
                print(f"  • vs SMA 200:      {mom_details['distance_from_sma200_pct']:.2f}%")
            
            print(f"\n📊 Détails Statistiques:")
            stat_details = bubble_data['details']['statistical']
            if 'price_zscore' in stat_details:
                print(f"  • Z-score prix:        {stat_details['price_zscore']:.4f}")
                print(f"  • Ratio volatilité:    {stat_details['volatility_ratio']:.4f}")
                print(f"  • Skewness rendements: {stat_details['returns_skewness']:.4f}")
                print(f"  • Kurtosis rendements: {stat_details['returns_kurtosis']:.4f}")
            
            print(f"\n💭 Détails Sentiment:")
            sent_details = bubble_data['details']['sentiment']
            if 'current_sentiment' in sent_details:
                print(f"  • Sentiment actuel:      {sent_details['current_sentiment']:.4f}")
                print(f"  • Sentiment moy 30j:     {sent_details['avg_sentiment_30d']:.4f}")
                print(f"  • Jours extrêmes (>0.8): {sent_details['extreme_sentiment_days']}")
            
            # Sauvegarder dans la base
            saved = service.save_bubble_indicators(bubble_data, db)
            print(f"\n✅ Indicateurs sauvegardés (ID: {saved.id})")
            
            results.append(bubble_data)
        else:
            print(f"\n❌ Erreur: {bubble_data['error']}")
    
    # Résumé
    print(f"\n{'='*80}")
    print("RÉSUMÉ")
    print(f"{'='*80}\n")
    
    # Trier par score de bulle
    valid_results = [r for r in results if 'bubble_score' in r]
    valid_results.sort(key=lambda x: x['bubble_score'], reverse=True)
    
    print(f"{'Symbole':<10} {'Score':<10} {'Niveau':<15} {'Val':<8} {'Mom':<8} {'Stat':<8} {'Sent':<8}")
    print("-" * 80)
    
    for r in valid_results:
        print(f"{r['symbol']:<10} "
              f"{r['bubble_score']:>6.2f}    "
              f"{r['bubble_level']:<15} "
              f"{r['scores']['valuation']:>6.2f}  "
              f"{r['scores']['momentum']:>6.2f}  "
              f"{r['scores']['statistical']:>6.2f}  "
              f"{r['scores']['sentiment']:>6.2f}")
    
    print()
    
    # Alertes
    print("\n🚨 ALERTES:")
    for r in valid_results:
        if r['bubble_level'] in ['PROBABLE', 'CRITICAL']:
            print(f"  ⚠️  {r['symbol']}: {r['bubble_level']} (score: {r['bubble_score']:.2f})")
        elif r['bubble_level'] == 'RISK':
            print(f"  ⚡ {r['symbol']}: {r['bubble_level']} (score: {r['bubble_score']:.2f})")
    
    db.close()
    print("\n✅ Test terminé!\n")


if __name__ == "__main__":
    test_bubble_detection()
