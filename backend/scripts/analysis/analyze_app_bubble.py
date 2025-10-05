"""
Analyse détaillée de APP (AppLovin) - Score RISK 59.97/100
"""

import sys
sys.path.append('/Users/loiclinais/Documents/dev/aimarkets/backend')

from datetime import date
from app.core.database import SessionLocal
from app.services.bubble_detection import BubbleDetectionService
from app.services.financial_ratios_service import FinancialRatiosService
from app.models.bubble_indicators import BubbleIndicators
from app.models.financial_ratios import FinancialRatios
import json


def analyze_app_in_depth():
    """Analyse approfondie de APP"""
    
    db = SessionLocal()
    bubble_service = BubbleDetectionService(db)
    ratios_service = FinancialRatiosService()
    
    symbol = 'APP'
    
    print("=" * 100)
    print(f"ANALYSE DÉTAILLÉE DE {symbol} (AppLovin Corp)")
    print("=" * 100)
    print()
    
    # 1. Récupérer l'analyse de bulle complète
    print("1️⃣  ANALYSE DE BULLE COMPLÈTE")
    print("-" * 100)
    
    bubble_data = bubble_service.analyze_bubble_risk(symbol, db=db)
    
    print(f"\n🎯 SCORE DE BULLE: {bubble_data['bubble_score']:.2f}/100")
    print(f"⚠️  NIVEAU: {bubble_data['bubble_level']}")
    print()
    
    print("📊 Répartition des scores:")
    scores = bubble_data['scores']
    details = bubble_data['details']
    
    print(f"  • Valorisation:  {scores['valuation']:.2f}/100  (poids: 30%)")
    print(f"  • Momentum:      {scores['momentum']:.2f}/100  (poids: 25%)")
    print(f"  • Statistique:   {scores['statistical']:.2f}/100  (poids: 25%)")
    print(f"  • Sentiment:     {scores['sentiment']:.2f}/100  (poids: 20%)")
    print()
    
    # 2. Analyse de valorisation détaillée
    print("\n2️⃣  ANALYSE DE VALORISATION (Score: {:.2f}/100)".format(scores['valuation']))
    print("-" * 100)
    
    val_details = details['valuation']
    
    if 'pe_ratio' in val_details and val_details['pe_ratio']:
        print(f"\n📈 Ratios financiers:")
        print(f"  • P/E Ratio:     {val_details['pe_ratio']:.2f}")
        print(f"  • P/S Ratio:     {val_details.get('ps_ratio', 'N/A')}")
        print(f"  • P/B Ratio:     {val_details.get('pb_ratio', 'N/A')}")
        print(f"  • PEG Ratio:     {val_details.get('peg_ratio', 'N/A')}")
        
        print(f"\n🎯 Comparaison au secteur Technology:")
        if 'pe_vs_sector_pct' in val_details:
            pe_dev = val_details['pe_vs_sector_pct']
            pe_ratio = val_details['pe_ratio']
            sector_avg_pe = 30.0
            print(f"  • P/E vs secteur: {pe_dev:+.2f}% ({pe_ratio:.2f} vs {sector_avg_pe:.2f})")
            if pe_dev > 100:
                print(f"    ⚠️  ALERTE: P/E {pe_dev/100:.1f}x supérieur à la moyenne secteur!")
        
        if 'ps_vs_sector_pct' in val_details:
            ps_dev = val_details['ps_vs_sector_pct']
            ps_ratio = val_details.get('ps_ratio')
            sector_avg_ps = 10.0
            if ps_ratio:
                print(f"  • P/S vs secteur: {ps_dev:+.2f}% ({ps_ratio:.2f} vs {sector_avg_ps:.2f})")
                if ps_dev > 100:
                    print(f"    ⚠️  ALERTE: P/S {ps_dev/100:.1f}x supérieur à la moyenne secteur!")
        
        if 'pb_vs_sector_pct' in val_details:
            pb_dev = val_details['pb_vs_sector_pct']
            pb_ratio = val_details.get('pb_ratio')
            sector_avg_pb = 15.0
            if pb_ratio:
                print(f"  • P/B vs secteur: {pb_dev:+.2f}% ({pb_ratio:.2f} vs {sector_avg_pb:.2f})")
                if pb_dev > 100:
                    print(f"    ⚠️  ALERTE: P/B {pb_dev/100:.1f}x supérieur à la moyenne secteur!")
        
        print(f"\n🏢 Contexte:")
        print(f"  • Secteur:   {val_details.get('sector', 'N/A')}")
        print(f"  • Industrie: {val_details.get('industry', 'N/A')}")
    
    # 3. Analyse de momentum détaillée
    print("\n3️⃣  ANALYSE DE MOMENTUM (Score: {:.2f}/100)".format(scores['momentum']))
    print("-" * 100)
    
    mom_details = details['momentum']
    
    if 'growth_30d_pct' in mom_details:
        print(f"\n📈 Croissance du prix:")
        print(f"  • 30 jours:  {mom_details['growth_30d_pct']:+.2f}%")
        print(f"  • 90 jours:  {mom_details['growth_90d_pct']:+.2f}%")
        print(f"  • 180 jours: {mom_details['growth_180d_pct']:+.2f}%")
        
        if 'price_acceleration' in mom_details:
            accel = mom_details['price_acceleration']
            print(f"  • Accélération: {accel:+.4f}")
            if accel > 10:
                print(f"    ⚠️  ALERTE: Accélération forte ({accel:.2f}), signe de momentum excessif!")
        
        print(f"\n🎯 Position relative:")
        print(f"  • RSI 14j:      {mom_details['rsi_14d']:.2f}")
        if mom_details['rsi_14d'] > 70:
            print(f"    ⚠️  RSI en zone de surachat (>70)")
        if mom_details['rsi_14d'] > 80:
            print(f"    🚨 RSI CRITIQUE en zone extrême (>80)!")
        
        print(f"  • vs SMA 50:    {mom_details['distance_from_sma50_pct']:+.2f}%")
        print(f"  • vs SMA 200:   {mom_details['distance_from_sma200_pct']:+.2f}%")
        
        if mom_details['distance_from_sma50_pct'] > 20 or mom_details['distance_from_sma200_pct'] > 30:
            print(f"    ⚠️  Prix très éloigné des moyennes mobiles, risque de correction!")
    
    # 4. Analyse statistique détaillée
    print("\n4️⃣  ANALYSE STATISTIQUE (Score: {:.2f}/100)".format(scores['statistical']))
    print("-" * 100)
    
    stat_details = details['statistical']
    
    if 'price_zscore' in stat_details:
        print(f"\n📊 Métriques statistiques:")
        zscore = stat_details['price_zscore']
        print(f"  • Z-score prix:        {zscore:.4f}")
        if abs(zscore) > 2:
            print(f"    ⚠️  Prix à {abs(zscore):.1f} écart-types de la moyenne!")
        if abs(zscore) > 3:
            print(f"    🚨 ANOMALIE STATISTIQUE: |Z-score| > 3!")
        
        print(f"  • Ratio volatilité:    {stat_details['volatility_ratio']:.4f}")
        if stat_details['volatility_ratio'] > 1.5:
            print(f"    ⚠️  Volatilité actuelle {stat_details['volatility_ratio']:.1f}x supérieure à l'historique!")
        
        print(f"  • Volatilité récente:  {stat_details['recent_volatility']:.6f}")
        print(f"  • Volatilité historique: {stat_details['historical_volatility']:.6f}")
        
        print(f"\n📉 Distribution des rendements:")
        skew = stat_details['returns_skewness']
        kurt = stat_details['returns_kurtosis']
        
        print(f"  • Skewness:  {skew:.4f}")
        if skew < -0.5:
            print(f"    ⚠️  Asymétrie négative: plus de risque de grosses pertes que de gros gains")
        elif skew > 0.5:
            print(f"    ℹ️  Asymétrie positive: distribution favorise les gains")
        
        print(f"  • Kurtosis:  {kurt:.4f}")
        if kurt > 3:
            print(f"    ⚠️  Queues épaisses (kurtosis > 3): événements extrêmes plus fréquents")
        if kurt > 10:
            print(f"    🚨 TRÈS FORTE KURTOSIS: Risque d'événements extrêmes significatif!")
    
    # 5. Analyse de sentiment détaillée
    print("\n5️⃣  ANALYSE DE SENTIMENT (Score: {:.2f}/100)".format(scores['sentiment']))
    print("-" * 100)
    
    sent_details = details['sentiment']
    
    if 'current_sentiment' in sent_details:
        print(f"\n💭 Sentiment du marché:")
        curr_sent = sent_details['current_sentiment']
        avg_sent = sent_details['avg_sentiment_30d']
        extreme_days = sent_details['extreme_sentiment_days']
        
        print(f"  • Sentiment actuel:     {curr_sent:.4f}")
        print(f"  • Moyenne 30 jours:     {avg_sent:.4f}")
        print(f"  • Jours extrêmes (>0.8): {extreme_days}")
        
        if curr_sent > 0.8:
            print(f"    ⚠️  Sentiment extrêmement positif, risque d'euphorie!")
        if extreme_days > 5:
            print(f"    🚨 Sentiment extrême prolongé ({extreme_days} jours), signe de FOMO potentiel!")
    
    # 6. Récupérer les données de la base
    print("\n6️⃣  DONNÉES PERSISTÉES")
    print("-" * 100)
    
    saved_bubble = db.query(BubbleIndicators).filter(
        BubbleIndicators.symbol == symbol,
        BubbleIndicators.analysis_date == date.today()
    ).first()
    
    if saved_bubble:
        print(f"\n✅ Indicateurs de bulle sauvegardés:")
        print(f"  • ID: {saved_bubble.id}")
        print(f"  • Date: {saved_bubble.analysis_date}")
        print(f"  • Score: {saved_bubble.bubble_score}")
        print(f"  • Niveau: {saved_bubble.bubble_level}")
        
        # Vérifier les champs individuels
        print(f"\n  Champs individuels:")
        print(f"  • P/E Ratio: {saved_bubble.pe_ratio}")
        print(f"  • P/S Ratio: {saved_bubble.ps_ratio}")
        print(f"  • P/B Ratio: {saved_bubble.pb_ratio}")
        print(f"  • RSI 14j: {saved_bubble.rsi_14d}")
        print(f"  • Croissance 30j: {saved_bubble.price_growth_30d}")
        print(f"  • Z-score: {saved_bubble.price_zscore}")
    
    saved_ratios = db.query(FinancialRatios).filter(
        FinancialRatios.symbol == symbol,
        FinancialRatios.retrieved_date == date.today()
    ).first()
    
    if saved_ratios:
        print(f"\n✅ Ratios financiers sauvegardés:")
        print(f"  • Entreprise: {saved_ratios.company_name}")
        print(f"  • Secteur: {saved_ratios.sector}")
        print(f"  • Market Cap: ${saved_ratios.market_cap:,}" if saved_ratios.market_cap else "  • Market Cap: N/A")
        print(f"  • P/E: {saved_ratios.pe_ratio}")
        print(f"  • P/S: {saved_ratios.ps_ratio}")
        print(f"  • P/B: {saved_ratios.pb_ratio}")
        print(f"  • ROE: {saved_ratios.roe}")
        print(f"  • Debt/Equity: {saved_ratios.debt_to_equity}")
    
    # 7. Synthèse et recommandations
    print("\n7️⃣  SYNTHÈSE ET INTERPRÉTATION")
    print("-" * 100)
    
    total_score = bubble_data['bubble_score']
    level = bubble_data['bubble_level']
    
    print(f"\n🎯 Score global: {total_score:.2f}/100 ({level})")
    print()
    
    # Identifier les facteurs de risque principaux
    risk_factors = []
    
    if scores['valuation'] > 60:
        risk_factors.append(f"Valorisation excessive ({scores['valuation']:.2f}/100)")
    if scores['momentum'] > 60:
        risk_factors.append(f"Momentum excessif ({scores['momentum']:.2f}/100)")
    if scores['statistical'] > 60:
        risk_factors.append(f"Anomalies statistiques ({scores['statistical']:.2f}/100)")
    if scores['sentiment'] > 60:
        risk_factors.append(f"Sentiment extrême ({scores['sentiment']:.2f}/100)")
    
    if risk_factors:
        print("🚨 FACTEURS DE RISQUE IDENTIFIÉS:")
        for i, factor in enumerate(risk_factors, 1):
            print(f"  {i}. {factor}")
    else:
        print("ℹ️  Aucun facteur de risque majeur isolé (score distribué)")
    
    print()
    
    # Interprétation du niveau de risque
    print("📋 INTERPRÉTATION DU NIVEAU DE RISQUE:")
    print()
    
    if level == 'RISK':
        print("  ⚠️  NIVEAU RISK (50-70/100):")
        print("     - Signes significatifs de surévaluation")
        print("     - Risque de correction à moyen terme")
        print("     - Surveillance rapprochée recommandée")
        print("     - Éviter les nouvelles positions ou réduire l'exposition")
        print()
    elif level == 'WATCH':
        print("  👀 NIVEAU WATCH (30-50/100):")
        print("     - Valorisation élevée mais pas critique")
        print("     - Surveiller l'évolution du momentum")
        print()
    
    # Recommandations
    print("💡 RECOMMANDATIONS:")
    print()
    
    if total_score > 50:
        print("  1. 🔴 VENTE ou RÉDUCTION DE POSITION:")
        print("     - Risque de correction significatif")
        print("     - Prendre des profits si position existante")
        print()
        print("  2. 📉 NE PAS INITIER DE NOUVELLE POSITION:")
        print("     - Valorisation trop élevée par rapport aux fondamentaux")
        print()
        print("  3. 📊 SURVEILLER CES INDICATEURS:")
        if scores['valuation'] > 60:
            print("     - Évolution des ratios P/E, P/S, P/B")
        if scores['momentum'] > 60:
            print("     - RSI et distance aux moyennes mobiles")
        if mom_details.get('rsi_14d', 0) > 70:
            print(f"     - RSI actuellement à {mom_details['rsi_14d']:.2f} (surachat)")
        print()
        print("  4. ⏰ POINTS DE SORTIE POTENTIELS:")
        if mom_details.get('rsi_14d', 0) > 70:
            print("     - RSI retombe sous 70")
        if mom_details.get('distance_from_sma50_pct', 0) > 10:
            print("     - Prix retourne vers SMA 50")
        print("     - Correction de 10-15% depuis le sommet")
    else:
        print("  ℹ️  Niveau de risque modéré, surveillance continue recommandée")
    
    print()
    print("=" * 100)
    print()
    
    db.close()


if __name__ == "__main__":
    analyze_app_in_depth()
