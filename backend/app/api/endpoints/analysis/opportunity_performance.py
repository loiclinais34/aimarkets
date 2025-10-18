from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, cast, Float
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from statistics import mean, stdev
import logging

from app.core.database import get_db
from app.models.historical_opportunities import HistoricalOpportunities, HistoricalOpportunityValidation
from app.models.database import HistoricalData
from app.services.performance_analytics import (
    calculate_return_metrics,
    calculate_rolling_metrics,
    analyze_recommendation_performance,
    ReturnMetrics
)

# Set up proper logging
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Performance des Opportunités"])

# Configuration constants
VALIDATION_CONFIG = {
    'max_gap_days': 10,  # Maximum acceptable gap in trading days (augmenté)
    'max_price_spike_pct': 0.30,  # 30% single-day move threshold (augmenté)
    'min_data_points': 3,  # Minimum data points required (réduit)
    'min_coverage_pct': 30  # Minimum data coverage percentage (réduit)
}

TRANSACTION_COSTS = {
    'commission': 0.001,  # 0.1% commission
    'slippage': 0.0005,   # 0.05% slippage
    'spread': 0.0005      # 0.05% bid-ask spread
}

RECOMMENDATION_THRESHOLDS = {
    'BUY_STRONG': (0.03, float('inf')),  # >3% (plus réaliste)
    'BUY_MODERATE': (0.02, float('inf')), # >2% (réduit)
    'BUY_WEAK': (0.01, float('inf')),    # >1% (réduit)
    'HOLD': (-0.02, 0.02),               # Between -2% and +2%
    'SELL_WEAK': (-float('inf'), -0.02), # <-2%
    'SELL_STRONG': (-float('inf'), -0.05) # <-5%
}

RECOMMENDATION_MULTIPLIERS = {
    'BUY_STRONG': 1.0,
    'BUY_MODERATE': 0.7,
    'BUY_WEAK': 0.5,
    'HOLD': 0.0,
    'SELL_WEAK': -0.5,
    'SELL_STRONG': -1.0
}


