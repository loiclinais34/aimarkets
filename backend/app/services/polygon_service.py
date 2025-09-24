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

logger = logging.getLogger(__name__)

class PolygonService:
    """Service pour interagir avec l'API Polygon.io"""
    
    def __init__(self):
        self.api_key = "HVxEJr0Up37u0LNBN24tqb23qGKHW6Qt"
        self.base_url = "https://api.polygon.io"
        self.rate_limit_delay = 0.1  # 100ms entre les requêtes pour respecter les limites
        
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
    
    def get_short_interest_data(self, symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Récupère les données de short interest
        
        Args:
            symbol: Symbole du titre
            from_date: Date de début (format YYYY-MM-DD)
            to_date: Date de fin (format YYYY-MM-DD)
        
        Returns:
            Liste des données de short interest
        """
        endpoint = f"/stocks/v1/short-interest/{symbol}"
        params = {
            'timestamp.gte': from_date,
            'timestamp.lte': to_date
        }
        
        data = self._make_request(endpoint, params)
        
        if not data or 'results' not in data:
            logger.warning(f"Aucune donnée de short interest trouvée pour {symbol}")
            return []
        
        results = []
        for item in data['results']:
            results.append({
                'symbol': symbol,
                'date': datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00')).date(),
                'short_interest_ratio': Decimal(str(item.get('short_interest_ratio', 0))),
                'short_interest_volume': int(item.get('short_interest_volume', 0)),
                'short_interest_date': datetime.fromisoformat(item.get('short_interest_date', item['timestamp']).replace('Z', '+00:00')).date() if item.get('short_interest_date') else None
            })
        
        logger.info(f"Récupéré {len(results)} points de short interest pour {symbol}")
        return results
    
    def get_short_volume_data(self, symbol: str, from_date: str, to_date: str) -> List[Dict[str, Any]]:
        """
        Récupère les données de short volume
        
        Args:
            symbol: Symbole du titre
            from_date: Date de début (format YYYY-MM-DD)
            to_date: Date de fin (format YYYY-MM-DD)
        
        Returns:
            Liste des données de short volume
        """
        endpoint = f"/stocks/v1/short-volume/{symbol}"
        params = {
            'timestamp.gte': from_date,
            'timestamp.lte': to_date
        }
        
        data = self._make_request(endpoint, params)
        
        if not data or 'results' not in data:
            logger.warning(f"Aucune donnée de short volume trouvée pour {symbol}")
            return []
        
        results = []
        for item in data['results']:
            results.append({
                'symbol': symbol,
                'date': datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00')).date(),
                'short_volume': int(item.get('short_volume', 0)),
                'short_exempt_volume': int(item.get('short_exempt_volume', 0)),
                'total_volume': int(item.get('total_volume', 0)),
                'short_volume_ratio': Decimal(str(item.get('short_volume_ratio', 0)))
            })
        
        logger.info(f"Récupéré {len(results)} points de short volume pour {symbol}")
        return results
    
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
    
    def calculate_sentiment_from_news(self, news_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calcule les métriques de sentiment à partir des données de news
        
        Args:
            news_data: Liste des données de news
        
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
                'top_news_url': None
            }
        
        # Analyser le sentiment des titres (simulation basique)
        sentiment_scores = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        # Mots-clés pour l'analyse de sentiment (très basique)
        positive_words = ['rise', 'gain', 'up', 'positive', 'growth', 'profit', 'beat', 'exceed', 'strong']
        negative_words = ['fall', 'drop', 'down', 'negative', 'loss', 'decline', 'miss', 'weak', 'concern']
        
        top_news = None
        max_sentiment = -1
        
        for news in news_data:
            title = news.get('title', '').lower()
            description = news.get('description', '').lower()
            text = f"{title} {description}"
            
            # Calculer un score de sentiment basique
            positive_score = sum(1 for word in positive_words if word in text)
            negative_score = sum(1 for word in negative_words if word in text)
            
            if positive_score > negative_score:
                sentiment = 0.5 + (positive_score - negative_score) * 0.1
                positive_count += 1
            elif negative_score > positive_score:
                sentiment = 0.5 - (negative_score - positive_score) * 0.1
                negative_count += 1
            else:
                sentiment = 0.5
                neutral_count += 1
            
            sentiment_scores.append(sentiment)
            
            # Garder la news avec le sentiment le plus fort
            if abs(sentiment - 0.5) > abs(max_sentiment - 0.5):
                max_sentiment = sentiment
                top_news = news
        
        # Calculer les statistiques
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.5
        sentiment_std = (sum((s - avg_sentiment) ** 2 for s in sentiment_scores) / len(sentiment_scores)) ** 0.5 if sentiment_scores else 0.0
        
        return {
            'news_count': len(news_data),
            'news_sentiment_score': Decimal(str(round(avg_sentiment, 4))),
            'news_sentiment_std': Decimal(str(round(sentiment_std, 4))),
            'news_positive_count': positive_count,
            'news_negative_count': negative_count,
            'news_neutral_count': neutral_count,
            'top_news_title': top_news.get('title') if top_news else None,
            'top_news_sentiment': Decimal(str(round(max_sentiment, 4))) if top_news else None,
            'top_news_url': top_news.get('article_url') if top_news else None
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
