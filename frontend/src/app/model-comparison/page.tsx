'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  ChartBarIcon, 
  CpuChipIcon, 
  RocketLaunchIcon,
  LightBulbIcon,
  BrainIcon,
  CheckCircleIcon,
  XCircleIcon,
  ClockIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  MinusIcon
} from '@heroicons/react/24/outline';

import { 
  modelComparisonApi, 
  modelComparisonUtils,
  type ComparisonRequest,
  type ComparisonResult,
  type ModelRecommendation,
  type ModelInfo
} from '../../services/modelComparisonApi';

export default function ModelComparisonPage() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [comparisonResult, setComparisonResult] = useState<ComparisonResult | null>(null);
  const [isComparing, setIsComparing] = useState(false);

  const queryClient = useQueryClient();

  // Queries
  const { data: availableModels, isLoading: modelsLoading } = useQuery({
    queryKey: ['available-models'],
    queryFn: modelComparisonApi.getAvailableModels,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const { data: availableSymbols, isLoading: symbolsLoading } = useQuery({
    queryKey: ['available-symbols'],
    queryFn: modelComparisonApi.getAvailableSymbols,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  const { data: recommendations, isLoading: recommendationsLoading } = useQuery({
    queryKey: ['model-recommendations', selectedSymbol],
    queryFn: () => modelComparisonApi.getModelRecommendations({ symbol: selectedSymbol }),
    enabled: !!selectedSymbol,
    staleTime: 10 * 60 * 1000, // 10 minutes
  });

  // Mutations
  const compareModelsMutation = useMutation({
    mutationFn: (request: ComparisonRequest) => modelComparisonApi.compareSingleSymbol(request),
    onSuccess: (data) => {
      setComparisonResult(data);
      setIsComparing(false);
    },
    onError: (error) => {
      console.error('Erreur lors de la comparaison:', error);
      setIsComparing(false);
    },
  });

  // Handlers
  const handleSymbolChange = (symbol: string) => {
    setSelectedSymbol(symbol);
    setSelectedModels([]);
    setComparisonResult(null);
  };

  const handleModelToggle = (modelName: string) => {
    setSelectedModels(prev => 
      prev.includes(modelName) 
        ? prev.filter(m => m !== modelName)
        : [...prev, modelName]
    );
  };

  const handleCompare = () => {
    if (!selectedSymbol || selectedModels.length === 0) return;
    
    setIsComparing(true);
    compareModelsMutation.mutate({
      symbol: selectedSymbol,
      models_to_test: selectedModels,
    });
  };

  const handleUseRecommendations = () => {
    if (recommendations?.success && recommendations.recommendations.primary.length > 0) {
      setSelectedModels(recommendations.recommendations.primary);
    }
  };

  // Auto-select recommended models when recommendations change
  useEffect(() => {
    if (recommendations?.success && recommendations.recommendations.primary.length > 0 && selectedModels.length === 0) {
      setSelectedModels(recommendations.recommendations.primary);
    }
  }, [recommendations, selectedModels.length]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Comparaison de Modèles ML</h1>
                <p className="text-gray-600 mt-1">
                  Comparez les performances de différents modèles d'apprentissage automatique pour vos symboles
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Configuration Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Configuration</h2>
              
              {/* Symbol Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Symbole à analyser
                </label>
                <select
                  value={selectedSymbol}
                  onChange={(e) => handleSymbolChange(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={symbolsLoading}
                >
                  <option value="">Sélectionner un symbole</option>
                  {availableSymbols?.symbols.map((symbol) => (
                    <option key={symbol} value={symbol}>{symbol}</option>
                  ))}
                </select>
                {symbolsLoading && (
                  <p className="text-sm text-gray-500 mt-1">Chargement des symboles...</p>
                )}
              </div>

              {/* Model Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Modèles à comparer
                </label>
                {modelsLoading ? (
                  <p className="text-sm text-gray-500">Chargement des modèles...</p>
                ) : (
                  <div className="space-y-2">
                    {availableModels?.available_models && Object.entries(availableModels.available_models).map(([name, info]) => (
                      <label key={name} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={selectedModels.includes(name)}
                          onChange={() => handleModelToggle(name)}
                          className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                        />
                        <span className="ml-2 text-sm text-gray-700">
                          {modelComparisonUtils.getModelIcon(name)} {name}
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>

              {/* Recommendations */}
              {recommendations?.success && (
                <div className="mb-6 p-4 bg-blue-50 rounded-lg">
                  <h3 className="text-sm font-medium text-blue-900 mb-2">Recommandations</h3>
                  <div className="text-sm text-blue-800">
                    <p className="mb-2">
                      <strong>Volatilité:</strong> {recommendations.analysis.volatility_class} 
                      ({recommendations.analysis.volatility.toFixed(3)})
                    </p>
                    <p className="mb-2">
                      <strong>Tendance:</strong> {recommendations.analysis.trend_class} 
                      ({recommendations.analysis.trend.toFixed(3)})
                    </p>
                    <p className="mb-3">
                      <strong>Recommandé:</strong> {recommendations.recommendations.primary.join(', ')}
                    </p>
                    <button
                      onClick={handleUseRecommendations}
                      className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700"
                    >
                      Utiliser les recommandations
                    </button>
                  </div>
                </div>
              )}

              {/* Compare Button */}
              <button
                onClick={handleCompare}
                disabled={!selectedSymbol || selectedModels.length === 0 || isComparing}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isComparing ? (
                  <>
                    <ClockIcon className="h-4 w-4 mr-2 animate-spin" />
                    Comparaison en cours...
                  </>
                ) : (
                  <>
                    <ChartBarIcon className="h-4 w-4 mr-2" />
                    Comparer les modèles
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Results Panel */}
          <div className="lg:col-span-2">
            {comparisonResult ? (
              <div className="space-y-6">
                {/* Best Model Summary */}
                <div className="bg-white rounded-lg shadow p-6">
                  <div className="flex items-center mb-4">
                    <CheckCircleIcon className="h-6 w-6 text-green-600 mr-2" />
                    <h2 className="text-xl font-semibold text-gray-900">Meilleur Modèle</h2>
                  </div>
                  
                  <div className="bg-green-50 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <span className="text-2xl mr-2">
                        {modelComparisonUtils.getModelIcon(comparisonResult.best_model.name)}
                      </span>
                      <h3 className="text-lg font-semibold text-green-900">
                        {comparisonResult.best_model.name}
                      </h3>
                    </div>
                    <p className="text-sm text-green-800 mb-3">
                      {modelComparisonUtils.getModelDescription(comparisonResult.best_model.name)}
                    </p>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          {(comparisonResult.best_model.metrics.f1_score * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-green-800">F1-Score</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          {(comparisonResult.best_model.metrics.accuracy * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-green-800">Accuracy</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          {comparisonResult.best_model.metrics.sharpe_ratio.toFixed(3)}
                        </div>
                        <div className="text-xs text-green-800">Sharpe Ratio</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          {(comparisonResult.best_model.metrics.total_return * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-green-800">Return</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Detailed Results */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-6">Résultats Détaillés</h2>
                  
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Modèle
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Accuracy
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            F1-Score
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Sharpe
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Return
                          </th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Temps
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {Object.entries(comparisonResult.results).map(([modelName, metrics]) => {
                          const formatted = modelComparisonUtils.formatMetrics(metrics);
                          return (
                            <tr key={modelName} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center">
                                  <span className="text-lg mr-2">
                                    {modelComparisonUtils.getModelIcon(modelName)}
                                  </span>
                                  <div>
                                    <div className="text-sm font-medium text-gray-900">{modelName}</div>
                                    <div className="text-sm text-gray-500">
                                      {modelComparisonUtils.getModelDescription(modelName)}
                                    </div>
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`text-sm font-medium ${modelComparisonUtils.getPerformanceColor(metrics.accuracy, 'accuracy')}`}>
                                  {formatted.accuracy}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`text-sm font-medium ${modelComparisonUtils.getPerformanceColor(metrics.f1_score, 'f1')}`}>
                                  {formatted.f1Score}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`text-sm font-medium ${modelComparisonUtils.getPerformanceColor(metrics.sharpe_ratio, 'sharpe')}`}>
                                  {formatted.sharpeRatio}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`text-sm font-medium ${modelComparisonUtils.getPerformanceColor(metrics.total_return, 'return')}`}>
                                  {formatted.totalReturn}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {formatted.trainingTime}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Data Info */}
                <div className="bg-white rounded-lg shadow p-6">
                  <h2 className="text-xl font-semibold text-gray-900 mb-4">Informations sur les Données</h2>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {comparisonResult.data_info.train_samples}
                      </div>
                      <div className="text-sm text-gray-600">Échantillons d'entraînement</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {comparisonResult.data_info.test_samples}
                      </div>
                      <div className="text-sm text-gray-600">Échantillons de test</div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold text-blue-600">
                        {comparisonResult.data_info.features}
                      </div>
                      <div className="text-sm text-gray-600">Features</div>
                    </div>
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-lg shadow p-12 text-center">
                <ChartBarIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Aucune comparaison effectuée
                </h3>
                <p className="text-gray-600">
                  Sélectionnez un symbole et des modèles pour commencer la comparaison
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
