'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';

interface AsyncComparisonRequest {
  symbol: string;
  models_to_test?: string[];
  parameters?: Record<string, Record<string, any>>;
}

interface TaskStatus {
  task_id: string;
  status: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  progress?: number;
  message?: string;
  model_name?: string;
  symbol?: string;
  details?: any;
  result?: any;
  error?: string;
}

interface ModelResult {
  model_name: string;
  symbol: string;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc?: number;
  training_time: number;
  status: string;
}

const AsyncModelComparison: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [selectedModels, setSelectedModels] = useState<string[]>([]);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isRunning, setIsRunning] = useState(false);
  
  const queryClient = useQueryClient();

  // Récupération des symboles disponibles
  const { data: symbolsData } = useQuery({
    queryKey: ['available-symbols'],
    queryFn: async () => {
      const response = await fetch('/api/v1/model-comparison/available-symbols');
      return response.json();
    },
  });

  // Récupération des modèles disponibles
  const { data: modelsData } = useQuery({
    queryKey: ['available-models'],
    queryFn: async () => {
      const response = await fetch('/api/v1/model-comparison/available-models');
      return response.json();
    },
  });

  // Surveillance du statut de la tâche
  const { data: taskStatus, refetch: refetchTaskStatus } = useQuery({
    queryKey: ['task-status', taskId],
    queryFn: async () => {
      if (!taskId) return null;
      const response = await fetch(`/api/v1/model-comparison/task-status/${taskId}`);
      return response.json();
    },
    enabled: !!taskId && isRunning,
    refetchInterval: 2000, // Rafraîchir toutes les 2 secondes
  });

  // Mutation pour lancer la comparaison asynchrone
  const startComparisonMutation = useMutation({
    mutationFn: async (request: AsyncComparisonRequest) => {
      const response = await fetch('/api/v1/model-comparison/compare-async', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
      return response.json();
    },
    onSuccess: (data) => {
      setTaskId(data.task_id);
      setIsRunning(true);
    },
    onError: (error) => {
      console.error('Erreur lors du lancement de la comparaison:', error);
    },
  });

  // Effet pour arrêter la surveillance quand la tâche est terminée
  useEffect(() => {
    if (taskStatus?.status === 'SUCCESS' || taskStatus?.status === 'FAILURE') {
      setIsRunning(false);
    }
  }, [taskStatus?.status]);

  const handleStartComparison = () => {
    if (!selectedSymbol || selectedModels.length === 0) {
      alert('Veuillez sélectionner un symbole et au moins un modèle');
      return;
    }

    const request: AsyncComparisonRequest = {
      symbol: selectedSymbol,
      models_to_test: selectedModels,
      parameters: {
        PyTorchLSTM: {
          sequence_length: 3,
          hidden_sizes: [8],
          epochs: 2,
          batch_size: 2,
        },
      },
    };

    startComparisonMutation.mutate(request);
  };

  const handleModelToggle = (modelName: string) => {
    setSelectedModels(prev => 
      prev.includes(modelName) 
        ? prev.filter(m => m !== modelName)
        : [...prev, modelName]
    );
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING': return 'text-yellow-600';
      case 'PROGRESS': return 'text-blue-600';
      case 'SUCCESS': return 'text-green-600';
      case 'FAILURE': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'PENDING': return '⏳';
      case 'PROGRESS': return '🔄';
      case 'SUCCESS': return '✅';
      case 'FAILURE': return '❌';
      default: return '❓';
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">
        Comparaison Asynchrone de Modèles ML
      </h1>

      {/* Configuration */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Configuration</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Sélection du symbole */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Symbole à analyser
            </label>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Sélectionner un symbole</option>
              {symbolsData?.symbols?.map((symbol: string) => (
                <option key={symbol} value={symbol}>{symbol}</option>
              ))}
            </select>
          </div>

          {/* Sélection des modèles */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Modèles à comparer
            </label>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {modelsData?.available_models && Object.entries(modelsData.available_models).map(([name, info]: [string, any]) => (
                <label key={name} className="flex items-center">
                  <input
                    type="checkbox"
                    checked={selectedModels.includes(name)}
                    onChange={() => handleModelToggle(name)}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    {info.name} - {info.description}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={handleStartComparison}
            disabled={!selectedSymbol || selectedModels.length === 0 || isRunning}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isRunning ? '🔄 Comparaison en cours...' : '🚀 Lancer la comparaison asynchrone'}
          </button>
        </div>
      </div>

      {/* Statut de la tâche */}
      {taskId && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Statut de la tâche</h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-gray-700">Task ID:</span>
              <span className="text-sm text-gray-600 font-mono">{taskId}</span>
            </div>
            
            {taskStatus && (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Statut:</span>
                  <span className={`text-sm font-medium ${getStatusColor(taskStatus.status)}`}>
                    {getStatusIcon(taskStatus.status)} {taskStatus.status}
                  </span>
                </div>
                
                {taskStatus.progress !== undefined && (
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">Progrès:</span>
                      <span className="text-sm text-gray-600">{taskStatus.progress}%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${taskStatus.progress}%` }}
                      ></div>
                    </div>
                  </div>
                )}
                
                {taskStatus.message && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Message:</span>
                    <span className="text-sm text-gray-600">{taskStatus.message}</span>
                  </div>
                )}
                
                {taskStatus.model_name && (
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-700">Modèle actuel:</span>
                    <span className="text-sm text-gray-600">{taskStatus.model_name}</span>
                  </div>
                )}
                
                {/* Détails pour PyTorchLSTM */}
                {taskStatus.model_name === 'PyTorchLSTM' && taskStatus.details && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-2">Détails PyTorchLSTM:</h3>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      {taskStatus.details.epoch && (
                        <div>
                          <span className="font-medium">Epoch:</span> {taskStatus.details.epoch}/{taskStatus.details.total_epochs}
                        </div>
                      )}
                      {taskStatus.details.loss && (
                        <div>
                          <span className="font-medium">Loss:</span> {taskStatus.details.loss.toFixed(4)}
                        </div>
                      )}
                      {taskStatus.details.val_accuracy && (
                        <div>
                          <span className="font-medium">Val Accuracy:</span> {taskStatus.details.val_accuracy.toFixed(4)}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}

      {/* Résultats */}
      {taskStatus?.status === 'SUCCESS' && taskStatus.result && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Résultats</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {taskStatus.result.results && Object.entries(taskStatus.result.results).map(([modelName, metrics]: [string, any]) => (
              <div key={modelName} className="border rounded-lg p-4">
                <h3 className="text-lg font-medium text-gray-900 mb-2">{modelName}</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span>Accuracy:</span>
                    <span className="font-medium">{(metrics.accuracy * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span>F1-Score:</span>
                    <span className="font-medium">{metrics.f1_score.toFixed(3)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Temps d'entraînement:</span>
                    <span className="font-medium">{metrics.training_time.toFixed(2)}s</span>
                  </div>
                  {metrics.roc_auc && (
                    <div className="flex justify-between">
                      <span>ROC AUC:</span>
                      <span className="font-medium">{metrics.roc_auc.toFixed(3)}</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Erreur */}
      {taskStatus?.status === 'FAILURE' && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <h2 className="text-xl font-semibold text-red-900 mb-2">Erreur</h2>
          <p className="text-red-700">{taskStatus.error || 'Une erreur est survenue'}</p>
        </div>
      )}
    </div>
  );
};

export default AsyncModelComparison;
