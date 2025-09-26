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
        
        print(f"🎯 Nouveau paramètre créé pour {symbol}: {target_return_percentage}% sur {time_horizon_days} jours")
        
        return target_param

    def get_available_models_for_symbol(self, symbol: str, config: ScreenerConfig) -> List[Dict[str, Any]]:
        """Récupère tous les modèles disponibles pour un symbole (RandomForest, XGBoost, LightGBM)"""
        # Joindre avec TargetParameters pour filtrer par target_return_percentage et time_horizon_days
        models = self.db.query(MLModels).join(TargetParameters).filter(
            and_(
                MLModels.symbol == symbol,
                TargetParameters.target_return_percentage == config.target_return_percentage,
                TargetParameters.time_horizon_days == config.time_horizon_days,
                MLModels.is_active == True
            )
        ).all()
        
        available_models = []
        for model in models:
            # Extraire l'algorithme des paramètres du modèle
            algorithm = "RandomForest"  # Par défaut
            if model.model_parameters:
                import json
                params = json.loads(model.model_parameters) if isinstance(model.model_parameters, str) else model.model_parameters
                algorithm = params.get("algorithm", "RandomForest")
            
            # Extraire les métriques de performance
            performance_metrics = {}
            if model.performance_metrics:
                performance_metrics = json.loads(model.performance_metrics) if isinstance(model.performance_metrics, str) else model.performance_metrics
            
            available_models.append({
                "model_id": model.id,
                "model_name": model.model_name,
                "model_type": model.model_type,
                "algorithm": algorithm,
                "accuracy": performance_metrics.get("test_score", 0.0),
                "precision": performance_metrics.get("precision", 0.0),
                "recall": performance_metrics.get("recall", 0.0),
                "f1_score": performance_metrics.get("f1_score", 0.0),
                "roc_auc": performance_metrics.get("roc_auc", 0.0),
                "sharpe_ratio": performance_metrics.get("sharpe_ratio", 0.0),
                "max_drawdown": performance_metrics.get("max_drawdown", 0.0),
                "total_return": performance_metrics.get("total_return", 0.0),
                "win_rate": performance_metrics.get("win_rate", 0.0),
                "profit_factor": performance_metrics.get("profit_factor", 0.0)
            })
        
        return available_models

    def select_best_model(self, models: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sélectionne le meilleur modèle basé sur un score composite"""
        if not models:
            return None
        
        if len(models) == 1:
            return models[0]
        
        # Score composite basé sur plusieurs métriques
        best_model = None
        best_score = -1
        
        for model in models:
            # Score composite : 40% accuracy + 30% f1_score + 20% sharpe_ratio + 10% win_rate
            composite_score = (
                0.4 * model["accuracy"] +
                0.3 * model["f1_score"] +
                0.2 * model["sharpe_ratio"] +
                0.1 * model["win_rate"]
            )
            
            if composite_score > best_score:
                best_score = composite_score
                best_model = model
        
        # Ajouter le score composite au modèle sélectionné
        best_model["composite_score"] = best_score
        return best_model

    async def run_predictions_for_all_models(self, model_results: Dict[str, Any], config: ScreenerConfig) -> List[Dict[str, Any]]:
        """Exécute les prédictions pour tous les modèles entraînés avec sélection du meilleur modèle"""
        today = date.today()
        opportunities = []
        
        print(f"🔮 Début des prédictions pour {len(model_results)} symboles...")
        
        for symbol, model_info in model_results.items():
            try:
                print(f"🔍 Analyse des modèles pour {symbol}")
                
                # Récupérer tous les modèles disponibles pour ce symbole
                available_models = self.get_available_models_for_symbol(symbol, config)
                
                if not available_models:
                    print(f"⚠️ Aucun modèle disponible pour {symbol}")
                    continue
                
                # Sélectionner le meilleur modèle
                best_model = self.select_best_model(available_models)
                
                if not best_model:
                    print(f"⚠️ Impossible de sélectionner un modèle pour {symbol}")
                    continue
                
                print(f"🎯 Meilleur modèle pour {symbol}: {best_model['algorithm']} (Score: {best_model['composite_score']:.3f})")
                
                # Faire la prédiction avec le meilleur modèle
                prediction_result = self.ml_service.predict(
                    symbol=symbol,
                    model_id=best_model["model_id"],
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
                            "model_id": best_model["model_id"],
                            "model_name": best_model["model_name"],
                            "model_type": best_model["model_type"],
                            "model_algorithm": best_model["algorithm"],
                            "model_accuracy": best_model["accuracy"],
                            "model_f1_score": best_model["f1_score"],
                            "model_sharpe_ratio": best_model["sharpe_ratio"],
                            "model_composite_score": best_model["composite_score"],
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
