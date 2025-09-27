#!/usr/bin/env python3
"""
Script de recalcul des indicateurs de volatilité
Calcule les indicateurs de volatilité avancés pour les symboles
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging

from app.core.database import get_db
from app.models.database import HistoricalData
from app.models.market_indicators import VolatilityIndicators

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VolatilityCalculator:
    """Calculateur d'indicateurs de volatilité"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def calculate_volatility_indicators(self, symbol: str, force_update: bool = False) -> dict:
        """
        Calcule les indicateurs de volatilité pour un symbole
        
        Args:
            symbol: Symbole à traiter
            force_update: Forcer le recalcul
        
        Returns:
            Dict contenant le résultat du calcul
        """
        try:
            logger.info(f"Calculating volatility indicators for {symbol}")
            
            # Vérifier si les indicateurs existent déjà et sont récents
            if not force_update:
                latest_indicator = self.db.query(VolatilityIndicators)\
                    .filter(VolatilityIndicators.symbol == symbol)\
                    .order_by(VolatilityIndicators.analysis_date.desc())\
                    .first()
                
                if latest_indicator and latest_indicator.analysis_date >= datetime.now() - timedelta(days=1):
                    logger.info(f"Volatility indicators for {symbol} are already up to date")
                    return {"status": "skipped", "reason": "already_up_to_date"}
            
            # Récupérer les données historiques (252 jours = 1 année de trading)
            historical_data = self.db.query(HistoricalData).filter(
                HistoricalData.symbol == symbol
            ).order_by(HistoricalData.date.desc()).limit(252).all()
            
            if not historical_data:
                logger.warning(f"No historical data found for {symbol}")
                return {"status": "error", "symbol": symbol, "error": "No historical data"}
            
            # Convertir en DataFrame
            data = []
            for row in historical_data:
                data.append({
                    'date': row.date,
                    'open': float(row.open),
                    'high': float(row.high),
                    'low': float(row.low),
                    'close': float(row.close),
                    'volume': int(row.volume)
                })
            
            df = pd.DataFrame(data)
            df = df.sort_values('date').reset_index(drop=True)
            
            # Supprimer les anciens indicateurs si force_update
            if force_update:
                self.db.query(VolatilityIndicators).filter(VolatilityIndicators.symbol == symbol).delete()
            
            # Calculer les indicateurs de volatilité
            volatility_data = self._calculate_volatility_metrics(df)
            
            # Créer l'enregistrement
            volatility_indicator = VolatilityIndicators(
                symbol=symbol,
                analysis_date=datetime.now(),
                current_volatility=volatility_data['current_volatility'],
                historical_volatility=volatility_data['historical_volatility'],
                implied_volatility=volatility_data['implied_volatility'],
                vix_value=volatility_data['vix_value'],
                volatility_ratio=volatility_data['volatility_ratio'],
                volatility_percentile=volatility_data['volatility_percentile'],
                volatility_skew=volatility_data['volatility_skew'],
                risk_premium=volatility_data['risk_premium'],
                risk_level=volatility_data['risk_level'],
                regime_analysis=volatility_data['regime_analysis']
            )
            
            self.db.add(volatility_indicator)
            self.db.commit()
            
            logger.info(f"Volatility indicators calculated for {symbol}")
            return {"status": "success", "symbol": symbol, "indicators_created": 1}
            
        except Exception as e:
            logger.error(f"Error calculating volatility indicators for {symbol}: {e}")
            self.db.rollback()
            return {"status": "error", "symbol": symbol, "error": str(e)}
    
    def _calculate_volatility_metrics(self, df: pd.DataFrame) -> dict:
        """Calculer les métriques de volatilité"""
        
        # Calculer les rendements logarithmiques
        df['returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Volatilité actuelle (20 jours)
        current_volatility = df['returns'].tail(20).std() * np.sqrt(252)
        
        # Volatilité historique (252 jours)
        historical_volatility = df['returns'].std() * np.sqrt(252)
        
        # Volatilité implicite (estimation basée sur les gaps)
        gaps = np.log(df['open'] / df['close'].shift(1))
        implied_volatility = gaps.std() * np.sqrt(252)
        
        # VIX simulé (basé sur la volatilité des rendements)
        vix_value = current_volatility * 100  # Approximation
        
        # Ratio de volatilité
        volatility_ratio = current_volatility / historical_volatility if historical_volatility > 0 else 1.0
        
        # Percentile de volatilité (basé sur les 252 derniers jours)
        volatility_percentile = self._calculate_volatility_percentile(df['returns'])
        
        # Skew de volatilité (asymétrie des rendements)
        volatility_skew = df['returns'].skew()
        
        # Prime de risque (volatilité ajustée)
        risk_premium = current_volatility * volatility_ratio
        
        # Niveau de risque
        risk_level = self._determine_risk_level(current_volatility, volatility_percentile)
        
        # Analyse des régimes
        regime_analysis = self._analyze_volatility_regime(df)
        
        return {
            'current_volatility': float(current_volatility),
            'historical_volatility': float(historical_volatility),
            'implied_volatility': float(implied_volatility),
            'vix_value': float(vix_value),
            'volatility_ratio': float(volatility_ratio),
            'volatility_percentile': float(volatility_percentile),
            'volatility_skew': float(volatility_skew),
            'risk_premium': float(risk_premium),
            'risk_level': risk_level,
            'regime_analysis': regime_analysis
        }
    
    def _calculate_volatility_percentile(self, returns: pd.Series) -> float:
        """Calculer le percentile de volatilité"""
        # Calculer la volatilité mobile sur 20 jours
        rolling_vol = returns.rolling(window=20).std() * np.sqrt(252)
        
        # Calculer le percentile de la volatilité actuelle
        current_vol = rolling_vol.iloc[-1]
        percentile = (rolling_vol < current_vol).mean() * 100
        
        return float(percentile)
    
    def _determine_risk_level(self, current_vol: float, percentile: float) -> str:
        """Déterminer le niveau de risque"""
        if current_vol < 0.15 and percentile < 30:
            return "LOW"
        elif current_vol < 0.25 and percentile < 60:
            return "MEDIUM"
        elif current_vol < 0.40 and percentile < 80:
            return "HIGH"
        else:
            return "VERY_HIGH"
    
    def _analyze_volatility_regime(self, df: pd.DataFrame) -> dict:
        """Analyser le régime de volatilité"""
        returns = df['returns']
        
        # Volatilité mobile sur différentes périodes
        vol_5d = returns.tail(5).std() * np.sqrt(252)
        vol_20d = returns.tail(20).std() * np.sqrt(252)
        vol_60d = returns.tail(60).std() * np.sqrt(252)
        
        # Tendance de volatilité
        if vol_5d > vol_20d > vol_60d:
            trend = "INCREASING"
        elif vol_5d < vol_20d < vol_60d:
            trend = "DECREASING"
        else:
            trend = "SIDEWAYS"
        
        # Clustering de volatilité (GARCH-like)
        squared_returns = returns ** 2
        clustering_score = squared_returns.autocorr(lag=1)
        
        return {
            "volatility_5d": float(vol_5d),
            "volatility_20d": float(vol_20d),
            "volatility_60d": float(vol_60d),
            "trend": trend,
            "clustering_score": float(clustering_score),
            "regime": "HIGH_VOL" if vol_20d > 0.25 else "LOW_VOL"
        }

def recompute_volatility_indicators_for_symbol(symbol: str, force_update: bool = False) -> dict:
    """
    Recalculer les indicateurs de volatilité pour un symbole
    
    Args:
        symbol: Symbole à traiter
        force_update: Forcer le recalcul
    
    Returns:
        Dict contenant le résultat
    """
    try:
        db = next(get_db())
        calculator = VolatilityCalculator(db)
        result = calculator.calculate_volatility_indicators(symbol, force_update)
        return result
    except Exception as e:
        logger.error(f"Error in recompute_volatility_indicators_for_symbol: {e}")
        return {"status": "error", "symbol": symbol, "error": str(e)}
    finally:
        db.close()

def recompute_volatility_indicators_for_symbols(symbols: list, force_update: bool = False) -> dict:
    """
    Recalculer les indicateurs de volatilité pour plusieurs symboles
    
    Args:
        symbols: Liste des symboles à traiter
        force_update: Forcer le recalcul
    
    Returns:
        Dict contenant les résultats
    """
    results = {
        "total_symbols": len(symbols),
        "processed_symbols": 0,
        "successful_symbols": 0,
        "failed_symbols": 0,
        "total_indicators_created": 0,
        "errors": [],
        "start_time": datetime.now().isoformat()
    }
    
    logger.info(f"Starting volatility indicators recompute for {len(symbols)} symbols")
    
    for symbol in symbols:
        try:
            logger.info(f"Processing volatility indicators for {symbol}")
            result = recompute_volatility_indicators_for_symbol(symbol, force_update)
            
            results["processed_symbols"] += 1
            
            if result["status"] == "success":
                results["successful_symbols"] += 1
                results["total_indicators_created"] += result.get("indicators_created", 0)
                logger.info(f"Volatility indicators calculated successfully for {symbol}: {result.get('indicators_created', 0)} indicators")
            elif result["status"] == "skipped":
                results["successful_symbols"] += 1
                logger.info(f"Volatility indicators skipped for {symbol}: {result.get('reason', 'Unknown')}")
            else:
                results["failed_symbols"] += 1
                results["errors"].append({
                    "symbol": symbol,
                    "error": result.get("error", "Unknown error")
                })
                logger.error(f"Failed to calculate volatility indicators for {symbol}: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            results["processed_symbols"] += 1
            results["failed_symbols"] += 1
            results["errors"].append({
                "symbol": symbol,
                "error": str(e)
            })
            logger.error(f"Error processing {symbol}: {e}")
    
    results["end_time"] = datetime.now().isoformat()
    results["duration"] = (datetime.fromisoformat(results["end_time"]) - 
                          datetime.fromisoformat(results["start_time"])).total_seconds()
    
    logger.info(f"Volatility indicators recompute completed: {results}")
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Recompute volatility indicators")
    parser.add_argument("--symbols", nargs="+", help="Symbols to recompute", default=["PLTR"])
    parser.add_argument("--force", action="store_true", help="Force recalculate")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Exécuter le recalcul
    results = recompute_volatility_indicators_for_symbols(args.symbols, args.force)
    
    # Afficher les résultats
    print("\n" + "="*80)
    print("VOLATILITY INDICATORS RECOMPUTE RESULTS")
    print("="*80)
    print(f"Total symbols: {results['total_symbols']}")
    print(f"Processed: {results['processed_symbols']}")
    print(f"Successful: {results['successful_symbols']}")
    print(f"Failed: {results['failed_symbols']}")
    print(f"Total indicators created: {results['total_indicators_created']}")
    print(f"Duration: {results['duration']:.2f} seconds")
    print(f"Success rate: {(results['successful_symbols']/results['processed_symbols']*100):.1f}%")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  {error['symbol']}: {error['error']}")
    
    print("="*80)
