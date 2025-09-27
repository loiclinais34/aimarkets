"""
Endpoints API pour l'analyse de sentiment.

Ce module expose les endpoints pour accéder aux fonctionnalités
d'analyse de sentiment et de volatilité.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from ...core.database import get_db
from ...services.sentiment_analysis import GARCHModels, MonteCarloSimulation, MarkovChainAnalysis, VolatilityForecaster
from ...models.sentiment_analysis import SentimentAnalysis, GARCHModels as GARCHModelsModel, MonteCarloSimulations, MarkovChainAnalysis as MarkovChainAnalysisModel, VolatilityForecasts
from ...utils.json_encoder import make_json_safe

router = APIRouter()


@router.get("/garch/{symbol}")
async def get_garch_analysis(
    symbol: str,
    model_type: str = "GARCH",
    period: int = 252,
    db: Session = Depends(get_db)
):
    """
    Récupère l'analyse GARCH pour un symbole.
    Calcule et persiste les résultats en base de données.
    
    Args:
        symbol: Symbole à analyser
        model_type: Type de modèle GARCH ("GARCH", "EGARCH", "GJR-GARCH")
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant l'analyse GARCH
    """
    try:
        # Récupérer les données historiques depuis la base de données locale
        from ...models.database import HistoricalData
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 an de données pour GARCH
        
        historical_records = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol,
            HistoricalData.date >= start_date.date(),
            HistoricalData.date <= end_date.date()
        ).order_by(HistoricalData.date).all()
        
        if not historical_records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune donnée historique trouvée pour {symbol} en base de données"
            )
        
        # Convertir en DataFrame
        data = []
        for record in historical_records:
            data.append({
                'date': record.date,
                'open': float(record.open),
                'high': float(record.high),
                'low': float(record.low),
                'close': float(record.close),
                'volume': int(record.volume)
            })
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Calculer les rendements
        returns = GARCHModels.calculate_returns(df['close'])
        
        if len(returns) < 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Pas assez de données pour ajuster un modèle GARCH. Requis: 100, Disponible: {len(returns)}"
            )
        
        # Effectuer l'analyse GARCH
        garch_analysis = GARCHModels.comprehensive_analysis(returns)
        
        # Persister les résultats en base de données
        try:
            # Extraire les données du modèle spécifique depuis model_comparison
            model_comparison = garch_analysis.get('model_comparison', {})
            volatility_forecast = garch_analysis.get('volatility_forecast', {})
            
            # Obtenir les données du modèle spécifique depuis la comparaison
            comparison_data = model_comparison.get('comparison', {})
            model_data = comparison_data.get(model_type, {})
            
            # Extraire les valeurs avec des valeurs par défaut appropriées
            volatility_forecast_value = volatility_forecast.get('current_volatility', 0) if isinstance(volatility_forecast, dict) else 0
            var_95_value = model_data.get('var_95', 0)
            var_99_value = model_data.get('var_99', 0)
            aic_value = model_data.get('aic', 0)
            bic_value = model_data.get('bic', 0)
            log_likelihood_value = model_data.get('log_likelihood', 0)
            
            # Extraire les résidus et volatilité conditionnelle (déjà convertis en listes)
            residuals_list = model_data.get('residuals', None)
            conditional_volatility_list = model_data.get('conditional_volatility', None)
            
            # Vérifier si un enregistrement existe déjà pour aujourd'hui
            existing_record = db.query(GARCHModelsModel).filter(
                GARCHModelsModel.symbol == symbol,
                GARCHModelsModel.model_type == model_type,
                GARCHModelsModel.analysis_date >= datetime.now().date()
            ).first()
            
            if existing_record:
                # Mettre à jour l'enregistrement existant
                existing_record.volatility_forecast = float(volatility_forecast_value)
                existing_record.var_95 = float(var_95_value)
                existing_record.var_99 = float(var_99_value)
                existing_record.aic = float(aic_value) if aic_value != 0 else None
                existing_record.bic = float(bic_value) if bic_value != 0 else None
                existing_record.log_likelihood = float(log_likelihood_value) if log_likelihood_value != 0 else None
                existing_record.model_parameters = model_comparison  # Stocker toute la comparaison
                existing_record.residuals = residuals_list  # Résidus du modèle
                existing_record.conditional_volatility = conditional_volatility_list  # Volatilité conditionnelle
            else:
                # Créer un nouvel enregistrement
                new_record = GARCHModelsModel(
                    symbol=symbol,
                    model_type=model_type,
                    analysis_date=datetime.now(),
                    volatility_forecast=float(volatility_forecast_value),
                    var_95=float(var_95_value),
                    var_99=float(var_99_value),
                    aic=float(aic_value) if aic_value != 0 else None,
                    bic=float(bic_value) if bic_value != 0 else None,
                    log_likelihood=float(log_likelihood_value) if log_likelihood_value != 0 else None,
                    model_parameters=model_comparison,  # Stocker toute la comparaison
                    residuals=residuals_list,  # Résidus du modèle
                    conditional_volatility=conditional_volatility_list,  # Volatilité conditionnelle
                    is_best_model=True  # Par défaut, considérer comme le meilleur modèle
                )
                db.add(new_record)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            print(f"Erreur lors de la persistance GARCH: {e}")
        
        return make_json_safe({
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "model_type": model_type,
            "period": period,
            "analysis": garch_analysis,
            "current_price": float(df['close'].iloc[-1]),
            "persisted": True
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse GARCH: {str(e)}"
        )


@router.get("/monte-carlo/{symbol}")
async def get_monte_carlo_simulation(
    symbol: str,
    simulations: int = 10000,
    time_horizon: int = 30,
    db: Session = Depends(get_db)
):
    """
    Récupère une simulation Monte Carlo pour un symbole.
    Calcule et persiste les résultats en base de données.
    
    Args:
        symbol: Symbole à analyser
        simulations: Nombre de simulations
        time_horizon: Horizon temporel en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant les résultats de simulation
    """
    try:
        # Récupérer les données historiques depuis la base de données locale
        from ...models.database import HistoricalData
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=252 + 50)  # 1 an de données
        
        historical_records = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol,
            HistoricalData.date >= start_date.date(),
            HistoricalData.date <= end_date.date()
        ).order_by(HistoricalData.date).all()
        
        if not historical_records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune donnée historique trouvée pour {symbol} en base de données"
            )
        
        # Convertir en DataFrame
        data = []
        for record in historical_records:
            data.append({
                'date': record.date,
                'open': float(record.open),
                'high': float(record.high),
                'low': float(record.low),
                'close': float(record.close),
                'volume': int(record.volume)
            })
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Calculer les paramètres
        current_price = float(df['close'].iloc[-1])
        returns = df['close'].pct_change().dropna()
        drift = float(returns.mean() * 252)  # Dérive annuelle
        volatility = float(returns.std() * (252 ** 0.5))  # Volatilité annuelle
        
        # Effectuer la simulation Monte Carlo
        simulation = MonteCarloSimulation()
        paths = simulation.simulate_price_paths(
            current_price=current_price,
            volatility=volatility,
            drift=drift,
            time_horizon=time_horizon,
            simulations=simulations
        )
        
        # Calculer les métriques de risque
        final_prices = paths[:, -1]
        returns_sim = (final_prices - current_price) / current_price
        
        var_95 = float(pd.Series(returns_sim).quantile(0.05))
        var_99 = float(pd.Series(returns_sim).quantile(0.01))
        expected_shortfall_95 = float(pd.Series(returns_sim)[pd.Series(returns_sim) <= var_95].mean())
        expected_shortfall_99 = float(pd.Series(returns_sim)[pd.Series(returns_sim) <= var_99].mean())
        
        monte_carlo_analysis = {
            'var_95': var_95,
            'var_99': var_99,
            'expected_shortfall_95': expected_shortfall_95,
            'expected_shortfall_99': expected_shortfall_99,
            'mean_return': float(pd.Series(returns_sim).mean()),
            'std_return': float(pd.Series(returns_sim).std()),
            'min_return': float(pd.Series(returns_sim).min()),
            'max_return': float(pd.Series(returns_sim).max()),
            'probability_positive_return': float((pd.Series(returns_sim) > 0).mean()),
            'stress_test_results': {},
            'tail_risk_analysis': {}
        }
        
        # Persister les résultats en base de données
        try:
            # Vérifier si un enregistrement existe déjà pour aujourd'hui
            existing_record = db.query(MonteCarloSimulations).filter(
                MonteCarloSimulations.symbol == symbol,
                MonteCarloSimulations.analysis_date >= datetime.now().date()
            ).first()
            
            if existing_record:
                # Mettre à jour l'enregistrement existant
                existing_record.current_price = current_price
                existing_record.volatility = volatility
                existing_record.drift = drift
                existing_record.time_horizon = time_horizon
                existing_record.simulations_count = simulations
                existing_record.var_95 = float(monte_carlo_analysis.get('var_95', 0))
                existing_record.var_99 = float(monte_carlo_analysis.get('var_99', 0))
                existing_record.expected_shortfall_95 = float(monte_carlo_analysis.get('expected_shortfall_95', 0))
                existing_record.expected_shortfall_99 = float(monte_carlo_analysis.get('expected_shortfall_99', 0))
                existing_record.mean_return = float(monte_carlo_analysis.get('mean_return', 0))
                existing_record.std_return = float(monte_carlo_analysis.get('std_return', 0))
                existing_record.min_return = float(monte_carlo_analysis.get('min_return', 0))
                existing_record.max_return = float(monte_carlo_analysis.get('max_return', 0))
                existing_record.probability_positive_return = float(monte_carlo_analysis.get('probability_positive_return', 0))
                existing_record.stress_test_results = monte_carlo_analysis.get('stress_test_results', {})
                existing_record.tail_risk_analysis = monte_carlo_analysis.get('tail_risk_analysis', {})
            else:
                # Créer un nouvel enregistrement
                new_record = MonteCarloSimulations(
                    symbol=symbol,
                    analysis_date=datetime.now(),
                    current_price=current_price,
                    volatility=volatility,
                    drift=drift,
                    time_horizon=time_horizon,
                    simulations_count=simulations,
                    var_95=float(monte_carlo_analysis.get('var_95', 0)),
                    var_99=float(monte_carlo_analysis.get('var_99', 0)),
                    expected_shortfall_95=float(monte_carlo_analysis.get('expected_shortfall_95', 0)),
                    expected_shortfall_99=float(monte_carlo_analysis.get('expected_shortfall_99', 0)),
                    mean_return=float(monte_carlo_analysis.get('mean_return', 0)),
                    std_return=float(monte_carlo_analysis.get('std_return', 0)),
                    min_return=float(monte_carlo_analysis.get('min_return', 0)),
                    max_return=float(monte_carlo_analysis.get('max_return', 0)),
                    probability_positive_return=float(monte_carlo_analysis.get('probability_positive_return', 0)),
                    stress_test_results=monte_carlo_analysis.get('stress_test_results', {}),
                    tail_risk_analysis=monte_carlo_analysis.get('tail_risk_analysis', {})
                )
                db.add(new_record)
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            print(f"Erreur lors de la persistance Monte Carlo: {e}")
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "current_price": current_price,
            "parameters": {
                "drift": drift,
                "volatility": volatility,
                "time_horizon": time_horizon,
                "simulations": simulations
            },
            "analysis": monte_carlo_analysis,
            "persisted": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la simulation Monte Carlo: {str(e)}"
        )


@router.get("/markov-test/{symbol}")
async def get_markov_test(symbol: str, db: Session = Depends(get_db)):
    """Test simple pour diagnostiquer l'erreur Markov"""
    try:
        return {
            "symbol": symbol,
            "test": "simple",
            "status": "ok"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur test: {str(e)}"
        )


