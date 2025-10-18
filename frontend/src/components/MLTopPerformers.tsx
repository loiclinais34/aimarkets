import React, { useState, useEffect } from 'react';
import { mlPerformanceApi } from '../services/mlPerformanceApi';

interface MLTopPerformersProps {
  className?: string;
}

interface TopPerformer {
  symbol: string;
  performance: {
    count: number;
    success_rate: number;
    mean_return: number;
    avg_confidence: number;
    volatility: number;
    sharpe_ratio: number;
    max_drawdown: number;
    win_rate: number;
    profit_factor: number;
  };
}

const MLTopPerformers: React.FC<MLTopPerformersProps> = ({ className = '' }) => {
  const [topPerformers, setTopPerformers] = useState<TopPerformer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTopPerformers = async () => {
      try {
        setLoading(true);
        const data = await mlPerformanceApi.getMLTopPerformers(10, 1000);
        setTopPerformers(data.top_performers || []);
        setError(null);
      } catch (err) {
        console.error('Error fetching ML top performers:', err);
        setError('Erreur lors du chargement des meilleurs symboles');
      } finally {
        setLoading(false);
      }
    };

    fetchTopPerformers();
  }, []);

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || topPerformers.length === 0) {
    return (
      <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          🏆 Meilleurs Symboles ML
        </h3>
        <div className="text-center text-gray-500">
          <p>{error || 'Aucune donnée disponible'}</p>
          <p className="text-sm mt-2">
            Les données nécessitent des opportunités ML avec des retours calculés.
          </p>
        </div>
      </div>
    );
  }

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;
  const formatNumber = (value: number, decimals: number = 3) => value.toFixed(decimals);
  const formatCurrency = (value: number) => `${(value * 100).toFixed(2)}%`;

  const getPerformanceColor = (successRate: number) => {
    if (successRate >= 0.6) return 'text-green-600 bg-green-50 border-green-200';
    if (successRate >= 0.4) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getReturnColor = (returnValue: number) => {
    if (returnValue >= 0.05) return 'text-green-600';
    if (returnValue >= 0) return 'text-green-500';
    return 'text-red-600';
  };

  return (
    <div className={`bg-white rounded-lg shadow p-6 ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 mb-6">
        🏆 Meilleurs Symboles ML
      </h3>

      <div className="space-y-4">
        {topPerformers.map((performer, index) => (
          <div key={performer.symbol} className={`border rounded-lg p-4 ${getPerformanceColor(performer.performance.success_rate)}`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center">
                <div className="flex-shrink-0 w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center mr-3">
                  <span className="text-sm font-bold text-gray-600">#{index + 1}</span>
                </div>
                <div>
                  <h4 className="font-semibold text-lg">{performer.symbol}</h4>
                  <p className="text-sm text-gray-600">
                    {performer.performance.count} opportunités analysées
                  </p>
                </div>
              </div>
              <div className="text-right">
                <div className={`text-lg font-bold ${getReturnColor(performer.performance.mean_return)}`}>
                  {formatCurrency(performer.performance.mean_return)}
                </div>
                <div className="text-sm text-gray-600">
                  Retour moyen
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-gray-500">Taux de Succès</div>
                <div className="font-semibold">{formatPercentage(performer.performance.success_rate)}</div>
              </div>
              <div>
                <div className="text-gray-500">Ratio de Sharpe</div>
                <div className="font-semibold">{formatNumber(performer.performance.sharpe_ratio)}</div>
              </div>
              <div>
                <div className="text-gray-500">Taux de Gain</div>
                <div className="font-semibold">{formatPercentage(performer.performance.win_rate)}</div>
              </div>
              <div>
                <div className="text-gray-500">Confiance Moy.</div>
                <div className="font-semibold">{formatNumber(performer.performance.avg_confidence)}</div>
              </div>
            </div>

            <div className="mt-3 pt-3 border-t border-gray-200">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-xs text-gray-600">
                <div>
                  <span className="font-medium">Volatilité:</span> {formatCurrency(performer.performance.volatility)}
                </div>
                <div>
                  <span className="font-medium">Max Drawdown:</span> {formatCurrency(performer.performance.max_drawdown)}
                </div>
                <div>
                  <span className="font-medium">Profit Factor:</span> {formatNumber(performer.performance.profit_factor)}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <div className="text-sm text-gray-600">
          <p className="font-medium mb-2">📊 Critères de Classement:</p>
          <ul className="space-y-1 text-xs">
            <li>• Classés par retour moyen décroissant</li>
            <li>• Basé sur 6,162 opportunités ML avec retours calculés</li>
            <li>• Analyse sur 3 horizons (1, 7, 30 jours)</li>
            <li>• Modèles ML sophistiqués avec indicateurs techniques</li>
            <li>• Données historiques réelles depuis janvier 2025</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default MLTopPerformers;
