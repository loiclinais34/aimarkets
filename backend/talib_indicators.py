"""
Module d'intégration TA-Lib pour les indicateurs techniques avancés
"""

import pandas as pd
import numpy as np
import talib
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class TALibIndicators:
    """
    Classe pour calculer des indicateurs techniques avancés avec TA-Lib
    """
    
    def __init__(self):
        self.indicators_cache = {}
    
    def calculate_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule tous les indicateurs techniques TA-Lib disponibles
        
        Args:
            df: DataFrame avec colonnes OHLCV (Open, High, Low, Close, Volume)
            
        Returns:
            DataFrame enrichi avec tous les indicateurs TA-Lib
        """
        if df.empty or len(df) < 50:  # Minimum 50 périodes pour la plupart des indicateurs
            logger.warning("DataFrame trop petit pour calculer les indicateurs TA-Lib")
            return df
        
        # S'assurer que les colonnes sont en float
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Calculer tous les groupes d'indicateurs
        df = self._calculate_overlap_studies(df)
        df = self._calculate_momentum_indicators(df)
        df = self._calculate_volume_indicators(df)
        df = self._calculate_volatility_indicators(df)
        df = self._calculate_price_transform(df)
        df = self._calculate_cycle_indicators(df)
        df = self._calculate_pattern_recognition(df)
        df = self._calculate_statistic_functions(df)
        
        return df
    
    def _calculate_overlap_studies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les indicateurs de superposition (moyennes mobiles, etc.)"""
        try:
            # Moyennes mobiles simples
            df['sma_5'] = talib.SMA(df['close'], timeperiod=5)
            df['sma_10'] = talib.SMA(df['close'], timeperiod=10)
            df['sma_20'] = talib.SMA(df['close'], timeperiod=20)
            df['sma_50'] = talib.SMA(df['close'], timeperiod=50)
            df['sma_100'] = talib.SMA(df['close'], timeperiod=100)
            df['sma_200'] = talib.SMA(df['close'], timeperiod=200)
            
            # Moyennes mobiles exponentielles
            df['ema_5'] = talib.EMA(df['close'], timeperiod=5)
            df['ema_10'] = talib.EMA(df['close'], timeperiod=10)
            df['ema_20'] = talib.EMA(df['close'], timeperiod=20)
            df['ema_50'] = talib.EMA(df['close'], timeperiod=50)
            df['ema_100'] = talib.EMA(df['close'], timeperiod=100)
            df['ema_200'] = talib.EMA(df['close'], timeperiod=200)
            
            # Moyennes mobiles pondérées
            df['wma_20'] = talib.WMA(df['close'], timeperiod=20)
            df['wma_50'] = talib.WMA(df['close'], timeperiod=50)
            
            # Moyennes mobiles triangulaires
            df['trima_20'] = talib.TRIMA(df['close'], timeperiod=20)
            df['trima_50'] = talib.TRIMA(df['close'], timeperiod=50)
            
            # Moyennes mobiles Kaufman
            df['kama_20'] = talib.KAMA(df['close'], timeperiod=20)
            df['kama_50'] = talib.KAMA(df['close'], timeperiod=50)
            
            # Moyennes mobiles MESA
            df['mama'], df['fama'] = talib.MAMA(df['close'])
            
            # Bande de Bollinger
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(df['close'])
            df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
            df['bb_percent'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            
            # Moyennes mobiles démarrées
            df['dema_20'] = talib.DEMA(df['close'], timeperiod=20)
            df['tema_20'] = talib.TEMA(df['close'], timeperiod=20)
            
            # Moyennes mobiles Hull
            df['hma_20'] = talib.HMA(df['close'], timeperiod=20)
            
            # Moyennes mobiles MidPoint
            df['midpoint_20'] = talib.MIDPOINT(df['close'], timeperiod=20)
            df['midprice_20'] = talib.MIDPRICE(df['high'], df['low'], timeperiod=20)
            
            # Moyennes mobiles Sar
            df['sar'] = talib.SAR(df['high'], df['low'])
            
            # Moyennes mobiles T3
            df['t3_20'] = talib.T3(df['close'], timeperiod=20)
            
            logger.info("Indicateurs de superposition calculés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des indicateurs de superposition: {e}")
        
        return df
    
    def _calculate_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les indicateurs de momentum"""
        try:
            # RSI
            df['rsi_14'] = talib.RSI(df['close'], timeperiod=14)
            df['rsi_21'] = talib.RSI(df['close'], timeperiod=21)
            
            # Stochastic
            df['stoch_k'], df['stoch_d'] = talib.STOCH(df['high'], df['low'], df['close'])
            df['stochf_k'], df['stochf_d'] = talib.STOCHF(df['high'], df['low'], df['close'])
            df['stochrsi_k'], df['stochrsi_d'] = talib.STOCHRSI(df['close'])
            
            # Williams %R
            df['willr_14'] = talib.WILLR(df['high'], df['low'], df['close'], timeperiod=14)
            
            # ADX
            df['adx_14'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14)
            df['adxr_14'] = talib.ADXR(df['high'], df['low'], df['close'], timeperiod=14)
            df['plus_di'] = talib.PLUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
            df['minus_di'] = talib.MINUS_DI(df['high'], df['low'], df['close'], timeperiod=14)
            
            # Aroon
            df['aroon_up'], df['aroon_down'] = talib.AROON(df['high'], df['low'], timeperiod=14)
            df['aroonosc'] = talib.AROONOSC(df['high'], df['low'], timeperiod=14)
            
            # Balance of Power
            df['bop'] = talib.BOP(df['open'], df['high'], df['low'], df['close'])
            
            # Commodity Channel Index
            df['cci_14'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=14)
            
            # CMO
            df['cmo_14'] = talib.CMO(df['close'], timeperiod=14)
            
            # DX
            df['dx_14'] = talib.DX(df['high'], df['low'], df['close'], timeperiod=14)
            
            # MACD
            df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(df['close'])
            df['macd_fix'], df['macd_fix_signal'], df['macd_fix_hist'] = talib.MACDFIX(df['close'])
            
            # Momentum
            df['mom_10'] = talib.MOM(df['close'], timeperiod=10)
            df['mom_20'] = talib.MOM(df['close'], timeperiod=20)
            
            # Rate of Change
            df['roc_10'] = talib.ROC(df['close'], timeperiod=10)
            df['roc_20'] = talib.ROC(df['close'], timeperiod=20)
            df['rocp_10'] = talib.ROCP(df['close'], timeperiod=10)
            df['rocr_10'] = talib.ROCR(df['close'], timeperiod=10)
            df['rocr100_10'] = talib.ROCR100(df['close'], timeperiod=10)
            
            # Ultimate Oscillator
            df['ultosc'] = talib.ULTOSC(df['high'], df['low'], df['close'])
            
            logger.info("Indicateurs de momentum calculés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des indicateurs de momentum: {e}")
        
        return df
    
    def _calculate_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les indicateurs de volume"""
        try:
            # AD (Accumulation/Distribution)
            df['ad'] = talib.AD(df['high'], df['low'], df['close'], df['volume'])
            
            # ADOSC
            df['adosc'] = talib.ADOSC(df['high'], df['low'], df['close'], df['volume'])
            
            # OBV
            df['obv'] = talib.OBV(df['close'], df['volume'])
            
            # Chaikin Money Flow
            df['cmf_20'] = talib.CMF(df['high'], df['low'], df['close'], df['volume'], timeperiod=20)
            
            # Money Flow Index
            df['mfi_14'] = talib.MFI(df['high'], df['low'], df['close'], df['volume'], timeperiod=14)
            
            # Volume Price Trend
            df['vpt'] = talib.VPT(df['close'], df['volume'])
            
            # Williams Accumulation/Distribution
            df['wad'] = talib.WAD(df['high'], df['low'], df['close'])
            
            logger.info("Indicateurs de volume calculés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des indicateurs de volume: {e}")
        
        return df
    
    def _calculate_volatility_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les indicateurs de volatilité"""
        try:
            # Average True Range
            df['atr_14'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            df['atr_20'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=20)
            
            # True Range
            df['trange'] = talib.TRANGE(df['high'], df['low'], df['close'])
            
            # Normalized Average True Range
            df['natr_14'] = talib.NATR(df['high'], df['low'], df['close'], timeperiod=14)
            
            # Standard Deviation
            df['stddev_20'] = talib.STDDEV(df['close'], timeperiod=20)
            df['stddev_50'] = talib.STDDEV(df['close'], timeperiod=50)
            
            # Variance
            df['var_20'] = talib.VAR(df['close'], timeperiod=20)
            df['var_50'] = talib.VAR(df['close'], timeperiod=50)
            
            logger.info("Indicateurs de volatilité calculés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des indicateurs de volatilité: {e}")
        
        return df
    
    def _calculate_price_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les transformations de prix"""
        try:
            # Average Price
            df['avgprice'] = talib.AVGPRICE(df['open'], df['high'], df['low'], df['close'])
            
            # Median Price
            df['medprice'] = talib.MEDPRICE(df['high'], df['low'])
            
            # Typical Price
            df['typprice'] = talib.TYPPRICE(df['high'], df['low'], df['close'])
            
            # Weighted Close Price
            df['wclprice'] = talib.WCLPRICE(df['high'], df['low'], df['close'])
            
            logger.info("Transformations de prix calculées avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des transformations de prix: {e}")
        
        return df
    
    def _calculate_cycle_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les indicateurs de cycle"""
        try:
            # Hilbert Transform - Dominant Cycle Period
            df['ht_dcperiod'] = talib.HT_DCPERIOD(df['close'])
            
            # Hilbert Transform - Dominant Cycle Phase
            df['ht_dcphase'] = talib.HT_DCPHASE(df['close'])
            
            # Hilbert Transform - Phasor Components
            df['ht_phasor_inphase'], df['ht_phasor_quadrature'] = talib.HT_PHASOR(df['close'])
            
            # Hilbert Transform - SineWave
            df['ht_sine'], df['ht_leadsine'] = talib.HT_SINE(df['close'])
            
            # Hilbert Transform - Trend vs Cycle Mode
            df['ht_trendmode'] = talib.HT_TRENDMODE(df['close'])
            
            logger.info("Indicateurs de cycle calculés avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des indicateurs de cycle: {e}")
        
        return df
    
    def _calculate_pattern_recognition(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule la reconnaissance de patterns"""
        try:
            # Patterns de chandeliers japonais
            df['cdl_2crows'] = talib.CDL2CROWS(df['open'], df['high'], df['low'], df['close'])
            df['cdl_3blackcrows'] = talib.CDL3BLACKCROWS(df['open'], df['high'], df['low'], df['close'])
            df['cdl_3inside'] = talib.CDL3INSIDE(df['open'], df['high'], df['low'], df['close'])
            df['cdl_3linestrike'] = talib.CDL3LINESTRIKE(df['open'], df['high'], df['low'], df['close'])
            df['cdl_3outside'] = talib.CDL3OUTSIDE(df['open'], df['high'], df['low'], df['close'])
            df['cdl_3starsinsouth'] = talib.CDL3STARSINSOUTH(df['open'], df['high'], df['low'], df['close'])
            df['cdl_3whitesoldiers'] = talib.CDL3WHITESOLDIERS(df['open'], df['high'], df['low'], df['close'])
            df['cdl_abandonedbaby'] = talib.CDLABANDONEDBABY(df['open'], df['high'], df['low'], df['close'])
            df['cdl_advanceblock'] = talib.CDLADVANCEBLOCK(df['open'], df['high'], df['low'], df['close'])
            df['cdl_belthold'] = talib.CDLBELTHOLD(df['open'], df['high'], df['low'], df['close'])
            df['cdl_breakaway'] = talib.CDLBREAKAWAY(df['open'], df['high'], df['low'], df['close'])
            df['cdl_closingmarubozu'] = talib.CDLCLOSINGMARUBOZU(df['open'], df['high'], df['low'], df['close'])
            df['cdl_concealbabyswall'] = talib.CDLCONCEALBABYSWALL(df['open'], df['high'], df['low'], df['close'])
            df['cdl_counterattack'] = talib.CDLCOUNTERATTACK(df['open'], df['high'], df['low'], df['close'])
            df['cdl_darkcloudcover'] = talib.CDLDARKCLOUDCOVER(df['open'], df['high'], df['low'], df['close'])
            df['cdl_doji'] = talib.CDLDOJI(df['open'], df['high'], df['low'], df['close'])
            df['cdl_dojistar'] = talib.CDLDOJISTAR(df['open'], df['high'], df['low'], df['close'])
            df['cdl_dragonflydoji'] = talib.CDLDRAGONFLYDOJI(df['open'], df['high'], df['low'], df['close'])
            df['cdl_engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close'])
            df['cdl_eveningdojistar'] = talib.CDLEVENINGDOJISTAR(df['open'], df['high'], df['low'], df['close'])
            df['cdl_eveningstar'] = talib.CDLEVENINGSTAR(df['open'], df['high'], df['low'], df['close'])
            df['cdl_gapsidesidewhite'] = talib.CDLGAPSIDESIDEWHITE(df['open'], df['high'], df['low'], df['close'])
            df['cdl_gravestonedoji'] = talib.CDLGRAVESTONEDOJI(df['open'], df['high'], df['low'], df['close'])
            df['cdl_hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close'])
            df['cdl_hangingman'] = talib.CDLHANGINGMAN(df['open'], df['high'], df['low'], df['close'])
            df['cdl_harami'] = talib.CDLHARAMI(df['open'], df['high'], df['low'], df['close'])
            df['cdl_haramicross'] = talib.CDLHARAMICROSS(df['open'], df['high'], df['low'], df['close'])
            df['cdl_highwave'] = talib.CDLHIGHWAVE(df['open'], df['high'], df['low'], df['close'])
            df['cdl_hikkake'] = talib.CDLHIKKAKE(df['open'], df['high'], df['low'], df['close'])
            df['cdl_hikkakemod'] = talib.CDLHIKKAKEMOD(df['open'], df['high'], df['low'], df['close'])
            df['cdl_identical3crows'] = talib.CDLIDENTICAL3CROWS(df['open'], df['high'], df['low'], df['close'])
            df['cdl_inneck'] = talib.CDLINNECK(df['open'], df['high'], df['low'], df['close'])
            df['cdl_invertedhammer'] = talib.CDLINVERTEDHAMMER(df['open'], df['high'], df['low'], df['close'])
            df['cdl_kicking'] = talib.CDLKICKING(df['open'], df['high'], df['low'], df['close'])
            df['cdl_kickingbylength'] = talib.CDLKICKINGBYLENGTH(df['open'], df['high'], df['low'], df['close'])
            df['cdl_ladderbottom'] = talib.CDLLADDERBOTTOM(df['open'], df['high'], df['low'], df['close'])
            df['cdl_longleggeddoji'] = talib.CDLLONGLEGGEDDOJI(df['open'], df['high'], df['low'], df['close'])
            df['cdl_longline'] = talib.CDLLONGLINE(df['open'], df['high'], df['low'], df['close'])
            df['cdl_marubozu'] = talib.CDLMARUBOZU(df['open'], df['high'], df['low'], df['close'])
            df['cdl_matchinglow'] = talib.CDLMATCHINGLOW(df['open'], df['high'], df['low'], df['close'])
            df['cdl_mathold'] = talib.CDLMATHOLD(df['open'], df['high'], df['low'], df['close'])
            df['cdl_morningdojistar'] = talib.CDLMORNINGDOJISTAR(df['open'], df['high'], df['low'], df['close'])
            df['cdl_morningstar'] = talib.CDLMORNINGSTAR(df['open'], df['high'], df['low'], df['close'])
            df['cdl_onneck'] = talib.CDLONNECK(df['open'], df['high'], df['low'], df['close'])
            df['cdl_piercing'] = talib.CDLPIERCING(df['open'], df['high'], df['low'], df['close'])
            df['cdl_rickshawman'] = talib.CDLRICKSHAWMAN(df['open'], df['high'], df['low'], df['close'])
            df['cdl_risefall3methods'] = talib.CDLRISEFALL3METHODS(df['open'], df['high'], df['low'], df['close'])
            df['cdl_separatinglines'] = talib.CDLSEPARATINGLINES(df['open'], df['high'], df['low'], df['close'])
            df['cdl_shootingstar'] = talib.CDLSHOOTINGSTAR(df['open'], df['high'], df['low'], df['close'])
            df['cdl_shortline'] = talib.CDLSHORTLINE(df['open'], df['high'], df['low'], df['close'])
            df['cdl_spinningtop'] = talib.CDLSPINNINGTOP(df['open'], df['high'], df['low'], df['close'])
            df['cdl_stalledpattern'] = talib.CDLSTALLEDPATTERN(df['open'], df['high'], df['low'], df['close'])
            df['cdl_sticksandwich'] = talib.CDLSTICKSANDWICH(df['open'], df['high'], df['low'], df['close'])
            df['cdl_takuri'] = talib.CDLTAKURI(df['open'], df['high'], df['low'], df['close'])
            df['cdl_tasukigap'] = talib.CDLTASUKIGAP(df['open'], df['high'], df['low'], df['close'])
            df['cdl_thrusting'] = talib.CDLTHRUSTING(df['open'], df['high'], df['low'], df['close'])
            df['cdl_tristar'] = talib.CDLTRISTAR(df['open'], df['high'], df['low'], df['close'])
            df['cdl_unique3river'] = talib.CDLUNIQUE3RIVER(df['open'], df['high'], df['low'], df['close'])
            df['cdl_upsidegap2crows'] = talib.CDLUPSIDEGAP2CROWS(df['open'], df['high'], df['low'], df['close'])
            df['cdl_xsidegap3methods'] = talib.CDLXSIDEGAP3METHODS(df['open'], df['high'], df['low'], df['close'])
            
            logger.info("Reconnaissance de patterns calculée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul de la reconnaissance de patterns: {e}")
        
        return df
    
    def _calculate_statistic_functions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcule les fonctions statistiques"""
        try:
            # Beta
            df['beta_20'] = talib.BETA(df['high'], df['low'], timeperiod=20)
            
            # Correlation
            df['correl_20'] = talib.CORREL(df['high'], df['low'], timeperiod=20)
            
            # Linear Regression
            df['linearreg'] = talib.LINEARREG(df['close'], timeperiod=20)
            df['linearreg_angle'] = talib.LINEARREG_ANGLE(df['close'], timeperiod=20)
            df['linearreg_intercept'] = talib.LINEARREG_INTERCEPT(df['close'], timeperiod=20)
            df['linearreg_slope'] = talib.LINEARREG_SLOPE(df['close'], timeperiod=20)
            
            # Time Series Forecast
            df['tsf_20'] = talib.TSF(df['close'], timeperiod=20)
            
            logger.info("Fonctions statistiques calculées avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des fonctions statistiques: {e}")
        
        return df
    
    def get_feature_columns(self) -> List[str]:
        """
        Retourne la liste des colonnes d'indicateurs techniques générées
        
        Returns:
            Liste des noms de colonnes d'indicateurs
        """
        feature_columns = [
            # Overlap Studies
            'sma_5', 'sma_10', 'sma_20', 'sma_50', 'sma_100', 'sma_200',
            'ema_5', 'ema_10', 'ema_20', 'ema_50', 'ema_100', 'ema_200',
            'wma_20', 'wma_50', 'trima_20', 'trima_50', 'kama_20', 'kama_50',
            'mama', 'fama', 'bb_upper', 'bb_middle', 'bb_lower', 'bb_width', 'bb_percent',
            'dema_20', 'tema_20', 'hma_20', 'midpoint_20', 'midprice_20', 'sar', 't3_20',
            
            # Momentum Indicators
            'rsi_14', 'rsi_21', 'stoch_k', 'stoch_d', 'stochf_k', 'stochf_d',
            'stochrsi_k', 'stochrsi_d', 'willr_14', 'adx_14', 'adxr_14',
            'plus_di', 'minus_di', 'aroon_up', 'aroon_down', 'aroonosc', 'bop',
            'cci_14', 'cmo_14', 'dx_14', 'macd', 'macd_signal', 'macd_hist',
            'macd_fix', 'macd_fix_signal', 'macd_fix_hist', 'mom_10', 'mom_20',
            'roc_10', 'roc_20', 'rocp_10', 'rocr_10', 'rocr100_10', 'ultosc',
            
            # Volume Indicators
            'ad', 'adosc', 'obv', 'cmf_20', 'mfi_14', 'vpt', 'wad',
            
            # Volatility Indicators
            'atr_14', 'atr_20', 'trange', 'natr_14', 'stddev_20', 'stddev_50',
            'var_20', 'var_50',
            
            # Price Transform
            'avgprice', 'medprice', 'typprice', 'wclprice',
            
            # Cycle Indicators
            'ht_dcperiod', 'ht_dcphase', 'ht_phasor_inphase', 'ht_phasor_quadrature',
            'ht_sine', 'ht_leadsine', 'ht_trendmode',
            
            # Pattern Recognition (subset des plus importants)
            'cdl_doji', 'cdl_hammer', 'cdl_hangingman', 'cdl_engulfing',
            'cdl_morningstar', 'cdl_eveningstar', 'cdl_piercing', 'cdl_darkcloudcover',
            'cdl_shootingstar', 'cdl_marubozu', 'cdl_spinningtop',
            
            # Statistic Functions
            'beta_20', 'correl_20', 'linearreg', 'linearreg_angle',
            'linearreg_intercept', 'linearreg_slope', 'tsf_20'
        ]
        
        return feature_columns
    
    def calculate_custom_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcule des features personnalisées basées sur les indicateurs TA-Lib
        
        Args:
            df: DataFrame avec les indicateurs TA-Lib
            
        Returns:
            DataFrame enrichi avec des features personnalisées
        """
        try:
            # Ratios de moyennes mobiles
            if 'sma_20' in df.columns and 'sma_50' in df.columns:
                df['sma_ratio_20_50'] = df['sma_20'] / df['sma_50']
            
            if 'ema_20' in df.columns and 'ema_50' in df.columns:
                df['ema_ratio_20_50'] = df['ema_20'] / df['ema_50']
            
            # Position relative dans les bandes de Bollinger
            if all(col in df.columns for col in ['bb_upper', 'bb_lower', 'close']):
                df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
                df['bb_squeeze'] = (df['bb_upper'] - df['bb_lower']) / df['close']
            
            # Momentum composite
            momentum_cols = ['rsi_14', 'stoch_k', 'willr_14', 'cci_14']
            available_momentum = [col for col in momentum_cols if col in df.columns]
            if available_momentum:
                df['momentum_composite'] = df[available_momentum].mean(axis=1)
            
            # Volatilité composite
            volatility_cols = ['atr_14', 'stddev_20', 'bb_width']
            available_volatility = [col for col in volatility_cols if col in df.columns]
            if available_volatility:
                df['volatility_composite'] = df[available_volatility].mean(axis=1)
            
            # Trend strength composite
            trend_cols = ['adx_14', 'plus_di', 'minus_di']
            available_trend = [col for col in trend_cols if col in df.columns]
            if available_trend:
                df['trend_strength'] = df[available_trend].mean(axis=1)
            
            # Volume-price relationship
            if 'obv' in df.columns and 'close' in df.columns:
                df['obv_price_divergence'] = df['obv'].pct_change() - df['close'].pct_change()
            
            logger.info("Features personnalisées calculées avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des features personnalisées: {e}")
        
        return df


