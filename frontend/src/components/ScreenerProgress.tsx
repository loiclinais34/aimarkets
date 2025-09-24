'use client'

import React, { useState, useEffect } from 'react'
import { screenerApi } from '@/services/api'

interface ScreenerProgressProps {
  taskId: string
  onComplete: (result: any) => void
  onError: (error: string) => void
}

interface TaskStatus {
  state: string
  status: string
  progress: number
  meta?: {
    current_step?: string
    current_symbol?: string
    total_symbols?: number
    trained_models?: number
    successful_models?: number
    predictions_made?: number
    screener_run_id?: number
  }
  result?: any
}

export default function ScreenerProgress({ taskId, onComplete, onError }: ScreenerProgressProps) {
  const [status, setStatus] = useState<TaskStatus | null>(null)
  const [isPolling, setIsPolling] = useState(true)

  useEffect(() => {
    if (!taskId || !isPolling) return

    const pollStatus = async () => {
      try {
        const statusData = await screenerApi.getTaskStatus(taskId)
        setStatus(statusData)

        if (statusData.state === 'SUCCESS') {
          setIsPolling(false)
          // Les résultats sont dans statusData.result.result
          const actualResult = statusData.result?.result || statusData.result
          onComplete(actualResult)
        } else if (statusData.state === 'FAILURE') {
          setIsPolling(false)
          onError(statusData.status)
        }
      } catch (error) {
        console.error('Erreur lors de la récupération du statut:', error)
        setIsPolling(false)
        onError('Erreur lors du suivi de la progression')
      }
    }

    // Polling immédiat
    pollStatus()

    // Polling toutes les 2 secondes
    const interval = setInterval(pollStatus, 2000)

    return () => clearInterval(interval)
  }, [taskId, isPolling, onComplete, onError])

  if (!status) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Initialisation...</span>
        </div>
      </div>
    )
  }

  const getStepIcon = (step: string) => {
    switch (step) {
      case 'initialization':
        return '🚀'
      case 'fetching_symbols':
        return '📋'
      case 'training_models':
        return '🤖'
      case 'making_predictions':
        return '🔮'
      case 'completed':
        return '✅'
      default:
        return '⏳'
    }
  }

  const getStepName = (step: string) => {
    switch (step) {
      case 'initialization':
        return 'Initialisation'
      case 'fetching_symbols':
        return 'Récupération des symboles'
      case 'training_models':
        return 'Entraînement des modèles'
      case 'making_predictions':
        return 'Calcul des prédictions'
      case 'completed':
        return 'Terminé'
      default:
        return 'En cours'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="mb-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-lg font-medium text-gray-900">
            {getStepIcon(status.meta?.current_step || '')} {getStepName(status.meta?.current_step || '')}
          </h3>
          <span className="text-sm font-medium text-blue-600">
            {status.progress}%
          </span>
        </div>
        
        {/* Barre de progression */}
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${status.progress}%` }}
          ></div>
        </div>
      </div>

      {/* Statut détaillé */}
      <div className="space-y-2">
        <p className="text-sm text-gray-600">{status.status}</p>
        
        {status.meta?.current_symbol && (
          <p className="text-sm text-blue-600">
            🔍 Traitement: <span className="font-medium">{status.meta.current_symbol}</span>
          </p>
        )}

        {status.meta?.total_symbols && (
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-500">Symboles analysés:</span>
              <span className="ml-2 font-medium">{status.meta.total_symbols}</span>
            </div>
            {status.meta.trained_models !== undefined && (
              <div>
                <span className="text-gray-500">Modèles entraînés:</span>
                <span className="ml-2 font-medium">
                  {status.meta.trained_models}/{status.meta.total_symbols}
                </span>
              </div>
            )}
            {status.meta.successful_models !== undefined && (
              <div>
                <span className="text-gray-500">Modèles réussis:</span>
                <span className="ml-2 font-medium">{status.meta.successful_models}</span>
              </div>
            )}
            {status.meta.predictions_made !== undefined && (
              <div>
                <span className="text-gray-500">Prédictions:</span>
                <span className="ml-2 font-medium">{status.meta.predictions_made}</span>
              </div>
            )}
          </div>
        )}

        {status.meta?.screener_run_id && (
          <p className="text-xs text-gray-400">
            ID de run: {status.meta.screener_run_id}
          </p>
        )}
      </div>

      {/* Indicateur de progression */}
      {isPolling && (
        <div className="mt-4 flex items-center text-sm text-gray-500">
          <div className="animate-pulse w-2 h-2 bg-blue-600 rounded-full mr-2"></div>
          Mise à jour en temps réel...
        </div>
      )}
    </div>
  )
}
