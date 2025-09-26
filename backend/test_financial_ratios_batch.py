#!/usr/bin/env python3
"""
Script de test pour la récupération des ratios financiers par lots
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.tasks.financial_ratios_tasks import update_financial_ratios_task
from app.core.database import get_db
from app.models.database import SymbolMetadata, FinancialRatios
import logging
import time

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_financial_ratios_batch():
    """Test de la récupération des ratios financiers par lots"""
    
    print("🔍 Test de la récupération des ratios financiers par lots...")
    
    # Récupérer quelques symboles pour le test
    db = next(get_db())
    try:
        # Récupérer les 20 premiers symboles (hors AAPL)
        symbol_records = db.query(SymbolMetadata).limit(20).all()
        test_symbols = [record.symbol for record in symbol_records if record.symbol != 'AAPL']
        
        print(f"Symboles de test: {test_symbols}")
        print(f"Nombre de symboles: {len(test_symbols)}")
        
    finally:
        db.close()
    
    if not test_symbols:
        print("❌ Aucun symbole trouvé pour le test")
        return False
    
    # Lancer la tâche avec des paramètres de test
    print("\n🚀 Lancement de la tâche Celery...")
    print("Paramètres:")
    print(f"  - Symboles: {len(test_symbols)}")
    print(f"  - Taille des lots: 25 (limite Alpha Vantage)")
    print(f"  - Délai entre lots: 0 minute (quota quotidien)")
    
    # Lancer la tâche
    result = update_financial_ratios_task.delay(
        symbols=test_symbols,
        batch_size=25,  # Limite Alpha Vantage gratuite
        delay_minutes=0  # Pas de délai pour 25 symboles/jour
    )
    
    print(f"Tâche lancée avec ID: {result.id}")
    
    # Suivre le progrès
    print("\n📊 Suivi du progrès...")
    while not result.ready():
        try:
            info = result.info
            if info:
                print(f"Progrès: {info.get('progress', 0)}% - {info.get('status', 'N/A')}")
                if 'current_symbol' in info:
                    print(f"  Symbole actuel: {info['current_symbol']}")
                if 'successful_updates' in info:
                    print(f"  Réussis: {info['successful_updates']}")
                if 'failed_updates' in info:
                    print(f"  Échoués: {info['failed_updates']}")
                if 'waiting_seconds' in info:
                    print(f"  Attente: {info['waiting_seconds']} secondes")
        except:
            pass
        
        time.sleep(10)  # Vérifier toutes les 10 secondes
    
    # Résultat final
    if result.successful():
        task_result = result.result
        print(f"\n✅ Tâche terminée avec succès!")
        print(f"Total symboles: {task_result.get('total_symbols', 0)}")
        print(f"Réussis: {task_result.get('successful_updates', 0)}")
        print(f"Échoués: {task_result.get('failed_updates', 0)}")
        
        # Afficher les résultats détaillés
        results = task_result.get('results', [])
        print(f"\n📋 Résultats détaillés:")
        for result_item in results:
            status_icon = "✅" if result_item['status'] == 'success' else "❌"
            print(f"  {status_icon} {result_item['symbol']}: {result_item['message']}")
        
        return True
    else:
        print(f"\n❌ Tâche échouée: {result.result}")
        return False

def test_financial_ratios_incremental():
    """Test de la mise à jour incrémentale"""
    
    print("\n🔍 Test de la mise à jour incrémentale...")
    
    from app.tasks.financial_ratios_tasks import update_financial_ratios_incremental_task
    
    # Lancer la tâche incrémentale
    result = update_financial_ratios_incremental_task.delay(days_since_update=1)
    
    print(f"Tâche incrémentale lancée avec ID: {result.id}")
    
    # Attendre un peu
    time.sleep(5)
    
    if result.ready():
        if result.successful():
            task_result = result.result
            print(f"✅ Tâche incrémentale terminée!")
            print(f"Résultat: {task_result}")
        else:
            print(f"❌ Tâche incrémentale échouée: {result.result}")
    else:
        print("⏳ Tâche incrémentale en cours...")

def check_existing_ratios():
    """Vérifier les ratios financiers existants"""
    
    print("\n🔍 Vérification des ratios financiers existants...")
    
    db = next(get_db())
    try:
        # Compter les enregistrements
        total_ratios = db.query(FinancialRatios).count()
        print(f"Total des ratios financiers en base: {total_ratios}")
        
        if total_ratios > 0:
            # Afficher quelques exemples
            recent_ratios = db.query(FinancialRatios).order_by(
                FinancialRatios.last_updated.desc()
            ).limit(5).all()
            
            print(f"\n📊 5 derniers ratios financiers:")
            for ratio in recent_ratios:
                print(f"  {ratio.symbol}: {ratio.name} - P/E: {ratio.pe_ratio} - Mis à jour: {ratio.last_updated}")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Démarrage des tests de récupération des ratios financiers par lots")
    print("=" * 80)
    
    # Vérifier l'état actuel
    check_existing_ratios()
    
    # Test principal
    success = test_financial_ratios_batch()
    
    if success:
        # Test incrémental
        test_financial_ratios_incremental()
    
    print("\n" + "=" * 80)
    print("🏁 Tests terminés")
