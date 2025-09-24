"""
Service Web Server pour le Screener ML Complet
Stratégie robuste avec gestion d'erreurs et sessions optimisées
"""
import time
import os
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from celery import current_task
from sqlalchemy.orm import Session
from contextlib import contextmanager

from app.core.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.database import ScreenerRun, ScreenerResult, MLModels, TargetParameters, SymbolMetadata
from app.models.schemas import ScreenerRequest
from app.services.ml_service import MLService

# Configuration du logging détaillé
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


@contextmanager
def get_db_session():
    """Context manager pour les sessions de base de données"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()


class MLWebService:
    """Service web robuste pour le ML complet"""
    
    def __init__(self):
        # Ne pas instancier MLService ici car il sera créé avec une session DB appropriée
        self.ml_service = None
        self.start_time = time.time()
    
    def get_execution_time(self) -> int:
        """Calculer le temps d'exécution"""
        return int(time.time() - self.start_time)
    
    def get_active_symbols(self, db: Session, limit: Optional[int] = None) -> List[str]:
        """Récupérer les symboles actifs"""
        logger.info(f"🔍 [GET_SYMBOLS] Récupération des symboles actifs (limite: {limit})")
        
        query = db.query(SymbolMetadata.symbol).filter(
            SymbolMetadata.is_active == True
        ).order_by(SymbolMetadata.symbol.asc())
        
        if limit:
            query = query.limit(limit)
        
        symbols = [row[0] for row in query.all()]
        logger.info(f"🔍 [GET_SYMBOLS] {len(symbols)} symboles trouvés")
        logger.debug(f"🔍 [GET_SYMBOLS] Premiers symboles: {symbols[:5] if symbols else 'Aucun'}")
        
        return symbols
    
    def create_screener_run(self, db: Session, user_id: str) -> ScreenerRun:
        """Créer un enregistrement de run de screener"""
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
        return screener_run
    
    def get_active_symbols(self, db: Session, limit: Optional[int] = None) -> List[str]:
        """Récupérer les symboles actifs"""
        query = db.query(SymbolMetadata.symbol).filter(
            SymbolMetadata.is_active == True
        ).order_by(SymbolMetadata.symbol.asc())
        
        if limit:
            query = query.limit(limit)
        
        return [row[0] for row in query.all()]
    
    def create_target_parameter(self, db: Session, symbol: str, request: ScreenerRequest, user_id: str) -> TargetParameters:
        """Créer ou récupérer les paramètres cibles"""
        existing_param = db.query(TargetParameters).filter(
            TargetParameters.user_id == user_id,
            TargetParameters.parameter_name == f"target_{symbol}_{request.target_return_percentage}%_{request.time_horizon_days}d"
        ).first()
        
        if existing_param:
            return existing_param
        
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
            target_return_percentage=request.target_return_percentage,
            time_horizon_days=request.time_horizon_days,
            risk_tolerance=risk_tolerance_str,
            min_confidence_threshold=request.risk_tolerance,
            max_drawdown_percentage=5.0,
            is_active=True
        )
        db.add(target_param)
        db.commit()
        db.refresh(target_param)
        return target_param
    
    def train_model_for_symbol(self, db: Session, symbol: str, target_param: TargetParameters) -> bool:
        """Entraîner un modèle pour un symbole"""
        logger.info(f"🔧 [TRAIN] Début entraînement pour {symbol}")
        logger.debug(f"🔧 [TRAIN] Target param ID: {target_param.id}, DB session: {type(db)}")
        
        try:
            # Instancier le service ML avec la session DB appropriée
            logger.debug(f"🔧 [TRAIN] Instanciation MLService avec session DB pour {symbol}")
            ml_service = MLService(db)
            logger.debug(f"🔧 [TRAIN] MLService instancié: {type(ml_service)}")
            
            logger.info(f"🔧 [TRAIN] Appel train_classification_model pour {symbol}")
            model_result = ml_service.train_classification_model(
                symbol=symbol,
                target_param=target_param,
                db=db
            )
            logger.debug(f"🔧 [TRAIN] Résultat entraînement {symbol}: {model_result}")
            
            if model_result and model_result.get("model_id"):
                logger.info(f"✅ [TRAIN] Modèle ML entraîné avec succès pour {symbol} (ID: {model_result.get('model_id')})")
                return True
            else:
                error_msg = model_result.get('error', 'Erreur inconnue') if model_result else 'Pas de résultat'
                logger.error(f"❌ [TRAIN] Échec entraînement {symbol}: {error_msg}")
                return False
                
        except Exception as e:
            logger.error(f"❌ [TRAIN] Exception lors de l'entraînement ML pour {symbol}: {str(e)}")
            logger.error(f"❌ [TRAIN] Type d'erreur: {type(e)}")
            import traceback
            logger.error(f"❌ [TRAIN] Stack trace: {traceback.format_exc()}")
            return False
    
    def predict_for_model(self, db: Session, model: MLModels, request: ScreenerRequest, screener_run_id: int = None) -> Optional[Dict[str, Any]]:
        """Faire une prédiction pour un modèle"""
        logger.info(f"🔮 [PREDICT] Début prédiction pour {model.symbol}")
        logger.debug(f"🔮 [PREDICT] Model ID: {model.id}, DB session: {type(db)}")
        
        try:
            # D'abord, vérifier s'il y a des prédictions récentes pour ce modèle
            from app.models.database import MLPredictions
            recent_prediction = db.query(MLPredictions).filter(
                MLPredictions.model_id == model.id,
                MLPredictions.created_at >= date.today()
            ).order_by(MLPredictions.created_at.desc()).first()
            
            if recent_prediction:
                logger.info(f"🔮 [PREDICT] Utilisation prédiction existante pour {model.symbol}: {recent_prediction.prediction_value}, confiance: {recent_prediction.confidence}")
                
                return {
                    "prediction": float(recent_prediction.prediction_value),
                    "confidence": float(recent_prediction.confidence),
                    "is_opportunity": recent_prediction.prediction_value == 1.0 and recent_prediction.confidence >= request.risk_tolerance
                }
            
            # Si pas de prédiction récente, faire une nouvelle prédiction
            logger.info(f"🔮 [PREDICT] Aucune prédiction récente trouvée, création nouvelle prédiction pour {model.symbol}")
            
            # Instancier le service ML avec la session DB appropriée
            logger.debug(f"🔮 [PREDICT] Instanciation MLService avec session DB pour {model.symbol}")
            ml_service = MLService(db)
            logger.debug(f"🔮 [PREDICT] MLService instancié: {type(ml_service)}")
            
            logger.info(f"🔮 [PREDICT] Appel predict pour {model.symbol}")
            prediction_result = ml_service.predict(
                symbol=model.symbol,
                model_id=model.id,
                date=date.today(),
                db=db,
                screener_run_id=screener_run_id
            )
            logger.debug(f"🔮 [PREDICT] Résultat prédiction {model.symbol}: {prediction_result}")
            
            if prediction_result and not prediction_result.get("error"):
                prediction = prediction_result["prediction"]
                confidence = prediction_result["confidence"]
                
                logger.info(f"🔮 [PREDICT] Prédiction réussie pour {model.symbol}: {prediction}, confiance: {confidence}")
                
                return {
                    "prediction": prediction,
                    "confidence": confidence,
                    "is_opportunity": prediction == 1.0 and confidence >= request.risk_tolerance
                }
            else:
                error_msg = prediction_result.get('error', 'Erreur inconnue') if prediction_result else 'Pas de résultat'
                logger.error(f"❌ [PREDICT] Échec prédiction {model.symbol}: {error_msg}")
                return None
                
        except Exception as e:
            logger.error(f"❌ [PREDICT] Exception lors de la prédiction ML pour {model.symbol}: {str(e)}")
            logger.error(f"❌ [PREDICT] Type d'erreur: {type(e)}")
            import traceback
            logger.error(f"❌ [PREDICT] Stack trace: {traceback.format_exc()}")
            return None
    
    def get_predictions_for_screener_run(self, db: Session, screener_run_id: int) -> List[Dict[str, Any]]:
        """Récupérer toutes les prédictions générées par un screener run"""
        from app.models.database import MLPredictions
        
        predictions = db.query(MLPredictions).filter(
            MLPredictions.screener_run_id == screener_run_id
        ).order_by(MLPredictions.created_at.desc()).all()
        
        results = []
        for pred in predictions:
            results.append({
                "symbol": pred.symbol,
                "prediction_value": float(pred.prediction_value),
                "confidence": float(pred.confidence),
                "prediction_date": pred.prediction_date,
                "created_at": pred.created_at,
                "model_id": pred.model_id
            })
        
        return results
    
    def get_opportunities_for_screener_run(self, db: Session, screener_run_id: int, min_confidence: float = 0.5) -> List[Dict[str, Any]]:
        """Récupérer les opportunités (prediction_value = 1) générées par un screener run"""
        from app.models.database import MLPredictions
        
        opportunities = db.query(MLPredictions).filter(
            MLPredictions.screener_run_id == screener_run_id,
            MLPredictions.prediction_value == 1.0,
            MLPredictions.confidence >= min_confidence
        ).order_by(MLPredictions.confidence.desc()).all()
        
        results = []
        for opp in opportunities:
            results.append({
                "symbol": opp.symbol,
                "prediction_value": float(opp.prediction_value),
                "confidence": float(opp.confidence),
                "prediction_date": opp.prediction_date,
                "created_at": opp.created_at,
                "model_id": opp.model_id
            })
        
        return results

    def get_results_for_run(self, db: Session, screener_run_id: int) -> List[Dict[str, Any]]:
        """Récupérer les résultats détaillés d'un run"""
        screener_results_db = db.query(ScreenerResult).filter(
            ScreenerResult.screener_run_id == screener_run_id
        ).all()
        
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
        
        return results_list


