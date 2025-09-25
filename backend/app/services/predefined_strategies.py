"""
Stratégies de Trading Prédéfinies
"""

from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class PredefinedStrategies:
    """Collection de stratégies de trading prédéfinies"""
    
    @staticmethod
    def get_momentum_strategy() -> Dict[str, Any]:
        """Stratégie Momentum - Suit les tendances"""
        return {
            "name": "Momentum Strategy",
            "description": "Stratégie qui suit les tendances en achetant les actifs en hausse et en vendant ceux en baisse",
            "strategy_type": "momentum",
            "parameters": {
                "lookback_period": 20,
                "momentum_threshold": 0.05,
                "stop_loss_percentage": 0.05,
                "take_profit_percentage": 0.10,
                "max_holding_period": 10
            },
            "rules": [
                {
                    "rule_type": "entry",
                    "rule_name": "Momentum Entry",
                    "rule_condition": "price_change_20d > momentum_threshold AND confidence > 0.7",
                    "rule_action": "BUY",
                    "priority": 1
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Take Profit",
                    "rule_condition": "current_return > take_profit_percentage",
                    "rule_action": "SELL",
                    "priority": 1
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Stop Loss",
                    "rule_condition": "current_return < -stop_loss_percentage",
                    "rule_action": "SELL",
                    "priority": 2
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Timeout Exit",
                    "rule_condition": "holding_days >= max_holding_period",
                    "rule_action": "SELL",
                    "priority": 3
                },
                {
                    "rule_type": "position_sizing",
                    "rule_name": "Fixed Position Size",
                    "rule_condition": "confidence > 0.8",
                    "rule_action": "position_size = 0.15",
                    "priority": 1
                },
                {
                    "rule_type": "position_sizing",
                    "rule_name": "Reduced Position Size",
                    "rule_condition": "confidence <= 0.8",
                    "rule_action": "position_size = 0.10",
                    "priority": 2
                }
            ]
        }
    
    @staticmethod
    def get_mean_reversion_strategy() -> Dict[str, Any]:
        """Stratégie Mean Reversion - Contre-tendance"""
        return {
            "name": "Mean Reversion Strategy",
            "description": "Stratégie qui anticipe un retour à la moyenne des prix après des mouvements extrêmes",
            "strategy_type": "mean_reversion",
            "parameters": {
                "lookback_period": 20,
                "oversold_threshold": -0.10,
                "overbought_threshold": 0.10,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "max_holding_period": 5
            },
            "rules": [
                {
                    "rule_type": "entry",
                    "rule_name": "Oversold Entry",
                    "rule_condition": "price_change_20d < oversold_threshold AND rsi < rsi_oversold AND confidence > 0.6",
                    "rule_action": "BUY",
                    "priority": 1
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Mean Reversion Exit",
                    "rule_condition": "current_return > 0.03 OR rsi > 50",
                    "rule_action": "SELL",
                    "priority": 1
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Stop Loss",
                    "rule_condition": "current_return < -0.05",
                    "rule_action": "SELL",
                    "priority": 2
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Timeout Exit",
                    "rule_condition": "holding_days >= max_holding_period",
                    "rule_action": "SELL",
                    "priority": 3
                },
                {
                    "rule_type": "position_sizing",
                    "rule_name": "Conservative Position Size",
                    "rule_condition": "confidence > 0.7",
                    "rule_action": "position_size = 0.12",
                    "priority": 1
                },
                {
                    "rule_type": "position_sizing",
                    "rule_name": "Reduced Position Size",
                    "rule_condition": "confidence <= 0.7",
                    "rule_action": "position_size = 0.08",
                    "priority": 2
                }
            ]
        }
    
    @staticmethod
    def get_breakout_strategy() -> Dict[str, Any]:
        """Stratégie Breakout - Cassure de niveaux"""
        return {
            "name": "Breakout Strategy",
            "description": "Stratégie qui achète lors de cassures de résistance et vend lors de cassures de support",
            "strategy_type": "breakout",
            "parameters": {
                "lookback_period": 20,
                "breakout_threshold": 0.02,
                "volume_multiplier": 1.5,
                "stop_loss_percentage": 0.03,
                "take_profit_percentage": 0.08,
                "max_holding_period": 7
            },
            "rules": [
                {
                    "rule_type": "entry",
                    "rule_name": "Resistance Breakout",
                    "rule_condition": "price > resistance_level AND volume > avg_volume * volume_multiplier AND confidence > 0.75",
                    "rule_action": "BUY",
                    "priority": 1
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Take Profit",
                    "rule_condition": "current_return > take_profit_percentage",
                    "rule_action": "SELL",
                    "priority": 1
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Stop Loss",
                    "rule_condition": "current_return < -stop_loss_percentage",
                    "rule_action": "SELL",
                    "priority": 2
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Failed Breakout",
                    "rule_condition": "price < entry_price * 0.98",
                    "rule_action": "SELL",
                    "priority": 2
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Timeout Exit",
                    "rule_condition": "holding_days >= max_holding_period",
                    "rule_action": "SELL",
                    "priority": 3
                },
                {
                    "rule_type": "position_sizing",
                    "rule_name": "Aggressive Position Size",
                    "rule_condition": "confidence > 0.8 AND volume > avg_volume * 2",
                    "rule_action": "position_size = 0.20",
                    "priority": 1
                },
                {
                    "rule_type": "position_sizing",
                    "rule_name": "Standard Position Size",
                    "rule_condition": "confidence > 0.75",
                    "rule_action": "position_size = 0.15",
                    "priority": 2
                }
            ]
        }
    
    @staticmethod
    def get_scalping_strategy() -> Dict[str, Any]:
        """Stratégie Scalping - Trading à court terme"""
        return {
            "name": "Scalping Strategy",
            "description": "Stratégie de trading à très court terme pour capturer de petits mouvements de prix",
            "strategy_type": "scalping",
            "parameters": {
                "min_price_movement": 0.005,
                "max_holding_period": 1,
                "stop_loss_percentage": 0.01,
                "take_profit_percentage": 0.015,
                "min_volume": 1000000
            },
            "rules": [
                {
                    "rule_type": "entry",
                    "rule_name": "Quick Entry",
                    "rule_condition": "confidence > 0.8 AND volume > min_volume AND price_momentum > min_price_movement",
                    "rule_action": "BUY",
                    "priority": 1
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Quick Profit",
                    "rule_condition": "current_return > take_profit_percentage",
                    "rule_action": "SELL",
                    "priority": 1
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Quick Stop Loss",
                    "rule_condition": "current_return < -stop_loss_percentage",
                    "rule_action": "SELL",
                    "priority": 2
                },
                {
                    "rule_type": "exit",
                    "rule_name": "End of Day Exit",
                    "rule_condition": "holding_days >= max_holding_period",
                    "rule_action": "SELL",
                    "priority": 3
                },
                {
                    "rule_type": "position_sizing",
                    "rule_name": "Small Position Size",
                    "rule_condition": "confidence > 0.85",
                    "rule_action": "position_size = 0.25",
                    "priority": 1
                },
                {
                    "rule_type": "position_sizing",
                    "rule_name": "Reduced Position Size",
                    "rule_condition": "confidence <= 0.85",
                    "rule_action": "position_size = 0.20",
                    "priority": 2
                }
            ]
        }
    
    @staticmethod
    def get_swing_strategy() -> Dict[str, Any]:
        """Stratégie Swing - Trading à moyen terme"""
        return {
            "name": "Swing Strategy",
            "description": "Stratégie de trading à moyen terme qui capture les mouvements de prix sur plusieurs jours",
            "strategy_type": "swing",
            "parameters": {
                "trend_period": 10,
                "trend_strength_threshold": 0.03,
                "stop_loss_percentage": 0.08,
                "take_profit_percentage": 0.15,
                "max_holding_period": 14,
                "min_confidence": 0.65
            },
            "rules": [
                {
                    "rule_type": "entry",
                    "rule_name": "Trend Following Entry",
                    "rule_condition": "trend_strength > trend_strength_threshold AND confidence > min_confidence",
                    "rule_action": "BUY",
                    "priority": 1
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Take Profit",
                    "rule_condition": "current_return > take_profit_percentage",
                    "rule_action": "SELL",
                    "priority": 1
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Stop Loss",
                    "rule_condition": "current_return < -stop_loss_percentage",
                    "rule_action": "SELL",
                    "priority": 2
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Trend Reversal",
                    "rule_condition": "trend_strength < -trend_strength_threshold",
                    "rule_action": "SELL",
                    "priority": 2
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Timeout Exit",
                    "rule_condition": "holding_days >= max_holding_period",
                    "rule_action": "SELL",
                    "priority": 3
                },
                {
                    "rule_type": "position_sizing",
                    "rule_name": "Conservative Position Size",
                    "rule_condition": "confidence > 0.75",
                    "rule_action": "position_size = 0.12",
                    "priority": 1
                },
                {
                    "rule_type": "position_sizing",
                    "rule_name": "Reduced Position Size",
                    "rule_condition": "confidence <= 0.75",
                    "rule_action": "position_size = 0.08",
                    "priority": 2
                }
            ]
        }
    
    @staticmethod
    def get_conservative_strategy() -> Dict[str, Any]:
        """Stratégie Conservative - Faible risque"""
        return {
            "name": "Conservative Strategy",
            "description": "Stratégie conservative avec un focus sur la préservation du capital",
            "strategy_type": "conservative",
            "parameters": {
                "min_confidence": 0.85,
                "max_position_size": 0.05,
                "stop_loss_percentage": 0.03,
                "take_profit_percentage": 0.06,
                "max_holding_period": 21,
                "diversification_limit": 20
            },
            "rules": [
                {
                    "rule_type": "entry",
                    "rule_name": "High Confidence Entry",
                    "rule_condition": "confidence > min_confidence AND volatility < 0.02",
                    "rule_action": "BUY",
                    "priority": 1
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Take Profit",
                    "rule_condition": "current_return > take_profit_percentage",
                    "rule_action": "SELL",
                    "priority": 1
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Stop Loss",
                    "rule_condition": "current_return < -stop_loss_percentage",
                    "rule_action": "SELL",
                    "priority": 2
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Timeout Exit",
                    "rule_condition": "holding_days >= max_holding_period",
                    "rule_action": "SELL",
                    "priority": 3
                },
                {
                    "rule_type": "position_sizing",
                    "rule_name": "Small Position Size",
                    "rule_condition": "confidence > 0.9",
                    "rule_action": "position_size = max_position_size",
                    "priority": 1
                },
                {
                    "rule_type": "position_sizing",
                    "rule_name": "Reduced Position Size",
                    "rule_condition": "confidence <= 0.9",
                    "rule_action": "position_size = max_position_size * 0.5",
                    "priority": 2
                },
                {
                    "rule_type": "risk_management",
                    "rule_name": "Diversification Limit",
                    "rule_condition": "total_positions >= diversification_limit",
                    "rule_action": "SKIP_NEW_POSITIONS",
                    "priority": 1
                }
            ]
        }
    
    @staticmethod
    def get_aggressive_strategy() -> Dict[str, Any]:
        """Stratégie Aggressive - Haut risque, haut rendement"""
        return {
            "name": "Aggressive Strategy",
            "description": "Stratégie aggressive avec des positions importantes et des objectifs élevés",
            "strategy_type": "aggressive",
            "parameters": {
                "min_confidence": 0.6,
                "max_position_size": 0.25,
                "stop_loss_percentage": 0.10,
                "take_profit_percentage": 0.20,
                "max_holding_period": 5,
                "max_positions": 5
            },
            "rules": [
                {
                    "rule_type": "entry",
                    "rule_name": "Aggressive Entry",
                    "rule_condition": "confidence > min_confidence AND momentum > 0.05",
                    "rule_action": "BUY",
                    "priority": 1
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Take Profit",
                    "rule_condition": "current_return > take_profit_percentage",
                    "rule_action": "SELL",
                    "priority": 1
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Stop Loss",
                    "rule_condition": "current_return < -stop_loss_percentage",
                    "rule_action": "SELL",
                    "priority": 2
                },
                {
                    "rule_type": "exit",
                    "rule_name": "Timeout Exit",
                    "rule_condition": "holding_days >= max_holding_period",
                    "rule_action": "SELL",
                    "priority": 3
                },
                {
                    "rule_type": "position_sizing",
                    "rule_name": "Large Position Size",
                    "rule_condition": "confidence > 0.8",
                    "rule_action": "position_size = max_position_size",
                    "priority": 1
                },
                {
                    "rule_type": "position_sizing",
                    "rule_name": "Medium Position Size",
                    "rule_condition": "confidence <= 0.8",
                    "rule_action": "position_size = max_position_size * 0.7",
                    "priority": 2
                },
                {
                    "rule_type": "risk_management",
                    "rule_name": "Position Limit",
                    "rule_condition": "total_positions >= max_positions",
                    "rule_action": "SKIP_NEW_POSITIONS",
                    "priority": 1
                }
            ]
        }
    
    @staticmethod
    def get_all_strategies() -> List[Dict[str, Any]]:
        """Récupérer toutes les stratégies prédéfinies"""
        return [
            PredefinedStrategies.get_momentum_strategy(),
            PredefinedStrategies.get_mean_reversion_strategy(),
            PredefinedStrategies.get_breakout_strategy(),
            PredefinedStrategies.get_scalping_strategy(),
            PredefinedStrategies.get_swing_strategy(),
            PredefinedStrategies.get_conservative_strategy(),
            PredefinedStrategies.get_aggressive_strategy()
        ]
    
    @staticmethod
    def get_strategy_by_type(strategy_type: str) -> Dict[str, Any]:
        """Récupérer une stratégie par son type"""
        strategies_map = {
            "momentum": PredefinedStrategies.get_momentum_strategy(),
            "mean_reversion": PredefinedStrategies.get_mean_reversion_strategy(),
            "breakout": PredefinedStrategies.get_breakout_strategy(),
            "scalping": PredefinedStrategies.get_scalping_strategy(),
            "swing": PredefinedStrategies.get_swing_strategy(),
            "conservative": PredefinedStrategies.get_conservative_strategy(),
            "aggressive": PredefinedStrategies.get_aggressive_strategy()
        }
        
        return strategies_map.get(strategy_type, {})


