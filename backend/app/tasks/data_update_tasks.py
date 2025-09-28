"""
Tâches Celery pour la mise à jour des données historiques et de sentiment
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from celery import Celery
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.core.celery_app import celery_app
from app.services.data_update_service import DataUpdateService
from app.services.polygon_service import PolygonService
from app.services.sentiment_indicator_service import SentimentIndicatorService
from app.services.technical_indicators import TechnicalIndicatorsCalculator

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.data_update_tasks.check_data_freshness")
def check_data_freshness_task(self) -> Dict[str, Any]:
    """
    Vérifier la fraîcheur des données historiques et de sentiment
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Vérification de la fraîcheur des données'})
        
        db = next(get_db())
        service = DataUpdateService(db)
        
        # Vérifier les dates de dernière mise à jour
        historical_status = service.check_historical_data_freshness()
        sentiment_status = service.check_sentiment_data_freshness()
        
        # Déterminer si une mise à jour est nécessaire (plus de 8 heures)
        needs_update = False
        if historical_status['needs_update'] or sentiment_status['needs_update']:
            needs_update = True
        
        result = {
            'needs_update': needs_update,
            'historical_status': historical_status,
            'sentiment_status': sentiment_status,
            'check_time': datetime.now().isoformat()
        }
        
        self.update_state(state='SUCCESS', meta=result)
        return result
        
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de la fraîcheur: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

@celery_app.task(bind=True, name="app.tasks.data_update_tasks.update_historical_data")
def update_historical_data_task(self, force_update: bool = False) -> Dict[str, Any]:
    """
    Mettre à jour les données historiques pour tous les symboles
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Démarrage de la mise à jour des données historiques'})
        
        db = next(get_db())
        polygon_service = PolygonService()
        data_service = DataUpdateService(db)
        
        # Récupérer tous les symboles actifs
        symbols = data_service.get_active_symbols()
        total_symbols = len(symbols)
        
        logger.info(f"Début de la mise à jour des données historiques pour {total_symbols} symboles")
        
        results = []
        successful_updates = 0
        failed_updates = 0
        
        for i, symbol in enumerate(symbols):
            try:
                self.update_state(
                    state='PROGRESS', 
                    meta={
                        'status': f'Mise à jour des données historiques pour {symbol}',
                        'progress': int((i / total_symbols) * 100),
                        'current_symbol': symbol,
                        'total_symbols': total_symbols
                    }
                )
                
                # Mettre à jour les données pour ce symbole
                result = polygon_service.update_historical_data(symbol, force_update=force_update)
                results.append(result)
                
                if result['status'] == 'success':
                    successful_updates += 1
                else:
                    failed_updates += 1
                    
                logger.info(f"Symbole {symbol}: {result['status']} - {result['message']}")
                
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour de {symbol}: {e}")
                results.append({
                    'symbol': symbol,
                    'status': 'error',
                    'message': str(e)
                })
                failed_updates += 1
        
        final_result = {
            'status': 'completed',
            'total_symbols': total_symbols,
            'successful_updates': successful_updates,
            'failed_updates': failed_updates,
            'results': results,
            'completion_time': datetime.now().isoformat()
        }
        
        self.update_state(state='SUCCESS', meta=final_result)
        logger.info(f"Mise à jour des données historiques terminée: {successful_updates}/{total_symbols} réussies")
        return final_result
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des données historiques: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

# @celery_app.task(bind=True, name="app.tasks.data_update_tasks.calculate_technical_indicators")
# def calculate_technical_indicators_task(self) -> Dict[str, Any]:
#     """
#     Calculer les indicateurs techniques pour tous les symboles
#     """
#     try:
#         self.update_state(state='PROGRESS', meta={'status': 'Démarrage du calcul des indicateurs techniques'})
        
#         db = next(get_db())
#         indicators_service = TechnicalIndicatorsCalculator(db)
#         data_service = DataUpdateService(db)
        
