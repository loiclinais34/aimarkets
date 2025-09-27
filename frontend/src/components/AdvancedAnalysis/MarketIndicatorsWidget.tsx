// frontend/src/components/AdvancedAnalysis/MarketIndicatorsWidget.tsx
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
  RadialBarChart, 
  RadialBar 
} from 'recharts';
import { advancedAnalysisApi } from '@/services/advancedAnalysisApi';

interface MarketIndicatorsWidgetProps {
  symbol: string;
  className?: string;
}

interface MarketIndicatorData {
  timestamp: string;
  volatility_score: number;
  momentum_score: number;
  correlation_score: number;
  vix_level: number;
  volume_ratio: number;
  relative_strength: number;
}

interface IndicatorSummary {
  volatility_percentile: number;
  momentum_trend: string;
  correlation_strength: string;
  market_regime: string;
  overall_score: number;
}

const MarketIndicatorsWidget: React.FC<MarketIndicatorsWidgetProps> = ({ symbol, className = '' }) => {
  const [indicatorData, setIndicatorData] = useState<MarketIndicatorData[]>([]);
  const [summary, setSummary] = useState<IndicatorSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedView, setSelectedView] = useState<'trend' | 'radial' | 'summary'>('trend');

  useEffect(() => {
    fetchMarketIndicators();
  }, [symbol]);

  const fetchMarketIndicators = async () => {
    try {
      setLoading(true);
      const data = await advancedAnalysisApi.getMarketIndicators(symbol);
      
      // Simuler des données pour la démonstration
      const mockData = generateMockIndicatorData();
      setIndicatorData(mockData);
      
      const mockSummary = generateMockSummary();
      setSummary(mockSummary);
      
    } catch (err) {
      setError('Erreur lors du chargement des indicateurs de marché');
      console.error('Error fetching market indicators:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateMockIndicatorData = (): MarketIndicatorData[] => {
    const data = [];
    const baseDate = new Date();
    
    for (let i = 0; i < 15; i++) {
      const date = new Date(baseDate);
      date.setDate(date.getDate() - (14 - i));
      
      data.push({
        timestamp: date.toISOString().split('T')[0],
        volatility_score: 40 + Math.random() * 40,
        momentum_score: 30 + Math.random() * 50,
        correlation_score: 50 + Math.random() * 30,
        vix_level: 15 + Math.random() * 20,
        volume_ratio: 0.8 + Math.random() * 0.6,
        relative_strength: 45 + Math.random() * 30
      });
    }
    return data;
  };

  const generateMockSummary = (): IndicatorSummary => ({
    volatility_percentile: 65 + Math.random() * 30,
    momentum_trend: ['Bullish', 'Bearish', 'Neutral'][Math.floor(Math.random() * 3)],
    correlation_strength: ['High', 'Medium', 'Low'][Math.floor(Math.random() * 3)],
    market_regime: ['Bull Market', 'Bear Market', 'Sideways', 'High Volatility'][Math.floor(Math.random() * 4)],
    overall_score: 60 + Math.random() * 30
  });

  const getTrendColor = (trend: string) => {
    switch (trend.toLowerCase()) {
      case 'bullish': return '#10b981';
      case 'bearish': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getScoreColor = (score: number) => {
    if (score > 70) return '#10b981';
    if (score > 50) return '#f59e0b';
    return '#ef4444';
  };

  const getRegimeColor = (regime: string) => {
    switch (regime.toLowerCase()) {
      case 'bull market': return '#10b981';
      case 'bear market': return '#ef4444';
      case 'high volatility': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-3 gap-4">
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
            <div className="h-16 bg-gray-200 rounded"></div>
          </div>
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
            onClick={fetchMarketIndicators}
            className="mt-2 px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  const currentData = indicatorData[indicatorData.length - 1];
  const radialData = [
    { name: 'Volatilité', value: currentData?.volatility_score || 0, fill: '#3b82f6' },
    { name: 'Momentum', value: currentData?.momentum_score || 0, fill: '#10b981' },
    { name: 'Corrélation', value: currentData?.correlation_score || 0, fill: '#8b5cf6' },
    { name: 'Force Relative', value: currentData?.relative_strength || 0, fill: '#f59e0b' }
  ];

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Indicateurs de Marché - {symbol}
        </h3>
        <div className="flex space-x-2">
          {['trend', 'radial', 'summary'].map((view) => (
            <button
              key={view}
              onClick={() => setSelectedView(view as any)}
              className={`px-3 py-1 rounded text-sm font-medium ${
                selectedView === view
                  ? 'bg-green-100 text-green-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {view.charAt(0).toUpperCase() + view.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Contenu principal selon la vue sélectionnée */}
      {selectedView === 'trend' && (
        <div className="h-64 mb-6">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={indicatorData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis domain={[0, 100]} />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="volatility_score" 
                stroke="#3b82f6" 
                strokeWidth={2}
                name="Score Volatilité"
              />
              <Line 
                type="monotone" 
                dataKey="momentum_score" 
                stroke="#10b981" 
                strokeWidth={2}
                name="Score Momentum"
              />
              <Line 
                type="monotone" 
                dataKey="correlation_score" 
                stroke="#8b5cf6" 
                strokeWidth={2}
                name="Score Corrélation"
              />
              <Line 
                type="monotone" 
                dataKey="relative_strength" 
                stroke="#f59e0b" 
                strokeWidth={2}
                name="Force Relative"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {selectedView === 'radial' && (
        <div className="h-64 mb-6">
          <ResponsiveContainer width="100%" height="100%">
            <RadialBarChart cx="50%" cy="50%" innerRadius="20%" outerRadius="80%" data={radialData}>
              <RadialBar dataKey="value" cornerRadius={10} fill="#8884d8" />
              <Tooltip />
              <Legend />
            </RadialBarChart>
          </ResponsiveContainer>
        </div>
      )}

      {selectedView === 'summary' && summary && (
        <div className="space-y-6">
          {/* Score global */}
          <div className="text-center">
            <div className="text-4xl font-bold mb-2" style={{ color: getScoreColor(summary.overall_score) }}>
              {summary.overall_score.toFixed(0)}
            </div>
            <div className="text-lg text-gray-600">Score Global</div>
          </div>

          {/* Métriques clés */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-blue-900">
                {summary.volatility_percentile.toFixed(0)}%
              </div>
              <div className="text-sm text-blue-700">Percentile Volatilité</div>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg text-center">
              <div className="text-2xl font-bold text-gray-900">
                {currentData?.vix_level.toFixed(1)}
              </div>
              <div className="text-sm text-gray-700">Niveau VIX</div>
            </div>
          </div>
        </div>
      )}

      {/* Métriques actuelles */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-sm font-medium text-blue-800">Volatilité</div>
          <div className="text-2xl font-bold text-blue-900">
            {(currentData?.volatility_score || 0).toFixed(0)}
          </div>
          <div className="text-xs text-blue-600">Score</div>
        </div>
        
        <div className="bg-green-50 p-4 rounded-lg">
          <div className="text-sm font-medium text-green-800">Momentum</div>
          <div className="text-2xl font-bold text-green-900">
            {(currentData?.momentum_score || 0).toFixed(0)}
          </div>
          <div className="text-xs text-green-600">Score</div>
        </div>
        
        <div className="bg-purple-50 p-4 rounded-lg">
          <div className="text-sm font-medium text-purple-800">Corrélation</div>
          <div className="text-2xl font-bold text-purple-900">
            {(currentData?.correlation_score || 0).toFixed(0)}
          </div>
          <div className="text-xs text-purple-600">Score</div>
        </div>
        
        <div className="bg-orange-50 p-4 rounded-lg">
          <div className="text-sm font-medium text-orange-800">Volume Ratio</div>
          <div className="text-2xl font-bold text-orange-900">
            {(currentData?.volume_ratio || 0).toFixed(2)}
          </div>
          <div className="text-xs text-orange-600">Ratio</div>
        </div>
      </div>

      {/* Résumé des tendances */}
      {summary && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div>
            <h4 className="text-md font-semibold text-gray-900 mb-3">Tendances Actuelles</h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Tendance Momentum</span>
                <span 
                  className="px-2 py-1 rounded text-sm font-medium text-white"
                  style={{ backgroundColor: getTrendColor(summary.momentum_trend) }}
                >
                  {summary.momentum_trend}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Force Corrélation</span>
                <span className="text-sm font-bold text-gray-900">
                  {summary.correlation_strength}
                </span>
              </div>
            </div>
          </div>

          <div>
            <h4 className="text-md font-semibold text-gray-900 mb-3">Régime de Marché</h4>
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Régime Principal</span>
                <span 
                  className="px-2 py-1 rounded text-sm font-medium text-white"
                  style={{ backgroundColor: getRegimeColor(summary.market_regime) }}
                >
                  {summary.market_regime}
                </span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Score Global</span>
                <span 
                  className="text-sm font-bold"
                  style={{ color: getScoreColor(summary.overall_score) }}
                >
                  {summary.overall_score.toFixed(0)}/100
                </span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MarketIndicatorsWidget;
