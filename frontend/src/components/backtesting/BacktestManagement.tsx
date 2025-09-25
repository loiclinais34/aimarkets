'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  BacktestRun, 
  BacktestResults, 
  BacktestCreateForm,
  BacktestTrade,
  BacktestMetrics,
  BacktestEquityPoint,
  ModelPredictionDates
} from '../../types/strategies';
import { strategiesApi, backtestingApi } from '../../services/strategiesApi';
import { apiService } from '../../services/api';

interface BacktestCardProps {
  backtest: BacktestRun;
  onViewResults: (backtestId: number) => void;
  onDelete: (backtestId: number) => void;
}

export const BacktestCard: React.FC<BacktestCardProps> = ({
  backtest,
  onViewResults,
  onDelete
}) => {
  const [isDeleting, setIsDeleting] = useState(false);

  const deleteMutation = useMutation(
    () => backtestingApi.deleteBacktest(backtest.id),
    {
      onSuccess: () => {
        onDelete(backtest.id);
      },
      onError: (error: any) => {
        alert(`Erreur lors de la suppression: ${error.message}`);
      }
    }
  );

  const handleDelete = async () => {
    if (window.confirm(`Êtes-vous sûr de vouloir supprimer le backtest "${backtest.name}" ?`)) {
      setIsDeleting(true);
      try {
        await deleteMutation.mutateAsync();
      } finally {
        setIsDeleting(false);
      }
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-yellow-100 text-yellow-800',
      running: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pending: 'En attente',
      running: 'En cours',
      completed: 'Terminé',
      failed: 'Échec'
    };
    return texts[status] || status;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{backtest.name}</h3>
          <p className="text-sm text-gray-600">{backtest.description}</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => onViewResults(backtest.id)}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            Résultats
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="text-red-600 hover:text-red-800 text-sm font-medium disabled:opacity-50"
          >
            {isDeleting ? 'Suppression...' : 'Supprimer'}
          </button>
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-500">Modèle</p>
          <p className="text-sm font-medium">{backtest.model_name || `ID: ${backtest.model_id}`}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Stratégie</p>
          <p className="text-sm font-medium">{backtest.strategy_name || 'Aucune'}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Période</p>
          <p className="text-sm font-medium">
            {new Date(backtest.start_date).toLocaleDateString('fr-FR')} - {new Date(backtest.end_date).toLocaleDateString('fr-FR')}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500">Capital initial</p>
          <p className="text-sm font-medium">${backtest.initial_capital.toLocaleString()}</p>
        </div>
      </div>
      
      <div className="flex justify-between items-center">
        <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(backtest.status)}`}>
          {getStatusText(backtest.status)}
        </span>
        <span className="text-xs text-gray-500">
          {new Date(backtest.created_at).toLocaleDateString('fr-FR')}
        </span>
      </div>
      
      {backtest.error_message && (
        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
          <strong>Erreur:</strong> {backtest.error_message}
        </div>
      )}
    </div>
  );
};

interface BacktestListProps {
  onViewResults: (backtestId: number) => void;
  onDelete: (backtestId: number) => void;
}

export const BacktestList: React.FC<BacktestListProps> = ({
  onViewResults,
  onDelete
}) => {
  const { data: backtests, isLoading, error, refetch } = useQuery(
    'backtests',
    () => backtestingApi.getBacktestRuns(),
    {
      refetchOnWindowFocus: false
    }
  );

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Erreur lors du chargement des backtests</p>
        <button 
          onClick={() => refetch()}
          className="mt-2 text-red-600 hover:text-red-800 text-sm font-medium"
        >
          Réessayer
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4">
        <p className="text-sm text-gray-600">
          {backtests?.length || 0} backtest{(backtests?.length || 0) > 1 ? 's' : ''} trouvé{(backtests?.length || 0) > 1 ? 's' : ''}
        </p>
      </div>

      {!backtests || backtests.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">Aucun backtest trouvé</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {backtests.map((backtest) => (
            <BacktestCard
              key={backtest.id}
              backtest={backtest}
              onViewResults={onViewResults}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
};

interface BacktestFormProps {
  onSave: (backtest: BacktestCreateForm) => void;
  onCancel: () => void;
}

export const BacktestForm: React.FC<BacktestFormProps> = ({
  onSave,
  onCancel
}) => {
  const [formData, setFormData] = useState<BacktestCreateForm>({
    name: '',
    description: '',
    model_id: 0,
    strategy_id: undefined,
    start_date: '',
    end_date: '',
    initial_capital: 100000,
    position_size_percentage: 10,
    commission_rate: 0.001,
    slippage_rate: 0.0005,
    confidence_threshold: 0.6,
    max_positions: 10
  });

  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [availableModels, setAvailableModels] = useState<any[]>([]);
  const [selectedModel, setSelectedModel] = useState<any>(null);
  const [predictionDates, setPredictionDates] = useState<ModelPredictionDates | null>(null);
  const [modelSearchTerm, setModelSearchTerm] = useState<string>('');
  const [showModelDropdown, setShowModelDropdown] = useState<boolean>(false);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);

  const { data: symbolsData } = useQuery(
    'backtesting-symbols',
    () => backtestingApi.getAvailableSymbols(),
    {
      refetchOnWindowFocus: false
    }
  );

  const { data: strategies } = useQuery(
    'strategies',
    () => strategiesApi.getStrategies(),
    {
      refetchOnWindowFocus: false
    }
  );

  // Charger les modèles quand un symbole est sélectionné
  useEffect(() => {
    if (selectedSymbol) {
      // Charger seulement les premiers modèles (les plus pertinents)
      backtestingApi.getModelsForSymbol(selectedSymbol, 50, 0)
        .then(response => {
          setAvailableModels(response.models);
          // Réinitialiser la sélection du modèle
          setSelectedModel(null);
          setFormData(prev => ({ ...prev, model_id: 0 }));
          setModelSearchTerm('');
        })
        .catch(error => {
          console.error('Erreur lors du chargement des modèles:', error);
          setAvailableModels([]);
        });
    } else {
      setAvailableModels([]);
      setSelectedModel(null);
      setFormData(prev => ({ ...prev, model_id: 0 }));
      setModelSearchTerm('');
    }
  }, [selectedSymbol]);

  // Filtrer les modèles selon le terme de recherche
  const filteredModels = availableModels.filter(model =>
    model.name.toLowerCase().includes(modelSearchTerm.toLowerCase()) ||
    model.type.toLowerCase().includes(modelSearchTerm.toLowerCase())
  );

  // Modèles recommandés (avec le plus de prédictions)
  const recommendedModels = availableModels
    .sort((a, b) => b.prediction_count - a.prediction_count)
    .slice(0, 10);

  // Fonction pour rechercher des modèles via l'API
  const searchModels = async (searchTerm: string) => {
    if (!searchTerm.trim() || !selectedSymbol) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const response = await backtestingApi.getModelsForSymbol(selectedSymbol, 50, 0, searchTerm);
      setSearchResults(response.models);
    } catch (error) {
      console.error('Erreur lors de la recherche:', error);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Debounced search
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (modelSearchTerm.trim()) {
        searchModels(modelSearchTerm);
      } else {
        setSearchResults([]);
      }
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [modelSearchTerm, selectedSymbol]);

  useEffect(() => {
    if (formData.model_id && formData.model_id !== 0) {
      backtestingApi.getAvailableDatesForModel(formData.model_id)
        .then(dates => {
          setPredictionDates(dates as any);
          // Auto-remplir les dates si disponibles
          if (dates.available_dates && dates.available_dates.length > 0) {
            const startDate = dates.available_dates[0];
            const endDate = dates.available_dates[dates.available_dates.length - 1];
            setFormData(prev => ({
              ...prev,
              start_date: startDate,
              end_date: endDate
            }));
          }
        })
        .catch(error => {
          console.error('Erreur lors du chargement des dates:', error);
          setPredictionDates(null);
        });
    } else {
      setPredictionDates(null);
    }
  }, [formData.model_id]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  // Fermer le dropdown quand on clique ailleurs
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      if (!target.closest('.model-dropdown-container')) {
        setShowModelDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Nom du backtest *
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Symbole *
          </label>
          <select
            value={selectedSymbol}
            onChange={(e) => {
              setSelectedSymbol(e.target.value);
              setSelectedModel(null);
            }}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="">Sélectionner un symbole</option>
            {symbolsData?.symbols?.map((symbol) => (
              <option key={symbol.symbol} value={symbol.symbol}>
                {symbol.symbol} ({symbol.prediction_count} prédictions, {symbol.model_count} modèles)
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Modèle ML *
          </label>
          <div className="relative model-dropdown-container">
            <input
              type="text"
              value={modelSearchTerm}
              onChange={(e) => {
                setModelSearchTerm(e.target.value);
                setShowModelDropdown(true);
              }}
              onFocus={() => {
                setShowModelDropdown(true);
                // Forcer le rechargement des modèles si nécessaire
                if (availableModels.length === 0 && selectedSymbol) {
                  backtestingApi.getModelsForSymbol(selectedSymbol, 50, 0)
                    .then(response => {
                      setAvailableModels(response.models);
                    })
                    .catch(error => {
                      console.error('Erreur lors du rechargement des modèles:', error);
                    });
                }
              }}
              placeholder={selectedSymbol ? "Rechercher un modèle..." : "Sélectionnez d'abord un symbole"}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={!selectedSymbol}
            />
            
            {showModelDropdown && selectedSymbol && (
              <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                {modelSearchTerm === '' ? (
                  // Afficher les modèles recommandés quand aucun terme de recherche
                  <div>
                    <div className="px-3 py-2 bg-gray-50 text-gray-700 text-xs font-medium border-b">
                      Modèles recommandés (plus de prédictions)
                    </div>
                    {recommendedModels.map((model) => (
                      <div
                        key={model.id}
                        onClick={() => {
                          setSelectedModel(model);
                          setFormData(prev => ({ ...prev, model_id: model.id }));
                          setModelSearchTerm(model.name);
                          setShowModelDropdown(false);
                        }}
                        className="px-3 py-2 hover:bg-gray-100 cursor-pointer text-sm border-b border-gray-100 last:border-b-0"
                      >
                        <div className="font-medium">{model.name}</div>
                        <div className="text-gray-600 text-xs">
                          {model.type} - {model.prediction_count} prédictions
                        </div>
                      </div>
                    ))}
                    <div className="px-3 py-2 text-gray-500 text-xs border-t border-gray-200">
                      Tapez pour rechercher parmi {availableModels.length} modèles disponibles
                    </div>
                  </div>
                ) : (
                  // Afficher les résultats de recherche
                  <div>
                    {isSearching ? (
                      <div className="px-3 py-2 text-gray-500 text-sm">
                        🔍 Recherche en cours...
                      </div>
                    ) : searchResults.length === 0 ? (
                      <div className="px-3 py-2 text-gray-500 text-sm">
                        Aucun modèle trouvé pour "{modelSearchTerm}"
                      </div>
                    ) : (
                      <div>
                        <div className="px-3 py-2 bg-gray-50 text-gray-700 text-xs font-medium border-b">
                          {searchResults.length} modèle(s) trouvé(s) pour "{modelSearchTerm}"
                        </div>
                        {searchResults.map((model) => (
                          <div
                            key={model.id}
                            onClick={() => {
                              setSelectedModel(model);
                              setFormData(prev => ({ ...prev, model_id: model.id }));
                              setModelSearchTerm(model.name);
                              setShowModelDropdown(false);
                            }}
                            className="px-3 py-2 hover:bg-gray-100 cursor-pointer text-sm border-b border-gray-100 last:border-b-0"
                          >
                            <div className="font-medium">{model.name}</div>
                            <div className="text-gray-600 text-xs">
                              {model.type} - {model.prediction_count} prédictions
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
          
          {selectedModel && (
            <div className="mt-2 text-sm text-gray-600">
              <p><strong>Modèle sélectionné:</strong> {selectedModel.name}</p>
              <p>Période disponible: {selectedModel.date_range.start} à {selectedModel.date_range.end}</p>
              <p>Prédictions disponibles: {selectedModel.prediction_count}</p>
            </div>
          )}
          
          {selectedSymbol && availableModels.length > 0 && (
            <div className="mt-1 text-xs text-gray-500">
              {availableModels.length} modèles disponibles pour {selectedSymbol}
            </div>
          )}
          
          {selectedSymbol && availableModels.length === 0 && (
            <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
              <p><strong>Problème de chargement des modèles</strong></p>
              <p>Cliquez sur le champ de recherche pour forcer le chargement des modèles.</p>
            </div>
          )}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
          rows={3}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Stratégie de trading
          </label>
          <select
            value={formData.strategy_id || ''}
            onChange={(e) => setFormData(prev => ({ 
              ...prev, 
              strategy_id: e.target.value ? parseInt(e.target.value) : undefined 
            }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Aucune stratégie (backtesting standard)</option>
            {strategies?.data?.map((strategy) => (
              <option key={strategy.id} value={strategy.id}>
                {strategy.name} ({strategy.strategy_type})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Capital initial ($)
          </label>
          <input
            type="number"
            value={formData.initial_capital}
            onChange={(e) => setFormData(prev => ({ ...prev, initial_capital: parseFloat(e.target.value) }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="1000"
            step="1000"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Date de début *
          </label>
          <input
            type="date"
            value={formData.start_date}
            onChange={(e) => setFormData(prev => ({ ...prev, start_date: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Date de fin *
          </label>
          <input
            type="date"
            value={formData.end_date}
            onChange={(e) => setFormData(prev => ({ ...prev, end_date: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>
      </div>

      {predictionDates && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <p className="text-sm text-blue-800">
            <strong>Dates disponibles pour ce modèle:</strong><br />
            Du {new Date(predictionDates.first_prediction_date).toLocaleDateString('fr-FR')} 
            au {new Date(predictionDates.last_prediction_date).toLocaleDateString('fr-FR')}
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Taille de position (%)
          </label>
          <input
            type="number"
            value={formData.position_size_percentage}
            onChange={(e) => setFormData(prev => ({ ...prev, position_size_percentage: parseFloat(e.target.value) }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="1"
            max="100"
            step="1"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Seuil de confiance
          </label>
          <input
            type="number"
            value={formData.confidence_threshold}
            onChange={(e) => setFormData(prev => ({ ...prev, confidence_threshold: parseFloat(e.target.value) }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="0"
            max="1"
            step="0.1"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Commission (%)
          </label>
          <input
            type="number"
            value={formData.commission_rate * 100}
            onChange={(e) => setFormData(prev => ({ ...prev, commission_rate: parseFloat(e.target.value) / 100 }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="0"
            max="10"
            step="0.01"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Slippage (%)
          </label>
          <input
            type="number"
            value={formData.slippage_rate * 100}
            onChange={(e) => setFormData(prev => ({ ...prev, slippage_rate: parseFloat(e.target.value) / 100 }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="0"
            max="5"
            step="0.01"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Positions max
          </label>
          <input
            type="number"
            value={formData.max_positions}
            onChange={(e) => setFormData(prev => ({ ...prev, max_positions: parseInt(e.target.value) }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            min="1"
            max="50"
            step="1"
          />
        </div>
      </div>

      <div className="flex justify-end space-x-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
        >
          Annuler
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          Créer le backtest
        </button>
      </div>
    </form>
  );
};
