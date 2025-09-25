'use client';

import React from 'react';
import { useQuery } from 'react-query';
import { 
  ChartBarIcon, 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon,
  ClockIcon,
  StarIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import { screenerApi } from '@/services/api';
import Link from 'next/link';

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
  prediction_date: string;
}

interface LatestOpportunitiesProps {
  className?: string;
  maxItems?: number;
}

export default function LatestOpportunities({ className = '', maxItems = 6 }: LatestOpportunitiesProps) {
  const { data: opportunities, isLoading, error } = useQuery(
    'latest-opportunities',
    () => screenerApi.getLatestOpportunities(),
    { 
      staleTime: 2 * 60 * 1000, // 2 minutes
      refetchInterval: 5 * 60 * 1000 // Refetch every 5 minutes
    }
  );

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-blue-600 bg-blue-100';
    if (confidence >= 0.4) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getPredictionIcon = (prediction: number) => {
    return prediction > 0 ? (
      <ArrowTrendingUpIcon className="h-4 w-4 text-green-600" />
    ) : (
      <ArrowTrendingDownIcon className="h-4 w-4 text-red-600" />
    );
  };

  const getPredictionColor = (prediction: number) => {
    return prediction > 0 ? 'text-green-600' : 'text-red-600';
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
      </div>
    );
  }

  if (error || !opportunities || opportunities.length === 0) {
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
        <Link
          href="/screeners"
          className="text-sm text-blue-600 hover:text-blue-800 flex items-center"
        >
          <EyeIcon className="h-4 w-4 mr-1" />
          Voir tout
        </Link>
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
                <span className={`font-medium ${getPredictionColor(opportunity.prediction)}`}>
                  {opportunity.prediction > 0 ? '+' : ''}{(opportunity.prediction * 100).toFixed(1)}%
                </span>
                <span>{opportunity.target_return}% en {opportunity.time_horizon}j</span>
                <span className="text-gray-400">•</span>
                <span>{opportunity.model_name}</span>
              </div>
              <div className="flex items-center">
                <ClockIcon className="h-3 w-3 mr-1" />
                <span>{new Date(opportunity.prediction_date).toLocaleDateString()}</span>
              </div>
            </div>
            
            <div className="flex items-center justify-between">
              <div className="text-xs text-gray-400">
                Modèle #{opportunity.model_id}
              </div>
              <button className="text-xs bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 transition-colors">
                Analyser
              </button>
            </div>
          </div>
        ))}
      </div>
      
      {opportunities.length > maxItems && (
        <div className="mt-4 text-center">
          <Link
            href="/screeners"
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Voir {opportunities.length - maxItems} autres opportunités →
          </Link>
        </div>
      )}
    </div>
  );
}
