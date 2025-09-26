'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { StarIcon, ChartBarIcon, ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/outline';

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

interface LatestOpportunitiesProps {
  className?: string;
  maxItems?: number;
}

export default function LatestOpportunities({ className = '', maxItems = 6 }: LatestOpportunitiesProps) {
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

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

  useEffect(() => {
    fetchOpportunities();
    
    // Mise à jour automatique toutes les 5 minutes
    const interval = setInterval(fetchOpportunities, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, [fetchOpportunities]);

  const formatModelName = (modelName: string) => {
    // Extraire le type de modèle (RandomForest, XGBoost, LightGBM)
    if (modelName.includes('xgboost')) return 'XGBoost';
    if (modelName.includes('lightgbm')) return 'LightGBM';
    if (modelName.includes('randomforest')) return 'RandomForest';
    return 'ML Model';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getPredictionIcon = (prediction: number) => {
    return prediction > 0 ? (
      <ArrowUpIcon className="h-4 w-4 text-green-600" />
    ) : (
      <ArrowDownIcon className="h-4 w-4 text-red-600" />
    );
  };

  if (isLoading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <StarIcon className="h-5 w-5 mr-2 text-yellow-600" />
          Dernières Opportunités
        </h3>
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-16 bg-gray-200 rounded-lg"></div>
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
          Dernières Opportunités
        </h3>
        <div className="text-center py-8">
          <ChartBarIcon className="h-12 w-12 text-red-300 mx-auto mb-4" />
          <p className="text-red-600 font-medium">Erreur de chargement</p>
          <p className="text-sm text-gray-500 mt-1">{error}</p>
          <button
            onClick={fetchOpportunities}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
          >
            Réessayer
          </button>
        </div>
      </div>
    );
  }

  if (!opportunities || opportunities.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <StarIcon className="h-5 w-5 mr-2 text-yellow-600" />
          Dernières Opportunités
        </h3>
        <div className="text-center py-8">
          <ChartBarIcon className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <p className="text-gray-500">Aucune opportunité récente</p>
          <p className="text-sm text-gray-400 mt-1">
            Lancez une recherche pour découvrir de nouvelles opportunités
          </p>
        </div>
      </div>
    );
  }

  const displayOpportunities = opportunities.slice(0, maxItems);

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 flex items-center">
          <StarIcon className="h-5 w-5 mr-2 text-yellow-600" />
          Dernières Opportunités
        </h3>
        {lastUpdated && (
          <span className="text-xs text-gray-500">
            Mis à jour: {lastUpdated.toLocaleTimeString()}
          </span>
        )}
      </div>
      
      <div className="space-y-3">
        {displayOpportunities.map((opportunity: Opportunity, index: number) => (
          <div
            key={`${opportunity.symbol}-${opportunity.model_id}-${index}`}
            className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                <span className="text-lg font-bold text-gray-900">{opportunity.symbol}</span>
                <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  #{opportunity.rank}
                </span>
                {getPredictionIcon(opportunity.prediction)}
              </div>
              <span className={`text-sm font-medium px-2 py-1 rounded ${getConfidenceColor(opportunity.confidence)}`}>
                {(opportunity.confidence * 100).toFixed(1)}%
              </span>
            </div>
            
            <p className="text-sm text-gray-600 mb-2">{opportunity.company_name}</p>
            
            <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
              <div className="flex items-center space-x-4">
                <span className={`font-medium ${opportunity.prediction > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {opportunity.prediction > 0 ? '+' : ''}{(opportunity.prediction * 100).toFixed(1)}%
                </span>
                <span>{opportunity.target_return}% en {opportunity.time_horizon}j</span>
                <span className="text-gray-400">•</span>
                <span className="bg-gray-100 px-2 py-1 rounded text-xs">
                  {formatModelName(opportunity.model_name)}
                </span>
              </div>
              <div>
                <span>{opportunity.prediction_date ? new Date(opportunity.prediction_date).toLocaleDateString() : 'Récent'}</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {opportunities.length > maxItems && (
        <div className="mt-4 text-center">
          <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
            Voir toutes les opportunités ({opportunities.length})
          </button>
        </div>
      )}
    </div>
  );
}