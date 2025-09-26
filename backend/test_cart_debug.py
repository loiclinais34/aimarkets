#!/usr/bin/env python3
"""
Script de debug pour tester le panier d'opportunités
"""

import requests
import json

def test_cart_debug():
    """Test du panier d'opportunités"""
    
    print("🔍 Test du panier d'opportunités")
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
        
        # Prendre les 3 premières opportunités pour le test
        test_opportunities = opportunities[:3]
        
        print(f"\n🧪 Test avec {len(test_opportunities)} opportunités:")
        print("-" * 40)
        
        for i, opp in enumerate(test_opportunities):
            print(f"Opportunité {i+1}:")
            print(f"  • Symbole: {opp['symbol']}")
            print(f"  • Modèle: {opp['model_name']}")
            print(f"  • Confiance: {opp['confidence']:.3f}")
            print(f"  • Rendement: {opp['target_return']}%")
            print(f"  • Horizon: {opp['time_horizon']} jours")
            print()
        
        print("📝 Instructions pour tester le panier:")
        print("1. Ouvrez http://localhost:3000/dashboard")
        print("2. Cliquez sur une carte d'entreprise")
        print("3. Cliquez sur le bouton panier (🛒) à côté d'une opportunité")
        print("4. Vérifiez que l'icône panier en haut à droite se met à jour")
        print("5. Cliquez sur l'icône panier pour voir le contenu")
        print("6. Allez sur http://localhost:3000/analysis pour voir l'analyse")
        
        print("\n🔧 Debug localStorage:")
        print("Ouvrez les DevTools (F12) et exécutez:")
        print("localStorage.getItem('opportunity-cart')")
        print("Cela devrait afficher le contenu du panier en JSON")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")

if __name__ == "__main__":
    test_cart_debug()
