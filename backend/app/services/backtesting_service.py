"""
Service de Backtesting pour l'évaluation des modèles ML
"""

import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..models.database import (
    MLModels, MLPredictions, HistoricalData, 
    BacktestRun, BacktestTrade, BacktestMetrics, BacktestEquityCurve,
    SymbolMetadata, TradingStrategy, StrategyRule, StrategyPerformance
)
from ..services.ml_service import MLService
from ..services.trading_strategy_service import TradingStrategyService

logger = logging.getLogger(__name__)


class BacktestingService:
    """Service principal pour le backtesting des modèles ML"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ml_service = MLService(db)
        self.strategy_service = TradingStrategyService(db)
    
    def create_backtest_run(
        self,
        name: str,
        model_id: int,
        start_date: date,
        end_date: date,
        initial_capital: float = 100000.0,
        position_size_percentage: float = 10.0,
        commission_rate: float = 0.001,
        slippage_rate: float = 0.0005,
        confidence_threshold: float = 0.60,
        max_positions: int = 10,
        description: str = "",
        created_by: str = "system",
        strategy_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Créer une nouvelle exécution de backtesting"""
        try:
            # Vérifier que le modèle existe
            model = self.db.query(MLModels).filter(MLModels.id == model_id).first()
            if not model:
                return {"success": False, "error": f"Modèle {model_id} non trouvé"}
            
            # Vérifier la stratégie si fournie
            if strategy_id:
                strategy = self.db.query(TradingStrategy).filter(TradingStrategy.id == strategy_id).first()
                if not strategy:
                    return {"success": False, "error": f"Stratégie {strategy_id} non trouvée"}
            
            # Vérifier les dates
            if start_date >= end_date:
                return {"success": False, "error": "La date de début doit être antérieure à la date de fin"}
            
            # Créer l'enregistrement de backtest
            backtest_run = BacktestRun(
                name=name,
                description=description,
                model_id=model_id,
                strategy_id=strategy_id,
                start_date=start_date,
                end_date=end_date,
                initial_capital=Decimal(str(initial_capital)),
                position_size_percentage=Decimal(str(position_size_percentage)),
                commission_rate=Decimal(str(commission_rate)),
                slippage_rate=Decimal(str(slippage_rate)),
                confidence_threshold=Decimal(str(confidence_threshold)),
                max_positions=max_positions,
                status='pending',
                created_by=created_by
            )
            
            self.db.add(backtest_run)
            self.db.commit()
            self.db.refresh(backtest_run)
            
            logger.info(f"Backtest run créé: {backtest_run.id} - {name}")
            
            return {
                "success": True,
                "backtest_run_id": backtest_run.id,
                "message": "Exécution de backtesting créée avec succès"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la création du backtest run: {e}")
            return {"success": False, "error": str(e)}
    
    def run_backtest(self, backtest_run_id: int) -> Dict[str, Any]:
        """Exécuter un backtesting complet"""
        try:
            # Récupérer le backtest run
            backtest_run = self.db.query(BacktestRun).filter(
                BacktestRun.id == backtest_run_id
            ).first()
            
            if not backtest_run:
                return {"success": False, "error": f"Backtest run {backtest_run_id} non trouvé"}
            
            if backtest_run.status != 'pending':
                return {"success": False, "error": f"Backtest run déjà exécuté (status: {backtest_run.status})"}
            
            # Mettre à jour le statut
            backtest_run.status = 'running'
            backtest_run.started_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Début du backtesting pour le run {backtest_run_id}")
            
            # Exécuter le backtesting
            result = self._execute_backtest(backtest_run)
            
            if result["success"]:
                backtest_run.status = 'completed'
                backtest_run.completed_at = datetime.utcnow()
            else:
                backtest_run.status = 'failed'
                backtest_run.error_message = result.get("error", "Erreur inconnue")
            
            self.db.commit()
            
            logger.info(f"Backtesting terminé pour le run {backtest_run_id}: {backtest_run.status}")
            
            return result
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de l'exécution du backtesting: {e}")
            
            # Mettre à jour le statut en cas d'erreur
            try:
                backtest_run = self.db.query(BacktestRun).filter(
                    BacktestRun.id == backtest_run_id
                ).first()
                if backtest_run:
                    backtest_run.status = 'failed'
                    backtest_run.error_message = str(e)
                    self.db.commit()
            except:
                pass
            
            return {"success": False, "error": str(e)}
    
    def _execute_backtest(self, backtest_run: BacktestRun) -> Dict[str, Any]:
        """Logique principale d'exécution du backtesting"""
        try:
            # Récupérer les prédictions du modèle pour la période
            predictions = self._get_predictions_for_period(
                backtest_run.model_id,
                backtest_run.start_date,
                backtest_run.end_date
            )
            
            if not predictions:
                return {"success": False, "error": "Aucune prédiction trouvée pour la période spécifiée"}
            
            # Initialiser le simulateur de trading
            simulator = TradingSimulator(
                initial_capital=float(backtest_run.initial_capital),
                position_size_percentage=float(backtest_run.position_size_percentage),
                commission_rate=float(backtest_run.commission_rate),
                slippage_rate=float(backtest_run.slippage_rate),
                confidence_threshold=float(backtest_run.confidence_threshold),
                max_positions=backtest_run.max_positions,
                strategy_id=backtest_run.strategy_id
            )
            
            # Exécuter la simulation
            trades, equity_curve = simulator.run_simulation(predictions, self.db)
            
            # Calculer les métriques
            metrics_calculator = MetricsCalculator()
            metrics = metrics_calculator.calculate_metrics(trades, equity_curve, backtest_run)
            
            # Sauvegarder les résultats
            self._save_backtest_results(backtest_run, trades, equity_curve, metrics)
            
            return {
                "success": True,
                "total_trades": len(trades),
                "final_capital": equity_curve[-1]["equity_value"] if equity_curve else backtest_run.initial_capital,
                "total_return": metrics.get("total_return", 0),
                "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                "max_drawdown": metrics.get("max_drawdown", 0)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du backtesting: {e}")
            return {"success": False, "error": str(e)}
    
    def _get_predictions_for_period(
        self, 
        model_id: int, 
        start_date: date, 
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Récupérer les prédictions du modèle pour une période donnée"""
        logger.info(f"Recherche prédictions pour modèle {model_id}, période {start_date} à {end_date}")
        
        predictions = self.db.query(MLPredictions).filter(
            and_(
                MLPredictions.model_id == model_id,
                MLPredictions.prediction_date >= start_date,
                MLPredictions.prediction_date <= end_date,
                MLPredictions.prediction_value >= 1.0  # Signaux d'achat (>= 1.0)
            )
        ).order_by(MLPredictions.prediction_date.asc()).all()
        
        logger.info(f"Trouvé {len(predictions)} prédictions avec prediction_value >= 1.0")
        
        result = [
            {
                "symbol": pred.symbol,
                "date": pred.prediction_date,
                "confidence": float(pred.confidence),
                "prediction": float(pred.prediction_value)
            }
            for pred in predictions
        ]
        
        logger.info(f"Prédictions retournées: {result}")
        return result
    
    def _save_backtest_results(
        self,
        backtest_run: BacktestRun,
        trades: List[Dict[str, Any]],
        equity_curve: List[Dict[str, Any]],
        metrics: Dict[str, Any]
    ):
        """Sauvegarder les résultats du backtesting en base"""
        try:
            # Sauvegarder les trades
            for trade in trades:
                backtest_trade = BacktestTrade(
                    backtest_run_id=backtest_run.id,
                    symbol=trade["symbol"],
                    entry_date=trade["entry_date"],
                    exit_date=trade["exit_date"],
                    entry_price=Decimal(str(trade["entry_price"])),
                    exit_price=Decimal(str(trade["exit_price"])),
                    quantity=trade["quantity"],
                    position_type=trade["position_type"],
                    entry_confidence=Decimal(str(trade["entry_confidence"])),
                    exit_reason=trade["exit_reason"],
                    gross_pnl=Decimal(str(trade["gross_pnl"])),
                    commission=Decimal(str(trade["commission"])),
                    slippage=Decimal(str(trade["slippage"])),
                    net_pnl=Decimal(str(trade["net_pnl"])),
                    return_percentage=Decimal(str(trade["return_percentage"])),
                    holding_days=trade["holding_days"]
                )
                self.db.add(backtest_trade)
            
            # Sauvegarder la courbe d'équité
            for point in equity_curve:
                equity_point = BacktestEquityCurve(
                    backtest_run_id=backtest_run.id,
                    date=point["date"],
                    equity_value=Decimal(str(point["equity_value"])),
                    drawdown=Decimal(str(point["drawdown"])),
                    daily_return=Decimal(str(point["daily_return"])),
                    cumulative_return=Decimal(str(point["cumulative_return"]))
                )
                self.db.add(equity_point)
            
            # Sauvegarder les métriques
            backtest_metrics = BacktestMetrics(
                backtest_run_id=backtest_run.id,
                total_return=Decimal(str(metrics["total_return"])),
                annualized_return=Decimal(str(metrics["annualized_return"])),
                total_trades=metrics["total_trades"],
                winning_trades=metrics["winning_trades"],
                losing_trades=metrics["losing_trades"],
                win_rate=Decimal(str(metrics["win_rate"])),
                max_drawdown=Decimal(str(metrics["max_drawdown"])),
                max_drawdown_duration=metrics["max_drawdown_duration"],
                volatility=Decimal(str(metrics["volatility"])),
                sharpe_ratio=Decimal(str(metrics["sharpe_ratio"])),
                sortino_ratio=Decimal(str(metrics["sortino_ratio"])),
                avg_return_per_trade=Decimal(str(metrics["avg_return_per_trade"])),
                avg_winning_trade=Decimal(str(metrics["avg_winning_trade"])),
                avg_losing_trade=Decimal(str(metrics["avg_losing_trade"])),
                profit_factor=Decimal(str(metrics["profit_factor"])),
                avg_holding_period=Decimal(str(metrics["avg_holding_period"])),
                final_capital=Decimal(str(metrics["final_capital"])),
                max_capital=Decimal(str(metrics["max_capital"])),
                min_capital=Decimal(str(metrics["min_capital"])),
                calmar_ratio=Decimal(str(metrics["calmar_ratio"])),
                recovery_factor=Decimal(str(metrics["recovery_factor"])),
                expectancy=Decimal(str(metrics["expectancy"]))
            )
            self.db.add(backtest_metrics)
            
            self.db.commit()
            logger.info(f"Résultats du backtesting sauvegardés pour le run {backtest_run.id}")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la sauvegarde des résultats: {e}")
            raise
    
    def get_backtest_results(self, backtest_run_id: int) -> Dict[str, Any]:
        """Récupérer les résultats d'un backtesting"""
        try:
            backtest_run = self.db.query(BacktestRun).filter(
                BacktestRun.id == backtest_run_id
            ).first()
            
            if not backtest_run:
                return {"success": False, "error": f"Backtest run {backtest_run_id} non trouvé"}
            
            # Récupérer les métriques
            metrics = self.db.query(BacktestMetrics).filter(
                BacktestMetrics.backtest_run_id == backtest_run_id
            ).first()
            
            # Récupérer les trades
            trades = self.db.query(BacktestTrade).filter(
                BacktestTrade.backtest_run_id == backtest_run_id
            ).order_by(BacktestTrade.entry_date.asc()).all()
            
            # Récupérer la courbe d'équité
            equity_curve = self.db.query(BacktestEquityCurve).filter(
                BacktestEquityCurve.backtest_run_id == backtest_run_id
            ).order_by(BacktestEquityCurve.date.asc()).all()
            
            return {
                "success": True,
                "backtest_run": {
                    "id": backtest_run.id,
                    "name": backtest_run.name,
                    "description": backtest_run.description,
                    "model_id": backtest_run.model_id,
                    "start_date": backtest_run.start_date.isoformat(),
                    "end_date": backtest_run.end_date.isoformat(),
                    "initial_capital": float(backtest_run.initial_capital),
                    "status": backtest_run.status,
                    "created_at": backtest_run.created_at.isoformat(),
                    "completed_at": backtest_run.completed_at.isoformat() if backtest_run.completed_at else None
                },
                "metrics": self._format_metrics(metrics) if metrics else None,
                "trades": [self._format_trade(trade) for trade in trades],
                "equity_curve": [self._format_equity_point(point) for point in equity_curve]
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des résultats: {e}")
            return {"success": False, "error": str(e)}
    
    def _format_metrics(self, metrics: BacktestMetrics) -> Dict[str, Any]:
        """Formater les métriques pour la réponse API"""
        return {
            "total_return": float(metrics.total_return),
            "annualized_return": float(metrics.annualized_return),
            "total_trades": metrics.total_trades,
            "winning_trades": metrics.winning_trades,
            "losing_trades": metrics.losing_trades,
            "win_rate": float(metrics.win_rate),
            "max_drawdown": float(metrics.max_drawdown),
            "max_drawdown_duration": metrics.max_drawdown_duration,
            "volatility": float(metrics.volatility),
            "sharpe_ratio": float(metrics.sharpe_ratio),
            "sortino_ratio": float(metrics.sortino_ratio),
            "avg_return_per_trade": float(metrics.avg_return_per_trade),
            "avg_winning_trade": float(metrics.avg_winning_trade),
            "avg_losing_trade": float(metrics.avg_losing_trade),
            "profit_factor": float(metrics.profit_factor),
            "avg_holding_period": float(metrics.avg_holding_period),
            "final_capital": float(metrics.final_capital),
            "max_capital": float(metrics.max_capital),
            "min_capital": float(metrics.min_capital),
            "calmar_ratio": float(metrics.calmar_ratio),
            "recovery_factor": float(metrics.recovery_factor),
            "expectancy": float(metrics.expectancy)
        }
    
    def _format_trade(self, trade: BacktestTrade) -> Dict[str, Any]:
        """Formater un trade pour la réponse API"""
        return {
            "id": trade.id,
            "symbol": trade.symbol,
            "entry_date": trade.entry_date.isoformat(),
            "exit_date": trade.exit_date.isoformat(),
            "entry_price": float(trade.entry_price),
            "exit_price": float(trade.exit_price),
            "quantity": trade.quantity,
            "position_type": trade.position_type,
            "entry_confidence": float(trade.entry_confidence),
            "exit_reason": trade.exit_reason,
            "gross_pnl": float(trade.gross_pnl),
            "commission": float(trade.commission),
            "slippage": float(trade.slippage),
            "net_pnl": float(trade.net_pnl),
            "return_percentage": float(trade.return_percentage),
            "holding_days": trade.holding_days
        }
    
    def _format_equity_point(self, point: BacktestEquityCurve) -> Dict[str, Any]:
        """Formater un point de la courbe d'équité pour la réponse API"""
        return {
            "date": point.date.isoformat(),
            "equity_value": float(point.equity_value),
            "drawdown": float(point.drawdown),
            "daily_return": float(point.daily_return),
            "cumulative_return": float(point.cumulative_return)
        }


class TradingSimulator:
    """Simulateur de trading pour le backtesting"""
    
    def __init__(
        self,
        initial_capital: float,
        position_size_percentage: float,
        commission_rate: float,
        slippage_rate: float,
        confidence_threshold: float,
        max_positions: int,
        strategy_id: Optional[int] = None
    ):
        self.initial_capital = initial_capital
        self.position_size_percentage = position_size_percentage
        self.commission_rate = commission_rate
        self.slippage_rate = slippage_rate
        self.confidence_threshold = confidence_threshold
        self.max_positions = max_positions
        self.strategy_id = strategy_id
        
        self.current_capital = initial_capital
        self.positions = {}  # {symbol: position_info}
        self.trades = []
        self.equity_curve = []
        self.strategy_rules = []  # Règles de la stratégie
    
    def run_simulation(
        self, 
        predictions: List[Dict[str, Any]], 
        db: Session
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Exécuter la simulation de trading"""
        try:
            # Charger les règles de stratégie si une stratégie est définie
            if self.strategy_id:
                self._load_strategy_rules(db)
            
            # Grouper les prédictions par date
            predictions_by_date = {}
            for pred in predictions:
                date_key = pred["date"]
                if date_key not in predictions_by_date:
                    predictions_by_date[date_key] = []
                predictions_by_date[date_key].append(pred)
            
            # Traiter chaque jour de trading
            current_date = min(predictions_by_date.keys())
            end_date = max(predictions_by_date.keys())
            
            while current_date <= end_date:
                # Fermer les positions qui doivent être fermées
                self._close_positions(current_date, db)
                
                # Ouvrir de nouvelles positions si possible
                if current_date in predictions_by_date:
                    self._open_positions(predictions_by_date[current_date], current_date, db)
                
                # Mettre à jour la courbe d'équité
                self._update_equity_curve(current_date)
                
                current_date += timedelta(days=1)
            
            # Fermer toutes les positions restantes
            self._close_all_positions(end_date, db)
            
            return self.trades, self.equity_curve
            
        except Exception as e:
            logger.error(f"Erreur lors de la simulation de trading: {e}")
            raise
    
    def _load_strategy_rules(self, db: Session):
        """Charger les règles de stratégie depuis la base de données"""
        try:
            rules = db.query(StrategyRule).filter(
                StrategyRule.strategy_id == self.strategy_id,
                StrategyRule.is_active == True
            ).order_by(StrategyRule.priority.asc()).all()
            
            self.strategy_rules = [
                {
                    "id": rule.id,
                    "rule_type": rule.rule_type,
                    "rule_name": rule.rule_name,
                    "rule_condition": rule.rule_condition,
                    "rule_action": rule.rule_action,
                    "priority": rule.priority
                }
                for rule in rules
            ]
            
            logger.info(f"Chargé {len(self.strategy_rules)} règles de stratégie")
            
        except Exception as e:
            logger.error(f"Erreur lors du chargement des règles de stratégie: {e}")
            self.strategy_rules = []
    
    def _open_positions(
        self, 
        predictions: List[Dict[str, Any]], 
        current_date: date, 
        db: Session
    ):
        """Ouvrir de nouvelles positions basées sur les prédictions et les règles de stratégie"""
        logger.info(f"Ouverture positions pour {len(predictions)} prédictions le {current_date}")
        logger.info(f"Seuil de confiance: {self.confidence_threshold}")
        
        # Filtrer les prédictions par seuil de confiance
        valid_predictions = [
            p for p in predictions 
            if p["confidence"] >= self.confidence_threshold
        ]
        
        logger.info(f"Prédictions valides après filtre confiance: {len(valid_predictions)}")
        logger.info(f"Prédictions valides: {valid_predictions}")
        
        # Trier par confiance décroissante
        valid_predictions.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Ouvrir des positions jusqu'à la limite
        for pred in valid_predictions:
            if len(self.positions) >= self.max_positions:
                logger.info(f"Limite de positions atteinte ({self.max_positions})")
                break
            
            if pred["symbol"] not in self.positions:
                logger.info(f"Tentative d'ouverture position pour {pred['symbol']}")
                # Appliquer les règles de stratégie pour l'entrée
                if self._should_open_position(pred, current_date, db):
                    logger.info(f"Ouverture position confirmée pour {pred['symbol']}")
                    self._open_position(pred, current_date, db)
                else:
                    logger.info(f"Position refusée par les règles de stratégie pour {pred['symbol']}")
    
    def _should_open_position(
        self, 
        prediction: Dict[str, Any], 
        current_date: date, 
        db: Session
    ) -> bool:
        """Évaluer si une position doit être ouverte selon les règles de stratégie"""
        if not self.strategy_rules:
            # Pas de stratégie définie, utiliser la logique par défaut
            return True
        
        # Récupérer les règles d'entrée
        entry_rules = [rule for rule in self.strategy_rules if rule["rule_type"] == "entry"]
        
        if not entry_rules:
            return True
        
        # Évaluer chaque règle d'entrée
        for rule in entry_rules:
            if self._evaluate_rule_condition(rule, prediction, current_date, db):
                return True
        
        return False
    
    def _evaluate_rule_condition(
        self, 
        rule: Dict[str, Any], 
        prediction: Dict[str, Any], 
        current_date: date, 
        db: Session
    ) -> bool:
        """Évaluer une condition de règle"""
        try:
            condition = rule["rule_condition"]
            
            # Récupérer les données nécessaires pour l'évaluation
            symbol = prediction["symbol"]
            confidence = prediction["confidence"]
            
            # Récupérer les données historiques pour les calculs
            price_data = db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol,
                HistoricalData.date <= current_date
            ).order_by(HistoricalData.date.desc()).limit(20).all()
            
            if not price_data:
                return False
            
            # Calculer les métriques nécessaires
            current_price = float(price_data[0].close)
            prices = [float(p.close) for p in price_data]
            
            # Calculs basiques
            price_change_20d = (current_price - prices[-1]) / prices[-1] if len(prices) > 1 else 0
            avg_volume = sum(p.volume for p in price_data) / len(price_data)
            current_volume = price_data[0].volume
            
            # Variables disponibles pour l'évaluation des conditions
            context = {
                "confidence": confidence,
                "current_price": current_price,
                "price_change_20d": price_change_20d,
                "volume": current_volume,
                "avg_volume": avg_volume,
                "momentum_threshold": 0.05,
                "oversold_threshold": -0.10,
                "overbought_threshold": 0.10,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "breakout_threshold": 0.02,
                "volume_multiplier": 1.5
            }
            
            # Évaluation simple des conditions (dans une implémentation complète, 
            # on utiliserait un moteur d'expression plus sophistiqué)
            if "confidence >" in condition:
                threshold = float(condition.split("confidence >")[1].strip())
                return confidence > threshold
            
            elif "price_change_20d >" in condition:
                threshold = float(condition.split("price_change_20d >")[1].strip())
                return price_change_20d > threshold
            
            elif "volume >" in condition and "avg_volume" in condition:
                multiplier = float(condition.split("volume_multiplier")[1].split()[0])
                return current_volume > avg_volume * multiplier
            
            # Condition par défaut pour les règles simples
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation de la condition: {e}")
            return False
    
    def _open_position(
        self, 
        prediction: Dict[str, Any], 
        current_date: date, 
        db: Session
    ):
        """Ouvrir une position pour un symbole"""
        try:
            symbol = prediction["symbol"]
            
            # Récupérer le prix d'ouverture du jour
            price_data = db.query(HistoricalData).filter(
                and_(
                    HistoricalData.symbol == symbol,
                    HistoricalData.date == current_date
                )
            ).first()
            
            if not price_data:
                logger.warning(f"Pas de données de prix pour {symbol} le {current_date}")
                return
            
            # Calculer la taille de la position selon les règles de stratégie
            position_size = self._calculate_position_size(prediction, current_date, db)
            position_value = self.current_capital * position_size
            quantity = int(position_value / float(price_data.open))
            
            if quantity <= 0:
                return
            
            # Calculer les coûts
            entry_price = float(price_data.open) * (1 + self.slippage_rate)
            total_cost = entry_price * quantity
            commission = total_cost * self.commission_rate
            
            # Vérifier que nous avons assez de capital
            if total_cost + commission > self.current_capital:
                return
            
            # Ouvrir la position
            self.positions[symbol] = {
                "entry_date": current_date,
                "entry_price": entry_price,
                "quantity": quantity,
                "confidence": prediction["confidence"],
                "total_cost": total_cost,
                "commission": commission
            }
            
            self.current_capital -= (total_cost + commission)
            
            logger.debug(f"Position ouverte: {symbol} - {quantity} @ {entry_price}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture de position pour {prediction['symbol']}: {e}")
    
    def _calculate_position_size(
        self, 
        prediction: Dict[str, Any], 
        current_date: date, 
        db: Session
    ) -> float:
        """Calculer la taille de position selon les règles de stratégie"""
        if not self.strategy_rules:
            return self.position_size_percentage / 100
        
        # Récupérer les règles de sizing
        sizing_rules = [rule for rule in self.strategy_rules if rule["rule_type"] == "position_sizing"]
        
        if not sizing_rules:
            return self.position_size_percentage / 100
        
        # Évaluer les règles de sizing par ordre de priorité
        for rule in sorted(sizing_rules, key=lambda x: x["priority"]):
            if self._evaluate_rule_condition(rule, prediction, current_date, db):
                # Extraire la taille de position de l'action
                action = rule["rule_action"]
                if "position_size =" in action:
                    size_str = action.split("position_size =")[1].strip()
                    try:
                        return float(size_str)
                    except ValueError:
                        continue
        
        # Taille par défaut
        return self.position_size_percentage / 100
    
    def _should_close_position(
        self, 
        position: Dict[str, Any], 
        exit_price: float, 
        holding_days: int
    ) -> Tuple[bool, str]:
        """Évaluer si une position doit être fermée selon les règles de stratégie"""
        if not self.strategy_rules:
            # Logique par défaut
            if holding_days >= 7:
                return True, "timeout"
            elif exit_price >= position["entry_price"] * 1.05:
                return True, "target_hit"
            elif exit_price <= position["entry_price"] * 0.95:
                return True, "stop_loss"
            return False, ""
        
        # Récupérer les règles de sortie
        exit_rules = [rule for rule in self.strategy_rules if rule["rule_type"] == "exit"]
        
        if not exit_rules:
            return False, ""
        
        # Évaluer les règles de sortie par ordre de priorité
        for rule in sorted(exit_rules, key=lambda x: x["priority"]):
            if self._evaluate_exit_rule(rule, position, exit_price, holding_days):
                return True, rule["rule_name"].lower().replace(" ", "_")
        
        return False, ""
    
    def _evaluate_exit_rule(
        self, 
        rule: Dict[str, Any], 
        position: Dict[str, Any], 
        exit_price: float, 
        holding_days: int
    ) -> bool:
        """Évaluer une règle de sortie spécifique"""
        try:
            condition = rule["rule_condition"]
            entry_price = position["entry_price"]
            current_return = (exit_price - entry_price) / entry_price
            
            # Évaluation simple des conditions de sortie
            if "current_return >" in condition:
                threshold = float(condition.split("current_return >")[1].strip())
                return current_return > threshold
            
            elif "current_return <" in condition:
                threshold = float(condition.split("current_return <")[1].strip())
                return current_return < threshold
            
            elif "holding_days >=" in condition:
                threshold = int(condition.split("holding_days >=")[1].strip())
                return holding_days >= threshold
            
            elif "price <" in condition and "entry_price" in condition:
                multiplier = float(condition.split("entry_price *")[1].strip())
                return exit_price < entry_price * multiplier
            
            # Condition par défaut
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation de la règle de sortie: {e}")
            return False
    
    def _close_positions(self, current_date: date, db: Session):
        """Fermer les positions selon les critères de sortie"""
        positions_to_close = []
        
        for symbol, position in self.positions.items():
            # Récupérer le prix de clôture du jour
            price_data = db.query(HistoricalData).filter(
                and_(
                    HistoricalData.symbol == symbol,
                    HistoricalData.date == current_date
                )
            ).first()
            
            if not price_data:
                continue
            
            exit_price = float(price_data.close) * (1 - self.slippage_rate)
            holding_days = (current_date - position["entry_date"]).days
            
            # Critères de sortie selon les règles de stratégie
            should_exit, exit_reason = self._should_close_position(position, exit_price, holding_days)
            
            if should_exit:
                positions_to_close.append((symbol, exit_price, exit_reason))
        
        # Fermer les positions
        for symbol, exit_price, exit_reason in positions_to_close:
            self._close_position(symbol, exit_price, exit_reason, current_date)
    
    def _close_position(
        self, 
        symbol: str, 
        exit_price: float, 
        exit_reason: str, 
        exit_date: date
    ):
        """Fermer une position"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # Calculer le P&L
        gross_pnl = (exit_price - position["entry_price"]) * position["quantity"]
        exit_value = exit_price * position["quantity"]
        commission = exit_value * self.commission_rate
        slippage_cost = exit_value * self.slippage_rate
        net_pnl = gross_pnl - commission - slippage_cost
        
        # Calculer le pourcentage de retour
        return_percentage = (net_pnl / position["total_cost"]) * 100
        
        # Créer l'enregistrement de trade
        trade = {
            "symbol": symbol,
            "entry_date": position["entry_date"],
            "exit_date": exit_date,
            "entry_price": position["entry_price"],
            "exit_price": exit_price,
            "quantity": position["quantity"],
            "position_type": "long",
            "entry_confidence": position["confidence"],
            "exit_reason": exit_reason,
            "gross_pnl": gross_pnl,
            "commission": commission,
            "slippage": slippage_cost,
            "net_pnl": net_pnl,
            "return_percentage": return_percentage,
            "holding_days": (exit_date - position["entry_date"]).days
        }
        
        self.trades.append(trade)
        
        # Mettre à jour le capital
        self.current_capital += exit_value - commission - slippage_cost
        
        # Supprimer la position
        del self.positions[symbol]
        
        logger.debug(f"Position fermée: {symbol} - P&L: {net_pnl:.2f}")
    
    def _close_all_positions(self, end_date: date, db: Session):
        """Fermer toutes les positions restantes à la fin du backtesting"""
        for symbol in list(self.positions.keys()):
            # Récupérer le dernier prix disponible
            price_data = db.query(HistoricalData).filter(
                and_(
                    HistoricalData.symbol == symbol,
                    HistoricalData.date <= end_date
                )
            ).order_by(desc(HistoricalData.date)).first()
            
            if price_data:
                exit_price = float(price_data.close) * (1 - self.slippage_rate)
                self._close_position(symbol, exit_price, "end_of_period", end_date)
    
    def _update_equity_curve(self, current_date: date):
        """Mettre à jour la courbe d'équité"""
        # Calculer la valeur totale des positions ouvertes
        positions_value = 0
        for position in self.positions.values():
            # Estimation basique de la valeur actuelle (utiliser le prix d'entrée pour simplifier)
            positions_value += position["total_cost"]
        
        total_equity = self.current_capital + positions_value
        
        # Calculer le drawdown
        if not self.equity_curve:
            max_equity = self.initial_capital
        else:
            max_equity = max(point["equity_value"] for point in self.equity_curve)
        
        drawdown = ((max_equity - total_equity) / max_equity) * 100 if max_equity > 0 else 0
        
        # Calculer le retour quotidien
        if not self.equity_curve:
            daily_return = 0
            cumulative_return = 0
        else:
            previous_equity = self.equity_curve[-1]["equity_value"]
            daily_return = ((total_equity - previous_equity) / previous_equity) * 100 if previous_equity > 0 else 0
            cumulative_return = ((total_equity - self.initial_capital) / self.initial_capital) * 100
        
        equity_point = {
            "date": current_date,
            "equity_value": total_equity,
            "drawdown": drawdown,
            "daily_return": daily_return,
            "cumulative_return": cumulative_return
        }
        
        self.equity_curve.append(equity_point)


class MetricsCalculator:
    """Calculateur de métriques de performance"""
    
    def calculate_metrics(
        self, 
        trades: List[Dict[str, Any]], 
        equity_curve: List[Dict[str, Any]], 
        backtest_run: BacktestRun
    ) -> Dict[str, Any]:
        """Calculer toutes les métriques de performance"""
        try:
            if not trades:
                return self._get_empty_metrics(backtest_run)
            
            # Métriques de base
            total_trades = len(trades)
            winning_trades = len([t for t in trades if t["net_pnl"] > 0])
            losing_trades = total_trades - winning_trades
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            # Métriques de retour
            initial_capital = float(backtest_run.initial_capital)
            final_capital = equity_curve[-1]["equity_value"] if equity_curve else initial_capital
            total_return = ((final_capital - initial_capital) / initial_capital) * 100
            
            # Calculer le retour annualisé
            days = (backtest_run.end_date - backtest_run.start_date).days
            annualized_return = ((final_capital / initial_capital) ** (365 / days) - 1) * 100 if days > 0 else 0
            
            # Métriques de risque
            max_drawdown, max_drawdown_duration = self._calculate_max_drawdown(equity_curve)
            volatility = self._calculate_volatility(equity_curve)
            
            # Métriques de trade
            avg_return_per_trade = np.mean([t["return_percentage"] for t in trades])
            avg_winning_trade = np.mean([t["return_percentage"] for t in trades if t["net_pnl"] > 0]) if winning_trades > 0 else 0
            avg_losing_trade = np.mean([t["return_percentage"] for t in trades if t["net_pnl"] < 0]) if losing_trades > 0 else 0
            
            # Profit factor
            gross_profit = sum(t["net_pnl"] for t in trades if t["net_pnl"] > 0)
            gross_loss = abs(sum(t["net_pnl"] for t in trades if t["net_pnl"] < 0))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 999999.0  # Limiter à une grande valeur
            
            # Période de détention moyenne
            avg_holding_period = np.mean([t["holding_days"] for t in trades])
            
            # Métriques de capital
            max_capital = max(point["equity_value"] for point in equity_curve) if equity_curve else initial_capital
            min_capital = min(point["equity_value"] for point in equity_curve) if equity_curve else initial_capital
            
            # Ratios avancés
            sharpe_ratio = self._calculate_sharpe_ratio(equity_curve, annualized_return)
            sortino_ratio = self._calculate_sortino_ratio(equity_curve, annualized_return)
            calmar_ratio = annualized_return / max_drawdown if max_drawdown > 0 else 999999.0  # Limiter à une grande valeur
            recovery_factor = (final_capital - initial_capital) / (initial_capital * max_drawdown / 100) if max_drawdown > 0 else 999999.0  # Limiter à une grande valeur
            expectancy = avg_return_per_trade
            
            return {
                "total_return": total_return,
                "annualized_return": annualized_return,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": win_rate,
                "max_drawdown": max_drawdown,
                "max_drawdown_duration": max_drawdown_duration,
                "volatility": volatility,
                "sharpe_ratio": sharpe_ratio,
                "sortino_ratio": sortino_ratio,
                "avg_return_per_trade": avg_return_per_trade,
                "avg_winning_trade": avg_winning_trade,
                "avg_losing_trade": avg_losing_trade,
                "profit_factor": profit_factor,
                "avg_holding_period": avg_holding_period,
                "final_capital": final_capital,
                "max_capital": max_capital,
                "min_capital": min_capital,
                "calmar_ratio": calmar_ratio,
                "recovery_factor": recovery_factor,
                "expectancy": expectancy
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des métriques: {e}")
            return self._get_empty_metrics(backtest_run)
    
    def _get_empty_metrics(self, backtest_run: BacktestRun) -> Dict[str, Any]:
        """Retourner des métriques vides en cas d'erreur"""
        initial_capital = float(backtest_run.initial_capital)
        return {
            "total_return": 0,
            "annualized_return": 0,
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "max_drawdown": 0,
            "max_drawdown_duration": 0,
            "volatility": 0,
            "sharpe_ratio": 0,
            "sortino_ratio": 0,
            "avg_return_per_trade": 0,
            "avg_winning_trade": 0,
            "avg_losing_trade": 0,
            "profit_factor": 0,
            "avg_holding_period": 0,
            "final_capital": initial_capital,
            "max_capital": initial_capital,
            "min_capital": initial_capital,
            "calmar_ratio": 0,
            "recovery_factor": 0,
            "expectancy": 0
        }
    
    def _calculate_max_drawdown(self, equity_curve: List[Dict[str, Any]]) -> Tuple[float, int]:
        """Calculer le drawdown maximum et sa durée"""
        if not equity_curve:
            return 0, 0
        
        max_equity = equity_curve[0]["equity_value"]
        max_drawdown = 0
        max_drawdown_duration = 0
        current_drawdown_duration = 0
        
        for point in equity_curve:
            if point["equity_value"] > max_equity:
                max_equity = point["equity_value"]
                current_drawdown_duration = 0
            else:
                drawdown = ((max_equity - point["equity_value"]) / max_equity) * 100
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                
                current_drawdown_duration += 1
                if current_drawdown_duration > max_drawdown_duration:
                    max_drawdown_duration = current_drawdown_duration
        
        return max_drawdown, max_drawdown_duration
    
    def _calculate_volatility(self, equity_curve: List[Dict[str, Any]]) -> float:
        """Calculer la volatilité annualisée"""
        if len(equity_curve) < 2:
            return 0
        
        returns = [point["daily_return"] for point in equity_curve[1:]]
        return np.std(returns) * np.sqrt(252) * 100  # Annualisé
    
    def _calculate_sharpe_ratio(self, equity_curve: List[Dict[str, Any]], annualized_return: float) -> float:
        """Calculer le ratio de Sharpe"""
        if len(equity_curve) < 2:
            return 0
        
        returns = [point["daily_return"] for point in equity_curve[1:]]
        volatility = np.std(returns) * np.sqrt(252) * 100
        
        if volatility == 0:
            return 0
        
        # Supposer un taux sans risque de 2%
        risk_free_rate = 2.0
        return (annualized_return - risk_free_rate) / volatility
    
    def _calculate_sortino_ratio(self, equity_curve: List[Dict[str, Any]], annualized_return: float) -> float:
        """Calculer le ratio de Sortino"""
        if len(equity_curve) < 2:
            return 0
        
        returns = [point["daily_return"] for point in equity_curve[1:]]
        negative_returns = [r for r in returns if r < 0]
        
        if not negative_returns:
            return 999999.0  # Limiter à une grande valeur
        
        downside_deviation = np.std(negative_returns) * np.sqrt(252) * 100
        
        if downside_deviation == 0:
            return 0
        
        # Supposer un taux sans risque de 2%
        risk_free_rate = 2.0
        return (annualized_return - risk_free_rate) / downside_deviation
