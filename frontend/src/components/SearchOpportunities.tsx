'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { apiService } from '@/services/api';
import { 
  ChartBarIcon, 
  ClockIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  EyeIcon,
  ShoppingCartIcon
} from '@heroicons/react/24/outline';
import LoadingSpinner from './LoadingSpinner';
import ErrorMessage from './ErrorMessage';
import { toast } from 'react-hot-toast';

interface SearchOpportunitiesProps {
  searchId: string;
  onAddToCart?: (opportunity: any) => void;
}

interface Opportunity {
  id: number;
  symbol: string;
  model_id: number;
  model_name: string;
  prediction: number;
  confidence: number;
  rank: number;
  target_return: number;
  time_horizon: number;
  prediction_date: string;
  screener_run_id: number;
}

interface SearchData {
  search_id: string;
  status: string;
  total_opportunities: number;
  opportunities: Opportunity[];
  search_parameters: {
    target_return_percentage: number;
    time_horizon_days: number;
    risk_tolerance: number;
    confidence_threshold: number;
  };
  created_at: string;
  completed_at?: string;
}

export default function SearchOpportunities({ searchId, onAddToCart }: SearchOpportunitiesProps) {
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);

  const { data: searchData, isLoading, error, refetch } = useQuery<SearchData>(
    ['search-opportunities', searchId],
    () => apiService.getSearchOpportunities(searchId),
    {
      enabled: !!searchId,
      refetchInterval: 5000, // Refetch toutes les 5 secondes
      refetchIntervalInBackground: false,
    }
  );

  const formatModelName = (modelName: string) => {
    if (modelName.includes('xgboost')) return 'XGBoost';
    if (modelName.includes('lightgbm')) return 'LightGBM';
    if (modelName.includes('randomforest')) return 'RandomForest';
    if (modelName.includes('neural')) return 'Neural Network';
    return 'ML Model';
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'running':
        return <ClockIcon className="h-5 w-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Terminée';
      case 'running':
        return 'En cours';
      case 'failed':
        return 'Échouée';
      case 'pending':
        return 'En attente';
      default:
        return status;
    }
  };

  const handleAddToCart = (opportunity: Opportunity) => {
    if (onAddToCart) {
      onAddToCart(opportunity);
      toast.success(`${opportunity.symbol} ajouté au panier`);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center">
          <LoadingSpinner />
          <span className="ml-2 text-gray-600">Chargement des opportunités...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <ErrorMessage message="Erreur lors du chargement des opportunités" />
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Réessayer
        </button>
      </div>
    );
  }

  if (!searchData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-gray-500">
          Aucune donnée de recherche disponible
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* Header avec informations de la recherche */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getStatusIcon(searchData.status)}
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                Résultats de la recherche
              </h3>
              <p className="text-sm text-gray-500">
                Statut: {getStatusText(searchData.status)} • 
                {searchData.total_opportunities} opportunités trouvées
              </p>
            </div>
          </div>
          <div className="text-right text-sm text-gray-500">
            <p>Créée: {new Date(searchData.created_at).toLocaleString('fr-FR')}</p>
            {searchData.completed_at && (
              <p>Terminée: {new Date(searchData.completed_at).toLocaleString('fr-FR')}</p>
            )}
          </div>
        </div>

        {/* Paramètres de recherche */}
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="font-medium text-gray-700">Rendement cible:</span>
            <p className="text-gray-900">{searchData.search_parameters.target_return_percentage}%</p>
          </div>
          <div>
            <span className="font-medium text-gray-700">Horizon:</span>
            <p className="text-gray-900">{searchData.search_parameters.time_horizon_days} jours</p>
          </div>
          <div>
            <span className="font-medium text-gray-700">Risque:</span>
            <p className="text-gray-900">{(searchData.search_parameters.risk_tolerance * 100).toFixed(0)}%</p>
          </div>
          <div>
            <span className="font-medium text-gray-700">Confiance min:</span>
            <p className="text-gray-900">{(searchData.search_parameters.confidence_threshold * 100).toFixed(0)}%</p>
          </div>
        </div>
      </div>

      {/* Liste des opportunités */}
      <div className="p-6">
        {searchData.opportunities.length === 0 ? (
          <div className="text-center py-8">
            <ChartBarIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">
              {searchData.status === 'completed' 
                ? 'Aucune opportunité trouvée avec ces paramètres'
                : 'Recherche en cours...'
              }
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {searchData.opportunities.map((opportunity) => (
              <div
                key={opportunity.id}
                className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold">
                      {opportunity.symbol.substring(0, 4)}
                    </div>
                    <div>
                      <h4 className="font-semibold text-gray-900">{opportunity.symbol}</h4>
                      <p className="text-sm text-gray-500">
                        {formatModelName(opportunity.model_name)} • Rang #{opportunity.rank}
                      </p>
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-6">
                    <div className="text-center">
                      <div className="text-lg font-bold text-green-600">
                        {(opportunity.confidence * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500">Confiance</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-lg font-bold text-blue-600">
                        {opportunity.target_return}%
                      </div>
                      <div className="text-xs text-gray-500">Rendement</div>
                    </div>
                    
                    <div className="text-center">
                      <div className="text-lg font-bold text-purple-600">
                        {opportunity.time_horizon}j
                      </div>
                      <div className="text-xs text-gray-500">Horizon</div>
                    </div>
                    
                    <div className="flex space-x-2">
                      <button
                        onClick={() => setSelectedOpportunity(opportunity)}
                        className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                        title="Analyser"
                      >
                        <EyeIcon className="h-5 w-5" />
                      </button>
                      
                      {onAddToCart && (
                        <button
                          onClick={() => handleAddToCart(opportunity)}
                          className="p-2 text-gray-400 hover:text-green-600 transition-colors"
                          title="Ajouter au panier"
                        >
                          <ShoppingCartIcon className="h-5 w-5" />
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
