#!/usr/bin/env python3
"""
Test de débogage pour l'endpoint GARCH.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.polygon_service import PolygonService
from app.services.sentiment_analysis import GARCHModels
import pandas as pd
from datetime import datetime, timedelta

def test_garch_debug():
    """Test de débogage pour GARCH."""
    try:
        print("🔍 Test de débogage GARCH...")
        
        symbol = "AAPL"
        
        # Récupérer les données
        polygon_service = PolygonService()
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        print(f"📅 Période: {start_date.strftime('%Y-%m-%d')} à {end_date.strftime('%Y-%m-%d')}")
        
        historical_data = polygon_service.get_historical_data(
            symbol=symbol,
            from_date=start_date.strftime('%Y-%m-%d'),
            to_date=end_date.strftime('%Y-%m-%d')
        )
        
        print(f"📊 Données récupérées: {len(historical_data) if historical_data else 0}")
        
        if not historical_data:
            print("❌ Aucune donnée historique trouvée")
            return False
        
        # Convertir en DataFrame
        df = pd.DataFrame(historical_data)
        print(f"📋 DataFrame: {len(df)} lignes, {len(df.columns)} colonnes")
        print(f"   Colonnes: {list(df.columns)}")
        
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        print(f"📈 Prix de clôture: {len(df['close'])} valeurs")
        print(f"   Première valeur: {df['close'].iloc[0]}")
        print(f"   Dernière valeur: {df['close'].iloc[-1]}")
        
        # Calculer les rendements
        returns = GARCHModels.calculate_returns(df['close'])
        print(f"📊 Rendements calculés: {len(returns)} valeurs")
        
        if len(returns) > 0:
            print(f"   Premier rendement: {returns.iloc[0]}")
            print(f"   Dernier rendement: {returns.iloc[-1]}")
            print(f"   Moyenne: {returns.mean()}")
            print(f"   Écart-type: {returns.std()}")
        else:
            print("❌ Aucun rendement calculé")
            return False
        
        # Test de l'analyse GARCH
        if len(returns) >= 100:
            print("🔍 Test de l'analyse GARCH...")
            garch_analysis = GARCHModels.comprehensive_analysis(returns)
            print(f"✅ Analyse GARCH réussie: {len(garch_analysis)} éléments")
        else:
            print(f"⚠️ Pas assez de données pour GARCH: {len(returns)} < 100")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_garch_debug()
    sys.exit(0 if success else 1)
