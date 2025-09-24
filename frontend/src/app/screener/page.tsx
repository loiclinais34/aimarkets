'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import { 
  MagnifyingGlassIcon,
  ChartBarIcon,
  ClockIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline'
import { apiService, screenerApi } from '@/services/api'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'
import ScreenerProgress from '@/components/ScreenerProgress'
import ScreenerResults from '@/components/ScreenerResults'
import { toast } from 'react-hot-toast'

interface ScreenerParameters {
  target_return_percentage: number
  time_horizon_days: number
  risk_tolerance: number
}

interface ScreenerResult {
  symbol: string
  company_name: string
  prediction: number
  confidence: number
  model_id: number
  model_name: string
  target_return: number
  time_horizon: number
  rank: number
}

export default function ScreenerPage() {
  const [parameters, setParameters] = useState<ScreenerParameters>({
    target_return_percentage: 0.5,
    time_horizon_days: 30,
    risk_tolerance: 0.2
  })
  
  const [isRunning, setIsRunning] = useState(false)
  const [results, setResults] = useState<ScreenerResult[]>([])
  const [taskId, setTaskId] = useState<string | null>(null)
  const [stats, setStats] = useState<{
    total_symbols: number
    successful_models: number
    execution_time_seconds: number
  } | null>(null)
  
  const queryClient = useQueryClient()

  // Récupérer la liste des symboles disponibles
  const { data: symbols, isLoading: symbolsLoading } = useQuery(
    'symbols',
    () => apiService.getAvailableSymbols(),
    { staleTime: 5 * 60 * 1000 }
  )

  // Mutation pour lancer le screener ML complet
  const screenerMutation = useMutation(
    async (params: ScreenerParameters) => {
      return await screenerApi.runFullScreener(params)
    },
    {
      onSuccess: (data) => {
        setTaskId(data.task_id)
        toast.success('Screener ML lancé en arrière-plan')
      },
      onError: (error: any) => {
        toast.error(error.message || 'Erreur lors du lancement du screener')
      },
    }
  )

  const handleParameterChange = (field: keyof ScreenerParameters, value: number) => {
    setParameters(prev => ({
      ...prev,
      [field]: value
    }))
  }

  const handleRunScreener = async () => {
    setIsRunning(true)
    setResults([])
    setStats(null)
    setTaskId(null)
    try {
      await screenerMutation.mutateAsync(parameters)
    } catch (error) {
      setIsRunning(false)
    }
  }

  const handleComplete = (result: any) => {
    setIsRunning(false)
    setResults(result.results || [])
    setStats({
      total_symbols: result.total_symbols,
      successful_models: result.successful_models,
      execution_time_seconds: result.execution_time_seconds
    })
    toast.success(`Screener terminé ! ${result.results?.length || 0} opportunités trouvées`)
  }

  const handleError = (errorMessage: string) => {
    setIsRunning(false)
    toast.error(errorMessage)
  }

  const getRiskToleranceLabel = (value: number) => {
    if (value <= 0.3) return 'Très conservateur'
    if (value <= 0.5) return 'Conservateur'
    if (value <= 0.7) return 'Modéré'
    if (value <= 0.8) return 'Agressif'
    return 'Très agressif'
  }

  const getRiskToleranceColor = (value: number) => {
    if (value <= 0.3) return 'text-green-600'
    if (value <= 0.5) return 'text-blue-600'
    if (value <= 0.7) return 'text-yellow-600'
    if (value <= 0.8) return 'text-orange-600'
    return 'text-red-600'
  }

  if (symbolsLoading) {
    return <LoadingSpinner message="Chargement des données..." />
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex items-center py-6">
              <MagnifyingGlassIcon className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  Screener ML
                </h1>
                <p className="text-sm text-gray-500">
                  Analyse complète avec modèles ML réels sur tous les symboles
                </p>
              </div>
            </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Paramètres du Screener */}
          <div className="lg:col-span-1">
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-lg font-semibold text-gray-900 mb-6">
                Paramètres du Screener ML
              </h2>
              
              {/* Note informative */}
              <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-6">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <CheckCircleIcon className="h-5 w-5 text-blue-400" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-blue-700">
                      <strong>Screener ML opérationnel :</strong> Analyse complète avec modèles ML réels entraînés sur des données historiques. 
                      Le processus peut prendre 2-3 minutes pour analyser tous les symboles.
                    </p>
                  </div>
                </div>
              </div>
              
              <div className="space-y-6">
                {/* Rendement attendu */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rendement attendu (%)
                  </label>
                  <div className="relative">
                    <input
                      type="number"
                      step="0.1"
                      min="0.1"
                      max="50"
                      value={parameters.target_return_percentage}
                      onChange={(e) => handleParameterChange('target_return_percentage', parseFloat(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <span className="absolute right-3 top-2 text-gray-500">%</span>
                  </div>
                </div>

                {/* Horizon temporel */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Horizon temporel (jours)
                  </label>
                  <div className="relative">
                    <ClockIcon className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
                    <input
                      type="number"
                      min="1"
                      max="365"
                      value={parameters.time_horizon_days}
                      onChange={(e) => handleParameterChange('time_horizon_days', parseInt(e.target.value))}
                      className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                {/* Tolérance au risque */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tolérance au risque
                  </label>
                  <div className="space-y-2">
                    <input
                      type="range"
                      min="0.1"
                      max="1.0"
                      step="0.1"
                      value={parameters.risk_tolerance}
                      onChange={(e) => handleParameterChange('risk_tolerance', parseFloat(e.target.value))}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>Conservateur</span>
                      <span className={`font-medium ${getRiskToleranceColor(parameters.risk_tolerance)}`}>
                        {getRiskToleranceLabel(parameters.risk_tolerance)}
                      </span>
                      <span>Agressif</span>
                    </div>
                    <div className="text-sm text-gray-600">
                      Seuil de confiance: {(parameters.risk_tolerance * 100).toFixed(0)}%
                    </div>
                  </div>
                </div>

                {/* Bouton de lancement */}
                <button
                  onClick={handleRunScreener}
                  disabled={isRunning || screenerMutation.isLoading}
                  className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {isRunning || screenerMutation.isLoading ? (
                    <>
                      <LoadingSpinner message="" />
                      <span className="ml-2">Analyse en cours...</span>
                    </>
                  ) : (
                    <>
                      <MagnifyingGlassIcon className="h-5 w-5 mr-2" />
                      Lancer le Screener ML
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>

          {/* Progression et Résultats du Screener */}
          <div className="lg:col-span-2 space-y-6">
            {/* Progression */}
            {isRunning && taskId && (
              <ScreenerProgress
                taskId={taskId}
                onComplete={handleComplete}
                onError={handleError}
              />
            )}

            {/* Résultats */}
            {results.length > 0 && stats && (
              <ScreenerResults
                results={results}
                totalSymbols={stats.total_symbols}
                successfulModels={stats.successful_models}
                executionTime={stats.execution_time_seconds}
              />
            )}

            {/* État initial */}
            {!isRunning && results.length === 0 && (
              <div className="bg-white p-6 rounded-lg shadow">
                <div className="text-center py-12">
                  <ChartBarIcon className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                  <p className="text-gray-500">Aucun résultat pour le moment</p>
                  <p className="text-sm text-gray-400">Configurez les paramètres et lancez le screener</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
