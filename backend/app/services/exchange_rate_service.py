"""
Service de gestion des taux de change
"""

import requests
from decimal import Decimal
from typing import Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.models.exchange_rates import ExchangeRate
from app.core.config import get_settings

settings = get_settings()


class ExchangeRateService:
    def __init__(self, db: Session):
        self.db = db
        self.api_key = getattr(settings, 'EXCHANGE_API_KEY', None)
        self.base_url = "https://api.exchangerate-api.com/v4/latest"  # Free API
        self.cache_duration = timedelta(hours=1)  # Cache rates for 1 hour
    
    def get_exchange_rate(
        self, 
        from_currency: str, 
        to_currency: str, 
        force_refresh: bool = False
    ) -> Optional[ExchangeRate]:
        """
        Récupère le taux de change entre deux devises
        
        Args:
            from_currency: Devise source (ex: 'USD')
            to_currency: Devise cible (ex: 'EUR')
            force_refresh: Force la mise à jour depuis l'API
            
        Returns:
            ExchangeRate object ou None si non trouvé
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        if from_currency == to_currency:
            # Même devise, taux = 1
            return ExchangeRate(
                from_currency=from_currency,
                to_currency=to_currency,
                pair=f"{from_currency}/{to_currency}",
                rate=Decimal('1.000000'),
                inverse_rate=Decimal('1.000000'),
                source="identity",
                is_active=True
            )
        
        # Chercher en base de données
        if not force_refresh:
            rate = self.db.query(ExchangeRate).filter(
                and_(
                    ExchangeRate.from_currency == from_currency,
                    ExchangeRate.to_currency == to_currency,
                    ExchangeRate.is_active == True
                )
            ).first()
            
            # Vérifier si le taux est encore valide (pas trop ancien)
            if rate and rate.last_fetched_at:
                if datetime.utcnow() - rate.last_fetched_at < self.cache_duration:
                    return rate
        
        # Récupérer depuis l'API
        try:
            new_rate = self._fetch_from_api(from_currency, to_currency)
            if new_rate:
                # Désactiver les anciens taux
                self.db.query(ExchangeRate).filter(
                    and_(
                        ExchangeRate.from_currency == from_currency,
                        ExchangeRate.to_currency == to_currency
                    )
                ).update({"is_active": False})
                
                # Ajouter le nouveau taux
                self.db.add(new_rate)
                self.db.commit()
                self.db.refresh(new_rate)
                
                return new_rate
        except Exception as e:
            print(f"Erreur lors de la récupération du taux de change: {e}")
            # Retourner le dernier taux disponible même s'il est ancien
            return self.db.query(ExchangeRate).filter(
                and_(
                    ExchangeRate.from_currency == from_currency,
                    ExchangeRate.to_currency == to_currency
                )
            ).order_by(ExchangeRate.updated_at.desc()).first()
        
        return None
    
    def _fetch_from_api(self, from_currency: str, to_currency: str) -> Optional[ExchangeRate]:
        """
        Récupère le taux de change depuis l'API externe
        """
        try:
            url = f"{self.base_url}/{from_currency}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            rate_value = data.get('rates', {}).get(to_currency)
            
            if rate_value is None:
                print(f"Taux de change {from_currency}/{to_currency} non trouvé dans la réponse API")
                return None
            
            rate = Decimal(str(rate_value))
            inverse_rate = Decimal('1.000000') / rate if rate != 0 else Decimal('0.000000')
            
            return ExchangeRate(
                from_currency=from_currency,
                to_currency=to_currency,
                pair=f"{from_currency}/{to_currency}",
                rate=rate,
                inverse_rate=inverse_rate,
                source="api",
                is_active=True,
                last_fetched_at=datetime.utcnow()
            )
            
        except requests.RequestException as e:
            print(f"Erreur API pour {from_currency}/{to_currency}: {e}")
            return None
        except Exception as e:
            print(f"Erreur lors du traitement de la réponse API: {e}")
            return None
    
    def convert_amount(
        self, 
        amount: Decimal, 
        from_currency: str, 
        to_currency: str,
        force_refresh: bool = False
    ) -> Optional[Decimal]:
        """
        Convertit un montant d'une devise à une autre
        
        Args:
            amount: Montant à convertir
            from_currency: Devise source
            to_currency: Devise cible
            force_refresh: Force la mise à jour du taux
            
        Returns:
            Montant converti ou None si erreur
        """
        if from_currency.upper() == to_currency.upper():
            return amount
        
        rate = self.get_exchange_rate(from_currency, to_currency, force_refresh)
        if not rate:
            return None
        
        return amount * rate.rate
    
    def get_portfolio_currency_rates(self, currencies: List[str]) -> Dict[str, ExchangeRate]:
        """
        Récupère les taux de change pour toutes les devises d'un portefeuille
        
        Args:
            currencies: Liste des devises du portefeuille
            
        Returns:
            Dictionnaire {currency: ExchangeRate}
        """
        rates = {}
        for currency in currencies:
            rate = self.get_exchange_rate(currency, "USD")  # Convertir vers USD comme référence
            if rate:
                rates[currency] = rate
        return rates
    
    def update_all_rates(self, base_currency: str = "USD") -> int:
        """
        Met à jour tous les taux de change depuis l'API
        
        Args:
            base_currency: Devise de base pour les conversions
            
        Returns:
            Nombre de taux mis à jour
        """
        # Devises courantes à mettre à jour
        currencies = ["EUR", "USD", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]
        
        updated_count = 0
        for currency in currencies:
            if currency != base_currency:
                rate = self._fetch_from_api(base_currency, currency)
                if rate:
                    # Désactiver les anciens taux
                    self.db.query(ExchangeRate).filter(
                        and_(
                            ExchangeRate.from_currency == base_currency,
                            ExchangeRate.to_currency == currency
                        )
                    ).update({"is_active": False})
                    
                    # Ajouter le nouveau taux
                    self.db.add(rate)
                    updated_count += 1
        
        self.db.commit()
        return updated_count
    
    def get_supported_currencies(self) -> List[str]:
        """
        Retourne la liste des devises supportées
        """
        return ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", "SEK", "NOK", "DKK"]
    
    def get_rate_history(
        self, 
        from_currency: str, 
        to_currency: str, 
        days: int = 30
    ) -> List[ExchangeRate]:
        """
        Récupère l'historique des taux de change
        
        Args:
            from_currency: Devise source
            to_currency: Devise cible
            days: Nombre de jours d'historique
            
        Returns:
            Liste des taux de change historiques
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return self.db.query(ExchangeRate).filter(
            and_(
                ExchangeRate.from_currency == from_currency,
                ExchangeRate.to_currency == to_currency,
                ExchangeRate.updated_at >= cutoff_date
            )
        ).order_by(ExchangeRate.updated_at.desc()).all()
