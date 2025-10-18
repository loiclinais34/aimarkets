"""
Service pour l'analyse avancée des performances des opportunités
"""
from typing import List, Dict, Any, Tuple
import numpy as np
from scipy import stats
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ReturnMetrics:
    """Métriques de performance des retours"""
    mean: float
    median: float
    std_dev: float
    skewness: float
    kurtosis: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float

def calculate_return_metrics(returns: List[float], risk_free_rate: float = 0.02) -> ReturnMetrics:
    """
    Calcule les métriques avancées sur les retours
    
    Args:
        returns: Liste des retours
        risk_free_rate: Taux sans risque annualisé (par défaut 2%)
    """
    if not returns:
        return ReturnMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    
    returns_array = np.array(returns)
    
    # Métriques de base
    mean_return = np.mean(returns_array)
    median_return = np.median(returns_array)
    std_dev = np.std(returns_array, ddof=1)
    
    # Métriques de distribution
    skewness = stats.skew(returns_array) if len(returns_array) > 2 else 0
    kurtosis = stats.kurtosis(returns_array) if len(returns_array) > 2 else 0
    
    # Ratios de performance
    excess_returns = returns_array - (risk_free_rate / 252)  # Convertir taux annuel en journalier
    sharpe_ratio = (np.mean(excess_returns) / std_dev) * np.sqrt(252) if std_dev > 0 else 0
    
    # Sortino ratio (ne considère que la volatilité négative)
    negative_returns = returns_array[returns_array < 0]
    downside_std = np.std(negative_returns, ddof=1) if len(negative_returns) > 0 else std_dev
    sortino_ratio = (np.mean(excess_returns) / downside_std) * np.sqrt(252) if downside_std > 0 else 0
    
    # Maximum drawdown
    cumulative_returns = np.cumprod(1 + returns_array)
    running_max = np.maximum.accumulate(cumulative_returns)
    drawdowns = (cumulative_returns - running_max) / running_max
    max_drawdown = abs(np.min(drawdowns)) if len(drawdowns) > 0 else 0
    
    # Win rate et profit factor
    winning_trades = np.sum(returns_array > 0)
    win_rate = winning_trades / len(returns_array) if len(returns_array) > 0 else 0
    
    gross_profits = np.sum(returns_array[returns_array > 0])
    gross_losses = abs(np.sum(returns_array[returns_array < 0]))
    profit_factor = gross_profits / gross_losses if gross_losses > 0 else float('inf')
    
    return ReturnMetrics(
        mean=mean_return,
        median=median_return,
        std_dev=std_dev,
        skewness=skewness,
        kurtosis=kurtosis,
        sharpe_ratio=sharpe_ratio,
        sortino_ratio=sortino_ratio,
        max_drawdown=max_drawdown,
        win_rate=win_rate,
        profit_factor=profit_factor
    )

def calculate_rolling_metrics(returns: List[float], window: int = 30) -> Dict[str, List[float]]:
    """
    Calcule les métriques sur une fenêtre glissante
    
    Args:
        returns: Liste des retours
        window: Taille de la fenêtre en jours
    """
    if len(returns) < window:
        return {
            "rolling_sharpe": [],
            "rolling_volatility": [],
            "rolling_returns": []
        }
    
    returns_array = np.array(returns)
    rolling_returns = []
    rolling_volatility = []
    rolling_sharpe = []
    
    for i in range(window, len(returns_array) + 1):
        window_returns = returns_array[i-window:i]
        rolling_returns.append(np.mean(window_returns))
        rolling_volatility.append(np.std(window_returns, ddof=1))
        rolling_sharpe.append((np.mean(window_returns) / np.std(window_returns, ddof=1)) * np.sqrt(252) if np.std(window_returns, ddof=1) > 0 else 0)
    
    return {
        "rolling_sharpe": rolling_sharpe,
        "rolling_volatility": rolling_volatility,
        "rolling_returns": rolling_returns
    }

def analyze_recommendation_performance(returns: List[float], recommendations: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Analyse la performance par type de recommandation
    """
    rec_types = ['BUY_STRONG', 'BUY_WEAK', 'HOLD', 'SELL_WEAK', 'SELL_STRONG']
    performance = {}
    
    for rec_type in rec_types:
        rec_returns = [ret for ret, rec in zip(returns, recommendations) if rec == rec_type]
        if rec_returns:
            metrics = calculate_return_metrics(rec_returns)
            performance[rec_type] = {
                "count": len(rec_returns),
                "mean_return": metrics.mean,
                "win_rate": metrics.win_rate,
                "sharpe_ratio": metrics.sharpe_ratio
            }
        else:
            performance[rec_type] = {
                "count": 0,
                "mean_return": 0,
                "win_rate": 0,
                "sharpe_ratio": 0
            }
    
    return performance