#!/usr/bin/env python3
"""
Système d'indicateurs techniques avancés pour le ML sophistiqué.
Calcule tous les indicateurs techniques nécessaires pour les modèles ML.
"""

import os
import sys
import pandas as pd
import numpy as np
import psycopg2
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import talib
from dotenv import load_dotenv

# Ajouter le chemin du projet
sys.path.append('/Users/loiclinais/Documents/dev/aimarkets/backend')

load_dotenv()

class AdvancedTechnicalIndicators:
    """Classe pour calculer les indicateurs techniques avancés"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'aimarkets'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'password')
        )
    
    def get_historical_data(self, symbol: str, start_date: str = '2025-01-01') -> pd.DataFrame:
        """Récupère les données historiques pour un symbole"""
        query = """
        SELECT date, open, high, low, close, volume
        FROM historical_data 
        WHERE symbol = %s AND date >= %s
        ORDER BY date
        """
        df = pd.read_sql_query(query, self.conn, params=[symbol, start_date])
        
        # Convertir les colonnes numériques en float pour TA-Lib
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        return df
    
    def calculate_sma(self, prices: pd.Series, periods: List[int]) -> Dict[str, float]:
        """Calcule les moyennes mobiles simples"""
        sma_values = {}
        for period in periods:
            sma_values[f'sma_{period}'] = prices.rolling(window=period).mean().iloc[-1] if len(prices) >= period else None
        return sma_values
    
    def calculate_ema(self, prices: pd.Series, periods: List[int]) -> Dict[str, float]:
        """Calcule les moyennes mobiles exponentielles"""
        ema_values = {}
        for period in periods:
            ema_values[f'ema_{period}'] = prices.ewm(span=period).mean().iloc[-1] if len(prices) >= period else None
        return ema_values
    
    def calculate_rsi(self, prices: pd.Series, periods: List[int]) -> Dict[str, float]:
        """Calcule le RSI pour différentes périodes"""
        rsi_values = {}
        for period in periods:
            if len(prices) >= period + 1:
                rsi_values[f'rsi_{period}'] = talib.RSI(prices.values, timeperiod=period)[-1]
            else:
                rsi_values[f'rsi_{period}'] = None
        return rsi_values
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict[str, float]:
        """Calcule les bandes de Bollinger"""
        if len(prices) < period:
            return {'bollinger_upper': None, 'bollinger_middle': None, 'bollinger_lower': None, 'bollinger_width': None}
        
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        width = (upper - lower) / sma
        
        return {
            'bollinger_upper': upper.iloc[-1],
            'bollinger_middle': sma.iloc[-1],
            'bollinger_lower': lower.iloc[-1],
            'bollinger_width': width.iloc[-1]
        }
    
    def calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """Calcule le MACD"""
        if len(prices) < slow + signal:
            return {'macd_line': None, 'macd_signal': None, 'macd_histogram': None}
        
        macd_line, macd_signal, macd_histogram = talib.MACD(prices.values, fastperiod=fast, slowperiod=slow, signalperiod=signal)
        
        return {
            'macd_line': macd_line[-1],
            'macd_signal': macd_signal[-1],
            'macd_histogram': macd_histogram[-1]
        }
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Dict[str, float]:
        """Calcule le stochastique"""
        if len(close) < k_period + d_period:
            return {'stochastic_k': None, 'stochastic_d': None}
        
        k_percent, d_percent = talib.STOCH(high.values, low.values, close.values, 
                                         fastk_period=k_period, slowk_period=d_period, slowd_period=d_period)
        
        return {
            'stochastic_k': k_percent[-1],
            'stochastic_d': d_percent[-1]
        }
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> float:
        """Calcule l'ATR (Average True Range)"""
        if len(close) < period + 1:
            return None
        
        atr = talib.ATR(high.values, low.values, close.values, timeperiod=period)
        return atr[-1]
    
    def calculate_volatility(self, prices: pd.Series, period: int = 20) -> float:
        """Calcule la volatilité historique"""
        if len(prices) < period + 1:
            return None
        
        returns = prices.pct_change().dropna()
        return returns.rolling(window=period).std().iloc[-1] * np.sqrt(252)  # Annualisée
    
    def calculate_volume_indicators(self, volume: pd.Series, close: pd.Series, period: int = 20) -> Dict[str, float]:
        """Calcule les indicateurs de volume"""
        if len(volume) < period:
            return {'volume_sma_20': None, 'volume_ratio': None, 'obv': None, 'vwap': None}
        
        volume_sma = volume.rolling(window=period).mean().iloc[-1]
        volume_ratio = volume.iloc[-1] / volume_sma if volume_sma > 0 else None
        
        # OBV (On Balance Volume)
        obv = talib.OBV(close.values, volume.values)
        
        # VWAP (Volume Weighted Average Price) - approximation
        vwap = (close * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()
        
        return {
            'volume_sma_20': volume_sma,
            'volume_ratio': volume_ratio,
            'obv': obv[-1],
            'vwap': vwap.iloc[-1]
        }
    
    def detect_candlestick_patterns(self, open_price: pd.Series, high: pd.Series, low: pd.Series, close: pd.Series) -> Dict[str, bool]:
        """Détecte les patterns de chandeliers"""
        if len(close) < 2:
            return {'doji': False, 'hammer': False, 'shooting_star': False, 'engulfing_bullish': False, 'engulfing_bearish': False}
        
        # Doji
        doji = abs(close.iloc[-1] - open_price.iloc[-1]) <= (high.iloc[-1] - low.iloc[-1]) * 0.1
        
        # Hammer
        hammer = (close.iloc[-1] > open_price.iloc[-1]) and \
                (close.iloc[-1] - low.iloc[-1]) > 2 * (high.iloc[-1] - close.iloc[-1]) and \
                (high.iloc[-1] - close.iloc[-1]) < (close.iloc[-1] - low.iloc[-1]) * 0.3
        
        # Shooting Star
        shooting_star = (open_price.iloc[-1] > close.iloc[-1]) and \
                       (high.iloc[-1] - open_price.iloc[-1]) > 2 * (open_price.iloc[-1] - low.iloc[-1]) and \
                       (open_price.iloc[-1] - low.iloc[-1]) < (high.iloc[-1] - open_price.iloc[-1]) * 0.3
        
        # Engulfing patterns (nécessite 2 bougies)
        if len(close) >= 2:
            engulfing_bullish = (close.iloc[-1] > open_price.iloc[-1]) and \
                               (open_price.iloc[-2] > close.iloc[-2]) and \
                               (open_price.iloc[-1] < close.iloc[-2]) and \
                               (close.iloc[-1] > open_price.iloc[-2])
            
            engulfing_bearish = (open_price.iloc[-1] > close.iloc[-1]) and \
                               (close.iloc[-2] > open_price.iloc[-2]) and \
                               (close.iloc[-1] < open_price.iloc[-2]) and \
                               (open_price.iloc[-1] > close.iloc[-2])
        else:
            engulfing_bullish = False
            engulfing_bearish = False
        
        return {
            'doji': doji,
            'hammer': hammer,
            'shooting_star': shooting_star,
            'engulfing_bullish': engulfing_bullish,
            'engulfing_bearish': engulfing_bearish
        }
    
    def calculate_support_resistance(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 20) -> Dict[str, float]:
        """Calcule les niveaux de support et résistance"""
        if len(close) < period:
            return {'support_level': None, 'resistance_level': None, 'pivot_point': None}
        
        recent_highs = high.rolling(window=period).max().iloc[-1]
        recent_lows = low.rolling(window=period).min().iloc[-1]
        pivot = (recent_highs + recent_lows + close.iloc[-1]) / 3
        
        return {
            'support_level': recent_lows,
            'resistance_level': recent_highs,
            'pivot_point': pivot
        }
    
    def calculate_all_indicators(self, symbol: str, start_date: str = '2025-01-01') -> pd.DataFrame:
        """Calcule tous les indicateurs techniques pour un symbole"""
        df = self.get_historical_data(symbol, start_date)
        
        if df.empty:
            return pd.DataFrame()
        
        indicators_data = []
        
        # Calculer les indicateurs pour chaque date (fenêtre glissante)
        for i in range(50, len(df)):  # Commencer après 50 jours pour avoir assez de données
            current_data = df.iloc[:i+1]
            
            # Indicateurs de base
            sma_values = self.calculate_sma(current_data['close'], [5, 10, 20, 50, 200])
            ema_values = self.calculate_ema(current_data['close'], [5, 10, 20, 50, 200])
            rsi_values = self.calculate_rsi(current_data['close'], [14, 21])
            bollinger = self.calculate_bollinger_bands(current_data['close'])
            macd = self.calculate_macd(current_data['close'])
            stochastic = self.calculate_stochastic(current_data['high'], current_data['low'], current_data['close'])
            
            # Indicateurs avancés
            atr = self.calculate_atr(current_data['high'], current_data['low'], current_data['close'])
            volatility = self.calculate_volatility(current_data['close'])
            volume_indicators = self.calculate_volume_indicators(current_data['volume'], current_data['close'])
            candlestick_patterns = self.detect_candlestick_patterns(current_data['open'], current_data['high'], 
                                                                  current_data['low'], current_data['close'])
            support_resistance = self.calculate_support_resistance(current_data['high'], current_data['low'], current_data['close'])
            
            # Combiner tous les indicateurs
            indicators = {
                'symbol': symbol,
                'date': current_data['date'].iloc[-1],
                **sma_values,
                **ema_values,
                **rsi_values,
                **bollinger,
                **macd,
                **stochastic,
                'atr_14': atr,
                'volatility_20': volatility,
                **volume_indicators,
                **candlestick_patterns,
                **support_resistance
            }
            
            indicators_data.append(indicators)
        
        return pd.DataFrame(indicators_data)
    
    def save_indicators_to_db(self, indicators_df: pd.DataFrame):
        """Sauvegarde les indicateurs dans la base de données"""
        if indicators_df.empty:
            return
        
        cur = self.conn.cursor()
        
        for _, row in indicators_df.iterrows():
            # Préparer les données pour l'insertion
            columns = list(row.index)
            values = [row[col] for col in columns]
            placeholders = ', '.join(['%s'] * len(values))
            
            # Requête d'insertion avec gestion des conflits
            query = f"""
            INSERT INTO advanced_technical_indicators ({', '.join(columns)})
            VALUES ({placeholders})
            ON CONFLICT (symbol, date) DO UPDATE SET
                {', '.join([f'{col} = EXCLUDED.{col}' for col in columns if col not in ['symbol', 'date']])},
                updated_at = CURRENT_TIMESTAMP
            """
            
            cur.execute(query, values)
        
        self.conn.commit()
        cur.close()
    
    def process_all_symbols(self, start_date: str = '2025-01-01'):
        """Traite tous les symboles disponibles"""
        cur = self.conn.cursor()
        
        # Récupérer tous les symboles uniques
        cur.execute("""
            SELECT DISTINCT symbol 
            FROM historical_data 
            WHERE date >= %s
            ORDER BY symbol
        """, (start_date,))
        
        symbols = [row[0] for row in cur.fetchall()]
        cur.close()
        
        print(f"🔄 Traitement de {len(symbols)} symboles...")
        
        for i, symbol in enumerate(symbols, 1):
            try:
                print(f"  [{i}/{len(symbols)}] Traitement de {symbol}...")
                
                indicators_df = self.calculate_all_indicators(symbol, start_date)
                
                if not indicators_df.empty:
                    self.save_indicators_to_db(indicators_df)
                    print(f"    ✅ {len(indicators_df)} indicateurs calculés et sauvegardés")
                else:
                    print(f"    ⚠️ Aucune donnée pour {symbol}")
                    
            except Exception as e:
                print(f"    ❌ Erreur pour {symbol}: {str(e)}")
        
        print("✅ Traitement terminé!")
    
    def close(self):
        """Ferme la connexion à la base de données"""
        self.conn.close()

def main():
    """Fonction principale"""
    print("🚀 Démarrage du calcul des indicateurs techniques avancés...")
    
    calculator = AdvancedTechnicalIndicators()
    
    try:
        # Traiter tous les symboles depuis janvier 2025
        calculator.process_all_symbols('2025-01-01')
        
        # Vérifier les résultats
        cur = calculator.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM advanced_technical_indicators")
        count = cur.fetchone()[0]
        print(f"\\n📊 Total d'indicateurs calculés: {count:,}")
        
        cur.close()
        
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
    finally:
        calculator.close()

if __name__ == "__main__":
    main()