#         # Récupérer tous les symboles actifs
#         symbols = data_service.get_active_symbols()
#         total_symbols = len(symbols)
        
#         logger.info(f"Début du calcul des indicateurs techniques pour {total_symbols} symboles")
        
#         results = []
#         successful_calculations = 0
#         failed_calculations = 0
        
#         for i, symbol in enumerate(symbols):
#             try:
#                 self.update_state(
#                     state='PROGRESS', 
#                     meta={
#                         'status': f'Calcul des indicateurs techniques pour {symbol}',
#                         'progress': int((i / total_symbols) * 100),
#                         'current_symbol': symbol,
#                         'total_symbols': total_symbols
#                     }
#                 )
                
#                 # Calculer les indicateurs pour ce symbole
#                 result = indicators_service.calculate_all_indicators(symbol)
#                 result_dict = {
#                     'symbol': symbol,
#                     'status': 'success' if result else 'error',
#                     'message': 'Indicateurs calculés avec succès' if result else 'Erreur lors du calcul des indicateurs'
#                 }
#                 results.append(result_dict)
                
#                 if result:
#                     successful_calculations += 1
#                 else:
#                     failed_calculations += 1
                    
#                 logger.info(f"Symbole {symbol}: {result_dict['status']} - {result_dict['message']}")
                
#             except Exception as e:
#                 logger.error(f"Erreur lors du calcul des indicateurs pour {symbol}: {e}")
#                 results.append({
#                     'symbol': symbol,
#                     'status': 'error',
#                     'message': str(e)
#                 })
#                 failed_calculations += 1
        
#         final_result = {
#             'status': 'completed',
#             'total_symbols': total_symbols,
#             'successful_calculations': successful_calculations,
#             'failed_calculations': failed_calculations,
#             'results': results,
#             'completion_time': datetime.now().isoformat()
#         }
        
#         self.update_state(state='SUCCESS', meta=final_result)
#         logger.info(f"Calcul des indicateurs techniques terminé: {successful_calculations}/{total_symbols} réussis")
#         return final_result
        
#     except Exception as e:
#         logger.error(f"Erreur lors du calcul des indicateurs techniques: {e}", exc_info=True)
#         self.update_state(state='FAILURE', meta={'error': str(e)})
#         raise

