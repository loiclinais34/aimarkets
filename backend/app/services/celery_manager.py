"""
Service de gestion de Celery - Vérification et démarrage automatique
"""
import subprocess
import psutil
import os
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class CeleryManager:
    """Gestionnaire pour vérifier et démarrer Celery automatiquement"""
    
    def __init__(self):
        self.backend_dir = Path(__file__).parent.parent.parent  # backend/
        self.celery_script = self.backend_dir / "start_celery.sh"
        
    def is_celery_running(self) -> bool:
        """
        Vérifie si Celery est en cours d'exécution
        
        Returns:
            True si Celery est actif, False sinon
        """
        try:
            # Chercher les processus Celery
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('celery' in arg.lower() for arg in cmdline):
                        # Vérifier que c'est bien notre worker Celery
                        if any('app.core.celery_app' in arg for arg in cmdline):
                            logger.info(f"Celery trouvé en cours d'exécution (PID: {proc.info['pid']})")
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            logger.warning("Aucun processus Celery trouvé")
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de Celery: {e}")
            return False
    
    def is_redis_running(self) -> bool:
        """
        Vérifie si Redis est en cours d'exécution
        
        Returns:
            True si Redis est actif, False sinon
        """
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and 'redis-server' in proc.info['name'].lower():
                        logger.info(f"Redis trouvé en cours d'exécution (PID: {proc.info['pid']})")
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            logger.warning("Redis n'est pas en cours d'exécution")
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de Redis: {e}")
            return False
    
    def start_celery(self) -> Dict[str, Any]:
        """
        Démarre Celery en arrière-plan
        
        Returns:
            Dictionnaire avec le résultat du démarrage
        """
        try:
            # Vérifier que le script existe
            if not self.celery_script.exists():
                return {
                    'success': False,
                    'error': f"Script Celery non trouvé: {self.celery_script}",
                    'pid': None
                }
            
            # Vérifier Redis d'abord
            if not self.is_redis_running():
                return {
                    'success': False,
                    'error': 'Redis n\'est pas en cours d\'exécution. Démarrez Redis avec: brew services start redis',
                    'pid': None
                }
            
            # Démarrer Celery en arrière-plan
            logger.info("Démarrage de Celery en arrière-plan...")
            
            # Utiliser le script de démarrage
            process = subprocess.Popen(
                ['bash', str(self.celery_script)],
                cwd=str(self.backend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid  # Créer un nouveau groupe de processus
            )
            
            # Attendre un peu pour voir si le processus démarre correctement
            import time
            time.sleep(2)
            
            # Vérifier si le processus est toujours actif
            if process.poll() is None:
                logger.info(f"Celery démarré avec succès (PID: {process.pid})")
                return {
                    'success': True,
                    'message': 'Celery démarré avec succès',
                    'pid': process.pid
                }
            else:
                # Le processus s'est arrêté, récupérer l'erreur
                stdout, stderr = process.communicate()
                error_msg = stderr.decode() if stderr else stdout.decode()
                logger.error(f"Erreur lors du démarrage de Celery: {error_msg}")
                return {
                    'success': False,
                    'error': f"Erreur lors du démarrage: {error_msg}",
                    'pid': None
                }
                
        except Exception as e:
            logger.error(f"Exception lors du démarrage de Celery: {e}")
            return {
                'success': False,
                'error': f"Exception: {str(e)}",
                'pid': None
            }
    
    def stop_celery(self) -> Dict[str, Any]:
        """
        Arrête tous les processus Celery
        
        Returns:
            Dictionnaire avec le résultat de l'arrêt
        """
        try:
            stopped_pids = []
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('celery' in arg.lower() for arg in cmdline):
                        if any('app.core.celery_app' in arg for arg in cmdline):
                            pid = proc.info['pid']
                            proc.terminate()
                            stopped_pids.append(pid)
                            logger.info(f"Processus Celery arrêté (PID: {pid})")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if stopped_pids:
                return {
                    'success': True,
                    'message': f'Celery arrêté ({len(stopped_pids)} processus)',
                    'stopped_pids': stopped_pids
                }
            else:
                return {
                    'success': True,
                    'message': 'Aucun processus Celery à arrêter',
                    'stopped_pids': []
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt de Celery: {e}")
            return {
                'success': False,
                'error': f"Erreur lors de l'arrêt: {str(e)}",
                'stopped_pids': []
            }
    
    def get_celery_status(self) -> Dict[str, Any]:
        """
        Récupère le statut complet de Celery
        
        Returns:
            Dictionnaire avec toutes les informations de statut
        """
        celery_running = self.is_celery_running()
        redis_running = self.is_redis_running()
        
        status = {
            'celery_running': celery_running,
            'redis_running': redis_running,
            'ready': celery_running and redis_running,
            'backend_dir': str(self.backend_dir),
            'celery_script': str(self.celery_script),
            'script_exists': self.celery_script.exists()
        }
        
        # Ajouter les PIDs des processus actifs
        if celery_running:
            celery_pids = []
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any('celery' in arg.lower() for arg in cmdline):
                        if any('app.core.celery_app' in arg for arg in cmdline):
                            celery_pids.append(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            status['celery_pids'] = celery_pids
        
        return status
    
    def ensure_celery_running(self) -> Dict[str, Any]:
        """
        S'assure que Celery est en cours d'exécution
        Le démarre automatiquement si nécessaire
        
        Returns:
            Dictionnaire avec le résultat de l'opération
        """
        logger.info("Vérification de l'état de Celery...")
        
        # Vérifier le statut actuel
        status = self.get_celery_status()
        
        if status['ready']:
            logger.info("Celery est déjà en cours d'exécution")
            return {
                'success': True,
                'message': 'Celery est déjà en cours d\'exécution',
                'status': status,
                'action': 'none'
            }
        
        # Celery n'est pas prêt, essayer de le démarrer
        logger.info("Celery n'est pas prêt, tentative de démarrage...")
        
        if not status['redis_running']:
            return {
                'success': False,
                'error': 'Redis n\'est pas en cours d\'exécution. Démarrez Redis avec: brew services start redis',
                'status': status,
                'action': 'failed'
            }
        
        # Démarrer Celery
        start_result = self.start_celery()
        
        if start_result['success']:
            # Vérifier que Celery est maintenant actif
            time.sleep(3)  # Attendre un peu
            final_status = self.get_celery_status()
            
            return {
                'success': True,
                'message': 'Celery démarré avec succès',
                'status': final_status,
                'action': 'started',
                'pid': start_result['pid']
            }
        else:
            return {
                'success': False,
                'error': start_result['error'],
                'status': status,
                'action': 'failed'
            }
