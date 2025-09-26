#!/usr/bin/env python3
"""
Script de test pour le screener multi-modèles amélioré
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_db
from app.services.screener_service import ScreenerService
from app.models.schemas import ScreenerRequest

async def test_enhanced_screener():
    """Test du screener multi-modèles"""
    
    # Obtenir une session de base de données
    db = next(get_db())
    screener_service = ScreenerService(db=db)
    
    print("🚀 Test du screener multi-modèles amélioré")
    print("="*50)
    
    # Configuration du screener
    request = ScreenerRequest(
        target_return_percentage=5.0,
        time_horizon_days=30,
        risk_tolerance=0.7
    )
    
    print(f"📊 Configuration:")
    print(f"  - Objectif: {request.target_return_percentage}%")
    print(f"  - Horizon: {request.time_horizon_days} jours")
    print(f"  - Tolérance au risque: {request.risk_tolerance}")
    print()
    
    try:
        # Lancer le screener
        print("🔍 Lancement du screener...")
        result = await screener_service.run_screener(request, "test_user")
        
        print(f"\n✅ Screener terminé!")
        print(f"📈 Résultats:")
        print(f"  - Symboles analysés: {result.total_symbols}")
        print(f"  - Modèles utilisés: {result.successful_models}")
        print(f"  - Opportunités trouvées: {result.opportunities_found}")
        print(f"  - Temps d'exécution: {result.execution_time_seconds}s")
        
        if result.results:
            print(f"\n🎯 Top 5 des opportunités:")
            for i, opportunity in enumerate(result.results[:5]):
                print(f"  {i+1}. {opportunity['symbol']} ({opportunity['company_name']})")
                print(f"     - Algorithme: {opportunity['model_algorithm']}")
                print(f"     - Confiance: {opportunity['confidence']:.1%}")
                print(f"     - Score composite: {opportunity['model_composite_score']:.3f}")
                print(f"     - Accuracy: {opportunity['model_accuracy']:.3f}")
                print()
        
        return result
        
    except Exception as e:
        print(f"❌ Erreur lors du screener: {str(e)}")
        return None

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_enhanced_screener())
