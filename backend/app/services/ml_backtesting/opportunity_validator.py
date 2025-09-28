"""
Service pour valider les performances des opportunités historiques
"""
import asyncio
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import logging
from decimal import Decimal

from app.models.database import HistoricalData
from app.models.historical_opportunities import HistoricalOpportunities, HistoricalOpportunityValidation

logger = logging.getLogger(__name__)


class OpportunityValidator:
    """
    Validateur de performances des opportunités historiques
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    async def validate_opportunity_performance(
        self, 
        opportunity: HistoricalOpportunities, 
        validation_periods: List[int] = [1, 7, 30]
    ) -> Dict[str, Any]:
        """
        Valide la performance d'une opportunité sur plusieurs périodes
        
        Args:
            opportunity: L'opportunité historique à valider
            validation_periods: Liste des périodes de validation en jours
        
        Returns:
            Dictionnaire contenant les résultats de validation
        """
        try:
            logger.info(f"Validation de l'opportunité {opportunity.symbol} du {opportunity.opportunity_date}")
            
            validation_results = {}
            
            for period_days in validation_periods:
                try:
                    result = await self._validate_single_period(opportunity, period_days)
                    validation_results[f"{period_days}_days"] = result
                    
                    # Mettre à jour l'opportunité avec les résultats
                    await self._update_opportunity_with_validation(opportunity, period_days, result)
                    
                except Exception as e:
                    logger.error(f"Erreur lors de la validation sur {period_days} jours: {e}")
                    continue
            
            # Calculer le score de performance global
            performance_score = self._calculate_performance_score(validation_results)
            opportunity.performance_score = performance_score
            
            # Sauvegarder les modifications
            self.db.commit()
            
            return {
                'opportunity_id': opportunity.id,
                'symbol': opportunity.symbol,
                'opportunity_date': opportunity.opportunity_date,
                'validation_results': validation_results,
                'performance_score': performance_score
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation de l'opportunité {opportunity.id}: {e}")
            self.db.rollback()
            raise
    
    async def _validate_single_period(
        self, 
        opportunity: HistoricalOpportunities, 
        period_days: int
    ) -> Dict[str, Any]:
        """
        Valide la performance sur une période donnée
        """
        try:
            # Calculer la date de fin de validation
            validation_end_date = opportunity.opportunity_date + timedelta(days=period_days)
            
            # Récupérer le prix à la date de fin de validation
            end_price_data = self.db.query(HistoricalData).filter(
                and_(
                    HistoricalData.symbol == opportunity.symbol,
                    HistoricalData.date == validation_end_date
                )
            ).first()
            
            if not end_price_data:
                logger.warning(f"Pas de données de prix pour {opportunity.symbol} le {validation_end_date}")
                return {
                    'period_days': period_days,
                    'validation_end_date': validation_end_date,
                    'actual_return': None,
                    'predicted_return': None,
                    'prediction_error': None,
                    'recommendation_correct': None,
                    'performance_category': 'NO_DATA'
                }
            
            # Calculer le rendement réel
            if opportunity.price_at_generation and opportunity.price_at_generation > 0:
                actual_return = (float(end_price_data.close) - float(opportunity.price_at_generation)) / float(opportunity.price_at_generation)
            else:
                actual_return = None
            
            # Calculer le rendement prédit basé sur la recommandation
            predicted_return = self._calculate_predicted_return(opportunity, period_days)
            
            # Calculer l'erreur de prédiction
            prediction_error = None
            if actual_return is not None and predicted_return is not None:
                prediction_error = abs(float(actual_return) - float(predicted_return))
            
            # Vérifier si la recommandation était correcte
            recommendation_correct = self._evaluate_recommendation_accuracy(
                opportunity.recommendation, actual_return, period_days
            )
            
            # Classifier la performance
            performance_category = self._classify_performance(actual_return, period_days)
            
            # Calculer les métriques de risque
            sharpe_ratio = await self._calculate_sharpe_ratio(opportunity, validation_end_date, period_days)
            max_drawdown = await self._calculate_max_drawdown(opportunity, validation_end_date, period_days)
            volatility = await self._calculate_volatility(opportunity, validation_end_date, period_days)
            
            # Calculer le beta et le rendement du marché
            market_return = await self._calculate_market_return(validation_end_date, period_days)
            beta = await self._calculate_beta(opportunity, validation_end_date, period_days)
            
            return {
                'period_days': period_days,
                'validation_end_date': validation_end_date,
                'actual_return': float(actual_return) if actual_return else None,
                'predicted_return': float(predicted_return) if predicted_return else None,
                'prediction_error': float(prediction_error) if prediction_error else None,
                'recommendation_correct': recommendation_correct,
                'performance_category': performance_category,
                'sharpe_ratio': float(sharpe_ratio) if sharpe_ratio else None,
                'max_drawdown': float(max_drawdown) if max_drawdown else None,
                'volatility': float(volatility) if volatility else None,
                'market_return': float(market_return) if market_return else None,
                'beta': float(beta) if beta else None
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la validation sur {period_days} jours: {e}")
            raise
    
    def _calculate_predicted_return(self, opportunity: HistoricalOpportunities, period_days: int) -> Optional[float]:
        """
        Calcule le rendement prédit basé sur la recommandation et le score composite
        """
        try:
            if not opportunity.composite_score:
                return None
            
            # Convertir le score composite en rendement prédit
            # Score > 0.7 (BUY) -> rendement positif
            # Score < 0.3 (SELL) -> rendement négatif
            # Score entre 0.3 et 0.7 (HOLD) -> rendement proche de 0
            
            base_return = (float(opportunity.composite_score) - 0.5) * 2  # -1 à +1
            
            # Ajuster selon la période (plus la période est longue, plus l'incertitude augmente)
            time_decay_factor = 1.0 / (1.0 + period_days / 30.0)  # Décroissance avec le temps
            
            # Ajuster selon le niveau de confiance
            confidence_factor = 1.0
            if opportunity.confidence_level == "HIGH":
                confidence_factor = 1.2
            elif opportunity.confidence_level == "LOW":
                confidence_factor = 0.8
            
            predicted_return = base_return * time_decay_factor * confidence_factor
            
            # Limiter le rendement prédit à des valeurs raisonnables
            return max(-0.5, min(0.5, predicted_return))
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du rendement prédit: {e}")
            return None
    
    def _evaluate_recommendation_accuracy(self, recommendation: str, actual_return: Optional[float], period_days: int = 1) -> Optional[bool]:
        """
        Évalue si la recommandation était correcte avec des seuils adaptatifs
        
        Args:
            recommendation: BUY, SELL, ou HOLD
            actual_return: Rendement réel observé
            period_days: Période de validation en jours
        """
        if actual_return is None or not recommendation:
            return None
        
        # Seuils adaptatifs selon la période
        if period_days == 1:
            buy_sell_threshold = 0.01  # 1% pour couvrir les frais
            hold_threshold = 0.06      # 6% pour HOLD
        elif period_days == 7:
            buy_sell_threshold = 0.02  # 2% sur 7 jours
            hold_threshold = 0.08      # 8% pour HOLD
        elif period_days == 30:
            buy_sell_threshold = 0.05  # 5% sur 30 jours
            hold_threshold = 0.12      # 12% pour HOLD
        else:
            # Seuils par défaut
            buy_sell_threshold = 0.01
            hold_threshold = 0.06
        
        if recommendation == "BUY":
            return actual_return > buy_sell_threshold
        elif recommendation == "SELL":
            return actual_return < -buy_sell_threshold
        else:  # HOLD
            return abs(actual_return) < hold_threshold
    
    def _classify_performance(self, actual_return: Optional[float], period_days: int) -> str:
        """
        Classe la performance selon le rendement réel
        """
        if actual_return is None:
            return "NO_DATA"
        
        # Ajuster les seuils selon la période
        if period_days == 1:
            # Seuils pour 1 jour
            if actual_return > 0.05:
                return "EXCELLENT"
            elif actual_return > 0.02:
                return "GOOD"
            elif actual_return > -0.02:
                return "AVERAGE"
            elif actual_return > -0.05:
                return "POOR"
            else:
                return "TERRIBLE"
        elif period_days == 7:
            # Seuils pour 7 jours
            if actual_return > 0.10:
                return "EXCELLENT"
            elif actual_return > 0.05:
                return "GOOD"
            elif actual_return > -0.05:
                return "AVERAGE"
            elif actual_return > -0.10:
                return "POOR"
            else:
                return "TERRIBLE"
        else:  # 30 jours
            # Seuils pour 30 jours
            if actual_return > 0.20:
                return "EXCELLENT"
            elif actual_return > 0.10:
                return "GOOD"
            elif actual_return > -0.10:
                return "AVERAGE"
            elif actual_return > -0.20:
                return "POOR"
            else:
                return "TERRIBLE"
    
    async def _calculate_sharpe_ratio(
        self, 
        opportunity: HistoricalOpportunities, 
        validation_end_date: date, 
        period_days: int
    ) -> Optional[float]:
        """
        Calcule le ratio de Sharpe pour la période de validation
        """
        try:
            # Récupérer les données de prix sur la période
            start_date = opportunity.opportunity_date
            price_data = self.db.query(HistoricalData).filter(
                and_(
                    HistoricalData.symbol == opportunity.symbol,
                    HistoricalData.date >= start_date,
                    HistoricalData.date <= validation_end_date
                )
            ).order_by(HistoricalData.date).all()
            
            if len(price_data) < 2:
                return None
            
            # Calculer les rendements quotidiens
            returns = []
            for i in range(1, len(price_data)):
                daily_return = (float(price_data[i].close) - float(price_data[i-1].close)) / float(price_data[i-1].close)
                returns.append(daily_return)
            
            if not returns:
                return None
            
            # Calculer le ratio de Sharpe (supposant un taux sans risque de 0)
            mean_return = sum(returns) / len(returns)
            std_return = (sum((float(r) - float(mean_return)) ** 2 for r in returns) / len(returns)) ** 0.5
            
            if std_return == 0:
                return 0.0
            
            return mean_return / std_return
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du ratio de Sharpe: {e}")
            return None
    
    async def _calculate_max_drawdown(
        self, 
        opportunity: HistoricalOpportunities, 
        validation_end_date: date, 
        period_days: int
    ) -> Optional[float]:
        """
        Calcule le drawdown maximum pour la période de validation
        """
        try:
            # Récupérer les données de prix sur la période
            start_date = opportunity.opportunity_date
            price_data = self.db.query(HistoricalData).filter(
                and_(
                    HistoricalData.symbol == opportunity.symbol,
                    HistoricalData.date >= start_date,
                    HistoricalData.date <= validation_end_date
                )
            ).order_by(HistoricalData.date).all()
            
            if len(price_data) < 2:
                return None
            
            # Calculer le drawdown maximum
            peak = price_data[0].close
            max_drawdown = 0.0
            
            for data in price_data:
                if data.close > peak:
                    peak = data.close
                else:
                    drawdown = (peak - data.close) / peak
                    max_drawdown = max(max_drawdown, drawdown)
            
            return max_drawdown
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du drawdown maximum: {e}")
            return None
    
    async def _calculate_volatility(
        self, 
        opportunity: HistoricalOpportunities, 
        validation_end_date: date, 
        period_days: int
    ) -> Optional[float]:
        """
        Calcule la volatilité pour la période de validation
        """
        try:
            # Récupérer les données de prix sur la période
            start_date = opportunity.opportunity_date
            price_data = self.db.query(HistoricalData).filter(
                and_(
                    HistoricalData.symbol == opportunity.symbol,
                    HistoricalData.date >= start_date,
                    HistoricalData.date <= validation_end_date
                )
            ).order_by(HistoricalData.date).all()
            
            if len(price_data) < 2:
                return None
            
            # Calculer les rendements quotidiens
            returns = []
            for i in range(1, len(price_data)):
                daily_return = (float(price_data[i].close) - float(price_data[i-1].close)) / float(price_data[i-1].close)
                returns.append(daily_return)
            
            if not returns:
                return None
            
            # Calculer la volatilité (écart-type des rendements)
            mean_return = sum(returns) / len(returns)
            variance = sum((float(r) - float(mean_return)) ** 2 for r in returns) / len(returns)
            volatility = variance ** 0.5
            
            return volatility
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la volatilité: {e}")
            return None
    
    async def _calculate_market_return(self, validation_end_date: date, period_days: int) -> Optional[float]:
        """
        Calcule le rendement du marché (NASDAQ) pour la période
        """
        try:
            # Utiliser un ETF NASDAQ comme proxy (QQQ)
            start_date = validation_end_date - timedelta(days=period_days)
            
            start_price = self.db.query(HistoricalData).filter(
                and_(
                    HistoricalData.symbol == "QQQ",
                    HistoricalData.date == start_date
                )
            ).first()
            
            end_price = self.db.query(HistoricalData).filter(
                and_(
                    HistoricalData.symbol == "QQQ",
                    HistoricalData.date == validation_end_date
                )
            ).first()
            
            if not start_price or not end_price:
                return None
            
            market_return = (end_price.close - start_price.close) / start_price.close
            return market_return
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du rendement du marché: {e}")
            return None
    
    async def _calculate_beta(
        self, 
        opportunity: HistoricalOpportunities, 
        validation_end_date: date, 
        period_days: int
    ) -> Optional[float]:
        """
        Calcule le beta de l'action par rapport au marché
        """
        try:
            start_date = opportunity.opportunity_date
            
            # Récupérer les données de l'action
            stock_data = self.db.query(HistoricalData).filter(
                and_(
                    HistoricalData.symbol == opportunity.symbol,
                    HistoricalData.date >= start_date,
                    HistoricalData.date <= validation_end_date
                )
            ).order_by(HistoricalData.date).all()
            
            # Récupérer les données du marché (QQQ)
            market_data = self.db.query(HistoricalData).filter(
                and_(
                    HistoricalData.symbol == "QQQ",
                    HistoricalData.date >= start_date,
                    HistoricalData.date <= validation_end_date
                )
            ).order_by(HistoricalData.date).all()
            
            if len(stock_data) < 2 or len(market_data) < 2:
                return None
            
            # Calculer les rendements
            stock_returns = []
            market_returns = []
            
            for i in range(1, min(len(stock_data), len(market_data))):
                stock_return = (stock_data[i].close - stock_data[i-1].close) / stock_data[i-1].close
                market_return = (market_data[i].close - market_data[i-1].close) / market_data[i-1].close
                
                stock_returns.append(stock_return)
                market_returns.append(market_return)
            
            if len(stock_returns) < 2:
                return None
            
            # Calculer le beta (covariance / variance du marché)
            mean_stock = sum(stock_returns) / len(stock_returns)
            mean_market = sum(market_returns) / len(market_returns)
            
            covariance = sum((stock_returns[i] - mean_stock) * (market_returns[i] - mean_market) 
                           for i in range(len(stock_returns))) / len(stock_returns)
            
            market_variance = sum((r - mean_market) ** 2 for r in market_returns) / len(market_returns)
            
            if market_variance == 0:
                return 1.0
            
            beta = covariance / market_variance
            return beta
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du beta: {e}")
            return None
    
    async def _update_opportunity_with_validation(
        self, 
        opportunity: HistoricalOpportunities, 
        period_days: int, 
        validation_result: Dict[str, Any]
    ):
        """
        Met à jour l'opportunité avec les résultats de validation
        """
        try:
            # Mettre à jour les champs correspondants
            if period_days == 1:
                # Récupérer le prix final pour price_1_day_later
                final_price = self._get_final_price_for_period(opportunity, period_days)
                opportunity.price_1_day_later = final_price
                opportunity.return_1_day = validation_result.get('actual_return')
                opportunity.recommendation_correct_1_day = validation_result.get('recommendation_correct')
            elif period_days == 7:
                # Récupérer le prix final pour price_7_days_later
                final_price = self._get_final_price_for_period(opportunity, period_days)
                opportunity.price_7_days_later = final_price
                opportunity.return_7_days = validation_result.get('actual_return')
                opportunity.recommendation_correct_7_days = validation_result.get('recommendation_correct')
            elif period_days == 30:
                # Récupérer le prix final pour price_30_days_later
                final_price = self._get_final_price_for_period(opportunity, period_days)
                opportunity.price_30_days_later = final_price
                opportunity.return_30_days = validation_result.get('actual_return')
                opportunity.recommendation_correct_30_days = validation_result.get('recommendation_correct')
            
            # Créer un enregistrement de validation détaillé
            validation_record = HistoricalOpportunityValidation(
                historical_opportunity_id=opportunity.id,
                validation_period_days=period_days,
                validation_date=validation_result.get('validation_end_date'),
                actual_return=validation_result.get('actual_return'),
                predicted_return=validation_result.get('predicted_return'),
                prediction_error=validation_result.get('prediction_error'),
                sharpe_ratio=validation_result.get('sharpe_ratio'),
                max_drawdown=validation_result.get('max_drawdown'),
                volatility=validation_result.get('volatility'),
                performance_category=validation_result.get('performance_category'),
                market_return=validation_result.get('market_return'),
                beta=validation_result.get('beta')
            )
            
            self.db.add(validation_record)
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour de l'opportunité: {e}")
            raise
    
    def _get_final_price_for_period(self, opportunity: HistoricalOpportunities, period_days: int) -> Optional[float]:
        """
        Récupère le prix final pour une période donnée
        """
        try:
            from datetime import timedelta
            validation_end_date = opportunity.opportunity_date + timedelta(days=period_days)
            
            # Récupérer le prix à la date de fin de validation
            end_price_data = self.db.query(HistoricalData).filter(
                HistoricalData.symbol == opportunity.symbol,
                HistoricalData.date == validation_end_date
            ).first()
            
            if end_price_data:
                return float(end_price_data.close)
            else:
                return None
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du prix final: {e}")
            return None
    
    def _calculate_performance_score(self, validation_results: Dict[str, Any]) -> float:
        """
        Calcule un score de performance global basé sur tous les résultats de validation
        """
        try:
            if not validation_results:
                return 0.5
            
            total_score = 0.0
            weight_sum = 0.0
            
            # Poids selon la période (plus la période est longue, plus le poids est important)
            weights = {1: 0.2, 7: 0.3, 30: 0.5}
            
            for period_key, result in validation_results.items():
                period_days = int(period_key.split('_')[0])
                weight = weights.get(period_days, 0.33)
                
                # Score basé sur la catégorie de performance
                category_score = self._get_category_score(result.get('performance_category', 'NO_DATA'))
                
                # Ajustement basé sur la précision de la recommandation
                if result.get('recommendation_correct') is True:
                    category_score *= 1.2
                elif result.get('recommendation_correct') is False:
                    category_score *= 0.8
                
                total_score += category_score * weight
                weight_sum += weight
            
            if weight_sum == 0:
                return 0.5
            
            final_score = total_score / weight_sum
            return max(0.0, min(1.0, final_score))  # Clamp entre 0 et 1
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul du score de performance: {e}")
            return 0.5
    
    def _get_category_score(self, category: str) -> float:
        """
        Convertit une catégorie de performance en score numérique
        """
        category_scores = {
            'EXCELLENT': 0.9,
            'GOOD': 0.7,
            'AVERAGE': 0.5,
            'POOR': 0.3,
            'TERRIBLE': 0.1,
            'NO_DATA': 0.5
        }
        
        return category_scores.get(category, 0.5)
    
    async def validate_opportunities_batch(
        self, 
        opportunities: List[HistoricalOpportunities],
        validation_periods: List[int] = [1, 7, 30]
    ) -> List[Dict[str, Any]]:
        """
        Valide un lot d'opportunités
        """
        results = []
        
        for opportunity in opportunities:
            try:
                result = await self.validate_opportunity_performance(opportunity, validation_periods)
                results.append(result)
            except Exception as e:
                logger.error(f"Erreur lors de la validation de l'opportunité {opportunity.id}: {e}")
                continue
        
        return results
