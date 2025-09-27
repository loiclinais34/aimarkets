'use client';

import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from 'react-query';
import { apiService, screenerApi } from '@/services/api';
import { toast } from 'react-hot-toast';
import { 
  MagnifyingGlassIcon, 
  ChartBarIcon, 
  ClockIcon, 
  ArrowTrendingUpIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

interface OpportunitySearchProps {
  className?: string;
  onSearchCompleted?: (searchId: string) => void;
}

interface SearchParameters {
  target_return_percentage: number;
  time_horizon_days: number;
  risk_tolerance: number;
  confidence_threshold: number;
}

export default function OpportunitySearch({ className = '', onSearchCompleted }: OpportunitySearchProps) {
  const queryClient = useQueryClient();
  const [isSearching, setIsSearching] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [currentSearchId, setCurrentSearchId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<any>(null);
  
  const [parameters, setParameters] = useState<SearchParameters>({
    target_return_percentage: 5.0,
    time_horizon_days: 30,
    risk_tolerance: 0.5,
    confidence_threshold: 0.7
  });

  const handleParameterChange = (key: keyof SearchParameters, value: number) => {
    setParameters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const searchOpportunitiesMutation = useMutation(
    async (searchParams: SearchParameters) => {
      const response = await apiService.searchOpportunities(searchParams);
      return response;
    },
    {
      onSuccess: (data) => {
        console.log('Search opportunities response:', data);
        if (data.task_id && data.search_id) {
          console.log('Setting task ID:', data.task_id, 'and search ID:', data.search_id);
          setCurrentTaskId(data.task_id);
          setCurrentSearchId(data.search_id);
          toast.success('Recherche d\'opportunités lancée');
        } else {
          console.log('No task ID or search ID, search completed immediately');
          toast.success(`Recherche terminée: ${data.opportunities_found || 0} opportunités trouvées`);
          queryClient.invalidateQueries(['latest-opportunities']);
          setIsSearching(false);
        }
      },
      onError: (error: any) => {
        toast.error(`Erreur lors de la recherche: ${error.message}`);
        setIsSearching(false);
      }
    }
  );

  // Polling pour le statut de la tâche
  useEffect(() => {
    if (!currentTaskId) return;

    const pollTaskStatus = async () => {
      try {
        console.log('Polling task status for:', currentTaskId);
        const response = await screenerApi.getTaskStatus(currentTaskId);
        console.log('Task status response:', response);
        setTaskStatus(response);
        
        if (response.state === 'SUCCESS') {
          console.log('Task completed successfully:', response.result);
          toast.success(`Recherche terminée: ${response.result?.total_opportunities_found || 0} opportunités trouvées`);
          // Invalider les queries pour les opportunités de cette recherche spécifique
          if (currentSearchId) {
            queryClient.invalidateQueries(['search-opportunities', currentSearchId]);
            // Notifier le parent que la recherche est terminée
            if (onSearchCompleted) {
              onSearchCompleted(currentSearchId);
            }
          }
          queryClient.invalidateQueries(['latest-opportunities']);
          setIsSearching(false);
          setCurrentTaskId(null);
          setCurrentSearchId(null);
        } else if (response.state === 'FAILURE') {
          console.log('Task failed:', (response as any).error);
          toast.error(`Erreur lors de la recherche: ${(response as any).error || 'Erreur inconnue'}`);
          setIsSearching(false);
          setCurrentTaskId(null);
          setCurrentSearchId(null);
        } else {
          console.log('Task in progress:', response.state, response.progress);
        }
      } catch (error) {
        console.error('Erreur lors du polling:', error);
      }
    };

    const interval = setInterval(pollTaskStatus, 2000); // Polling toutes les 2 secondes
    return () => clearInterval(interval);
  }, [currentTaskId, currentSearchId, queryClient]);

  const handleSearch = () => {
    setIsSearching(true);
    searchOpportunitiesMutation.mutate(parameters);
  };

  const getRiskLevel = (riskTolerance: number, confidenceThreshold: number) => {
    // Calcul du risque combiné : plus la confiance est élevée, plus le risque est faible
    // Formule : risque = risk_tolerance * (1 - confidence_threshold)
    const combinedRisk = riskTolerance * (1 - confidenceThreshold);
    
    if (combinedRisk <= 0.2) return { label: 'Très Conservateur', color: 'text-green-600', bg: 'bg-green-100' };
    if (combinedRisk <= 0.4) return { label: 'Conservateur', color: 'text-green-500', bg: 'bg-green-50' };
    if (combinedRisk <= 0.6) return { label: 'Modéré', color: 'text-yellow-600', bg: 'bg-yellow-100' };
    if (combinedRisk <= 0.8) return { label: 'Élevé', color: 'text-orange-600', bg: 'bg-orange-100' };
    return { label: 'Très Agressif', color: 'text-red-600', bg: 'bg-red-100' };
  };

  const riskLevel = getRiskLevel(parameters.risk_tolerance, parameters.confidence_threshold);

  const getProgressSteps = () => {
    if (!taskStatus) return [];
    
    const steps = [
      { name: 'Entraînement des modèles', status: 'pending' },
      { name: 'Calcul des prédictions', status: 'pending' },
      { name: 'Filtrage des opportunités', status: 'pending' },
      { name: 'Finalisation', status: 'pending' }
    ];
    
    if (taskStatus.state === 'PROGRESS') {
      const progress = taskStatus.progress || 0;
      if (progress < 25) {
        steps[0].status = 'current';
      } else if (progress < 50) {
        steps[0].status = 'completed';
        steps[1].status = 'current';
      } else if (progress < 75) {
        steps[0].status = 'completed';
        steps[1].status = 'completed';
        steps[2].status = 'current';
      } else {
        steps[0].status = 'completed';
        steps[1].status = 'completed';
        steps[2].status = 'completed';
        steps[3].status = 'current';
      }
    } else if (taskStatus.state === 'SUCCESS') {
      steps.forEach(step => step.status = 'completed');
    }
    
    return steps;
  };

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <MagnifyingGlassIcon className="h-6 w-6 text-blue-600 mr-3" />
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Recherche d'Opportunités</h3>
            <p className="text-sm text-gray-500">Paramétrez votre recherche de signaux de trading</p>
          </div>
        </div>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          {showAdvanced ? 'Paramètres simples' : 'Paramètres avancés'}
        </button>
      </div>

      {/* Paramètres principaux */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        {/* Rendement attendu */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <ArrowTrendingUpIcon className="h-4 w-4 inline mr-1" />
            Rendement attendu (%)
          </label>
          <div className="relative">
            <input
              type="number"
              min="1"
              max="50"
              step="0.5"
              value={parameters.target_return_percentage}
              onChange={(e) => handleParameterChange('target_return_percentage', parseFloat(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <span className="absolute right-3 top-2 text-sm text-gray-500">%</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Rendement cible sur la période
          </p>
        </div>

        {/* Horizon temporel */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            <ClockIcon className="h-4 w-4 inline mr-1" />
            Horizon temporel (jours)
          </label>
          <div className="relative">
            <input
              type="number"
              min="1"
              max="365"
              step="1"
              value={parameters.time_horizon_days}
              onChange={(e) => handleParameterChange('time_horizon_days', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            <span className="absolute right-3 top-2 text-sm text-gray-500">jours</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">
            Période d'investissement
          </p>
        </div>
      </div>

      {/* Paramètres avancés */}
      {showAdvanced && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6 p-4 bg-gray-50 rounded-lg">
          {/* Tolérance au risque */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <ExclamationTriangleIcon className="h-4 w-4 inline mr-1" />
              Tolérance au risque
            </label>
            <div className="space-y-2">
              <input
                type="range"
                min="0.1"
                max="1.0"
                step="0.1"
                value={parameters.risk_tolerance}
                onChange={(e) => handleParameterChange('risk_tolerance', parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500">
                <span>Conservateur</span>
                <span className={`px-2 py-1 rounded text-xs font-medium ${riskLevel.bg} ${riskLevel.color}`}>
                  {riskLevel.label}
                </span>
                <span>Agressif</span>
              </div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Influence le seuil de confiance requis
            </p>
          </div>

          {/* Seuil de confiance */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <CheckCircleIcon className="h-4 w-4 inline mr-1" />
              Seuil de confiance minimum
            </label>
            
            {/* Slider pour le niveau de confiance */}
            <div className="mb-3">
              <input
                type="range"
                min="0.5"
                max="0.95"
                step="0.05"
                value={parameters.confidence_threshold}
                onChange={(e) => handleParameterChange('confidence_threshold', parseFloat(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer slider"
                style={{
                  background: `linear-gradient(to right, #ef4444 0%, #f97316 25%, #eab308 50%, #22c55e 75%, #16a34a 100%)`
                }}
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>50%</span>
                <span>60%</span>
                <span>70%</span>
                <span>80%</span>
                <span>90%</span>
              </div>
            </div>
            
            {/* Affichage de la valeur actuelle */}
            <div className="relative">
              <input
                type="number"
                min="0.5"
                max="0.95"
                step="0.05"
                value={parameters.confidence_threshold}
                onChange={(e) => handleParameterChange('confidence_threshold', parseFloat(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <span className="absolute right-3 top-2 text-sm text-gray-500">%</span>
            </div>
            
            {/* Indicateur de niveau de confiance */}
            <div className="mt-2 flex items-center space-x-2">
              <div className={`px-2 py-1 rounded-full text-xs font-medium ${
                parameters.confidence_threshold >= 0.8 ? 'bg-green-100 text-green-800' :
                parameters.confidence_threshold >= 0.7 ? 'bg-yellow-100 text-yellow-800' :
                parameters.confidence_threshold >= 0.6 ? 'bg-orange-100 text-orange-800' :
                'bg-red-100 text-red-800'
              }`}>
                {parameters.confidence_threshold >= 0.8 ? 'Très élevée' :
                 parameters.confidence_threshold >= 0.7 ? 'Élevée' :
                 parameters.confidence_threshold >= 0.6 ? 'Modérée' : 'Faible'}
              </div>
              <span className="text-xs text-gray-500">
                Confiance requise
              </span>
            </div>
            
            <p className="text-xs text-gray-500 mt-1">
              Plus le seuil est élevé, plus les opportunités sont filtrées
            </p>
          </div>
        </div>
      )}

      {/* Résumé des paramètres */}
      <div className="mb-6 p-4 bg-blue-50 rounded-lg">
        <h4 className="text-sm font-medium text-blue-900 mb-2">Résumé de la recherche</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-blue-700">Rendement:</span>
            <span className="font-medium text-blue-900 ml-1">{parameters.target_return_percentage}%</span>
          </div>
          <div>
            <span className="text-blue-700">Horizon:</span>
            <span className="font-medium text-blue-900 ml-1">{parameters.time_horizon_days} jours</span>
          </div>
          <div>
            <span className="text-blue-700">Risque:</span>
            <span className={`font-medium ml-1 ${riskLevel.color}`}>{riskLevel.label}</span>
          </div>
          <div>
            <span className="text-blue-700">Confiance:</span>
            <span className="font-medium text-blue-900 ml-1">{(parameters.confidence_threshold * 100).toFixed(0)}%</span>
          </div>
        </div>
        
        {/* Indicateur de risque combiné */}
        <div className="mt-3 pt-3 border-t border-blue-200">
          <div className="flex items-center justify-between">
            <span className="text-sm text-blue-700">Profil de risque combiné:</span>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${riskLevel.bg} ${riskLevel.color}`}>
              {riskLevel.label}
            </div>
          </div>
          <p className="text-xs text-blue-600 mt-1">
            Basé sur la tolérance au risque ({parameters.risk_tolerance}) et le niveau de confiance ({(parameters.confidence_threshold * 100).toFixed(0)}%)
          </p>
        </div>
      </div>

      {/* Barre de progression */}
      {isSearching && taskStatus && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <h4 className="text-sm font-medium text-gray-900">Progression de la recherche</h4>
            <span className="text-sm text-gray-500">{taskStatus.progress || 0}%</span>
          </div>
          
          {/* Barre de progression globale */}
          <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${taskStatus.progress || 0}%` }}
            ></div>
          </div>
          
          {/* Étapes détaillées */}
          <div className="space-y-2">
            {getProgressSteps().map((step, index) => (
              <div key={index} className="flex items-center text-sm">
                <div className={`w-3 h-3 rounded-full mr-3 ${
                  step.status === 'completed' ? 'bg-green-500' :
                  step.status === 'current' ? 'bg-blue-500' : 'bg-gray-300'
                }`}></div>
                <span className={`${
                  step.status === 'completed' ? 'text-green-700' :
                  step.status === 'current' ? 'text-blue-700 font-medium' : 'text-gray-500'
                }`}>
                  {step.name}
                </span>
              </div>
            ))}
          </div>
          
          {/* Informations de statut */}
          {taskStatus.current_symbol && (
            <div className="mt-3 text-xs text-gray-600">
              Traitement de: <span className="font-medium">{taskStatus.current_symbol}</span>
            </div>
          )}
          
          {taskStatus.successful_updates !== undefined && (
            <div className="mt-2 text-xs text-gray-600">
              Modèles entraînés: <span className="font-medium">{taskStatus.successful_updates}</span>
            </div>
          )}
        </div>
      )}

      {/* Bouton de recherche */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-500">
          <ChartBarIcon className="h-4 w-4 inline mr-1" />
          Modèles utilisés: Random Forest, XGBoost, LightGBM, Neural Networks
        </div>
        <button
          onClick={handleSearch}
          disabled={isSearching}
          className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSearching ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Recherche en cours...
            </>
          ) : (
            <>
              <MagnifyingGlassIcon className="h-4 w-4 mr-2" />
              Lancer la recherche
            </>
          )}
        </button>
      </div>
    </div>
  );
}
