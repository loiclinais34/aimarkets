#!/usr/bin/env python3
"""
Test direct de la pipeline d'analyse avancée
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.tasks.advanced_analysis_pipeline_tasks import advanced_analysis_pipeline
import asyncio

async def test_pipeline():
    """Test direct de la pipeline"""
    try:
        print("🚀 Démarrage du test de la pipeline d'analyse avancée...")
        
        # Test avec quelques symboles
        symbols = ["AAPL", "MSFT", "GOOGL"]
        force_update = False
        
        print(f"📊 Analyse de {len(symbols)} symboles: {symbols}")
        
        # Exécuter la pipeline directement
        result = await advanced_analysis_pipeline(force_update=force_update, symbols=symbols)
        
        print("✅ Pipeline exécutée avec succès!")
        print(f"📈 Résultats:")
        print(f"   - Statut: {result.get('status', 'unknown')}")
        
        if result.get('status') == 'completed':
            pipeline_exec = result.get('pipeline_execution', {})
            opportunities = result.get('opportunities_analysis', {})
            
            print(f"   - Symboles traités: {pipeline_exec.get('symbols_processed', 0)}")
            print(f"   - Opportunités créées: {opportunities.get('opportunities_created', 0)}")
            print(f"   - Opportunités mises à jour: {opportunities.get('opportunities_updated', 0)}")
            
            if opportunities.get('errors'):
                print(f"   - Erreurs: {len(opportunities['errors'])}")
                for error in opportunities['errors'][:3]:  # Afficher les 3 premières erreurs
                    print(f"     • {error}")
        else:
            print(f"   - Erreur: {result.get('error', 'Erreur inconnue')}")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_pipeline())
