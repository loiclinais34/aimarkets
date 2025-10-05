"""
Script de test pour le service de ratios financiers
"""

import sys
sys.path.append('/Users/loiclinais/Documents/dev/aimarkets/backend')

from app.services.financial_ratios_service import FinancialRatiosService
import json


def test_financial_ratios():
    """Test du service de ratios financiers"""
    
    service = FinancialRatiosService()
    
    # Symboles à tester
    test_symbols = ['AAPL', 'NVDA', 'TSLA', 'META', 'GOOGL']
    
    print("=" * 80)
    print("TEST DU SERVICE DE RATIOS FINANCIERS")
    print("=" * 80)
    print()
    
    # Test 1: Récupération des ratios pour un symbole
    print("Test 1: Récupération des ratios pour AAPL")
    print("-" * 80)
    
    ratios = service.get_financial_ratios('AAPL')
    
    if 'error' not in ratios:
        print(f"✅ Entreprise: {ratios['company_name']}")
        print(f"✅ Secteur: {ratios['sector']}")
        print(f"✅ Industrie: {ratios['industry']}")
        print()
        print("Ratios de valorisation:")
        print(f"  P/E (Trailing): {ratios['pe_ratio']}")
        print(f"  P/E (Forward):  {ratios['forward_pe']}")
        print(f"  P/S:            {ratios['ps_ratio']}")
        print(f"  P/B:            {ratios['pb_ratio']}")
        print(f"  PEG:            {ratios['peg_ratio']}")
        print()
        print("Ratios de rentabilité:")
        print(f"  Profit Margin:  {ratios['profit_margin']}")
        print(f"  ROE:            {ratios['roe']}")
        print(f"  ROA:            {ratios['roa']}")
        print()
        print("Ratios de liquidité:")
        print(f"  Current Ratio:  {ratios['current_ratio']}")
        print(f"  Quick Ratio:    {ratios['quick_ratio']}")
        print(f"  Debt/Equity:    {ratios['debt_to_equity']}")
    else:
        print(f"❌ Erreur: {ratios['error']}")
    
    print()
    print("=" * 80)
    
    # Test 2: Batch récupération
    print("\nTest 2: Récupération en batch")
    print("-" * 80)
    
    batch_results = service.batch_get_ratios(test_symbols)
    
    print(f"\n{'Symbole':<10} {'P/E':<10} {'P/S':<10} {'P/B':<10} {'Secteur':<20}")
    print("-" * 70)
    
    for symbol, ratios in batch_results.items():
        if 'error' not in ratios:
            print(f"{symbol:<10} "
                  f"{ratios['pe_ratio'] or 'N/A':<10.2f} " if ratios['pe_ratio'] else f"{symbol:<10} {'N/A':<10} ",
                  end="")
            print(f"{ratios['ps_ratio'] or 'N/A':<10.2f} " if ratios['ps_ratio'] else f"{'N/A':<10} ",
                  end="")
            print(f"{ratios['pb_ratio'] or 'N/A':<10.2f} " if ratios['pb_ratio'] else f"{'N/A':<10} ",
                  end="")
            print(f"{ratios['sector']:<20}")
        else:
            print(f"{symbol:<10} ❌ Erreur: {ratios['error']}")
    
    print()
    print("✅ Test terminé!\n")


if __name__ == "__main__":
    test_financial_ratios()
