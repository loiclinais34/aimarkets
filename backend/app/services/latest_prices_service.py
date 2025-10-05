"""
Service pour récupérer les derniers cours des titres
"""

from datetime import datetime, date
from typing import Dict, List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import desc
import logging

from app.models.database import HistoricalData

logger = logging.getLogger(__name__)


class LatestPricesService:
    """Service pour récupérer les derniers cours des titres"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_latest_price(self, symbol: str) -> Optional[Dict]:
        """
        Récupère le dernier cours connu pour un symbole
        
        Args:
            symbol: Symbole du titre (ex: "AAPL")
            
        Returns:
            Dict contenant les informations du dernier cours ou None si non trouvé
        """
        try:
            latest_data = (
                self.db.query(HistoricalData)
                .filter(HistoricalData.symbol == symbol.upper())
                .order_by(desc(HistoricalData.date))
                .first()
            )
            
            if not latest_data:
                logger.warning(f"Aucun cours trouvé pour le symbole {symbol}")
                return None
            
            return {
                "symbol": latest_data.symbol,
                "price": float(latest_data.close),
                "date": latest_data.date,
                "volume": latest_data.volume,
                "currency": "USD"  # Par défaut
            }
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du cours pour {symbol}: {e}")
            return None
    
    def get_latest_prices(self, symbols: List[str]) -> Dict[str, Dict]:
        """
        Récupère les derniers cours pour une liste de symboles
        
        Args:
            symbols: Liste des symboles
            
        Returns:
            Dict avec les symboles comme clés et les informations de cours comme valeurs
        """
        result = {}
        
        for symbol in symbols:
            price_info = self.get_latest_price(symbol)
            if price_info:
                result[symbol] = price_info
        
        logger.info(f"Récupéré {len(result)} cours sur {len(symbols)} symboles demandés")
        return result
    
    def get_symbols_from_positions(self, positions: List) -> List[str]:
        """
        Extrait la liste des symboles uniques d'une liste de positions
        
        Args:
            positions: Liste des positions (objets avec attribut symbol)
            
        Returns:
            Liste des symboles uniques
        """
        symbols = []
        for position in positions:
            if hasattr(position, 'symbol') and position.symbol:
                symbols.append(position.symbol)
        
        return list(set(symbols))  # Supprimer les doublons
    
    def update_positions_with_latest_prices(self, positions: List) -> List:
        """
        Met à jour une liste de positions avec les derniers cours
        
        Args:
            positions: Liste des positions à mettre à jour
            
        Returns:
            Liste des positions mises à jour
        """
        if not positions:
            return positions
        
        # Extraire les symboles
        symbols = self.get_symbols_from_positions(positions)
        
        # Récupérer les derniers cours
        latest_prices = self.get_latest_prices(symbols)
        
        # Mettre à jour chaque position
        for position in positions:
            if hasattr(position, 'symbol') and position.symbol in latest_prices:
                price_info = latest_prices[position.symbol]
                # S'assurer que current_price est un Decimal
                if isinstance(position.current_price, float):
                    position.current_price = Decimal(str(position.current_price))
                else:
                    position.current_price = Decimal(str(price_info["price"]))
                
                # Recalculer la valeur de marché et le P&L
                if hasattr(position, 'quantity') and position.quantity:
                    position.current_value = position.quantity * position.current_price
                    
                    if hasattr(position, 'total_cost') and position.total_cost:
                        position.unrealized_pnl = position.current_value - position.total_cost
                        
                        if position.total_cost > 0:
                            position.unrealized_pnl_percentage = (
                                position.unrealized_pnl / position.total_cost
                            ) * 100
        
        return positions