class StrategyInitializer:
    """Classe pour initialiser les stratégies prédéfinies en base de données"""
    
    def __init__(self, strategy_service):
        self.strategy_service = strategy_service
    
    def initialize_all_strategies(self) -> Dict[str, Any]:
        """Initialiser toutes les stratégies prédéfinies"""
        try:
            strategies = PredefinedStrategies.get_all_strategies()
            results = []
            
            for strategy_data in strategies:
                result = self.strategy_service.create_strategy(
                    name=strategy_data["name"],
                    description=strategy_data["description"],
                    strategy_type=strategy_data["strategy_type"],
                    parameters=strategy_data["parameters"],
                    rules=strategy_data["rules"],
                    created_by="system"
                )
                
                if result["success"]:
                    results.append({
                        "name": strategy_data["name"],
                        "strategy_id": result["strategy_id"],
                        "status": "created"
                    })
                else:
                    results.append({
                        "name": strategy_data["name"],
                        "status": "failed",
                        "error": result["error"]
                    })
            
            return {
                "success": True,
                "results": results,
                "message": f"{len([r for r in results if r['status'] == 'created'])} stratégies initialisées"
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation des stratégies: {e}")
            return {"success": False, "error": str(e)}
    
    def initialize_strategy_by_type(self, strategy_type: str) -> Dict[str, Any]:
        """Initialiser une stratégie spécifique par son type"""
        try:
            strategy_data = PredefinedStrategies.get_strategy_by_type(strategy_type)
            
            if not strategy_data:
                return {"success": False, "error": f"Type de stratégie '{strategy_type}' non trouvé"}
            
            result = self.strategy_service.create_strategy(
                name=strategy_data["name"],
                description=strategy_data["description"],
                strategy_type=strategy_data["strategy_type"],
                parameters=strategy_data["parameters"],
                rules=strategy_data["rules"],
                created_by="system"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la stratégie {strategy_type}: {e}")
            return {"success": False, "error": str(e)}
