import React, { useState, useEffect } from 'react';
import { mlPerformanceApi, MLPerformanceSummary } from '../services/mlPerformanceApi';

interface MLPerformanceKPIsProps {
  className?: string;
}

const MLPerformanceKPIs: React.FC<MLPerformanceKPIsProps> = ({ className = '' }) => {
  const [mlData, setMlData] = useState<MLPerformanceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchMLPerformance = async () => {
      try {
        setLoading(true);
        const data = await mlPerformanceApi.getMLPerformanceSummary(1000);
        setMlData(data);
        setError(null);
      } catch (err) {
        console.error('Error fetching ML performance data:', err);
        setError('Erreur lors du chargement des données ML');
      } finally {
        setLoading(false);
      }
    };

    fetchMLPerformance();
  }, []);

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !mlData) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          📊 Performance ML
        </h3>
        <div className="text-center text-gray-500">
          <p>{error || 'Aucune donnée disponible'}</p>
          <p className="text-sm mt-2">
            Les opportunités ML nécessitent des données historiques suffisantes pour l'analyse.
          </p>
        </div>
      </div>
    );
  }

  const { summary, recommendation_performance, horizon_performance } = mlData;

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;
  const formatNumber = (value: number, decimals: number = 3) => value.toFixed(decimals);
  const formatCurrency = (value: number) => `${(value * 100).toFixed(2)}%`;

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'BUY_STRONG':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'BUY_MODERATE':
        return 'text-green-500 bg-green-50 border-green-200';
      case 'BUY_WEAK':
        return 'text-green-400 bg-green-50 border-green-200';
      case 'SELL_STRONG':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'SELL_MODERATE':
        return 'text-red-500 bg-red-50 border-red-200';
      case 'SELL_WEAK':
        return 'text-red-400 bg-red-50 border-red-200';
      case 'HOLD':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getHorizonColor = (horizon: string) => {
    switch (horizon) {
      case '1':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      case '7':
        return 'text-purple-600 bg-purple-50 border-purple-200';
      case '30':
        return 'text-indigo-600 bg-indigo-50 border-indigo-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-6">
        🤖 Performance des Opportunités ML
      </h3>

      {/* KPIs Globaux */}
      <div className="mb-8">
        <h4 className="text-md font-medium text-gray-700 mb-4">📈 Performance Globale</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-sm font-medium text-blue-600">Taux de Succès</div>
            <div className="text-2xl font-bold text-blue-900">
              {formatPercentage(summary.success_rate)}
            </div>
            <div className="text-xs text-blue-600">
              {summary.total_opportunities.toLocaleString()} opportunités
            </div>
          </div>
          
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="text-sm font-medium text-green-600">Retour Moyen</div>
            <div className="text-2xl font-bold text-green-900">
              {formatCurrency(summary.mean_return)}
            </div>
            <div className="text-xs text-green-600">
              Volatilité: {formatCurrency(summary.volatility)}
            </div>
          </div>
          
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <div className="text-sm font-medium text-purple-600">Ratio de Sharpe</div>
            <div className="text-2xl font-bold text-purple-900">
              {formatNumber(summary.sharpe_ratio)}
            </div>
            <div className="text-xs text-purple-600">
              Taux de gain: {formatPercentage(summary.win_rate)}
            </div>
          </div>
          
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="text-sm font-medium text-orange-600">Ratio de Profit</div>
            <div className="text-2xl font-bold text-orange-900">
              {formatNumber(summary.profit_factor)}
            </div>
            <div className="text-xs text-orange-600">
              Max Drawdown: {formatCurrency(summary.max_drawdown)}
            </div>
          </div>
        </div>
      </div>

      {/* Performance par Recommandation */}
      <div className="mb-8">
        <h4 className="text-md font-medium text-gray-700 mb-4">📊 Performance par Type de Recommandation</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(recommendation_performance).map(([recommendation, metrics]) => (
            <div key={recommendation} className={`border rounded-lg p-4 ${getRecommendationColor(recommendation)}`}>
              <div className="font-semibold text-sm mb-2">{recommendation}</div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span>Succès:</span>
                  <span className="font-medium">{formatPercentage(metrics.success_rate)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Retour:</span>
                  <span className="font-medium">{formatCurrency(metrics.mean_return)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Confiance:</span>
                  <span className="font-medium">{formatNumber(metrics.avg_confidence)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Précision:</span>
                  <span className="font-medium">{formatNumber(metrics.prediction_accuracy)}</span>
                </div>
                <div className="text-xs text-gray-500 mt-2">
                  {metrics.count.toLocaleString()} opportunités
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Performance par Horizon */}
      <div>
        <h4 className="text-md font-medium text-gray-700 mb-4">⏰ Performance par Horizon</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {Object.entries(horizon_performance).map(([horizon, metrics]) => (
            <div key={horizon} className={`border rounded-lg p-4 ${getHorizonColor(horizon)}`}>
              <div className="font-semibold text-sm mb-2">{horizon} jour{horizon !== '1' ? 's' : ''}</div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span>Succès:</span>
                  <span className="font-medium">{formatPercentage(metrics.success_rate)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Retour:</span>
                  <span className="font-medium">{formatCurrency(metrics.mean_return)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Sharpe:</span>
                  <span className="font-medium">{formatNumber(metrics.sharpe_ratio)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Gain:</span>
                  <span className="font-medium">{formatPercentage(metrics.win_rate)}</span>
                </div>
                <div className="text-xs text-gray-500 mt-2">
                  {metrics.count.toLocaleString()} opportunités
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Informations supplémentaires */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <div className="text-sm text-gray-600">
          <p className="font-medium mb-2">📋 Informations sur l'Analyse:</p>
          <ul className="space-y-1 text-xs">
            <li>• Analyse basée sur {summary.total_opportunities.toLocaleString()} opportunités ML réelles</li>
            <li>• Données historiques depuis le 1er janvier 2025 jusqu'au 15 septembre 2025</li>
            <li>• 101 symboles analysés sur 3 horizons (1, 7, 30 jours)</li>
            <li>• Modèles ML sophistiqués avec indicateurs techniques avancés</li>
            <li>• Base de données de 88,173 opportunités historiques générées</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default MLPerformanceKPIs;
