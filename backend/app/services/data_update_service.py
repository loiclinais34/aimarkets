"""
Service de gestion des mises à jour de données
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text, func

logger = logging.getLogger(__name__)

class DataUpdateService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_nasdaq_close_time_utc2(self, target_date: datetime = None) -> datetime:
        """
        Calculer l'heure de clôture du NASDAQ en UTC+2 (Paris)
        Le NASDAQ ferme à 16h00 EST (Eastern Standard Time)
        EST = UTC-5, donc 16h00 EST = 21h00 UTC
        En UTC+2 (Paris), cela donne 23h00
        """
        if target_date is None:
            target_date = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=2)))
        
        # Convertir en UTC+2 si ce n'est pas déjà le cas
        if target_date.tzinfo is None:
            target_date = target_date.replace(tzinfo=timezone(timedelta(hours=2)))
        elif target_date.tzinfo != timezone(timedelta(hours=2)):
            target_date = target_date.astimezone(timezone(timedelta(hours=2)))
        
        # NASDAQ ferme à 16h00 EST = 23h00 UTC+2
        nasdaq_close_hour = 23
        
        # Si c'est un jour de semaine et avant 23h00, utiliser la date actuelle
        # Sinon, utiliser le prochain jour ouvrable
        if target_date.weekday() < 5 and target_date.hour < nasdaq_close_hour:
            close_time = target_date.replace(hour=nasdaq_close_hour, minute=0, second=0, microsecond=0)
        else:
            # Trouver le prochain jour ouvrable
            days_ahead = 1
            while (target_date + timedelta(days=days_ahead)).weekday() > 4:  # 0-4 = lundi-vendredi
                days_ahead += 1
            next_weekday = target_date + timedelta(days=days_ahead)
            close_time = next_weekday.replace(hour=nasdaq_close_hour, minute=0, second=0, microsecond=0)
        
        return close_time
    
    def get_last_trading_day_close_time_utc2(self) -> datetime:
        """
        Obtenir l'heure de clôture du dernier jour de trading effectivement terminé en UTC+2
        """
        now_utc2 = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=2)))
        
        # Si c'est un jour de semaine et avant 23h00, les données d'aujourd'hui ne sont pas encore disponibles
        # Donc la dernière clôture effective est celle d'hier
        if now_utc2.weekday() < 5 and now_utc2.hour < 23:
            # Trouver le dernier jour ouvrable terminé
            days_back = 1
            while (now_utc2 - timedelta(days=days_back)).weekday() > 4:  # 0-4 = lundi-vendredi
                days_back += 1
            last_completed_weekday = now_utc2 - timedelta(days=days_back)
            return last_completed_weekday.replace(hour=23, minute=0, second=0, microsecond=0)
        
        # Si c'est après 23h00 ou un weekend, la dernière clôture effective est celle d'aujourd'hui
        if now_utc2.weekday() < 5:  # Jour de semaine
            return now_utc2.replace(hour=23, minute=0, second=0, microsecond=0)
        
        # Si c'est un weekend, trouver le dernier vendredi
        days_back = 1
        while (now_utc2 - timedelta(days=days_back)).weekday() != 4:  # 4 = vendredi
            days_back += 1
        last_friday = now_utc2 - timedelta(days=days_back)
        return last_friday.replace(hour=23, minute=0, second=0, microsecond=0)
    
    def check_historical_data_freshness(self) -> Dict[str, Any]:
        """
        Vérifier la fraîcheur des données historiques en comparant avec l'heure de clôture du NASDAQ
        """
        try:
            # Récupérer la date et l'heure de la dernière mise à jour (created_at)
            result = self.db.execute(text("""
                SELECT MAX(created_at) as last_update_datetime, COUNT(*) as total_records
                FROM historical_data
            """)).fetchone()
            
            if not result or not result[0]:
                return {
                    'needs_update': True,
                    'last_update_date': None,
                    'total_records': 0,
                    'hours_since_update': None,
                    'hours_behind_nasdaq_close': None,
                    'message': 'Aucune donnée historique trouvée'
                }
            
            last_update_datetime = result[0]
            total_records = result[1]
            
            # Obtenir l'heure de clôture du dernier jour de trading NASDAQ en UTC+2
            nasdaq_close_time = self.get_last_trading_day_close_time_utc2()
            
            # Convertir last_update_datetime en UTC+2 si nécessaire
            if last_update_datetime.tzinfo is None:
                # Supposer que c'est en UTC si pas de timezone
                last_update_utc2 = last_update_datetime.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=2)))
            else:
                last_update_utc2 = last_update_datetime.astimezone(timezone(timedelta(hours=2)))
            
            # Calculer les heures depuis la dernière mise à jour (pour compatibilité)
            now_utc2 = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=2)))
            hours_since_update = (now_utc2 - last_update_utc2).total_seconds() / 3600
            
            # Calculer le retard par rapport à la clôture NASDAQ
            hours_behind_nasdaq_close = (nasdaq_close_time - last_update_utc2).total_seconds() / 3600
            
            # Déterminer si une mise à jour est nécessaire
            # Vérifier si les données sont à jour par rapport à la dernière clôture NASDAQ
            if hours_behind_nasdaq_close > 0:
                # Les données sont en retard par rapport à la dernière clôture
                needs_update = True
            else:
                # Les données sont à jour par rapport à la dernière clôture
                needs_update = False
            
            # Déterminer le message
            if needs_update:
                if hours_behind_nasdaq_close < 1:
                    message = f'Mise à jour nécessaire ({int(hours_behind_nasdaq_close * 60)} minutes de retard)'
                elif hours_behind_nasdaq_close < 24:
                    message = f'Mise à jour urgente ({int(hours_behind_nasdaq_close)}h de retard)'
                else:
                    days_behind = int(hours_behind_nasdaq_close / 24)
                    hours_remaining = int(hours_behind_nasdaq_close % 24)
                    message = f'Mise à jour urgente ({days_behind}j {hours_remaining}h de retard)'
            else:
                # Les données sont à jour par rapport à la dernière clôture
                if now_utc2.weekday() < 5 and now_utc2.hour < 23:
                    # Avant la clôture d'aujourd'hui
                    next_close_hour = 23 - now_utc2.hour
                    next_close_min = 60 - now_utc2.minute
                    if next_close_min == 60:
                        next_close_min = 0
                        next_close_hour += 1
                    message = f'Données à jour (prochaine clôture dans {next_close_hour}h {next_close_min}min)'
                else:
                    message = 'Données à jour'
            
            return {
                'needs_update': needs_update,
                'last_update_date': last_update_utc2.strftime('%Y-%m-%d %H:%M:%S'),
                'total_records': total_records,
                'hours_since_update': round(hours_since_update, 2),
                'hours_behind_nasdaq_close': round(hours_behind_nasdaq_close, 2),
                'nasdaq_close_time': nasdaq_close_time.strftime('%Y-%m-%d %H:%M:%S'),
                'message': message
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la fraîcheur des données historiques: {e}")
            return {
                'needs_update': True,
                'error': str(e),
                'message': 'Erreur lors de la vérification'
            }
    
    def check_sentiment_data_freshness(self) -> Dict[str, Any]:
        """
        Vérifier la fraîcheur des données de sentiment
        """
        try:
            # Récupérer la date de la dernière mise à jour
            result = self.db.execute(text("""
                SELECT MAX(created_at) as last_update_date, COUNT(*) as total_records
                FROM sentiment_data
            """)).fetchone()
            
            if not result or not result[0]:
                return {
                    'needs_update': True,
                    'last_update_date': None,
                    'total_records': 0,
                    'hours_since_update': None,
                    'message': 'Aucune donnée de sentiment trouvée'
                }
            
            last_update_date = result[0]
            total_records = result[1]
            
            # Calculer les heures depuis la dernière mise à jour
            if isinstance(last_update_date, datetime):
                hours_since_update = (datetime.now() - last_update_date).total_seconds() / 3600
            else:
                # Si c'est une date, convertir en datetime à minuit
                last_update_datetime = datetime.combine(last_update_date, datetime.min.time())
                hours_since_update = (datetime.now() - last_update_datetime).total_seconds() / 3600
            
            needs_update = hours_since_update > 8
            
            return {
                'needs_update': needs_update,
                'last_update_date': last_update_date.isoformat(),
                'total_records': total_records,
                'hours_since_update': round(hours_since_update, 2),
                'message': f'Dernière mise à jour il y a {round(hours_since_update, 1)} heures'
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la fraîcheur des données de sentiment: {e}")
            return {
                'needs_update': True,
                'error': str(e),
                'message': 'Erreur lors de la vérification'
            }
    
    def get_active_symbols(self) -> List[str]:
        """
        Récupérer la liste des symboles actifs
        """
        try:
            result = self.db.execute(text("""
                SELECT DISTINCT symbol 
                FROM historical_data 
                WHERE symbol IS NOT NULL 
                ORDER BY symbol
            """)).fetchall()
            
            return [row[0] for row in result]
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des symboles actifs: {e}")
            return []
    
    def get_data_stats(self) -> Dict[str, Any]:
        """
        Récupérer les statistiques générales des données
        """
        try:
            # Statistiques des données historiques
            historical_stats = self.db.execute(text("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date
                FROM historical_data
            """)).fetchone()
            
            # Statistiques des données de sentiment
            sentiment_stats = self.db.execute(text("""
                SELECT 
                    COUNT(*) as total_records,
                    COUNT(DISTINCT symbol) as unique_symbols,
                    MIN(date) as earliest_date,
                    MAX(date) as latest_date
                FROM sentiment_data
            """)).fetchone()
            
            return {
                'historical_data': {
                    'total_records': historical_stats[0] if historical_stats else 0,
                    'unique_symbols': historical_stats[1] if historical_stats else 0,
                    'earliest_date': historical_stats[2].isoformat() if historical_stats and historical_stats[2] else None,
                    'latest_date': historical_stats[3].isoformat() if historical_stats and historical_stats[3] else None
                },
                'sentiment_data': {
                    'total_records': sentiment_stats[0] if sentiment_stats else 0,
                    'unique_symbols': sentiment_stats[1] if sentiment_stats else 0,
                    'earliest_date': sentiment_stats[2].isoformat() if sentiment_stats and sentiment_stats[2] else None,
                    'latest_date': sentiment_stats[3].isoformat() if sentiment_stats and sentiment_stats[3] else None
                },
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des statistiques: {e}")
            return {
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
    
    def get_update_status(self) -> Dict[str, Any]:
        """
        Récupérer le statut global des mises à jour
        """
        try:
            historical_freshness = self.check_historical_data_freshness()
            sentiment_freshness = self.check_sentiment_data_freshness()
            data_stats = self.get_data_stats()
            
            # Déterminer le statut global basé uniquement sur les données historiques
            overall_status = 'up_to_date'
            if historical_freshness.get('needs_update', False):
                overall_status = 'needs_update'
            
            return {
                'overall_status': overall_status,
                'historical_freshness': historical_freshness,
                'sentiment_freshness': sentiment_freshness,
                'data_stats': data_stats,
                'last_check': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du statut des mises à jour: {e}")
            return {
                'overall_status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }