'use client'

import { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { 
  ChartBarIcon, 
  CpuChipIcon, 
  ChartBarSquareIcon, 
  ArrowTrendingUpIcon,
  MagnifyingGlassIcon,
  InformationCircleIcon,
  PlayIcon,
  StopIcon
} from '@heroicons/react/24/outline'
import { apiService, SymbolWithMetadata } from '@/services/api'
import TargetParameterForm from '@/components/TargetParameterForm'
import TargetParameterList from '@/components/TargetParameterList'
import MLModelList from '@/components/MLModelList'
import ModelTrainingForm from '@/components/ModelTrainingForm'
import PredictionForm from '@/components/PredictionForm'
import DataStats from '@/components/DataStats'
import SymbolSelector from '@/components/SymbolSelector'
import PriceChart from '@/components/PriceChart'
import DataFreshnessIndicator from '@/components/DataFreshnessIndicator'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'

export default function Dashboard() {
  const [selectedSymbol, setSelectedSymbol] = useState<string>('AAPL')
  const [activeTab, setActiveTab] = useState<'overview' | 'targets' | 'models' | 'predictions'>('overview')
  const [userId] = useState<string>('demo_user')

  // Queries pour les données
  const { data: symbols, isLoading: symbolsLoading } = useQuery<SymbolWithMetadata[]>(
    'symbols',
    () => apiService.getAvailableSymbols(),
    { staleTime: 5 * 60 * 1000 } // 5 minutes
  )

  const { data: dataStats, isLoading: statsLoading } = useQuery(
    'dataStats',
    () => apiService.getDataStats(),
    { staleTime: 2 * 60 * 1000 } // 2 minutes
  )

  const { data: targetParameters, isLoading: targetsLoading, refetch: refetchTargets } = useQuery(
    ['targetParameters', userId],
    () => apiService.getTargetParameters(userId),
    { staleTime: 1 * 60 * 1000 } // 1 minute
  )

  const { data: mlModels, isLoading: modelsLoading, refetch: refetchModels } = useQuery(
    'mlModels',
    () => apiService.getMLModels({ active_only: true }),
    { staleTime: 1 * 60 * 1000 } // 1 minute
  )

  const { data: modelStats, isLoading: modelStatsLoading } = useQuery(
    'modelStats',
    () => apiService.getModelStats(),
    { staleTime: 2 * 60 * 1000 } // 2 minutes
  )

  // Gestion des erreurs
  if (symbolsLoading || statsLoading) {
    return <LoadingSpinner message="Chargement des données..." />;
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <ArrowTrendingUpIcon className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AIMarkets</h1>
                <p className="text-sm text-gray-500">Analyse d'opportunités sur les marchés financiers</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <SymbolSelector
                symbols={symbols || []}
                selectedSymbol={selectedSymbol}
                onSymbolChange={setSelectedSymbol}
                loading={symbolsLoading}
              />
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="flex space-x-8">
              {[
                { id: 'overview', name: 'Vue d\'ensemble', icon: ChartBarIcon },
                { id: 'targets', name: 'Paramètres de Cible', icon: ChartBarSquareIcon },
                { id: 'models', name: 'Modèles ML', icon: CpuChipIcon },
                { id: 'predictions', name: 'Prédictions', icon: ArrowTrendingUpIcon },
                { id: 'screener', name: 'Screener', icon: MagnifyingGlassIcon, href: '/screener' },
              ].map((tab) => (
                tab.href ? (
                  <a
                    key={tab.id}
                    href={tab.href}
                    className="flex items-center py-4 px-1 border-b-2 font-medium text-sm border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  >
                    {(() => {
                      const IconComponent = tab.icon
                      return <IconComponent className="h-5 w-5 mr-2" />
                    })()}
                    {tab.name}
                  </a>
                ) : (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center py-4 px-1 border-b-2 font-medium text-sm ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    {(() => {
                      const IconComponent = tab.icon
                      return <IconComponent className="h-5 w-5 mr-2" />
                    })()}
                    {tab.name}
                  </button>
                )
              ))}
            </div>
            
            {/* Indicateur de fraîcheur des données compact */}
            <div className="py-2">
              <DataFreshnessIndicator compact={true} />
            </div>
          </div>
        </div>
      </nav>

      {/* Contenu principal */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-8">
            {/* Statistiques globales */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <ChartBarIcon className="h-6 w-6 text-blue-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Symboles</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dataStats?.total_symbols || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <ArrowTrendingUpIcon className="h-6 w-6 text-green-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Enregistrements</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {dataStats?.total_historical_records?.toLocaleString() || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <CpuChipIcon className="h-6 w-6 text-purple-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Modèles ML</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {modelStats?.total_models || 0}
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <div className="flex items-center">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <ChartBarSquareIcon className="h-6 w-6 text-orange-600" />
                  </div>
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-500">Paramètres</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {targetParameters?.length || 0}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Indicateur de fraîcheur des données historiques */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <InformationCircleIcon className="h-5 w-5 mr-2 text-blue-600" />
                État des Données Historiques
              </h2>
              <DataFreshnessIndicator showDetails={true} />
            </div>

            {/* Graphique des prix */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Prix de {selectedSymbol}
              </h2>
              <PriceChart symbol={selectedSymbol} />
            </div>

            {/* Détails des données */}
            <DataStats stats={dataStats} loading={statsLoading} />
          </div>
        )}

        {activeTab === 'targets' && (
          <div className="space-y-8">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">Paramètres de Cible</h2>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Créer un nouveau paramètre
                </h3>
                <TargetParameterForm
                  userId={userId}
                  onSuccess={() => refetchTargets()}
                />
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Paramètres existants
                </h3>
                <TargetParameterList
                  parameters={targetParameters || []}
                  loading={targetsLoading}
                  onUpdate={() => refetchTargets()}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'models' && (
          <div className="space-y-8">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">Modèles de Machine Learning</h2>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Entraîner un nouveau modèle
                </h3>
                <ModelTrainingForm
                  symbols={symbols || []}
                  targetParameters={targetParameters || []}
                  onSuccess={() => refetchModels()}
                />
              </div>

              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Modèles existants
                </h3>
                <MLModelList
                  models={mlModels || []}
                  loading={modelsLoading}
                  onUpdate={() => refetchModels()}
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'predictions' && (
          <div className="space-y-8">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">Prédictions</h2>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Faire une prédiction
              </h3>
              <PredictionForm
                symbols={symbols || []}
                models={mlModels || []}
              />
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
