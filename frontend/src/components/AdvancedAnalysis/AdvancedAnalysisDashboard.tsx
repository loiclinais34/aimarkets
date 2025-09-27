// frontend/src/components/AdvancedAnalysis/AdvancedAnalysisDashboard.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
  MagnifyingGlassIcon, 
  ChartBarIcon, 
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  Cog6ToothIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import TechnicalSignalsChart from './TechnicalSignalsChart';
import SentimentAnalysisPanel from './SentimentAnalysisPanel';
import MarketIndicatorsWidget from './MarketIndicatorsWidget';
import HybridOpportunityCard from './HybridOpportunityCard';
import { advancedAnalysisApi, HybridAnalysisRequest, HybridAnalysisResponse } from '@/services/advancedAnalysisApi';

interface AdvancedAnalysisDashboardProps {
  className?: string;
}

const AdvancedAnalysisDashboard: React.FC<AdvancedAnalysisDashboardProps> = ({ className = '' }) => {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [hybridOpportunities, setHybridOpportunities] = useState<HybridAnalysisResponse['opportunities']>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchConfig, setSearchConfig] = useState({
    symbols: ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
    weights: {
      technical: 0.35,
      sentiment: 0.30,
      market: 0.25,
      ml: 0.10
    },
    threshold: 0.7
  });
  const [activeTab, setActiveTab] = useState<'overview' | 'technical' | 'sentiment' | 'market' | 'hybrid'>('overview');

  useEffect(() => {
    performHybridSearch();
  }, []);

  const performHybridSearch = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const request: HybridAnalysisRequest = {
        symbols: searchConfig.symbols,
        weights: searchConfig.weights,
        threshold: searchConfig.threshold
      };
      
      const response = await advancedAnalysisApi.hybridSearch(request);
      setHybridOpportunities(response.opportunities);
      
    } catch (err) {
      setError('Erreur lors de la recherche hybride d\'opportunités');
      console.error('Error performing hybrid search:', err);
      
      // Données de démonstration en cas d'erreur
      setHybridOpportunities([
        {
          symbol: 'AAPL',
          hybrid_score: 85.2,
          confidence: 0.87,
          recommendation: 'STRONG_BUY',
          risk_level: 'LOW',
          technical_score: 88,
          sentiment_score: 82,
          market_score: 85,
          ml_score: 86
        },
        {
          symbol: 'MSFT',
          hybrid_score: 78.5,
          confidence: 0.79,
          recommendation: 'BUY',
          risk_level: 'MEDIUM',
          technical_score: 75,
          sentiment_score: 80,
          market_score: 78,
          ml_score: 81
        },
        {
          symbol: 'GOOGL',
          hybrid_score: 72.1,
          confidence: 0.73,
          recommendation: 'BUY',
          risk_level: 'MEDIUM',
          technical_score: 70,
          sentiment_score: 74,
          market_score: 72,
          ml_score: 72
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSymbolChange = (symbol: string) => {
    setSelectedSymbol(symbol);
  };

  const handleAnalyzeSymbol = (symbol: string) => {
    setSelectedSymbol(symbol);
    setActiveTab('overview');
  };

  const tabs = [
    { id: 'overview', name: 'Vue d\'ensemble', icon: ChartBarIcon },
    { id: 'technical', name: 'Technique', icon: ArrowTrendingUpIcon },
    { id: 'sentiment', name: 'Sentiment', icon: ExclamationTriangleIcon },
    { id: 'market', name: 'Marché', icon: ChartBarIcon },
    { id: 'hybrid', name: 'Hybride', icon: Cog6ToothIcon }
  ];

  return (
    <div className={`bg-gray-50 min-h-screen ${className}`}>
      {/* En-tête */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Analyse Avancée de Trading
                </h1>
                <p className="mt-2 text-gray-600">
                  Système d'analyse combinée ML + conventionnelle pour des décisions éclairées
                </p>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <MagnifyingGlassIcon className="w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={selectedSymbol}
                    onChange={(e) => setSelectedSymbol(e.target.value.toUpperCase())}
                    placeholder="Symbole (ex: AAPL)"
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <button
                  onClick={performHybridSearch}
                  disabled={loading}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <ArrowPathIcon className="w-4 h-4 animate-spin" />
                  ) : (
                    <MagnifyingGlassIcon className="w-4 h-4" />
                  )}
                  <span>Rechercher</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation par onglets */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Contenu des onglets */}
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Opportunités hybrides */}
            <div>
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-2xl font-bold text-gray-900">
                  Opportunités Hybrides Détectées
                </h2>
                <div className="text-sm text-gray-600">
                  {hybridOpportunities.length} opportunité{hybridOpportunities.length > 1 ? 's' : ''} trouvée{hybridOpportunities.length > 1 ? 's' : ''}
                </div>
              </div>
              
              {error && (
                <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center">
                    <ExclamationTriangleIcon className="w-5 h-5 text-red-400 mr-2" />
                    <span className="text-red-800">{error}</span>
                  </div>
                </div>
              )}
              
              <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                {hybridOpportunities.map((opportunity) => (
                  <HybridOpportunityCard
                    key={opportunity.symbol}
                    opportunity={opportunity}
                    onAnalyze={handleAnalyzeSymbol}
                  />
                ))}
              </div>
            </div>

            {/* Configuration de recherche */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Configuration de Recherche
              </h3>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Symboles à Analyser
                  </label>
                  <input
                    type="text"
                    value={searchConfig.symbols.join(', ')}
                    onChange={(e) => setSearchConfig({
                      ...searchConfig,
                      symbols: e.target.value.split(',').map(s => s.trim().toUpperCase()).filter(s => s)
                    })}
                    placeholder="AAPL, MSFT, GOOGL, TSLA, NVDA"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Seuil de Score ({searchConfig.threshold})
                  </label>
                  <input
                    type="range"
                    min="0.5"
                    max="1.0"
                    step="0.05"
                    value={searchConfig.threshold}
                    onChange={(e) => setSearchConfig({
                      ...searchConfig,
                      threshold: parseFloat(e.target.value)
                    })}
                    className="w-full"
                  />
                </div>
              </div>
              
              <div className="mt-6">
                <h4 className="text-md font-semibold text-gray-900 mb-3">Poids des Analyses</h4>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                  {Object.entries(searchConfig.weights).map(([key, value]) => (
                    <div key={key}>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        {key.charAt(0).toUpperCase() + key.slice(1)} ({value})
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.05"
                        value={value}
                        onChange={(e) => setSearchConfig({
                          ...searchConfig,
                          weights: {
                            ...searchConfig.weights,
                            [key]: parseFloat(e.target.value)
                          }
                        })}
                        className="w-full"
                      />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'technical' && (
          <TechnicalSignalsChart symbol={selectedSymbol} />
        )}

        {activeTab === 'sentiment' && (
          <SentimentAnalysisPanel symbol={selectedSymbol} />
        )}

        {activeTab === 'market' && (
          <MarketIndicatorsWidget symbol={selectedSymbol} />
        )}

        {activeTab === 'hybrid' && (
          <div className="space-y-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Analyse Hybride Complète - {selectedSymbol}
              </h3>
              <p className="text-gray-600 mb-6">
                Cette vue combine l'analyse technique, de sentiment, de marché et ML pour {selectedSymbol}.
              </p>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <TechnicalSignalsChart symbol={selectedSymbol} />
                <SentimentAnalysisPanel symbol={selectedSymbol} />
              </div>
              
              <div className="mt-6">
                <MarketIndicatorsWidget symbol={selectedSymbol} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AdvancedAnalysisDashboard;
