#!/usr/bin/env python3
"""
Script de test pour le service de ratios financiers Alpha Vantage
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.financial_ratios_service import FinancialRatiosService
from app.models.database import FinancialRatios
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_financial_ratios_service():
    """Test du service de ratios financiers"""
    
    print("🔍 Test du service de ratios financiers Alpha Vantage...")
    
    # Initialiser le service
    service = FinancialRatiosService()
    
    # Vérifier la configuration
    if not service.api_key:
        print("❌ Clé API Alpha Vantage non configurée")
        print("   Veuillez définir ALPHA_VANTAGE_API_KEY dans vos variables d'environnement")
        return False
    
    print(f"✅ Clé API configurée: {service.api_key[:8]}...")
    
    # Test avec AAPL
    symbol = "AAPL"
    print(f"\n📊 Test avec {symbol}...")
    
    try:
        # Test de récupération des données
        print("   Récupération des données...")
        overview = service.get_company_overview(symbol)
        
        if overview:
            print("   ✅ Données récupérées avec succès")
            print(f"   Nom: {overview.get('name', 'N/A')}")
            print(f"   Secteur: {overview.get('sector', 'N/A')}")
            print(f"   P/E Ratio: {overview.get('pe_ratio', 'N/A')}")
            print(f"   P/B Ratio: {overview.get('price_to_book_ratio', 'N/A')}")
            print(f"   ROE: {overview.get('return_on_equity_ttm', 'N/A')}")
            print(f"   ROA: {overview.get('return_on_assets_ttm', 'N/A')}")
            print(f"   Beta: {overview.get('beta', 'N/A')}")
            print(f"   Market Cap: {overview.get('market_capitalization', 'N/A')}")
        else:
            print("   ❌ Aucune donnée récupérée")
            return False
        
        # Test de sauvegarde en base
        print("\n   Sauvegarde en base de données...")
        db = next(get_db())
        
        try:
            success = service.save_financial_ratios(db, symbol)
            
            if success:
                print("   ✅ Données sauvegardées avec succès")
                
                # Vérifier en base
                record = db.query(FinancialRatios).filter(
                    FinancialRatios.symbol == symbol
                ).first()
                
                if record:
                    print("   ✅ Enregistrement trouvé en base")
                    print(f"   ID: {record.id}")
                    print(f"   Nom: {record.name}")
                    print(f"   P/E: {record.pe_ratio}")
                    print(f"   Dernière mise à jour: {record.last_updated}")
                else:
                    print("   ❌ Aucun enregistrement trouvé en base")
                    return False
            else:
                print("   ❌ Erreur lors de la sauvegarde")
                return False
                
        except Exception as e:
            print(f"   ❌ Erreur lors de la sauvegarde: {e}")
            return False
        finally:
            db.close()
        
        print(f"\n✅ Test réussi pour {symbol}")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def test_multiple_symbols():
    """Test avec plusieurs symboles"""
    
    print("\n🔍 Test avec plusieurs symboles...")
    
    symbols = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
    service = FinancialRatiosService()
    
    if not service.api_key:
        print("❌ Clé API Alpha Vantage non configurée")
        return False
    
    results = []
    
    for symbol in symbols:
        print(f"\n📊 Test avec {symbol}...")
        
        try:
            # Récupérer les données
            overview = service.get_company_overview(symbol)
            
            if overview:
                print(f"   ✅ {symbol}: {overview.get('name', 'N/A')} - P/E: {overview.get('pe_ratio', 'N/A')}")
                results.append(True)
            else:
                print(f"   ❌ {symbol}: Aucune donnée")
                results.append(False)
                
        except Exception as e:
            print(f"   ❌ {symbol}: Erreur - {e}")
            results.append(False)
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n📈 Résultats: {success_count}/{total_count} symboles réussis")
    
    return success_count == total_count

if __name__ == "__main__":
    print("🚀 Démarrage des tests du service de ratios financiers")
    print("=" * 60)
    
    # Test principal
    success = test_financial_ratios_service()
    
    if success:
        # Test avec plusieurs symboles
        test_multiple_symbols()
    
    print("\n" + "=" * 60)
    print("🏁 Tests terminés")
