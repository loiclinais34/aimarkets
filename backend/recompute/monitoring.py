"""
Module de monitoring système pour le recompute
"""
import psutil
import logging
from datetime import datetime

class SystemMonitor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def check_resources(self) -> dict:
        """
        Surveille les ressources système
        """
        return {
            "memory_percent": psutil.virtual_memory().percent,
            "cpu_percent": psutil.cpu_percent(),
            "timestamp": datetime.now().isoformat()
        }
    
    def log_if_critical(self, metrics: dict):
        """
        Alerte si seuils critiques dépassés
        """
        if metrics["memory_percent"] > 90:
            self.logger.warning(f"High memory usage: {metrics['memory_percent']}%")
        if metrics["cpu_percent"] > 80:
            self.logger.warning(f"High CPU usage: {metrics['cpu_percent']}%")