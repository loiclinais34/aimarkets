"""
Service de calcul des indicateurs techniques
Calcule tous les indicateurs techniques pour les données historiques
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import text
import logging

from ..core.config import settings
from ..models.database import HistoricalData, TechnicalIndicators

logger = logging.getLogger(__name__)


class TechnicalIndicatorsCalculator:
    """Calculateur d'indicateurs techniques"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.config = settings
    
    def calculate_all_indicators(self, symbol: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> bool:
        """
        Calcule tous les indicateurs techniques pour un symbole
        
        Args:
            symbol: Symbole du titre
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            logger.info(f"Calcul des indicateurs techniques pour {symbol}")
            
            # Récupérer les données historiques
            historical_data = self._get_historical_data(symbol, start_date, end_date)
            if historical_data.empty:
                logger.warning(f"Aucune donnée historique trouvée pour {symbol}")
                return False
            
            # Calculer tous les indicateurs
            indicators = self._calculate_indicators(historical_data)
            
            # Sauvegarder les indicateurs
            self._save_indicators(symbol, indicators)
            
            logger.info(f"Indicateurs techniques calculés avec succès pour {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du calcul des indicateurs pour {symbol}: {e}")
            return False
    
    def _get_historical_data(self, symbol: str, start_date: Optional[date] = None, end_date: Optional[date] = None) -> pd.DataFrame:
        """Récupérer les données historiques depuis la base de données"""
        query = self.db.query(HistoricalData).filter(HistoricalData.symbol == symbol.upper())
        
        if start_date:
            query = query.filter(HistoricalData.date >= start_date)
        if end_date:
            query = query.filter(HistoricalData.date <= end_date)
        
        query = query.order_by(HistoricalData.date)
        
        # Convertir en DataFrame
        data = []
        for row in query.all():
            data.append({
                'date': row.date,
                'open': float(row.open),
                'high': float(row.high),
                'low': float(row.low),
                'close': float(row.close),
                'volume': int(row.volume),
                'vwap': float(row.vwap) if row.vwap else None
            })
        
        return pd.DataFrame(data)
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculer tous les indicateurs techniques"""
        if df.empty:
            return df
        
        # S'assurer que les données sont triées par date
        df = df.sort_values('date').reset_index(drop=True)
        
        # Calculer les moyennes mobiles
        df = self._calculate_moving_averages(df)
        
        # Calculer les indicateurs de momentum
        df = self._calculate_momentum_indicators(df)
        
        # Calculer les Bollinger Bands
        df = self._calculate_bollinger_bands(df)
        
        # Calculer les indicateurs de volume
        df = self._calculate_volume_indicators(df)
        
        # Calculer l'ATR
        df = self._calculate_atr(df)
        
        return df
    
    def _calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculer les moyennes mobiles simples et exponentielles"""
        periods = self.config.technical_sma_periods
        
        # Moyennes mobiles simples (SMA)
        for period in periods:
            df[f'sma_{period}'] = df['close'].rolling(window=period).mean()
        
        # Moyennes mobiles exponentielles (EMA)
        for period in periods:
            df[f'ema_{period}'] = df['close'].ewm(span=period).mean()
        
        return df
    
    def _calculate_momentum_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculer les indicateurs de momentum"""
        
        # RSI (Relative Strength Index)
        df['rsi_14'] = self._calculate_rsi(df['close'], 14)
        
        # MACD (Moving Average Convergence Divergence)
        macd_data = self._calculate_macd(df['close'])
        df['macd'] = macd_data['macd']
        df['macd_signal'] = macd_data['signal']
        df['macd_histogram'] = macd_data['histogram']
        
        # Stochastic Oscillator
        stoch_data = self._calculate_stochastic(df)
        df['stochastic_k'] = stoch_data['k']
        df['stochastic_d'] = stoch_data['d']
        
        # Williams %R
        df['williams_r'] = self._calculate_williams_r(df)
        
        # Rate of Change (ROC)
        df['roc'] = self._calculate_roc(df['close'], 10)
        
        # Commodity Channel Index (CCI)
        df['cci'] = self._calculate_cci(df)
        
        return df
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculer les Bollinger Bands"""
        period = self.config.technical_bollinger_period
        std_dev = self.config.technical_bollinger_std
        
        # Moyenne mobile et écart-type
        sma = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        
        # Bands
        df['bb_upper'] = sma + (std * std_dev)
        df['bb_middle'] = sma
        df['bb_lower'] = sma - (std * std_dev)
        
        # Largeur et position
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        return df
    
    def _calculate_volume_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculer les indicateurs de volume"""
        
        # On-Balance Volume (OBV)
        df['obv'] = self._calculate_obv(df)
        
        # Volume Rate of Change
        df['volume_roc'] = self._calculate_volume_roc(df['volume'])
        
        # Volume Moving Average
        df['volume_sma_20'] = df['volume'].rolling(window=20).mean()
        
        return df
    
    def _calculate_atr(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculer l'Average True Range (ATR)"""
        period = self.config.technical_atr_period
        
        # True Range
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        
        # ATR
        df['atr_14'] = df['tr'].rolling(window=period).mean()
        
        # Supprimer la colonne temporaire
        df.drop('tr', axis=1, inplace=True)
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculer le RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, pd.Series]:
        """Calculer le MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        macd_histogram = macd - macd_signal
        
        return {
            'macd': macd,
            'signal': macd_signal,
            'histogram': macd_histogram
        }
    
    def _calculate_stochastic(self, df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """Calculer le Stochastic Oscillator"""
        lowest_low = df['low'].rolling(window=k_period).min()
        highest_high = df['high'].rolling(window=k_period).max()
        
        k_percent = 100 * ((df['close'] - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        
        return {
            'k': k_percent,
            'd': d_percent
        }
    
    def _calculate_williams_r(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculer le Williams %R"""
        highest_high = df['high'].rolling(window=period).max()
        lowest_low = df['low'].rolling(window=period).min()
        
        williams_r = -100 * ((highest_high - df['close']) / (highest_high - lowest_low))
        
        return williams_r
    
    def _calculate_roc(self, prices: pd.Series, period: int = 10) -> pd.Series:
        """Calculer le Rate of Change"""
        roc = ((prices - prices.shift(period)) / prices.shift(period)) * 100
        return roc
    
    def _calculate_cci(self, df: pd.DataFrame, period: int = 20) -> pd.Series:
        """Calculer le Commodity Channel Index"""
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        sma_tp = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
        
        cci = (typical_price - sma_tp) / (0.015 * mad)
        
        return cci
    
    def _calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """Calculer l'On-Balance Volume"""
        obv = np.zeros(len(df))
        obv[0] = df['volume'].iloc[0]
        
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv[i] = obv[i-1] + df['volume'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv[i] = obv[i-1] - df['volume'].iloc[i]
            else:
                obv[i] = obv[i-1]
        
        return pd.Series(obv, index=df.index)
    
    def _calculate_volume_roc(self, volume: pd.Series, period: int = 10) -> pd.Series:
        """Calculer le Volume Rate of Change"""
        volume_roc = ((volume - volume.shift(period)) / volume.shift(period)) * 100
        return volume_roc
    
    def _convert_nan_to_none(self, value):
        """Convertir les valeurs NaN en None pour la base de données"""
        if pd.isna(value) or np.isnan(value) if isinstance(value, (int, float)) else False:
            return None
        return value
    
    def _save_indicators(self, symbol: str, indicators_df: pd.DataFrame) -> None:
        """Sauvegarder les indicateurs dans la base de données"""
        for _, row in indicators_df.iterrows():
            # Vérifier si l'enregistrement existe déjà
            existing = self.db.query(TechnicalIndicators).filter(
                TechnicalIndicators.symbol == symbol.upper(),
                TechnicalIndicators.date == row['date']
            ).first()
            
            if existing:
                # Mettre à jour l'enregistrement existant
                existing.sma_5 = self._convert_nan_to_none(row.get('sma_5'))
                existing.sma_10 = self._convert_nan_to_none(row.get('sma_10'))
                existing.sma_20 = self._convert_nan_to_none(row.get('sma_20'))
                existing.sma_50 = self._convert_nan_to_none(row.get('sma_50'))
                existing.sma_200 = self._convert_nan_to_none(row.get('sma_200'))
                existing.ema_5 = self._convert_nan_to_none(row.get('ema_5'))
                existing.ema_10 = self._convert_nan_to_none(row.get('ema_10'))
                existing.ema_20 = self._convert_nan_to_none(row.get('ema_20'))
                existing.ema_50 = self._convert_nan_to_none(row.get('ema_50'))
                existing.ema_200 = self._convert_nan_to_none(row.get('ema_200'))
                existing.rsi_14 = self._convert_nan_to_none(row.get('rsi_14'))
                existing.macd = self._convert_nan_to_none(row.get('macd'))
                existing.macd_signal = self._convert_nan_to_none(row.get('macd_signal'))
                existing.macd_histogram = self._convert_nan_to_none(row.get('macd_histogram'))
                existing.stochastic_k = self._convert_nan_to_none(row.get('stochastic_k'))
                existing.stochastic_d = self._convert_nan_to_none(row.get('stochastic_d'))
                existing.williams_r = self._convert_nan_to_none(row.get('williams_r'))
                existing.roc = self._convert_nan_to_none(row.get('roc'))
                existing.cci = self._convert_nan_to_none(row.get('cci'))
                existing.bb_upper = self._convert_nan_to_none(row.get('bb_upper'))
                existing.bb_middle = self._convert_nan_to_none(row.get('bb_middle'))
                existing.bb_lower = self._convert_nan_to_none(row.get('bb_lower'))
                existing.bb_width = self._convert_nan_to_none(row.get('bb_width'))
                existing.bb_position = self._convert_nan_to_none(row.get('bb_position'))
                existing.obv = self._convert_nan_to_none(row.get('obv'))
                existing.volume_roc = self._convert_nan_to_none(row.get('volume_roc'))
                existing.volume_sma_20 = self._convert_nan_to_none(row.get('volume_sma_20'))
                existing.atr_14 = self._convert_nan_to_none(row.get('atr_14'))
            else:
                # Créer un nouvel enregistrement
                new_indicator = TechnicalIndicators(
                    symbol=symbol.upper(),
                    date=row['date'],
                    sma_5=self._convert_nan_to_none(row.get('sma_5')),
                    sma_10=self._convert_nan_to_none(row.get('sma_10')),
                    sma_20=self._convert_nan_to_none(row.get('sma_20')),
                    sma_50=self._convert_nan_to_none(row.get('sma_50')),
                    sma_200=self._convert_nan_to_none(row.get('sma_200')),
                    ema_5=self._convert_nan_to_none(row.get('ema_5')),
                    ema_10=self._convert_nan_to_none(row.get('ema_10')),
                    ema_20=self._convert_nan_to_none(row.get('ema_20')),
                    ema_50=self._convert_nan_to_none(row.get('ema_50')),
                    ema_200=self._convert_nan_to_none(row.get('ema_200')),
                    rsi_14=self._convert_nan_to_none(row.get('rsi_14')),
                    macd=self._convert_nan_to_none(row.get('macd')),
                    macd_signal=self._convert_nan_to_none(row.get('macd_signal')),
                    macd_histogram=self._convert_nan_to_none(row.get('macd_histogram')),
                    stochastic_k=self._convert_nan_to_none(row.get('stochastic_k')),
                    stochastic_d=self._convert_nan_to_none(row.get('stochastic_d')),
                    williams_r=self._convert_nan_to_none(row.get('williams_r')),
                    roc=self._convert_nan_to_none(row.get('roc')),
                    cci=self._convert_nan_to_none(row.get('cci')),
                    bb_upper=self._convert_nan_to_none(row.get('bb_upper')),
                    bb_middle=self._convert_nan_to_none(row.get('bb_middle')),
                    bb_lower=self._convert_nan_to_none(row.get('bb_lower')),
                    bb_width=self._convert_nan_to_none(row.get('bb_width')),
                    bb_position=self._convert_nan_to_none(row.get('bb_position')),
                    obv=self._convert_nan_to_none(row.get('obv')),
                    volume_roc=self._convert_nan_to_none(row.get('volume_roc')),
                    volume_sma_20=self._convert_nan_to_none(row.get('volume_sma_20')),
                    atr_14=self._convert_nan_to_none(row.get('atr_14'))
                )
                self.db.add(new_indicator)
        
        self.db.commit()
    
    def calculate_indicators_for_all_symbols(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict[str, bool]:
        """
        Calculer les indicateurs techniques pour tous les symboles
        
        Args:
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)
            
        Returns:
            Dict[str, bool]: Résultat par symbole
        """
        # Récupérer tous les symboles uniques
        symbols = self.db.query(HistoricalData.symbol).distinct().all()
        symbols = [symbol[0] for symbol in symbols]
        
        results = {}
        total_symbols = len(symbols)
        
        logger.info(f"Début du calcul des indicateurs pour {total_symbols} symboles")
        
        for i, symbol in enumerate(symbols, 1):
            logger.info(f"Traitement {i}/{total_symbols}: {symbol}")
            try:
                success = self.calculate_all_indicators(symbol, start_date, end_date)
                results[symbol] = success
                if success:
                    logger.info(f"✅ {symbol} traité avec succès")
                else:
                    logger.warning(f"⚠️ {symbol} échoué")
            except Exception as e:
                logger.error(f"❌ Erreur pour {symbol}: {e}")
                results[symbol] = False
        
        successful = sum(1 for success in results.values() if success)
        logger.info(f"Calcul terminé: {successful}/{total_symbols} symboles traités avec succès")
        
        return results
    
    def get_indicators_summary(self) -> Dict[str, int]:
        """Obtenir un résumé des indicateurs calculés"""
        try:
            total_indicators = self.db.query(TechnicalIndicators).count()
            unique_symbols = self.db.query(TechnicalIndicators.symbol).distinct().count()
            unique_dates = self.db.query(TechnicalIndicators.date).distinct().count()
            
            return {
                'total_indicators': total_indicators,
                'unique_symbols': unique_symbols,
                'unique_dates': unique_dates
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du résumé: {e}")
            return {'total_indicators': 0, 'unique_symbols': 0, 'unique_dates': 0}
