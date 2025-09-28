// frontend/src/components/AdvancedAnalysis/TechnicalSignalsChart.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer, 
  BarChart, 
  Bar,
  Area,
  AreaChart,
  ComposedChart
} from 'recharts';
import { advancedAnalysisApi } from '@/services/advancedAnalysisApi';

interface TechnicalSignalsChartProps {
  symbol: string;
  className?: string;
}

interface TechnicalData {
  timestamp: string;
  rsi: number;
  macd: number;
  bollinger_upper: number;
  bollinger_lower: number;
  price: number;
  price_normalized: number;
  signal_strength: number;
  williams_r: number;
  cci: number;
  adx: number;
  parabolic_sar: number;
  ichimoku_tenkan: number;
  ichimoku_kijun: number;
  ichimoku_senkou_a: number;
  ichimoku_senkou_b: number;
  ichimoku_chikou: number;
  sma_20: number;
  sma_50: number;
}

interface SignalData {
  signal_type: string;
  strength: number;
  direction: 'bullish' | 'bearish' | 'neutral';
  timestamp: string;
}

interface PriceInfo {
  current_price: number;
  previous_price: number;
  price_change: number;
  price_change_percent: number;
  last_update: string;
}

const TechnicalSignalsChart: React.FC<TechnicalSignalsChartProps> = ({ symbol, className = '' }) => {
  const [technicalData, setTechnicalData] = useState<TechnicalData[]>([]);
  const [signals, setSignals] = useState<SignalData[]>([]);
  const [priceInfo, setPriceInfo] = useState<PriceInfo | null>(null);
  const [supportResistanceData, setSupportResistanceData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndicator, setSelectedIndicator] = useState<'rsi' | 'macd' | 'bollinger' | 'williams_r' | 'cci' | 'adx' | 'parabolic_sar' | 'ichimoku' | 'sma' | 'support_resistance' | 'signals'>('rsi');
  const [historicalDepth, setHistoricalDepth] = useState<'5d' | '10d' | '1m' | '3m' | '6m' | '1y'>('1m');

  useEffect(() => {
    fetchTechnicalData();
  }, [symbol, historicalDepth]);

  const fetchTechnicalData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:8000/api/v1/technical-analysis/signals/${symbol}?period=${historicalDepth}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Convertir les données de l'API en format pour le graphique
      const chartData = convertApiDataToChartData(data);
      setTechnicalData(chartData);
      
      // Calculer les signaux à partir des indicateurs
      const calculatedSignals = calculateSignalsFromIndicators(data);
      setSignals(calculatedSignals);
      
      // Extraire les informations de prix
      const currentPrice = data.current_price || 0;
      const previousPrice = data.previous_price || null;
      const priceChange = previousPrice ? currentPrice - previousPrice : 0;
      const priceChangePercent = previousPrice ? (priceChange / previousPrice) * 100 : 0;
      
      const priceData: PriceInfo = {
        current_price: currentPrice,
        previous_price: previousPrice || 0,
        price_change: priceChange,
        price_change_percent: priceChangePercent,
        last_update: data.last_update || new Date().toISOString()
      };
      setPriceInfo(priceData);
      
      // Extraire les données de support/résistance
      setSupportResistanceData(data.support_resistance || null);
      
    } catch (err) {
      setError('Erreur lors du chargement des données techniques');
      console.error('Error fetching technical data:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateMockTechnicalData = (): TechnicalData[] => {
    const data = [];
    const basePrice = 150;
    const baseDate = new Date();
    
    for (let i = 0; i < 30; i++) {
      const date = new Date(baseDate);
      date.setDate(date.getDate() - (29 - i));
      
      data.push({
        timestamp: date.toISOString().split('T')[0],
        rsi: 30 + Math.random() * 40,
        macd: -2 + Math.random() * 4,
        bollinger_upper: basePrice + 5 + Math.random() * 10,
        bollinger_lower: basePrice - 5 - Math.random() * 10,
        price: basePrice + (Math.random() - 0.5) * 20,
        price_normalized: 0, // Sera calculé après
        signal_strength: Math.random() * 100,
        williams_r: -80 + Math.random() * 60,
        cci: -200 + Math.random() * 400,
        adx: 10 + Math.random() * 40,
        parabolic_sar: basePrice + (Math.random() - 0.5) * 10,
        ichimoku_tenkan: basePrice + (Math.random() - 0.5) * 8,
        ichimoku_kijun: basePrice + (Math.random() - 0.5) * 6,
        ichimoku_senkou_a: basePrice + (Math.random() - 0.5) * 4,
        ichimoku_senkou_b: basePrice + (Math.random() - 0.5) * 4,
        ichimoku_chikou: basePrice + (Math.random() - 0.5) * 3,
        sma_20: basePrice + (Math.random() - 0.5) * 5,
        sma_50: basePrice + (Math.random() - 0.5) * 7
      });
    }
    return data;
  };

  const convertApiDataToChartData = (apiData: any): TechnicalData[] => {
    // Utiliser les vraies séries de données de l'API
    const indicators = apiData.indicators || {};
    const historicalPrices = apiData.historical_prices?.series || [];
    
    const data = [];
    
    // Fonction helper pour récupérer la valeur d'un indicateur à une date donnée
    const getIndicatorValue = (series: any[], date: string, fallback: number = 0) => {
      const point = series.find(p => p.date === date);
      return point ? point.value : fallback;
    };
    
    // Utiliser les prix historiques comme base
    // Adapter le nombre de points selon la période sélectionnée
    const maxPoints = {
      '5d': 5,
      '10d': 10,
      '1m': 30,
      '3m': 90,
      '6m': 180,
      '1y': 365
    }[historicalDepth] || 50;
    
    for (const pricePoint of historicalPrices.slice(-maxPoints)) { // Points selon la période
      const date = pricePoint.date;
      const price = pricePoint.close;
      
      data.push({
        timestamp: date,
        rsi: getIndicatorValue(indicators.rsi?.series || [], date, 50),
        macd: getIndicatorValue(indicators.macd?.series?.macd || [], date, 0),
        bollinger_upper: getIndicatorValue(indicators.bollinger_bands?.series?.upper || [], date, price * 1.02),
        bollinger_lower: getIndicatorValue(indicators.bollinger_bands?.series?.lower || [], date, price * 0.98),
        price: price,
        price_normalized: 0, // Sera calculé après normalisation
        signal_strength: Math.random() * 100, // Garder simulé pour l'instant
        williams_r: getIndicatorValue(indicators.williams_r?.series || [], date, -50),
        cci: getIndicatorValue(indicators.cci?.series || [], date, 0),
        adx: getIndicatorValue(indicators.adx?.series?.adx || [], date, 25),
        parabolic_sar: getIndicatorValue(indicators.parabolic_sar?.series || [], date, price),
        ichimoku_tenkan: getIndicatorValue(indicators.ichimoku?.series?.tenkan_sen || [], date, price),
        ichimoku_kijun: getIndicatorValue(indicators.ichimoku?.series?.kijun_sen || [], date, price),
        ichimoku_senkou_a: getIndicatorValue(indicators.ichimoku?.series?.senkou_span_a || [], date, price),
        ichimoku_senkou_b: getIndicatorValue(indicators.ichimoku?.series?.senkou_span_b || [], date, price),
        ichimoku_chikou: getIndicatorValue(indicators.ichimoku?.series?.chikou_span || [], date, price),
        sma_20: getIndicatorValue(indicators.sma_20?.series || [], date, price),
        sma_50: getIndicatorValue(indicators.sma_50?.series || [], date, price)
      });
    }
    
    // Normaliser les prix en pourcentage par rapport au dernier prix
    if (data.length > 0) {
      const lastPrice = data[data.length - 1].price;
      data.forEach(point => {
        point.price_normalized = ((point.price - lastPrice) / lastPrice) * 100;
      });
    }
    
    return data;
  };

  // Fonction pour préparer les données du nuage Ichimoku
  const prepareIchimokuCloudData = (data: TechnicalData[]) => {
    const cloudBull = [];
    const cloudBear = [];
    
    for (let i = 0; i < data.length; i++) {
      const d = data[i];
      const a = d.ichimoku_senkou_a;
      const b = d.ichimoku_senkou_b;
      const row = { ...d };

      if (a != null && b != null) {
        if (a >= b) {
          // Zone haussière : on peuple bull, on "casse" bear
          cloudBull.push({
            ...row,
            upper: a,
            lower: b,
          });
          cloudBear.push({
            ...row,
            upper: undefined,
            lower: undefined,
          });
        } else {
          // Zone baissière : on peuple bear, on "casse" bull
          cloudBull.push({
            ...row,
            upper: undefined,
            lower: undefined,
          });
          cloudBear.push({
            ...row,
            upper: b,
            lower: a,
          });
        }
      } else {
        cloudBull.push({ ...row, upper: undefined, lower: undefined });
        cloudBear.push({ ...row, upper: undefined, lower: undefined });
      }
    }
    
    return { cloudBull, cloudBear };
  };

  const calculateSignalsFromIndicators = (apiData: any): SignalData[] => {
    const indicators = apiData.indicators || {};
    const signals: SignalData[] = [];
    
    // RSI Signal
    if (indicators.rsi?.current !== undefined && indicators.rsi.current !== null) {
      const rsi = indicators.rsi.current;
      let direction: 'bullish' | 'bearish' | 'neutral' = 'neutral';
      if (rsi < 30) direction = 'bullish';
      else if (rsi > 70) direction = 'bearish';
      
      signals.push({
        signal_type: 'RSI',
        strength: Math.abs(rsi - 50) * 2, // Force basée sur l'écart à 50
        direction,
        timestamp: new Date().toISOString()
      });
    }
    
    // MACD Signal
    if (indicators.macd?.current?.histogram !== undefined && indicators.macd.current.histogram !== null) {
      const histogram = indicators.macd.current.histogram;
      let direction: 'bullish' | 'bearish' | 'neutral' = 'neutral';
      if (histogram > 0) direction = 'bullish';
      else if (histogram < 0) direction = 'bearish';
      
      signals.push({
        signal_type: 'MACD',
        strength: Math.abs(histogram) * 50,
        direction,
        timestamp: new Date().toISOString()
      });
    }
    
    // Williams %R Signal
    if (indicators.williams_r?.current !== undefined && indicators.williams_r.current !== null) {
      const williams_r = indicators.williams_r.current;
      let direction: 'bullish' | 'bearish' | 'neutral' = 'neutral';
      if (williams_r < -80) direction = 'bullish';
      else if (williams_r > -20) direction = 'bearish';
      
      signals.push({
        signal_type: 'Williams %R',
        strength: Math.abs(williams_r + 50) * 2,
        direction,
        timestamp: new Date().toISOString()
      });
    }
    
    // CCI Signal
    if (indicators.cci?.current !== undefined && indicators.cci.current !== null) {
      const cci = indicators.cci.current;
      let direction: 'bullish' | 'bearish' | 'neutral' = 'neutral';
      if (cci > 100) direction = 'bullish';
      else if (cci < -100) direction = 'bearish';
      
      signals.push({
        signal_type: 'CCI',
        strength: Math.abs(cci) / 2,
        direction,
        timestamp: new Date().toISOString()
      });
    }
    
    // ADX Signal
    if (indicators.adx?.current?.adx !== undefined && indicators.adx.current.adx !== null) {
      const adx = indicators.adx.current.adx;
      const plus_di = indicators.adx.current.plus_di || 0;
      const minus_di = indicators.adx.current.minus_di || 0;
      
      let direction: 'bullish' | 'bearish' | 'neutral' = 'neutral';
      if (adx > 25) {
        if (plus_di > minus_di) direction = 'bullish';
        else if (minus_di > plus_di) direction = 'bearish';
      }
      
      signals.push({
        signal_type: 'ADX',
        strength: adx,
        direction,
        timestamp: new Date().toISOString()
      });
    }
    
    // Parabolic SAR Signal
    if (indicators.parabolic_sar?.current !== undefined && indicators.parabolic_sar.current !== null) {
      const sar = indicators.parabolic_sar.current;
      const currentPrice = apiData.current_price || 0;
      
      let direction: 'bullish' | 'bearish' | 'neutral' = 'neutral';
      if (currentPrice > sar) direction = 'bullish';
      else if (currentPrice < sar) direction = 'bearish';
      
      signals.push({
        signal_type: 'Parabolic SAR',
        strength: Math.abs(currentPrice - sar) / currentPrice * 100,
        direction,
        timestamp: new Date().toISOString()
      });
    }
    
    // Ichimoku Signal
    if (indicators.ichimoku?.current?.tenkan_sen !== undefined && indicators.ichimoku?.current?.kijun_sen !== undefined) {
      const tenkan = indicators.ichimoku.current.tenkan_sen;
      const kijun = indicators.ichimoku.current.kijun_sen;
      const currentPrice = apiData.current_price || 0;
      
      let direction: 'bullish' | 'bearish' | 'neutral' = 'neutral';
      if (currentPrice > tenkan && currentPrice > kijun) direction = 'bullish';
      else if (currentPrice < tenkan && currentPrice < kijun) direction = 'bearish';
      
      signals.push({
        signal_type: 'Ichimoku',
        strength: Math.abs(currentPrice - (tenkan + kijun) / 2) / currentPrice * 100,
        direction,
        timestamp: new Date().toISOString()
      });
    }
    
    return signals;
  };

  const getSignalColor = (direction: string) => {
    switch (direction) {
      case 'bullish': return '#10b981';
      case 'bearish': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getIndicatorColor = (indicator: string) => {
    switch (indicator) {
      case 'rsi': return '#3b82f6';
      case 'macd': return '#8b5cf6';
      case 'bollinger': return '#f59e0b';
      case 'williams_r': return '#10b981';
      case 'cci': return '#f97316';
      case 'adx': return '#ef4444';
      case 'parabolic_sar': return '#8b5cf6';
      case 'ichimoku': return '#06b6d4';
      case 'sma': return '#10b981';
      case 'support_resistance': return '#dc2626';
      default: return '#6b7280';
    }
  };

  const getSignalAnalysis = (): JSX.Element => {
    const bullishSignals = signals.filter(s => s.direction === 'bullish');
    const bearishSignals = signals.filter(s => s.direction === 'bearish');
    const neutralSignals = signals.filter(s => s.direction === 'neutral');
    
    const totalSignals = signals.length;
    const bullishPercentage = totalSignals > 0 ? (bullishSignals.length / totalSignals * 100).toFixed(0) : '0';
    const bearishPercentage = totalSignals > 0 ? (bearishSignals.length / totalSignals * 100).toFixed(0) : '0';
    const neutralPercentage = totalSignals > 0 ? (neutralSignals.length / totalSignals * 100).toFixed(0) : '0';
    
    const avgBullishStrength = bullishSignals.length > 0 ? 
      (bullishSignals.reduce((sum, s) => sum + s.strength, 0) / bullishSignals.length).toFixed(1) : '0';
    const avgBearishStrength = bearishSignals.length > 0 ? 
      (bearishSignals.reduce((sum, s) => sum + s.strength, 0) / bearishSignals.length).toFixed(1) : '0';
    
    return (
      <div className="space-y-2">
        <div className="grid grid-cols-2 gap-4 text-xs">
          <div>
            <span className="font-medium">Répartition:</span> {bullishPercentage}% Bullish, {bearishPercentage}% Bearish, {neutralPercentage}% Neutre
          </div>
          <div>
            <span className="font-medium">Force moyenne:</span> Bullish {avgBullishStrength}, Bearish {avgBearishStrength}
          </div>
        </div>
        
        {bullishSignals.length > bearishSignals.length && (
          <div className="text-green-700 font-medium">
            → Tendance haussière dominante avec {bullishSignals.map(s => s.signal_type).join(', ')}
          </div>
        )}
        
        {bearishSignals.length > bullishSignals.length && (
          <div className="text-red-700 font-medium">
            → Tendance baissière dominante avec {bearishSignals.map(s => s.signal_type).join(', ')}
          </div>
        )}
        
        {bullishSignals.length === bearishSignals.length && bullishSignals.length > 0 && (
          <div className="text-gray-700 font-medium">
            → Signaux équilibrés, marché indécis
          </div>
        )}
        
        {totalSignals === 0 && (
          <div className="text-gray-600">
            → Aucun signal technique disponible
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="text-red-600 text-center">
          <p>{error}</p>
          <button 
            onClick={fetchTechnicalData}
            className="mt-2 px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Signaux Techniques - {symbol}
        </h3>
        
        <div className="flex items-center space-x-4">
          {/* Sélecteur de profondeur historique */}
          <div className="flex items-center space-x-2">
            <label className="text-sm font-medium text-gray-700">Période:</label>
            <select
              value={historicalDepth}
              onChange={(e) => setHistoricalDepth(e.target.value as '5d' | '10d' | '1m' | '3m' | '6m' | '1y')}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="5d">5 jours</option>
              <option value="10d">10 jours</option>
              <option value="1m">1 mois</option>
              <option value="3m">3 mois</option>
              <option value="6m">6 mois</option>
              <option value="1y">1 an</option>
            </select>
          </div>
          
          {/* Informations de prix */}
          {priceInfo && (
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">
                ${priceInfo.current_price.toFixed(2)}
              </div>
              <div className="text-sm text-gray-600">
                {new Date(priceInfo.last_update).toLocaleDateString('fr-FR', {
                  day: '2-digit',
                  month: '2-digit',
                  year: 'numeric',
                  hour: '2-digit',
                  minute: '2-digit'
                })}
              </div>
              {priceInfo.previous_price > 0 ? (
                <div className={`text-sm font-medium ${
                  priceInfo.price_change >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {priceInfo.price_change >= 0 ? '+' : ''}{priceInfo.price_change.toFixed(2)} 
                  ({priceInfo.price_change_percent >= 0 ? '+' : ''}{priceInfo.price_change_percent.toFixed(2)}%)
                </div>
              ) : (
                <div className="text-sm text-gray-500">
                  Données précédentes indisponibles
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      <div className="flex flex-wrap gap-2 mb-6">
          {[
            { key: 'rsi', label: 'RSI' },
            { key: 'macd', label: 'MACD' },
            { key: 'bollinger', label: 'Bollinger' },
            { key: 'williams_r', label: 'Williams %R' },
            { key: 'cci', label: 'CCI' },
            { key: 'adx', label: 'ADX' },
            { key: 'parabolic_sar', label: 'Parabolic SAR' },
            { key: 'ichimoku', label: 'Ichimoku' },
            { key: 'sma', label: 'SMA' },
            { key: 'support_resistance', label: 'Support/Résistance' },
            { key: 'signals', label: 'Signals' }
          ].map((indicator) => (
            <button
              key={indicator.key}
              onClick={() => setSelectedIndicator(indicator.key as any)}
              className={`px-3 py-1 rounded text-sm font-medium ${
                selectedIndicator === indicator.key
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {indicator.label}
            </button>
          ))}
      </div>

      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          {selectedIndicator === 'signals' ? (
            <BarChart data={signals}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="signal_type" 
                tick={{ fontSize: 10 }}
              />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar 
                dataKey="strength" 
                fill="#3b82f6"
                name="Force du Signal"
              />
            </BarChart>
          ) : (
            <ComposedChart data={technicalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="timestamp" 
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis yAxisId="main" />
              <YAxis 
                yAxisId="price" 
                orientation="right" 
                domain={['dataMin - 10', 'dataMax + 10']}
                allowDataOverflow={false}
              />
              <Tooltip />
              <Legend 
                payload={selectedIndicator === 'bollinger' ? [
                  { value: 'Prix', type: 'line', color: '#1f2937' },
                  { value: 'Bollinger Supérieur', type: 'line', color: getIndicatorColor('bollinger') },
                  { value: 'Bollinger Inférieur', type: 'line', color: getIndicatorColor('bollinger') }
                ] : undefined}
              />
              {selectedIndicator === 'rsi' && (
                <>
                <Line 
                  type="monotone" 
                  dataKey="rsi" 
                  stroke={getIndicatorColor('rsi')} 
                  strokeWidth={2}
                  name="RSI"
                    yAxisId="main"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="price_normalized" 
                    stroke="#1f2937" 
                    strokeWidth={1}
                    strokeDasharray="2 2"
                    name="Prix (normalisé)"
                    yAxisId="price"
                    dot={false}
                  />
                </>
              )}
              {selectedIndicator === 'macd' && (
                <>
                <Line 
                  type="monotone" 
                  dataKey="macd" 
                  stroke={getIndicatorColor('macd')} 
                  strokeWidth={2}
                  name="MACD"
                    yAxisId="main"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="price_normalized" 
                    stroke="#1f2937" 
                    strokeWidth={1}
                    strokeDasharray="2 2"
                    name="Prix (normalisé)"
                    yAxisId="price"
                    dot={false}
                  />
                </>
              )}
              {selectedIndicator === 'bollinger' && (
                <>
                  {/* Zone colorisée entre les bandes de Bollinger */}
                  <Area
                    type="monotone"
                    dataKey="bollinger_upper"
                    stroke="none"
                    fill="#f59e0b"
                    fillOpacity={0.3}
                    yAxisId="price"
                    connectNulls={false}
                    isAnimationActive={false}
                  />
                  <Area
                    type="monotone"
                    dataKey="bollinger_lower"
                    stroke="none"
                    fill="#ffffff"
                    fillOpacity={1}
                    yAxisId="price"
                    connectNulls={false}
                    isAnimationActive={false}
                  />
                  
                  {/* Ligne de prix */}
                  <Line 
                    type="monotone" 
                    dataKey="price" 
                    stroke="#1f2937" 
                    strokeWidth={2}
                    name="Prix"
                    yAxisId="price"
                    dot={false}
                  />
                  
                  {/* Lignes des bandes de Bollinger */}
                  <Line 
                    type="monotone" 
                    dataKey="bollinger_upper" 
                    stroke={getIndicatorColor('bollinger')} 
                    strokeWidth={1}
                    strokeDasharray="5 5"
                    name="Bollinger Supérieur"
                    yAxisId="price"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="bollinger_lower" 
                    stroke={getIndicatorColor('bollinger')} 
                    strokeWidth={1}
                    strokeDasharray="5 5"
                    name="Bollinger Inférieur"
                    yAxisId="price"
                    dot={false}
                  />
                </>
              )}
              {selectedIndicator === 'williams_r' && (
                <>
                  <Line 
                    type="monotone" 
                    dataKey="williams_r" 
                    stroke={getIndicatorColor('williams_r')} 
                    strokeWidth={2}
                    name="Williams %R"
                    yAxisId="main"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="price_normalized" 
                    stroke="#1f2937" 
                    strokeWidth={1}
                    strokeDasharray="2 2"
                    name="Prix (normalisé)"
                    yAxisId="price"
                    dot={false}
                  />
                </>
              )}
              {selectedIndicator === 'cci' && (
                <>
                  <Line 
                    type="monotone" 
                    dataKey="cci" 
                    stroke={getIndicatorColor('cci')} 
                    strokeWidth={2}
                    name="CCI"
                    yAxisId="main"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="price_normalized" 
                    stroke="#1f2937" 
                    strokeWidth={1}
                    strokeDasharray="2 2"
                    name="Prix (normalisé)"
                    yAxisId="price"
                    dot={false}
                  />
                </>
              )}
              {selectedIndicator === 'adx' && (
                <Line 
                  type="monotone" 
                  dataKey="adx" 
                  stroke={getIndicatorColor('adx')} 
                  strokeWidth={2}
                  name="ADX"
                  yAxisId="main"
                  dot={false}
                />
              )}
              {selectedIndicator === 'parabolic_sar' && (
                <>
                  <Line 
                    type="monotone" 
                    dataKey="price" 
                    stroke="#1f2937" 
                    strokeWidth={2}
                    name="Prix"
                    yAxisId="price"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="parabolic_sar" 
                    stroke={getIndicatorColor('parabolic_sar')} 
                    strokeWidth={2}
                    strokeDasharray="3 3"
                    name="Parabolic SAR"
                    yAxisId="price"
                    dot={false}
                  />
                </>
              )}
              {selectedIndicator === 'ichimoku' && (
                <>
                  {/* Ligne de prix */}
                  <Line 
                    type="monotone" 
                    dataKey="price" 
                    stroke="#1f2937" 
                    strokeWidth={2}
                    name="Prix"
                    yAxisId="price"
                    dot={false}
                  />
                  
                  {/* Lignes Ichimoku */}
                  <Line 
                    type="monotone" 
                    dataKey="ichimoku_tenkan" 
                    stroke="#ef4444" 
                    strokeWidth={2}
                    name="Tenkan-sen"
                    yAxisId="price"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="ichimoku_kijun" 
                    stroke="#3b82f6" 
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    name="Kijun-sen"
                    yAxisId="price"
                    dot={false}
                  />
                  
                  {/* Senkou Span A avec zone de remplissage */}
                  <Line 
                    type="monotone" 
                    dataKey="ichimoku_senkou_a" 
                    stroke="#10b981" 
                    strokeWidth={2}
                    strokeDasharray="3 3"
                    name="Senkou Span A"
                    yAxisId="price"
                    fill="#10b981"
                    fillOpacity={0.4}
                    dot={false}
                  />
                  
                  {/* Senkou Span B avec zone de remplissage */}
                  <Line 
                    type="monotone" 
                    dataKey="ichimoku_senkou_b" 
                    stroke="#f59e0b" 
                    strokeWidth={2}
                    strokeDasharray="3 3"
                    name="Senkou Span B"
                    yAxisId="price"
                    fill="#f59e0b"
                    fillOpacity={0.4}
                    dot={false}
                  />
                  
                  <Line 
                    type="monotone" 
                    dataKey="ichimoku_chikou" 
                    stroke="#8b5cf6" 
                    strokeWidth={1}
                    strokeDasharray="2 2"
                    name="Chikou Span"
                    yAxisId="price"
                    dot={false}
                  />
                </>
              )}
              {selectedIndicator === 'sma' && (
                <>
                  <Line 
                    type="monotone" 
                    dataKey="price" 
                    stroke="#1f2937" 
                    strokeWidth={2}
                    name="Prix"
                    yAxisId="price"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="sma_20" 
                    stroke={getIndicatorColor('sma')} 
                    strokeWidth={2}
                    name="SMA 20"
                    yAxisId="price"
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="sma_50" 
                    stroke="#059669" 
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    name="SMA 50"
                    yAxisId="price"
                    dot={false}
                  />
                </>
              )}
              {selectedIndicator === 'support_resistance' && supportResistanceData && (
                <>
                  <Line 
                    type="monotone" 
                    dataKey="price" 
                    stroke="#1f2937" 
                    strokeWidth={2}
                    name="Prix"
                    yAxisId="price"
                    dot={false}
                  />
                  {/* Lignes de support */}
                  {supportResistanceData.support_levels && supportResistanceData.support_levels.map((level: number, index: number) => (
                    <Line 
                      key={`support-${index}`}
                      type="monotone" 
                      dataKey={() => level} 
                      stroke="#10b981" 
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name={`Support ${index + 1}`}
                      yAxisId="price"
                      dot={false}
                      connectNulls={false}
                    />
                  ))}
                  {/* Lignes de résistance */}
                  {supportResistanceData.resistance_levels && supportResistanceData.resistance_levels.map((level: number, index: number) => (
                    <Line 
                      key={`resistance-${index}`}
                      type="monotone" 
                      dataKey={() => level} 
                      stroke="#ef4444" 
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      name={`Résistance ${index + 1}`}
                      yAxisId="price"
                      dot={false}
                      connectNulls={false}
                    />
                  ))}
                  {/* Points pivots */}
                  {supportResistanceData.pivot_points && (
                    <>
                      {supportResistanceData.pivot_points.pivot && (
                        <Line 
                          type="monotone" 
                          dataKey={() => supportResistanceData.pivot_points.pivot} 
                          stroke="#8b5cf6" 
                          strokeWidth={2}
                          strokeDasharray="3 3"
                          name="Pivot"
                          yAxisId="price"
                          dot={false}
                          connectNulls={false}
                        />
                      )}
                      {supportResistanceData.pivot_points.r1 && (
                        <Line 
                          type="monotone" 
                          dataKey={() => supportResistanceData.pivot_points.r1} 
                          stroke="#f59e0b" 
                          strokeWidth={1}
                          strokeDasharray="2 2"
                          name="R1"
                          yAxisId="price"
                          dot={false}
                          connectNulls={false}
                        />
                      )}
                      {supportResistanceData.pivot_points.r2 && (
                        <Line 
                          type="monotone" 
                          dataKey={() => supportResistanceData.pivot_points.r2} 
                          stroke="#f59e0b" 
                          strokeWidth={1}
                          strokeDasharray="2 2"
                          name="R2"
                          yAxisId="price"
                          dot={false}
                          connectNulls={false}
                        />
                      )}
                      {supportResistanceData.pivot_points.s1 && (
                        <Line 
                          type="monotone" 
                          dataKey={() => supportResistanceData.pivot_points.s1} 
                          stroke="#06b6d4" 
                          strokeWidth={1}
                          strokeDasharray="2 2"
                          name="S1"
                          yAxisId="price"
                          dot={false}
                          connectNulls={false}
                        />
                      )}
                      {supportResistanceData.pivot_points.s2 && (
                        <Line 
                          type="monotone" 
                          dataKey={() => supportResistanceData.pivot_points.s2} 
                          stroke="#06b6d4" 
                          strokeWidth={1}
                          strokeDasharray="2 2"
                          name="S2"
                          yAxisId="price"
                          dot={false}
                          connectNulls={false}
                        />
                      )}
                    </>
                  )}
                </>
              )}
            </ComposedChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Résumé des signaux */}
      <div className="space-y-4">
        {/* Analyse synthétique */}
        <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-400">
          <h3 className="text-sm font-semibold text-blue-900 mb-2">Analyse Synthétique des Signaux</h3>
          <div className="text-xs text-blue-800 space-y-1">
            {getSignalAnalysis()}
          </div>
        </div>
        
        {/* Cartes des signaux */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
            <span className="text-sm font-medium text-green-800">Signaux Bullish</span>
          </div>
          <p className="text-2xl font-bold text-green-900 mt-1">
            {signals.filter(s => s.direction === 'bullish').length}
          </p>
          <div className="mt-2 text-xs text-green-700">
            {signals.filter(s => s.direction === 'bullish').map(signal => (
              <div key={signal.signal_type} className="flex justify-between">
                <span>{signal.signal_type}:</span>
                <span className="font-medium">{isNaN(signal.strength) ? 'N/A' : signal.strength.toFixed(1)}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="bg-red-50 p-4 rounded-lg">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
            <span className="text-sm font-medium text-red-800">Signaux Bearish</span>
          </div>
          <p className="text-2xl font-bold text-red-900 mt-1">
            {signals.filter(s => s.direction === 'bearish').length}
          </p>
          <div className="mt-2 text-xs text-red-700">
            {signals.filter(s => s.direction === 'bearish').map(signal => (
              <div key={signal.signal_type} className="flex justify-between">
                <span>{signal.signal_type}:</span>
                <span className="font-medium">{isNaN(signal.strength) ? 'N/A' : signal.strength.toFixed(1)}</span>
              </div>
            ))}
          </div>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-gray-500 rounded-full mr-2"></div>
            <span className="text-sm font-medium text-gray-800">Signaux Neutres</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {signals.filter(s => s.direction === 'neutral').length}
          </p>
          <div className="mt-2 text-xs text-gray-700">
            {signals.filter(s => s.direction === 'neutral').map(signal => (
              <div key={signal.signal_type} className="flex justify-between">
                <span>{signal.signal_type}:</span>
                <span className="font-medium">{isNaN(signal.strength) ? 'N/A' : signal.strength.toFixed(1)}</span>
              </div>
            ))}
          </div>
        </div>
        </div>
      </div>
    </div>
  );
};

export default TechnicalSignalsChart;