@celery_app.task(bind=True, name="app.tasks.data_update_tasks.update_sentiment_data")
def update_sentiment_data_task(self, force_update: bool = False) -> Dict[str, Any]:
    """
    Mettre à jour les données de sentiment pour tous les symboles
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Démarrage de la mise à jour des données de sentiment'})
        
        db = next(get_db())
        polygon_service = PolygonService()
        data_service = DataUpdateService(db)
        
        # Récupérer tous les symboles actifs
        symbols = data_service.get_active_symbols()
        total_symbols = len(symbols)
        
        logger.info(f"Début de la mise à jour des données de sentiment pour {total_symbols} symboles")
        
        results = []
        successful_updates = 0
        failed_updates = 0
        
        for i, symbol in enumerate(symbols):
            try:
                self.update_state(
                    state='PROGRESS', 
                    meta={
                        'status': f'Mise à jour des données de sentiment pour {symbol}',
                        'progress': int((i / total_symbols) * 100),
                        'current_symbol': symbol,
                        'total_symbols': total_symbols
                    }
                )
                
                # Créer une nouvelle session pour chaque symbole
                symbol_db = next(get_db())
                
                # Mettre à jour les données de sentiment pour ce symbole
                from datetime import datetime, timedelta
                
                # Déterminer la période de récupération (7 derniers jours)
                end_date = datetime.now().date()
                start_date = end_date - timedelta(days=7)
                
                # Récupérer les données de news uniquement
                news_data = polygon_service.get_news_data(
                    symbol, 
                    start_date.strftime('%Y-%m-%d'), 
                    end_date.strftime('%Y-%m-%d')
                )
                
                # Sauvegarder les données en base
                from app.models.database import SentimentData
                records_added = 0
                
                # Traiter chaque date dans la période
                current_date = start_date
                while current_date <= end_date:
                    # Vérifier si l'enregistrement existe déjà pour cette date
                    existing_record = symbol_db.query(SentimentData).filter(
                        SentimentData.symbol == symbol,
                        SentimentData.date == current_date
                    ).first()
                    
                    if not existing_record or existing_record.news_count == 0:
                        # Récupérer les données de news spécifiques à cette date
                        # Les news de Polygon ont 'published_utc' au format ISO
                        date_news = []
                        for n in news_data:
                            published_utc = n.get('published_utc', '')
                            if published_utc:
                                try:
                                    from datetime import datetime
                                    # Parser la date ISO et extraire la date
                                    news_date = datetime.fromisoformat(published_utc.replace('Z', '+00:00')).date()
                                    if news_date == current_date:
                                        date_news.append(n)
                                except:
                                    continue
                        
                        # Calculer les métriques de sentiment pour cette date
                        date_sentiment = polygon_service.calculate_sentiment_from_news(date_news, symbol)
                        
                        if existing_record:
                            # Mettre à jour l'enregistrement existant
                            existing_record.news_count = date_sentiment['news_count']
                            existing_record.news_sentiment_score = date_sentiment['news_sentiment_score']
                            existing_record.news_sentiment_std = date_sentiment['news_sentiment_std']
                            existing_record.news_positive_count = date_sentiment['news_positive_count']
                            existing_record.news_negative_count = date_sentiment['news_negative_count']
                            existing_record.news_neutral_count = date_sentiment['news_neutral_count']
                            existing_record.top_news_title = date_sentiment['top_news_title']
                            existing_record.top_news_sentiment = date_sentiment['top_news_sentiment']
                            existing_record.top_news_url = date_sentiment['top_news_url']
                            existing_record.sentiment_reasoning = date_sentiment['sentiment_reasoning']
                        else:
                            # Créer l'enregistrement (uniquement avec les données de news)
                            sentiment_record = SentimentData(
                                symbol=symbol,
                                date=current_date,
                                news_count=date_sentiment['news_count'],
                                news_sentiment_score=date_sentiment['news_sentiment_score'],
                                news_sentiment_std=date_sentiment['news_sentiment_std'],
                                news_positive_count=date_sentiment['news_positive_count'],
                                news_negative_count=date_sentiment['news_negative_count'],
                                news_neutral_count=date_sentiment['news_neutral_count'],
                                top_news_title=date_sentiment['top_news_title'],
                                top_news_sentiment=date_sentiment['top_news_sentiment'],
                                top_news_url=date_sentiment['top_news_url'],
                                sentiment_reasoning=date_sentiment['sentiment_reasoning']
                            )
                            symbol_db.add(sentiment_record)
                        records_added += 1
                    
                    current_date += timedelta(days=1)
                
                # Commit des changements pour ce symbole
                symbol_db.commit()
                
                # Fermer la session
                symbol_db.close()
                
                result = {
                    'symbol': symbol,
                    'status': 'success',
                    'message': f'Données de sentiment mises à jour: {len(news_data)} news, {records_added} nouveaux enregistrements',
                    'records_updated': records_added,
                    'news_count': len(news_data)
                }
                results.append(result)
                
                if result['status'] == 'success':
                    successful_updates += 1
                else:
                    failed_updates += 1
                    
                logger.info(f"Symbole {symbol}: {result['status']} - {result['message']}")
                
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du sentiment pour {symbol}: {e}")
                # Fermer la session en cas d'erreur
                try:
                    symbol_db.close()
                except:
                    pass
                results.append({
                    'symbol': symbol,
                    'status': 'error',
                    'message': str(e)
                })
                failed_updates += 1
        
        final_result = {
            'status': 'completed',
            'total_symbols': total_symbols,
            'successful_updates': successful_updates,
            'failed_updates': failed_updates,
            'results': results,
            'completion_time': datetime.now().isoformat()
        }
        
        self.update_state(state='SUCCESS', meta=final_result)
        logger.info(f"Mise à jour des données de sentiment terminée: {successful_updates}/{total_symbols} réussies")
        return final_result
        
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des données de sentiment: {e}", exc_info=True)
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise

# @celery_app.task(bind=True, name="app.tasks.data_update_tasks.calculate_sentiment_indicators")
# def calculate_sentiment_indicators_task(self) -> Dict[str, Any]:
#     """
#     Calculer les indicateurs de sentiment pour tous les symboles
#     """
#     try:
#         self.update_state(state='PROGRESS', meta={'status': 'Démarrage du calcul des indicateurs de sentiment'})
        
