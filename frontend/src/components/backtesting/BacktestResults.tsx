'use client';

import React, { useState, useEffect } from 'react';
import { useQuery } from 'react-query';
import { BacktestResults, BacktestTrade, BacktestMetrics, BacktestEquityPoint } from '../../types/strategies';
import { backtestingApi } from '../../services/strategiesApi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

interface BacktestResultsProps {
  backtestId: number;
  onClose: () => void;
}

export const BacktestResultsView: React.FC<BacktestResultsProps> = ({
  backtestId,
  onClose
}) => {
  const { data: results, isLoading, error } = useQuery(
    ['backtest-results', backtestId],
    () => backtestingApi.getBacktestResults(backtestId),
    {
      refetchOnWindowFocus: false
    }
  );

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="flex justify-center items-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !results) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Erreur</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
          <p className="text-red-600">Erreur lors du chargement des résultats</p>
        </div>
      </div>
    );
  }

  const { backtest_run, trades, metrics, equity_curve } = results;

  // Vérifier si les métriques sont disponibles
  if (!metrics) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Résultats du Backtest</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>
          <div className="text-center py-8">
            <p className="text-gray-600">Les métriques du backtest ne sont pas encore disponibles.</p>
            <p className="text-sm text-gray-500 mt-2">Le backtest est peut-être encore en cours d'exécution.</p>
          </div>
        </div>
      </div>
    );
  }

  // Préparer les données pour les graphiques
  const equityData = equity_curve?.map((point: BacktestEquityPoint) => ({
    date: new Date(point.date).toLocaleDateString('fr-FR'),
    equity: point.equity_value,
    drawdown: point.drawdown,
    cumulative_return: point.cumulative_return
  }));

  const tradesBySymbol = trades.reduce((acc: Record<string, number>, trade: BacktestTrade) => {
    acc[trade.symbol] = (acc[trade.symbol] || 0) + 1;
    return acc;
  }, {});

  const tradesData = Object.entries(tradesBySymbol).map(([symbol, count]) => ({
    symbol,
    count
  }));

  const profitableTrades = trades.filter((trade: BacktestTrade) => trade.net_pnl > 0).length;
  const losingTrades = trades.filter((trade: BacktestTrade) => trade.net_pnl < 0).length;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold">{backtest_run.name}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl"
          >
            ✕
          </button>
        </div>

        {/* Métriques principales */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 rounded-lg p-4">
            <p className="text-sm text-blue-600">Retour Total</p>
            <p className="text-2xl font-bold text-blue-800">
              {metrics.total_return.toFixed(2)}%
            </p>
          </div>
          <div className="bg-green-50 rounded-lg p-4">
            <p className="text-sm text-green-600">Capital Final</p>
            <p className="text-2xl font-bold text-green-800">
              ${metrics.final_capital.toLocaleString()}
            </p>
          </div>
          <div className="bg-purple-50 rounded-lg p-4">
            <p className="text-sm text-purple-600">Taux de Réussite</p>
            <p className="text-2xl font-bold text-purple-800">
              {metrics.win_rate.toFixed(1)}%
            </p>
          </div>
          <div className="bg-red-50 rounded-lg p-4">
            <p className="text-sm text-red-600">Max Drawdown</p>
            <p className="text-2xl font-bold text-red-800">
              {metrics.max_drawdown.toFixed(2)}%
            </p>
          </div>
        </div>

        {/* Graphique de la courbe d'équité */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold mb-4">Courbe d'Équité</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={equityData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip 
                  formatter={(value: any, name: string) => [
                    name === 'equity' ? `$${value.toLocaleString()}` : `${value.toFixed(2)}%`,
                    name === 'equity' ? 'Équité' : name === 'drawdown' ? 'Drawdown' : 'Retour Cumulé'
                  ]}
                />
                <Line 
                  type="monotone" 
                  dataKey="equity" 
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  name="Équité"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Métriques détaillées */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div>
            <h3 className="text-lg font-semibold mb-4">Métriques de Performance</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Retour Annualisé:</span>
                <span className="font-medium">{metrics.annualized_return.toFixed(2)}%</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Sharpe Ratio:</span>
                <span className="font-medium">{metrics.sharpe_ratio.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Sortino Ratio:</span>
                <span className="font-medium">{metrics.sortino_ratio.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Calmar Ratio:</span>
                <span className="font-medium">{metrics.calmar_ratio.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Volatilité:</span>
                <span className="font-medium">{metrics.volatility.toFixed(2)}%</span>
              </div>
            </div>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Métriques de Trading</h3>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-gray-600">Total des Trades:</span>
                <span className="font-medium">{metrics.total_trades}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Trades Gagnants:</span>
                <span className="font-medium text-green-600">{metrics.winning_trades}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Trades Perdants:</span>
                <span className="font-medium text-red-600">{metrics.losing_trades}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Profit Factor:</span>
                <span className="font-medium">{metrics.profit_factor.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Période Moyenne:</span>
                <span className="font-medium">{metrics.avg_holding_period.toFixed(1)} jours</span>
              </div>
            </div>
          </div>
        </div>

        {/* Graphique des trades par symbole */}
        {tradesData.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-4">Trades par Symbole</h3>
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={tradesData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="symbol" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3B82F6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Tableau des trades */}
        <div>
          <h3 className="text-lg font-semibold mb-4">Détail des Trades</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Symbole</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Entrée</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Sortie</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Prix Entrée</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Prix Sortie</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">P&L</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Retour</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Durée</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {trades?.map((trade: BacktestTrade) => (
                  <tr key={trade.id}>
                    <td className="px-4 py-2 text-sm font-medium text-gray-900">{trade.symbol}</td>
                    <td className="px-4 py-2 text-sm text-gray-500">
                      {new Date(trade.entry_date).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-500">
                      {new Date(trade.exit_date).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-500">${trade.entry_price.toFixed(2)}</td>
                    <td className="px-4 py-2 text-sm text-gray-500">${trade.exit_price.toFixed(2)}</td>
                    <td className={`px-4 py-2 text-sm font-medium ${trade.net_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${trade.net_pnl.toFixed(2)}
                    </td>
                    <td className={`px-4 py-2 text-sm font-medium ${trade.return_percentage >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {trade.return_percentage.toFixed(2)}%
                    </td>
                    <td className="px-4 py-2 text-sm text-gray-500">{trade.holding_days} jours</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Informations sur la stratégie */}
        {backtest_run.strategy_name && (
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h3 className="text-lg font-semibold mb-2">Stratégie Utilisée</h3>
            <p className="text-blue-800">{backtest_run.strategy_name}</p>
          </div>
        )}
      </div>
    </div>
  );
};
