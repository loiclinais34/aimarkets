"""
Service d'Intégration du Framework de Comparaison de Modèles
============================================================

Ce service intègre le framework de comparaison de modèles avec notre
système existant de ML et de données financières.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from .model_comparison_framework import (
    ModelComparisonFramework, 
    RandomForestModel, 
    XGBoostModel, 
    LightGBMModel, 
    NeuralNetworkModel
)
from ..models.database import (
    MLModels, MLPredictions, HistoricalData, 
    TechnicalIndicators, SentimentIndicators, SymbolMetadata
)

logger = logging.getLogger(__name__)

class ModelComparisonService:
    """Service pour comparer les modèles ML avec nos données financières"""
    
    def __init__(self, db: Session):
        self.db = db
        self.framework = ModelComparisonFramework()
        
    def prepare_training_data(
        self, 
        symbol: str, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        lookback_days: int = 30
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Préparer les données d'entraînement pour un symbole donné
        
        Args:
            symbol: Symbole à analyser
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)
            lookback_days: Nombre de jours de lookback pour les features
        
        Returns:
            Tuple contenant (X_train, y_train, X_test, y_test, prices)
        """
        try:
            logger.info(f"Préparation des données pour {symbol}")
            
            # Déterminer les dates si non fournies
            if not start_date:
                start_date = date.today() - timedelta(days=365)
            if not end_date:
                end_date = date.today()
            
            # Récupérer les données historiques
            historical_data = self.db.query(HistoricalData).filter(
                and_(
                    HistoricalData.symbol == symbol,
                    HistoricalData.date >= start_date,
                    HistoricalData.date <= end_date
                )
            ).order_by(HistoricalData.date.asc()).all()
            
            if len(historical_data) < lookback_days + 10:
                raise ValueError(f"Pas assez de données historiques pour {symbol}")
            
            # Récupérer les indicateurs techniques
            technical_data = self.db.query(TechnicalIndicators).filter(
                and_(
                    TechnicalIndicators.symbol == symbol,
                    TechnicalIndicators.date >= start_date,
                    TechnicalIndicators.date <= end_date
                )
            ).order_by(TechnicalIndicators.date.asc()).all()
            
            # Récupérer les indicateurs de sentiment
            sentiment_data = self.db.query(SentimentIndicators).filter(
                and_(
                    SentimentIndicators.symbol == symbol,
                    SentimentIndicators.date >= start_date,
                    SentimentIndicators.date <= end_date
                )
            ).order_by(SentimentIndicators.date.asc()).all()
            
            # Créer un DataFrame combiné
            df = self._create_combined_dataframe(
                historical_data, technical_data, sentiment_data
            )
            
            if df.empty:
                raise ValueError(f"Aucune donnée combinée trouvée pour {symbol}")
            
            # Créer les features et labels
            X, y, prices = self._create_features_and_labels(df, lookback_days)
            
            # Diviser en train/test (80/20)
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X[:split_idx], X[split_idx:]
            y_train, y_test = y[:split_idx], y[split_idx:]
            prices_test = prices[split_idx:]
            
            logger.info(f"Données préparées: {len(X_train)} train, {len(X_test)} test")
            return X_train, y_train, X_test, y_test, prices_test
            
        except Exception as e:
            logger.error(f"Erreur lors de la préparation des données pour {symbol}: {e}")
            raise
    
    def _create_combined_dataframe(
        self, 
        historical_data: List[HistoricalData],
        technical_data: List[TechnicalIndicators],
        sentiment_data: List[SentimentIndicators]
    ) -> pd.DataFrame:
        """Créer un DataFrame combiné avec toutes les données"""
        
        # DataFrame historique
        hist_df = pd.DataFrame([{
            'date': h.date,
            'open': float(h.open),
            'high': float(h.high),
            'low': float(h.low),
            'close': float(h.close),
            'volume': h.volume,
            'vwap': float(h.vwap) if h.vwap else None
        } for h in historical_data])
        
        # DataFrame technique
        tech_df = pd.DataFrame([{
            'date': t.date,
            'sma_20': float(t.sma_20) if t.sma_20 else None,
            'sma_50': float(t.sma_50) if t.sma_50 else None,
            'ema_12': float(t.ema_12) if t.ema_12 else None,
            'ema_26': float(t.ema_26) if t.ema_26 else None,
            'rsi': float(t.rsi) if t.rsi else None,
            'macd': float(t.macd) if t.macd else None,
            'macd_signal': float(t.macd_signal) if t.macd_signal else None,
            'bb_upper': float(t.bb_upper) if t.bb_upper else None,
            'bb_middle': float(t.bb_middle) if t.bb_middle else None,
            'bb_lower': float(t.bb_lower) if t.bb_lower else None,
            'bb_position': float(t.bb_position) if t.bb_position else None,
            'atr': float(t.atr) if t.atr else None,
            'obv': float(t.obv) if t.obv else None,
            'stochastic_k': float(t.stochastic_k) if t.stochastic_k else None,
            'stochastic_d': float(t.stochastic_d) if t.stochastic_d else None,
            'williams_r': float(t.williams_r) if t.williams_r else None,
            'roc': float(t.roc) if t.roc else None,
            'cci': float(t.cci) if t.cci else None
        } for t in technical_data])
        
        # DataFrame sentiment
        sent_df = pd.DataFrame([{
            'date': s.date,
            'sentiment_score': float(s.sentiment_score) if s.sentiment_score else None,
            'sentiment_momentum': float(s.sentiment_momentum) if s.sentiment_momentum else None,
            'sentiment_volatility': float(s.sentiment_volatility) if s.sentiment_volatility else None,
            'news_count': s.news_count if s.news_count else 0,
            'short_interest': float(s.short_interest) if s.short_interest else None,
            'short_volume': float(s.short_volume) if s.short_volume else None,
            'short_volume_ratio': float(s.short_volume_ratio) if s.short_volume_ratio else None
        } for s in sentiment_data])
        
        # Combiner les DataFrames
        df = hist_df.copy()
        
        # Joindre les données techniques
        if not tech_df.empty:
            df = df.merge(tech_df, on='date', how='left')
        
        # Joindre les données de sentiment
        if not sent_df.empty:
            df = df.merge(sent_df, on='date', how='left')
        
        # Trier par date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Remplacer les NaN par des valeurs par défaut
        df = df.fillna(method='ffill').fillna(0)
        
        return df
    
    def _create_features_and_labels(
        self, 
        df: pd.DataFrame, 
        lookback_days: int
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Créer les features et labels pour l'entraînement"""
        
        # Calculer les returns
        df['return'] = df['close'].pct_change()
        df['return_5d'] = df['close'].pct_change(5)
        df['return_10d'] = df['close'].pct_change(10)
        df['return_20d'] = df['close'].pct_change(20)
        
        # Calculer les volumes relatifs
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        
        # Calculer les volatilités
        df['volatility_5d'] = df['return'].rolling(5).std()
        df['volatility_20d'] = df['return'].rolling(20).std()
        
        # Calculer les prix relatifs aux moyennes mobiles
        df['price_vs_sma20'] = (df['close'] - df['sma_20']) / df['sma_20']
        df['price_vs_sma50'] = (df['close'] - df['sma_50']) / df['sma_50']
        
        # Calculer les spreads Bollinger
        df['bb_spread'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        
        # Créer les labels (signal d'achat si return futur > 2%)
        df['future_return'] = df['close'].shift(-5) / df['close'] - 1
        df['label'] = (df['future_return'] > 0.02).astype(int)
        
        # Sélectionner les features
        feature_columns = [
            'return', 'return_5d', 'return_10d', 'return_20d',
            'volume_ratio', 'volatility_5d', 'volatility_20d',
            'price_vs_sma20', 'price_vs_sma50', 'bb_spread',
            'rsi', 'macd', 'macd_signal', 'bb_position',
            'atr', 'stochastic_k', 'stochastic_d', 'williams_r',
            'roc', 'cci', 'sentiment_score', 'sentiment_momentum',
            'sentiment_volatility', 'news_count', 'short_interest',
            'short_volume_ratio'
        ]
        
        # Filtrer les colonnes disponibles
        available_features = [col for col in feature_columns if col in df.columns]
        
        # Créer les features avec lookback
        X_list = []
        y_list = []
        prices_list = []
        
        for i in range(lookback_days, len(df) - 5):  # -5 pour éviter les NaN des future_return
            # Features avec lookback
            features = []
            for j in range(i - lookback_days, i):
                row_features = df.iloc[j][available_features].values
                features.extend(row_features)
            
            X_list.append(features)
            y_list.append(df.iloc[i]['label'])
            prices_list.append(df.iloc[i]['close'])
        
        X = np.array(X_list)
        y = np.array(y_list)
        prices = np.array(prices_list)
        
        # Supprimer les lignes avec des NaN
        valid_mask = ~(np.isnan(X).any(axis=1) | np.isnan(y) | np.isnan(prices))
        X = X[valid_mask]
        y = y[valid_mask]
        prices = prices[valid_mask]
        
        logger.info(f"Features créées: {X.shape}, Labels: {y.shape}")
        return X, y, prices
    
    def compare_models_for_symbol(
        self, 
        symbol: str,
        models_to_test: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Comparer les modèles pour un symbole donné
        
        Args:
            symbol: Symbole à analyser
            models_to_test: Liste des modèles à tester
            start_date: Date de début
            end_date: Date de fin
        
        Returns:
            Résultats de la comparaison
        """
        try:
            logger.info(f"Début de la comparaison de modèles pour {symbol}")
            
            # Préparer les données
            X_train, y_train, X_test, y_test, prices = self.prepare_training_data(
                symbol, start_date, end_date
            )
            
            if len(X_train) == 0 or len(X_test) == 0:
                raise ValueError(f"Pas assez de données pour {symbol}")
            
            # Comparer les modèles
            results = self.framework.compare_models(
                X_train, y_train, X_test, y_test, prices, models_to_test
            )
            
            # Générer le rapport
            report = self.framework.generate_report()
            
            # Obtenir le meilleur modèle
            best_model_name, best_metrics = self.framework.get_best_model('f1_score')
            
            return {
                'success': True,
                'symbol': symbol,
                'results': results,
                'best_model': {
                    'name': best_model_name,
                    'metrics': {
                        'accuracy': best_metrics.accuracy,
                        'f1_score': best_metrics.f1_score,
                        'sharpe_ratio': best_metrics.sharpe_ratio,
                        'total_return': best_metrics.total_return
                    }
                },
                'report': report,
                'data_info': {
                    'train_samples': len(X_train),
                    'test_samples': len(X_test),
                    'features': X_train.shape[1]
                }
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la comparaison pour {symbol}: {e}")
            return {
                'success': False,
                'symbol': symbol,
                'error': str(e)
            }
    
    def compare_models_for_multiple_symbols(
        self, 
        symbols: List[str],
        models_to_test: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Comparer les modèles pour plusieurs symboles
        
        Args:
            symbols: Liste des symboles à analyser
            models_to_test: Liste des modèles à tester
        
        Returns:
            Résultats agrégés de la comparaison
        """
        logger.info(f"Début de la comparaison pour {len(symbols)} symboles")
        
        results = {}
        successful_symbols = []
        failed_symbols = []
        
        for symbol in symbols:
            try:
                result = self.compare_models_for_symbol(symbol, models_to_test)
                if result['success']:
                    results[symbol] = result
                    successful_symbols.append(symbol)
                else:
                    failed_symbols.append(symbol)
                    logger.warning(f"Échec pour {symbol}: {result.get('error', 'Unknown error')}")
            except Exception as e:
                failed_symbols.append(symbol)
                logger.error(f"Erreur critique pour {symbol}: {e}")
        
        # Calculer les statistiques agrégées
        if successful_symbols:
            # Compter les victoires par modèle
            model_wins = {}
            for symbol in successful_symbols:
                best_model = results[symbol]['best_model']['name']
                model_wins[best_model] = model_wins.get(best_model, 0) + 1
            
            # Calculer les métriques moyennes par modèle
            model_avg_metrics = {}
            for symbol in successful_symbols:
                for model_name, metrics in results[symbol]['results'].items():
                    if model_name not in model_avg_metrics:
                        model_avg_metrics[model_name] = {
                            'accuracy': [],
                            'f1_score': [],
                            'sharpe_ratio': [],
                            'total_return': []
                        }
                    
                    model_avg_metrics[model_name]['accuracy'].append(metrics.accuracy)
                    model_avg_metrics[model_name]['f1_score'].append(metrics.f1_score)
                    model_avg_metrics[model_name]['sharpe_ratio'].append(metrics.sharpe_ratio)
                    model_avg_metrics[model_name]['total_return'].append(metrics.total_return)
            
            # Calculer les moyennes
            for model_name in model_avg_metrics:
                for metric in model_avg_metrics[model_name]:
                    values = model_avg_metrics[model_name][metric]
                    model_avg_metrics[model_name][metric] = {
                        'mean': np.mean(values),
                        'std': np.std(values),
                        'min': np.min(values),
                        'max': np.max(values)
                    }
        
        return {
            'success': True,
            'summary': {
                'total_symbols': len(symbols),
                'successful_symbols': len(successful_symbols),
                'failed_symbols': len(failed_symbols),
                'success_rate': len(successful_symbols) / len(symbols) if symbols else 0
            },
            'model_wins': model_wins if successful_symbols else {},
            'model_avg_metrics': model_avg_metrics if successful_symbols else {},
            'results': results,
            'failed_symbols': failed_symbols
        }
    
    def get_available_symbols(self) -> List[str]:
        """Obtenir la liste des symboles disponibles pour la comparaison"""
        try:
            # Récupérer les symboles avec des données historiques récentes
            symbols = self.db.query(HistoricalData.symbol).filter(
                HistoricalData.date >= date.today() - timedelta(days=30)
            ).distinct().all()
            
            return [s[0] for s in symbols]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des symboles: {e}")
            return []
    
    def get_model_recommendations(self, symbol: str) -> Dict[str, Any]:
        """
        Obtenir des recommandations de modèles pour un symbole donné
        
        Args:
            symbol: Symbole à analyser
        
        Returns:
            Recommandations de modèles
        """
        try:
            # Analyser les caractéristiques du symbole
            symbol_analysis = self._analyze_symbol_characteristics(symbol)
            
            # Recommander des modèles basés sur les caractéristiques
            recommendations = self._get_model_recommendations(symbol_analysis)
            
            return {
                'success': True,
                'symbol': symbol,
                'analysis': symbol_analysis,
                'recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de {symbol}: {e}")
            return {
                'success': False,
                'symbol': symbol,
                'error': str(e)
            }
    
    def _analyze_symbol_characteristics(self, symbol: str) -> Dict[str, Any]:
        """Analyser les caractéristiques d'un symbole"""
        try:
            # Récupérer les données récentes
            recent_data = self.db.query(HistoricalData).filter(
                and_(
                    HistoricalData.symbol == symbol,
                    HistoricalData.date >= date.today() - timedelta(days=90)
                )
            ).order_by(HistoricalData.date.desc()).limit(90).all()
            
            if not recent_data:
                raise ValueError(f"Pas de données récentes pour {symbol}")
            
            # Calculer les caractéristiques
            prices = [float(d.close) for d in recent_data]
            volumes = [d.volume for d in recent_data]
            
            # Volatilité
            returns = np.diff(prices) / prices[:-1]
            volatility = np.std(returns) * np.sqrt(252)
            
            # Volume moyen
            avg_volume = np.mean(volumes)
            
            # Tendance
            price_change = (prices[0] - prices[-1]) / prices[-1]
            
            # Classification
            if volatility > 0.3:
                volatility_class = 'high'
            elif volatility > 0.15:
                volatility_class = 'medium'
            else:
                volatility_class = 'low'
            
            if price_change > 0.1:
                trend_class = 'bullish'
            elif price_change < -0.1:
                trend_class = 'bearish'
            else:
                trend_class = 'sideways'
            
            return {
                'volatility': volatility,
                'volatility_class': volatility_class,
                'trend': price_change,
                'trend_class': trend_class,
                'avg_volume': avg_volume,
                'data_points': len(recent_data)
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de {symbol}: {e}")
            raise
    
    def _get_model_recommendations(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Obtenir des recommandations de modèles basées sur l'analyse"""
        
        recommendations = {
            'primary': [],
            'secondary': [],
            'avoid': [],
            'reasoning': []
        }
        
        volatility_class = analysis['volatility_class']
        trend_class = analysis['trend_class']
        
        # Recommandations basées sur la volatilité
        if volatility_class == 'high':
            recommendations['primary'].extend(['XGBoost', 'LightGBM'])
            recommendations['secondary'].append('RandomForest')
            recommendations['avoid'].append('NeuralNetwork')
            recommendations['reasoning'].append("Haute volatilité: modèles robustes recommandés")
        
        elif volatility_class == 'medium':
            recommendations['primary'].extend(['RandomForest', 'XGBoost'])
            recommendations['secondary'].extend(['LightGBM', 'NeuralNetwork'])
            recommendations['reasoning'].append("Volatilité modérée: tous les modèles peuvent fonctionner")
        
        else:  # low volatility
            recommendations['primary'].extend(['NeuralNetwork', 'RandomForest'])
            recommendations['secondary'].append('XGBoost')
            recommendations['avoid'].append('LightGBM')
            recommendations['reasoning'].append("Faible volatilité: modèles complexes peuvent sur-ajuster")
        
        # Recommandations basées sur la tendance
        if trend_class == 'bullish':
            recommendations['reasoning'].append("Tendance haussière: privilégier les modèles de momentum")
        elif trend_class == 'bearish':
            recommendations['reasoning'].append("Tendance baissière: modèles robustes recommandés")
        else:
            recommendations['reasoning'].append("Tendance latérale: modèles de mean reversion")
        
        # Supprimer les doublons
        recommendations['primary'] = list(set(recommendations['primary']))
        recommendations['secondary'] = list(set(recommendations['secondary']))
        recommendations['avoid'] = list(set(recommendations['avoid']))
        
        return recommendations
