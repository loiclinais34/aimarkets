"""
Service de mise à jour des données historiques et de sentiment
"""
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from sqlalchemy.exc import IntegrityError

from ..models.database import HistoricalData, SentimentData, SymbolMetadata
from .polygon_service import PolygonService
from .indicators_recalculation_service import IndicatorsRecalculationService

logger = logging.getLogger(__name__)

class DataUpdateService:
    """Service pour mettre à jour les données historiques et de sentiment"""
    
    def __init__(self, db: Session):
        self.db = db
        self.polygon_service = PolygonService()
        self.indicators_service = IndicatorsRecalculationService(db)
    
    def update_historical_data_for_symbol(self, symbol: str, force_update: bool = False) -> Dict[str, Any]:
        """
        Met à jour les données historiques pour un symbole spécifique
        
        Args:
            symbol: Symbole du titre
            force_update: Forcer la mise à jour même si les données semblent à jour
        
        Returns:
            Dictionnaire avec le résultat de la mise à jour
        """
        logger.info(f"Début de la mise à jour des données historiques pour {symbol}")
        
        try:
            # Vérifier si une mise à jour est nécessaire
            if not force_update:
                should_update, db_latest_date, polygon_latest_date = self.polygon_service.should_update_data(
                    self.db, symbol
                )
                
                if not should_update:
                    logger.info(f"Les données pour {symbol} sont déjà à jour (DB: {db_latest_date}, Polygon: {polygon_latest_date})")
                    return {
                        'symbol': symbol,
                        'status': 'skipped',
                        'message': 'Données déjà à jour',
                        'db_latest_date': db_latest_date.isoformat() if db_latest_date else None,
                        'polygon_latest_date': polygon_latest_date.isoformat() if polygon_latest_date else None,
                        'records_updated': 0
                    }
            
            # Déterminer la période de mise à jour
            db_latest_date = self.polygon_service.get_database_latest_date(self.db, symbol, HistoricalData)
            
            if db_latest_date:
                # Mettre à jour depuis le jour suivant la dernière date en base
                start_date = db_latest_date + timedelta(days=1)
            else:
                # Récupérer les 30 derniers jours si aucune donnée en base
                start_date = date.today() - timedelta(days=30)
            
            end_date = date.today()
            
            # Récupérer les données depuis Polygon
            historical_data = self.polygon_service.get_historical_data(
                symbol,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if not historical_data:
                logger.warning(f"Aucune donnée historique récupérée pour {symbol}")
                return {
                    'symbol': symbol,
                    'status': 'no_data',
                    'message': 'Aucune donnée récupérée depuis Polygon',
                    'records_updated': 0
                }
            
            # Insérer les données en base
            records_inserted = 0
            records_updated = 0
            
            for data in historical_data:
                try:
                    # Vérifier si l'enregistrement existe déjà
                    existing = self.db.query(HistoricalData).filter(
                        HistoricalData.symbol == symbol,
                        HistoricalData.date == data['date']
                    ).first()
                    
                    if existing:
                        # Mettre à jour l'enregistrement existant
                        existing.open = data['open']
                        existing.high = data['high']
                        existing.low = data['low']
                        existing.close = data['close']
                        existing.volume = data['volume']
                        existing.vwap = data['vwap']
                        existing.updated_at = datetime.now()
                        records_updated += 1
                    else:
                        # Créer un nouvel enregistrement
                        new_record = HistoricalData(
                            symbol=data['symbol'],
                            date=data['date'],
                            open=data['open'],
                            high=data['high'],
                            low=data['low'],
                            close=data['close'],
                            volume=data['volume'],
                            vwap=data['vwap']
                        )
                        self.db.add(new_record)
                        records_inserted += 1
                
                except IntegrityError as e:
                    logger.error(f"Erreur d'intégrité lors de l'insertion des données pour {symbol} le {data['date']}: {e}")
                    self.db.rollback()
                    continue
            
            # Valider les changements
            self.db.commit()
            
            logger.info(f"Mise à jour terminée pour {symbol}: {records_inserted} nouveaux enregistrements, {records_updated} mises à jour")
            
            # Recalculer les indicateurs techniques après la mise à jour des données historiques
            indicators_result = None
            if records_inserted > 0 or records_updated > 0:
                logger.info(f"Recalcul des indicateurs techniques pour {symbol}...")
                try:
                    indicators_result = self.indicators_service.recalculate_technical_indicators(symbol)
                    if indicators_result['success']:
                        logger.info(f"Indicateurs techniques recalculés pour {symbol}: {indicators_result['processed_dates']} dates")
                    else:
                        logger.error(f"Erreur lors du recalcul des indicateurs techniques pour {symbol}: {indicators_result['error']}")
                except Exception as e:
                    logger.error(f"Exception lors du recalcul des indicateurs techniques pour {symbol}: {e}")
                    indicators_result = {'success': False, 'error': str(e)}
            
            return {
                'symbol': symbol,
                'status': 'success',
                'message': f'Mise à jour réussie: {records_inserted} nouveaux, {records_updated} mises à jour',
                'records_inserted': records_inserted,
                'records_updated': records_updated,
                'total_records': records_inserted + records_updated,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'indicators_recalculated': indicators_result['success'] if indicators_result else False,
                'indicators_processed_dates': indicators_result['processed_dates'] if indicators_result and indicators_result['success'] else 0,
                'indicators_error': indicators_result['error'] if indicators_result and not indicators_result['success'] else None
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des données historiques pour {symbol}: {e}")
            self.db.rollback()
            return {
                'symbol': symbol,
                'status': 'error',
                'message': f'Erreur: {str(e)}',
                'records_updated': 0
            }
    
    def update_sentiment_data_for_symbol(self, symbol: str, force_update: bool = False) -> Dict[str, Any]:
        """
        Met à jour les données de sentiment pour un symbole spécifique
        
        Args:
            symbol: Symbole du titre
            force_update: Forcer la mise à jour même si les données semblent à jour
        
        Returns:
            Dictionnaire avec le résultat de la mise à jour
        """
        logger.info(f"Début de la mise à jour des données de sentiment pour {symbol}")
        
        try:
            # Vérifier si une mise à jour est nécessaire
            if not force_update:
                should_update, db_latest_date, polygon_latest_date = self.polygon_service.should_update_data(
                    self.db, symbol
                )
                
                if not should_update:
                    logger.info(f"Les données de sentiment pour {symbol} sont déjà à jour")
                    return {
                        'symbol': symbol,
                        'status': 'skipped',
                        'message': 'Données de sentiment déjà à jour',
                        'records_updated': 0
                    }
            
            # Déterminer la période de mise à jour
            db_latest_date = self.polygon_service.get_database_latest_date(self.db, symbol, SentimentData)
            
            if db_latest_date:
                start_date = db_latest_date + timedelta(days=1)
            else:
                start_date = date.today() - timedelta(days=30)
            
            end_date = date.today()
            
            # Récupérer les données de news
            news_data = self.polygon_service.get_news_data(
                symbol,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            # Récupérer les données de short interest
            short_interest_data = self.polygon_service.get_short_interest_data(
                symbol,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            # Récupérer les données de short volume
            short_volume_data = self.polygon_service.get_short_volume_data(
                symbol,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            # Grouper les données par date
            sentiment_by_date = {}
            
            # Traiter les données de news
            for news in news_data:
                news_date = datetime.fromisoformat(news['published_utc'].replace('Z', '+00:00')).date()
                if news_date not in sentiment_by_date:
                    sentiment_by_date[news_date] = {'news': [], 'short_interest': None, 'short_volume': None}
                sentiment_by_date[news_date]['news'].append(news)
            
            # Traiter les données de short interest
            for si_data in short_interest_data:
                si_date = si_data['date']
                if si_date not in sentiment_by_date:
                    sentiment_by_date[si_date] = {'news': [], 'short_interest': None, 'short_volume': None}
                sentiment_by_date[si_date]['short_interest'] = si_data
            
            # Traiter les données de short volume
            for sv_data in short_volume_data:
                sv_date = sv_data['date']
                if sv_date not in sentiment_by_date:
                    sentiment_by_date[sv_date] = {'news': [], 'short_interest': None, 'short_volume': None}
                sentiment_by_date[sv_date]['short_volume'] = sv_data
            
            # Calculer et insérer les données de sentiment
            records_inserted = 0
            records_updated = 0
            
            for data_date, data in sentiment_by_date.items():
                try:
                    # Calculer les métriques de sentiment
                    sentiment_metrics = self.polygon_service.calculate_sentiment_from_news(data['news'])
                    
                    # Préparer les données pour l'insertion
                    sentiment_data = {
                        'symbol': symbol,
                        'date': data_date,
                        'news_count': sentiment_metrics['news_count'],
                        'news_sentiment_score': sentiment_metrics['news_sentiment_score'],
                        'news_sentiment_std': sentiment_metrics['news_sentiment_std'],
                        'news_positive_count': sentiment_metrics['news_positive_count'],
                        'news_negative_count': sentiment_metrics['news_negative_count'],
                        'news_neutral_count': sentiment_metrics['news_neutral_count'],
                        'top_news_title': sentiment_metrics['top_news_title'],
                        'top_news_sentiment': sentiment_metrics['top_news_sentiment'],
                        'top_news_url': sentiment_metrics['top_news_url']
                    }
                    
                    # Ajouter les données de short interest
                    if data['short_interest']:
                        si = data['short_interest']
                        sentiment_data.update({
                            'short_interest_ratio': si['short_interest_ratio'],
                            'short_interest_volume': si['short_interest_volume'],
                            'short_interest_date': si['short_interest_date']
                        })
                    
                    # Ajouter les données de short volume
                    if data['short_volume']:
                        sv = data['short_volume']
                        sentiment_data.update({
                            'short_volume': sv['short_volume'],
                            'short_exempt_volume': sv['short_exempt_volume'],
                            'total_volume': sv['total_volume'],
                            'short_volume_ratio': sv['short_volume_ratio']
                        })
                    
                    # Vérifier si l'enregistrement existe déjà
                    existing = self.db.query(SentimentData).filter(
                        SentimentData.symbol == symbol,
                        SentimentData.date == data_date
                    ).first()
                    
                    if existing:
                        # Mettre à jour l'enregistrement existant
                        for key, value in sentiment_data.items():
                            if key not in ['symbol', 'date']:
                                setattr(existing, key, value)
                        existing.updated_at = datetime.now()
                        records_updated += 1
                    else:
                        # Créer un nouvel enregistrement
                        new_record = SentimentData(**sentiment_data)
                        self.db.add(new_record)
                        records_inserted += 1
                
                except Exception as e:
                    logger.error(f"Erreur lors du traitement des données de sentiment pour {symbol} le {data_date}: {e}")
                    continue
            
            # Valider les changements
            self.db.commit()
            
            logger.info(f"Mise à jour des données de sentiment terminée pour {symbol}: {records_inserted} nouveaux enregistrements, {records_updated} mises à jour")
            
            # Recalculer les indicateurs de sentiment après la mise à jour des données de sentiment
            sentiment_indicators_result = None
            if records_inserted > 0 or records_updated > 0:
                logger.info(f"Recalcul des indicateurs de sentiment pour {symbol}...")
                try:
                    sentiment_indicators_result = self.indicators_service.recalculate_sentiment_indicators(symbol)
                    if sentiment_indicators_result['success']:
                        logger.info(f"Indicateurs de sentiment recalculés pour {symbol}: {sentiment_indicators_result['processed_dates']} dates")
                    else:
                        logger.error(f"Erreur lors du recalcul des indicateurs de sentiment pour {symbol}: {sentiment_indicators_result['error']}")
                except Exception as e:
                    logger.error(f"Exception lors du recalcul des indicateurs de sentiment pour {symbol}: {e}")
                    sentiment_indicators_result = {'success': False, 'error': str(e)}
            
            return {
                'symbol': symbol,
                'status': 'success',
                'message': f'Mise à jour des données de sentiment réussie: {records_inserted} nouveaux, {records_updated} mises à jour',
                'records_inserted': records_inserted,
                'records_updated': records_updated,
                'total_records': records_inserted + records_updated,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'sentiment_indicators_recalculated': sentiment_indicators_result['success'] if sentiment_indicators_result else False,
                'sentiment_indicators_processed_dates': sentiment_indicators_result['processed_dates'] if sentiment_indicators_result and sentiment_indicators_result['success'] else 0,
                'sentiment_indicators_error': sentiment_indicators_result['error'] if sentiment_indicators_result and not sentiment_indicators_result['success'] else None
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des données de sentiment pour {symbol}: {e}")
            self.db.rollback()
            return {
                'symbol': symbol,
                'status': 'error',
                'message': f'Erreur: {str(e)}',
                'records_updated': 0
            }
    
    def update_all_symbols(self, force_update: bool = False, max_symbols: int = None) -> Dict[str, Any]:
        """
        Met à jour les données pour tous les symboles actifs
        
        Args:
            force_update: Forcer la mise à jour même si les données semblent à jour
            max_symbols: Nombre maximum de symboles à traiter (pour les tests)
        
        Returns:
            Dictionnaire avec le résultat global de la mise à jour
        """
        logger.info("Début de la mise à jour des données pour tous les symboles")
        
        # Récupérer la liste des symboles actifs
        symbols = self.polygon_service.get_symbols_to_update(self.db)
        
        if max_symbols:
            symbols = symbols[:max_symbols]
        
        logger.info(f"Traitement de {len(symbols)} symboles")
        
        results = {
            'total_symbols': len(symbols),
            'historical_data': {
                'success': 0,
                'error': 0,
                'skipped': 0,
                'results': []
            },
            'sentiment_data': {
                'success': 0,
                'error': 0,
                'skipped': 0,
                'results': []
            },
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration_seconds': None
        }
        
        start_time = datetime.now()
        
        for i, symbol in enumerate(symbols):
            logger.info(f"Traitement du symbole {i+1}/{len(symbols)}: {symbol}")
            
            # Mettre à jour les données historiques
            historical_result = self.update_historical_data_for_symbol(symbol, force_update)
            results['historical_data']['results'].append(historical_result)
            
            if historical_result['status'] == 'success':
                results['historical_data']['success'] += 1
            elif historical_result['status'] == 'error':
                results['historical_data']['error'] += 1
            else:
                results['historical_data']['skipped'] += 1
            
            # Mettre à jour les données de sentiment
            sentiment_result = self.update_sentiment_data_for_symbol(symbol, force_update)
            results['sentiment_data']['results'].append(sentiment_result)
            
            if sentiment_result['status'] == 'success':
                results['sentiment_data']['success'] += 1
            elif sentiment_result['status'] == 'error':
                results['sentiment_data']['error'] += 1
            else:
                results['sentiment_data']['skipped'] += 1
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        results['end_time'] = end_time.isoformat()
        results['duration_seconds'] = duration
        
        # Recalculer les corrélations après toutes les mises à jour
        correlations_result = None
        if results['historical_data']['success'] > 0 or results['sentiment_data']['success'] > 0:
            logger.info("Recalcul des corrélations après mise à jour des données...")
            try:
                correlations_result = self.indicators_service.recalculate_correlations(symbols)
                if correlations_result['success']:
                    logger.info(f"Corrélations recalculées: {correlations_result['processed_correlations']} corrélations")
                else:
                    logger.error(f"Erreur lors du recalcul des corrélations: {correlations_result['error']}")
            except Exception as e:
                logger.error(f"Exception lors du recalcul des corrélations: {e}")
                correlations_result = {'success': False, 'error': str(e)}
        
        # Ajouter les résultats des corrélations
        results['correlations'] = {
            'recalculated': correlations_result['success'] if correlations_result else False,
            'processed_correlations': correlations_result['processed_correlations'] if correlations_result and correlations_result['success'] else 0,
            'error': correlations_result['error'] if correlations_result and not correlations_result['success'] else None
        }
        
        logger.info(f"Mise à jour terminée en {duration:.2f} secondes")
        logger.info(f"Données historiques: {results['historical_data']['success']} succès, {results['historical_data']['error']} erreurs, {results['historical_data']['skipped']} ignorés")
        logger.info(f"Données de sentiment: {results['sentiment_data']['success']} succès, {results['sentiment_data']['error']} erreurs, {results['sentiment_data']['skipped']} ignorés")
        if correlations_result and correlations_result['success']:
            logger.info(f"Corrélations: {correlations_result['processed_correlations']} corrélations recalculées")
        
        return results
    
    def get_data_freshness_status(self) -> Dict[str, Any]:
        """
        Récupère le statut de fraîcheur des données
        
        Returns:
            Dictionnaire avec le statut de fraîcheur des données
        """
        try:
            # Récupérer la dernière date de données historiques
            latest_historical = self.db.query(func.max(HistoricalData.date)).first()
            latest_historical_date = latest_historical[0] if latest_historical and latest_historical[0] else None
            
            # Récupérer la dernière date de données de sentiment
            latest_sentiment = self.db.query(func.max(SentimentData.date)).first()
            latest_sentiment_date = latest_sentiment[0] if latest_sentiment and latest_sentiment[0] else None
            
            # Récupérer le dernier jour de trading
            last_trading_day = self.polygon_service.get_last_trading_day()
            
            # Déterminer si les données sont à jour
            historical_is_fresh = (
                latest_historical_date is not None and 
                latest_historical_date >= last_trading_day
            )
            
            sentiment_is_fresh = (
                latest_sentiment_date is not None and 
                latest_sentiment_date >= last_trading_day
            )
            
            # Calculer le nombre de jours depuis la dernière mise à jour
            days_since_historical = None
            days_since_sentiment = None
            
            if latest_historical_date:
                days_since_historical = (last_trading_day - latest_historical_date).days
            
            if latest_sentiment_date:
                days_since_sentiment = (last_trading_day - latest_sentiment_date).days
            
            return {
                'last_trading_day': last_trading_day.isoformat(),
                'historical_data': {
                    'latest_date': latest_historical_date.isoformat() if latest_historical_date else None,
                    'is_fresh': historical_is_fresh,
                    'days_behind': days_since_historical,
                    'needs_update': not historical_is_fresh
                },
                'sentiment_data': {
                    'latest_date': latest_sentiment_date.isoformat() if latest_sentiment_date else None,
                    'is_fresh': sentiment_is_fresh,
                    'days_behind': days_since_sentiment,
                    'needs_update': not sentiment_is_fresh
                },
                'overall_status': 'fresh' if (historical_is_fresh and sentiment_is_fresh) else 'needs_update',
                'market_is_open': self.polygon_service.is_market_open(),
                'current_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut de fraîcheur: {e}")
            return {
                'error': str(e),
                'overall_status': 'error'
            }
