// frontend/src/app/advanced-analysis/hybrid-opportunities/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
  MagnifyingGlassIcon, 
  ArrowPathIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import HybridOpportunityCard from '@/components/AdvancedAnalysis/HybridOpportunityCard';
import { advancedAnalysisApi, HybridAnalysisRequest } from '@/services/advancedAnalysisApi';

const HybridOpportunitiesPage: React.FC = () => {
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchConfig, setSearchConfig] = useState({
    symbols: ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'AMZN', 'META', 'NFLX'],
    weights: {
      technical: 0.35,
      sentiment: 0.30,
      market: 0.25,
      ml: 0.10
    },
    threshold: 0.7
  });

  useEffect(() => {
    performSearch();
  }, []);

  const performSearch = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const request: HybridAnalysisRequest = {
        symbols: searchConfig.symbols,
        weights: searchConfig.weights,
        threshold: searchConfig.threshold
      };
      
      const response = await advancedAnalysisApi.hybridSearch(request);
      setOpportunities(response.opportunities);
      
    } catch (err) {
      setError('Erreur lors de la recherche d\'opportunités hybrides');
      console.error('Error performing hybrid search:', err);
      
      // Données de démonstration
      setOpportunities([
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
        },
        {
          symbol: 'TSLA',
          hybrid_score: 68.3,
          confidence: 0.65,
          recommendation: 'HOLD',
          risk_level: 'HIGH',
          technical_score: 65,
          sentiment_score: 70,
          market_score: 68,
          ml_score: 70
        },
        {
          symbol: 'NVDA',
          hybrid_score: 82.7,
          confidence: 0.84,
          recommendation: 'STRONG_BUY',
          risk_level: 'MEDIUM',
          technical_score: 85,
          sentiment_score: 80,
          market_score: 82,
          ml_score: 84
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeSymbol = (symbol: string) => {
    // Rediriger vers la page d'analyse détaillée
    window.location.href = `/advanced-analysis?symbol=${symbol}`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* En-tête */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Opportunités Hybrides
                </h1>
                <p className="mt-2 text-gray-600">
                  Détection d'opportunités combinant ML et analyse conventionnelle
                </p>
              </div>
              
              <button
                onClick={performSearch}
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Configuration de recherche */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
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

        {/* Résultats */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              Opportunités Détectées
            </h2>
            <div className="text-sm text-gray-600">
              {opportunities.length} opportunité{opportunities.length > 1 ? 's' : ''} trouvée{opportunities.length > 1 ? 's' : ''}
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
          
          {loading ? (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-white rounded-lg shadow-md p-6">
                  <div className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
                    <div className="h-8 bg-gray-200 rounded w-1/2 mb-4"></div>
                    <div className="h-32 bg-gray-200 rounded"></div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {opportunities.map((opportunity) => (
                <HybridOpportunityCard
                  key={opportunity.symbol}
                  opportunity={opportunity}
                  onAnalyze={handleAnalyzeSymbol}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default HybridOpportunitiesPage;
