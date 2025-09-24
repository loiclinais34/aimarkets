import asyncio
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from decimal import Decimal
import time

from ..models.database import (
    ScreenerConfig, ScreenerRun, ScreenerResult, 
    MLModels, TargetParameters, SymbolMetadata
)
from ..models.schemas import ScreenerRequest, ScreenerResponse
from .ml_service import MLService


class ScreenerService:
    def __init__(self, db: Session):
        self.db = db
        self.ml_service = MLService(db=db)

    def calculate_confidence_threshold(self, risk_tolerance: float) -> float:
        """
        Calcule le seuil de confiance basé sur la tolérance au risque.
        Plus la tolérance au risque est élevée, plus le seuil de confiance est bas.
        """
        # Mapping: risk_tolerance (0.1-1.0) -> confidence_threshold (0.9-0.5)
        # risk_tolerance = 0.1 (très conservateur) -> confidence_threshold = 0.9
        # risk_tolerance = 1.0 (très agressif) -> confidence_threshold = 0.5
        confidence_threshold = 0.9 - (risk_tolerance - 0.1) * 0.4
        return max(0.5, min(0.9, confidence_threshold))

    def create_screener_config(self, request: ScreenerRequest, created_by: str = "screener_user") -> ScreenerConfig:
        """Crée une nouvelle configuration de screener"""
        confidence_threshold = self.calculate_confidence_threshold(request.risk_tolerance)
        
        config = ScreenerConfig(
            name=f"Screener_{request.target_return_percentage}%_{request.time_horizon_days}d_{request.risk_tolerance}",
            target_return_percentage=Decimal(str(request.target_return_percentage)),
            time_horizon_days=request.time_horizon_days,
            risk_tolerance=Decimal(str(request.risk_tolerance)),
            confidence_threshold=Decimal(str(confidence_threshold)),
            created_by=created_by
        )
        
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        
        return config

    def get_available_symbols(self) -> List[str]:
        """Récupère la liste des symboles disponibles"""
        symbols = self.db.query(SymbolMetadata.symbol).filter(
            SymbolMetadata.is_active == True
        ).all()
        return [symbol[0] for symbol in symbols]

    async def train_models_for_all_symbols(self, config: ScreenerConfig) -> Dict[str, Any]:
        """Entraîne les modèles pour tous les symboles disponibles"""
        symbols = self.get_available_symbols()
        successful_models = 0
        failed_models = 0
        model_results = {}
        
        print(f"🚀 Début de l'entraînement pour {len(symbols)} symboles...")
        
        for i, symbol in enumerate(symbols):
            try:
                print(f"📊 Entraînement {i+1}/{len(symbols)}: {symbol}")
                
                # Créer ou récupérer les paramètres cibles
                target_param = self._get_or_create_target_parameter(
                    symbol=symbol,
                    target_return_percentage=float(config.target_return_percentage),
                    time_horizon_days=config.time_horizon_days,
                    risk_tolerance=float(config.risk_tolerance),
                    user_id="screener_user"
                )
                
                # Entraîner le modèle de classification
                model_result = self.ml_service.train_classification_model(
                    symbol=symbol,
                    target_param=target_param,
                    db=self.db
                )
                
                if model_result and "model_id" in model_result:
                    successful_models += 1
                    model_results[symbol] = {
                        "model_id": model_result["model_id"],
                        "model_name": model_result["model_name"],
                        "performance": model_result.get("performance_metrics", {})
                    }
                    print(f"✅ {symbol}: Modèle entraîné avec succès (ID: {model_result['model_id']})")
                else:
                    failed_models += 1
                    print(f"❌ {symbol}: Échec de l'entraînement")
                    
            except Exception as e:
                failed_models += 1
                print(f"❌ {symbol}: Erreur - {str(e)}")
                continue
        
        print(f"🎯 Entraînement terminé: {successful_models} succès, {failed_models} échecs")
        
        return {
            "total_symbols": len(symbols),
            "successful_models": successful_models,
            "failed_models": failed_models,
            "model_results": model_results
        }

    def _get_or_create_target_parameter(self, symbol: str, target_return_percentage: float, 
                                       time_horizon_days: int, risk_tolerance: float, 
                                       user_id: str = "screener_user") -> TargetParameters:
        """Crée ou récupère les paramètres cibles pour un symbole"""
        # Vérifier si des paramètres existent déjà
        existing_param = self.db.query(TargetParameters).filter(
            and_(
                TargetParameters.user_id == user_id,
                TargetParameters.parameter_name == f"target_{symbol}_{target_return_percentage}%_{time_horizon_days}d"
            )
        ).first()
        
        if existing_param:
            return existing_param
        
        # Créer de nouveaux paramètres
        risk_tolerance_map = {
            0.1: "very_low",
            0.3: "low", 
            0.5: "medium",
            0.7: "high",
            0.9: "very_high"
        }
        
        risk_tolerance_str = "medium"  # default
        for threshold, risk_str in risk_tolerance_map.items():
            if risk_tolerance <= threshold:
                risk_tolerance_str = risk_str
                break
        
        target_param = TargetParameters(
            user_id=user_id,
            parameter_name=f"target_{symbol}_{target_return_percentage}%_{time_horizon_days}d",
            target_return_percentage=Decimal(str(target_return_percentage)),
            time_horizon_days=time_horizon_days,
            risk_tolerance=risk_tolerance_str,
            is_active=True
        )
        
        self.db.add(target_param)
        self.db.commit()
        self.db.refresh(target_param)
        
        return target_param

    async def run_predictions_for_all_models(self, model_results: Dict[str, Any], config: ScreenerConfig) -> List[Dict[str, Any]]:
        """Exécute les prédictions pour tous les modèles entraînés"""
        today = date.today()
        opportunities = []
        
        print(f"🔮 Début des prédictions pour {len(model_results)} modèles...")
        
        for symbol, model_info in model_results.items():
            try:
                model_id = model_info["model_id"]
                print(f"🔍 Prédiction pour {symbol} (Modèle ID: {model_id})")
                
                # Faire la prédiction
                prediction_result = self.ml_service.predict(
                    symbol=symbol,
                    model_id=model_id,
                    date=today,
                    db=self.db
                )
                
                if prediction_result and "prediction" in prediction_result:
                    prediction_value = float(prediction_result["prediction"])
                    confidence = float(prediction_result["confidence"])
                    
                    # Vérifier si c'est une opportunité (prediction = 1 et confiance >= seuil)
                    if prediction_value >= 0.5 and confidence >= float(config.confidence_threshold):
                        # Récupérer les métadonnées du symbole
                        symbol_metadata = self.db.query(SymbolMetadata).filter(
                            SymbolMetadata.symbol == symbol
                        ).first()
                        
                        opportunity = {
                            "symbol": symbol,
                            "company_name": symbol_metadata.company_name if symbol_metadata else symbol,
                            "prediction": prediction_value,
                            "confidence": confidence,
                            "model_id": model_id,
                            "model_name": model_info["model_name"],
                            "target_return": float(config.target_return_percentage),
                            "time_horizon": config.time_horizon_days
                        }
                        
                        opportunities.append(opportunity)
                        print(f"🎯 {symbol}: Opportunité trouvée! Confiance: {confidence:.1%}")
                    else:
                        print(f"⏭️ {symbol}: Pas d'opportunité (Confiance: {confidence:.1%}, Prédiction: {prediction_value})")
                        
            except Exception as e:
                print(f"❌ {symbol}: Erreur lors de la prédiction - {str(e)}")
                continue
        
        # Trier par confiance décroissante
        opportunities.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Ajouter le rang
        for i, opportunity in enumerate(opportunities):
            opportunity["rank"] = i + 1
        
        print(f"🎉 {len(opportunities)} opportunités trouvées sur {len(model_results)} modèles")
        
        return opportunities

    def run_screener_async(self, request: ScreenerRequest, user_id: str = "demo_user") -> Dict[str, Any]:
        """
        Lancer un screener de manière asynchrone
        """
        # Import local pour éviter les imports circulaires
        from ..tasks.screener_tasks import run_screener_async
        
        # Conversion de la requête en dictionnaire pour la tâche
        request_dict = {
            "target_return_percentage": request.target_return_percentage,
            "time_horizon_days": request.time_horizon_days,
            "risk_tolerance": request.risk_tolerance
        }
        
        # Lancement de la tâche asynchrone
        task = run_screener_async.delay(request_dict, user_id)
        
        return {
            "task_id": task.id,
            "status": "started",
            "message": "Screener lancé en arrière-plan"
        }

    async def run_screener(self, request: ScreenerRequest, created_by: str = "screener_user") -> ScreenerResponse:
        """Exécute le screener complet"""
        start_time = time.time()
        
        try:
            # 1. Créer la configuration du screener
            config = self.create_screener_config(request, created_by)
            print(f"📋 Configuration créée: {config.name}")
            
            # 2. Créer l'enregistrement de l'exécution
            screener_run = ScreenerRun(
                screener_config_id=config.id,
                run_date=date.today(),
                total_symbols=0,
                successful_models=0,
                opportunities_found=0,
                execution_time_seconds=0,
                status="running"
            )
            self.db.add(screener_run)
            self.db.commit()
            self.db.refresh(screener_run)
            
            # 3. Entraîner les modèles pour tous les symboles
            training_results = await self.train_models_for_all_symbols(config)
            
            # 4. Exécuter les prédictions
            opportunities = await self.run_predictions_for_all_models(
                training_results["model_results"], 
                config
            )
            
            # 5. Sauvegarder les résultats
            for opportunity in opportunities:
                result = ScreenerResult(
                    screener_run_id=screener_run.id,
                    symbol=opportunity["symbol"],
                    model_id=opportunity["model_id"],
                    prediction=Decimal(str(opportunity["prediction"])),
                    confidence=Decimal(str(opportunity["confidence"])),
                    rank=opportunity["rank"]
                )
                self.db.add(result)
            
            # 6. Mettre à jour l'exécution
            execution_time = int(time.time() - start_time)
            screener_run.total_symbols = training_results["total_symbols"]
            screener_run.successful_models = training_results["successful_models"]
            screener_run.opportunities_found = len(opportunities)
            screener_run.execution_time_seconds = execution_time
            screener_run.status = "completed"
            
            self.db.commit()
            
            print(f"✅ Screener terminé en {execution_time}s: {len(opportunities)} opportunités trouvées")
            
            return ScreenerResponse(
                screener_run_id=screener_run.id,
                total_symbols=training_results["total_symbols"],
                successful_models=training_results["successful_models"],
                opportunities_found=len(opportunities),
                execution_time_seconds=execution_time,
                results=opportunities
            )
            
        except Exception as e:
            # Mettre à jour le statut en cas d'erreur
            if 'screener_run' in locals():
                screener_run.status = "failed"
                screener_run.error_message = str(e)
                self.db.commit()
            
            print(f"❌ Erreur lors de l'exécution du screener: {str(e)}")
            raise e

    def get_screener_history(self, limit: int = 10) -> List[ScreenerRun]:
        """Récupère l'historique des exécutions de screener"""
        return self.db.query(ScreenerRun).order_by(
            desc(ScreenerRun.created_at)
        ).limit(limit).all()

    def get_screener_results(self, screener_run_id: int) -> List[ScreenerResult]:
        """Récupère les résultats d'une exécution de screener"""
        return self.db.query(ScreenerResult).filter(
            ScreenerResult.screener_run_id == screener_run_id
        ).order_by(ScreenerResult.rank).all()
