"""
Service de Gestion des Stratégies de Trading
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
import json
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from ..models.database import (
    TradingStrategy, StrategyRule, StrategyParameter, StrategyPerformance,
    BacktestRun, BacktestMetrics
)

logger = logging.getLogger(__name__)


class TradingStrategyService:
    """Service principal pour la gestion des stratégies de trading"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_strategy(
        self,
        name: str,
        description: str,
        strategy_type: str,
        parameters: Dict[str, Any],
        rules: List[Dict[str, Any]],
        created_by: str = "system"
    ) -> Dict[str, Any]:
        """Créer une nouvelle stratégie de trading"""
        try:
            # Vérifier que le nom est unique
            existing_strategy = self.db.query(TradingStrategy).filter(
                TradingStrategy.name == name
            ).first()
            
            if existing_strategy:
                return {"success": False, "error": f"Une stratégie avec le nom '{name}' existe déjà"}
            
            # Créer la stratégie
            strategy = TradingStrategy(
                name=name,
                description=description,
                strategy_type=strategy_type,
                parameters=parameters,
                is_active=True,
                created_by=created_by
            )
            
            self.db.add(strategy)
            self.db.flush()  # Pour obtenir l'ID
            
            # Créer les règles
            for rule_data in rules:
                rule = StrategyRule(
                    strategy_id=strategy.id,
                    rule_type=rule_data["rule_type"],
                    rule_name=rule_data["rule_name"],
                    rule_condition=rule_data["rule_condition"],
                    rule_action=rule_data["rule_action"],
                    priority=rule_data.get("priority", 1),
                    is_active=True
                )
                self.db.add(rule)
            
            self.db.commit()
            self.db.refresh(strategy)
            
            logger.info(f"Stratégie créée: {strategy.id} - {name}")
            
            return {
                "success": True,
                "strategy_id": strategy.id,
                "message": "Stratégie créée avec succès"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la création de la stratégie: {e}")
            return {"success": False, "error": str(e)}
    
    def get_strategy(self, strategy_id: int) -> Dict[str, Any]:
        """Récupérer une stratégie avec ses règles et paramètres"""
        try:
            strategy = self.db.query(TradingStrategy).filter(
                TradingStrategy.id == strategy_id
            ).first()
            
            if not strategy:
                return {"success": False, "error": f"Stratégie {strategy_id} non trouvée"}
            
            # Récupérer les règles
            rules = self.db.query(StrategyRule).filter(
                StrategyRule.strategy_id == strategy_id,
                StrategyRule.is_active == True
            ).order_by(StrategyRule.priority.asc()).all()
            
            # Récupérer les paramètres
            parameters = self.db.query(StrategyParameter).filter(
                StrategyParameter.strategy_id == strategy_id
            ).all()
            
            return {
                "success": True,
                "strategy": {
                    "id": strategy.id,
                    "name": strategy.name,
                    "description": strategy.description,
                    "strategy_type": strategy.strategy_type,
                    "parameters": strategy.parameters,
                    "is_active": strategy.is_active,
                    "created_by": strategy.created_by,
                    "created_at": strategy.created_at.isoformat(),
                    "updated_at": strategy.updated_at.isoformat() if strategy.updated_at else None
                },
                "rules": [
                    {
                        "id": rule.id,
                        "rule_type": rule.rule_type,
                        "rule_name": rule.rule_name,
                        "rule_condition": rule.rule_condition,
                        "rule_action": rule.rule_action,
                        "priority": rule.priority,
                        "is_active": rule.is_active
                    }
                    for rule in rules
                ],
                "parameters": [
                    {
                        "id": param.id,
                        "parameter_name": param.parameter_name,
                        "parameter_type": param.parameter_type,
                        "default_value": param.default_value,
                        "min_value": float(param.min_value) if param.min_value else None,
                        "max_value": float(param.max_value) if param.max_value else None,
                        "choices": param.choices,
                        "description": param.description,
                        "is_required": param.is_required
                    }
                    for param in parameters
                ]
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la stratégie: {e}")
            return {"success": False, "error": str(e)}
    
    def get_strategies(
        self,
        skip: int = 0,
        limit: int = 100,
        strategy_type: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Récupérer la liste des stratégies"""
        try:
            query = self.db.query(TradingStrategy)
            
            # Filtres optionnels
            if strategy_type:
                query = query.filter(TradingStrategy.strategy_type == strategy_type)
            if is_active is not None:
                query = query.filter(TradingStrategy.is_active == is_active)
            
            # Pagination et tri
            strategies = query.order_by(TradingStrategy.created_at.desc()).offset(skip).limit(limit).all()
            
            return {
                "success": True,
                "strategies": [
                    {
                        "id": strategy.id,
                        "name": strategy.name,
                        "description": strategy.description,
                        "strategy_type": strategy.strategy_type,
                        "is_active": strategy.is_active,
                        "created_by": strategy.created_by,
                        "created_at": strategy.created_at.isoformat(),
                        "updated_at": strategy.updated_at.isoformat() if strategy.updated_at else None
                    }
                    for strategy in strategies
                ],
                "total": query.count()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des stratégies: {e}")
            return {"success": False, "error": str(e)}
    
    def update_strategy(
        self,
        strategy_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        strategy_type: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Mettre à jour une stratégie"""
        try:
            strategy = self.db.query(TradingStrategy).filter(
                TradingStrategy.id == strategy_id
            ).first()
            
            if not strategy:
                return {"success": False, "error": f"Stratégie {strategy_id} non trouvée"}
            
            # Mettre à jour les champs fournis
            if name is not None:
                # Vérifier l'unicité du nom
                existing = self.db.query(TradingStrategy).filter(
                    TradingStrategy.name == name,
                    TradingStrategy.id != strategy_id
                ).first()
                if existing:
                    return {"success": False, "error": f"Une stratégie avec le nom '{name}' existe déjà"}
                strategy.name = name
            
            if description is not None:
                strategy.description = description
            if strategy_type is not None:
                strategy.strategy_type = strategy_type
            if parameters is not None:
                strategy.parameters = parameters
            if is_active is not None:
                strategy.is_active = is_active
            
            strategy.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            logger.info(f"Stratégie mise à jour: {strategy_id}")
            
            return {
                "success": True,
                "message": "Stratégie mise à jour avec succès"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la mise à jour de la stratégie: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_strategy(self, strategy_id: int) -> Dict[str, Any]:
        """Supprimer une stratégie"""
        try:
            strategy = self.db.query(TradingStrategy).filter(
                TradingStrategy.id == strategy_id
            ).first()
            
            if not strategy:
                return {"success": False, "error": f"Stratégie {strategy_id} non trouvée"}
            
            # Vérifier s'il y a des backtests associés
            backtests = self.db.query(BacktestRun).filter(
                BacktestRun.strategy_id == strategy_id
            ).count()
            
            if backtests > 0:
                return {
                    "success": False,
                    "error": f"Impossible de supprimer la stratégie: {backtests} backtest(s) associé(s)"
                }
            
            # Supprimer les règles et paramètres associés
            self.db.query(StrategyRule).filter(StrategyRule.strategy_id == strategy_id).delete()
            self.db.query(StrategyParameter).filter(StrategyParameter.strategy_id == strategy_id).delete()
            
            # Supprimer la stratégie
            self.db.delete(strategy)
            self.db.commit()
            
            logger.info(f"Stratégie supprimée: {strategy_id}")
            
            return {
                "success": True,
                "message": "Stratégie supprimée avec succès"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la suppression de la stratégie: {e}")
            return {"success": False, "error": str(e)}
    
    def add_strategy_rule(
        self,
        strategy_id: int,
        rule_type: str,
        rule_name: str,
        rule_condition: str,
        rule_action: str,
        priority: int = 1
    ) -> Dict[str, Any]:
        """Ajouter une règle à une stratégie"""
        try:
            # Vérifier que la stratégie existe
            strategy = self.db.query(TradingStrategy).filter(
                TradingStrategy.id == strategy_id
            ).first()
            
            if not strategy:
                return {"success": False, "error": f"Stratégie {strategy_id} non trouvée"}
            
            # Créer la règle
            rule = StrategyRule(
                strategy_id=strategy_id,
                rule_type=rule_type,
                rule_name=rule_name,
                rule_condition=rule_condition,
                rule_action=rule_action,
                priority=priority,
                is_active=True
            )
            
            self.db.add(rule)
            self.db.commit()
            self.db.refresh(rule)
            
            logger.info(f"Règle ajoutée à la stratégie {strategy_id}: {rule_name}")
            
            return {
                "success": True,
                "rule_id": rule.id,
                "message": "Règle ajoutée avec succès"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de l'ajout de la règle: {e}")
            return {"success": False, "error": str(e)}
    
    def update_strategy_rule(
        self,
        rule_id: int,
        rule_type: Optional[str] = None,
        rule_name: Optional[str] = None,
        rule_condition: Optional[str] = None,
        rule_action: Optional[str] = None,
        priority: Optional[int] = None,
        is_active: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Mettre à jour une règle de stratégie"""
        try:
            rule = self.db.query(StrategyRule).filter(
                StrategyRule.id == rule_id
            ).first()
            
            if not rule:
                return {"success": False, "error": f"Règle {rule_id} non trouvée"}
            
            # Mettre à jour les champs fournis
            if rule_type is not None:
                rule.rule_type = rule_type
            if rule_name is not None:
                rule.rule_name = rule_name
            if rule_condition is not None:
                rule.rule_condition = rule_condition
            if rule_action is not None:
                rule.rule_action = rule_action
            if priority is not None:
                rule.priority = priority
            if is_active is not None:
                rule.is_active = is_active
            
            self.db.commit()
            
            logger.info(f"Règle mise à jour: {rule_id}")
            
            return {
                "success": True,
                "message": "Règle mise à jour avec succès"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la mise à jour de la règle: {e}")
            return {"success": False, "error": str(e)}
    
    def delete_strategy_rule(self, rule_id: int) -> Dict[str, Any]:
        """Supprimer une règle de stratégie"""
        try:
            rule = self.db.query(StrategyRule).filter(
                StrategyRule.id == rule_id
            ).first()
            
            if not rule:
                return {"success": False, "error": f"Règle {rule_id} non trouvée"}
            
            self.db.delete(rule)
            self.db.commit()
            
            logger.info(f"Règle supprimée: {rule_id}")
            
            return {
                "success": True,
                "message": "Règle supprimée avec succès"
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Erreur lors de la suppression de la règle: {e}")
            return {"success": False, "error": str(e)}
    
    def get_strategy_performance(self, strategy_id: int) -> Dict[str, Any]:
        """Récupérer les performances d'une stratégie"""
        try:
            # Récupérer les performances
            performances = self.db.query(StrategyPerformance).filter(
                StrategyPerformance.strategy_id == strategy_id
            ).order_by(StrategyPerformance.created_at.desc()).all()
            
            if not performances:
                return {
                    "success": True,
                    "performances": [],
                    "message": "Aucune performance trouvée pour cette stratégie"
                }
            
            # Calculer les statistiques globales
            total_performances = len(performances)
            avg_score = sum(float(p.strategy_score) for p in performances) / total_performances
            avg_alpha = sum(float(p.alpha) for p in performances if p.alpha) / len([p for p in performances if p.alpha])
            avg_beta = sum(float(p.beta) for p in performances if p.beta) / len([p for p in performances if p.beta])
            
            return {
                "success": True,
                "performances": [
                    {
                        "id": perf.id,
                        "backtest_run_id": perf.backtest_run_id,
                        "strategy_score": float(perf.strategy_score),
                        "rule_effectiveness": perf.rule_effectiveness,
                        "parameter_sensitivity": perf.parameter_sensitivity,
                        "market_conditions": perf.market_conditions,
                        "benchmark_return": float(perf.benchmark_return) if perf.benchmark_return else None,
                        "alpha": float(perf.alpha) if perf.alpha else None,
                        "beta": float(perf.beta) if perf.beta else None,
                        "information_ratio": float(perf.information_ratio) if perf.information_ratio else None,
                        "created_at": perf.created_at.isoformat()
                    }
                    for perf in performances
                ],
                "statistics": {
                    "total_backtests": total_performances,
                    "average_score": avg_score,
                    "average_alpha": avg_alpha if avg_alpha else 0,
                    "average_beta": avg_beta if avg_beta else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des performances: {e}")
            return {"success": False, "error": str(e)}
    
    def evaluate_strategy_rules(
        self,
        strategy_id: int,
        trades: List[Dict[str, Any]],
        equity_curve: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Évaluer l'efficacité des règles d'une stratégie"""
        try:
            # Récupérer les règles de la stratégie
            rules = self.db.query(StrategyRule).filter(
                StrategyRule.strategy_id == strategy_id,
                StrategyRule.is_active == True
            ).order_by(StrategyRule.priority.asc()).all()
            
            if not rules:
                return {"success": False, "error": "Aucune règle active trouvée pour cette stratégie"}
            
            rule_effectiveness = {}
            
            for rule in rules:
                effectiveness = self._evaluate_rule_effectiveness(rule, trades, equity_curve)
                rule_effectiveness[rule.rule_name] = effectiveness
            
            return {
                "success": True,
                "rule_effectiveness": rule_effectiveness
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation des règles: {e}")
            return {"success": False, "error": str(e)}
    
    def _evaluate_rule_effectiveness(
        self,
        rule: StrategyRule,
        trades: List[Dict[str, Any]],
        equity_curve: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Évaluer l'efficacité d'une règle spécifique"""
        try:
            # Logique d'évaluation basique
            # Dans une implémentation complète, on analyserait chaque trade
            # pour voir si la règle a été appliquée correctement
            
            if rule.rule_type == "entry":
                # Analyser les entrées réussies
                successful_entries = len([t for t in trades if t["net_pnl"] > 0])
                total_entries = len(trades)
                success_rate = (successful_entries / total_entries) * 100 if total_entries > 0 else 0
                
                return {
                    "rule_type": rule.rule_type,
                    "success_rate": success_rate,
                    "total_applications": total_entries,
                    "successful_applications": successful_entries,
                    "effectiveness_score": success_rate / 100
                }
            
            elif rule.rule_type == "exit":
                # Analyser les sorties
                profitable_exits = len([t for t in trades if t["net_pnl"] > 0])
                total_exits = len(trades)
                profitability_rate = (profitable_exits / total_exits) * 100 if total_exits > 0 else 0
                
                return {
                    "rule_type": rule.rule_type,
                    "profitability_rate": profitability_rate,
                    "total_applications": total_exits,
                    "profitable_applications": profitable_exits,
                    "effectiveness_score": profitability_rate / 100
                }
            
            elif rule.rule_type == "position_sizing":
                # Analyser la gestion de la taille des positions
                avg_position_size = sum(t["quantity"] for t in trades) / len(trades) if trades else 0
                position_consistency = 1.0 - (len(set(t["quantity"] for t in trades)) / len(trades)) if trades else 0
                
                return {
                    "rule_type": rule.rule_type,
                    "average_position_size": avg_position_size,
                    "position_consistency": position_consistency,
                    "effectiveness_score": position_consistency
                }
            
            elif rule.rule_type == "risk_management":
                # Analyser la gestion des risques
                max_loss = min(t["net_pnl"] for t in trades) if trades else 0
                avg_loss = sum(t["net_pnl"] for t in trades if t["net_pnl"] < 0) / len([t for t in trades if t["net_pnl"] < 0]) if any(t["net_pnl"] < 0 for t in trades) else 0
                
                return {
                    "rule_type": rule.rule_type,
                    "max_loss": max_loss,
                    "average_loss": avg_loss,
                    "risk_control_score": 1.0 if max_loss > -1000 else 0.5,  # Score basique
                    "effectiveness_score": 0.8  # Score par défaut
                }
            
            else:
                return {
                    "rule_type": rule.rule_type,
                    "effectiveness_score": 0.5  # Score par défaut
                }
                
        except Exception as e:
            logger.error(f"Erreur lors de l'évaluation de la règle {rule.id}: {e}")
            return {
                "rule_type": rule.rule_type,
                "effectiveness_score": 0.0,
                "error": str(e)
            }
