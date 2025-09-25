'use client';

import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient, useQuery } from 'react-query';
import { apiService } from '@/services/api';
import { toast } from 'react-hot-toast';
import { ArrowPathIcon, CloudArrowUpIcon, ClockIcon, CheckCircleIcon, ExclamationTriangleIcon, ChartBarIcon } from '@heroicons/react/24/outline';

interface TaskStatus {
  task_id: string;
  state: string;
  status: string;
  progress?: number;
  current_symbol?: string;
  total_symbols?: number;
  result?: any;
  error?: string;
}

interface DataUpdateControlsProps {
  className?: string;
}

export default function DataUpdateControls({ className = '' }: DataUpdateControlsProps) {
  const queryClient = useQueryClient();
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null);

  // Récupérer le statut des données
  const { data: dataStatus, isLoading: statusLoading } = useQuery(
    'dataUpdateStatus',
    () => apiService.getDataUpdateStatus(),
    {
      refetchInterval: 60 * 60 * 1000, // Refetch every 1 hour
      staleTime: 1000,
    }
  );

  // Mutation pour déclencher la mise à jour
  const updateDataMutation = useMutation(
    async () => {
      const response = await apiService.triggerDataUpdate();
      return response;
    },
    {
      onSuccess: (data) => {
        setCurrentTaskId(data.task_id);
        toast.success('Mise à jour des données déclenchée !');
        queryClient.invalidateQueries('dataUpdateStatus');
        queryClient.invalidateQueries('dataStats');
        queryClient.invalidateQueries('latestOpportunities');
      },
      onError: (error: any) => {
        toast.error(`Erreur lors de la mise à jour: ${error.message}`);
      },
    }
  );

  // Suivi du statut de la tâche
  useEffect(() => {
    if (!currentTaskId) return;

    const interval = setInterval(async () => {
      try {
        const response = await apiService.getTaskStatus(currentTaskId);
        
        if (response.success) {
          setTaskStatus(response.data);
          
          // Si la tâche est terminée, arrêter le polling
          if (response.data.state === 'SUCCESS' || response.data.state === 'FAILURE') {
            clearInterval(interval);
            setCurrentTaskId(null);
            
            if (response.data.state === 'SUCCESS') {
              toast.success('Mise à jour des données terminée avec succès !');
            } else {
              toast.error(`Erreur lors de la mise à jour: ${response.data.error}`);
            }
            
            // Rafraîchir les données
            queryClient.invalidateQueries('dataUpdateStatus');
            queryClient.invalidateQueries('dataStats');
            queryClient.invalidateQueries('latestOpportunities');
          }
        }
      } catch (error) {
        console.error('Erreur lors du suivi de la tâche:', error);
      }
    }, 2000); // Polling toutes les 2 secondes

    return () => clearInterval(interval);
  }, [currentTaskId, queryClient]);

  const handleUpdateData = () => {
    updateDataMutation.mutate();
  };

  const refreshOpportunitiesMutation = useMutation(
    async () => {
      const response = await apiService.runLatestScreener();
      return response;
    },
    {
      onSuccess: () => {
        toast.success('Recherche d\'opportunités lancée');
        queryClient.invalidateQueries(['latest-opportunities']);
      },
      onError: (error: any) => {
        toast.error(`Erreur lors de la recherche: ${error.message}`);
      }
    }
  );

  const handleRefreshOpportunities = () => {
    refreshOpportunitiesMutation.mutate();
  };

  const getStatusIcon = () => {
    if (taskStatus) {
      switch (taskStatus.state) {
        case 'SUCCESS':
          return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
        case 'FAILURE':
          return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
        case 'PROGRESS':
          return <ClockIcon className="h-5 w-5 text-blue-500 animate-spin" />;
        default:
          return <ClockIcon className="h-5 w-5 text-gray-400" />;
      }
    }
    return null;
  };

  const getStatusMessage = () => {
    if (taskStatus) {
      return taskStatus.status;
    }
    if (dataStatus?.data?.overall_status === 'needs_update') {
      return 'Mise à jour nécessaire';
    }
    return 'Données à jour';
  };

  const getProgressBar = () => {
    if (taskStatus && taskStatus.progress !== undefined) {
      return (
        <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
            style={{ width: `${taskStatus.progress}%` }}
          ></div>
        </div>
      );
    }
    return null;
  };

  const getCurrentSymbolInfo = () => {
    if (taskStatus && taskStatus.current_symbol && taskStatus.total_symbols) {
      return (
        <div className="text-xs text-gray-500 mt-1">
          {taskStatus.current_symbol} ({taskStatus.current_symbol}/{taskStatus.total_symbols})
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <CloudArrowUpIcon className="h-5 w-5 mr-2 text-blue-600" />
        Contrôles de Données
      </h3>
      
      <div className="space-y-4">
        {/* Statut actuel */}
        <div className="p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              {getStatusIcon()}
              <span className="ml-2 text-sm font-medium text-gray-900">
                {getStatusMessage()}
              </span>
            </div>
            {dataStatus?.data?.overall_status === 'needs_update' && (
              <span className="text-xs text-orange-600 font-medium">
                Mise à jour recommandée
              </span>
            )}
          </div>
          
          {getProgressBar()}
          {getCurrentSymbolInfo()}
        </div>

        {/* Mise à jour des données historiques */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center">
            <ChartBarIcon className="h-5 w-5 text-gray-400 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-900">Données historiques</p>
              <p className="text-xs text-gray-500">Mise à jour des prix et indicateurs</p>
            </div>
          </div>
          <button
            onClick={handleUpdateData}
            disabled={updateDataMutation.isLoading || currentTaskId !== null}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {updateDataMutation.isLoading || currentTaskId ? (
              <>
                <ClockIcon className="h-4 w-4 mr-2 animate-spin" />
                Mise à jour...
              </>
            ) : (
              <>
                <ArrowPathIcon className="h-4 w-4 mr-2" />
                Mettre à jour
              </>
            )}
          </button>
        </div>

        {/* Recherche d'opportunités */}
        <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center">
            <ClockIcon className="h-5 w-5 text-gray-400 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-900">Opportunités de trading</p>
              <p className="text-xs text-gray-500">Recherche automatique de signaux</p>
            </div>
          </div>
          <button
            onClick={handleRefreshOpportunities}
            disabled={refreshOpportunitiesMutation.isLoading}
            className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {refreshOpportunitiesMutation.isLoading ? (
              <>
                <ArrowPathIcon className="h-4 w-4 mr-2 animate-spin" />
                Recherche...
              </>
            ) : (
              <>
                <ArrowPathIcon className="h-4 w-4 mr-2" />
                Rechercher
              </>
            )}
          </button>
        </div>

        {/* Informations de fraîcheur */}
        {dataStatus?.data && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center mb-2">
              <CheckCircleIcon className="h-4 w-4 text-blue-600 mr-2" />
              <p className="text-sm text-blue-800 font-medium">État des données</p>
            </div>
            <div className="text-xs text-blue-700 space-y-1">
              <div className="flex justify-between">
                <span>Données historiques:</span>
                <span>
                  {dataStatus.data.historical_freshness?.hours_since_update 
                    ? `${Math.round(dataStatus.data.historical_freshness.hours_since_update)}h`
                    : 'N/A'
                  }
                </span>
              </div>
              <div className="flex justify-between">
                <span>Données de sentiment:</span>
                <span>
                  {dataStatus.data.sentiment_freshness?.hours_since_update 
                    ? `${Math.round(dataStatus.data.sentiment_freshness.hours_since_update)}h`
                    : 'N/A'
                  }
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}