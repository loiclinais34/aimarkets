"""
Tâche de screener de démonstration - évite complètement les exceptions
"""
import time
from datetime import datetime, date
from typing import Dict, List, Any
from celery import current_task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.database import ScreenerRun, ScreenerResult, MLModels, TargetParameters, SymbolMetadata
from app.models.schemas import ScreenerRequest


@celery_app.task(bind=True, name="run_demo_screener")
def run_demo_screener(self, screener_request: Dict[str, Any], user_id: str = "demo_user") -> Dict[str, Any]:
    """
    Tâche de démonstration pour exécuter un screener - évite toutes les exceptions
    """
    # Mise à jour du statut initial
    self.update_state(
        state="PROGRESS",
        meta={
            "status": "Démarrage du screener de démonstration...",
            "progress": 0,
            "current_step": "initialization"
        }
    )
    
    # Simulation simple sans base de données
    request = ScreenerRequest(**screener_request)
    
    # Phase 1: Simulation de récupération des symboles
    self.update_state(
        state="PROGRESS",
        meta={
            "status": "Récupération des symboles...",
            "progress": 10,
            "current_step": "fetching_symbols"
        }
    )
    
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]  # Symboles de démonstration
    total_symbols = len(symbols)
    
    # Phase 2: Simulation d'entraînement
    self.update_state(
        state="PROGRESS",
        meta={
            "status": f"Entraînement des modèles (0/{total_symbols})...",
            "progress": 20,
            "current_step": "training_models",
            "total_symbols": total_symbols,
            "trained_models": 0
        }
    )
    
    successful_models = 0
    
    for i, symbol in enumerate(symbols):
        progress = 20 + (i / total_symbols) * 30
        self.update_state(
            state="PROGRESS",
            meta={
                "status": f"Entraînement {symbol} ({i+1}/{total_symbols})...",
                "progress": int(progress),
                "current_step": "training_models",
                "total_symbols": total_symbols,
                "trained_models": successful_models,
                "current_symbol": symbol
            }
        )
        
        # Simulation d'entraînement
        time.sleep(0.5)  # Simulation du temps d'entraînement
        successful_models += 1
    
    # Phase 3: Simulation de prédictions
    self.update_state(
        state="PROGRESS",
        meta={
            "status": f"Calcul des prédictions...",
            "progress": 50,
            "current_step": "making_predictions",
            "total_symbols": total_symbols,
            "successful_models": successful_models
        }
    )
    
    opportunities_found = 0
    predictions_made = 0
    
    # Simulation de prédictions
    import random
    for i, symbol in enumerate(symbols):
        progress = 50 + (i / len(symbols)) * 40
        self.update_state(
            state="PROGRESS",
            meta={
                "status": f"Prédiction {symbol} ({i+1}/{len(symbols)})...",
                "progress": int(progress),
                "current_step": "making_predictions",
                "total_symbols": total_symbols,
                "successful_models": successful_models,
                "predictions_made": predictions_made,
                "current_symbol": symbol
            }
        )
        
        # Simulation de prédiction
        time.sleep(0.3)  # Simulation du temps de prédiction
        
        prediction = random.choice([0.0, 1.0])  # Prédiction aléatoire
        confidence = random.uniform(0.5, 0.95)  # Confiance aléatoire
        
        predictions_made += 1
        
        # Vérification si c'est une opportunité
        if prediction == 1.0 and confidence >= request.risk_tolerance:
            opportunities_found += 1
    
    # Phase 4: Finalisation
    execution_time = 10  # Temps fixe pour la démonstration
    
    # Résultat final
    result = {
        "screener_run_id": 999,  # ID factice
        "total_symbols": total_symbols,
        "successful_models": successful_models,
        "total_opportunities_found": opportunities_found,
        "execution_time_seconds": execution_time,
        "status": "completed",
        "results": [
            {
                "symbol": symbol,
                "company_name": f"{symbol} Corp",
                "prediction": 1.0,
                "confidence": random.uniform(0.7, 0.95),
                "model_id": i + 1,
                "model_name": f"Demo Model {symbol}",
                "target_return": request.target_return_percentage,
                "time_horizon": request.time_horizon_days,
                "rank": i + 1
            }
            for i, symbol in enumerate(symbols[:opportunities_found])
        ]
    }
    
    self.update_state(
        state="SUCCESS",
        meta={
            "status": "Screener de démonstration terminé avec succès!",
            "progress": 100,
            "current_step": "completed",
            "result": result
        }
    )
    
    return result
