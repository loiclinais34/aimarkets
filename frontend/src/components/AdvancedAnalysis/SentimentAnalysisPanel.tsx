// frontend/src/components/AdvancedAnalysis/SentimentAnalysisPanel.tsx
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
  AreaChart, 
  Area 
} from 'recharts';
import { advancedAnalysisApi } from '@/services/advancedAnalysisApi';

interface SentimentAnalysisPanelProps {
  symbol: string;
  className?: string;
}

interface SentimentData {
  timestamp: string;
  volatility_forecast: number;
  var_95: number;
  var_99: number;
  market_state: string;
  confidence: number;
  garch_volatility: number;
  monte_carlo_var: number;
  markov_state: string;
}

interface RiskMetrics {
  volatility_percentile: number;
  stress_test_loss: number;
  tail_risk: number;
  regime_probability: number;
}

const SentimentAnalysisPanel: React.FC<SentimentAnalysisPanelProps> = ({ symbol, className = '' }) => {
  const [sentimentData, setSentimentData] = useState<SentimentData[]>([]);
  const [riskMetrics, setRiskMetrics] = useState<RiskMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMetric, setSelectedMetric] = useState<'volatility' | 'var' | 'regime'>('volatility');

  useEffect(() => {
    fetchSentimentData();
  }, [symbol]);

  const fetchSentimentData = async () => {
    try {
      setLoading(true);
      const data = await advancedAnalysisApi.getSentimentAnalysis(symbol);
      
      // Simuler des données pour la démonstration
      const mockData = generateMockSentimentData();
      setSentimentData(mockData);
      
      const mockRiskMetrics = generateMockRiskMetrics();
      setRiskMetrics(mockRiskMetrics);
      
    } catch (err) {
      setError('Erreur lors du chargement des données de sentiment');
      console.error('Error fetching sentiment data:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateMockSentimentData = (): SentimentData[] => {
    const data = [];
    const baseDate = new Date();
    const marketStates = ['Bull Market', 'Bear Market', 'Sideways', 'High Volatility'];
    
    for (let i = 0; i < 20; i++) {
      const date = new Date(baseDate);
      date.setDate(date.getDate() - (19 - i));
      
      data.push({
        timestamp: date.toISOString().split('T')[0],
        volatility_forecast: 0.15 + Math.random() * 0.1,
        var_95: -0.02 - Math.random() * 0.03,
        var_99: -0.03 - Math.random() * 0.05,
        market_state: marketStates[Math.floor(Math.random() * marketStates.length)],
        confidence: 0.6 + Math.random() * 0.3,
        garch_volatility: 0.12 + Math.random() * 0.08,
        monte_carlo_var: -0.025 - Math.random() * 0.02,
        markov_state: marketStates[Math.floor(Math.random() * marketStates.length)]
      });
    }
    return data;
  };

  const generateMockRiskMetrics = (): RiskMetrics => ({
    volatility_percentile: 65 + Math.random() * 30,
    stress_test_loss: -0.08 - Math.random() * 0.05,
    tail_risk: 0.05 + Math.random() * 0.03,
    regime_probability: 0.7 + Math.random() * 0.2
  });

  const getMarketStateColor = (state: string) => {
    switch (state.toLowerCase()) {
      case 'bull market': return '#10b981';
      case 'bear market': return '#ef4444';
      case 'high volatility': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  const getRiskLevel = (percentile: number) => {
    if (percentile > 80) return { level: 'Élevé', color: 'text-red-600', bg: 'bg-red-50' };
    if (percentile > 60) return { level: 'Modéré', color: 'text-yellow-600', bg: 'bg-yellow-50' };
    return { level: 'Faible', color: 'text-green-600', bg: 'bg-green-50' };
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded mb-4"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
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
            onClick={fetchSentimentData}
            className="mt-2 px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  const currentData = sentimentData[sentimentData.length - 1];
  const riskLevel = getRiskLevel(riskMetrics?.volatility_percentile || 0);

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          Analyse de Sentiment - {symbol}
        </h3>
        <div className="flex space-x-2">
          {['volatility', 'var', 'regime'].map((metric) => (
            <button
              key={metric}
              onClick={() => setSelectedMetric(metric as any)}
              className={`px-3 py-1 rounded text-sm font-medium ${
                selectedMetric === metric
                  ? 'bg-purple-100 text-purple-700'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {metric.charAt(0).toUpperCase() + metric.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Graphique principal */}
      <div className="h-64 mb-6">
        <ResponsiveContainer width="100%" height="100%">
          {selectedMetric === 'volatility' ? (
            <AreaChart data={sentimentData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="volatility_forecast" 
                stroke="#8b5cf6" 
                fill="#8b5cf6" 
                fillOpacity={0.3}
                name="Volatilité Prévue"
              />
              <Area 
                type="monotone" 
                dataKey="garch_volatility" 
                stroke="#f59e0b" 
                fill="#f59e0b" 
                fillOpacity={0.3}
                name="Volatilité GARCH"
              />
            </AreaChart>
          ) : selectedMetric === 'var' ? (
            <LineChart data={sentimentData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="var_95" 
                stroke="#ef4444" 
                strokeWidth={2}
                name="VaR 95%"
              />
              <Line 
                type="monotone" 
                dataKey="var_99" 
                stroke="#dc2626" 
                strokeWidth={2}
                name="VaR 99%"
              />
              <Line 
                type="monotone" 
                dataKey="monte_carlo_var" 
                stroke="#f59e0b" 
                strokeWidth={2}
                name="VaR Monte Carlo"
              />
            </LineChart>
          ) : (
            <LineChart data={sentimentData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="timestamp" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="confidence" 
                stroke="#8b5cf6" 
                strokeWidth={2}
                name="Confiance"
              />
            </LineChart>
          )}
        </ResponsiveContainer>
      </div>

      {/* Métriques actuelles */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="bg-purple-50 p-4 rounded-lg">
          <div className="text-sm font-medium text-purple-800">Volatilité Prévue</div>
          <div className="text-2xl font-bold text-purple-900">
            {(currentData?.volatility_forecast * 100).toFixed(1)}%
          </div>
        </div>
        
        <div className="bg-red-50 p-4 rounded-lg">
          <div className="text-sm font-medium text-red-800">VaR 95%</div>
          <div className="text-2xl font-bold text-red-900">
            {(currentData?.var_95 * 100).toFixed(1)}%
          </div>
        </div>
        
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="text-sm font-medium text-blue-800">Confiance</div>
          <div className="text-2xl font-bold text-blue-900">
            {(currentData?.confidence * 100).toFixed(0)}%
          </div>
        </div>
        
        <div className={`p-4 rounded-lg ${riskLevel.bg}`}>
          <div className={`text-sm font-medium ${riskLevel.color}`}>Niveau de Risque</div>
          <div className={`text-2xl font-bold ${riskLevel.color}`}>
            {riskLevel.level}
          </div>
        </div>
      </div>

      {/* État du marché et métriques avancées */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <h4 className="text-md font-semibold text-gray-900 mb-3">État du Marché Actuel</h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">État Principal</span>
              <span 
                className="px-2 py-1 rounded text-sm font-medium text-white"
                style={{ backgroundColor: getMarketStateColor(currentData?.market_state || '') }}
              >
                {currentData?.market_state}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">État Markov</span>
              <span 
                className="px-2 py-1 rounded text-sm font-medium text-white"
                style={{ backgroundColor: getMarketStateColor(currentData?.markov_state || '') }}
              >
                {currentData?.markov_state}
              </span>
            </div>
          </div>
        </div>

        <div>
          <h4 className="text-md font-semibold text-gray-900 mb-3">Métriques de Risque Avancées</h4>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Percentile Volatilité</span>
              <span className="text-sm font-bold text-gray-900">
                {riskMetrics?.volatility_percentile.toFixed(0)}%
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Stress Test</span>
              <span className="text-sm font-bold text-red-600">
                {(riskMetrics?.stress_test_loss ? riskMetrics.stress_test_loss * 100 : 0).toFixed(1)}%
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Risque de Queue</span>
              <span className="text-sm font-bold text-orange-600">
                {(riskMetrics?.tail_risk ? riskMetrics.tail_risk * 100 : 0).toFixed(1)}%
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <span className="text-sm font-medium text-gray-700">Probabilité Régime</span>
              <span className="text-sm font-bold text-blue-600">
                {(riskMetrics?.regime_probability ? riskMetrics.regime_probability * 100 : 0).toFixed(0)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SentimentAnalysisPanel;
