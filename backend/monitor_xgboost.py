#!/usr/bin/env python3
"""
Script de surveillance pour la génération des opportunités XGBoost
"""

import time
import psutil
import subprocess
from datetime import datetime
import os

def get_process_info(pid):
    """Récupère les informations du processus."""
    try:
        process = psutil.Process(pid)
        return {
            'cpu_percent': process.cpu_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'status': process.status(),
            'create_time': datetime.fromtimestamp(process.create_time())
        }
    except psutil.NoSuchProcess:
        return None

def check_database_progress():
    """Vérifie le progrès dans la base de données."""
    try:
        # Compter les opportunités générées
        result = subprocess.run([
            'psql', '-d', 'aimarkets', '-U', 'loiclinais', '-t', '-c',
            "SELECT COUNT(*) FROM ml_opportunities_xgboost;"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            count = result.stdout.strip()
            return int(count) if count.isdigit() else 0
        return 0
    except:
        return 0

def monitor_xgboost_generation():
    """Surveille le processus de génération XGBoost."""
    print("🔍 Surveillance du processus de génération XGBoost")
    print("=" * 60)
    
    # Trouver le PID du processus principal
    try:
        result = subprocess.run([
            'pgrep', '-f', 'generate_full_xgboost_opportunities.py'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Processus de génération XGBoost non trouvé")
            return
        
        # Prendre le PID le plus récent (le processus principal)
        pids = [int(p.strip()) for p in result.stdout.strip().split('\n') if p.strip()]
        if not pids:
            print("❌ Aucun PID trouvé")
            return
            
        # Prendre le PID avec le plus gros CPU usage (le processus principal)
        main_pid = None
        max_cpu = 0
        for pid in pids:
            try:
                proc = psutil.Process(pid)
                cpu = proc.cpu_percent()
                if cpu > max_cpu:
                    max_cpu = cpu
                    main_pid = pid
            except:
                continue
        
        if not main_pid:
            main_pid = pids[0]  # Fallback au premier PID
            
        pid = main_pid
        print(f"📊 PID du processus principal: {pid} (CPU: {max_cpu:.1f}%)")
        
    except Exception as e:
        print(f"❌ Erreur lors de la recherche du processus: {e}")
        return
    
    start_time = time.time()
    last_count = 0
    
    while True:
        try:
            # Informations du processus
            proc_info = get_process_info(pid)
            if not proc_info:
                print("✅ Processus terminé!")
                break
            
            # Progrès dans la base de données
            current_count = check_database_progress()
            
            # Calcul du temps écoulé
            elapsed = time.time() - start_time
            elapsed_str = f"{int(elapsed//60)}m {int(elapsed%60)}s"
            
            # Calcul du taux de génération
            if elapsed > 0:
                rate = current_count / elapsed
                rate_str = f"{rate:.1f} opp/s"
            else:
                rate_str = "N/A"
            
            # Différence depuis la dernière vérification
            diff = current_count - last_count
            
            # Affichage du statut
            print(f"\r🔄 Temps: {elapsed_str} | "
                  f"CPU: {proc_info['cpu_percent']:.1f}% | "
                  f"RAM: {proc_info['memory_mb']:.0f}MB | "
                  f"Opportunités: {current_count:,} | "
                  f"Taux: {rate_str} | "
                  f"+{diff}", end="", flush=True)
            
            last_count = current_count
            
            # Vérifier si le processus est toujours actif
            if proc_info['status'] == 'zombie':
                print("\n✅ Processus terminé!")
                break
            
            time.sleep(5)  # Vérifier toutes les 5 secondes
            
        except KeyboardInterrupt:
            print("\n\n⏹️ Surveillance interrompue par l'utilisateur")
            break
        except Exception as e:
            print(f"\n❌ Erreur de surveillance: {e}")
            time.sleep(10)
    
    # Statistiques finales
    final_count = check_database_progress()
    total_time = time.time() - start_time
    
    print(f"\n\n📊 STATISTIQUES FINALES")
    print("=" * 40)
    print(f"⏱️  Temps total: {int(total_time//60)}m {int(total_time%60)}s")
    print(f"📈 Opportunités générées: {final_count:,}")
    if total_time > 0:
        print(f"🚀 Taux moyen: {final_count/total_time:.1f} opportunités/seconde")
    
    # Vérifier les logs récents
    print(f"\n📋 Dernières lignes du log:")
    try:
        with open('advanced_xgboost_ml_system.log', 'r') as f:
            lines = f.readlines()
            for line in lines[-5:]:
                print(f"  {line.strip()}")
    except:
        print("  Log non disponible")

if __name__ == "__main__":
    monitor_xgboost_generation()