#         db = next(get_db())
#         indicators_service = SentimentIndicatorService()
#         data_service = DataUpdateService(db)
        
#         # Récupérer tous les symboles actifs
#         symbols = data_service.get_active_symbols()
#         total_symbols = len(symbols)
        
#         logger.info(f"Début du calcul des indicateurs de sentiment pour {total_symbols} symboles")
        
#         results = []
#         successful_calculations = 0
#         failed_calculations = 0
        
#         for i, symbol in enumerate(symbols):
#             try:
#                 self.update_state(
#                     state='PROGRESS', 
#                     meta={
#                         'status': f'Calcul des indicateurs de sentiment pour {symbol}',
#                         'progress': int((i / total_symbols) * 100),
#                         'current_symbol': symbol,
#                         'total_symbols': total_symbols
#                     }
#                 )
                
#                 # Créer une nouvelle session pour chaque symbole
#                 symbol_db = next(get_db())
                
#                 # Calculer les indicateurs de sentiment pour ce symbole
#                 indicators_result = indicators_service.calculate_sentiment_indicators(symbol_db, symbol)
                
#                 # Fermer la session
#                 symbol_db.close()
                
#                 result = {
#                     'symbol': symbol,
#                     'status': 'success' if indicators_result else 'error',
#                     'message': 'Indicateurs de sentiment calculés avec succès' if indicators_result else 'Erreur lors du calcul des indicateurs'
#                 }
#                 results.append(result)
                
#                 if result['status'] == 'success':
#                     successful_calculations += 1
#                 else:
#                     failed_calculations += 1
                    
#                 logger.info(f"Symbole {symbol}: {result['status']} - {result['message']}")
                
#             except Exception as e:
#                 logger.error(f"Erreur lors du calcul des indicateurs de sentiment pour {symbol}: {e}")
#                 # Fermer la session en cas d'erreur
#                 try:
#                     symbol_db.close()
#                 except:
#                     pass
#                 results.append({
#                     'symbol': symbol,
#                     'status': 'error',
#                     'message': str(e)
#                 })
#                 failed_calculations += 1
        
#         final_result = {
#             'status': 'completed',
#             'total_symbols': total_symbols,
#             'successful_calculations': successful_calculations,
#             'failed_calculations': failed_calculations,
#             'results': results,
#             'completion_time': datetime.now().isoformat()
#         }
        
#         self.update_state(state='SUCCESS', meta=final_result)
#         logger.info(f"Calcul des indicateurs de sentiment terminé: {successful_calculations}/{total_symbols} réussis")
#         return final_result
        
#     except Exception as e:
#         logger.error(f"Erreur lors du calcul des indicateurs de sentiment: {e}", exc_info=True)
#         self.update_state(state='FAILURE', meta={'error': str(e)})
#         raise

