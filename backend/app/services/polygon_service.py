"""
Service pour récupérer les données depuis Polygon.io
"""
import requests
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from decimal import Decimal
import time
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..models.database import HistoricalData, SentimentData, SymbolMetadata
from ..core.config import settings

logger = logging.getLogger(__name__)

class PolygonService:
    """Service pour interagir avec l'API Polygon.io"""
    
    def __init__(self):
        self.api_key = settings.polygon_api_key
        self.base_url = settings.polygon_base_url
        self.rate_limit_delay = settings.polygon_rate_limit_delay
        
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Effectue une requête vers l'API Polygon.io avec gestion des erreurs"""
        if params is None:
            params = {}
        
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') in ['OK', 'DELAYED']:
                return data
            else:
                error_msg = data.get('message', 'Unknown error')
                logger.error(f"Erreur API Polygon: {error_msg}")
                logger.error(f"Endpoint: {endpoint}")
                logger.error(f"Params: {params}")
                logger.error(f"Response: {data}")
                return {}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête vers Polygon.io: {e}")
            logger.error(f"Endpoint: {endpoint}")
            logger.error(f"Params: {params}")
            return {}
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la requête Polygon: {e}")
            logger.error(f"Endpoint: {endpoint}")
            logger.error(f"Params: {params}")
            return {}
    
    def get_ticker_details(self, symbol: str) -> Dict[str, Any]:
        """Récupère les détails d'un ticker"""
        endpoint = f"/v3/reference/tickers/{symbol}"
        return self._make_request(endpoint)
    
    def get_historical_data(self, symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Récupère les données historiques pour un symbole
        
        Args:
            symbol: Symbole du titre (ex: AAPL)
            from_date: Date de début (format YYYY-MM-DD)
            to_date: Date de fin (format YYYY-MM-DD)
        
        Returns:
            Liste des données historiques
        """
        endpoint = f"/v2/aggs/ticker/{symbol}/range/1/day/{from_date}/{to_date}"
        
        data = self._make_request(endpoint)
        
        if not data or 'results' not in data:
            logger.warning(f"Aucune donnée historique trouvée pour {symbol}")
            return []
        
        results = []
        for item in data['results']:
            results.append({
                'symbol': symbol,
                'date': datetime.fromtimestamp(item['t'] / 1000).date(),
                'open': Decimal(str(item['o'])),
                'high': Decimal(str(item['h'])),
                'low': Decimal(str(item['l'])),
                'close': Decimal(str(item['c'])),
                'volume': int(item['v']),
                'vwap': Decimal(str(item.get('vw', item['c'])))  # VWAP ou close si non disponible
            })
        
        logger.info(f"Récupéré {len(results)} jours de données historiques pour {symbol}")
        return results
    
    def get_news_data(self, symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Récupère les données de news pour un symbole
        
        Args:
            symbol: Symbole du titre
            from_date: Date de début (format YYYY-MM-DD)
            to_date: Date de fin (format YYYY-MM-DD)
        
        Returns:
            Liste des données de news
        """
        endpoint = "/v2/reference/news"
        params = {
            'ticker': symbol,
            'published_utc.gte': f"{from_date}T00:00:00Z",
            'published_utc.lte': f"{to_date}T23:59:59Z",
            'limit': 1000  # Maximum par requête
        }
        
        all_news = []
        next_url = None
        
        while True:
            if next_url:
                # Pour les requêtes suivantes, utiliser l'URL complète
                try:
                    response = requests.get(next_url, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                except Exception as e:
                    logger.error(f"Erreur lors de la récupération des news suivantes: {e}")
                    break
            else:
                data = self._make_request(endpoint, params)
            
            if not data or 'results' not in data:
                break
            
            all_news.extend(data['results'])
            
            # Vérifier s'il y a une page suivante
            if 'next_url' in data:
                next_url = data['next_url']
                time.sleep(self.rate_limit_delay)  # Respecter le rate limit
            else:
                break
        
        logger.info(f"Récupéré {len(all_news)} articles de news pour {symbol}")
        return all_news
    
    
    
    def get_latest_data_date(self, symbol: str) -> Optional[date]:
        """
        Récupère la date des données les plus récentes disponibles sur Polygon
        
        Args:
            symbol: Symbole du titre
        
        Returns:
            Date des données les plus récentes ou None
        """
        # Récupérer les données des 5 derniers jours pour trouver la date la plus récente
        end_date = date.today()
        start_date = end_date - timedelta(days=5)
        
        data = self.get_historical_data(
            symbol, 
            start_date.strftime('%Y-%m-%d'), 
            end_date.strftime('%Y-%m-%d')
        )
        
        if not data:
            return None
        
        # Retourner la date la plus récente
        latest_date = max(item['date'] for item in data)
        return latest_date
    
    def get_database_latest_date(self, db: Session, symbol: str, table_class) -> Optional[date]:
        """
        Récupère la date la plus récente dans la base de données pour un symbole
        
        Args:
            db: Session SQLAlchemy
            symbol: Symbole du titre
            table_class: Classe de la table (HistoricalData ou SentimentData)
        
        Returns:
            Date la plus récente ou None
        """
        result = db.query(func.max(table_class.date)).filter(
            table_class.symbol == symbol
        ).first()
        
        return result[0] if result and result[0] else None
    
    def get_symbols_to_update(self, db: Session) -> List[str]:
        """
        Récupère la liste des symboles actifs à mettre à jour
        
        Returns:
            Liste des symboles actifs
        """
        symbols = db.query(SymbolMetadata.symbol).filter(
            SymbolMetadata.is_active == True
        ).all()
        
        return [symbol[0] for symbol in symbols]
    
    def calculate_sentiment_from_news(self, news_data: List[Dict[str, Any]], symbol: str) -> Dict[str, Any]:
        """
        Calcule les métriques de sentiment à partir des données de news en utilisant les insights de Polygon
        
        Args:
            news_data: Liste des données de news
            symbol: Symbole pour lequel calculer le sentiment
        
        Returns:
            Dictionnaire avec les métriques de sentiment calculées
        """
        if not news_data:
            return {
                'news_count': 0,
                'news_sentiment_score': Decimal('0.0'),
                'news_sentiment_std': Decimal('0.0'),
                'news_positive_count': 0,
                'news_negative_count': 0,
                'news_neutral_count': 0,
                'top_news_title': None,
                'top_news_sentiment': None,
                'top_news_url': None,
                'sentiment_reasoning': None
            }
        
        # Analyser le sentiment en utilisant les insights de Polygon
        sentiment_scores = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        all_reasonings = []
        
        top_news = None
        max_sentiment = 0.0
        top_reasoning = None
        
        for news in news_data:
            # Chercher les insights pour ce symbole
            insights = news.get('insights', [])
            symbol_insight = None
            
            for insight in insights:
                if insight.get('ticker') == symbol:
                    symbol_insight = insight
                    break
            
            if symbol_insight:
                # Utiliser le sentiment de Polygon
                sentiment = symbol_insight.get('sentiment', 'neutral')
                reasoning = symbol_insight.get('sentiment_reasoning', '')
                
                # Convertir le sentiment en score numérique
                if sentiment == 'positive':
                    score = 1.0
                    positive_count += 1
                elif sentiment == 'negative':
                    score = -1.0
                    negative_count += 1
                else:  # neutral
                    score = 0.0
                    neutral_count += 1
                
                sentiment_scores.append(score)
                if reasoning:
                    all_reasonings.append(reasoning)
                
                # Garder la news avec le sentiment le plus fort
                if abs(score) > abs(max_sentiment):
                    max_sentiment = score
                    top_news = news
                    top_reasoning = reasoning
            else:
                # Fallback: analyse basique des mots-clés si pas d'insights
                title = news.get('title', '').lower()
                description = news.get('description', '').lower()
                text = f"{title} {description}"
                
                # Mots-clés pour l'analyse de sentiment (fallback)
                positive_words = ['rise', 'gain', 'up', 'positive', 'growth', 'profit', 'beat', 'exceed', 'strong']
                negative_words = ['fall', 'drop', 'down', 'negative', 'loss', 'decline', 'miss', 'weak', 'concern']
                
                positive_matches = sum(1 for word in positive_words if word in text)
                negative_matches = sum(1 for word in negative_words if word in text)
                
                if positive_matches > negative_matches:
                    score = 0.5
                    positive_count += 1
                elif negative_matches > positive_matches:
                    score = -0.5
                    negative_count += 1
                else:
                    score = 0.0
                    neutral_count += 1
                
                sentiment_scores.append(score)
                
                # Garder la news avec le sentiment le plus fort (fallback)
                if abs(score) > abs(max_sentiment):
                    max_sentiment = score
                    top_news = news
                    top_reasoning = None
        
        # Calculer les statistiques
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            sentiment_std = (sum((s - avg_sentiment) ** 2 for s in sentiment_scores) / len(sentiment_scores)) ** 0.5
        else:
            avg_sentiment = 0.0
            sentiment_std = 0.0
        
        # Combiner les raisonnements
        combined_reasoning = '; '.join(all_reasonings) if all_reasonings else None
        
        return {
            'news_count': len(news_data),
            'news_sentiment_score': Decimal(str(round(avg_sentiment, 4))),
            'news_sentiment_std': Decimal(str(round(sentiment_std, 4))),
            'news_positive_count': positive_count,
            'news_negative_count': negative_count,
            'news_neutral_count': neutral_count,
            'top_news_title': top_news.get('title') if top_news else None,
            'top_news_sentiment': Decimal(str(round(max_sentiment, 4))) if top_news else None,
            'top_news_url': top_news.get('article_url') if top_news else None,
            'sentiment_reasoning': combined_reasoning
        }
    
    def is_market_open(self, check_date: date = None) -> bool:
        """
        Vérifie si le marché Nasdaq est ouvert à une date donnée
        
        Args:
            check_date: Date à vérifier (par défaut aujourd'hui)
        
        Returns:
            True si le marché est ouvert, False sinon
        """
        if check_date is None:
            check_date = date.today()
        
        # Le marché Nasdaq est fermé le weekend
        if check_date.weekday() >= 5:  # Samedi = 5, Dimanche = 6
            return False
        
        # Vérifier les jours fériés américains (liste simplifiée)
        holidays_2024 = [
            date(2024, 1, 1),   # New Year's Day
            date(2024, 1, 15),  # Martin Luther King Jr. Day
            date(2024, 2, 19),  # Presidents' Day
            date(2024, 3, 29),  # Good Friday
            date(2024, 5, 27),  # Memorial Day
            date(2024, 6, 19),  # Juneteenth
            date(2024, 7, 4),   # Independence Day
            date(2024, 9, 2),   # Labor Day
            date(2024, 11, 28), # Thanksgiving
            date(2024, 12, 25), # Christmas Day
        ]
        
        if check_date in holidays_2024:
            return False
        
        return True
    
    def get_last_trading_day(self, check_date: date = None) -> date:
        """
        Récupère le dernier jour de trading avant une date donnée
        
        Args:
            check_date: Date de référence (par défaut aujourd'hui)
        
        Returns:
            Dernier jour de trading
        """
        if check_date is None:
            check_date = date.today()
        
        # Si c'est un jour de trading, retourner cette date
        if self.is_market_open(check_date):
            return check_date
        
        # Sinon, chercher le jour précédent
        previous_day = check_date - timedelta(days=1)
        return self.get_last_trading_day(previous_day)
    
    def should_update_data(self, db: Session, symbol: str) -> Tuple[bool, Optional[date], Optional[date]]:
        """
        Détermine si les données doivent être mises à jour pour un symbole
        
        Args:
            db: Session SQLAlchemy
            symbol: Symbole du titre
        
        Returns:
            Tuple (should_update, db_latest_date, polygon_latest_date)
        """
        # Récupérer la dernière date en base
        db_latest_date = self.get_database_latest_date(db, symbol, HistoricalData)
        
        # Récupérer la dernière date disponible sur Polygon
        polygon_latest_date = self.get_latest_data_date(symbol)
        
        if not polygon_latest_date:
            logger.warning(f"Impossible de récupérer la date la plus récente pour {symbol}")
            return False, db_latest_date, None
        
        # Récupérer le dernier jour de trading
        last_trading_day = self.get_last_trading_day()
        
        # Déterminer si une mise à jour est nécessaire
        should_update = False
        
        if db_latest_date is None:
            # Aucune donnée en base, mise à jour nécessaire
            should_update = True
        elif db_latest_date < polygon_latest_date:
            # Les données Polygon sont plus récentes
            should_update = True
        elif db_latest_date < last_trading_day:
            # Les données en base sont antérieures au dernier jour de trading
            should_update = True
        
        return should_update, db_latest_date, polygon_latest_date
    
    def update_historical_data(self, symbol: str, force_update: bool = False) -> Dict[str, Any]:
        """
        Met à jour les données historiques pour un symbole
        
        Args:
            symbol: Symbole du titre (ex: AAPL)
            force_update: Forcer la mise à jour même si les données sont récentes
        
        Returns:
            Dictionnaire avec le statut de la mise à jour
        """
        try:
            from app.core.database import get_db
            from app.models.database import HistoricalData
            from sqlalchemy.orm import Session
            from sqlalchemy import func, desc
            
            logger.info(f"Mise à jour des données historiques pour {symbol}")
            
            # Obtenir une session de base de données
            db = next(get_db())
            
            try:
                # 1. Déterminer la dernière date de données pour ce symbole
                last_date_result = db.query(func.max(HistoricalData.date)).filter(
                    HistoricalData.symbol == symbol
                ).first()
                
                last_date = last_date_result[0] if last_date_result[0] else None
                
                # 2. Déterminer la date de fin (hier pour éviter les données incomplètes)
                from datetime import datetime, timedelta, timezone
                end_date = (datetime.now() - timedelta(days=1)).date()
                
                # 3. Déterminer la date de début pour la mise à jour
                if last_date:
                    # Commencer le jour suivant la dernière date
                    start_date = last_date + timedelta(days=1)
                    
                    # Vérifier que start_date n'est pas postérieur à end_date
                    if start_date > end_date:
                        # Les données sont déjà à jour, pas besoin de récupérer
                        return {
                            'symbol': symbol,
                            'status': 'success',
                            'message': f'Données déjà à jour jusqu\'à {last_date}',
                            'records_updated': 0,
                            'last_date': last_date
                        }
                else:
                    # Si aucune donnée, récupérer les 5 dernières années
                    start_date = (datetime.now() - timedelta(days=365*5)).date()
                
                # 4. Vérifier si nous avons besoin de mettre à jour (logique de fraîcheur basée sur l'heure de clôture NASDAQ)
                if not force_update and last_date:
                    # Obtenir l'heure de la dernière mise à jour (created_at) pour ce symbole
                    last_update_result = db.query(func.max(HistoricalData.created_at)).filter(
                        HistoricalData.symbol == symbol
                    ).first()
                    
                    if last_update_result[0]:
                        last_update_datetime = last_update_result[0]
                        
                        # Calculer l'heure de clôture NASDAQ pour la date de la dernière donnée
                        from app.services.data_update_service import DataUpdateService
                        data_update_service = DataUpdateService(db)
                        
                        # Convertir last_date en datetime pour la comparaison
                        last_date_datetime = datetime.combine(last_date, datetime.min.time())
                        nasdaq_close_time = data_update_service.get_nasdaq_close_time_utc2(last_date_datetime)
                        
                        # Convertir last_update_datetime en UTC+2 si nécessaire
                        if last_update_datetime.tzinfo is None:
                            last_update_utc2 = last_update_datetime.replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=2)))
                        else:
                            last_update_utc2 = last_update_datetime.astimezone(timezone(timedelta(hours=2)))
                        
                        # Vérifier si la mise à jour est postérieure à la clôture NASDAQ
                        if last_update_utc2 >= nasdaq_close_time:
                            return {
                                'symbol': symbol,
                                'status': 'success',
                                'message': f'Données déjà à jour jusqu\'à {last_date} (mise à jour après clôture NASDAQ)',
                                'records_updated': 0,
                                'last_date': last_date
                            }
                
                # 5. Récupérer les nouvelles données depuis Polygon
                logger.info(f"Récupération des données pour {symbol} du {start_date} au {end_date}")
                historical_data = self.get_historical_data(symbol, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
                
                if not historical_data:
                    return {
                        'symbol': symbol,
                        'status': 'success',
                        'message': f'Aucune nouvelle donnée disponible pour {symbol}',
                        'records_updated': 0,
                        'last_date': last_date
                    }
                
                # 6. Sauvegarder les nouvelles données en base
                records_added = 0
                for data_point in historical_data:
                    # Vérifier si l'enregistrement existe déjà
                    existing_record = db.query(HistoricalData).filter(
                        HistoricalData.symbol == symbol,
                        HistoricalData.date == data_point['date']
                    ).first()
                    
                    if not existing_record:
                        # Créer un nouvel enregistrement
                        new_record = HistoricalData(
                            symbol=symbol,
                            date=data_point['date'],
                            open=data_point['open'],
                            high=data_point['high'],
                            low=data_point['low'],
                            close=data_point['close'],
                            volume=data_point['volume'],
                            vwap=data_point.get('vwap')  # VWAP peut être None
                        )
                        db.add(new_record)
                        records_added += 1
                
                # 7. Valider les changements
                db.commit()
                
                # 8. Obtenir la nouvelle dernière date
                new_last_date_result = db.query(func.max(HistoricalData.date)).filter(
                    HistoricalData.symbol == symbol
                ).first()
                new_last_date = new_last_date_result[0] if new_last_date_result[0] else last_date
                
                logger.info(f"Symbole {symbol}: {records_added} nouveaux enregistrements ajoutés")
                
                return {
                    'symbol': symbol,
                    'status': 'success',
                    'message': f'Données historiques mises à jour avec succès pour {symbol} ({records_added} nouveaux enregistrements)',
                    'records_updated': records_added,
                    'last_date': new_last_date
                }
                
            finally:
                db.close()
            
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour des données historiques pour {symbol}: {e}")
            return {
                'symbol': symbol,
                'status': 'error',
                'message': str(e),
                'records_updated': 0,
                'last_date': None
            }