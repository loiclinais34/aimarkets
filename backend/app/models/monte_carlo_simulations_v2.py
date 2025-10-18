from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

Base = declarative_base()

class MonteCarloSimulationsV2(Base):
    __tablename__ = 'monte_carlo_simulations_v2'
    
    id = Column(Integer, primary_key=True, index=True)
    simulation_name = Column(String(100), nullable=False, index=True)
    symbol = Column(String(10), nullable=False)  # Added symbol column
    
    # Simulation parameters
    simulation_parameters = Column(JSONB)  # Changed from parameters to simulation_parameters
    num_simulations = Column(Integer, nullable=False)  # Changed from iterations to num_simulations
    simulation_horizon = Column(Integer, nullable=False)  # Added simulation_horizon
    
    # Results
    results = Column(JSONB)
    statistics = Column(JSONB)
    
    # Performance metrics
    avg_return = Column(Numeric(8,4))  # Changed from average_performance to avg_return
    std_return = Column(Numeric(8,4))  # Changed from performance_std to std_return
    sharpe_ratio = Column(Numeric(8,4))  # Added sharpe_ratio
    max_drawdown = Column(Numeric(8,4))  # Added max_drawdown
    
    # Risk metrics
    var_95 = Column(Numeric(8,4))
    cvar_95 = Column(Numeric(8,4))  # Removed var_99 and cvar_99
    
    # Status
    status = Column(String(20), default='COMPLETED')  # Changed default to COMPLETED
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
