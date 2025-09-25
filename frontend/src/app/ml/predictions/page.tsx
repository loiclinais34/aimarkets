'use client';

import React, { useState } from 'react';
import RootLayout from '@/components/RootLayout';
import { useQuery } from 'react-query';
import { 
  BeakerIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

export default function MLPredictions() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);

  // Mock data - à remplacer par de vraies API calls
  const { data: availableSymbols } = useQuery({
    queryKey: ['available-symbols'],
    queryFn: () => Promise.resolve({ symbols: ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN'] }),
  });

  const { data: availableModels } = useQuery({
    queryKey: ['available-models'],
    queryFn: () => Promise.resolve({ 
      available_models: {
        'RandomForest': { name: 'Random Forest', description: 'Modèle d\'ensemble robuste' },
        'XGBoost': { name: 'XGBoost', description: 'Gradient boosting optimisé' },
        'LightGBM': { name: 'LightGBM', description: 'Gradient boosting rapide' },
        'NeuralNetwork': { name: 'Neural Network', description: 'Réseau de neurones' },
      }
    }),
  });

  const handleGeneratePrediction = () => {
    if (!selectedSymbol || !selectedModel) return;
    
    setIsGenerating(true);
    // Simuler une génération de prédiction
    setTimeout(() => {
      setIsGenerating(false);
    }, 3000);
  };

  return (
    <RootLayout>
      <div className="px-4 py-6 sm:px-0">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Prédictions ML</h1>
          <p className="mt-2 text-gray-600">
            Générez des prédictions avec vos modèles entraînés
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Configuration Panel */}
          <div>
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Configuration</h2>
              
              {/* Symbol Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Symbole à prédire
                </label>
                <select
                  value={selectedSymbol}
                  onChange={(e) => setSelectedSymbol(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Sélectionner un symbole</option>
                  {availableSymbols?.symbols.map((symbol) => (
                    <option key={symbol} value={symbol}>{symbol}</option>
                  ))}
                </select>
              </div>

              {/* Model Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Modèle à utiliser
                </label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Sélectionner un modèle</option>
                  {availableModels?.available_models && Object.entries(availableModels.available_models).map(([name, info]) => (
                    <option key={name} value={name}>{name}</option>
                  ))}
                </select>
              </div>

              {/* Generate Button */}
              <button
                onClick={handleGeneratePrediction}
                disabled={!selectedSymbol || !selectedModel || isGenerating}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isGenerating ? (
                  <>
                    <ClockIcon className="h-4 w-4 mr-2 animate-spin" />
                    Génération en cours...
                  </>
                ) : (
                  <>
                    <BeakerIcon className="h-4 w-4 mr-2" />
                    Générer la prédiction
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Results Panel */}
          <div>
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-6">Résultats</h2>
              
              {isGenerating ? (
                <div className="text-center py-12">
                  <ClockIcon className="h-16 w-16 text-blue-400 mx-auto mb-4 animate-spin" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Génération de la prédiction
                  </h3>
                  <p className="text-gray-600">
                    Analyse des données et calcul des prédictions en cours...
                  </p>
                </div>
              ) : selectedSymbol && selectedModel ? (
                <div className="space-y-6">
                  {/* Prediction Summary */}
                  <div className="bg-green-50 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <CheckCircleIcon className="h-6 w-6 text-green-600 mr-2" />
                      <h3 className="text-lg font-semibold text-green-900">
                        Prédiction pour {selectedSymbol}
                      </h3>
                    </div>
                    <p className="text-sm text-green-800 mb-3">
                      Modèle utilisé: {selectedModel}
                    </p>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          HAUSSE
                        </div>
                        <div className="text-xs text-green-800">Direction</div>
                      </div>
                      <div className="text-center">
                        <div className="text-2xl font-bold text-green-600">
                          0.75
                        </div>
                        <div className="text-xs text-green-800">Confiance</div>
                      </div>
                    </div>
                  </div>

                  {/* Detailed Metrics */}
                  <div className="space-y-4">
                    <h4 className="text-md font-medium text-gray-900">Métriques détaillées</h4>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="bg-gray-50 p-3 rounded">
                        <div className="text-sm text-gray-600">Probabilité Hausse</div>
                        <div className="text-lg font-semibold text-green-600">75%</div>
                      </div>
                      <div className="bg-gray-50 p-3 rounded">
                        <div className="text-sm text-gray-600">Probabilité Baisse</div>
                        <div className="text-lg font-semibold text-red-600">25%</div>
                      </div>
                      <div className="bg-gray-50 p-3 rounded">
                        <div className="text-sm text-gray-600">Retour attendu</div>
                        <div className="text-lg font-semibold text-blue-600">+2.3%</div>
                      </div>
                      <div className="bg-gray-50 p-3 rounded">
                        <div className="text-sm text-gray-600">Risque estimé</div>
                        <div className="text-lg font-semibold text-orange-600">Moyen</div>
                      </div>
                    </div>
                  </div>

                  {/* Risk Warning */}
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                    <div className="flex items-center mb-2">
                      <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 mr-2" />
                      <h4 className="text-sm font-medium text-yellow-900">Avertissement</h4>
                    </div>
                    <p className="text-sm text-yellow-800">
                      Les prédictions sont basées sur des données historiques et ne garantissent pas les résultats futurs. 
                      Utilisez ces informations à des fins d'analyse uniquement.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <BeakerIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    Aucune prédiction générée
                  </h3>
                  <p className="text-gray-600">
                    Sélectionnez un symbole et un modèle pour générer une prédiction
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </RootLayout>
  );
}
