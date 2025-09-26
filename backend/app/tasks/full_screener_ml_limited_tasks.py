"""
Tâche de screener ML limité - version de test avec un nombre limité de symboles
"""
import time
from datetime import datetime, date
from typing import Dict, List, Any
from decimal import Decimal
from celery import current_task
from sqlalchemy.orm import Session

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.database import ScreenerRun, ScreenerResult, MLModels, TargetParameters, SymbolMetadata
from app.models.schemas import ScreenerRequest
from app.services.ml_service import MLService


def get_fresh_db_session():
    """Créer une nouvelle session de base de données fraîche"""
    return SessionLocal()


@celery_app.task(bind=True, name="run_full_screener_ml_limited")
def run_full_screener_ml_limited(self, screener_request: Dict[str, Any], user_id: str = "screener_user", max_symbols: int = 5) -> Dict[str, Any]:
    """
    Tâche de screener ML limité pour les tests
    """
    screener_run_id = None
    start_time = time.time()
    
    try:
        # Mise à jour du statut initial
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "Démarrage du screener ML limité...",
                "progress": 0,
                "current_step": "initialization",
                "steps": [
                    {"step": 1, "name": "Entraînement des modèles", "status": "pending"},
                    {"step": 2, "name": "Calcul des prédictions", "status": "pending"},
                    {"step": 3, "name": "Filtrage des opportunités", "status": "pending"},
                    {"step": 4, "name": "Finalisation", "status": "pending"}
                ]
            }
        )
        
        # Conversion du dictionnaire en objet ScreenerRequest
        request = ScreenerRequest(**screener_request)
        
        # Création de l'enregistrement de run avec une session dédiée
        db = get_fresh_db_session()
        try:
            screener_run = ScreenerRun(
                screener_config_id=1,
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
            screener_run_id = screener_run.id
        finally:
            db.close()
        
        # Récupération des symboles disponibles (limités)
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "Récupération des symboles...",
                "progress": 5,
                "current_step": "fetching_symbols",
                "screener_run_id": screener_run_id
            }
        )
        
        db = get_fresh_db_session()
        try:
            # Récupérer les premiers symboles actifs (limités)
            symbols_query = db.query(SymbolMetadata.symbol).filter(
                SymbolMetadata.is_active == True
            ).order_by(SymbolMetadata.symbol.asc()).limit(max_symbols)
            
            symbols = [row[0] for row in symbols_query.all()]
            total_symbols = len(symbols)
            
            # Mise à jour du nombre total de symboles
            screener_run = db.query(ScreenerRun).filter(ScreenerRun.id == screener_run_id).first()
            if screener_run:
                screener_run.total_symbols = total_symbols
                db.commit()
        finally:
            db.close()
        
        print(f"📊 {total_symbols} symboles à analyser avec vrais modèles ML (limité à {max_symbols})")
        
        # Initialisation du service ML
        ml_service = MLService()
        
        # Phase d'entraînement des modèles ML réels
        self.update_state(
            state="PROGRESS",
            meta={
                "status": f"Entraînement des modèles ML (0/{total_symbols})...",
                "progress": 10,
                "current_step": "training_models",
                "screener_run_id": screener_run_id,
                "total_symbols": total_symbols,
                "trained_models": 0,
                "steps": [
                    {"step": 1, "name": "Entraînement des modèles", "status": "current"},
                    {"step": 2, "name": "Calcul des prédictions", "status": "pending"},
                    {"step": 3, "name": "Filtrage des opportunités", "status": "pending"},
                    {"step": 4, "name": "Finalisation", "status": "pending"}
                ]
            }
        )
        
        successful_models = 0
        
        for i, symbol in enumerate(symbols):
            progress = 10 + (i / total_symbols) * 40
            self.update_state(
                state="PROGRESS",
                meta={
                    "status": f"Entraînement ML {symbol} ({i+1}/{total_symbols})...",
                    "progress": int(progress),
                    "current_step": "training_models",
                    "screener_run_id": screener_run_id,
                    "total_symbols": total_symbols,
                    "trained_models": successful_models,
                    "current_symbol": symbol,
                    "successful_updates": successful_models,
                    "steps": [
                        {"step": 1, "name": "Entraînement des modèles", "status": "current"},
                        {"step": 2, "name": "Calcul des prédictions", "status": "pending"},
                        {"step": 3, "name": "Filtrage des opportunités", "status": "pending"},
                        {"step": 4, "name": "Finalisation", "status": "pending"}
                    ]
                }
            )
            
            try:
                # Créer une nouvelle session pour chaque symbole
                db = get_fresh_db_session()
                try:
                    # Créer ou récupérer les paramètres cibles
                    existing_param = db.query(TargetParameters).filter(
                        TargetParameters.user_id == user_id,
                        TargetParameters.parameter_name == f"target_{symbol}_{request.target_return_percentage}%_{request.time_horizon_days}d"
                    ).first()
                    
                    if existing_param:
                        target_param = existing_param
                    else:
                        # Créer de nouveaux paramètres cibles
                        risk_tolerance_map = {
                            0.1: "low", 0.2: "low", 0.3: "low",
                            0.4: "medium", 0.5: "medium", 0.6: "medium",
                            0.7: "high", 0.8: "high", 0.9: "high", 1.0: "high"
                        }
                        risk_tolerance_str = risk_tolerance_map.get(request.risk_tolerance, "medium")
                        
                        target_param = TargetParameters(
                            user_id=user_id,
                            parameter_name=f"target_{symbol}_{request.target_return_percentage}%_{request.time_horizon_days}d",
                            target_return_percentage=Decimal(str(request.target_return_percentage)),
                            time_horizon_days=request.time_horizon_days,
                            risk_tolerance=risk_tolerance_str,
                            min_confidence_threshold=Decimal(str(request.risk_tolerance)),
                            max_drawdown_percentage=Decimal("5.0"),
                            is_active=True
                        )
                        db.add(target_param)
                        db.commit()
                        db.refresh(target_param)
                    
                    # Entraîner le VRAI modèle de classification ML
                    model_result = ml_service.train_classification_model(
                        symbol=symbol,
                        target_param=target_param,
                        db=db
                    )
                    
                    if model_result and "error" not in model_result:
                        successful_models += 1
                        print(f"✅ {symbol}: Modèle ML entraîné avec succès")
                    else:
                        print(f"❌ {symbol}: Échec de l'entraînement ML - {model_result.get('error', 'Erreur inconnue') if model_result else 'Pas de résultat'}")
                        
                finally:
                    db.close()
                    
            except Exception as e:
                print(f"❌ {symbol}: Erreur lors de l'entraînement ML - {str(e)}")
                continue
        
        # Mise à jour du nombre de modèles entraînés avec succès
        db = get_fresh_db_session()
        try:
            screener_run = db.query(ScreenerRun).filter(ScreenerRun.id == screener_run_id).first()
            if screener_run:
                screener_run.successful_models = successful_models
                db.commit()
        finally:
            db.close()
        
        print(f"🎯 {successful_models}/{total_symbols} modèles ML entraînés avec succès")
        
        # Phase de prédictions avec vrais modèles ML
        self.update_state(
            state="PROGRESS",
            meta={
                "status": f"Calcul des prédictions ML...",
                "progress": 50,
                "current_step": "making_predictions",
                "screener_run_id": screener_run_id,
                "total_symbols": total_symbols,
                "successful_models": successful_models,
                "steps": [
                    {"step": 1, "name": "Entraînement des modèles", "status": "completed"},
                    {"step": 2, "name": "Calcul des prédictions", "status": "current"},
                    {"step": 3, "name": "Filtrage des opportunités", "status": "pending"},
                    {"step": 4, "name": "Finalisation", "status": "pending"}
                ]
            }
        )
        
        # Récupération des modèles actifs pour les symboles entraînés
        # Utiliser les modèles qui viennent d'être entraînés avec les paramètres spécifiques
        db = get_fresh_db_session()
        try:
            # Récupérer les modèles avec les paramètres spécifiques de cette recherche
            active_models = db.query(MLModels).filter(
                MLModels.is_active == True,
                MLModels.symbol.in_(symbols)
            ).all()
            
            # Filtrer par les paramètres de la recherche
            filtered_models = []
            for model in active_models:
                params = model.model_parameters
                if params and isinstance(params, dict):
                    model_target_return = params.get('target_return_percentage')
                    model_time_horizon = params.get('time_horizon_days')
                    
                    # Vérifier si les paramètres correspondent
                    if (str(model_target_return) == str(request.target_return_percentage) and 
                        model_time_horizon == request.time_horizon_days):
                        filtered_models.append(model)
            
            active_models = filtered_models
            print(f"🎯 {len(active_models)} modèles trouvés avec les paramètres {request.target_return_percentage}% sur {request.time_horizon_days} jours")
            
        finally:
            db.close()
        
        opportunities_found = 0
        predictions_made = 0
        today = date.today()
        
        for i, model in enumerate(active_models):
            progress = 50 + (i / len(active_models)) * 40
            self.update_state(
                state="PROGRESS",
                meta={
                    "status": f"Prédiction ML {model.symbol} ({i+1}/{len(active_models)})...",
                    "progress": int(progress),
                    "current_step": "making_predictions",
                    "screener_run_id": screener_run_id,
                    "current_symbol": model.symbol,
                    "steps": [
                        {"step": 1, "name": "Entraînement des modèles", "status": "completed"},
                        {"step": 2, "name": "Calcul des prédictions", "status": "current"},
                        {"step": 3, "name": "Filtrage des opportunités", "status": "pending"},
                        {"step": 4, "name": "Finalisation", "status": "pending"}
                    ],
                    "total_symbols": total_symbols,
                    "successful_models": successful_models,
                    "predictions_made": predictions_made
                }
            )
            
            try:
                # Créer une nouvelle session pour chaque prédiction
                db = get_fresh_db_session()
                try:
                    # Faire la VRAIE prédiction ML
                    prediction_result = ml_service.predict(
                        symbol=model.symbol,
                        model_id=model.id,
                        date=today,
                        db=db
                    )
                    
                    if prediction_result and "error" not in prediction_result:
                        predictions_made += 1
                        prediction = prediction_result["prediction"]
                        confidence = prediction_result["confidence"]
                        
                        # Vérification si c'est une opportunité
                        # Utiliser le confidence_threshold du paramètre de recherche
                        confidence_threshold = screener_request.get('confidence_threshold', 0.7)
                        if prediction == 1.0 and confidence >= confidence_threshold:
                            opportunities_found += 1
                            
                            # Enregistrement du résultat
                            screener_result = ScreenerResult(
                                screener_run_id=screener_run_id,
                                symbol=model.symbol,
                                model_id=model.id,
                                prediction=float(prediction),
                                confidence=float(confidence),
                                rank=opportunities_found
                            )
                            db.add(screener_result)
                            db.commit()
                            print(f"🎯 {model.symbol}: Opportunité ML trouvée! Confiance: {confidence:.1%}")
                        else:
                            print(f"⏭️ {model.symbol}: Pas d'opportunité ML (Confiance: {confidence:.1%}, Prédiction: {prediction})")
                    else:
                        print(f"❌ {model.symbol}: Échec de la prédiction ML - {prediction_result.get('error', 'Erreur inconnue') if prediction_result else 'Pas de résultat'}")
                        
                finally:
                    db.close()
                    
            except Exception as e:
                print(f"❌ {model.symbol}: Erreur lors de la prédiction ML - {str(e)}")
                continue
        
        # Finalisation
        db = get_fresh_db_session()
        try:
            screener_run = db.query(ScreenerRun).filter(ScreenerRun.id == screener_run_id).first()
            if screener_run:
                screener_run.opportunities_found = opportunities_found
                screener_run.status = "completed"
                screener_run.execution_time_seconds = int(time.time() - start_time)
                db.commit()
        finally:
            db.close()
        
        # Récupération des résultats détaillés
        db = get_fresh_db_session()
        try:
            screener_results_db = db.query(ScreenerResult).filter(ScreenerResult.screener_run_id == screener_run_id).all()
            results_list = []
            
            for res_db in screener_results_db:
                model = db.query(MLModels).filter(MLModels.id == res_db.model_id).first()
                target_param = db.query(TargetParameters).filter(TargetParameters.id == model.target_parameter_id).first()
                symbol_metadata = db.query(SymbolMetadata).filter(SymbolMetadata.symbol == res_db.symbol).first()
                company_name = symbol_metadata.company_name if symbol_metadata else f"{res_db.symbol} Corp"

                results_list.append({
                    "symbol": res_db.symbol,
                    "company_name": company_name,
                    "prediction": float(res_db.prediction),
                    "confidence": float(res_db.confidence),
                    "model_id": res_db.model_id,
                    "model_name": model.model_name,
                    "target_return": float(target_param.target_return_percentage),
                    "time_horizon": target_param.time_horizon_days,
                    "rank": res_db.rank
                })
        finally:
            db.close()
        
        print(f"🎉 Screener ML limité terminé: {opportunities_found} opportunités trouvées sur {total_symbols} symboles")
        
        # Résultat final
        result = {
            "screener_run_id": screener_run_id,
            "total_symbols": total_symbols,
            "successful_models": successful_models,
            "total_opportunities_found": opportunities_found,
            "execution_time_seconds": int(time.time() - start_time),
            "status": "completed",
            "results": results_list
        }
        
        self.update_state(
            state="SUCCESS",
            meta={
                "status": "Screener ML limité terminé avec succès!",
                "progress": 100,
                "steps": [
                    {"step": 1, "name": "Entraînement des modèles", "status": "completed"},
                    {"step": 2, "name": "Calcul des prédictions", "status": "completed"},
                    {"step": 3, "name": "Filtrage des opportunités", "status": "completed"},
                    {"step": 4, "name": "Finalisation", "status": "completed"}
                ],
                "current_step": "completed",
                "result": result
            }
        )
        
        return result
        
    except Exception as e:
        # Gestion d'erreur
        error_message = str(e)
        print(f"❌ Erreur générale dans le screener ML limité: {error_message}")
        
        if screener_run_id:
            try:
                db = get_fresh_db_session()
                try:
                    screener_run = db.query(ScreenerRun).filter(ScreenerRun.id == screener_run_id).first()
                    if screener_run:
                        screener_run.status = "failed"
                        screener_run.error_message = error_message
                        db.commit()
                finally:
                    db.close()
            except Exception as db_e:
                print(f"Erreur lors de la mise à jour du statut d'échec: {db_e}")
        
        # Retourner un résultat d'erreur simple
        error_result = {
            "status": "failed",
            "error": error_message,
            "screener_run_id": screener_run_id
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
