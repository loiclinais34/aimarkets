'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { 
  StarIcon, 
  ChartBarIcon, 
  ArrowUpIcon, 
  ArrowDownIcon,
  XMarkIcon,
  FunnelIcon,
  ChevronDownIcon,
  ShoppingCartIcon
} from '@heroicons/react/24/outline';
import { addOpportunityToCart } from './OpportunityCart';

interface Opportunity {
  symbol: string;
  company_name: string;
  prediction: number;
  confidence: number;
  model_id: number;
  model_name: string;
  target_return: number;
  time_horizon: number;
  rank: number;
  prediction_date: string | null;
  screener_run_id: number;
}

interface SymbolOpportunities {
  symbol: string;
  company_name: string;
  opportunities: Opportunity[];
  best_confidence: number;
  best_model: string;
  total_opportunities: number;
  latest_opportunity_date: string | null;
}

interface OpportunitiesBySymbolProps {
  className?: string;
  maxItems?: number;
}

export default function OpportunitiesBySymbol({ className = '', maxItems = 6 }: OpportunitiesBySymbolProps) {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [groupedOpportunities, setGroupedOpportunities] = useState<SymbolOpportunities[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState<SymbolOpportunities | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    minReturn: 0,
    maxReturn: 100,
    minHorizon: 1,
    maxHorizon: 365,
    startDate: '',
    endDate: ''
  });
  const [cartNotifications, setCartNotifications] = useState<{[key: string]: boolean}>({});

  const fetchOpportunities = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      const response = await fetch('/api/v1/screener/latest-opportunities');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      setOpportunities(result);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Erreur lors de la récupération des opportunités:', err);
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Grouper les opportunités par symbole
  useEffect(() => {
    if (opportunities.length === 0) {
      setGroupedOpportunities([]);
      return;
    }

    const grouped = opportunities.reduce((acc, opportunity) => {
      const existing = acc.find(item => item.symbol === opportunity.symbol);
      
      if (existing) {
        existing.opportunities.push(opportunity);
        if (opportunity.confidence > existing.best_confidence) {
          existing.best_confidence = opportunity.confidence;
          existing.best_model = opportunity.model_name;
        }
        existing.total_opportunities++;
        
        // Mettre à jour la date la plus récente
        if (opportunity.prediction_date && (!existing.latest_opportunity_date || 
            new Date(opportunity.prediction_date) > new Date(existing.latest_opportunity_date))) {
          existing.latest_opportunity_date = opportunity.prediction_date;
        }
      } else {
        acc.push({
          symbol: opportunity.symbol,
          company_name: opportunity.company_name,
          opportunities: [opportunity],
          best_confidence: opportunity.confidence,
          best_model: opportunity.model_name,
          total_opportunities: 1,
          latest_opportunity_date: opportunity.prediction_date
        });
      }
      
      return acc;
    }, [] as SymbolOpportunities[]);

    // Trier par meilleur score de confiance
    grouped.sort((a, b) => b.best_confidence - a.best_confidence);
    
    setGroupedOpportunities(grouped);
  }, [opportunities]);

  // Auto-refresh des opportunités
  useEffect(() => {
    if (typeof window === 'undefined') return;
    
    // Fetch initial
    const timeoutId = setTimeout(() => {
      fetchOpportunities();
    }, 1000);
    
    // Polling périodique seulement si l'onglet est visible
    let intervalId: NodeJS.Timeout | null = null;
    
    const startPolling = () => {
      if (intervalId) return; // Éviter les doublons
      intervalId = setInterval(fetchOpportunities, 60000); // Toutes les 60 secondes
    };
    
    const stopPolling = () => {
      if (intervalId) {
        clearInterval(intervalId);
        intervalId = null;
      }
    };
    
    // Gestion de la visibilité de l'onglet
    const handleVisibilityChange = () => {
      if (document.hidden) {
        stopPolling();
      } else {
        startPolling();
        fetchOpportunities(); // Fetch immédiat quand l'onglet redevient visible
      }
    };
    
    // Démarrer le polling initial
    startPolling();
    
    // Écouter les changements de visibilité
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    return () => {
      clearTimeout(timeoutId);
      stopPolling();
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [fetchOpportunities]);

  const formatModelName = (modelName: string) => {
    if (modelName.includes('xgboost')) return 'XGBoost';
    if (modelName.includes('lightgbm')) return 'LightGBM';
    if (modelName.includes('randomforest')) return 'RandomForest';
    if (modelName.includes('neural')) return 'Neural Network';
    return 'ML Model';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'Élevée';
    if (confidence >= 0.6) return 'Moyenne';
    return 'Faible';
  };

  const handleSymbolClick = (symbolData: SymbolOpportunities) => {
    setSelectedSymbol(symbolData);
  };

  const closeModal = () => {
    setSelectedSymbol(null);
  };

  const handleAddToCart = (opportunity: Opportunity) => {
    const success = addOpportunityToCart(opportunity);
    if (success) {
      const key = `${opportunity.symbol}-${opportunity.model_id}`;
      setCartNotifications(prev => ({ ...prev, [key]: true }));
      
      // Masquer la notification après 2 secondes
      setTimeout(() => {
        setCartNotifications(prev => ({ ...prev, [key]: false }));
      }, 2000);
    }
  };

  const getFilteredOpportunities = () => {
    if (!selectedSymbol) return [];
    
    return selectedSymbol.opportunities
      .filter(opp => {
        const matchesReturn = opp.target_return >= filters.minReturn && opp.target_return <= filters.maxReturn;
        const matchesHorizon = opp.time_horizon >= filters.minHorizon && opp.time_horizon <= filters.maxHorizon;
        
        let matchesDate = true;
        if (filters.startDate && opp.prediction_date) {
          matchesDate = matchesDate && new Date(opp.prediction_date) >= new Date(filters.startDate);
        }
        if (filters.endDate && opp.prediction_date) {
          matchesDate = matchesDate && new Date(opp.prediction_date) <= new Date(filters.endDate);
        }
        
        return matchesReturn && matchesHorizon && matchesDate;
      })
      .sort((a, b) => b.confidence - a.confidence);
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Récent';
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <StarIcon className="h-5 w-5 mr-2 text-yellow-600" />
          Opportunités par Titre
        </h3>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-20 bg-gray-200 rounded-lg"></div>
            </div>
          ))}
        </div>
        <div className="mt-4 text-sm text-gray-500 text-center">
          Chargement des opportunités...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <StarIcon className="h-5 w-5 mr-2 text-yellow-600" />
          Opportunités par Titre
        </h3>
        <div className="text-center py-8">
          <div className="text-red-600 mb-2">Erreur de chargement</div>
          <div className="text-sm text-gray-500 mb-4">{error}</div>
          <button
            onClick={fetchOpportunities}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  const displayOpportunities = groupedOpportunities.slice(0, maxItems);

  return (
    <>
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            <StarIcon className="h-5 w-5 mr-2 text-yellow-600" />
            Opportunités par Titre
          </h3>
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-500">
              {groupedOpportunities.length} titres
            </span>
            {lastUpdated && (
              <span className="text-xs text-gray-400">
                Mis à jour: {lastUpdated.toLocaleTimeString('fr-FR')}
              </span>
            )}
          </div>
        </div>

        {displayOpportunities.length === 0 ? (
          <div className="text-center py-8">
            <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <div className="text-gray-500 mb-2">Aucune opportunité trouvée</div>
            <div className="text-sm text-gray-400">
              Lancez une recherche d'opportunités pour voir les résultats
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {displayOpportunities.map((symbolData) => (
              <div
                key={symbolData.symbol}
                onClick={() => handleSymbolClick(symbolData)}
                className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-md cursor-pointer transition-all duration-200"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-sm font-semibold text-blue-600">
                          {symbolData.symbol}
                        </span>
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 truncate">
                        {symbolData.company_name}
                      </div>
                      <div className="text-xs text-gray-500">
                        {symbolData.total_opportunities} opportunité{symbolData.total_opportunities > 1 ? 's' : ''}
                        {symbolData.latest_opportunity_date && (
                          <span className="ml-2">
                            • {formatDate(symbolData.latest_opportunity_date)}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <div className="text-right">
                      <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(symbolData.best_confidence)}`}>
                        {getConfidenceLabel(symbolData.best_confidence)}
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        {formatModelName(symbolData.best_model)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-lg font-semibold text-gray-900">
                        {(symbolData.best_confidence * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500">Confiance</div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {groupedOpportunities.length > maxItems && (
          <div className="mt-4 text-center">
            <div className="text-sm text-gray-500">
              Et {groupedOpportunities.length - maxItems} autre{groupedOpportunities.length - maxItems > 1 ? 's' : ''} titre{groupedOpportunities.length - maxItems > 1 ? 's' : ''}
            </div>
          </div>
        )}
      </div>

      {/* Modal des opportunités détaillées */}
      {selectedSymbol && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {selectedSymbol.symbol} - {selectedSymbol.company_name}
                </h3>
                <p className="text-sm text-gray-500">
                  {selectedSymbol.total_opportunities} opportunité{selectedSymbol.total_opportunities > 1 ? 's' : ''} détectée{selectedSymbol.total_opportunities > 1 ? 's' : ''}
                </p>
              </div>
              <button
                onClick={closeModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            <div className="p-6 flex-1 overflow-y-auto">
              {/* Filtres */}
              <div className="mb-6">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="flex items-center text-sm text-blue-600 hover:text-blue-800"
                >
                  <FunnelIcon className="h-4 w-4 mr-1" />
                  Filtres
                  <ChevronDownIcon className={`h-4 w-4 ml-1 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
                </button>

                {showFilters && (
                  <div className="mt-3 p-4 bg-gray-50 rounded-lg">
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Rendement Min (%)
                        </label>
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={filters.minReturn}
                          onChange={(e) => setFilters(prev => ({ ...prev, minReturn: Number(e.target.value) }))}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Rendement Max (%)
                        </label>
                        <input
                          type="number"
                          min="0"
                          max="100"
                          value={filters.maxReturn}
                          onChange={(e) => setFilters(prev => ({ ...prev, maxReturn: Number(e.target.value) }))}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Horizon Min (jours)
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="365"
                          value={filters.minHorizon}
                          onChange={(e) => setFilters(prev => ({ ...prev, minHorizon: Number(e.target.value) }))}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Horizon Max (jours)
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="365"
                          value={filters.maxHorizon}
                          onChange={(e) => setFilters(prev => ({ ...prev, maxHorizon: Number(e.target.value) }))}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Date Début
                        </label>
                        <input
                          type="date"
                          value={filters.startDate}
                          onChange={(e) => setFilters(prev => ({ ...prev, startDate: e.target.value }))}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-medium text-gray-700 mb-1">
                          Date Fin
                        </label>
                        <input
                          type="date"
                          value={filters.endDate}
                          onChange={(e) => setFilters(prev => ({ ...prev, endDate: e.target.value }))}
                          className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Liste des opportunités filtrées */}
              <div className="space-y-3">
                {getFilteredOpportunities().map((opportunity, index) => {
                  const cartKey = `${opportunity.symbol}-${opportunity.model_id}`;
                  const isInCart = cartNotifications[cartKey];
                  
                  return (
                    <div key={`${opportunity.model_id}-${index}`} className="p-4 border border-gray-200 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="flex-shrink-0">
                            <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                              <span className="text-xs font-semibold text-blue-600">
                                #{opportunity.rank}
                              </span>
                            </div>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="text-sm font-medium text-gray-900">
                              {formatModelName(opportunity.model_name)}
                            </div>
                            <div className="text-xs text-gray-500">
                              {opportunity.target_return}% sur {opportunity.time_horizon} jours
                              {opportunity.prediction_date && (
                                <span className="ml-2">
                                  • {formatDate(opportunity.prediction_date)}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center space-x-4">
                          <div className="text-right">
                            <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(opportunity.confidence)}`}>
                              {getConfidenceLabel(opportunity.confidence)}
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              {formatDate(opportunity.prediction_date)}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-lg font-semibold text-gray-900">
                              {(opportunity.confidence * 100).toFixed(1)}%
                            </div>
                            <div className="text-xs text-gray-500">Confiance</div>
                          </div>
                          <div className="flex-shrink-0">
                            <button
                              onClick={() => handleAddToCart(opportunity)}
                              className={`p-2 rounded-full transition-colors ${
                                isInCart 
                                  ? 'bg-green-100 text-green-600' 
                                  : 'bg-gray-100 text-gray-600 hover:bg-blue-100 hover:text-blue-600'
                              }`}
                              title="Ajouter au panier"
                            >
                              <ShoppingCartIcon className="h-4 w-4" />
                            </button>
                            {isInCart && (
                              <div className="absolute -top-1 -right-1 bg-green-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">
                                ✓
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {getFilteredOpportunities().length === 0 && (
                <div className="text-center py-8">
                  <div className="text-gray-500 mb-2">Aucune opportunité ne correspond aux filtres</div>
                  <div className="text-sm text-gray-400">
                    Ajustez les critères de filtrage pour voir plus de résultats
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
