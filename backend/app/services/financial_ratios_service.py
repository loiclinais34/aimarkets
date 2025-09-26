"""
Service pour récupérer les ratios financiers depuis Alpha Vantage
"""
import requests
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from decimal import Decimal
import time
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from ..models.database import FinancialRatios
from ..core.config import settings

logger = logging.getLogger(__name__)

class FinancialRatiosService:
    """Service pour interagir avec l'API Alpha Vantage pour les ratios financiers"""
    
    def __init__(self):
        self.api_key = settings.alpha_vantage_api_key
        self.base_url = settings.alpha_vantage_base_url
        self.rate_limit_delay = settings.alpha_vantage_rate_limit_delay
        
    def _make_request(self, function: str, symbol: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Effectue une requête vers l'API Alpha Vantage avec gestion des erreurs"""
        if params is None:
            params = {}
            
        # Paramètres de base
        base_params = {
            'function': function,
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        # Fusionner avec les paramètres spécifiques
        params.update(base_params)
        
        try:
            logger.info(f"Requête Alpha Vantage: {function} pour {symbol}")
            
            # Respecter les limites de taux
            time.sleep(self.rate_limit_delay)
            
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Vérifier les erreurs de l'API
            if 'Error Message' in data:
                logger.error(f"Erreur Alpha Vantage: {data['Error Message']}")
                return {}
                
            if 'Note' in data:
                logger.warning(f"Note Alpha Vantage: {data['Note']}")
                return {}
                
            if 'Information' in data:
                logger.warning(f"Information Alpha Vantage: {data['Information']}")
                return {}
            
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête Alpha Vantage: {e}")
            return {}
        except Exception as e:
            logger.error(f"Erreur inattendue Alpha Vantage: {e}")
            return {}
    
    def get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """
        Récupère les informations générales de l'entreprise et les ratios de base
        
        Args:
            symbol: Symbole du titre (ex: AAPL)
            
        Returns:
            Dictionnaire avec les informations de l'entreprise
        """
        data = self._make_request('OVERVIEW', symbol)
        
        if not data:
            return {}
            
        # Extraire les ratios financiers principaux
        overview = {
            'symbol': symbol,
            'name': data.get('Name', ''),
            'description': data.get('Description', ''),
            'sector': data.get('Sector', ''),
            'industry': data.get('Industry', ''),
            'market_capitalization': self._safe_decimal(data.get('MarketCapitalization')),
            'ebitda': self._safe_decimal(data.get('EBITDA')),
            'pe_ratio': self._safe_decimal(data.get('PERatio')),
            'peg_ratio': self._safe_decimal(data.get('PEGRatio')),
            'book_value': self._safe_decimal(data.get('BookValue')),
            'dividend_per_share': self._safe_decimal(data.get('DividendPerShare')),
            'dividend_yield': self._safe_decimal(data.get('DividendYield')),
            'eps': self._safe_decimal(data.get('EPS')),
            'revenue_per_share_ttm': self._safe_decimal(data.get('RevenuePerShareTTM')),
            'profit_margin': self._safe_decimal(data.get('ProfitMargin')),
            'operating_margin_ttm': self._safe_decimal(data.get('OperatingMarginTTM')),
            'return_on_assets_ttm': self._safe_decimal(data.get('ReturnOnAssetsTTM')),
            'return_on_equity_ttm': self._safe_decimal(data.get('ReturnOnEquityTTM')),
            'revenue_ttm': self._safe_decimal(data.get('RevenueTTM')),
            'gross_profit_ttm': self._safe_decimal(data.get('GrossProfitTTM')),
            'diluted_eps_ttm': self._safe_decimal(data.get('DilutedEPSTTM')),
            'quarterly_earnings_growth_yoy': self._safe_decimal(data.get('QuarterlyEarningsGrowthYOY')),
            'quarterly_revenue_growth_yoy': self._safe_decimal(data.get('QuarterlyRevenueGrowthYOY')),
            'analyst_target_price': self._safe_decimal(data.get('AnalystTargetPrice')),
            'trailing_pe': self._safe_decimal(data.get('TrailingPE')),
            'forward_pe': self._safe_decimal(data.get('ForwardPE')),
            'price_to_sales_ratio_ttm': self._safe_decimal(data.get('PriceToSalesRatioTTM')),
            'price_to_book_ratio': self._safe_decimal(data.get('PriceToBookRatio')),
            'ev_to_revenue': self._safe_decimal(data.get('EVToRevenue')),
            'ev_to_ebitda': self._safe_decimal(data.get('EVToEBITDA')),
            'beta': self._safe_decimal(data.get('Beta')),
            'fifty_two_week_high': self._safe_decimal(data.get('52WeekHigh')),
            'fifty_two_week_low': self._safe_decimal(data.get('52WeekLow')),
            'fifty_day_moving_average': self._safe_decimal(data.get('50DayMovingAverage')),
            'two_hundred_day_moving_average': self._safe_decimal(data.get('200DayMovingAverage')),
            'shares_outstanding': self._safe_decimal(data.get('SharesOutstanding')),
            'dividend_date': self._safe_date(data.get('DividendDate')),
            'ex_dividend_date': self._safe_date(data.get('ExDividendDate')),
            'last_updated': datetime.now()
        }
        
        return overview
    
    def get_income_statement(self, symbol: str) -> Dict[str, Any]:
        """
        Récupère le compte de résultat
        
        Args:
            symbol: Symbole du titre (ex: AAPL)
            
        Returns:
            Dictionnaire avec les données du compte de résultat
        """
        data = self._make_request('INCOME_STATEMENT', symbol)
        
        if not data or 'annualReports' not in data:
            return {}
            
        # Prendre le rapport annuel le plus récent
        latest_report = data['annualReports'][0] if data['annualReports'] else {}
        
        income_statement = {
            'symbol': symbol,
            'fiscal_date_ending': self._safe_date(latest_report.get('fiscalDateEnding')),
            'total_revenue': self._safe_decimal(latest_report.get('totalRevenue')),
            'cost_of_revenue': self._safe_decimal(latest_report.get('costOfRevenue')),
            'gross_profit': self._safe_decimal(latest_report.get('grossProfit')),
            'operating_income': self._safe_decimal(latest_report.get('operatingIncome')),
            'ebit': self._safe_decimal(latest_report.get('ebit')),
            'ebitda': self._safe_decimal(latest_report.get('ebitda')),
            'net_income': self._safe_decimal(latest_report.get('netIncome')),
            'research_and_development': self._safe_decimal(latest_report.get('researchAndDevelopment')),
            'selling_general_administrative': self._safe_decimal(latest_report.get('sellingGeneralAdministrative')),
            'interest_expense': self._safe_decimal(latest_report.get('interestExpense')),
            'income_before_tax': self._safe_decimal(latest_report.get('incomeBeforeTax')),
            'income_tax_expense': self._safe_decimal(latest_report.get('incomeTaxExpense')),
            'last_updated': datetime.now()
        }
        
        return income_statement
    
    def get_balance_sheet(self, symbol: str) -> Dict[str, Any]:
        """
        Récupère le bilan
        
        Args:
            symbol: Symbole du titre (ex: AAPL)
            
        Returns:
            Dictionnaire avec les données du bilan
        """
        data = self._make_request('BALANCE_SHEET', symbol)
        
        if not data or 'annualReports' not in data:
            return {}
            
        # Prendre le rapport annuel le plus récent
        latest_report = data['annualReports'][0] if data['annualReports'] else {}
        
        balance_sheet = {
            'symbol': symbol,
            'fiscal_date_ending': self._safe_date(latest_report.get('fiscalDateEnding')),
            'total_assets': self._safe_decimal(latest_report.get('totalAssets')),
            'total_current_assets': self._safe_decimal(latest_report.get('totalCurrentAssets')),
            'cash_and_cash_equivalents': self._safe_decimal(latest_report.get('cashAndCashEquivalentsAtCarryingValue')),
            'cash_and_short_term_investments': self._safe_decimal(latest_report.get('cashAndShortTermInvestments')),
            'inventory': self._safe_decimal(latest_report.get('inventory')),
            'current_net_receivables': self._safe_decimal(latest_report.get('currentNetReceivables')),
            'total_liabilities': self._safe_decimal(latest_report.get('totalLiabilities')),
            'total_current_liabilities': self._safe_decimal(latest_report.get('totalCurrentLiabilities')),
            'current_accounts_payable': self._safe_decimal(latest_report.get('currentAccountsPayable')),
            'deferred_revenue': self._safe_decimal(latest_report.get('deferredRevenue')),
            'current_debt': self._safe_decimal(latest_report.get('currentDebt')),
            'short_term_debt': self._safe_decimal(latest_report.get('shortTermDebt')),
            'total_shareholder_equity': self._safe_decimal(latest_report.get('totalShareholderEquity')),
            'treasury_stock': self._safe_decimal(latest_report.get('treasuryStock')),
            'retained_earnings': self._safe_decimal(latest_report.get('retainedEarnings')),
            'common_stock': self._safe_decimal(latest_report.get('commonStock')),
            'last_updated': datetime.now()
        }
        
        return balance_sheet
    
    def get_cash_flow(self, symbol: str) -> Dict[str, Any]:
        """
        Récupère le tableau des flux de trésorerie
        
        Args:
            symbol: Symbole du titre (ex: AAPL)
            
        Returns:
            Dictionnaire avec les données des flux de trésorerie
        """
        data = self._make_request('CASH_FLOW', symbol)
        
        if not data or 'annualReports' not in data:
            return {}
            
        # Prendre le rapport annuel le plus récent
        latest_report = data['annualReports'][0] if data['annualReports'] else {}
        
        cash_flow = {
            'symbol': symbol,
            'fiscal_date_ending': self._safe_date(latest_report.get('fiscalDateEnding')),
            'operating_cashflow': self._safe_decimal(latest_report.get('operatingCashflow')),
            'payments_for_operating_activities': self._safe_decimal(latest_report.get('paymentsForOperatingActivities')),
            'proceeds_from_operating_activities': self._safe_decimal(latest_report.get('proceedsFromOperatingActivities')),
            'change_in_operating_liabilities': self._safe_decimal(latest_report.get('changeInOperatingLiabilities')),
            'change_in_operating_assets': self._safe_decimal(latest_report.get('changeInOperatingAssets')),
            'depreciation_depletion_and_amortization': self._safe_decimal(latest_report.get('depreciationDepletionAndAmortization')),
            'capital_expenditures': self._safe_decimal(latest_report.get('capitalExpenditures')),
            'change_in_receivables': self._safe_decimal(latest_report.get('changeInReceivables')),
            'change_in_inventory': self._safe_decimal(latest_report.get('changeInInventory')),
            'profit_loss': self._safe_decimal(latest_report.get('profitLoss')),
            'cashflow_from_investment': self._safe_decimal(latest_report.get('cashflowFromInvestment')),
            'cashflow_from_financing': self._safe_decimal(latest_report.get('cashflowFromFinancing')),
            'proceeds_from_repayments_of_short_term_debt': self._safe_decimal(latest_report.get('proceedsFromRepaymentsOfShortTermDebt')),
            'payments_for_repurchase_of_common_stock': self._safe_decimal(latest_report.get('paymentsForRepurchaseOfCommonStock')),
            'payments_for_repurchase_of_equity': self._safe_decimal(latest_report.get('paymentsForRepurchaseOfEquity')),
            'payments_for_repurchase_of_preferred_stock': self._safe_decimal(latest_report.get('paymentsForRepurchaseOfPreferredStock')),
            'dividend_payout': self._safe_decimal(latest_report.get('dividendPayout')),
            'dividend_payout_common_stock': self._safe_decimal(latest_report.get('dividendPayoutCommonStock')),
            'dividend_payout_preferred_stock': self._safe_decimal(latest_report.get('dividendPayoutPreferredStock')),
            'proceeds_from_issuance_of_common_stock': self._safe_decimal(latest_report.get('proceedsFromIssuanceOfCommonStock')),
            'proceeds_from_issuance_of_long_term_debt_and_capital_securities_net': self._safe_decimal(latest_report.get('proceedsFromIssuanceOfLongTermDebtAndCapitalSecuritiesNet')),
            'proceeds_from_issuance_of_preferred_stock': self._safe_decimal(latest_report.get('proceedsFromIssuanceOfPreferredStock')),
            'proceeds_from_repurchase_of_equity': self._safe_decimal(latest_report.get('proceedsFromRepurchaseOfEquity')),
            'proceeds_from_sale_of_treasury_stock': self._safe_decimal(latest_report.get('proceedsFromSaleOfTreasuryStock')),
            'change_in_cash_and_cash_equivalents': self._safe_decimal(latest_report.get('changeInCashAndCashEquivalents')),
            'change_in_exchange_rate': self._safe_decimal(latest_report.get('changeInExchangeRate')),
            'net_income': self._safe_decimal(latest_report.get('netIncome')),
            'last_updated': datetime.now()
        }
        
        return cash_flow
    
    def save_financial_ratios(self, db: Session, symbol: str) -> bool:
        """
        Récupère et sauvegarde tous les ratios financiers pour un symbole
        
        Args:
            db: Session de base de données
            symbol: Symbole du titre
            
        Returns:
            True si succès, False sinon
        """
        try:
            logger.info(f"Récupération des ratios financiers pour {symbol}")
            
            # Récupérer les données
            overview = self.get_company_overview(symbol)
            income_statement = self.get_income_statement(symbol)
            balance_sheet = self.get_balance_sheet(symbol)
            cash_flow = self.get_cash_flow(symbol)
            
            if not overview:
                logger.warning(f"Aucune donnée trouvée pour {symbol}")
                return False
            
            # Vérifier si l'enregistrement existe déjà
            existing_record = db.query(FinancialRatios).filter(
                FinancialRatios.symbol == symbol
            ).first()
            
            if existing_record:
                # Mettre à jour l'enregistrement existant
                for key, value in overview.items():
                    if hasattr(existing_record, key):
                        setattr(existing_record, key, value)
                
                # Ajouter les données des états financiers
                for key, value in income_statement.items():
                    if hasattr(existing_record, key) and key != 'symbol':
                        setattr(existing_record, key, value)
                
                for key, value in balance_sheet.items():
                    if hasattr(existing_record, key) and key != 'symbol':
                        setattr(existing_record, key, value)
                
                for key, value in cash_flow.items():
                    if hasattr(existing_record, key) and key != 'symbol':
                        setattr(existing_record, key, value)
                
                existing_record.last_updated = datetime.now()
                
            else:
                # Créer un nouvel enregistrement
                # Combiner toutes les données en excluant les clés 'symbol' en double
                all_data = {}
                all_data.update(overview)
                all_data.update({k: v for k, v in income_statement.items() if k != 'symbol'})
                all_data.update({k: v for k, v in balance_sheet.items() if k != 'symbol'})
                all_data.update({k: v for k, v in cash_flow.items() if k != 'symbol'})
                
                # S'assurer que symbol est défini
                all_data['symbol'] = symbol
                
                # Générer un ID unique
                all_data['id'] = f"{symbol}_{datetime.now().strftime('%Y%m%d')}"
                
                financial_ratios = FinancialRatios(**all_data)
                db.add(financial_ratios)
            
            db.commit()
            logger.info(f"Ratios financiers sauvegardés pour {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde des ratios financiers pour {symbol}: {e}")
            db.rollback()
            return False
    
    def _safe_decimal(self, value: Any) -> Optional[Decimal]:
        """Convertit une valeur en Decimal de manière sécurisée"""
        if value is None or value == 'None' or value == '':
            return None
        try:
            return Decimal(str(value))
        except (ValueError, TypeError):
            return None
    
    def _safe_date(self, value: Any) -> Optional[date]:
        """Convertit une valeur en date de manière sécurisée"""
        if value is None or value == 'None' or value == '':
            return None
        try:
            if isinstance(value, str):
                return datetime.strptime(value, '%Y-%m-%d').date()
            return value
        except (ValueError, TypeError):
            return None
