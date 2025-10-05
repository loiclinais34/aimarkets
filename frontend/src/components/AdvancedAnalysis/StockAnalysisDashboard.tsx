// frontend/src/components/AdvancedAnalysis/StockAnalysisDashboard.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
  MagnifyingGlassIcon, 
  ChartBarIcon, 
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  Cog6ToothIcon,
  ArrowPathIcon,
  XMarkIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline';
import TechnicalSignalsChart from './TechnicalSignalsChart';
import SentimentAnalysisPanel from './SentimentAnalysisPanel';
import MarketIndicatorsWidget from './MarketIndicatorsWidget';
import BubbleRiskPanel from './BubbleRiskPanel';
import { apiService, SymbolWithMetadata } from '@/services/api';

interface StockAnalysisDashboardProps {
  className?: string;
}

type AnalysisType = 'technical' | 'sentiment' | 'market' | 'bubble' | 'composite';

interface AnalysisResult {
  symbol: string;
  type: AnalysisType;
  isLoading: boolean;
  hasData: boolean;
  error?: string;
}

const StockAnalysisDashboard: React.FC<StockAnalysisDashboardProps> = ({ className = '' }) => {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [selectedSymbolData, setSelectedSymbolData] = useState<SymbolWithMetadata | null>(null);
  const [availableSymbols, setAvailableSymbols] = useState<SymbolWithMetadata[]>([]);
  const [analysisResults, setAnalysisResults] = useState<AnalysisResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSymbolSearch, setShowSymbolSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchLoading, setSearchLoading] = useState(false);
  
  // États pour les analyses en cours
  const [runningAnalyses, setRunningAnalyses] = useState<Set<AnalysisType>>(new Set());
  const [completedAnalyses, setCompletedAnalyses] = useState<Set<AnalysisType>>(new Set());

  // Symboles populaires par défaut
  const popularSymbols = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX', 'AMD', 'INTC',
    'CRM', 'ADBE', 'PYPL', 'UBER', 'SQ', 'ZM', 'ROKU', 'DOCU', 'OKTA', 'CRWD'
  ];

  // Types d'analyse disponibles
  const analysisTypes: { id: AnalysisType; name: string; description: string; icon: any }[] = [
    { id: 'technical', name: 'Analyse Technique', description: 'Indicateurs techniques, patterns et signaux', icon: ArrowTrendingUpIcon },
    { id: 'sentiment', name: 'Analyse de Sentiment', description: 'Sentiment du marché et des news', icon: ExclamationTriangleIcon },
    { id: 'market', name: 'Indicateurs de Marché', description: 'Indicateurs macro et sectoriels', icon: ChartBarIcon },
    { id: 'bubble', name: 'Détection de Bulle', description: 'Analyse du risque de bulle spéculative', icon: ExclamationTriangleIcon },
    { id: 'composite', name: 'Analyse Composite', description: 'Vue combinée de toutes les analyses', icon: Cog6ToothIcon }
  ];

  // Charger les symboles populaires par défaut
  useEffect(() => {
    loadPopularSymbols();
  }, []);

  // Afficher automatiquement les symboles populaires au chargement
  useEffect(() => {
    if (availableSymbols.length > 0 && !selectedSymbol) {
      setShowSymbolSearch(true);
    }
  }, [availableSymbols, selectedSymbol]);

  // Fonction pour charger les symboles populaires
  const loadPopularSymbols = async () => {
    try {
      const symbols = await apiService.getAvailableSymbols();
      // Filtrer pour ne garder que les symboles populaires
      const popularSymbolsData = symbols.filter(symbol => 
        popularSymbols.includes(symbol.symbol)
      );
      setAvailableSymbols(popularSymbolsData);
    } catch (err) {
      console.error('Erreur lors du chargement des symboles:', err);
      // Fallback vers une liste statique en cas d'erreur
      setAvailableSymbols(popularSymbols.map(symbol => ({
        symbol,
        company_name: symbol,
        sector: 'Unknown'
      })));
    }
  };

  // Fonction pour rechercher des symboles via l'API
  const searchSymbols = async (query: string) => {
    if (!query.trim()) {
      await loadPopularSymbols();
      return;
    }

    setSearchLoading(true);
    try {
      // Utiliser l'apiService pour faire l'appel
      const response = await fetch(`/api/v1/data/symbols?search=${encodeURIComponent(query)}&limit=20`);
      if (response.ok) {
        const symbols = await response.json();
        setAvailableSymbols(symbols);
      } else {
        throw new Error('Erreur lors de la recherche');
      }
    } catch (err) {
      console.error('Erreur lors de la recherche de symboles:', err);
      setError('Erreur lors de la recherche de symboles');
      // En cas d'erreur, garder la liste actuelle
    } finally {
      setSearchLoading(false);
    }
  };

  // Fonction pour sélectionner un symbole
  const selectSymbol = (symbolData: SymbolWithMetadata) => {
    setSelectedSymbol(symbolData.symbol);
    setSelectedSymbolData(symbolData);
    setShowSymbolSearch(false);
    setAnalysisResults([]);
    setRunningAnalyses(new Set());
    setCompletedAnalyses(new Set());
    setError(null);
    setSearchQuery('');
  };

  // Fonction pour lancer une analyse
  const runAnalysis = async (analysisType: AnalysisType) => {
    if (!selectedSymbol) return;

    setRunningAnalyses(prev => new Set(prev).add(analysisType));
    
    // Simuler le chargement de l'analyse
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setRunningAnalyses(prev => {
      const newSet = new Set(prev);
      newSet.delete(analysisType);
      return newSet;
    });
    
    setCompletedAnalyses(prev => new Set(prev).add(analysisType));
    
    // Ajouter le résultat à la liste
    setAnalysisResults(prev => [...prev, {
      symbol: selectedSymbol,
      type: analysisType,
      isLoading: false,
      hasData: true
    }]);
  };

  // Fonction pour lancer toutes les analyses
  const runAllAnalyses = async () => {
    if (!selectedSymbol) return;

    setLoading(true);
    setError(null);
    setAnalysisResults([]);
    setRunningAnalyses(new Set(analysisTypes.map(t => t.id)));
    setCompletedAnalyses(new Set());

    try {
      // Lancer toutes les analyses en parallèle
      const analysisPromises = analysisTypes.map(async (analysis) => {
        await runAnalysis(analysis.id);
      });

      await Promise.all(analysisPromises);
    } catch (err) {
      setError('Erreur lors de l\'exécution des analyses');
      console.error('Erreur analyses:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fonction pour réinitialiser
  const reset = () => {
    setSelectedSymbol('');
    setSelectedSymbolData(null);
    setAnalysisResults([]);
    setRunningAnalyses(new Set());
    setCompletedAnalyses(new Set());
    setError(null);
    setSearchQuery('');
    loadPopularSymbols();
  };

  // Fonction pour gérer la recherche avec debounce
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (searchQuery !== undefined) {
        searchSymbols(searchQuery);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  return (
    <div className={`bg-gray-50 min-h-screen ${className}`}>
      {/* En-tête */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  📈 Analyse Avancée de Titres
                </h1>
                <p className="mt-2 text-gray-600">
                  Analysez n'importe quel titre avec nos outils d'analyse avancés
                </p>
              </div>
              {selectedSymbol && (
                <button
                  onClick={reset}
                  className="flex items-center space-x-2 px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <XMarkIcon className="w-4 h-4" />
                  <span>Nouvelle analyse</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Sélection du symbole */}
        <div className="mb-8 p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Sélection du Titre à Analyser
          </h2>
          
          {!selectedSymbol ? (
            <div className="space-y-4">
              <div className="relative">
                <div className="flex items-center space-x-4">
                  <div className="flex-1">
                    <input
                      type="text"
                      placeholder="Rechercher un symbole ou une entreprise (ex: AAPL, Apple, Microsoft)"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <button
                    onClick={() => setShowSymbolSearch(!showSymbolSearch)}
                    className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                  >
                    <MagnifyingGlassIcon className="w-5 h-5" />
                  </button>
                </div>
                
                {/* Message d'aide */}
                <div className="text-sm text-gray-500">
                  Cliquez sur le bouton de recherche ou tapez pour voir les symboles disponibles
                </div>
                
                {(showSymbolSearch || searchQuery || availableSymbols.length > 0) && (
                  <div className="mt-2 p-4 bg-gray-50 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-sm font-medium text-gray-700">
                        {searchQuery ? 'Résultats de recherche' : 'Symboles populaires'}
                      </h3>
                      {searchLoading && (
                        <ArrowPathIcon className="w-4 h-4 animate-spin text-blue-600" />
                      )}
                    </div>
                    
                    <div className="max-h-60 overflow-y-auto">
                      {availableSymbols.length > 0 ? (
                        <div className="space-y-2">
                          {availableSymbols.map((symbolData) => (
                            <button
                              key={symbolData.symbol}
                              onClick={() => selectSymbol(symbolData)}
                              className="w-full px-3 py-2 text-left bg-white border border-gray-200 rounded-md hover:bg-blue-50 hover:border-blue-300 transition-colors"
                            >
                              <div className="flex items-center justify-between">
                                <div>
                                  <div className="font-semibold text-gray-900">{symbolData.symbol}</div>
                                  <div className="text-sm text-gray-600 truncate">{symbolData.company_name}</div>
                                </div>
                                {symbolData.sector && (
                                  <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                                    {symbolData.sector}
                                  </div>
                                )}
                              </div>
                            </button>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-4 text-gray-500">
                          {searchLoading ? 'Recherche...' : 'Aucun symbole trouvé'}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-between p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-blue-600 text-white rounded-lg flex items-center justify-center font-bold text-lg">
                  {selectedSymbol.charAt(0)}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{selectedSymbol}</h3>
                  <p className="text-sm text-gray-600">
                    {selectedSymbolData?.company_name || 'Titre sélectionné'}
                  </p>
                  {selectedSymbolData?.sector && (
                    <p className="text-xs text-blue-600">{selectedSymbolData.sector}</p>
                  )}
                </div>
              </div>
              <button
                onClick={runAllAnalyses}
                disabled={loading}
                className="flex items-center space-x-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <ArrowPathIcon className="w-5 h-5 animate-spin" />
                ) : (
                  <Cog6ToothIcon className="w-5 h-5" />
                )}
                <span>
                  {loading ? 'Analyse en cours...' : 'Lancer toutes les analyses'}
                </span>
              </button>
            </div>
          )}
        </div>

        {/* Types d'analyse */}
        {selectedSymbol && (
          <div className="mb-8 p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">
              Types d'Analyse Disponibles
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {analysisTypes.map((analysis) => {
                const Icon = analysis.icon;
                const isRunning = runningAnalyses.has(analysis.id);
                const isCompleted = completedAnalyses.has(analysis.id);
                
                return (
                  <div
                    key={analysis.id}
                    className={`p-4 border-2 rounded-lg transition-all cursor-pointer ${
                      isRunning
                        ? 'border-blue-300 bg-blue-50'
                        : isCompleted
                        ? 'border-green-300 bg-green-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => !isRunning && runAnalysis(analysis.id)}
                  >
                    <div className="flex items-center space-x-3 mb-2">
                      <div className={`p-2 rounded-lg ${
                        isRunning
                          ? 'bg-blue-100 text-blue-600'
                          : isCompleted
                          ? 'bg-green-100 text-green-600'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {isRunning ? (
                          <ArrowPathIcon className="w-5 h-5 animate-spin" />
                        ) : (
                          <Icon className="w-5 h-5" />
                        )}
                      </div>
                      <h3 className="font-semibold text-gray-900">{analysis.name}</h3>
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{analysis.description}</p>
                    <div className="flex items-center justify-between">
                      <span className={`text-xs px-2 py-1 rounded-full ${
                        isRunning
                          ? 'bg-blue-100 text-blue-700'
                          : isCompleted
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-600'
                      }`}>
                        {isRunning ? 'En cours...' : isCompleted ? 'Terminé' : 'Cliquer pour analyser'}
                      </span>
                      {isCompleted && (
                        <span className="text-green-600 text-sm">✓</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Affichage des résultats */}
        {selectedSymbol && analysisResults.length > 0 && (
          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-gray-900">
              Résultats d'Analyse - {selectedSymbol}
            </h2>
            
            {analysisResults.map((result) => {
              if (!result.hasData) return null;
              
              switch (result.type) {
                case 'technical':
                  return (
                    <div key="technical" className="bg-white rounded-lg shadow-sm p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Analyse Technique - {result.symbol}
                      </h3>
                      <TechnicalSignalsChart symbol={result.symbol} />
                    </div>
                  );
                
                case 'sentiment':
                  return (
                    <div key="sentiment" className="bg-white rounded-lg shadow-sm p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Analyse de Sentiment - {result.symbol}
                      </h3>
                      <SentimentAnalysisPanel symbol={result.symbol} />
                    </div>
                  );
                
                case 'market':
                  return (
                    <div key="market" className="bg-white rounded-lg shadow-sm p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Indicateurs de Marché - {result.symbol}
                      </h3>
                      <MarketIndicatorsWidget symbol={result.symbol} />
                    </div>
                  );
                
                case 'bubble':
                  return (
                    <div key="bubble" className="bg-white rounded-lg shadow-sm p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Analyse de Bulle - {result.symbol}
                      </h3>
                      <BubbleRiskPanel symbol={result.symbol} />
                    </div>
                  );
                
                case 'composite':
                  return (
                    <div key="composite" className="bg-white rounded-lg shadow-sm p-6">
                      <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Analyse Composite - {result.symbol}
                      </h3>
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <TechnicalSignalsChart symbol={result.symbol} />
                        <SentimentAnalysisPanel symbol={result.symbol} />
                      </div>
                      <div className="mt-6">
                        <MarketIndicatorsWidget symbol={result.symbol} />
                      </div>
                      <div className="mt-6">
                        <BubbleRiskPanel symbol={result.symbol} />
                      </div>
                    </div>
                  );
                
                default:
                  return null;
              }
            })}
          </div>
        )}

        {/* Message d'erreur */}
        {error && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-400 mr-2" />
              <span className="text-red-800">{error}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StockAnalysisDashboard;
