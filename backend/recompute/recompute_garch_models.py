#!/usr/bin/env python3
"""
Script de recalcul des modèles GARCH
Calcule les modèles GARCH pour la prévision de volatilité
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
from app.models.sentiment_analysis import GARCHModels

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GARCHModelCalculator:
    """Calculateur de modèles GARCH"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def calculate_garch_models(self, symbol: str, force_update: bool = False) -> dict:
        """
        Calcule les modèles GARCH pour un symbole
        
        Args:
            symbol: Symbole à traiter
            force_update: Forcer le recalcul
        
        Returns:
            Dict contenant le résultat du calcul
        """
        try:
            logger.info(f"Calculating GARCH models for {symbol}")
            
            # Vérifier si les modèles existent déjà et sont récents
            if not force_update:
                latest_model = self.db.query(GARCHModels)\
                    .filter(GARCHModels.symbol == symbol)\
                    .order_by(GARCHModels.created_at.desc())\
                    .first()
                
                if latest_model and latest_model.created_at >= datetime.now() - timedelta(days=1):
                    logger.info(f"GARCH models for {symbol} are already up to date")
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
                    'close': float(row.close)
                })
            
            df = pd.DataFrame(data)
            df = df.sort_values('date').reset_index(drop=True)
            
            # Supprimer les anciens modèles si force_update
            if force_update:
                self.db.query(GARCHModels).filter(GARCHModels.symbol == symbol).delete()
            
            # Calculer les rendements
            df['returns'] = np.log(df['close'] / df['close'].shift(1))
            df = df.dropna()
            
            if len(df) < 50:
                logger.warning(f"Insufficient data for GARCH modeling for {symbol}")
                return {"status": "error", "symbol": symbol, "error": "Insufficient data"}
            
            # Calculer les modèles GARCH
            models_created = self._calculate_garch_variants(df, symbol)
            
            logger.info(f"GARCH models calculated for {symbol}: {models_created} models")
            return {
                "status": "success", 
                "symbol": symbol, 
                "models_created": models_created
            }
            
        except Exception as e:
            logger.error(f"Error calculating GARCH models for {symbol}: {e}")
            self.db.rollback()
            return {"status": "error", "symbol": symbol, "error": str(e)}
    
    def _calculate_garch_variants(self, df: pd.DataFrame, symbol: str) -> int:
        """Calculer les variantes GARCH"""
        returns = df['returns'].values
        models_created = 0
        
        # GARCH(1,1) - Modèle de base
        garch_result = self._fit_garch_11(returns)
        if garch_result:
            model = GARCHModels(
                symbol=symbol,
                model_type="GARCH(1,1)",
                analysis_date=datetime.now(),
                volatility_forecast=garch_result['volatility_forecast'],
                var_95=garch_result['var_95'],
                var_99=garch_result['var_99'],
                aic=garch_result['aic'],
                bic=garch_result['bic'],
                log_likelihood=garch_result['log_likelihood'],
                model_parameters=garch_result['parameters'],
                residuals=garch_result['residuals'],
                conditional_volatility=garch_result['conditional_volatility'],
                is_best_model=True  # Pour l'instant, seul modèle
            )
            self.db.add(model)
            models_created += 1
        
        # EGARCH(1,1) - Modèle avec effet de levier
        egarch_result = self._fit_egarch_11(returns)
        if egarch_result:
            model = GARCHModels(
                symbol=symbol,
                model_type="EGARCH(1,1)",
                analysis_date=datetime.now(),
                volatility_forecast=egarch_result['volatility_forecast'],
                var_95=egarch_result['var_95'],
                var_99=egarch_result['var_99'],
                aic=egarch_result['aic'],
                bic=egarch_result['bic'],
                log_likelihood=egarch_result['log_likelihood'],
                model_parameters=egarch_result['parameters'],
                residuals=egarch_result['residuals'],
                conditional_volatility=egarch_result['conditional_volatility'],
                is_best_model=False
            )
            self.db.add(model)
            models_created += 1
        
        self.db.commit()
        return models_created
    
    def _fit_garch_11(self, returns: np.ndarray) -> dict:
        """Ajuster un modèle GARCH(1,1) simplifié"""
        try:
            # Calculer la volatilité historique
            volatility = np.std(returns) * np.sqrt(252)
            
            # Paramètres simplifiés pour GARCH(1,1)
            omega = 0.0001  # Variance inconditionnelle
            alpha = 0.1    # Coefficient ARCH
            beta = 0.85    # Coefficient GARCH
            
            # Calculer la volatilité conditionnelle
            conditional_vol = np.zeros(len(returns))
            conditional_vol[0] = volatility
            
            for i in range(1, len(returns)):
                conditional_vol[i] = np.sqrt(omega + alpha * returns[i-1]**2 + beta * conditional_vol[i-1]**2)
            
            # Prévision de volatilité (1 jour)
            volatility_forecast = np.sqrt(omega + alpha * returns[-1]**2 + beta * conditional_vol[-1]**2)
            
            # Calculer VaR
            var_95 = -1.645 * volatility_forecast
            var_99 = -2.326 * volatility_forecast
            
            # Métriques simplifiées
            aic = -2 * len(returns) * np.log(volatility_forecast) + 2 * 3  # 3 paramètres
            bic = -2 * len(returns) * np.log(volatility_forecast) + np.log(len(returns)) * 3
            log_likelihood = -len(returns) * np.log(volatility_forecast)
            
            return {
                'volatility_forecast': float(volatility_forecast),
                'var_95': float(var_95),
                'var_99': float(var_99),
                'aic': float(aic),
                'bic': float(bic),
                'log_likelihood': float(log_likelihood),
                'parameters': {
                    'omega': omega,
                    'alpha': alpha,
                    'beta': beta
                },
                'residuals': returns.tolist()[-50:],  # 50 dernières valeurs
                'conditional_volatility': conditional_vol.tolist()[-50:]
            }
            
        except Exception as e:
            logger.error(f"Error fitting GARCH(1,1): {e}")
            return None
    
    def _fit_egarch_11(self, returns: np.ndarray) -> dict:
        """Ajuster un modèle EGARCH(1,1) simplifié"""
        try:
            # Calculer la volatilité historique
            volatility = np.std(returns) * np.sqrt(252)
            
            # Paramètres simplifiés pour EGARCH(1,1)
            omega = 0.0001  # Variance inconditionnelle
            alpha = 0.1     # Coefficient ARCH
            gamma = 0.05   # Coefficient d'asymétrie
            beta = 0.85    # Coefficient GARCH
            
            # Calculer la volatilité conditionnelle
            conditional_vol = np.zeros(len(returns))
            conditional_vol[0] = volatility
            
            for i in range(1, len(returns)):
                # EGARCH avec effet de levier
                log_var = omega + alpha * (abs(returns[i-1]) / conditional_vol[i-1] - np.sqrt(2/np.pi)) + \
                         gamma * returns[i-1] / conditional_vol[i-1] + beta * np.log(conditional_vol[i-1]**2)
                conditional_vol[i] = np.sqrt(np.exp(log_var))
            
            # Prévision de volatilité (1 jour)
            log_var_forecast = omega + alpha * (abs(returns[-1]) / conditional_vol[-1] - np.sqrt(2/np.pi)) + \
                              gamma * returns[-1] / conditional_vol[-1] + beta * np.log(conditional_vol[-1]**2)
            volatility_forecast = np.sqrt(np.exp(log_var_forecast))
            
            # Calculer VaR
            var_95 = -1.645 * volatility_forecast
            var_99 = -2.326 * volatility_forecast
            
            # Métriques simplifiées
            aic = -2 * len(returns) * np.log(volatility_forecast) + 2 * 4  # 4 paramètres
            bic = -2 * len(returns) * np.log(volatility_forecast) + np.log(len(returns)) * 4
            log_likelihood = -len(returns) * np.log(volatility_forecast)
            
            return {
                'volatility_forecast': float(volatility_forecast),
                'var_95': float(var_95),
                'var_99': float(var_99),
                'aic': float(aic),
                'bic': float(bic),
                'log_likelihood': float(log_likelihood),
                'parameters': {
                    'omega': omega,
                    'alpha': alpha,
                    'gamma': gamma,
                    'beta': beta
                },
                'residuals': returns.tolist()[-50:],  # 50 dernières valeurs
                'conditional_volatility': conditional_vol.tolist()[-50:]
            }
            
        except Exception as e:
            logger.error(f"Error fitting EGARCH(1,1): {e}")
            return None

