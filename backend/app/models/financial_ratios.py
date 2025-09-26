"""
Modèle SQLAlchemy pour les ratios financiers
"""
from sqlalchemy import Column, String, Numeric, Date, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class FinancialRatios(Base):
    """Modèle pour stocker les ratios financiers des entreprises"""
    
    __tablename__ = 'financial_ratios'
    
    # Identifiants
    id = Column(String, primary_key=True)  # symbol + date
    symbol = Column(String(10), nullable=False, index=True)
    
    # Informations générales
    name = Column(String(255))
    description = Column(Text)
    sector = Column(String(100))
    industry = Column(String(100))
    
    # Ratios de valorisation
    market_capitalization = Column(Numeric(20, 2))
    pe_ratio = Column(Numeric(10, 4))
    peg_ratio = Column(Numeric(10, 4))
    price_to_sales_ratio_ttm = Column(Numeric(10, 4))
    price_to_book_ratio = Column(Numeric(10, 4))
    ev_to_revenue = Column(Numeric(10, 4))
    ev_to_ebitda = Column(Numeric(10, 4))
    trailing_pe = Column(Numeric(10, 4))
    forward_pe = Column(Numeric(10, 4))
    
    # Ratios de rentabilité
    profit_margin = Column(Numeric(10, 4))
    operating_margin_ttm = Column(Numeric(10, 4))
    return_on_assets_ttm = Column(Numeric(10, 4))
    return_on_equity_ttm = Column(Numeric(10, 4))
    
    # Ratios de croissance
    quarterly_earnings_growth_yoy = Column(Numeric(10, 4))
    quarterly_revenue_growth_yoy = Column(Numeric(10, 4))
    
    # Ratios de dividende
    dividend_per_share = Column(Numeric(10, 4))
    dividend_yield = Column(Numeric(10, 4))
    dividend_date = Column(Date)
    ex_dividend_date = Column(Date)
    
    # Ratios de risque
    beta = Column(Numeric(10, 4))
    
    # Valeurs de marché
    book_value = Column(Numeric(10, 4))
    eps = Column(Numeric(10, 4))
    diluted_eps_ttm = Column(Numeric(10, 4))
    revenue_per_share_ttm = Column(Numeric(10, 4))
    analyst_target_price = Column(Numeric(10, 4))
    
    # Données financières
    ebitda = Column(Numeric(20, 2))
    revenue_ttm = Column(Numeric(20, 2))
    gross_profit_ttm = Column(Numeric(20, 2))
    shares_outstanding = Column(Numeric(20, 0))
    
    # Prix et moyennes mobiles
    fifty_two_week_high = Column(Numeric(10, 4))
    fifty_two_week_low = Column(Numeric(10, 4))
    fifty_day_moving_average = Column(Numeric(10, 4))
    two_hundred_day_moving_average = Column(Numeric(10, 4))
    
    # Compte de résultat
    fiscal_date_ending = Column(Date)
    total_revenue = Column(Numeric(20, 2))
    cost_of_revenue = Column(Numeric(20, 2))
    gross_profit = Column(Numeric(20, 2))
    operating_income = Column(Numeric(20, 2))
    ebit = Column(Numeric(20, 2))
    net_income = Column(Numeric(20, 2))
    research_and_development = Column(Numeric(20, 2))
    selling_general_administrative = Column(Numeric(20, 2))
    interest_expense = Column(Numeric(20, 2))
    income_before_tax = Column(Numeric(20, 2))
    income_tax_expense = Column(Numeric(20, 2))
    
    # Bilan
    total_assets = Column(Numeric(20, 2))
    total_current_assets = Column(Numeric(20, 2))
    cash_and_cash_equivalents = Column(Numeric(20, 2))
    cash_and_short_term_investments = Column(Numeric(20, 2))
    inventory = Column(Numeric(20, 2))
    current_net_receivables = Column(Numeric(20, 2))
    total_liabilities = Column(Numeric(20, 2))
    total_current_liabilities = Column(Numeric(20, 2))
    current_accounts_payable = Column(Numeric(20, 2))
    deferred_revenue = Column(Numeric(20, 2))
    current_debt = Column(Numeric(20, 2))
    short_term_debt = Column(Numeric(20, 2))
    total_shareholder_equity = Column(Numeric(20, 2))
    treasury_stock = Column(Numeric(20, 2))
    retained_earnings = Column(Numeric(20, 2))
    common_stock = Column(Numeric(20, 2))
    
    # Flux de trésorerie
    operating_cashflow = Column(Numeric(20, 2))
    payments_for_operating_activities = Column(Numeric(20, 2))
    proceeds_from_operating_activities = Column(Numeric(20, 2))
    change_in_operating_liabilities = Column(Numeric(20, 2))
    change_in_operating_assets = Column(Numeric(20, 2))
    depreciation_depletion_and_amortization = Column(Numeric(20, 2))
    capital_expenditures = Column(Numeric(20, 2))
    change_in_receivables = Column(Numeric(20, 2))
    change_in_inventory = Column(Numeric(20, 2))
    profit_loss = Column(Numeric(20, 2))
    cashflow_from_investment = Column(Numeric(20, 2))
    cashflow_from_financing = Column(Numeric(20, 2))
    proceeds_from_repayments_of_short_term_debt = Column(Numeric(20, 2))
    payments_for_repurchase_of_common_stock = Column(Numeric(20, 2))
    payments_for_repurchase_of_equity = Column(Numeric(20, 2))
    payments_for_repurchase_of_preferred_stock = Column(Numeric(20, 2))
    dividend_payout = Column(Numeric(20, 2))
    dividend_payout_common_stock = Column(Numeric(20, 2))
    dividend_payout_preferred_stock = Column(Numeric(20, 2))
    proceeds_from_issuance_of_common_stock = Column(Numeric(20, 2))
    proceeds_from_issuance_of_long_term_debt_and_capital_securities_net = Column(Numeric(20, 2))
    proceeds_from_issuance_of_preferred_stock = Column(Numeric(20, 2))
    proceeds_from_repurchase_of_equity = Column(Numeric(20, 2))
    proceeds_from_sale_of_treasury_stock = Column(Numeric(20, 2))
    change_in_cash_and_cash_equivalents = Column(Numeric(20, 2))
    change_in_exchange_rate = Column(Numeric(20, 2))
    
    # Métadonnées
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<FinancialRatios(symbol='{self.symbol}', name='{self.name}')>"
