// frontend/src/components/AdvancedAnalysis/AdvancedTechnicalIndicators.tsx
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

interface AdvancedTechnicalIndicatorsProps {
  symbol: string;
  className?: string;
}

interface AdvancedTechnicalData {
  date: string;
  // Indicateurs TA-Lib avancés
  rsi_14: number;
  macd: number;
  macd_signal: number;
  macd_histogram: number;
  bb_upper: number;
  bb_middle: number;
  bb_lower: number;
  bb_position: number;
  williams_r: number;
  cci: number;
  adx: number;
  plus_di: number;
  minus_di: number;
  sar: number;
  mfi_14: number;
  midpoint_20: number;
  midprice_20: number;
  obv_price_divergence: number;
  t3_20: number;
  vpt: number;
  wad: number;
  momentum_composite: number;
  volatility_composite: number;
  trend_strength: number;
  price: number;
}

const AdvancedTechnicalIndicators: React.FC<AdvancedTechnicalIndicatorsProps> = ({ 
  symbol, 
  className = '' 
}) => {
  const [technicalData, setTechnicalData] = useState<AdvancedTechnicalData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndicator, setSelectedIndicator] = useState<'rsi' | 'macd' | 'bollinger' | 'williams_r' | 'cci' | 'adx' | 'sar' | 'mfi' | 'momentum' | 'volatility' | 'trend'>('rsi');
  const [historicalDepth, setHistoricalDepth] = useState<'5d' | '10d' | '1m' | '3m' | '6m' | '1y'>('1m');

  useEffect(() => {
    fetchAdvancedTechnicalData();
  }, [symbol, historicalDepth]);

  const fetchAdvancedTechnicalData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Appel à l'API pour récupérer les indicateurs techniques avancés
      const response = await fetch(`/api/v1/technical-analysis/advanced-indicators/${symbol}?period=${historicalDepth}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      // Convertir les données de l'API en format pour le graphique
      const chartData = convertApiDataToChartData(data);
      setTechnicalData(chartData);
      
    } catch (err) {
      setError('Erreur lors du chargement des indicateurs techniques avancés');
      console.error('Error fetching advanced technical data:', err);
      
      // Générer des données de démonstration en cas d'erreur
      setTechnicalData(generateMockAdvancedTechnicalData());
    } finally {
      setLoading(false);
    }
  };

  const generateMockAdvancedTechnicalData = (): AdvancedTechnicalData[] => {
    const data = [];
    const basePrice = 150;
    const baseDate = new Date();
    
    for (let i = 0; i < 30; i++) {
      const date = new Date(baseDate);
      date.setDate(date.getDate() - (29 - i));
      
      data.push({
        date: date.toISOString().split('T')[0],
        rsi_14: 30 + Math.random() * 40,
        macd: -2 + Math.random() * 4,
        macd_signal: -1.5 + Math.random() * 3,
        macd_histogram: -0.5 + Math.random() * 1,
        bb_upper: basePrice + 5 + Math.random() * 10,
        bb_middle: basePrice + (Math.random() - 0.5) * 5,
        bb_lower: basePrice - 5 - Math.random() * 10,
        bb_position: Math.random(),
        williams_r: -80 + Math.random() * 60,
        cci: -200 + Math.random() * 400,
        adx: 10 + Math.random() * 40,
        plus_di: 10 + Math.random() * 30,
        minus_di: 10 + Math.random() * 30,
        sar: basePrice + (Math.random() - 0.5) * 10,
        mfi_14: 20 + Math.random() * 60,
        midpoint_20: basePrice + (Math.random() - 0.5) * 3,
        midprice_20: basePrice + (Math.random() - 0.5) * 3,
        obv_price_divergence: -0.1 + Math.random() * 0.2,
        t3_20: basePrice + (Math.random() - 0.5) * 4,
        vpt: basePrice * 1000 + (Math.random() - 0.5) * 10000,
        wad: (Math.random() - 0.5) * 1000,
        momentum_composite: -0.5 + Math.random() * 1,
        volatility_composite: 0.1 + Math.random() * 0.3,
        trend_strength: 0.2 + Math.random() * 0.6,
        price: basePrice + (Math.random() - 0.5) * 20
      });
    }
    return data;
  };

  const convertApiDataToChartData = (apiData: any): AdvancedTechnicalData[] => {
    // Cette fonction convertira les données de l'API réelle
    // Pour l'instant, on utilise les données mock
    return generateMockAdvancedTechnicalData();
  };

  const getIndicatorColor = (indicator: string) => {
    switch (indicator) {
      case 'rsi': return '#3b82f6';
      case 'macd': return '#8b5cf6';
      case 'bollinger': return '#f59e0b';
      case 'williams_r': return '#10b981';
      case 'cci': return '#f97316';
      case 'adx': return '#ef4444';
      case 'sar': return '#8b5cf6';
      case 'mfi': return '#06b6d4';
      case 'momentum': return '#10b981';
      case 'volatility': return '#f59e0b';
      case 'trend': return '#3b82f6';
      default: return '#6b7280';
    }
  };

  const getCurrentIndicatorValue = () => {
    if (technicalData.length === 0) return null;
    const latest = technicalData[technicalData.length - 1];
    
    switch (selectedIndicator) {
      case 'rsi': return latest.rsi_14;
      case 'macd': return latest.macd;
      case 'bollinger': return latest.bb_position;
      case 'williams_r': return latest.williams_r;
      case 'cci': return latest.cci;
      case 'adx': return latest.adx;
      case 'sar': return latest.sar;
      case 'mfi': return latest.mfi_14;
      case 'momentum': return latest.momentum_composite;
      case 'volatility': return latest.volatility_composite;
      case 'trend': return latest.trend_strength;
      default: return null;
    }
  };

  const getIndicatorInterpretation = (indicator: string, value: number) => {
    switch (indicator) {
      case 'rsi':
        if (value < 30) return { text: 'Survente', color: 'text-green-600' };
        if (value > 70) return { text: 'Surachat', color: 'text-red-600' };
        return { text: 'Neutre', color: 'text-gray-600' };
      
      case 'macd':
        if (value > 0) return { text: 'Signal haussier', color: 'text-green-600' };
        return { text: 'Signal baissier', color: 'text-red-600' };
      
      case 'bollinger':
        if (value > 0.8) return { text: 'Proche résistance', color: 'text-red-600' };
        if (value < 0.2) return { text: 'Proche support', color: 'text-green-600' };
        return { text: 'Zone neutre', color: 'text-gray-600' };
      
      case 'williams_r':
        if (value < -80) return { text: 'Survente', color: 'text-green-600' };
        if (value > -20) return { text: 'Surachat', color: 'text-red-600' };
        return { text: 'Neutre', color: 'text-gray-600' };
      
      case 'cci':
        if (value > 100) return { text: 'Signal haussier', color: 'text-green-600' };
        if (value < -100) return { text: 'Signal baissier', color: 'text-red-600' };
        return { text: 'Neutre', color: 'text-gray-600' };
      
      case 'adx':
        if (value > 25) return { text: 'Tendance forte', color: 'text-blue-600' };
        return { text: 'Tendance faible', color: 'text-gray-600' };
      
      case 'momentum':
        if (value > 0.3) return { text: 'Momentum fort', color: 'text-green-600' };
        if (value < -0.3) return { text: 'Momentum faible', color: 'text-red-600' };
        return { text: 'Momentum neutre', color: 'text-gray-600' };
      
      case 'volatility':
        if (value > 0.3) return { text: 'Volatilité élevée', color: 'text-red-600' };
        return { text: 'Volatilité normale', color: 'text-green-600' };
      
      case 'trend':
        if (value > 0.6) return { text: 'Tendance forte', color: 'text-green-600' };
        if (value < 0.4) return { text: 'Tendance faible', color: 'text-red-600' };
        return { text: 'Tendance modérée', color: 'text-yellow-600' };
      
      default:
        return { text: 'N/A', color: 'text-gray-600' };
    }
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
            onClick={fetchAdvancedTechnicalData}
            className="mt-2 px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  const currentValue = getCurrentIndicatorValue();
  const interpretation = currentValue ? getIndicatorInterpretation(selectedIndicator, currentValue) : null;

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Indicateurs Techniques Avancés TA-Lib - {symbol}
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
          
          {/* Valeur actuelle et interprétation */}
          {currentValue !== null && interpretation && (
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">
                {currentValue.toFixed(2)}
              </div>
              <div className={`text-sm font-medium ${interpretation.color}`}>
                {interpretation.text}
              </div>
            </div>
          )}
        </div>
      </div>
      
      <div className="flex flex-wrap gap-2 mb-6">
        {[
          { key: 'rsi', label: 'RSI (14)' },
          { key: 'macd', label: 'MACD' },
          { key: 'bollinger', label: 'Bollinger Position' },
          { key: 'williams_r', label: 'Williams %R' },
          { key: 'cci', label: 'CCI' },
          { key: 'adx', label: 'ADX' },
          { key: 'sar', label: 'Parabolic SAR' },
          { key: 'mfi', label: 'MFI (14)' },
          { key: 'momentum', label: 'Momentum Composite' },
          { key: 'volatility', label: 'Volatilité Composite' },
          { key: 'trend', label: 'Force Tendance' }
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
          <ComposedChart data={technicalData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
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
            />
            <Tooltip />
            <Legend />
            
            {selectedIndicator === 'rsi' && (
              <>
                <Line 
                  type="monotone" 
                  dataKey="rsi_14" 
                  stroke={getIndicatorColor('rsi')} 
                  strokeWidth={2}
                  name="RSI (14)"
                  yAxisId="main"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey={() => 70} 
                  stroke="#ef4444" 
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  name="Surachat (70)"
                  yAxisId="main"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey={() => 30} 
                  stroke="#10b981" 
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  name="Survente (30)"
                  yAxisId="main"
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
                  dataKey="macd_signal" 
                  stroke="#f59e0b" 
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  name="Signal"
                  yAxisId="main"
                  dot={false}
                />
                <Bar 
                  dataKey="macd_histogram" 
                  fill="#8b5cf6"
                  fillOpacity={0.6}
                  name="Histogramme"
                  yAxisId="main"
                />
              </>
            )}
            
            {selectedIndicator === 'bollinger' && (
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
                  dataKey="bb_upper" 
                  stroke={getIndicatorColor('bollinger')} 
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  name="Bollinger Supérieur"
                  yAxisId="price"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey="bb_middle" 
                  stroke="#6b7280" 
                  strokeWidth={1}
                  name="Bollinger Moyen"
                  yAxisId="price"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey="bb_lower" 
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
                  dataKey={() => -20} 
                  stroke="#ef4444" 
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  name="Surachat (-20)"
                  yAxisId="main"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey={() => -80} 
                  stroke="#10b981" 
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  name="Survente (-80)"
                  yAxisId="main"
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
                  dataKey={() => 100} 
                  stroke="#10b981" 
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  name="Signal Haussier (100)"
                  yAxisId="main"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey={() => -100} 
                  stroke="#ef4444" 
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  name="Signal Baissier (-100)"
                  yAxisId="main"
                  dot={false}
                />
              </>
            )}
            
            {selectedIndicator === 'adx' && (
              <>
                <Line 
                  type="monotone" 
                  dataKey="adx" 
                  stroke={getIndicatorColor('adx')} 
                  strokeWidth={2}
                  name="ADX"
                  yAxisId="main"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey="plus_di" 
                  stroke="#10b981" 
                  strokeWidth={2}
                  strokeDasharray="3 3"
                  name="+DI"
                  yAxisId="main"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey="minus_di" 
                  stroke="#ef4444" 
                  strokeWidth={2}
                  strokeDasharray="3 3"
                  name="-DI"
                  yAxisId="main"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey={() => 25} 
                  stroke="#6b7280" 
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  name="Tendance Forte (25)"
                  yAxisId="main"
                  dot={false}
                />
              </>
            )}
            
            {selectedIndicator === 'sar' && (
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
                  dataKey="sar" 
                  stroke={getIndicatorColor('sar')} 
                  strokeWidth={2}
                  strokeDasharray="3 3"
                  name="Parabolic SAR"
                  yAxisId="price"
                  dot={false}
                />
              </>
            )}
            
            {selectedIndicator === 'mfi' && (
              <>
                <Line 
                  type="monotone" 
                  dataKey="mfi_14" 
                  stroke={getIndicatorColor('mfi')} 
                  strokeWidth={2}
                  name="MFI (14)"
                  yAxisId="main"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey={() => 80} 
                  stroke="#ef4444" 
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  name="Surachat (80)"
                  yAxisId="main"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey={() => 20} 
                  stroke="#10b981" 
                  strokeWidth={1}
                  strokeDasharray="5 5"
                  name="Survente (20)"
                  yAxisId="main"
                  dot={false}
                />
              </>
            )}
            
            {selectedIndicator === 'momentum' && (
              <Line 
                type="monotone" 
                dataKey="momentum_composite" 
                stroke={getIndicatorColor('momentum')} 
                strokeWidth={2}
                name="Momentum Composite"
                yAxisId="main"
                dot={false}
              />
            )}
            
            {selectedIndicator === 'volatility' && (
              <Line 
                type="monotone" 
                dataKey="volatility_composite" 
                stroke={getIndicatorColor('volatility')} 
                strokeWidth={2}
                name="Volatilité Composite"
                yAxisId="main"
                dot={false}
              />
            )}
            
            {selectedIndicator === 'trend' && (
              <Line 
                type="monotone" 
                dataKey="trend_strength" 
                stroke={getIndicatorColor('trend')} 
                strokeWidth={2}
                name="Force Tendance"
                yAxisId="main"
                dot={false}
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Résumé des indicateurs */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg">
          <h4 className="text-sm font-semibold text-blue-900 mb-2">Indicateurs de Momentum</h4>
          <div className="space-y-1 text-xs text-blue-800">
            <div>RSI (14): {technicalData[technicalData.length - 1]?.rsi_14?.toFixed(1) || 'N/A'}</div>
            <div>Williams %R: {technicalData[technicalData.length - 1]?.williams_r?.toFixed(1) || 'N/A'}</div>
            <div>CCI: {technicalData[technicalData.length - 1]?.cci?.toFixed(1) || 'N/A'}</div>
            <div>MFI (14): {technicalData[technicalData.length - 1]?.mfi_14?.toFixed(1) || 'N/A'}</div>
          </div>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg">
          <h4 className="text-sm font-semibold text-green-900 mb-2">Indicateurs de Tendance</h4>
          <div className="space-y-1 text-xs text-green-800">
            <div>MACD: {technicalData[technicalData.length - 1]?.macd?.toFixed(3) || 'N/A'}</div>
            <div>ADX: {technicalData[technicalData.length - 1]?.adx?.toFixed(1) || 'N/A'}</div>
            <div>+DI: {technicalData[technicalData.length - 1]?.plus_di?.toFixed(1) || 'N/A'}</div>
            <div>-DI: {technicalData[technicalData.length - 1]?.minus_di?.toFixed(1) || 'N/A'}</div>
          </div>
        </div>
        
        <div className="bg-purple-50 p-4 rounded-lg">
          <h4 className="text-sm font-semibold text-purple-900 mb-2">Indicateurs Composés</h4>
          <div className="space-y-1 text-xs text-purple-800">
            <div>Momentum: {technicalData[technicalData.length - 1]?.momentum_composite?.toFixed(2) || 'N/A'}</div>
            <div>Volatilité: {technicalData[technicalData.length - 1]?.volatility_composite?.toFixed(2) || 'N/A'}</div>
            <div>Force Tendance: {technicalData[technicalData.length - 1]?.trend_strength?.toFixed(2) || 'N/A'}</div>
            <div>BB Position: {technicalData[technicalData.length - 1]?.bb_position?.toFixed(2) || 'N/A'}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedTechnicalIndicators;
