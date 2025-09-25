'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  TradingStrategy, 
  StrategyDetail, 
  PredefinedStrategy,
  StrategyCreateForm 
} from '../../types/strategies';
import { strategiesApi } from '../../services/strategiesApi';
import { StrategyList, StrategyForm } from '../../components/strategies/StrategyManagement';
import { HomeIcon, PlusIcon, CogIcon, MagnifyingGlassIcon, ChartBarSquareIcon } from '@heroicons/react/24/outline';

export default function StrategiesPage() {
  const [showForm, setShowForm] = useState(false);
  const [editingStrategy, setEditingStrategy] = useState<TradingStrategy | null>(null);
  const [viewingStrategy, setViewingStrategy] = useState<number | null>(null);
  const [predefinedStrategy, setPredefinedStrategy] = useState<PredefinedStrategy | null>(null);

  const queryClient = useQueryClient();

  const createMutation = useMutation(
    (strategyData: StrategyCreateForm) => strategiesApi.createStrategy(strategyData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('strategies');
        setShowForm(false);
        setPredefinedStrategy(null);
        alert('Stratégie créée avec succès!');
      },
      onError: (error: any) => {
        alert(`Erreur lors de la création: ${error.message}`);
      }
    }
  );

  const updateMutation = useMutation(
    ({ id, updates }: { id: number; updates: Partial<TradingStrategy> }) => 
      strategiesApi.updateStrategy(id, updates),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('strategies');
        setEditingStrategy(null);
        alert('Stratégie mise à jour avec succès!');
      },
      onError: (error: any) => {
        alert(`Erreur lors de la mise à jour: ${error.message}`);
      }
    }
  );

  const initializeAllMutation = useMutation(
    () => strategiesApi.initializePredefinedStrategies(),
    {
      onSuccess: (result) => {
        queryClient.invalidateQueries('strategies');
        const successCount = result.data?.results?.filter(r => r.status === 'created').length || 0;
        alert(`${successCount} stratégies prédéfinies initialisées avec succès!`);
      },
      onError: (error: any) => {
        alert(`Erreur lors de l'initialisation: ${error.message}`);
      }
    }
  );

  const handleCreateStrategy = (strategyData: StrategyCreateForm) => {
    createMutation.mutate(strategyData);
  };

  const handleEditStrategy = (strategy: TradingStrategy) => {
    setEditingStrategy(strategy);
    setShowForm(true);
  };

  const handleDeleteStrategy = (strategyId: number) => {
    queryClient.invalidateQueries('strategies');
  };

  const handleViewDetails = (strategyId: number) => {
    setViewingStrategy(strategyId);
  };

  const handleTestAPI = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/strategies/');
      const data = await response.json();
      console.log('Test API Response:', data);
      alert(`API Test: ${data.strategies?.length || 0} stratégies trouvées`);
    } catch (error) {
      console.error('API Test Error:', error);
      alert(`Erreur API: ${error}`);
    }
  };

  const handleLoadPredefined = async (strategyType: string) => {
    try {
      const result = await strategiesApi.getPredefinedStrategy(strategyType);
      setPredefinedStrategy(result.data || null);
      setShowForm(true);
    } catch (error: any) {
      alert(`Erreur lors du chargement: ${error.message}`);
    }
  };

  const { data: predefinedTypes } = useQuery(
    'predefined-strategy-types',
    () => strategiesApi.getPredefinedTypes(),
    {
      refetchOnWindowFocus: false
    }
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="flex space-x-8">
              <a
                href="/"
                className="flex items-center py-4 px-1 border-b-2 font-medium text-sm border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                <HomeIcon className="h-5 w-5 mr-2" />
                Dashboard
              </a>
              <a
                href="/screener"
                className="flex items-center py-4 px-1 border-b-2 font-medium text-sm border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
                Screener
              </a>
              <div className="flex items-center py-4 px-1 border-b-2 font-medium text-sm border-blue-500 text-blue-600">
                <CogIcon className="h-5 w-5 mr-2" />
                Stratégies
              </div>
              <a
                href="/backtesting"
                className="flex items-center py-4 px-1 border-b-2 font-medium text-sm border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                <ChartBarSquareIcon className="h-5 w-5 mr-2" />
                Backtesting
              </a>
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <CogIcon className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Stratégies de Trading</h1>
                <p className="text-sm text-gray-600">Gérez vos stratégies de trading personnalisées</p>
              </div>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowForm(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Nouvelle Stratégie
              </button>
              <button
                onClick={() => initializeAllMutation.mutate()}
                disabled={initializeAllMutation.isLoading}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50"
              >
                {initializeAllMutation.isLoading ? 'Initialisation...' : 'Initialiser Toutes'}
              </button>
              <button
                onClick={handleTestAPI}
                className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
              >
                Test API
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stratégies prédéfinies */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Stratégies Prédéfinies</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {predefinedTypes?.data?.map((strategyType) => (
              <div key={strategyType.type} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <h3 className="font-medium text-gray-900 mb-2">{strategyType.name}</h3>
                <p className="text-sm text-gray-600 mb-3">{strategyType.description}</p>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleLoadPredefined(strategyType.type)}
                    className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded hover:bg-blue-200"
                  >
                    Charger
                  </button>
                  <button
                    onClick={() => {/* TODO: Implémenter handleInitializePredefined */}}
                    className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded hover:bg-green-200"
                  >
                    Initialiser
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Liste des stratégies */}
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Mes Stratégies</h2>
          <StrategyList
            onEdit={handleEditStrategy}
            onDelete={handleDeleteStrategy}
            onViewDetails={handleViewDetails}
          />
        </div>

        {/* Formulaire de création/édition */}
        {showForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold">
                  {editingStrategy ? 'Modifier la Stratégie' : predefinedStrategy ? 'Stratégie Prédéfinie' : 'Nouvelle Stratégie'}
                </h2>
                <button
                  onClick={() => {
                    setShowForm(false);
                    setEditingStrategy(null);
                    setPredefinedStrategy(null);
                  }}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
              <StrategyForm
                strategy={editingStrategy || undefined}
                predefinedStrategy={predefinedStrategy || undefined}
                onSave={handleCreateStrategy}
                onCancel={() => {
                  setShowForm(false);
                  setEditingStrategy(null);
                  setPredefinedStrategy(null);
                }}
              />
            </div>
          </div>
        )}

        {/* Modal de détails */}
        {viewingStrategy && (
          <StrategyDetailsModal
            strategyId={viewingStrategy}
            onClose={() => setViewingStrategy(null)}
          />
        )}
      </div>
    </div>
  );
}