@celery_app.task(bind=True, name="run_full_screener_ml_web")
def run_full_screener_ml_web(self, screener_request: Dict[str, Any], user_id: str = "screener_user", max_symbols: Optional[int] = None) -> Dict[str, Any]:
    """
    Tâche de screener ML complet avec service web robuste
    """
    ml_service = MLWebService()
    screener_run_id = None
    
    try:
        # Mise à jour du statut initial
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "Démarrage du screener ML complet...",
                "progress": 0,
                "current_step": "initialization"
            }
        )
        
        # Conversion du dictionnaire en objet ScreenerRequest
        request = ScreenerRequest(**screener_request)
        
        # Phase 1: Initialisation
        with get_db_session() as db:
            screener_run = ml_service.create_screener_run(db, user_id)
            screener_run_id = screener_run.id
        
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "Récupération des symboles...",
                "progress": 5,
                "current_step": "fetching_symbols",
                "screener_run_id": screener_run_id
            }
        )
        
        # Phase 2: Récupération des symboles
        with get_db_session() as db:
            symbols = ml_service.get_active_symbols(db, max_symbols)
            total_symbols = len(symbols)
            logger.info(f"📊 [MAIN] Symboles récupérés: {total_symbols}")
            logger.debug(f"📊 [MAIN] Premiers symboles: {symbols[:5] if symbols else 'Aucun'}")
            
            # Mise à jour du nombre total de symboles
            screener_run = db.query(ScreenerRun).filter(ScreenerRun.id == screener_run_id).first()
            if screener_run:
                screener_run.total_symbols = total_symbols
                db.commit()
        
        logger.info(f"📊 [MAIN] {total_symbols} symboles à analyser avec vrais modèles ML")
        logger.debug(f"📊 [MAIN] Symboles: {symbols[:5]}...")  # Log des premiers symboles
        
        # Phase 3: Entraînement des modèles
        self.update_state(
            state="PROGRESS",
            meta={
                "status": f"Entraînement des modèles ML (0/{total_symbols})...",
                "progress": 10,
                "current_step": "training_models",
                "screener_run_id": screener_run_id,
                "total_symbols": total_symbols,
                "trained_models": 0
            }
        )
        
        successful_models = 0
        
        for i, symbol in enumerate(symbols):
            progress = 10 + (i / total_symbols) * 40
            logger.info(f"🔧 [MAIN] Traitement symbole {i+1}/{total_symbols}: {symbol}")
            
            self.update_state(
                state="PROGRESS",
                meta={
                    "status": f"Entraînement ML {symbol} ({i+1}/{total_symbols})...",
                    "progress": int(progress),
                    "current_step": "training_models",
                    "screener_run_id": screener_run_id,
                    "total_symbols": total_symbols,
                    "trained_models": successful_models,
                    "current_symbol": symbol
                }
            )
            
            with get_db_session() as db:
                try:
                    logger.debug(f"🔧 [MAIN] Création target parameter pour {symbol}")
                    target_param = ml_service.create_target_parameter(db, symbol, request, user_id)
                    logger.debug(f"🔧 [MAIN] Target parameter créé: {target_param.id}")
                    
                    if ml_service.train_model_for_symbol(db, symbol, target_param):
                        successful_models += 1
                        
                except Exception as e:
                    print(f"❌ {symbol}: Erreur générale - {str(e)}")
                    continue
        
        # Mise à jour du nombre de modèles entraînés
        with get_db_session() as db:
            screener_run = db.query(ScreenerRun).filter(ScreenerRun.id == screener_run_id).first()
            if screener_run:
                screener_run.successful_models = successful_models
                db.commit()
        
        print(f"🎯 {successful_models}/{total_symbols} modèles ML entraînés avec succès")
        
        # Phase 4: Prédictions
        self.update_state(
            state="PROGRESS",
            meta={
                "status": f"Calcul des prédictions ML...",
                "progress": 50,
                "current_step": "making_predictions",
                "screener_run_id": screener_run_id,
                "total_symbols": total_symbols,
                "successful_models": successful_models
            }
        )
        
        with get_db_session() as db:
            # Sélectionner seulement les modèles qui correspondent aux paramètres du screener
            active_models = db.query(MLModels).join(TargetParameters).filter(
                MLModels.is_active == True,
                MLModels.symbol.in_(symbols),
                TargetParameters.target_return_percentage == request.target_return_percentage,
                TargetParameters.time_horizon_days == request.time_horizon_days
            ).all()
        
        opportunities_found = 0
        
        for i, model in enumerate(active_models):
            progress = 50 + (i / len(active_models)) * 40
            self.update_state(
                state="PROGRESS",
                meta={
                    "status": f"Prédiction ML {model.symbol} ({i+1}/{len(active_models)})...",
                    "progress": int(progress),
                    "current_step": "making_predictions",
                    "screener_run_id": screener_run_id,
                    "total_symbols": total_symbols,
                    "successful_models": successful_models,
                    "current_symbol": model.symbol
                }
            )
            
            with get_db_session() as db:
                prediction_data = ml_service.predict_for_model(db, model, request, screener_run_id)
                
                if prediction_data and prediction_data["is_opportunity"]:
                    opportunities_found += 1
                    
                    screener_result = ScreenerResult(
                        screener_run_id=screener_run_id,
                        symbol=model.symbol,
                        model_id=model.id,
                        prediction=float(prediction_data["prediction"]),
                        confidence=float(prediction_data["confidence"]),
                        rank=opportunities_found
                    )
                    db.add(screener_result)
                    db.commit()
                    print(f"🎯 {model.symbol}: Opportunité ML trouvée! Confiance: {prediction_data['confidence']:.1%}")
                elif prediction_data:
                    print(f"⏭️ {model.symbol}: Pas d'opportunité ML (Confiance: {prediction_data['confidence']:.1%}, Prédiction: {prediction_data['prediction']})")
        
        # Phase 5: Finalisation
        with get_db_session() as db:
            screener_run = db.query(ScreenerRun).filter(ScreenerRun.id == screener_run_id).first()
            if screener_run:
                screener_run.opportunities_found = opportunities_found
                screener_run.status = "completed"
                screener_run.execution_time_seconds = ml_service.get_execution_time()
                db.commit()
        
        # Récupération des résultats
        with get_db_session() as db:
            results_list = ml_service.get_results_for_run(db, screener_run_id)
        
        print(f"🎉 Screener ML complet terminé: {opportunities_found} opportunités trouvées sur {total_symbols} symboles")
        
        # Résultat final
        result = {
            "screener_run_id": screener_run_id,
            "total_symbols": total_symbols,
            "successful_models": successful_models,
            "total_opportunities_found": opportunities_found,
            "execution_time_seconds": ml_service.get_execution_time(),
            "status": "completed",
            "results": results_list
        }
        
        self.update_state(
            state="SUCCESS",
            meta={
                "status": "Screener ML complet terminé avec succès!",
                "progress": 100,
                "current_step": "completed",
                "result": result
            }
        )
        
        return result
        
    except Exception as e:
        # Gestion d'erreur robuste
        error_message = str(e)
        print(f"❌ Erreur générale dans le screener ML complet: {error_message}")
        
        if screener_run_id:
            try:
                with get_db_session() as db:
                    screener_run = db.query(ScreenerRun).filter(ScreenerRun.id == screener_run_id).first()
                    if screener_run:
                        screener_run.status = "failed"
                        screener_run.error_message = error_message
                        db.commit()
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
