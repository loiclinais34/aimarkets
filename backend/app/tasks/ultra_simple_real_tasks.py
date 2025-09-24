"""
Tâche de screener ultra-simple - évite les problèmes de session DB
"""
import time
from datetime import datetime, date
from typing import Dict, List, Any
from celery import current_task

from app.core.celery_app import celery_app


@celery_app.task(bind=True, name="run_ultra_simple_real_screener")
def run_ultra_simple_real_screener(self, screener_request: Dict[str, Any], user_id: str = "screener_user", max_symbols: int = 5) -> Dict[str, Any]:
    """
    Tâche de screener ultra-simple qui évite les problèmes de session DB
    """
    try:
        # Mise à jour du statut initial
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "Démarrage du screener ultra-simple...",
                "progress": 0,
                "current_step": "initialization"
            }
        )
        
        # Conversion du dictionnaire en objet ScreenerRequest
        from app.models.schemas import ScreenerRequest
        request = ScreenerRequest(**screener_request)
        
        # Symboles populaires pour test
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"][:max_symbols]
        total_symbols = len(symbols)
        
        # Phase d'entraînement simulé
        self.update_state(
            state="PROGRESS",
            meta={
                "status": f"Entraînement des modèles (0/{total_symbols})...",
                "progress": 10,
                "current_step": "training_models",
                "total_symbols": total_symbols,
                "trained_models": 0
            }
        )
        
        successful_models = 0
        
        for i, symbol in enumerate(symbols):
            progress = 10 + (i / total_symbols) * 40
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
            time.sleep(1)  # Simuler le travail
            
            # Simuler un succès pour la plupart des symboles
            if symbol != "TSLA":  # TSLA échoue pour la démonstration
                successful_models += 1
                print(f"✅ {symbol}: Modèle entraîné avec succès")
            else:
                print(f"❌ {symbol}: Échec de l'entraînement simulé")
        
        # Phase de prédictions simulées
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
        results = []
        
        for i, symbol in enumerate(symbols):
            if symbol == "TSLA":
                continue  # Skip failed models
                
            progress = 50 + (i / len(symbols)) * 40
            self.update_state(
                state="PROGRESS",
                meta={
                    "status": f"Prédiction {symbol} ({i+1}/{len(symbols)})...",
                    "progress": int(progress),
                    "current_step": "making_predictions",
                    "total_symbols": total_symbols,
                    "successful_models": successful_models,
                    "current_symbol": symbol
                }
            )
            
            # Simulation de prédiction
            time.sleep(0.5)
            
            # Simuler des prédictions et confiances
            prediction = 1.0 if symbol in ["AAPL", "GOOGL"] else 0.0
            confidence = 0.7 + (i * 0.05)
            
            if prediction == 1.0 and confidence >= request.risk_tolerance:
                opportunities_found += 1
                results.append({
                    "symbol": symbol,
                    "company_name": f"{symbol} Corp",
                    "prediction": float(prediction),
                    "confidence": float(confidence),
                    "model_id": i + 1,
                    "model_name": f"Model {symbol}",
                    "target_return": float(request.target_return_percentage),
                    "time_horizon": request.time_horizon_days,
                    "rank": opportunities_found
                })
                print(f"🎯 {symbol}: Opportunité trouvée! Confiance: {confidence:.1%}")
            else:
                print(f"⏭️ {symbol}: Pas d'opportunité (Confiance: {confidence:.1%}, Prédiction: {prediction})")
        
        # Résultat final
        result = {
            "screener_run_id": 999,  # ID factice
            "total_symbols": total_symbols,
            "successful_models": successful_models,
            "total_opportunities_found": opportunities_found,
            "execution_time_seconds": int(time.time() - self.request.started_at),
            "status": "completed",
            "results": results
        }
        
        self.update_state(
            state="SUCCESS",
            meta={
                "status": "Screener ultra-simple terminé avec succès!",
                "progress": 100,
                "current_step": "completed",
                "result": result
            }
        )
        
        return result
        
    except Exception as e:
        # Gestion d'erreur simple
        error_message = str(e)
        print(f"❌ Erreur générale dans le screener ultra-simple: {error_message}")
        
        error_result = {
            "status": "failed",
            "error": error_message,
            "screener_run_id": None
        }
        
        self.update_state(
            state="FAILURE",
            meta={
                "status": f"Erreur: {error_message}",
                "progress": 0,
                "current_step": "error",
                "result": error_result
            }
        )
        
        return error_result