@router.get("/markov/{symbol}")
async def get_markov_analysis(
    symbol: str,
    n_states: int = 3,
    period: int = 252,
    db: Session = Depends(get_db)
):
    """
    Récupère l'analyse des chaînes de Markov pour un symbole.
    Calcule et persiste les résultats en base de données.
    
    Args:
        symbol: Symbole à analyser
        n_states: Nombre d'états à identifier
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant l'analyse des chaînes de Markov
    """
    try:
        # Récupérer les données historiques depuis la base de données locale
        from ...models.database import HistoricalData
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 an de données
        
        historical_records = db.query(HistoricalData).filter(
            HistoricalData.symbol == symbol,
            HistoricalData.date >= start_date.date(),
            HistoricalData.date <= end_date.date()
        ).order_by(HistoricalData.date).all()
        
        if not historical_records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune donnée historique trouvée pour {symbol} en base de données"
            )
        
        # Convertir en DataFrame
        data = []
        for record in historical_records:
            data.append({
                'date': record.date,
                'open': float(record.open),
                'high': float(record.high),
                'low': float(record.low),
                'close': float(record.close),
                'volume': int(record.volume)
            })
        
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Calculer les rendements
        returns = df['close'].pct_change().dropna()
        
        if len(returns) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pas assez de données pour l'analyse des chaînes de Markov"
            )
        
        # Effectuer l'analyse des chaînes de Markov
        try:
            markov_analysis = MarkovChainAnalysis.comprehensive_markov_analysis(returns, n_states)
            analysis_success = True
        except Exception as e:
            print(f"Erreur dans comprehensive_markov_analysis: {e}")
            markov_analysis = {"error": str(e)}
            analysis_success = False
        
        # Persister les résultats en base de données
        persisted = False
        if analysis_success:
            try:
                # Extraire les données pour la persistance
                state_identification = markov_analysis.get('state_identification', {})
                transition_analysis = markov_analysis.get('transition_analysis', {})
                regime_analysis = markov_analysis.get('regime_analysis', {})
                future_predictions = markov_analysis.get('future_predictions', {})
                state_probabilities = markov_analysis.get('state_probabilities', {})
                
                # Extraire les valeurs avec des valeurs par défaut appropriées
                n_states_value = state_identification.get('n_states', n_states)
                current_state_value = markov_analysis.get('current_state', 0)
                
                # Convertir en types Python natifs pour éviter les erreurs de sérialisation
                n_states_value = int(n_states_value) if n_states_value is not None else n_states
                current_state_value = int(current_state_value) if current_state_value is not None else 0
                
                # Convertir les probabilités d'état en liste
                state_probabilities_list = []
                if isinstance(state_probabilities, pd.DataFrame):
                    # Convertir le DataFrame en liste de dictionnaires
                    state_probabilities_list = state_probabilities.to_dict('records')
                elif isinstance(state_probabilities, dict):
                    for i in range(n_states_value):
                        state_probabilities_list.append({
                            f'state_{i}': state_probabilities.get(f'state_{i}', 0.0)
                        })
                
                # Extraire la matrice de transition
                transition_matrix_data = {}
                if isinstance(transition_analysis, dict):
                    transition_matrix_raw = transition_analysis.get('transition_matrix', None)
                    if transition_matrix_raw is not None:
                        if hasattr(transition_matrix_raw, 'tolist'):
                            transition_matrix_data['matrix'] = transition_matrix_raw.tolist()
                        else:
                            transition_matrix_data['matrix'] = transition_matrix_raw
                    
                    stationary_probs = transition_analysis.get('stationary_probabilities', None)
                    if stationary_probs is not None:
                        if hasattr(stationary_probs, 'tolist'):
                            transition_matrix_data['stationary_probabilities'] = stationary_probs.tolist()
                        else:
                            transition_matrix_data['stationary_probabilities'] = stationary_probs
                
                # Extraire les changements de régime
                regime_changes_data = None
                if isinstance(regime_analysis, dict):
                    # Chercher 'regimes' au lieu de 'regime_changes'
                    regimes_raw = regime_analysis.get('regimes', None)
                    if regimes_raw is not None and isinstance(regimes_raw, list):
                        # Convertir les Timestamp pandas en strings
                        regime_changes_data = []
                        for regime in regimes_raw:
                            if isinstance(regime, dict):
                                regime_clean = {}
                                for k, v in regime.items():
                                    if hasattr(v, 'strftime'):  # Timestamp pandas
                                        regime_clean[k] = v.strftime('%Y-%m-%d')
                                    elif isinstance(v, (int, float, str, bool)):
                                        regime_clean[k] = v
                                    else:
                                        regime_clean[k] = str(v)
                                regime_changes_data.append(regime_clean)
                            else:
                                regime_changes_data.append(str(regime))
                
                # Extraire les prédictions futures
                future_predictions_data = None
                if isinstance(future_predictions, dict):
                    predictions_raw = future_predictions.get('predictions', None)
                    if predictions_raw is not None:
                        if isinstance(predictions_raw, pd.DataFrame):
                            # Convertir le DataFrame en liste de dictionnaires
                            future_predictions_data = predictions_raw.to_dict('records')
                        elif hasattr(predictions_raw, 'tolist'):
                            future_predictions_data = predictions_raw.tolist()
                        else:
                            future_predictions_data = predictions_raw
                    
                    # Ajouter aussi les autres métadonnées importantes
                    if future_predictions_data is not None:
                        future_predictions_enhanced = {
                            'predictions': future_predictions_data,
                            'most_likely_states': future_predictions.get('most_likely_states', []).tolist() if hasattr(future_predictions.get('most_likely_states', []), 'tolist') else future_predictions.get('most_likely_states', []),
                            'max_probabilities': future_predictions.get('max_probabilities', []).tolist() if hasattr(future_predictions.get('max_probabilities', []), 'tolist') else future_predictions.get('max_probabilities', []),
                            'horizon': int(future_predictions.get('horizon', 5)),
                            'current_state': int(future_predictions.get('current_state', 0))
                        }
                        future_predictions_data = future_predictions_enhanced
                
                # Nettoyer state_identification pour la persistance
                state_analysis_clean = {}
                if isinstance(state_identification, dict):
                    for key, value in state_identification.items():
                        if key == 'states' and hasattr(value, 'tolist'):
                            # Convertir la série pandas en liste
                            state_analysis_clean[key] = value.tolist()
                        elif key == 'model' and hasattr(value, '__dict__'):
                            # Ignorer l'objet modèle qui n'est pas sérialisable
                            continue
                        elif isinstance(value, (dict, list, str, int, float, bool)):
                            # Garder les types sérialisables
                            state_analysis_clean[key] = value
                        else:
                            # Convertir en string pour les autres types
                            state_analysis_clean[key] = str(value)
                
                # Vérifier si un enregistrement existe déjà pour aujourd'hui
                existing_record = db.query(MarkovChainAnalysisModel).filter(
                    MarkovChainAnalysisModel.symbol == symbol,
                    MarkovChainAnalysisModel.analysis_date >= datetime.now().date()
                ).first()
                
                if existing_record:
                    # Mettre à jour l'enregistrement existant
                    existing_record.n_states = n_states_value
                    existing_record.current_state = current_state_value
                    existing_record.state_probabilities = state_probabilities_list
                    existing_record.transition_matrix = transition_matrix_data
                    existing_record.stationary_probabilities = transition_matrix_data.get('stationary_probabilities', None)
                    existing_record.regime_changes = regime_changes_data
                    existing_record.future_state_predictions = future_predictions_data
                    existing_record.state_analysis = state_analysis_clean
                    existing_record.model_parameters = {
                        'method': state_identification.get('method', 'gmm'),
                        'n_states': n_states_value,
                        'state_labels': state_identification.get('state_labels', list(range(n_states_value)))
                    }
                else:
                    # Créer un nouvel enregistrement
                    new_record = MarkovChainAnalysisModel(
                        symbol=symbol,
                        analysis_date=datetime.now(),
                        n_states=n_states_value,
                        current_state=current_state_value,
                        state_probabilities=state_probabilities_list,
                        transition_matrix=transition_matrix_data,
                        stationary_probabilities=transition_matrix_data.get('stationary_probabilities', None),
                        regime_changes=regime_changes_data,
                        future_state_predictions=future_predictions_data,
                        state_analysis=state_analysis_clean,
                        model_parameters={
                            'method': state_identification.get('method', 'gmm'),
                            'n_states': n_states_value,
                            'state_labels': state_identification.get('state_labels', list(range(n_states_value)))
                        }
                    )
                    db.add(new_record)
                
                db.commit()
                persisted = True
                
            except Exception as e:
                db.rollback()
                print(f"Erreur lors de la persistance Markov: {e}")
        
        return make_json_safe({
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "n_states": n_states,
            "period": period,
            "analysis": markov_analysis,
            "current_price": float(df['close'].iloc[-1]),
            "analysis_success": analysis_success,
            "persisted": persisted
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse des chaînes de Markov: {str(e)}"
        )


@router.get("/volatility-forecast/{symbol}")
async def get_volatility_forecast(
    symbol: str,
    horizon: int = 5,
    period: int = 252,
    db: Session = Depends(get_db)
):
    """
    Récupère la prédiction de volatilité pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        horizon: Horizon de prédiction en jours
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant la prédiction de volatilité
    """
    try:
        # Récupérer les données historiques
        from ...services.polygon_service import PolygonService
        data_service = PolygonService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 an de données pour GARCH
        
        historical_data = data_service.get_historical_data(
            symbol=symbol,
            from_date=start_date.strftime('%Y-%m-%d'),
            to_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not historical_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune donnée historique trouvée pour {symbol}"
            )
        
        # Convertir en DataFrame
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Calculer les rendements
        returns = df['close'].pct_change().dropna()
        
        if len(returns) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pas assez de données pour la prédiction de volatilité"
            )
        
        # Effectuer la prédiction de volatilité
        volatility_forecaster = VolatilityForecaster()
        volatility_forecast = volatility_forecaster.comprehensive_volatility_forecast(returns, horizon)
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "horizon": horizon,
            "period": period,
            "forecast": volatility_forecast,
            "current_price": float(df['close'].iloc[-1])
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la prédiction de volatilité: {str(e)}"
        )