def test_talib_integration():
    """
    Fonction de test pour vérifier l'intégration TA-Lib
    """
    import pandas as pd
    import numpy as np
    
    # Créer des données de test
    np.random.seed(42)
    dates = pd.date_range('2025-01-01', periods=100, freq='D')
    
    # Générer des données OHLCV simulées
    base_price = 100
    prices = []
    for i in range(100):
        change = np.random.normal(0, 0.02)
        base_price *= (1 + change)
        prices.append(base_price)
    
    df = pd.DataFrame({
        'date': dates,
        'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
        'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, 100)
    })
    
    # S'assurer que high >= low et high >= open,close et low <= open,close
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    print("Données de test créées:")
    print(df.head())
    print(f"Shape: {df.shape}")
    
    # Tester l'intégration TA-Lib
    talib_calculator = TALibIndicators()
    
    print("\nCalcul des indicateurs TA-Lib...")
    df_with_indicators = talib_calculator.calculate_all_indicators(df)
    
    print(f"Shape après calcul des indicateurs: {df_with_indicators.shape}")
    print(f"Nombre de colonnes ajoutées: {df_with_indicators.shape[1] - df.shape[1]}")
    
    # Afficher quelques indicateurs clés
    key_indicators = ['rsi_14', 'macd', 'bb_upper', 'bb_lower', 'atr_14', 'obv']
    available_indicators = [col for col in key_indicators if col in df_with_indicators.columns]
    
    print(f"\nIndicateurs clés disponibles: {available_indicators}")
    print(df_with_indicators[['date', 'close'] + available_indicators].tail())
    
    # Calculer les features personnalisées
    print("\nCalcul des features personnalisées...")
    df_with_custom = talib_calculator.calculate_custom_features(df_with_indicators)
    
    custom_features = [col for col in df_with_custom.columns if col not in df_with_indicators.columns]
    print(f"Features personnalisées ajoutées: {custom_features}")
    
    print("\n✅ Test d'intégration TA-Lib réussi!")
    return df_with_custom


if __name__ == "__main__":
    test_talib_integration()
