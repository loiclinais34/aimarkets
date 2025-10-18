import React, { useState, useEffect } from 'react';
import {
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartBarIcon,
  CheckCircleIcon,
  ClockIcon,
  ScaleIcon,
  TrophyIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';
import { performanceApi } from '@/services/performanceApi';

interface RecommendationMetrics {
  total_opportunities: number;
  successful_predictions: number;
  success_rate: number;
  mean_return: number;
  median_return: number;
  std_return: number;
  mean_confidence: number;
  risk_adjusted_return: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  gross_profit: number;
  gross_loss: number;
}

interface PerformanceStats {
  total_opportunities: number;
  analyzed_opportunities: number;
  overall_success_rate: number;
  recommendation_performance: {
    [key: string]: RecommendationMetrics;
  };
}

export default function OpportunityPerformanceKPIs() {
  const [stats, setStats] = useState<PerformanceStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setIsLoading(true);
        const data = await performanceApi.getOpportunityPerformanceStats();
        setStats(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erreur inconnue');
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (isLoading) {
    return (
      <div className="p-6 bg-white rounded-lg shadow animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-24 bg-gray-100 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-white rounded-lg shadow">
        <div className="text-red-600 text-center">
          <p className="font-semibold">Erreur de chargement</p>
          <p className="text-sm mt-1">{error}</p>
        </div>
      </div>
    );
  }

  if (!stats) return null;

  // Fonction pour obtenir la couleur selon la performance
  const getPerformanceColor = (successRate: number, meanReturn: number) => {
    if (successRate >= 0.5 && meanReturn > 0) return "text-green-600";
    if (successRate >= 0.3 && meanReturn > 0) return "text-yellow-600";
    return "text-red-600";
  };

  // Fonction pour obtenir l'icône selon le type de recommandation
  const getRecommendationIcon = (recommendation: string) => {
    if (recommendation.includes('BUY')) return ArrowTrendingUpIcon;
    if (recommendation.includes('SELL')) return ArrowTrendingDownIcon;
    return CheckCircleIcon;
  };

  // Fonction pour obtenir le badge de performance
  const getPerformanceBadge = (successRate: number, meanReturn: number) => {
    if (successRate >= 0.5 && meanReturn > 0) {
      return { text: "Excellent", color: "bg-green-100 text-green-800" };
    }
    if (successRate >= 0.3 && meanReturn > 0) {
      return { text: "Bon", color: "bg-yellow-100 text-yellow-800" };
    }
    if (successRate >= 0.2) {
      return { text: "Moyen", color: "bg-orange-100 text-orange-800" };
    }
    return { text: "Faible", color: "bg-red-100 text-red-800" };
  };

  return (
    <div className="space-y-6">
      {/* KPIs Généraux */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-gray-500">Total Opportunités</h3>
              <div className="mt-2 flex items-baseline">
                <p className="text-2xl font-semibold text-blue-600">
                  {stats.total_opportunities.toLocaleString()}
                </p>
              </div>
              <p className="mt-1 text-xs text-gray-500">Opportunités analysées: {stats.analyzed_opportunities}</p>
            </div>
            <div className="p-3 rounded-md text-blue-600 bg-blue-50">
              <ChartBarIcon className="h-6 w-6" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-gray-500">Taux de Réussite Global</h3>
              <div className="mt-2 flex items-baseline">
                <p className={`text-2xl font-semibold ${stats.overall_success_rate >= 0.5 ? 'text-green-600' : 'text-red-600'}`}>
                  {(stats.overall_success_rate * 100).toFixed(1)}%
                </p>
              </div>
              <p className="mt-1 text-xs text-gray-500">Performance globale</p>
            </div>
            <div className={`p-3 rounded-md ${stats.overall_success_rate >= 0.5 ? 'text-green-600 bg-green-50' : 'text-red-600 bg-red-50'}`}>
              <CheckCircleIcon className="h-6 w-6" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h3 className="text-sm font-medium text-gray-500">Types de Recommandations</h3>
              <div className="mt-2 flex items-baseline">
                <p className="text-2xl font-semibold text-purple-600">
                  {Object.keys(stats.recommendation_performance).length}
                </p>
              </div>
              <p className="mt-1 text-xs text-gray-500">Catégories analysées</p>
            </div>
            <div className="p-3 rounded-md text-purple-600 bg-purple-50">
              <TrophyIcon className="h-6 w-6" />
            </div>
          </div>
        </div>
      </div>

      {/* Métriques par Type de Recommandation */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Performance par Type de Recommandation</h3>
          <p className="text-sm text-gray-500 mt-1">Analyse détaillée de chaque stratégie d'investissement</p>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            {Object.entries(stats.recommendation_performance).map(([recommendation, metrics]) => {
              const Icon = getRecommendationIcon(recommendation);
              const color = getPerformanceColor(metrics.success_rate, metrics.mean_return);
              const badge = getPerformanceBadge(metrics.success_rate, metrics.mean_return);
              
              return (
                <div key={recommendation} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2">
                      <div className={`p-2 rounded-md ${color} bg-opacity-10`}>
                        <Icon className={`h-5 w-5 ${color}`} />
                      </div>
                      <h4 className="font-medium text-gray-900">{recommendation}</h4>
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${badge.color}`}>
                      {badge.text}
                    </span>
                  </div>

                  <div className="space-y-3">
                    {/* Métriques principales */}
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-xs text-gray-500">Taux de Réussite</p>
                        <p className={`text-lg font-semibold ${color}`}>
                          {(metrics.success_rate * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500">Retour Moyen</p>
                        <p className={`text-lg font-semibold ${metrics.mean_return > 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {(metrics.mean_return * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>

                    {/* Métriques secondaires */}
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Opportunités:</span>
                        <span className="font-medium">{metrics.total_opportunities}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Confiance Moy.:</span>
                        <span className="font-medium">{(metrics.mean_confidence * 100).toFixed(0)}%</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Ratio Risque/Rend.:</span>
                        <span className="font-medium">{metrics.risk_adjusted_return.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Profit Factor:</span>
                        <span className="font-medium">{metrics.profit_factor.toFixed(2)}</span>
                      </div>
                    </div>

                    {/* Barre de progression pour le taux de réussite */}
                    <div className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-gray-500">Performance</span>
                        <span className="text-gray-500">{(metrics.success_rate * 100).toFixed(1)}%</span>
                      </div>
                      <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className={`absolute left-0 top-0 h-full rounded-full ${
                            metrics.success_rate >= 0.5 ? 'bg-green-500' : 
                            metrics.success_rate >= 0.3 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${metrics.success_rate * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}