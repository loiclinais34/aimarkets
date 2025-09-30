"""
Service pour récupérer les ratios financiers via yfinance
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, date
import yfinance as yf
from sqlalchemy.orm import Session

from app.models.financial_ratios import FinancialRatios

logger = logging.getLogger(__name__)


class FinancialRatiosService:
    """
    Service pour récupérer et gérer les ratios financiers des entreprises
    Source: Yahoo Finance via yfinance
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_financial_ratios(self, symbol: str) -> Dict[str, Any]:
        """
        Récupère les ratios financiers pour un symbole donné
        
        Args:
            symbol: Symbole du titre (ex: AAPL)
            
        Returns:
            Dict contenant les ratios financiers
        """
        try:
            self.logger.info(f"Récupération des ratios financiers pour {symbol}")
            
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extraire les ratios pertinents
            ratios = {
                # Ratios de valorisation
                'pe_ratio': self._safe_float(info.get('trailingPE')),
                'forward_pe': self._safe_float(info.get('forwardPE')),
                'ps_ratio': self._safe_float(info.get('priceToSalesTrailing12Months')),
                'pb_ratio': self._safe_float(info.get('priceToBook')),
                'peg_ratio': self._safe_float(info.get('pegRatio')),
                
                # Ratios de rentabilité
                'profit_margin': self._safe_float(info.get('profitMargins')),
                'operating_margin': self._safe_float(info.get('operatingMargins')),
                'roe': self._safe_float(info.get('returnOnEquity')),
                'roa': self._safe_float(info.get('returnOnAssets')),
                
                # Ratios de liquidité
                'current_ratio': self._safe_float(info.get('currentRatio')),
                'quick_ratio': self._safe_float(info.get('quickRatio')),
                
                # Ratios d'endettement
                'debt_to_equity': self._safe_float(info.get('debtToEquity')),
                
                # Autres métriques
                'market_cap': self._safe_float(info.get('marketCap')),
                'enterprise_value': self._safe_float(info.get('enterpriseValue')),
                'eps': self._safe_float(info.get('trailingEps')),
                'dividend_yield': self._safe_float(info.get('dividendYield')),
                
                # Informations contextuelles
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'company_name': info.get('longName') or info.get('shortName'),
                
                # Métadonnées
                'retrieved_at': datetime.now().isoformat(),
                'symbol': symbol
            }
            
            self.logger.info(f"Ratios récupérés pour {symbol}: P/E={ratios['pe_ratio']}, P/S={ratios['ps_ratio']}, P/B={ratios['pb_ratio']}")
            return ratios
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des ratios pour {symbol}: {e}")
            return {
                'symbol': symbol,
                'error': str(e),
                'retrieved_at': datetime.now().isoformat()
            }
    
    def get_sector_averages(self, symbols: list, sector: str = None) -> Dict[str, float]:
        """
        Calcule les moyennes des ratios pour un secteur
        
        Args:
            symbols: Liste de symboles du secteur
            sector: Nom du secteur (optionnel)
            
        Returns:
            Dict avec les moyennes des ratios
        """
        try:
            all_ratios = []
            
            for symbol in symbols:
                ratios = self.get_financial_ratios(symbol)
                if 'error' not in ratios:
                    all_ratios.append(ratios)
            
            if not all_ratios:
                return {}
            
            # Calculer les moyennes
            averages = {}
            ratio_keys = ['pe_ratio', 'ps_ratio', 'pb_ratio', 'peg_ratio', 'roe', 'roa', 'debt_to_equity']
            
            for key in ratio_keys:
                values = [r[key] for r in all_ratios if r.get(key) is not None]
                if values:
                    averages[f'avg_{key}'] = sum(values) / len(values)
                    averages[f'median_{key}'] = sorted(values)[len(values) // 2]
            
            averages['sample_size'] = len(all_ratios)
            averages['sector'] = sector
            
            return averages
            
        except Exception as e:
            self.logger.error(f"Erreur lors du calcul des moyennes sectorielles: {e}")
            return {}
    
    def compare_to_sector(self, symbol: str, sector_symbols: list) -> Dict[str, Any]:
        """
        Compare les ratios d'un symbole à la moyenne de son secteur
        
        Args:
            symbol: Symbole à comparer
            sector_symbols: Liste des symboles du secteur
            
        Returns:
            Dict avec les comparaisons
        """
        try:
            # Récupérer les ratios du symbole
            symbol_ratios = self.get_financial_ratios(symbol)
            if 'error' in symbol_ratios:
                return symbol_ratios
            
            # Récupérer les moyennes du secteur
            sector_averages = self.get_sector_averages(sector_symbols, symbol_ratios.get('sector'))
            
            # Calculer les écarts
            comparisons = {
                'symbol': symbol,
                'sector': symbol_ratios.get('sector'),
                'ratios': symbol_ratios,
                'sector_averages': sector_averages,
                'deviations': {}
            }
            
            for key in ['pe_ratio', 'ps_ratio', 'pb_ratio']:
                symbol_value = symbol_ratios.get(key)
                sector_avg = sector_averages.get(f'avg_{key}')
                
                if symbol_value is not None and sector_avg is not None and sector_avg > 0:
                    deviation_pct = ((symbol_value - sector_avg) / sector_avg) * 100
                    comparisons['deviations'][key] = {
                        'symbol_value': symbol_value,
                        'sector_average': sector_avg,
                        'deviation_pct': round(deviation_pct, 2)
                    }
            
            return comparisons
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la comparaison sectorielle pour {symbol}: {e}")
            return {'symbol': symbol, 'error': str(e)}
    
    def _safe_float(self, value) -> Optional[float]:
        """Convertit une valeur en float de manière sécurisée"""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def batch_get_ratios(self, symbols: list) -> Dict[str, Dict[str, Any]]:
        """
        Récupère les ratios pour plusieurs symboles en batch
        
        Args:
            symbols: Liste de symboles
            
        Returns:
            Dict {symbol: ratios}
        """
        results = {}
        
        for symbol in symbols:
            self.logger.info(f"Récupération des ratios pour {symbol} ({symbols.index(symbol)+1}/{len(symbols)})")
            results[symbol] = self.get_financial_ratios(symbol)
        
        return results
    
    def save_financial_ratios(self, ratios_data: Dict[str, Any], db: Session) -> Optional[FinancialRatios]:
        """
        Sauvegarde les ratios financiers dans la base de données
        
        Args:
            ratios_data: Dict contenant les ratios
            db: Session de base de données
            
        Returns:
            FinancialRatios object ou None si erreur
        """
        try:
            if 'error' in ratios_data:
                self.logger.warning(f"Impossible de sauvegarder les ratios pour {ratios_data.get('symbol')}: erreur dans les données")
                return None
            
            symbol = ratios_data['symbol']
            retrieved_date = date.today()
            
            # Vérifier si un enregistrement existe déjà pour aujourd'hui
            existing = db.query(FinancialRatios).filter(
                FinancialRatios.symbol == symbol,
                FinancialRatios.retrieved_date == retrieved_date
            ).first()
            
            if existing:
                # Mettre à jour
                existing.company_name = ratios_data.get('company_name')
                existing.sector = ratios_data.get('sector')
                existing.industry = ratios_data.get('industry')
                existing.pe_ratio = ratios_data.get('pe_ratio')
                existing.forward_pe = ratios_data.get('forward_pe')
                existing.ps_ratio = ratios_data.get('ps_ratio')
                existing.pb_ratio = ratios_data.get('pb_ratio')
                existing.peg_ratio = ratios_data.get('peg_ratio')
                existing.profit_margin = ratios_data.get('profit_margin')
                existing.operating_margin = ratios_data.get('operating_margin')
                existing.roe = ratios_data.get('roe')
                existing.roa = ratios_data.get('roa')
                existing.current_ratio = ratios_data.get('current_ratio')
                existing.quick_ratio = ratios_data.get('quick_ratio')
                existing.debt_to_equity = ratios_data.get('debt_to_equity')
                existing.market_cap = ratios_data.get('market_cap')
                existing.enterprise_value = ratios_data.get('enterprise_value')
                existing.eps = ratios_data.get('eps')
                existing.dividend_yield = ratios_data.get('dividend_yield')
                existing.raw_data = ratios_data
                existing.updated_at = datetime.now()
                
                db.commit()
                self.logger.info(f"Ratios financiers mis à jour pour {symbol}")
                return existing
            else:
                # Créer un nouvel enregistrement
                new_ratios = FinancialRatios(
                    symbol=symbol,
                    retrieved_date=retrieved_date,
                    company_name=ratios_data.get('company_name'),
                    sector=ratios_data.get('sector'),
                    industry=ratios_data.get('industry'),
                    pe_ratio=ratios_data.get('pe_ratio'),
                    forward_pe=ratios_data.get('forward_pe'),
                    ps_ratio=ratios_data.get('ps_ratio'),
                    pb_ratio=ratios_data.get('pb_ratio'),
                    peg_ratio=ratios_data.get('peg_ratio'),
                    profit_margin=ratios_data.get('profit_margin'),
                    operating_margin=ratios_data.get('operating_margin'),
                    roe=ratios_data.get('roe'),
                    roa=ratios_data.get('roa'),
                    current_ratio=ratios_data.get('current_ratio'),
                    quick_ratio=ratios_data.get('quick_ratio'),
                    debt_to_equity=ratios_data.get('debt_to_equity'),
                    market_cap=ratios_data.get('market_cap'),
                    enterprise_value=ratios_data.get('enterprise_value'),
                    eps=ratios_data.get('eps'),
                    dividend_yield=ratios_data.get('dividend_yield'),
                    raw_data=ratios_data
                )
                
                db.add(new_ratios)
                db.commit()
                self.logger.info(f"Nouveaux ratios financiers créés pour {symbol}")
                return new_ratios
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la sauvegarde des ratios pour {ratios_data.get('symbol')}: {e}")
            db.rollback()
            return None
    
    def get_cached_ratios(self, symbol: str, db: Session, max_age_days: int = 7) -> Optional[Dict[str, Any]]:
        """
        Récupère les ratios en cache si disponibles et récents
        
        Args:
            symbol: Symbole du titre
            db: Session de base de données
            max_age_days: Âge maximum en jours (défaut 7)
            
        Returns:
            Dict avec les ratios ou None si trop vieux ou inexistant
        """
        try:
            from datetime import timedelta
            
            min_date = date.today() - timedelta(days=max_age_days)
            
            cached = db.query(FinancialRatios).filter(
                FinancialRatios.symbol == symbol,
                FinancialRatios.retrieved_date >= min_date
            ).order_by(FinancialRatios.retrieved_date.desc()).first()
            
            if cached:
                return cached.raw_data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la récupération des ratios en cache pour {symbol}: {e}")
            return None
    
    def get_or_fetch_ratios(self, symbol: str, db: Session, max_age_days: int = 7) -> Dict[str, Any]:
        """
        Récupère les ratios en cache ou les fetch si nécessaire
        
        Args:
            symbol: Symbole du titre
            db: Session de base de données
            max_age_days: Âge maximum en jours
            
        Returns:
            Dict avec les ratios
        """
        # Essayer de récupérer depuis le cache
        cached_ratios = self.get_cached_ratios(symbol, db, max_age_days)
        
        if cached_ratios:
            self.logger.info(f"Ratios trouvés en cache pour {symbol}")
            return cached_ratios
        
        # Sinon, fetch et sauvegarder
        self.logger.info(f"Ratios non trouvés en cache pour {symbol}, récupération depuis yfinance")
        ratios = self.get_financial_ratios(symbol)
        
        if 'error' not in ratios:
            self.save_financial_ratios(ratios, db)
        
        return ratios