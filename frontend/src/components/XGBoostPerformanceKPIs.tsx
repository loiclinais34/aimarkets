'use client';

import React, { useEffect, useState } from 'react';
import { xgboostPerformanceApi, XGBoostPerformanceSummary } from '@/services/xgboostPerformanceApi';
import { formatCurrency, formatPercentage } from '@/utils/formatters';

interface KPICardProps {
  title: string;
  value: string | number;
  trend?: 'up' | 'down' | 'neutral';
  description?: string;
  color?: 'green' | 'red' | 'blue' | 'yellow' | 'gray';
}

const KPICard: React.FC<KPICardProps> = ({ title, value, trend, description, color = 'gray' }) => {
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
          <dd className="mt-1 text-3xl font-semibold">
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

const XGBoostPerformanceKPIs: React.FC = () => {
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
        <p className="text-gray-500">Chargement des performances XGBoost...</p>
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
        <p className="text-gray-500">Aucune donnée de performance XGBoost disponible.</p>
      </div>
    );
  }

  const { summary, recommendation_performance, horizon_performance, top_symbols, confidence_distribution } = performanceData;

  return (
    <div className="space-y-6">
      {/* En-tête avec informations générales */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg p-6">
        <h2 className="text-2xl font-bold mb-2">🚀 Performance XGBoost</h2>
        <p className="text-blue-100">
          Modèles ML sophistiqués avec indicateurs TA-Lib avancés
        </p>
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-blue-200">Total Opportunités:</span>
            <div className="font-bold text-lg">{summary.total_opportunities.toLocaleString()}</div>
          </div>
          <div>
            <span className="text-blue-200">Symboles:</span>
            <div className="font-bold text-lg">{summary.unique_symbols}</div>
          </div>
          <div>
            <span className="text-blue-200">Horizons:</span>
            <div className="font-bold text-lg">{summary.horizons_count}</div>
          </div>
          <div>
            <span className="text-blue-200">Confiance Moyenne:</span>
            <div className="font-bold text-lg">{formatPercentage(summary.avg_confidence)}</div>
          </div>
        </div>
      </div>

      {/* KPIs principaux */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          title="Confiance Moyenne"
          value={formatPercentage(summary.avg_confidence)}
          trend={summary.avg_confidence > 0.7 ? 'up' : 'neutral'}
          description="Niveau de confiance moyen des prédictions"
          color="green"
        />
        <KPICard
          title="Retour Potentiel Moyen"
          value={formatPercentage(summary.avg_potential_return)}
          trend={summary.avg_potential_return > 0 ? 'up' : 'down'}
          description="Retour moyen prédit par les modèles"
          color="blue"
        />
        <KPICard
          title="Score de Risque Moyen"
          value={formatPercentage(summary.avg_risk_score)}
          trend={summary.avg_risk_score < 0.3 ? 'up' : 'down'}
          description="Risque moyen calculé (plus bas = mieux)"
          color="yellow"
        />
        <KPICard
          title="Période Couverte"
          value={`${summary.date_range.earliest?.split('T')[0]} → ${summary.date_range.latest?.split('T')[0]}`}
          description="Plage de dates des opportunités"
          color="gray"
        />
      </div>

      {/* Performance par Recommandation */}
      {Object.keys(recommendation_performance).length > 0 && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              📊 Performance par Type de Recommandation
            </h3>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(recommendation_performance).map(([type, metrics]) => {
                const getColor = (type: string) => {
                  if (type.includes('BUY_STRONG')) return 'green';
                  if (type.includes('BUY')) return 'blue';
                  if (type.includes('HOLD')) return 'yellow';
                  if (type.includes('SELL')) return 'red';
                  return 'gray';
                };

                return (
                  <KPICard
                    key={type}
                    title={type.replace('_', ' ')}
                    value={formatPercentage(metrics.avg_confidence)}
                    trend={metrics.avg_potential_return > 0 ? 'up' : 'down'}
                    description={`${metrics.count} opportunités | Retour: ${formatPercentage(metrics.avg_potential_return)}`}
                    color={getColor(type)}
                  />
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Performance par Horizon */}
      {Object.keys(horizon_performance).length > 0 && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              ⏰ Performance par Horizon
            </h3>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
              {Object.entries(horizon_performance).map(([horizon, metrics]) => (
                <KPICard
                  key={horizon}
                  title={`${horizon} Jours`}
                  value={formatPercentage(metrics.avg_confidence)}
                  trend={metrics.avg_potential_return > 0 ? 'up' : 'down'}
                  description={`${metrics.count} opportunités | Retour: ${formatPercentage(metrics.avg_potential_return)}`}
                  color="blue"
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Top Symboles */}
      {Object.keys(top_symbols).length > 0 && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              ⭐ Top 10 Symboles par Confiance
            </h3>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
              {Object.entries(top_symbols).slice(0, 10).map(([symbol, metrics]) => (
                <KPICard
                  key={symbol}
                  title={symbol}
                  value={formatPercentage(metrics.avg_confidence)}
                  trend={metrics.avg_potential_return > 0 ? 'up' : 'down'}
                  description={`${metrics.count} opp. | Max: ${formatPercentage(metrics.max_confidence)}`}
                  color="green"
                />
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Distribution des Confiances */}
      {Object.keys(confidence_distribution).length > 0 && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              📈 Distribution des Niveaux de Confiance
            </h3>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(confidence_distribution).map(([range, metrics]) => {
                const getColor = (range: string) => {
                  if (range.includes('Très Haute')) return 'green';
                  if (range.includes('Haute')) return 'blue';
                  if (range.includes('Moyenne-Haute')) return 'yellow';
                  if (range.includes('Moyenne')) return 'gray';
                  return 'red';
                };

                return (
                  <KPICard
                    key={range}
                    title={range}
                    value={metrics.count.toLocaleString()}
                    trend={metrics.avg_potential_return > 0 ? 'up' : 'down'}
                    description={`Confiance: ${formatPercentage(metrics.avg_confidence)} | Retour: ${formatPercentage(metrics.avg_potential_return)}`}
                    color={getColor(range)}
                  />
                );
              })}
            </div>
          </div>
        </div>
      )}

      {/* Informations supplémentaires */}
      <div className="mt-6 p-4 bg-gradient-to-r from-gray-50 to-blue-50 rounded-lg">
        <div className="text-sm text-gray-600">
          <p className="font-medium mb-2">🔬 Informations sur les Modèles XGBoost:</p>
          <ul className="space-y-1 text-xs">
            <li>• Modèles sophistiqués avec 135 features (116 TA-Lib + 22 avancées)</li>
            <li>• Classification + Régression avec XGBoost</li>
            <li>• Entraînement sur {summary.total_opportunities.toLocaleString()} opportunités historiques</li>
            <li>• Seuil de confiance minimum: 60%</li>
            <li>• Confiance maximale observée: {Math.max(...Object.values(recommendation_performance).map(m => m.max_confidence)).toFixed(1)}%</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default XGBoostPerformanceKPIs;
