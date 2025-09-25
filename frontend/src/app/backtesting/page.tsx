'use client';

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { BacktestRun, BacktestCreateForm } from '../../types/strategies';
import { backtestingApi } from '../../services/strategiesApi';
import { BacktestList, BacktestForm } from '../../components/backtesting/BacktestManagement';
import { BacktestResultsView } from '../../components/backtesting/BacktestResults';
import { ChartBarIcon, PlusIcon, PlayIcon, HomeIcon, MagnifyingGlassIcon, CogIcon } from '@heroicons/react/24/outline';

export default function BacktestingPage() {
  const [showForm, setShowForm] = useState(false);
  const [viewingResults, setViewingResults] = useState<number | null>(null);
  const [runningBacktest, setRunningBacktest] = useState<number | null>(null);

  const queryClient = useQueryClient();

  const createMutation = useMutation(
    (backtestData: BacktestCreateForm) => backtestingApi.createBacktest(backtestData),
    {
      onSuccess: (result) => {
        queryClient.invalidateQueries('backtests');
        setShowForm(false);
        alert('Backtest créé avec succès!');
        // Automatiquement exécuter le backtest après création
        if (result.backtest_run_id) {
          runBacktestMutation.mutate(result.backtest_run_id);
        }
      },
      onError: (error: any) => {
        alert(`Erreur lors de la création: ${error.message}`);
      }
    }
  );

  const runBacktestMutation = useMutation(
    (backtestId: number) => backtestingApi.runBacktest(backtestId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('backtests');
        setRunningBacktest(null);
        alert('Backtest exécuté avec succès!');
      },
      onError: (error: any) => {
        setRunningBacktest(null);
        alert(`Erreur lors de l'exécution: ${error.message}`);
      }
    }
  );

  const handleCreateBacktest = (backtestData: BacktestCreateForm) => {
    createMutation.mutate(backtestData);
  };

  const handleRunBacktest = (backtestId: number) => {
    setRunningBacktest(backtestId);
    runBacktestMutation.mutate(backtestId);
  };

  const handleViewResults = (backtestId: number) => {
    setViewingResults(backtestId);
  };

  const handleDeleteBacktest = (backtestId: number) => {
    queryClient.invalidateQueries('backtests');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="flex space-x-8">
              <a
                href="/"
                className="flex items-center py-4 px-1 border-b-2 font-medium text-sm border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                <HomeIcon className="h-5 w-5 mr-2" />
                Dashboard
              </a>
              <a
                href="/screener"
                className="flex items-center py-4 px-1 border-b-2 font-medium text-sm border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
                Screener
              </a>
              <a
                href="/strategies"
                className="flex items-center py-4 px-1 border-b-2 font-medium text-sm border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              >
                <CogIcon className="h-5 w-5 mr-2" />
                Stratégies
              </a>
              <div className="flex items-center py-4 px-1 border-b-2 font-medium text-sm border-blue-500 text-blue-600">
                <ChartBarIcon className="h-5 w-5 mr-2" />
                Backtesting
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Backtesting</h1>
                <p className="text-sm text-gray-600">Testez vos stratégies sur des données historiques</p>
              </div>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={() => setShowForm(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
              >
                <PlusIcon className="h-4 w-4 mr-2" />
                Nouveau Backtest
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Statistiques rapides */}
        <BacktestStats />

        {/* Liste des backtests */}
        <div className="mt-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Mes Backtests</h2>
          <BacktestList
            onViewResults={handleViewResults}
            onDelete={handleDeleteBacktest}
          />
        </div>

        {/* Formulaire de création */}
        {showForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold">Nouveau Backtest</h2>
                <button
                  onClick={() => setShowForm(false)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
              <BacktestForm
                onSave={handleCreateBacktest}
                onCancel={() => setShowForm(false)}
              />
            </div>
          </div>
        )}

        {/* Modal des résultats */}
        {viewingResults && (
          <BacktestResultsView
            backtestId={viewingResults}
            onClose={() => setViewingResults(null)}
          />
        )}

        {/* Indicateur de backtest en cours */}
        {runningBacktest && (
          <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
            Exécution du backtest en cours...
          </div>
        )}
      </div>
    </div>
  );
}

const BacktestStats: React.FC = () => {
  const { data: backtests } = useQuery(
    'backtests',
    () => backtestingApi.getBacktestRuns(),
    {
      refetchOnWindowFocus: false
    }
  );

  if (!backtests) return null;

  const totalBacktests = backtests.length;
  const completedBacktests = backtests.filter(b => b.status === 'completed').length;
  const failedBacktests = backtests.filter(b => b.status === 'failed').length;
  const runningBacktests = backtests.filter(b => b.status === 'running').length;

  const avgReturn = backtests
    .filter(b => b.status === 'completed')
    .reduce((sum, b) => sum + (b as any).total_return || 0, 0) / completedBacktests || 0;

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <ChartBarIcon className="h-8 w-8 text-blue-600" />
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-500">Total Backtests</p>
            <p className="text-2xl font-semibold text-gray-900">{totalBacktests}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
              <svg className="h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            </div>
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-500">Terminés</p>
            <p className="text-2xl font-semibold text-gray-900">{completedBacktests}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="h-8 w-8 bg-red-100 rounded-full flex items-center justify-center">
              <svg className="h-5 w-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </div>
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-500">Échecs</p>
            <p className="text-2xl font-semibold text-gray-900">{failedBacktests}</p>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
              <PlayIcon className="h-5 w-5 text-blue-600" />
            </div>
          </div>
          <div className="ml-4">
            <p className="text-sm font-medium text-gray-500">En Cours</p>
            <p className="text-2xl font-semibold text-gray-900">{runningBacktests}</p>
          </div>
        </div>
      </div>
    </div>
  );
};