@celery_app.task(bind=True, name="app.tasks.data_update_tasks.full_data_update_workflow")
def full_data_update_workflow_task(self, force_update: bool = False) -> Dict[str, Any]:
    """
    Workflow complet de mise à jour des données
    """
    try:
        self.update_state(state='PROGRESS', meta={'status': 'Démarrage du workflow de mise à jour complet'})
        
        workflow_results = {
            'start_time': datetime.now().isoformat(),
            'steps': [],
            'overall_status': 'in_progress'
        }
        
        # Étape 1: Vérifier la fraîcheur des données
        self.update_state(state='PROGRESS', meta={
            'status': 'Étape 1/5: Vérification de la fraîcheur des données',
            'steps': workflow_results['steps'],
            'overall_status': workflow_results['overall_status'],
            'start_time': workflow_results['start_time']
        })
        freshness_result = check_data_freshness_task.apply()
        workflow_results['steps'].append({
            'step': 1,
            'name': 'Vérification de la fraîcheur',
            'result': freshness_result.result
        })
        
        # Si pas besoin de mise à jour et pas forcé, arrêter ici
        if not freshness_result.result['needs_update'] and not force_update:
            workflow_results['overall_status'] = 'skipped'
            workflow_results['message'] = 'Aucune mise à jour nécessaire'
            self.update_state(state='SUCCESS', meta=workflow_results)
            return workflow_results
        
        # Étape 2: Mise à jour des données historiques
        self.update_state(state='PROGRESS', meta={
            'status': 'Étape 2/5: Mise à jour des données historiques',
            'steps': workflow_results['steps'],
            'overall_status': workflow_results['overall_status'],
            'start_time': workflow_results['start_time']
        })
        historical_result = update_historical_data_task.apply(args=[force_update])
        workflow_results['steps'].append({
            'step': 2,
            'name': 'Mise à jour données historiques',
            'result': historical_result.result
        })
        
        # # Étape 3: Calcul des indicateurs techniques
        # self.update_state(state='PROGRESS', meta={
        #     'status': 'Étape 3/5: Calcul des indicateurs techniques',
        #     'steps': workflow_results['steps'],
        #     'overall_status': workflow_results['overall_status'],
        #     'start_time': workflow_results['start_time']
        # })
        # technical_result = calculate_technical_indicators_task.apply()
        # workflow_results['steps'].append({
        #     'step': 3,
        #     'name': 'Calcul indicateurs techniques',
        #     'result': technical_result.result
        # })
        
        # Étape 4: Mise à jour des données de sentiment
        self.update_state(state='PROGRESS', meta={
            'status': 'Étape 4/5: Mise à jour des données de sentiment',
            'steps': workflow_results['steps'],
            'overall_status': workflow_results['overall_status'],
            'start_time': workflow_results['start_time']
        })
        sentiment_result = update_sentiment_data_task.apply(args=[force_update])
        workflow_results['steps'].append({
            'step': 4,
            'name': 'Mise à jour données de sentiment',
            'result': sentiment_result.result
        })
        
        # # Étape 5: Calcul des indicateurs de sentiment
        # self.update_state(state='PROGRESS', meta={
        #     'status': 'Étape 5/5: Calcul des indicateurs de sentiment',
        #     'steps': workflow_results['steps'],
        #     'overall_status': workflow_results['overall_status'],
        #     'start_time': workflow_results['start_time']
        # })
        # sentiment_indicators_result = calculate_sentiment_indicators_task.apply()
        # workflow_results['steps'].append({
        #     'step': 5,
        #     'name': 'Calcul indicateurs de sentiment',
        #     'result': sentiment_indicators_result.result
        # })
        
        # Finalisation
        workflow_results['overall_status'] = 'completed'
        workflow_results['end_time'] = datetime.now().isoformat()
        workflow_results['message'] = 'Workflow de mise à jour terminé avec succès'
        
        self.update_state(state='SUCCESS', meta=workflow_results)
        logger.info("Workflow de mise à jour des données terminé avec succès")
        return workflow_results
        
    except Exception as e:
        logger.error(f"Erreur lors du workflow de mise à jour: {e}", exc_info=True)
        workflow_results['overall_status'] = 'failed'
        workflow_results['error'] = str(e)
        self.update_state(state='FAILURE', meta=workflow_results)
        raise
