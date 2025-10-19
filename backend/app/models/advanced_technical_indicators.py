from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Index, Boolean, Numeric, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

Base = declarative_base()

class AdvancedTechnicalIndicators(Base):
    __tablename__ = 'advanced_technical_indicators'
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    
    # Price-based indicators
    sma_5 = Column(Numeric(10,4))
    sma_10 = Column(Numeric(10,4))
    sma_20 = Column(Numeric(10,4))
    sma_50 = Column(Numeric(10,4))
    sma_200 = Column(Numeric(10,4))
    
    ema_5 = Column(Numeric(10,4))
    ema_10 = Column(Numeric(10,4))
    ema_20 = Column(Numeric(10,4))
    ema_50 = Column(Numeric(10,4))
    ema_200 = Column(Numeric(10,4))
    
    # Momentum indicators
    rsi_14 = Column(Numeric(5,2))
    rsi_21 = Column(Numeric(5,2))
    macd = Column(Numeric(10,4))
    macd_signal = Column(Numeric(10,4))
    macd_hist = Column(Numeric(10,4))
    
    # Volatility indicators
    bb_upper = Column(Numeric(10,4))
    bb_middle = Column(Numeric(10,4))
    bb_lower = Column(Numeric(10,4))
    bb_width = Column(Numeric(8,4))
    bb_percent = Column(Numeric(8,4))
    bb_position = Column(Numeric(8,4))
    bb_squeeze = Column(Numeric(8,4))
    
    atr_14 = Column(Numeric(10,4))
    atr_20 = Column(Numeric(10,4))
    
    # Volume indicators
    obv = Column(Numeric(15,2))
    
    # Additional indicators
    stoch_k = Column(Numeric(5,2))
    stoch_d = Column(Numeric(5,2))
    stochf_k = Column(Numeric(5,2))
    stochf_d = Column(Numeric(5,2))
    stochrsi_k = Column(Numeric(5,2))
    stochrsi_d = Column(Numeric(5,2))
    willr_14 = Column(Numeric(5,2))
    cci_14 = Column(Numeric(8,2))
    roc_10 = Column(Numeric(8,2))
    roc_20 = Column(Numeric(8,2))
    rocp_10 = Column(Numeric(8,2))
    rocr_10 = Column(Numeric(8,2))
    rocr100_10 = Column(Numeric(8,2))
    
    # Advanced indicators
    adx_14 = Column(Numeric(5,2))
    adxr_14 = Column(Numeric(5,2))
    plus_di = Column(Numeric(5,2))
    minus_di = Column(Numeric(5,2))
    dx_14 = Column(Numeric(5,2))
    sar = Column(Numeric(10,4))
    mfi_14 = Column(Numeric(5,2))
    midpoint_20 = Column(Numeric(10,4))
    midprice_20 = Column(Numeric(10,4))
    obv_price_divergence = Column(Numeric(10,4))
    t3_20 = Column(Numeric(10,4))
    vpt = Column(Numeric(15,2))
    wad = Column(Numeric(15,2))
    momentum_composite = Column(Numeric(8,4))
    volatility_composite = Column(Numeric(8,4))
    trend_strength = Column(Numeric(8,4))
    
    # Candlestick patterns
    cdl_doji = Column(Boolean, default=False)
    cdl_hammer = Column(Boolean, default=False)
    cdl_shootingstar = Column(Boolean, default=False)
    cdl_engulfing = Column(Boolean, default=False)
    cdl_darkcloudcover = Column(Boolean, default=False)
    cdl_eveningstar = Column(Boolean, default=False)
    cdl_hangingman = Column(Boolean, default=False)
    cdl_marubozu = Column(Boolean, default=False)
    cdl_morningstar = Column(Boolean, default=False)
    cdl_piercing = Column(Boolean, default=False)
    cdl_spinningtop = Column(Boolean, default=False)
    
    # Additional technical indicators
    ad = Column(Numeric(15,2))
    adosc = Column(Numeric(15,2))
    aroon_down = Column(Numeric(5,2))
    aroon_up = Column(Numeric(5,2))
    aroonosc = Column(Numeric(5,2))
    avgprice = Column(Numeric(10,4))
    beta_20 = Column(Numeric(8,4))
    bop = Column(Numeric(8,4))
    cmo_14 = Column(Numeric(5,2))
    correl_20 = Column(Numeric(8,4))
    dema_20 = Column(Numeric(10,4))
    fama = Column(Numeric(10,4))
    ht_dcperiod = Column(Numeric(8,4))
    ht_dcphase = Column(Numeric(8,4))
    ht_leadsine = Column(Numeric(8,4))
    ht_phasor_inphase = Column(Numeric(8,4))
    ht_phasor_quadrature = Column(Numeric(8,4))
    ht_sine = Column(Numeric(8,4))
    ht_trendmode = Column(Numeric(8,4))
    kama_20 = Column(Numeric(10,4))
    kama_50 = Column(Numeric(10,4))
    linearreg = Column(Numeric(10,4))
    linearreg_angle = Column(Numeric(8,4))
    linearreg_intercept = Column(Numeric(10,4))
    linearreg_slope = Column(Numeric(8,4))
    mama = Column(Numeric(10,4))
    medprice = Column(Numeric(10,4))
    mom_10 = Column(Numeric(8,4))
    mom_20 = Column(Numeric(8,4))
    natr_14 = Column(Numeric(8,4))
    sma_100 = Column(Numeric(10,4))
    sma_ratio_20_50 = Column(Numeric(8,4))
    stddev_20 = Column(Numeric(8,4))
    stddev_50 = Column(Numeric(8,4))
    tema_20 = Column(Numeric(10,4))
    trange = Column(Numeric(10,4))
    trima_20 = Column(Numeric(10,4))
    trima_50 = Column(Numeric(10,4))
    tsf_20 = Column(Numeric(10,4))
    typprice = Column(Numeric(10,4))
    ultosc = Column(Numeric(8,4))
    var_20 = Column(Numeric(8,4))
    var_50 = Column(Numeric(8,4))
    wclprice = Column(Numeric(10,4))
    wma_20 = Column(Numeric(10,4))
    wma_50 = Column(Numeric(10,4))
    ema_100 = Column(Numeric(10,4))
    ema_ratio_20_50 = Column(Numeric(8,4))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for better query performance
    __table_args__ = (
        Index('idx_symbol_date', 'symbol', 'date'),
        Index('idx_date_symbol', 'date', 'symbol'),
    )
