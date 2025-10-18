"""
Gestionnaire de points de reprise pour le recompute
"""
import json
import os
from datetime import datetime

class CheckpointManager:
    def __init__(self, base_dir: str = "/tmp/recompute_checkpoints"):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
    
    def save_checkpoint(self, stage: int, results: dict):
        """
        Sauvegarde l'état d'avancement
        """
        checkpoint_file = os.path.join(
            self.base_dir,
            f"checkpoint_{stage}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(checkpoint_file, "w") as f:
            json.dump(results, f)
    
    def get_latest_checkpoint(self) -> tuple[int, dict]:
        """
        Récupère le dernier point de reprise
        """
        files = os.listdir(self.base_dir)
        if not files:
            return 0, {}
            
        latest = max(files)
        with open(os.path.join(self.base_dir, latest)) as f:
            return int(latest.split("_")[1]), json.load(f)