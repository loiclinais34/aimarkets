#!/usr/bin/env python3
"""
Script de test pour la recherche d'opportunités avec des paramètres permissifs
"""

import os
import sys
import time
import requests
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_opportunity_search_permissive():
    """Test de la recherche d'opportunités avec des paramètres permissifs"""
    
    print("🔍 Test de la recherche d'opportunités avec paramètres permissifs")
    print("=" * 80)
    
    # Paramètres permissifs pour trouver des opportunités
    search_params = {
        "target_return_percentage": 1.0,  # 1% au lieu de 5%
        "time_horizon_days": 30,          # 30 jours au lieu de 10
        "risk_tolerance": 0.5,
        "confidence_threshold": 0.5       # 50% au lieu de 70%
    }
    
    print(f"📊 Paramètres de recherche permissifs:")
    print(f"  - Rendement attendu: {search_params['target_return_percentage']}%")
    print(f"  - Horizon temporel: {search_params['time_horizon_days']} jours")
    print(f"  - Tolérance au risque: {search_params['risk_tolerance']}")
    print(f"  - Seuil de confiance: {search_params['confidence_threshold']}")
    
    # Lancer la recherche d'opportunités
    print(f"\n🚀 Lancement de la recherche d'opportunités...")
    
    try:
        response = requests.post(
            'http://localhost:8000/api/v1/screener/search-opportunities',
            json=search_params,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            
            if task_id:
                print(f"✅ Recherche lancée avec succès")
                print(f"📋 Task ID: {task_id}")
                
                # Monitoring de la progression
                print(f"\n📊 Monitoring de la progression...")
                monitor_task_progress(task_id)
            else:
                print(f"❌ Aucun task_id retourné")
                print(f"📋 Réponse: {result}")
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            print(f"📋 Réponse: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossible de se connecter au backend")
        print(f"💡 Assurez-vous que le backend est démarré sur le port 8000")
    except Exception as e:
        print(f"❌ Erreur lors du lancement: {str(e)}")

def monitor_task_progress(task_id: str):
    """Monitorer la progression d'une tâche"""
    
    print(f"🔄 Surveillance de la tâche {task_id}")
    print("-" * 50)
    
    start_time = time.time()
    last_progress = -1
    
    while True:
        try:
            response = requests.get(f'http://localhost:8000/api/v1/screener/task-status/{task_id}')
            
            if response.status_code == 200:
                status = response.json()
                state = status.get('state', 'UNKNOWN')
                progress = status.get('progress', 0)
                current_step = status.get('current_step', 'unknown')
                current_symbol = status.get('current_symbol', '')
                successful_updates = status.get('successful_updates', 0)
                
                # Afficher la progression seulement si elle a changé
                if progress != last_progress:
                    elapsed = time.time() - start_time
                    print(f"⏱️  {elapsed:.1f}s | {progress}% | {state} | {current_step}")
                    
                    if current_symbol:
                        print(f"   📊 Traitement: {current_symbol}")
                    if successful_updates > 0:
                        print(f"   ✅ Modèles entraînés: {successful_updates}")
                    
                    # Afficher les étapes
                    steps = status.get('steps', [])
                    if steps:
                        print(f"   📋 Étapes:")
                        for step in steps:
                            status_icon = "✅" if step['status'] == 'completed' else "🔄" if step['status'] == 'current' else "⏳"
                            print(f"      {status_icon} {step['name']}")
                    
                    print()
                    last_progress = progress
                
                # Vérifier si la tâche est terminée
                if state == 'SUCCESS':
                    print(f"🎉 Tâche terminée avec succès!")
                    result = status.get('result', {})
                    opportunities_found = result.get('total_opportunities_found', 0)
                    execution_time = result.get('execution_time_seconds', 0)
                    
                    print(f"📊 Résultats:")
                    print(f"   - Opportunités trouvées: {opportunities_found}")
                    print(f"   - Temps d'exécution: {execution_time}s")
                    print(f"   - Symboles traités: {result.get('total_symbols', 0)}")
                    print(f"   - Modèles entraînés: {result.get('successful_models', 0)}")
                    
                    # Afficher les opportunités trouvées
                    results = result.get('results', [])
                    if results:
                        print(f"\n🎯 Opportunités détectées:")
                        for i, opp in enumerate(results[:10]):  # Afficher les 10 premières
                            print(f"   {i+1}. {opp['symbol']} - {opp['company_name']}")
                            print(f"      Prédiction: {opp['prediction']:.3f} | Confiance: {opp['confidence']:.1%}")
                            print(f"      Modèle: {opp['model_name']} | Cible: {opp['target_return']}% en {opp['time_horizon']}j")
                    
                    break
                elif state == 'FAILURE':
                    print(f"❌ Tâche échouée!")
                    error = status.get('error', 'Erreur inconnue')
                    print(f"📋 Erreur: {error}")
                    break
                
            else:
                print(f"❌ Erreur HTTP {response.status_code} lors du monitoring")
                print(f"📋 Réponse: {response.text}")
                break
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Impossible de se connecter au backend")
            break
        except Exception as e:
            print(f"❌ Erreur lors du monitoring: {str(e)}")
            break
        
        # Attendre avant la prochaine vérification
        time.sleep(2)
    
    total_time = time.time() - start_time
    print(f"\n⏱️  Temps total de monitoring: {total_time:.1f}s")

def test_opportunities_display():
    """Test de l'affichage des opportunités"""
    
    print(f"\n🎯 Test de l'affichage des opportunités")
    print("-" * 50)
    
    try:
        response = requests.get('http://localhost:8000/api/v1/screener/latest-opportunities')
        
        if response.status_code == 200:
            opportunities = response.json()
            
            if opportunities:
                print(f"✅ {len(opportunities)} opportunités trouvées")
                
                for i, opp in enumerate(opportunities[:5]):  # Afficher les 5 premières
                    print(f"\n{i+1}. {opp['symbol']} - {opp['company_name']}")
                    print(f"   Prédiction: {opp['prediction']:.3f}")
                    print(f"   Confiance: {opp['confidence']:.1%}")
                    print(f"   Modèle: {opp['model_name']}")
                    print(f"   Cible: {opp['target_return']}% en {opp['time_horizon']} jours")
                    print(f"   Rang: #{opp['rank']}")
            else:
                print(f"📭 Aucune opportunité trouvée")
        else:
            print(f"❌ Erreur HTTP {response.status_code}")
            print(f"📋 Réponse: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Impossible de se connecter au backend")
    except Exception as e:
        print(f"❌ Erreur lors de la récupération: {str(e)}")

if __name__ == "__main__":
    print("🚀 Démarrage des tests de recherche d'opportunités avec paramètres permissifs")
    
    # Test de l'affichage des opportunités existantes
    test_opportunities_display()
    
    # Test du monitoring de la recherche
    test_opportunity_search_permissive()
    
    print("\n🏁 Tests terminés")