@router.get("/comprehensive/{symbol}")
async def get_comprehensive_sentiment_analysis(
    symbol: str,
    period: int = 252,
    db: Session = Depends(get_db)
):
    """
    Effectue une analyse de sentiment complète pour un symbole.
    
    Args:
        symbol: Symbole à analyser
        period: Période de calcul en jours
        db: Session de base de données
        
    Returns:
        Dictionnaire contenant l'analyse de sentiment complète
    """
    try:
        # Récupérer les données historiques
        from ...services.polygon_service import PolygonService
        data_service = PolygonService()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 1 an de données pour GARCH
        
        historical_data = data_service.get_historical_data(
            symbol=symbol,
            from_date=start_date.strftime('%Y-%m-%d'),
            to_date=end_date.strftime('%Y-%m-%d')
        )
        
        if not historical_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucune donnée historique trouvée pour {symbol}"
            )
        
        # Convertir en DataFrame
        df = pd.DataFrame(historical_data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        # Calculer les rendements
        returns = df['close'].pct_change().dropna()
        
        if len(returns) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Pas assez de données pour l'analyse de sentiment"
            )
        
        # Effectuer toutes les analyses
        garch_analysis = GARCHModels.comprehensive_analysis(returns)
        markov_analysis = MarkovChainAnalysis.comprehensive_markov_analysis(returns)
        
        # Simulation Monte Carlo
        current_price = float(df['close'].iloc[-1])
        drift = float(returns.mean() * 252)
        volatility = float(returns.std() * (252 ** 0.5))
        monte_carlo_analysis = MonteCarloSimulation.comprehensive_monte_carlo_analysis(
            current_price, volatility, drift, 30, 10000
        )
        
        # Prédiction de volatilité
        volatility_forecaster = VolatilityForecaster()
        volatility_forecast = volatility_forecaster.comprehensive_volatility_forecast(returns, 5)
        
        return {
            "symbol": symbol,
            "analysis_date": datetime.now().isoformat(),
            "period": period,
            "current_price": current_price,
            "garch_analysis": garch_analysis,
            "markov_analysis": markov_analysis,
            "monte_carlo_analysis": monte_carlo_analysis,
            "volatility_forecast": volatility_forecast,
            "summary": {
                "volatility_regime": volatility_forecast.get("risk_metrics", {}).get("risk_level", "Unknown"),
                "market_state": markov_analysis.get("current_state", "Unknown"),
                "var_95": monte_carlo_analysis.get("risk_metrics", {}).get("var_95", 0.0),
                "var_99": monte_carlo_analysis.get("risk_metrics", {}).get("var_99", 0.0),
                "confidence": garch_analysis.get("model_comparison", {}).get("best_model_results", {}).get("log_likelihood", 0.0)
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de l'analyse de sentiment complète: {str(e)}"
        )
