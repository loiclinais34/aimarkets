#!/usr/bin/env python3
"""
Script pour calculer et stocker tous les indicateurs techniques TA-Lib
dans la table advanced_technical_indicators
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import logging
from typing import List, Dict, Any, Optional
import warnings
warnings.filterwarnings('ignore')

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Database imports
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Import TA-Lib integration
from talib_indicators import TALibIndicators

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('technical_indicators_calculation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TechnicalIndicatorsCalculator:
    """Calculateur d'indicateurs techniques avec stockage en base de données."""
    
    def __init__(self, db_config: Dict[str, str]):
        self.db_config = db_config
        self.engine = create_engine(
            f"postgresql://{db_config['user']}:{db_config['password']}@"
            f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        self.Session = sessionmaker(bind=self.engine)
        
        # TA-Lib calculator
        self.talib_calculator = TALibIndicators()
        
        logger.info("TechnicalIndicatorsCalculator initialized successfully")
    
    def recreate_table(self):
        """Recrée la table advanced_technical_indicators."""
        logger.info("🗑️ Recreating advanced_technical_indicators table...")
        
        try:
            with self.engine.connect() as conn:
                # Drop existing table
                conn.execute(text("DROP TABLE IF EXISTS advanced_technical_indicators CASCADE"))
                
                # Create new table with comprehensive schema
                create_table_sql = """
                CREATE TABLE advanced_technical_indicators (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(10) NOT NULL,
                    date DATE NOT NULL,
                    
                    -- Price data
                    open DECIMAL(10,4),
                    high DECIMAL(10,4),
                    low DECIMAL(10,4),
                    close DECIMAL(10,4),
                    volume BIGINT,
                    
                    -- Overlap Studies
                    sma_5 DECIMAL(10,4),
                    sma_10 DECIMAL(10,4),
                    sma_20 DECIMAL(10,4),
                    sma_50 DECIMAL(10,4),
                    sma_100 DECIMAL(10,4),
                    sma_200 DECIMAL(10,4),
                    ema_5 DECIMAL(10,4),
                    ema_10 DECIMAL(10,4),
                    ema_20 DECIMAL(10,4),
                    ema_50 DECIMAL(10,4),
                    ema_100 DECIMAL(10,4),
                    ema_200 DECIMAL(10,4),
                    wma_20 DECIMAL(10,4),
                    wma_50 DECIMAL(10,4),
                    trima_20 DECIMAL(10,4),
                    trima_50 DECIMAL(10,4),
                    kama_20 DECIMAL(10,4),
                    kama_50 DECIMAL(10,4),
                    mama DECIMAL(10,4),
                    fama DECIMAL(10,4),
                    bb_upper DECIMAL(10,4),
                    bb_middle DECIMAL(10,4),
                    bb_lower DECIMAL(10,4),
                    bb_width DECIMAL(10,4),
                    bb_percent DECIMAL(10,4),
                    dema_20 DECIMAL(10,4),
                    tema_20 DECIMAL(10,4),
                    midpoint_20 DECIMAL(10,4),
                    midprice_20 DECIMAL(10,4),
                    sar DECIMAL(10,4),
                    t3_20 DECIMAL(10,4),
                    
                    -- Momentum Indicators
                    rsi_14 DECIMAL(10,4),
                    rsi_21 DECIMAL(10,4),
                    stoch_k DECIMAL(10,4),
                    stoch_d DECIMAL(10,4),
                    stochf_k DECIMAL(10,4),
                    stochf_d DECIMAL(10,4),
                    stochrsi_k DECIMAL(10,4),
                    stochrsi_d DECIMAL(10,4),
                    willr_14 DECIMAL(10,4),
                    adx_14 DECIMAL(10,4),
                    adxr_14 DECIMAL(10,4),
                    plus_di DECIMAL(10,4),
                    minus_di DECIMAL(10,4),
                    aroon_up DECIMAL(10,4),
                    aroon_down DECIMAL(10,4),
                    aroonosc DECIMAL(10,4),
                    bop DECIMAL(10,4),
                    cci_14 DECIMAL(10,4),
                    cmo_14 DECIMAL(10,4),
                    dx_14 DECIMAL(10,4),
                    macd DECIMAL(10,4),
                    macd_signal DECIMAL(10,4),
                    macd_hist DECIMAL(10,4),
                    macd_fix DECIMAL(10,4),
                    macd_fix_signal DECIMAL(10,4),
                    macd_fix_hist DECIMAL(10,4),
                    mom_10 DECIMAL(10,4),
                    mom_20 DECIMAL(10,4),
                    roc_10 DECIMAL(10,4),
                    roc_20 DECIMAL(10,4),
                    rocp_10 DECIMAL(10,4),
                    rocr_10 DECIMAL(10,4),
                    rocr100_10 DECIMAL(10,4),
                    ultosc DECIMAL(10,4),
                    
                    -- Volume Indicators
                    ad DECIMAL(15,4),
                    adosc DECIMAL(15,4),
                    obv DECIMAL(15,4),
                    mfi_14 DECIMAL(10,4),
                    vpt DECIMAL(15,4),
                    wad DECIMAL(15,4),
                    
                    -- Volatility Indicators
                    atr_14 DECIMAL(10,4),
                    atr_20 DECIMAL(10,4),
                    trange DECIMAL(10,4),
                    natr_14 DECIMAL(10,4),
                    stddev_20 DECIMAL(10,4),
                    stddev_50 DECIMAL(10,4),
                    var_20 DECIMAL(10,4),
                    var_50 DECIMAL(10,4),
                    
                    -- Price Transform
                    avgprice DECIMAL(10,4),
                    medprice DECIMAL(10,4),
                    typprice DECIMAL(10,4),
                    wclprice DECIMAL(10,4),
                    
                    -- Cycle Indicators
                    ht_dcperiod DECIMAL(10,4),
                    ht_dcphase DECIMAL(10,4),
                    ht_phasor_inphase DECIMAL(10,4),
                    ht_phasor_quadrature DECIMAL(10,4),
                    ht_sine DECIMAL(10,4),
                    ht_leadsine DECIMAL(10,4),
                    ht_trendmode DECIMAL(10,4),
                    
                    -- Pattern Recognition (subset of most important)
                    cdl_doji INTEGER,
                    cdl_hammer INTEGER,
                    cdl_hangingman INTEGER,
                    cdl_engulfing INTEGER,
                    cdl_morningstar INTEGER,
                    cdl_eveningstar INTEGER,
                    cdl_piercing INTEGER,
                    cdl_darkcloudcover INTEGER,
                    cdl_shootingstar INTEGER,
                    cdl_marubozu INTEGER,
                    cdl_spinningtop INTEGER,
                    
                    -- Statistical Functions
                    beta_20 DECIMAL(10,4),
                    correl_20 DECIMAL(10,4),
                    linearreg DECIMAL(10,4),
                    linearreg_angle DECIMAL(10,4),
                    linearreg_intercept DECIMAL(10,4),
                    linearreg_slope DECIMAL(10,4),
                    tsf_20 DECIMAL(10,4),
                    
                    -- Custom Features
                    sma_ratio_20_50 DECIMAL(10,4),
                    ema_ratio_20_50 DECIMAL(10,4),
                    bb_position DECIMAL(10,4),
                    bb_squeeze DECIMAL(10,4),
                    momentum_composite DECIMAL(10,4),
                    volatility_composite DECIMAL(10,4),
                    trend_strength DECIMAL(10,4),
                    obv_price_divergence DECIMAL(10,4),
                    
                    -- Metadata
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
                
                conn.execute(text(create_table_sql))
                
                # Create indexes for better performance
                indexes_sql = [
                    "CREATE INDEX idx_advanced_tech_symbol_date ON advanced_technical_indicators (symbol, date);",
                    "CREATE INDEX idx_advanced_tech_symbol ON advanced_technical_indicators (symbol);",
                    "CREATE INDEX idx_advanced_tech_date ON advanced_technical_indicators (date);",
                    "CREATE INDEX idx_advanced_tech_rsi ON advanced_technical_indicators (rsi_14);",
                    "CREATE INDEX idx_advanced_tech_macd ON advanced_technical_indicators (macd);",
                    "CREATE INDEX idx_advanced_tech_bb_position ON advanced_technical_indicators (bb_position);"
                ]
                
                for index_sql in indexes_sql:
                    conn.execute(text(index_sql))
                
                conn.commit()
                
                logger.info("✅ Table advanced_technical_indicators recreated successfully")
                
        except Exception as e:
            logger.error(f"❌ Error recreating table: {e}")
            raise
    
    def get_all_symbols(self) -> List[str]:
        """Récupère tous les symboles disponibles."""
        query = "SELECT DISTINCT symbol FROM historical_data ORDER BY symbol"
        df = pd.read_sql(query, self.engine)
        symbols = df['symbol'].tolist()
        logger.info(f"📊 Found {len(symbols)} symbols")
        return symbols
    
    def get_symbol_data(self, symbol: str, limit: Optional[int] = None) -> pd.DataFrame:
        """Récupère les données historiques pour un symbole."""
        query = """
        SELECT date, open, high, low, close, volume
        FROM historical_data 
        WHERE symbol = %s 
        ORDER BY date ASC
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        df = pd.read_sql(query, self.engine, params=(symbol,))
        
        if not df.empty:
            # Convert to proper types
            df['date'] = pd.to_datetime(df['date']).dt.date
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce')
        
        return df
    
    def calculate_indicators_for_symbol(self, symbol: str) -> pd.DataFrame:
        """Calcule tous les indicateurs techniques pour un symbole."""
        logger.info(f"🔧 Calculating indicators for {symbol}...")
        
        try:
            # Get historical data
            df = self.get_symbol_data(symbol)
            
            if df.empty:
                logger.warning(f"⚠️ No data found for {symbol}")
                return pd.DataFrame()
            
            if len(df) < 50:
                logger.warning(f"⚠️ Insufficient data for {symbol} ({len(df)} rows)")
                return pd.DataFrame()
            
            logger.info(f"📊 Processing {len(df)} rows for {symbol}")
            
            # Calculate all TA-Lib indicators
            df_with_indicators = self.talib_calculator.calculate_all_indicators(df)
            
            # Add symbol column
            df_with_indicators['symbol'] = symbol
            
            # Select only the columns that exist in our table schema
            table_columns = self._get_table_columns()
            available_columns = [col for col in table_columns if col in df_with_indicators.columns]
            
            result_df = df_with_indicators[available_columns].copy()
            
            # Fill NaN values with None for database insertion
            result_df = result_df.where(pd.notnull(result_df), None)
            
            logger.info(f"✅ Calculated {len(result_df.columns)} indicators for {symbol}")
            
            return result_df
            
        except Exception as e:
            logger.error(f"❌ Error calculating indicators for {symbol}: {e}")
            return pd.DataFrame()
    
    def _get_table_columns(self) -> List[str]:
        """Retourne la liste des colonnes de la table."""
        return [
            'symbol', 'date', 'open', 'high', 'low', 'close', 'volume',
            # Overlap Studies
            'sma_5', 'sma_10', 'sma_20', 'sma_50', 'sma_100', 'sma_200',
            'ema_5', 'ema_10', 'ema_20', 'ema_50', 'ema_100', 'ema_200',
            'wma_20', 'wma_50', 'trima_20', 'trima_50', 'kama_20', 'kama_50',
            'mama', 'fama', 'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_percent',
            'dema_20', 'tema_20', 'midpoint_20', 'midprice_20', 'sar', 't3_20',
            # Momentum Indicators
            'rsi_14', 'rsi_21', 'stoch_k', 'stoch_d', 'stochf_k', 'stochf_d',
            'stochrsi_k', 'stochrsi_d', 'willr_14', 'adx_14', 'adxr_14',
            'plus_di', 'minus_di', 'aroon_up', 'aroon_down', 'aroonosc', 'bop',
            'cci_14', 'cmo_14', 'dx_14', 'macd', 'macd_signal', 'macd_hist',
            'macd_fix', 'macd_fix_signal', 'macd_fix_hist', 'mom_10', 'mom_20',
            'roc_10', 'roc_20', 'rocp_10', 'rocr_10', 'rocr100_10', 'ultosc',
            # Volume Indicators
            'ad', 'adosc', 'obv', 'mfi_14', 'vpt', 'wad',
            # Volatility Indicators
            'atr_14', 'atr_20', 'trange', 'natr_14', 'stddev_20', 'stddev_50',
            'var_20', 'var_50',
            # Price Transform
            'avgprice', 'medprice', 'typprice', 'wclprice',
            # Cycle Indicators
            'ht_dcperiod', 'ht_dcphase', 'ht_phasor_inphase', 'ht_phasor_quadrature',
            'ht_sine', 'ht_leadsine', 'ht_trendmode',
            # Pattern Recognition
            'cdl_doji', 'cdl_hammer', 'cdl_hangingman', 'cdl_engulfing',
            'cdl_morningstar', 'cdl_eveningstar', 'cdl_piercing', 'cdl_darkcloudcover',
            'cdl_shootingstar', 'cdl_marubozu', 'cdl_spinningtop',
            # Statistical Functions
            'beta_20', 'correl_20', 'linearreg', 'linearreg_angle',
            'linearreg_intercept', 'linearreg_slope', 'tsf_20',
            # Custom Features
            'sma_ratio_20_50', 'ema_ratio_20_50', 'bb_position', 'bb_squeeze',
            'momentum_composite', 'volatility_composite', 'trend_strength', 'obv_price_divergence'
        ]
    
    def store_indicators(self, df: pd.DataFrame, symbol: str):
        """Stocke les indicateurs calculés en base de données."""
        if df.empty:
            logger.warning(f"⚠️ No data to store for {symbol}")
            return
        
        try:
            logger.info(f"💾 Storing {len(df)} records for {symbol}...")
            
            # Insert data in batches for better performance
            batch_size = 1000
            total_batches = (len(df) + batch_size - 1) // batch_size
            
            for i in range(0, len(df), batch_size):
                batch_df = df.iloc[i:i+batch_size]
                batch_num = (i // batch_size) + 1
                
                logger.info(f"📦 Storing batch {batch_num}/{total_batches} for {symbol} ({len(batch_df)} records)")
                
                batch_df.to_sql(
                    'advanced_technical_indicators',
                    self.engine,
                    if_exists='append',
                    index=False,
                    method='multi'
                )
            
            logger.info(f"✅ Successfully stored {len(df)} records for {symbol}")
            
        except Exception as e:
            logger.error(f"❌ Error storing indicators for {symbol}: {e}")
            raise
    
    def calculate_all_indicators(self, symbols: Optional[List[str]] = None, limit_per_symbol: Optional[int] = None):
        """Calcule et stocke tous les indicateurs techniques."""
        logger.info("🚀 Starting comprehensive technical indicators calculation...")
        
        try:
            # Get symbols to process
            if symbols is None:
                symbols = self.get_all_symbols()
            
            logger.info(f"📊 Processing {len(symbols)} symbols")
            
            total_records = 0
            successful_symbols = 0
            failed_symbols = []
            
            for i, symbol in enumerate(symbols, 1):
                logger.info(f"\n📈 Processing {symbol} ({i}/{len(symbols)})")
                
                try:
                    # Calculate indicators
                    indicators_df = self.calculate_indicators_for_symbol(symbol)
                    
                    if not indicators_df.empty:
                        # Store indicators
                        self.store_indicators(indicators_df, symbol)
                        
                        total_records += len(indicators_df)
                        successful_symbols += 1
                        
                        logger.info(f"✅ {symbol}: {len(indicators_df)} records stored")
                    else:
                        logger.warning(f"⚠️ {symbol}: No indicators calculated")
                        failed_symbols.append(symbol)
                
                except Exception as e:
                    logger.error(f"❌ {symbol}: Failed - {e}")
                    failed_symbols.append(symbol)
                
                # Progress update every 10 symbols
                if i % 10 == 0:
                    logger.info(f"📊 Progress: {i}/{len(symbols)} symbols processed")
            
            # Final summary
            logger.info("\n" + "="*60)
            logger.info("📊 CALCULATION SUMMARY")
            logger.info("="*60)
            logger.info(f"✅ Successful symbols: {successful_symbols}")
            logger.info(f"❌ Failed symbols: {len(failed_symbols)}")
            logger.info(f"📈 Total records stored: {total_records:,}")
            
            if failed_symbols:
                logger.info(f"⚠️ Failed symbols: {failed_symbols}")
            
            logger.info("🎉 Technical indicators calculation completed!")
            
        except Exception as e:
            logger.error(f"❌ Error in calculation process: {e}")
            raise

def main():
    """Fonction principale."""
    logger.info("🚀 Starting Technical Indicators Calculation Script")
    
    # Database configuration
    db_config = {
        'host': 'localhost',
        'port': '5432',
        'database': 'aimarkets',
        'user': 'loiclinais',
        'password': 'password'
    }
    
    try:
        # Initialize calculator
        calculator = TechnicalIndicatorsCalculator(db_config)
        
        # Recreate table
        calculator.recreate_table()
        
        # Calculate all indicators
        calculator.calculate_all_indicators()
        
        logger.info("🎉 Script completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Script failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
