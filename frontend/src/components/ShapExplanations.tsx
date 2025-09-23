'use client'

import React, { useState } from 'react'
import { useQuery } from 'react-query'
import { apiService, ShapExplanationsResponse, FeatureImportanceResponse } from '@/services/api'
import LoadingSpinner from './LoadingSpinner'
import ErrorMessage from './ErrorMessage'
import { 
  ChartBarIcon, 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline'

interface ShapExplanationsProps {
  modelId: number
  symbol: string
  predictionDate: string
  onClose?: () => void
}

const ShapExplanations: React.FC<ShapExplanationsProps> = ({
  modelId,
  symbol,
  predictionDate,
  onClose
}) => {
  const [activeTab, setActiveTab] = useState<'shap' | 'importance'>('shap')

  // Requête pour les explications SHAP
  const { 
    data: shapData, 
    isLoading: shapLoading, 
    error: shapError 
  } = useQuery<ShapExplanationsResponse>({
    queryKey: ['shap-explanations', modelId, symbol, predictionDate],
    queryFn: () => apiService.getShapExplanations({
      model_id: modelId,
      symbol,
      prediction_date: predictionDate
    }),
    enabled: activeTab === 'shap'
  })

  // Requête pour l'importance des features
  const { 
    data: importanceData, 
    isLoading: importanceLoading, 
    error: importanceError 
  } = useQuery<FeatureImportanceResponse>({
    queryKey: ['feature-importance', modelId],
    queryFn: () => apiService.getModelFeatureImportance(modelId),
    enabled: activeTab === 'importance'
  })

  const formatValue = (value: number, decimals: number = 4) => {
    return value.toFixed(decimals)
  }

  const getImpactColor = (impact: 'positive' | 'negative') => {
    return impact === 'positive' 
      ? 'text-green-600 bg-green-50' 
      : 'text-red-600 bg-red-50'
  }

  const getImpactIcon = (impact: 'positive' | 'negative') => {
    return impact === 'positive' 
      ? <ArrowTrendingUpIcon className="w-4 h-4" />
      : <ArrowTrendingDownIcon className="w-4 h-4" />
  }

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <ChartBarIcon className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">
            Interprétabilité du Modèle
          </h2>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
        <button
          onClick={() => setActiveTab('shap')}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'shap'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Explications SHAP
        </button>
        <button
          onClick={() => setActiveTab('importance')}
          className={`flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors ${
            activeTab === 'importance'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Importance des Features
        </button>
      </div>

      {/* Content */}
      {activeTab === 'shap' && (
        <div>
          {shapLoading && <LoadingSpinner />}
          {shapError && <ErrorMessage message="Erreur lors du chargement des explications SHAP" />}
          
          {shapData && (
            <div className="space-y-6">
              {/* Informations générales */}
              <div className="bg-blue-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <InformationCircleIcon className="w-5 h-5 text-blue-600" />
                  <h3 className="font-medium text-blue-900">Informations de la Prédiction</h3>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-blue-700 font-medium">Modèle:</span>
                    <p className="text-blue-900">{shapData.model_name}</p>
                  </div>
                  <div>
                    <span className="text-blue-700 font-medium">Symbole:</span>
                    <p className="text-blue-900">{shapData.symbol}</p>
                  </div>
                  <div>
                    <span className="text-blue-700 font-medium">Prédiction:</span>
                    <p className="text-blue-900 font-semibold">
                      {shapData.model_type === 'classification' 
                        ? (shapData.prediction > 0.5 ? 'Classe Positive' : 'Classe Négative')
                        : formatValue(shapData.prediction, 2)
                      }
                    </p>
                  </div>
                  <div>
                    <span className="text-blue-700 font-medium">Valeur de Base:</span>
                    <p className="text-blue-900">{formatValue(shapData.base_value, 4)}</p>
                  </div>
                </div>
              </div>

              {/* Explications SHAP */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Contribution de chaque Feature
                </h3>
                <div className="space-y-3">
                  {shapData.shap_explanations.map((explanation, index) => (
                    <div
                      key={explanation.feature}
                      className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex-1">
                        <div className="flex items-center space-x-3">
                          <span className="text-sm font-medium text-gray-600 w-6">
                            #{index + 1}
                          </span>
                          <span className="font-medium text-gray-900">
                            {explanation.feature}
                          </span>
                          <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getImpactColor(explanation.impact)}`}>
                            {getImpactIcon(explanation.impact)}
                            <span>{explanation.impact === 'positive' ? 'Positif' : 'Négatif'}</span>
                          </div>
                        </div>
                        <div className="mt-2 text-sm text-gray-600">
                          Valeur: <span className="font-mono">{formatValue(explanation.feature_value, 2)}</span>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-lg font-semibold ${
                          explanation.shap_value > 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {explanation.shap_value > 0 ? '+' : ''}{formatValue(explanation.shap_value, 4)}
                        </div>
                        <div className="text-xs text-gray-500">Contribution SHAP</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'importance' && (
        <div>
          {importanceLoading && <LoadingSpinner />}
          {importanceError && <ErrorMessage message="Erreur lors du chargement de l'importance des features" />}
          
          {importanceData && (
            <div className="space-y-6">
              {/* Informations générales */}
              <div className="bg-green-50 rounded-lg p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <InformationCircleIcon className="w-5 h-5 text-green-600" />
                  <h3 className="font-medium text-green-900">Importance Globale des Features</h3>
                </div>
                <div className="text-sm text-green-700">
                  <p>Modèle: <span className="font-medium">{importanceData.model_name}</span></p>
                  <p>Type: <span className="font-medium">{importanceData.model_type}</span></p>
                </div>
              </div>

              {/* Graphique d'importance */}
              <div>
                <h3 className="text-lg font-medium text-gray-900 mb-4">
                  Classement par Importance
                </h3>
                <div className="space-y-3">
                  {importanceData.feature_importances.map((feature, index) => (
                    <div
                      key={feature.feature}
                      className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                      <span className="text-sm font-medium text-gray-600 w-6">
                        #{index + 1}
                      </span>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-900">
                            {feature.feature}
                          </span>
                          <span className="text-sm font-semibold text-gray-700">
                            {formatValue(feature.importance, 4)}
                          </span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${(feature.importance / importanceData.feature_importances[0].importance) * 100}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ShapExplanations
