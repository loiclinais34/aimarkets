"""
Modèle pour stocker les ratios financiers des entreprises
Source: Yahoo Finance via yfinance
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Date, JSON, Index, DECIMAL, BIGINT
from sqlalchemy.sql import func
from app.core.database import Base


class FinancialRatios(Base):
    """
    Modèle pour stocker les ratios financiers fondamentaux
    """
    __tablename__ = "financial_ratios"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    retrieved_date = Column(Date, nullable=False, index=True)  # Date de récupération
    
    # Informations de l'entreprise
    company_name = Column(String(200), nullable=True)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    
    # Ratios de valorisation
    pe_ratio = Column(DECIMAL(10, 2), nullable=True)  # P/E trailing
    forward_pe = Column(DECIMAL(10, 2), nullable=True)  # P/E forward
    ps_ratio = Column(DECIMAL(10, 2), nullable=True)  # Price to Sales
    pb_ratio = Column(DECIMAL(10, 2), nullable=True)  # Price to Book
    peg_ratio = Column(DECIMAL(10, 2), nullable=True)  # PEG ratio
    
    # Ratios de rentabilité
    profit_margin = Column(DECIMAL(10, 6), nullable=True)
    operating_margin = Column(DECIMAL(10, 6), nullable=True)
    roe = Column(DECIMAL(10, 6), nullable=True)  # Return on Equity
    roa = Column(DECIMAL(10, 6), nullable=True)  # Return on Assets
    
    # Ratios de liquidité
    current_ratio = Column(DECIMAL(10, 4), nullable=True)
    quick_ratio = Column(DECIMAL(10, 4), nullable=True)
    
    # Ratios d'endettement
    debt_to_equity = Column(DECIMAL(10, 4), nullable=True)
    
    # Métriques de marché
    market_cap = Column(BIGINT, nullable=True)
    enterprise_value = Column(BIGINT, nullable=True)
    
    # Métriques par action
    eps = Column(DECIMAL(10, 4), nullable=True)  # Earnings Per Share
    dividend_yield = Column(DECIMAL(10, 6), nullable=True)
    
    # Données brutes complètes (JSON)
    raw_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Index pour requêtes fréquentes
    __table_args__ = (
        Index('idx_financial_symbol_date', 'symbol', 'retrieved_date'),
        Index('idx_financial_pe', 'pe_ratio'),
        Index('idx_financial_sector', 'sector'),
        Index('idx_financial_date', 'retrieved_date'),
    )
    
    def __repr__(self):
        return f"<FinancialRatios(symbol={self.symbol}, date={self.retrieved_date}, PE={self.pe_ratio}, PS={self.ps_ratio}, PB={self.pb_ratio})>"