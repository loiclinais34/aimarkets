"""
Pipeline principal pour le backtesting ML
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging

from app.services.ml_backtesting.historical_opportunity_generator import HistoricalOpportunityGenerator
from app.services.ml_backtesting.opportunity_validator import OpportunityValidator

logger = logging.getLogger(__name__)


class BacktestingPipeline:
    """
    Pipeline principal pour le backtesting ML
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.generator = HistoricalOpportunityGenerator(db)
        self.validator = OpportunityValidator(db)
    
    async def run_full_backtest(
        self,
        start_date: date,
        end_date: date,
        symbols: Optional[List[str]] = None,
        limit_symbols: Optional[int] = None,
        validation_periods: List[int] = [1, 7, 30]
    ) -> Dict[str, Any]:
        """
        Exécute un backtest complet
        
        Args:
            start_date: Date de début du backtest
            end_date: Date de fin du backtest
            symbols: Liste des symboles à tester
            limit_symbols: Limite du nombre de symboles
            validation_periods: Périodes de validation
        
        Returns:
            Résultats du backtest
        """
        try:
            logger.info(f"Démarrage du backtest du {start_date} au {end_date}")
            
            # Étape 1: Génération des opportunités historiques
            logger.info("Étape 1: Génération des opportunités historiques")
            opportunities = await self.generator.generate_opportunities_for_date_range(
                start_date=start_date,
                end_date=end_date,
                symbols=symbols,
                limit_symbols=limit_symbols
            )
            
            logger.info(f"{len(opportunities)} opportunités générées")
            
            # Étape 2: Validation des performances
            logger.info("Étape 2: Validation des performances")
            validation_results = await self.validator.validate_opportunities_batch(
                opportunities=opportunities,
                validation_periods=validation_periods
            )
            
            logger.info(f"{len(validation_results)} opportunités validées")
            
            # Étape 3: Analyse des résultats
            logger.info("Étape 3: Analyse des résultats")
            analysis_results = self._analyze_backtest_results(validation_results)
            
            # Étape 4: Génération du rapport
            logger.info("Étape 4: Génération du rapport")
            report = self._generate_backtest_report(
                start_date=start_date,
                end_date=end_date,
                opportunities_count=len(opportunities),
                validation_results=validation_results,
                analysis_results=analysis_results
            )
            
            logger.info("Backtest terminé avec succès")
            
            return report
            
        except Exception as e:
            logger.error(f"Erreur lors du backtest: {e}")
            raise
    
    def _analyze_backtest_results(self, validation_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyse les résultats du backtest
        """
        try:
            if not validation_results:
                return {}
            
            # Statistiques générales
            total_opportunities = len(validation_results)
            
            # Analyse par période
            period_analysis = {}
            for period in [1, 7, 30]:
                period_key = f"{period}_days"
                period_results = [r for r in validation_results if period_key in r.get('validation_results', {})]
                
                if period_results:
                    period_analysis[period_key] = self._analyze_period_results(period_results, period_key)
            
            # Analyse par recommandation
            recommendation_analysis = self._analyze_by_recommendation(validation_results)
            
            # Analyse par niveau de confiance
            confidence_analysis = self._analyze_by_confidence(validation_results)
            
            # Analyse par niveau de risque
            risk_analysis = self._analyze_by_risk(validation_results)
            
            # Métriques globales
            global_metrics = self._calculate_global_metrics(validation_results)
            
            return {
                'total_opportunities': total_opportunities,
                'period_analysis': period_analysis,
                'recommendation_analysis': recommendation_analysis,
                'confidence_analysis': confidence_analysis,
                'risk_analysis': risk_analysis,
                'global_metrics': global_metrics
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des résultats: {e}")
            return {}
    
    def _analyze_period_results(self, period_results: List[Dict], period_key: str) -> Dict[str, Any]:
        """
        Analyse les résultats pour une période donnée
        """
        try:
            if not period_results:
                return {}
            
            # Extraire les données de la période
            actual_returns = []
            predicted_returns = []
            prediction_errors = []
            correct_predictions = 0
            total_predictions = 0
            
            for result in period_results:
                period_data = result.get('validation_results', {}).get(period_key, {})
                
                if period_data.get('actual_return') is not None:
                    actual_returns.append(period_data['actual_return'])
                
                if period_data.get('predicted_return') is not None:
                    predicted_returns.append(period_data['predicted_return'])
                
                if period_data.get('prediction_error') is not None:
                    prediction_errors.append(period_data['prediction_error'])
                
                if period_data.get('recommendation_correct') is not None:
                    total_predictions += 1
                    if period_data['recommendation_correct']:
                        correct_predictions += 1
            
            # Calculer les statistiques
            stats = {}
            
            if actual_returns:
                stats['mean_actual_return'] = sum(actual_returns) / len(actual_returns)
                stats['median_actual_return'] = sorted(actual_returns)[len(actual_returns) // 2]
                stats['std_actual_return'] = self._calculate_std(actual_returns)
                stats['min_actual_return'] = min(actual_returns)
                stats['max_actual_return'] = max(actual_returns)
            
            if predicted_returns:
                stats['mean_predicted_return'] = sum(predicted_returns) / len(predicted_returns)
                stats['median_predicted_return'] = sorted(predicted_returns)[len(predicted_returns) // 2]
                stats['std_predicted_return'] = self._calculate_std(predicted_returns)
            
            if prediction_errors:
                stats['mean_prediction_error'] = sum(prediction_errors) / len(prediction_errors)
                stats['median_prediction_error'] = sorted(prediction_errors)[len(prediction_errors) // 2]
                stats['std_prediction_error'] = self._calculate_std(prediction_errors)
            
            if total_predictions > 0:
                stats['accuracy'] = correct_predictions / total_predictions
                stats['correct_predictions'] = correct_predictions
                stats['total_predictions'] = total_predictions
            
            # Distribution des catégories de performance
            performance_categories = {}
            for result in period_results:
                period_data = result.get('validation_results', {}).get(period_key, {})
                category = period_data.get('performance_category', 'NO_DATA')
                performance_categories[category] = performance_categories.get(category, 0) + 1
            
            stats['performance_categories'] = performance_categories
            
            return stats
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse de la période {period_key}: {e}")
            return {}
    
    def _analyze_by_recommendation(self, validation_results: List[Dict]) -> Dict[str, Any]:
        """
        Analyse les résultats par type de recommandation
        """
        try:
            recommendations = {}
            
            for result in validation_results:
                # Récupérer la recommandation depuis l'opportunité
                # Note: Il faudrait récupérer cette info depuis la base de données
                # Pour l'instant, on utilise une approche simplifiée
                recommendation = "UNKNOWN"  # À implémenter
                
                if recommendation not in recommendations:
                    recommendations[recommendation] = {
                        'count': 0,
                        'total_return': 0.0,
                        'correct_predictions': 0,
                        'total_predictions': 0
                    }
                
                recommendations[recommendation]['count'] += 1
                
                # Agréger les rendements
                for period_key, period_data in result.get('validation_results', {}).items():
                    if period_data.get('actual_return') is not None:
                        recommendations[recommendation]['total_return'] += period_data['actual_return']
                    
                    if period_data.get('recommendation_correct') is not None:
                        recommendations[recommendation]['total_predictions'] += 1
                        if period_data['recommendation_correct']:
                            recommendations[recommendation]['correct_predictions'] += 1
            
            # Calculer les moyennes
            for rec in recommendations:
                if recommendations[rec]['count'] > 0:
                    recommendations[rec]['avg_return'] = recommendations[rec]['total_return'] / recommendations[rec]['count']
                
                if recommendations[rec]['total_predictions'] > 0:
                    recommendations[rec]['accuracy'] = recommendations[rec]['correct_predictions'] / recommendations[rec]['total_predictions']
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse par recommandation: {e}")
            return {}
    
    def _analyze_by_confidence(self, validation_results: List[Dict]) -> Dict[str, Any]:
        """
        Analyse les résultats par niveau de confiance
        """
        # Implémentation similaire à _analyze_by_recommendation
        # À implémenter
        return {}
    
    def _analyze_by_risk(self, validation_results: List[Dict]) -> Dict[str, Any]:
        """
        Analyse les résultats par niveau de risque
        """
        # Implémentation similaire à _analyze_by_recommendation
        # À implémenter
        return {}
    
    def _calculate_global_metrics(self, validation_results: List[Dict]) -> Dict[str, Any]:
        """
        Calcule les métriques globales du backtest
        """
        try:
            if not validation_results:
                return {}
            
            # Métriques de performance globale
            all_returns = []
            all_prediction_errors = []
            total_correct = 0
            total_predictions = 0
            
            for result in validation_results:
                for period_key, period_data in result.get('validation_results', {}).items():
                    if period_data.get('actual_return') is not None:
                        all_returns.append(period_data['actual_return'])
                    
                    if period_data.get('prediction_error') is not None:
                        all_prediction_errors.append(period_data['prediction_error'])
                    
                    if period_data.get('recommendation_correct') is not None:
                        total_predictions += 1
                        if period_data['recommendation_correct']:
                            total_correct += 1
            
            metrics = {}
            
            if all_returns:
                metrics['overall_mean_return'] = sum(all_returns) / len(all_returns)
                metrics['overall_std_return'] = self._calculate_std(all_returns)
                metrics['overall_sharpe_ratio'] = metrics['overall_mean_return'] / metrics['overall_std_return'] if metrics['overall_std_return'] > 0 else 0
            
            if all_prediction_errors:
                metrics['overall_mean_prediction_error'] = sum(all_prediction_errors) / len(all_prediction_errors)
                metrics['overall_std_prediction_error'] = self._calculate_std(all_prediction_errors)
            
            if total_predictions > 0:
                metrics['overall_accuracy'] = total_correct / total_predictions
            
            # Score de performance moyen
            performance_scores = [r.get('performance_score', 0.5) for r in validation_results if r.get('performance_score') is not None]
            if performance_scores:
                metrics['overall_performance_score'] = sum(performance_scores) / len(performance_scores)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des métriques globales: {e}")
            return {}
    
    def _calculate_std(self, values: List[float]) -> float:
        """
        Calcule l'écart-type d'une liste de valeurs
        """
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _generate_backtest_report(
        self,
        start_date: date,
        end_date: date,
        opportunities_count: int,
        validation_results: List[Dict],
        analysis_results: Dict
    ) -> Dict[str, Any]:
        """
        Génère un rapport complet du backtest
        """
        try:
            report = {
                'backtest_info': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'duration_days': (end_date - start_date).days,
                    'opportunities_generated': opportunities_count,
                    'opportunities_validated': len(validation_results),
                    'generation_timestamp': datetime.now().isoformat()
                },
                'analysis_results': analysis_results,
                'summary': self._generate_summary(analysis_results),
                'recommendations': self._generate_recommendations(analysis_results)
            }
            
            return report
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {e}")
            return {}
    
    def _generate_summary(self, analysis_results: Dict) -> Dict[str, Any]:
        """
        Génère un résumé des résultats
        """
        try:
            global_metrics = analysis_results.get('global_metrics', {})
            
            summary = {
                'overall_performance': global_metrics.get('overall_performance_score', 0.5),
                'overall_accuracy': global_metrics.get('overall_accuracy', 0.0),
                'overall_return': global_metrics.get('overall_mean_return', 0.0),
                'overall_sharpe_ratio': global_metrics.get('overall_sharpe_ratio', 0.0),
                'prediction_quality': global_metrics.get('overall_mean_prediction_error', 0.0)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du résumé: {e}")
            return {}
    
    def _generate_recommendations(self, analysis_results: Dict) -> List[str]:
        """
        Génère des recommandations basées sur les résultats
        """
        recommendations = []
        
        try:
            global_metrics = analysis_results.get('global_metrics', {})
            
            # Recommandations basées sur la performance
            if global_metrics.get('overall_accuracy', 0) < 0.5:
                recommendations.append("La précision des prédictions est faible. Considérer l'amélioration des modèles.")
            
            if global_metrics.get('overall_sharpe_ratio', 0) < 0.5:
                recommendations.append("Le ratio de Sharpe est faible. Optimiser la gestion des risques.")
            
            if global_metrics.get('overall_mean_prediction_error', 0) > 0.1:
                recommendations.append("L'erreur de prédiction est élevée. Revoir les paramètres des modèles.")
            
            # Recommandations basées sur l'analyse par période
            period_analysis = analysis_results.get('period_analysis', {})
            if '1_days' in period_analysis and '30_days' in period_analysis:
                short_term_accuracy = period_analysis['1_days'].get('accuracy', 0)
                long_term_accuracy = period_analysis['30_days'].get('accuracy', 0)
                
                if short_term_accuracy > long_term_accuracy * 1.2:
                    recommendations.append("Les prédictions à court terme sont meilleures qu'à long terme. Considérer des stratégies de trading plus courtes.")
                elif long_term_accuracy > short_term_accuracy * 1.2:
                    recommendations.append("Les prédictions à long terme sont meilleures qu'à court terme. Considérer des stratégies de trading plus longues.")
            
            if not recommendations:
                recommendations.append("Les résultats du backtest sont satisfaisants. Continuer avec les paramètres actuels.")
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des recommandations: {e}")
            return ["Erreur lors de l'analyse des résultats."]
    
    async def run_quick_backtest(
        self,
        test_date: date,
        symbols: Optional[List[str]] = None,
        limit_symbols: int = 10
    ) -> Dict[str, Any]:
        """
        Exécute un backtest rapide sur une date donnée
        """
        try:
            logger.info(f"Backtest rapide pour la date {test_date}")
            
            # Générer les opportunités pour cette date
            opportunities = await self.generator.generate_opportunities_for_date(
                target_date=test_date,
                symbols=symbols,
                limit_symbols=limit_symbols
            )
            
            if not opportunities:
                return {
                    'status': 'no_opportunities',
                    'message': f'Aucune opportunité générée pour {test_date}'
                }
            
            # Valider les performances
            validation_results = await self.validator.validate_opportunities_batch(
                opportunities=opportunities,
                validation_periods=[1, 7, 30]
            )
            
            # Analyse rapide
            analysis_results = self._analyze_backtest_results(validation_results)
            
            return {
                'status': 'success',
                'test_date': test_date.isoformat(),
                'opportunities_count': len(opportunities),
                'validation_results': validation_results,
                'analysis_results': analysis_results
            }
            
        except Exception as e:
            logger.error(f"Erreur lors du backtest rapide: {e}")
            return {
                'status': 'error',
                'message': str(e)
            }
