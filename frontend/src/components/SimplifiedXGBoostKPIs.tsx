'use client';

import React, { useEffect, useState } from 'react';
import { xgboostPerformanceApi, XGBoostPerformanceSummary } from '@/services/xgboostPerformanceApi';
import { formatPercentage } from '@/utils/formatters';

interface SimplifiedKPICardProps {
  title: string;
  value: string | number;
  trend?: 'up' | 'down' | 'neutral';
  description?: string;
  color?: 'green' | 'red' | 'blue' | 'yellow' | 'gray';
}

const SimplifiedKPICard: React.FC<SimplifiedKPICardProps> = ({ title, value, trend, description, color = 'gray' }) => {
  const colorClasses = {
    green: 'text-green-600 bg-green-50 border-green-200',
    red: 'text-red-600 bg-red-50 border-red-200',
    blue: 'text-blue-600 bg-blue-50 border-blue-200',
    yellow: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    gray: 'text-gray-600 bg-gray-50 border-gray-200'
  };

  const trendIcons = {
    up: '↗',
    down: '↘',
    neutral: '→'
  };

  return (
    <div className={`bg-white overflow-hidden shadow rounded-lg border ${colorClasses[color]}`}>
      <div className="p-5">
        <dl>
          <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
          <dd className="mt-1 text-2xl font-semibold">
            {value}
            {trend && (
              <span className="ml-2 text-lg" title={`Tendance: ${trend}`}>
                {trendIcons[trend]}
              </span>
            )}
          </dd>
          {description && (
            <dd className="mt-2 text-sm text-gray-500">{description}</dd>
          )}
        </dl>
      </div>
    </div>
  );
};

const SimplifiedXGBoostKPIs: React.FC = () => {
  const [performanceData, setPerformanceData] = useState<XGBoostPerformanceSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPerformance = async () => {
      try {
        setIsLoading(true);
        const data = await xgboostPerformanceApi.getPerformanceSummary();
        setPerformanceData(data);
      } catch (err) {
        console.error('Error fetching XGBoost performance:', err);
        setError('Failed to load XGBoost performance data.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchPerformance();
  }, []);

  if (isLoading) {
    return (
      <div className="bg-white shadow rounded-lg p-6 text-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
        <p className="text-gray-500">Chargement des performances...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
        <strong className="font-bold">Erreur:</strong>
        <span className="block sm:inline"> {error}</span>
      </div>
    );
  }

  if (!performanceData || !performanceData.summary) {
    return (
      <div className="bg-white shadow rounded-lg p-6 text-center">
        <p className="text-gray-500">Aucune donnée de performance disponible.</p>
      </div>
    );
  }

  const { summary, recommendation_performance } = performanceData;

  // Calculer les signaux actifs (non-HOLD)
  const activeSignals = Object.entries(recommendation_performance)
    .filter(([type]) => type !== 'HOLD')
    .reduce((sum, [, metrics]) => sum + metrics.count, 0);

  // Calculer le pourcentage de signaux actifs
  const activeSignalsPercent = summary.total_opportunities > 0 
    ? (activeSignals / summary.total_opportunities) * 100 
    : 0;

  return (
    <div className="space-y-6">
      {/* En-tête simplifié */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg p-4">
        <h2 className="text-xl font-bold mb-1">🚀 Performance XGBoost</h2>
        <p className="text-blue-100 text-sm">
          Modèles ML optimisés avec {summary.total_opportunities.toLocaleString()} opportunités analysées
        </p>
      </div>

      {/* KPIs principaux seulement */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <SimplifiedKPICard
          title="Confiance Moyenne"
          value={formatPercentage(summary.avg_confidence)}
          trend={summary.avg_confidence > 0.7 ? 'up' : 'neutral'}
          description="Niveau de confiance moyen"
          color="green"
        />
        <SimplifiedKPICard
          title="Retour Potentiel"
          value={formatPercentage(summary.avg_potential_return)}
          trend={summary.avg_potential_return > 0 ? 'up' : 'down'}
          description="Retour moyen prédit"
          color="blue"
        />
        <SimplifiedKPICard
          title="Signaux Actifs"
          value={`${activeSignals.toLocaleString()}`}
          trend={activeSignalsPercent > 0.1 ? 'up' : 'neutral'}
          description={`${activeSignalsPercent.toFixed(2)}% du total`}
          color="yellow"
        />
        <SimplifiedKPICard
          title="Symboles Couverts"
          value={summary.unique_symbols}
          description="Symboles analysés"
          color="gray"
        />
      </div>

      {/* Lien vers l'analyse détaillée */}
      <div className="bg-white shadow rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Analyse Détaillée</h3>
            <p className="text-sm text-gray-500">
              Consultez l'analyse complète des performances par recommandation, horizon et symboles
            </p>
          </div>
          <a 
            href="/performance-analysis"
            className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Voir l'Analyse
          </a>
        </div>
      </div>
    </div>
  );
};

export default SimplifiedXGBoostKPIs;
