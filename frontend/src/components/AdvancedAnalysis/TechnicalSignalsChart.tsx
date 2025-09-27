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
  Bar 
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
  signal_strength: number;
}

interface SignalData {
  signal_type: string;
  strength: number;
  direction: 'bullish' | 'bearish' | 'neutral';
  timestamp: string;
}

const TechnicalSignalsChart: React.FC<TechnicalSignalsChartProps> = ({ symbol, className = '' }) => {
  const [technicalData, setTechnicalData] = useState<TechnicalData[]>([]);
  const [signals, setSignals] = useState<SignalData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedIndicator, setSelectedIndicator] = useState<'rsi' | 'macd' | 'bollinger' | 'signals'>('rsi');

  useEffect(() => {
    fetchTechnicalData();
  }, [symbol]);

  const fetchTechnicalData = async () => {
    try {
      setLoading(true);
      const data = await advancedAnalysisApi.getTechnicalAnalysis(symbol);
      
      // Simuler des données pour la démonstration
      const mockData = generateMockTechnicalData();
      setTechnicalData(mockData);
      
      const mockSignals = generateMockSignals();
      setSignals(mockSignals);
      
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
        signal_strength: Math.random() * 100
      });
    }
    return data;
  };

  const generateMockSignals = (): SignalData[] => {
    const signalTypes = ['RSI Oversold', 'MACD Bullish', 'Bollinger Breakout', 'Volume Spike'];
    const directions: ('bullish' | 'bearish' | 'neutral')[] = ['bullish', 'bearish', 'neutral'];
    
    return signalTypes.map((type, index) => ({
      signal_type: type,
      strength: 60 + Math.random() * 40,
      direction: directions[index % 3],
      timestamp: new Date(Date.now() - Math.random() * 7 * 24 * 60 * 60 * 1000).toISOString()
    }));
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
      default: return '#6b7280';
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
        <div className="flex space-x-2">
          {['rsi', 'macd', 'bollinger', 'signals'].map((indicator) => (
            <button
              key={indicator}
              onClick={() => setSelectedIndicator(indicator as any)}
              className={`px-3 py-1 rounded text-sm font-medium ${
                selectedIndicator === indicator
                  ? 'bg-blue-100 text-blue-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {indicator.charAt(0).toUpperCase() + indicator.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          {selectedIndicator === 'signals' ? (
            <BarChart data={signals}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="signal_type" />
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
            <LineChart data={technicalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              {selectedIndicator === 'rsi' && (
                <Line 
                  type="monotone" 
                  dataKey="rsi" 
                  stroke={getIndicatorColor('rsi')} 
                  strokeWidth={2}
                  name="RSI"
                />
              )}
              {selectedIndicator === 'macd' && (
                <Line 
                  type="monotone" 
                  dataKey="macd" 
                  stroke={getIndicatorColor('macd')} 
                  strokeWidth={2}
                  name="MACD"
                />
              )}
              {selectedIndicator === 'bollinger' && (
                <>
                  <Line 
                    type="monotone" 
                    dataKey="price" 
                    stroke="#1f2937" 
                    strokeWidth={2}
                    name="Prix"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="bollinger_upper" 
                    stroke={getIndicatorColor('bollinger')} 
                    strokeWidth={1}
                    strokeDasharray="5 5"
                    name="Bollinger Supérieur"
                  />
                  <Line 
                    type="monotone" 
                    dataKey="bollinger_lower" 
                    stroke={getIndicatorColor('bollinger')} 
                    strokeWidth={1}
                    strokeDasharray="5 5"
                    name="Bollinger Inférieur"
                  />
                </>
              )}
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Résumé des signaux */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
            <span className="text-sm font-medium text-green-800">Signaux Bullish</span>
          </div>
          <p className="text-2xl font-bold text-green-900 mt-1">
            {signals.filter(s => s.direction === 'bullish').length}
          </p>
        </div>
        
        <div className="bg-red-50 p-4 rounded-lg">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-red-500 rounded-full mr-2"></div>
            <span className="text-sm font-medium text-red-800">Signaux Bearish</span>
          </div>
          <p className="text-2xl font-bold text-red-900 mt-1">
            {signals.filter(s => s.direction === 'bearish').length}
          </p>
        </div>
        
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center">
            <div className="w-3 h-3 bg-gray-500 rounded-full mr-2"></div>
            <span className="text-sm font-medium text-gray-800">Signaux Neutres</span>
          </div>
          <p className="text-2xl font-bold text-gray-900 mt-1">
            {signals.filter(s => s.direction === 'neutral').length}
          </p>
        </div>
      </div>
    </div>
  );
};

export default TechnicalSignalsChart;
