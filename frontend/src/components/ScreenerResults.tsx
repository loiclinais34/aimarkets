'use client'

import React from 'react'
import { CheckCircleIcon, ChartBarIcon } from '@heroicons/react/24/outline'
import { formatTime, formatPercentage } from '@/utils/formatters'

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

interface ScreenerResultsProps {
  results: ScreenerResult[]
  totalSymbols: number
  successfulModels: number
  executionTime: number
}

export default function ScreenerResults({ 
  results, 
  totalSymbols, 
  successfulModels, 
  executionTime 
}: ScreenerResultsProps) {
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100'
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100'
    return 'text-red-600 bg-red-100'
  }

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'Très élevée'
    if (confidence >= 0.6) return 'Élevée'
    return 'Moyenne'
  }

  return (
    <div className="bg-white rounded-lg shadow">
      {/* En-tête avec statistiques */}
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">
            🎯 Résultats du Screener
          </h3>
          <div className="text-sm text-gray-500">
            Terminé en {formatTime(executionTime)}
          </div>
        </div>
        
        <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 rounded-lg p-3">
            <div className="text-2xl font-bold text-blue-600">{totalSymbols}</div>
            <div className="text-sm text-blue-800">Symboles analysés</div>
          </div>
          <div className="bg-green-50 rounded-lg p-3">
            <div className="text-2xl font-bold text-green-600">{successfulModels}</div>
            <div className="text-sm text-green-800">Modèles entraînés</div>
          </div>
          <div className="bg-purple-50 rounded-lg p-3">
            <div className="text-2xl font-bold text-purple-600">{results.length}</div>
            <div className="text-sm text-purple-800">Opportunités trouvées</div>
          </div>
        </div>
      </div>

      {/* Liste des résultats */}
      <div className="divide-y divide-gray-200">
        {results.length === 0 ? (
          <div className="px-6 py-8 text-center">
            <div className="text-gray-400 text-4xl mb-2">🔍</div>
            <h4 className="text-lg font-medium text-gray-900 mb-2">
              Aucune opportunité trouvée
            </h4>
            <p className="text-gray-500">
              Aucun symbole n'a atteint le seuil de confiance requis.
            </p>
          </div>
        ) : (
          results.map((result) => (
            <div key={result.symbol} className="px-6 py-4 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-3">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-sm font-medium text-blue-600">
                          #{result.rank}
                        </span>
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <h4 className="text-lg font-medium text-gray-900">
                          {result.symbol}
                        </h4>
                        <span className="text-sm text-gray-500">
                          {result.company_name}
                        </span>
                      </div>
                      <div className="mt-1 text-sm text-gray-500">
                        Modèle: {result.model_name}
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="text-right">
                    <div className="text-sm text-gray-500">Confiance</div>
                    <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(result.confidence)}`}>
                      {getConfidenceLabel(result.confidence)}
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-2xl font-bold text-green-600">
                      {formatPercentage(result.confidence)}
                    </div>
                    <div className="text-sm text-gray-500">
                      {result.target_return}% sur {result.time_horizon}j
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Actions */}
      {results.length > 0 && (
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-500">
              {results.length} opportunité{results.length > 1 ? 's' : ''} trouvée{results.length > 1 ? 's' : ''}
            </div>
            <div className="flex space-x-3">
              <button className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                📊 Exporter
              </button>
              <button className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                📈 Analyser
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