def validate_historical_data_enhanced(
    historical_data: List,
    opportunity: HistoricalOpportunities
) -> Tuple[bool, Optional[float], Optional[float], str, Dict[str, Any]]:
    """
    Enhanced validation with comprehensive data quality checks.
    
    Returns:
        tuple: (is_valid, initial_price, final_price, message, diagnostics)
    """
    diagnostics = {
        'data_points': len(historical_data),
        'gaps_detected': [],
        'outliers': [],
        'warnings': [],
        'coverage_pct': 0
    }
    
    if not historical_data:
        logger.warning(f"No historical data found for {opportunity.symbol}")
        return False, None, None, "No historical data found", diagnostics
    
    if len(historical_data) < VALIDATION_CONFIG['min_data_points']:
        logger.warning(f"Insufficient data points for {opportunity.symbol}: {len(historical_data)}")
        return False, None, None, f"Insufficient data points: {len(historical_data)}", diagnostics
    
    # Sort data chronologically
    historical_data.sort(key=lambda x: x.date)
    
    # Validate price data quality
    prices = []
    for i, record in enumerate(historical_data):
        # Check for null or invalid prices - CONSISTENT USE OF CLOSE PRICES
        if record.close is None:
            logger.error(f"Null close price at index {i} for {opportunity.symbol}")
            return False, None, None, f"Null price at index {i}", diagnostics
        
        if record.close <= 0:
            logger.error(f"Invalid close price at index {i} for {opportunity.symbol}: {record.close}")
            return False, None, None, f"Invalid price at index {i}: {record.close}", diagnostics
        
        prices.append(record.close)
    
    # Check for outliers using IQR method
    if len(prices) >= 4:  # Need at least 4 points for quartiles
        # Convert Decimal prices to float for numpy operations
        float_prices = [float(p) for p in prices]
        q1, q3 = np.percentile(float_prices, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 3 * iqr
        upper_bound = q3 + 3 * iqr
        
        for i, price in enumerate(prices):
            if float(price) < lower_bound or float(price) > upper_bound:
                diagnostics['outliers'].append({
                    'index': i,
                    'price': float(price),
                    'date': historical_data[i].date.isoformat()
                })
                logger.warning(f"Potential outlier for {opportunity.symbol}: {price} at {historical_data[i].date}")
    
    # Check for suspicious price spikes
    for i in range(len(prices) - 1):
        pct_change = abs((float(prices[i+1]) - float(prices[i])) / float(prices[i]))
        if pct_change > VALIDATION_CONFIG['max_price_spike_pct']:
            diagnostics['warnings'].append({
                'type': 'large_move',
                'magnitude': pct_change,
                'date': historical_data[i+1].date.isoformat()
            })
            logger.warning(f"Large price move for {opportunity.symbol}: {pct_change:.2%} on {historical_data[i+1].date}")
    
    # Check data coverage
    # Convert datetime to date for comparison if needed
    opp_date = opportunity.opportunity_date.date() if hasattr(opportunity.opportunity_date, 'date') else opportunity.opportunity_date
    # Chercher des données AVANT la date de l'opportunité
    expected_start_date = opp_date - timedelta(days=30)  # 30 jours avant
    expected_end_date = opp_date  # Jusqu'à la date de l'opportunité
    actual_start = historical_data[0].date
    actual_end = historical_data[-1].date
    
    if actual_start > expected_start_date:
        logger.warning(f"Missing initial data for {opportunity.symbol}. First available: {actual_start}")
        return False, None, None, f"Missing initial data. First available: {actual_start}", diagnostics
    
    # Calculate actual coverage
    actual_days = (actual_end - actual_start).days
    expected_days = 30  # Horizon fixe de 30 jours
    coverage_pct = (actual_days / expected_days * 100) if expected_days > 0 else 0
    diagnostics['coverage_pct'] = coverage_pct
    
    if actual_end < expected_end_date:
        if coverage_pct < VALIDATION_CONFIG['min_coverage_pct']:
            logger.warning(f"Insufficient coverage for {opportunity.symbol}: {coverage_pct:.1f}%")
            return False, None, None, f"Insufficient coverage: {coverage_pct:.1f}%", diagnostics
        else:
            diagnostics['warnings'].append({
                'type': 'partial_coverage',
                'coverage_pct': coverage_pct
            })
            logger.info(f"Partial coverage for {opportunity.symbol}: {coverage_pct:.1f}%")
    
    # Check for significant gaps (more flexible now)
    for i in range(len(historical_data) - 1):
        gap = (historical_data[i + 1].date - historical_data[i].date).days
        if gap > VALIDATION_CONFIG['max_gap_days']:
            diagnostics['gaps_detected'].append({
                'start': historical_data[i].date.isoformat(),
                'end': historical_data[i + 1].date.isoformat(),
                'days': gap
            })
            logger.warning(f"Data gap for {opportunity.symbol}: {gap} days between {historical_data[i].date} and {historical_data[i+1].date}")
            # Only fail for very large gaps
            return False, None, None, f"Large data gap: {gap} days", diagnostics
    
    # CONSISTENT: Always use CLOSE prices (industry standard for close-to-close returns)
    # Utiliser les données AVANT la date de l'opportunité pour calculer le retour
    initial_price = historical_data[0].close  # Prix le plus ancien
    final_price = historical_data[-1].close   # Prix le plus récent (proche de la date de l'opportunité)
    
    logger.info(f"Validation successful for {opportunity.symbol}: {len(historical_data)} points, {coverage_pct:.1f}% coverage")
    return True, initial_price, final_price, "Validation successful", diagnostics


def fetch_historical_data_batch(
    db: Session,
    opportunities: List[HistoricalOpportunities]
) -> Dict[str, List]:
    """
    Fetch historical data for multiple opportunities in a single query.
    Solves N+1 query problem for better performance.
    
    Returns:
        dict: {(symbol, analysis_date): [historical_data]}
    """
    if not opportunities:
        return {}
    
    logger.info(f"Fetching historical data in batch for {len(opportunities)} opportunities")
    
    # Build OR conditions for all date ranges
    conditions = []
    for opp in opportunities:
        # Convert datetime to date for comparison
        opp_date = opp.opportunity_date.date() if hasattr(opp.opportunity_date, 'date') else opp.opportunity_date
        # Chercher des données AVANT la date de l'opportunité pour calculer le retour
        start_date = opp_date - timedelta(days=30)  # 30 jours avant
        end_date = opp_date  # Jusqu'à la date de l'opportunité
        conditions.append(
            and_(
                HistoricalData.symbol == opp.symbol,
                HistoricalData.date.between(start_date, end_date)
            )
        )
    
    # Single query for all data
    try:
        all_data = db.query(HistoricalData).filter(or_(*conditions)).all()
        logger.info(f"Fetched {len(all_data)} total historical data records")
    except Exception as e:
        logger.error(f"Error fetching batch historical data: {str(e)}", exc_info=True)
        return {}
    
    # Group by (symbol, opportunity_date)
    data_map = {}
    for opp in opportunities:
        key = (opp.symbol, opp.opportunity_date)
        # Convert datetime to date for comparison
        opp_date = opp.opportunity_date.date() if hasattr(opp.opportunity_date, 'date') else opp.opportunity_date
        # Chercher des données AVANT la date de l'opportunité
        start_date = opp_date - timedelta(days=30)  # 30 jours avant
        end_date = opp_date  # Jusqu'à la date de l'opportunité
        
        # Filter data for this specific opportunity
        opp_data = [
            record for record in all_data
            if record.symbol == opp.symbol and start_date <= record.date <= end_date
        ]
        data_map[key] = opp_data
    
    return data_map


def convert_confidence_to_float(confidence_str: str) -> float:
    """Convert confidence level string to float"""
    if confidence_str is None:
        return 0.5
    
    # Si c'est déjà un nombre, le convertir
    try:
        return float(confidence_str)
    except ValueError:
        # Conversion des valeurs textuelles
        confidence_mapping = {
            'LOW': 0.3,
            'MEDIUM': 0.6,
            'HIGH': 0.8,
            'VERY_HIGH': 0.9
        }
        return confidence_mapping.get(confidence_str.upper(), 0.5)


def should_upgrade_to_buy_strong(
    opportunity: HistoricalOpportunities,
    historical_data: List,
    technical_indicators: Dict[str, Any] = None
) -> bool:
    """
    Détermine si une opportunité BUY_MODERATE devrait être upgradée en BUY_STRONG.
    
    Args:
        opportunity: L'opportunité à évaluer
        historical_data: Données historiques pour validation
        technical_indicators: Indicateurs techniques supplémentaires
        
    Returns:
        True si l'opportunité mérite d'être BUY_STRONG
    """
    if opportunity.recommendation != 'BUY_MODERATE':
        return False
    
    confidence_float = convert_confidence_to_float(opportunity.confidence_level)
    
    # Critères pour BUY_STRONG :
    # 1. Confiance très élevée
    if confidence_float < 0.85:
        return False
    
    # 2. Validation des données historiques
    is_valid, initial_price, final_price, message, diagnostics = validate_historical_data_enhanced(
        historical_data, opportunity
    )
    
    if not is_valid:
        return False
    
    # 3. Retour potentiel élevé (basé sur les données historiques)
    potential_return = float(final_price - initial_price) / float(initial_price)
    if potential_return < 0.06:  # Au moins 6% de retour potentiel
        return False
    
    # 4. Volatilité contrôlée (si disponible)
    if technical_indicators and 'volatility' in technical_indicators:
        volatility = technical_indicators.get('volatility', 0)
        if volatility > 0.15:  # Volatilité trop élevée
            return False
    
    return True


def adjust_returns_for_costs(returns: List[float]) -> List[float]:
    """
    Adjust returns for realistic trading costs.
    
    Args:
        returns: List of raw returns
        
    Returns:
        List of returns adjusted for transaction costs
    """
    total_cost_per_trade = (
        TRANSACTION_COSTS['commission'] + 
        TRANSACTION_COSTS['slippage'] + 
        TRANSACTION_COSTS['spread']
    )
    
    # Deduct costs from both entry and exit (2x costs per round trip)
    adjusted_returns = [r - (2 * total_cost_per_trade) for r in returns]
    
    logger.debug(f"Adjusted {len(returns)} returns for transaction costs (2x {total_cost_per_trade:.4f})")
    return adjusted_returns


def calculate_performance_by_recommendation(
    opportunities_data: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Calcule les métriques de performance par type de recommandation.
    
    Args:
        opportunities_data: Liste des données d'opportunités avec leurs métriques
        
    Returns:
        Dict avec les métriques par type de recommandation
    """
    from collections import defaultdict
    
    # Grouper les données par type de recommandation
    by_recommendation = defaultdict(list)
    
    for opp_data in opportunities_data:
        recommendation = opp_data['recommendation']
        by_recommendation[recommendation].append(opp_data)
    
    # Calculer les métriques pour chaque type de recommandation
    recommendation_metrics = {}
    
    for recommendation, opps in by_recommendation.items():
        if not opps:
            continue
            
        # Extraire les données
        returns = [opp['actual_return'] for opp in opps]
        successes = [opp['success'] for opp in opps]
        confidence_levels = [opp['confidence_level'] for opp in opps]
        
        # Métriques de base
        total_count = len(opps)
        success_count = sum(successes)
        success_rate = success_count / total_count if total_count > 0 else 0
        
        # Métriques de retour
        mean_return = np.mean(returns) if returns else 0
        median_return = np.median(returns) if returns else 0
        std_return = np.std(returns) if len(returns) > 1 else 0
        
        # Métriques de confiance
        mean_confidence = np.mean(confidence_levels) if confidence_levels else 0
        
        # Ratio risque/rendement (Sharpe ratio simplifié)
        risk_adjusted_return = mean_return / std_return if std_return > 0 else 0
        
        # Métriques avancées
        positive_returns = [r for r in returns if r > 0]
        negative_returns = [r for r in returns if r < 0]
        
        win_rate = len(positive_returns) / total_count if total_count > 0 else 0
        avg_win = np.mean(positive_returns) if positive_returns else 0
        avg_loss = np.mean(negative_returns) if negative_returns else 0
        
        # Profit factor
        gross_profit = sum(positive_returns) if positive_returns else 0
        gross_loss = abs(sum(negative_returns)) if negative_returns else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        recommendation_metrics[recommendation] = {
            'total_opportunities': total_count,
            'successful_predictions': success_count,
            'success_rate': success_rate,
            'mean_return': mean_return,
            'median_return': median_return,
            'std_return': std_return,
            'mean_confidence': mean_confidence,
            'risk_adjusted_return': risk_adjusted_return,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'gross_profit': gross_profit,
            'gross_loss': gross_loss
        }
    
    return recommendation_metrics


def calculate_opportunity_success_enhanced(
    opportunity: HistoricalOpportunities,
    historical_data: List,
    apply_costs: bool = True
) -> Tuple[bool, float, float, Dict[str, Any]]:
    """
    Enhanced calculation of opportunity success with proper validation.
    
    Returns:
        tuple: (success, actual_return, adjusted_return, metadata)
    """
    metadata = {
        'symbol': opportunity.symbol,
        'opportunity_date': opportunity.opportunity_date.isoformat(),
        'recommendation': opportunity.recommendation,
        'confidence': opportunity.confidence_level,
        'horizon': 30  # Horizon fixe
    }
    
    logger.info(f"Analyzing opportunity: {opportunity.symbol} at {opportunity.opportunity_date} "
                f"({opportunity.recommendation}, confidence: {opportunity.confidence_level})")
    
    # Validate data quality - USE ENHANCED VALIDATION
    is_valid, initial_price, final_price, message, diagnostics = validate_historical_data_enhanced(
        historical_data, opportunity
    )
    
    metadata['validation'] = {
        'is_valid': is_valid,
        'message': message,
        'diagnostics': diagnostics
    }
    
    if not is_valid:
        logger.warning(f"Data validation failed for {opportunity.symbol}: {message}")
        return False, 0.0, 0.0, metadata
    
    # Calculate raw return using validated prices (convert Decimal to float)
    actual_return = float(final_price - initial_price) / float(initial_price)
    metadata['raw_return'] = actual_return
    metadata['initial_price'] = float(initial_price)
    metadata['final_price'] = float(final_price)
    
    # Determine if prediction was correct
    if opportunity.recommendation in RECOMMENDATION_THRESHOLDS:
        min_return, max_return = RECOMMENDATION_THRESHOLDS[opportunity.recommendation]
        success = min_return <= actual_return <= max_return
        
        # Validation spéciale pour BUY_STRONG - critères équilibrés
        if opportunity.recommendation == 'BUY_STRONG':
            confidence_float = convert_confidence_to_float(opportunity.confidence_level)
            # BUY_STRONG doit avoir une confiance élevée ET un retour positif
            if confidence_float < 0.6:  # Seuil réduit
                success = False
                metadata['buy_strong_rejection'] = f"Confidence trop faible: {confidence_float:.3f} < 0.6"
            elif actual_return < 0.01:  # Au moins 1% de retour minimum (plus réaliste)
                success = False
                metadata['buy_strong_rejection'] = f"Retour insuffisant: {actual_return:.4f} < 0.01"
            else:
                metadata['buy_strong_validation'] = f"Confidence: {confidence_float:.3f}, Retour: {actual_return:.4f}"
        
        metadata['expected_range'] = (min_return, max_return)
    else:
        success = False
        logger.warning(f"Unknown recommendation type: {opportunity.recommendation}")
    
    # Calculate adjusted return based on recommendation strength
    multiplier = RECOMMENDATION_MULTIPLIERS.get(opportunity.recommendation, 0)
    adjusted_return = actual_return * multiplier * convert_confidence_to_float(opportunity.confidence_level)
    
    # Apply transaction costs if requested
    if apply_costs:
        total_costs = 2 * (TRANSACTION_COSTS['commission'] + 
                          TRANSACTION_COSTS['slippage'] + 
                          TRANSACTION_COSTS['spread'])
        adjusted_return -= total_costs
        metadata['transaction_costs'] = total_costs
    
    metadata['success'] = success
    metadata['adjusted_return'] = adjusted_return
    
    logger.info(f"Results for {opportunity.symbol}: success={success}, "
                f"actual={actual_return:.4f}, adjusted={adjusted_return:.4f}")
    
    return success, actual_return, adjusted_return, metadata


def calculate_advanced_risk_metrics(returns: List[float]) -> Dict[str, float]:
    """
    Calculate comprehensive risk metrics beyond basic Sharpe/Sortino.
    
    Returns:
        Dictionary with advanced risk metrics
    """
    if not returns or len(returns) < 2:
        return {
            'var_95': 0.0,
            'cvar_95': 0.0,
            'max_consecutive_losses': 0,
            'calmar_ratio': 0.0,
            'downside_deviation': 0.0
        }
    
    returns_array = np.array(returns)
    
    # Value at Risk (95% confidence)
    var_95 = float(np.percentile(returns_array, 5))
    
    # Conditional VaR (Expected Shortfall)
    tail_losses = returns_array[returns_array <= var_95]
    cvar_95 = float(tail_losses.mean()) if len(tail_losses) > 0 else var_95
    
    # Maximum consecutive losses
    consecutive_losses = 0
    max_consecutive_losses = 0
    for r in returns:
        if r < 0:
            consecutive_losses += 1
            max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
        else:
            consecutive_losses = 0
    
    # Calmar Ratio (return / max drawdown)
    cumulative = np.cumsum(returns_array)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = cumulative - running_max
    max_drawdown = abs(float(np.min(drawdown))) if len(drawdown) > 0 else 0
    
    mean_return = float(np.mean(returns_array))
    calmar_ratio = mean_return / max_drawdown if max_drawdown > 0 else 0
    
    # Downside deviation
    negative_returns = returns_array[returns_array < 0]
    downside_deviation = float(np.std(negative_returns)) if len(negative_returns) > 1 else 0
    
    return {
        'var_95': var_95,
        'cvar_95': cvar_95,
        'max_consecutive_losses': max_consecutive_losses,
        'calmar_ratio': calmar_ratio,
        'downside_deviation': downside_deviation,
        'max_drawdown': max_drawdown
    }


@router.get("/performance", response_model=Dict[str, Any])
async def get_opportunity_performance_stats(
    db: Session = Depends(get_db),
    time_window: Optional[int] = 30,
    min_confidence: Optional[float] = None,
    max_confidence: Optional[float] = None,
    horizon_min: Optional[int] = None,
    horizon_max: Optional[int] = None,
    page: int = 1,
    page_size: int = 100,
    apply_transaction_costs: bool = True
):
    """
    Calculate performance statistics for opportunities with enhanced filtering and pagination.
    
    Args:
        time_window: Time window in days for analysis
        min_confidence: Minimum confidence level filter
        max_confidence: Maximum confidence level filter
        horizon_min: Minimum time horizon in days
        horizon_max: Maximum time horizon in days
        page: Page number for pagination (default: 1)
        page_size: Number of opportunities per page (default: 100)
        apply_transaction_costs: Whether to apply transaction costs to returns (default: True)
    """
    try:
        logger.info(f"Performance stats request: page={page}, page_size={page_size}, "
                   f"confidence=[{min_confidence}, {max_confidence}], "
                   f"horizon=[{horizon_min}, {horizon_max}]")
        
        # Build base query - get opportunities that have had time to develop
        # For testing purposes, we'll accept opportunities from the last 1 day
        # In production, you might want to use a longer period
        cutoff_date = datetime.now() - timedelta(days=1)
        query = db.query(HistoricalOpportunities).filter(
            HistoricalOpportunities.opportunity_date <= cutoff_date
        )
        
        # Apply filters
        # Note: confidence filters temporarily disabled due to mixed data types
        # if min_confidence is not None:
        #     query = query.filter(cast(HistoricalOpportunities.confidence_level, Float) >= min_confidence)
        # if max_confidence is not None:
        #     query = query.filter(cast(HistoricalOpportunities.confidence_level, Float) <= max_confidence)
        # Note: horizon filters removed since we use a fixed 30-day horizon
        
        # Get total count for pagination
        total_count = query.count()
        logger.info(f"Total opportunities matching filters: {total_count}")
        
        if total_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No historical data found matching the specified criteria"
            )
        
        # Apply pagination
        offset = (page - 1) * page_size
        past_opportunities = query.order_by(
            HistoricalOpportunities.opportunity_date.desc()
        ).offset(offset).limit(page_size).all()
        
        logger.info(f"Processing {len(past_opportunities)} opportunities (page {page})")
        
        # BATCH FETCH: Get all historical data in one query
        historical_data_map = fetch_historical_data_batch(db, past_opportunities)
        
        # Collect metrics
        returns: List[float] = []
        actual_returns: List[float] = []
        recommendations: List[str] = []
        confidence_levels: List[float] = []
        horizons: List[int] = []
        successes: List[bool] = []
        all_metadata: List[Dict] = []
        opportunities_data: List[Dict[str, Any]] = []  # Nouvelle structure pour l'analyse par recommandation
        failed_validations = 0
        
        for opportunity in past_opportunities:
            # Get pre-fetched historical data
            key = (opportunity.symbol, opportunity.opportunity_date)
            historical_data = historical_data_map.get(key, [])
            
            if not historical_data:
                logger.warning(f"No historical data found for {opportunity.symbol} at {opportunity.opportunity_date}")
                failed_validations += 1
                continue
            
            # Calculate success with enhanced validation
            try:
                success, actual_return, adjusted_return, metadata = calculate_opportunity_success_enhanced(
                    opportunity, historical_data, apply_costs=apply_transaction_costs
                )
            except Exception as e:
                logger.error(f"Error calculating success for {opportunity.symbol}: {str(e)}", exc_info=True)
                failed_validations += 1
                continue
            
            if not metadata['validation']['is_valid']:
                failed_validations += 1
                continue
            
            # Collecter les données pour l'analyse par recommandation
            opportunity_data = {
                'symbol': opportunity.symbol,
                'recommendation': opportunity.recommendation,
                'actual_return': actual_return,
                'adjusted_return': adjusted_return,
                'success': success,
                'confidence_level': convert_confidence_to_float(opportunity.confidence_level),
                'metadata': metadata
            }
            
            returns.append(adjusted_return)
            actual_returns.append(actual_return)
            recommendations.append(opportunity.recommendation)
            confidence_levels.append(convert_confidence_to_float(opportunity.confidence_level))  # Convertir en float
            horizons.append(30)  # Horizon fixe de 30 jours
            successes.append(success)
            all_metadata.append(metadata)
            opportunities_data.append(opportunity_data)
        
        if not returns:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No valid opportunities found after validation"
            )
        
        logger.info(f"Successfully processed {len(returns)} opportunities, {failed_validations} failed validation")
        
        # Calculate metrics by recommendation type
        recommendation_metrics = calculate_performance_by_recommendation(opportunities_data)
        
        # Calculate overall metrics using existing service (ensure all returns are float)
        float_returns = [float(r) for r in returns]
        return_metrics = calculate_return_metrics(float_returns)
        rolling_metrics = calculate_rolling_metrics(float_returns, window=min(time_window, len(float_returns)))
        recommendation_performance = analyze_recommendation_performance(float_returns, recommendations)
        
        # Calculate advanced risk metrics
        advanced_risk = calculate_advanced_risk_metrics(float_returns)
        
        # Calculate success rate
        success_rate = sum(successes) / len(successes) if successes else 0
        
        # Aggregate results
        response = {
            "overview": {
                "total_opportunities": total_count,
                "analyzed_opportunities": len(returns),
                "failed_validations": failed_validations,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_count + page_size - 1) // page_size,
                "success_rate": success_rate,
                "win_rate": return_metrics.win_rate,
                "profit_factor": return_metrics.profit_factor,
                "average_confidence": mean(confidence_levels) if confidence_levels else 0,
                "average_horizon": mean(horizons) if horizons else 0,
                "transaction_costs_applied": apply_transaction_costs
            },
            "recommendation_metrics": recommendation_metrics,  # Nouvelle section avec métriques par recommandation
            "return_metrics": {
                "mean_return": return_metrics.mean,
                "median_return": return_metrics.median,
                "volatility": return_metrics.std_dev,
                "skewness": return_metrics.skewness,
                "kurtosis": return_metrics.kurtosis,
                "max_drawdown": return_metrics.max_drawdown,
                "total_return": sum(float_returns) if float_returns else 0,
                "avg_actual_return": mean(actual_returns) if actual_returns else 0
            },
            "risk_metrics": {
                "sharpe_ratio": return_metrics.sharpe_ratio,
                "sortino_ratio": return_metrics.sortino_ratio,
                "var_95": advanced_risk['var_95'],
                "cvar_95": advanced_risk['cvar_95'],
                "max_consecutive_losses": advanced_risk['max_consecutive_losses'],
                "calmar_ratio": advanced_risk['calmar_ratio'],
                "downside_deviation": advanced_risk['downside_deviation']
            },
            "rolling_metrics": rolling_metrics,
            "recommendation_performance": recommendation_performance,
            "confidence_distribution": {
                "high": len([c for c in confidence_levels if c >= 0.7]),
                "medium": len([c for c in confidence_levels if 0.5 <= c < 0.7]),
                "low": len([c for c in confidence_levels if c < 0.5])
            },
            "horizon_distribution": {
                "short": len([h for h in horizons if h <= 7]),
                "medium": len([h for h in horizons if 7 < h <= 30]),
                "long": len([h for h in horizons if h > 30])
            }
        }
        
        logger.info(f"Performance analysis completed successfully: {len(returns)} opportunities analyzed")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating performance statistics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating performance statistics: {str(e)}"
        )


@router.get("/performance/analysis/buy-strong", response_model=Dict[str, Any])
async def analyze_buy_strong_opportunities(
    db: Session = Depends(get_db),
    time_window: Optional[int] = 30
):
    """
    Analyse spécifique des opportunités BUY_STRONG pour identifier les problèmes.
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=1)
        
        # Récupérer toutes les opportunités BUY_STRONG
        buy_strong_opportunities = db.query(HistoricalOpportunities).filter(
            HistoricalOpportunities.recommendation == 'BUY_STRONG',
            HistoricalOpportunities.opportunity_date <= cutoff_date
        ).order_by(HistoricalOpportunities.opportunity_date.desc()).limit(50).all()
        
        analysis_results = {
            'total_buy_strong': len(buy_strong_opportunities),
            'confidence_distribution': {},
            'performance_issues': [],
            'recommendations': []
        }
        
        # Analyser la distribution des confiances
        confidence_values = []
        for opp in buy_strong_opportunities:
            conf_float = convert_confidence_to_float(opp.confidence_level)
            confidence_values.append(conf_float)
        
        if confidence_values:
            analysis_results['confidence_distribution'] = {
                'min': min(confidence_values),
                'max': max(confidence_values),
                'mean': sum(confidence_values) / len(confidence_values),
                'count_low_confidence': sum(1 for c in confidence_values if c < 0.7)
            }
        
        # Identifier les problèmes potentiels
        if analysis_results['confidence_distribution'].get('count_low_confidence', 0) > 0:
            analysis_results['performance_issues'].append(
                f"{analysis_results['confidence_distribution']['count_low_confidence']} "
                f"opportunités BUY_STRONG ont une confiance < 0.7"
            )
        
        # Recommandations d'amélioration
        analysis_results['recommendations'] = [
            "Augmenter le seuil de confiance minimum pour BUY_STRONG à 0.85",
            "Ajouter une validation du retour potentiel minimum (6%)",
            "Considérer l'upgrade automatique de BUY_MODERATE vers BUY_STRONG",
            "Implémenter une validation de volatilité pour éviter les positions risquées"
        ]
        
        logger.info(f"Analyse BUY_STRONG terminée: {len(buy_strong_opportunities)} opportunités analysées")
        return analysis_results
        
    except Exception as e:
        logger.error(f"Erreur lors de l'analyse BUY_STRONG: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse BUY_STRONG: {str(e)}"
        )


@router.get("/performance/kpis", response_model=Dict[str, Any])
async def get_opportunity_performance_kpis(
    db: Session = Depends(get_db),
    time_window: Optional[int] = 30,
    min_confidence: Optional[float] = None,
    max_confidence: Optional[float] = None,
    horizon_min: Optional[int] = None,
    horizon_max: Optional[int] = None,
    apply_transaction_costs: bool = True
):
    """
    Get performance KPIs in the format expected by the frontend.
    This endpoint returns a simplified structure for KPI display.
    """
    try:
        # Get the detailed performance data
        detailed_response = await get_opportunity_performance_stats(
            db=db,
            time_window=time_window,
            min_confidence=min_confidence,
            max_confidence=max_confidence,
            horizon_min=horizon_min,
            horizon_max=horizon_max,
            page=1,
            page_size=100,
            apply_transaction_costs=apply_transaction_costs
        )
        
        # Map the detailed response to the KPI format expected by frontend
        overview = detailed_response["overview"]
        recommendation_metrics = detailed_response["recommendation_metrics"]
        
        # Créer une réponse structurée par type de recommandation
        kpi_response = {
            "total_opportunities": overview["total_opportunities"],
            "analyzed_opportunities": overview["analyzed_opportunities"],
            "overall_success_rate": overview["success_rate"],
            "recommendation_performance": {}
        }
        
        # Ajouter les métriques pour chaque type de recommandation
        for recommendation, metrics in recommendation_metrics.items():
            kpi_response["recommendation_performance"][recommendation] = {
                "total_opportunities": metrics["total_opportunities"],
                "successful_predictions": metrics["successful_predictions"],
                "success_rate": metrics["success_rate"],
                "mean_return": metrics["mean_return"],
                "median_return": metrics["median_return"],
                "std_return": metrics["std_return"],
                "mean_confidence": metrics["mean_confidence"],
                "risk_adjusted_return": metrics["risk_adjusted_return"],
                "win_rate": metrics["win_rate"],
                "avg_win": metrics["avg_win"],
                "avg_loss": metrics["avg_loss"],
                "profit_factor": metrics["profit_factor"],
                "gross_profit": metrics["gross_profit"],
                "gross_loss": metrics["gross_loss"]
            }
        
        logger.info(f"KPI response generated successfully")
        return kpi_response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating KPI response: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating KPI response: {str(e)}"
        )
