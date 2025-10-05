"""
Tâches asynchrones pour les screeners
"""
import time
from datetime import datetime, date
from typing import Dict, List, Any
from celery import current_task

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.services.screener_service import ScreenerService
from app.models.database import ScreenerRun, ScreenerResult
from app.models.schemas import ScreenerRequest


@celery_app.task(bind=True, name="run_screener_async")
def run_screener_async(self, screener_request: Dict[str, Any], user_id: str = "demo_user") -> Dict[str, Any]:
    """
    Tâche asynchrone pour exécuter un screener
    """
    try:
        # Mise à jour du statut
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "Démarrage du screener...",
                "progress": 0,
                "current_step": "initialization"
            }
        )
        
        # Création de la session de base de données
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        # Initialisation du service screener
        screener_service = ScreenerService(db)
        
        # Conversion du dictionnaire en objet ScreenerRequest
        request = ScreenerRequest(**screener_request)
        
        # Création de l'enregistrement de run
        screener_run = ScreenerRun(
            screener_config_id=1,  # Pour l'instant, on utilise un ID fixe
            run_date=date.today(),
            total_symbols=0,
            successful_models=0,
            opportunities_found=0,
            execution_time_seconds=0,
            status="running",
            created_at=datetime.now()
        )
        db.add(screener_run)
        db.commit()
        db.refresh(screener_run)
        
        # Récupération des symboles disponibles
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "Récupération des symboles...",
                "progress": 5,
                "current_step": "fetching_symbols",
                "screener_run_id": screener_run.id
            }
        )
        
        symbols = screener_service.get_available_symbols()
        total_symbols = len(symbols)
        
        # Mise à jour du nombre total de symboles
        screener_run.total_symbols = total_symbols
        db.commit()
        
        # Entraînement des modèles
        self.update_state(
            state="PROGRESS",
            meta={
                "status": f"Entraînement des modèles (0/{total_symbols})...",
                "progress": 10,
                "current_step": "training_models",
                "screener_run_id": screener_run.id,
                "total_symbols": total_symbols,
                "trained_models": 0
            }
        )
        
        trained_models = 0
        successful_models = 0
        
        for i, symbol in enumerate(symbols):
            try:
                # Mise à jour de la progression
                progress = 10 + (i / total_symbols) * 40  # 10-50% pour l'entraînement
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "status": f"Entraînement {symbol} ({i+1}/{total_symbols})...",
                        "progress": int(progress),
                        "current_step": "training_models",
                        "screener_run_id": screener_run.id,
                        "total_symbols": total_symbols,
                        "trained_models": trained_models,
                        "current_symbol": symbol
                    }
                )
                
                # Entraînement du modèle pour ce symbole
                try:
                    target_param = screener_service._get_or_create_target_parameter(
                        symbol=symbol,
                        target_return_percentage=request.target_return_percentage,
                        time_horizon_days=request.time_horizon_days,
                        risk_tolerance=request.risk_tolerance,
                        user_id=user_id
                    )
                    
                    # Entraînement du modèle
                    from app.services.ml_service import MLService
                    ml_service = MLService()
                    
                    model_result = ml_service.train_classification_model(
                        symbol=symbol,
                        target_param=target_param,
                        db=db
                    )
                    
                    if model_result and model_result.get("success"):
                        successful_models += 1
                        trained_models += 1
                        print(f"✅ {symbol}: Modèle entraîné avec succès")
                    else:
                        print(f"❌ {symbol}: Échec de l'entraînement - {model_result.get('error', 'Erreur inconnue') if model_result else 'Pas de résultat'}")
                        
                except Exception as e:
                    print(f"❌ {symbol}: Erreur lors de l'entraînement - {str(e)}")
                    continue
                
            except Exception as e:
                print(f"❌ {symbol}: Erreur générale - {str(e)}")
                continue
        
        # Mise à jour du nombre de modèles entraînés avec succès
        screener_run.successful_models = successful_models
        db.commit()
        
        # Prédictions
        self.update_state(
            state="PROGRESS",
            meta={
                "status": f"Calcul des prédictions (0/{successful_models})...",
                "progress": 50,
                "current_step": "making_predictions",
                "screener_run_id": screener_run.id,
                "total_symbols": total_symbols,
                "trained_models": trained_models,
                "successful_models": successful_models,
                "predictions_made": 0
            }
        )
        
        # Récupération des modèles actifs pour les symboles entraînés
        from app.models.database import MLModels
        from app.services.ml_service import MLService
        
        active_models = db.query(MLModels).filter(
            MLModels.is_active == True,
            MLModels.symbol.in_([s for s in symbols])
        ).all()
        
        opportunities_found = 0
        predictions_made = 0
        today = date.today()
        
        # Initialisation du service ML pour les prédictions
        ml_service = MLService()
        
        for i, model in enumerate(active_models):
            try:
                # Mise à jour de la progression
                progress = 50 + (i / len(active_models)) * 40  # 50-90% pour les prédictions
                self.update_state(
                    state="PROGRESS",
                    meta={
                        "status": f"Prédiction {model.symbol} ({i+1}/{len(active_models)})...",
                        "progress": int(progress),
                        "current_step": "making_predictions",
                        "screener_run_id": screener_run.id,
                        "total_symbols": total_symbols,
                        "trained_models": trained_models,
                        "successful_models": successful_models,
                        "predictions_made": predictions_made,
                        "current_symbol": model.symbol
                    }
                )
                
                # Prédiction
                try:
                    prediction_result = ml_service.predict(
                        symbol=model.symbol,
                        model_id=model.id,
                        date=today,
                        db=db
                    )
                    
                    if prediction_result and prediction_result.get("success"):
                        predictions_made += 1
                        prediction = prediction_result["prediction"]
                        confidence = prediction_result["confidence"]
                        
                        # Vérification si c'est une opportunité
                        if prediction == 1.0 and confidence >= request.risk_tolerance:
                            opportunities_found += 1
                            
                            # Enregistrement du résultat
                            screener_result = ScreenerResult(
                                screener_run_id=screener_run.id,
                                symbol=model.symbol,
                                model_id=model.id,
                                prediction=float(prediction),
                                confidence=float(confidence),
                                rank=opportunities_found
                            )
                            db.add(screener_result)
                            print(f"🎯 {model.symbol}: Opportunité trouvée! Confiance: {confidence:.1%}")
                        else:
                            print(f"⏭️ {model.symbol}: Pas d'opportunité (Confiance: {confidence:.1%}, Prédiction: {prediction})")
                    else:
                        print(f"❌ {model.symbol}: Échec de la prédiction - {prediction_result.get('error', 'Erreur inconnue') if prediction_result else 'Pas de résultat'}")
                        
                except Exception as e:
                    print(f"❌ {model.symbol}: Erreur lors de la prédiction - {str(e)}")
                    continue
                
            except Exception as e:
                print(f"❌ {model.symbol}: Erreur générale - {str(e)}")
                continue
        
        # Finalisation
        db.commit()
        
        # Mise à jour finale du run
        screener_run.opportunities_found = opportunities_found
        screener_run.status = "completed"
        screener_run.execution_time_seconds = int(time.time() - self.request.started_at)
        db.commit()
        
        # Résultat final
        result = {
            "screener_run_id": screener_run.id,
            "total_symbols": total_symbols,
            "successful_models": successful_models,
            "total_opportunities_found": opportunities_found,
            "execution_time_seconds": screener_run.execution_time_seconds,
            "status": "completed"
        }
        
        self.update_state(
            state="SUCCESS",
            meta={
                "status": "Screener terminé avec succès!",
                "progress": 100,
                "current_step": "completed",
                "result": result
            }
        )
        
        return result
        
    except Exception as e:
        # En cas d'erreur, marquer le run comme échoué
        try:
            if 'screener_run' in locals():
                screener_run.status = "failed"
                screener_run.error_message = str(e)
                db.commit()
        except:
            pass
        
        self.update_state(
            state="FAILURE",
            meta={
                "status": f"Erreur: {str(e)}",
                "progress": 0,
                "current_step": "error"
            }
        )
        raise e
    
    finally:
        if 'db' in locals():
            db.close()


@celery_app.task(name="get_task_status")
def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Récupérer le statut d'une tâche
    """
    from celery.result import AsyncResult
    
    task = AsyncResult(task_id, app=celery_app)
    
    if task.state == "PENDING":
        return {
            "state": task.state,
            "status": "En attente...",
            "progress": 0
        }
    elif task.state == "PROGRESS":
        return {
            "state": task.state,
            "status": task.info.get("status", "En cours..."),
            "progress": task.info.get("progress", 0),
            "meta": task.info
        }
    elif task.state == "SUCCESS":
        return {
            "state": task.state,
            "status": "Terminé avec succès!",
            "progress": 100,
            "result": task.result
        }
    else:  # FAILURE
        return {
            "state": task.state,
            "status": f"Erreur: {str(task.info)}",
            "progress": 0
        }