interface StrategyDetailsModalProps {
  strategyId: number;
  onClose: () => void;
}

const StrategyDetailsModal: React.FC<StrategyDetailsModalProps> = ({
  strategyId,
  onClose
}) => {
  const { data: strategyDetail, isLoading } = useQuery(
    ['strategy-detail', strategyId],
    () => strategiesApi.getStrategy(strategyId),
    {
      refetchOnWindowFocus: false
    }
  );

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!strategyDetail) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Erreur</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
          </div>
          <p className="text-red-600">Stratégie non trouvée</p>
        </div>
      </div>
    );
  }

  const { strategy, rules, parameters } = strategyDetail;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold">{strategy.name}</h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>

        <div className="space-y-6">
          {/* Informations générales */}
          <div>
            <h3 className="text-lg font-medium mb-3">Informations Générales</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Type</p>
                  <p className="font-medium">{strategy.strategy_type}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Statut</p>
                  <p className="font-medium">{strategy.is_active ? 'Actif' : 'Inactif'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Créé par</p>
                  <p className="font-medium">{strategy.created_by}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-600">Date de création</p>
                  <p className="font-medium">{new Date(strategy.created_at).toLocaleDateString('fr-FR')}</p>
                </div>
              </div>
              <div className="mt-3">
                <p className="text-sm text-gray-600">Description</p>
                <p className="font-medium">{strategy.description}</p>
              </div>
            </div>
          </div>

          {/* Règles */}
          <div>
            <h3 className="text-lg font-medium mb-3">Règles de Trading ({rules.length})</h3>
            <div className="space-y-3">
              {rules.map((rule) => (
                <div key={rule.id} className="bg-blue-50 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-medium text-blue-900">{rule.rule_name}</h4>
                    <span className="text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded">
                      {rule.rule_type}
                    </span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-blue-700 font-medium">Condition:</span>
                      <p className="text-blue-800">{rule.rule_condition}</p>
                    </div>
                    <div>
                      <span className="text-blue-700 font-medium">Action:</span>
                      <p className="text-blue-800">{rule.rule_action}</p>
                    </div>
                  </div>
                  <div className="mt-2 text-xs text-blue-600">
                    Priorité: {rule.priority}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Paramètres */}
          {parameters.length > 0 && (
            <div>
              <h3 className="text-lg font-medium mb-3">Paramètres ({parameters.length})</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {parameters.map((param) => (
                  <div key={param.id} className="bg-green-50 rounded-lg p-4">
                    <h4 className="font-medium text-green-900 mb-2">{param.parameter_name}</h4>
                    <div className="text-sm text-green-800">
                      <p><strong>Type:</strong> {param.parameter_type}</p>
                      <p><strong>Valeur par défaut:</strong> {param.default_value}</p>
                      {param.description && <p><strong>Description:</strong> {param.description}</p>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