def recompute_garch_models_for_symbol(symbol: str, force_update: bool = False) -> dict:
    """
    Recalculer les modèles GARCH pour un symbole
    
    Args:
        symbol: Symbole à traiter
        force_update: Forcer le recalcul
    
    Returns:
        Dict contenant le résultat
    """
    try:
        db = next(get_db())
        calculator = GARCHModelCalculator(db)
        result = calculator.calculate_garch_models(symbol, force_update)
        return result
    except Exception as e:
        logger.error(f"Error in recompute_garch_models_for_symbol: {e}")
        return {"status": "error", "symbol": symbol, "error": str(e)}
    finally:
        db.close()

def recompute_garch_models_for_symbols(symbols: list, force_update: bool = False) -> dict:
    """
    Recalculer les modèles GARCH pour plusieurs symboles
    
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
        "total_models_created": 0,
        "errors": [],
        "start_time": datetime.now().isoformat()
    }
    
    logger.info(f"Starting GARCH models recompute for {len(symbols)} symbols")
    
    for symbol in symbols:
        try:
            logger.info(f"Processing GARCH models for {symbol}")
            result = recompute_garch_models_for_symbol(symbol, force_update)
            
            results["processed_symbols"] += 1
            
            if result["status"] == "success":
                results["successful_symbols"] += 1
                results["total_models_created"] += result.get("models_created", 0)
                logger.info(f"GARCH models calculated successfully for {symbol}: {result.get('models_created', 0)} models")
            elif result["status"] == "skipped":
                results["successful_symbols"] += 1
                logger.info(f"GARCH models skipped for {symbol}: {result.get('reason', 'Unknown')}")
            else:
                results["failed_symbols"] += 1
                results["errors"].append({
                    "symbol": symbol,
                    "error": result.get("error", "Unknown error")
                })
                logger.error(f"Failed to calculate GARCH models for {symbol}: {result.get('error', 'Unknown error')}")
                
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
    
    logger.info(f"GARCH models recompute completed: {results}")
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Recompute GARCH models")
    parser.add_argument("--symbols", nargs="+", help="Symbols to recompute", default=["PLTR"])
    parser.add_argument("--force", action="store_true", help="Force recalculate")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Exécuter le recalcul
    results = recompute_garch_models_for_symbols(args.symbols, args.force)
    
    # Afficher les résultats
    print("\n" + "="*80)
    print("GARCH MODELS RECOMPUTE RESULTS")
    print("="*80)
    print(f"Total symbols: {results['total_symbols']}")
    print(f"Processed: {results['processed_symbols']}")
    print(f"Successful: {results['successful_symbols']}")
    print(f"Failed: {results['failed_symbols']}")
    print(f"Total models created: {results['total_models_created']}")
    print(f"Duration: {results['duration']:.2f} seconds")
    print(f"Success rate: {(results['successful_symbols']/results['processed_symbols']*100):.1f}%")
    
    if results['errors']:
        print("\nErrors:")
        for error in results['errors']:
            print(f"  {error['symbol']}: {error['error']}")
    
    print("="*80)
