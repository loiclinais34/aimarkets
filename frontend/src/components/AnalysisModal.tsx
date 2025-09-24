'use client'

import React, { useState, useEffect } from 'react'
import { Loader2, TrendingUp, TrendingDown, BarChart3, Brain, Target } from 'lucide-react'
import { apiService } from '@/services/api'
import { toast } from 'react-hot-toast'
import TechnicalChart from './TechnicalChart'

interface AnalysisModalProps {
  isOpen: boolean
  onClose: () => void
  symbol: string
  modelId: number
  companyName?: string
  prediction?: number
  confidence?: number
}

interface AnalysisData {
  symbol: string
  model_info: {
    id: number
    name: string
    version: string
    type: string
    target_return?: number
    time_horizon?: number
    created_at: string
  }
  chart_data: Array<{
    date: string
    open: number
    high: number
    low: number
    close: number
    volume: number
    vwap?: number
  }>
  technical_indicators: {
    sma_20?: number
    sma_50?: number
    ema_20?: number
    rsi_14?: number
    macd?: number
    macd_signal?: number
    bb_upper?: number
    bb_middle?: number
    bb_lower?: number
    atr_14?: number
    obv?: number
  }
  sentiment_indicators: {
    sentiment_score_normalized?: number
    sentiment_momentum_7d?: number
    sentiment_volatility_14d?: number
    news_positive_ratio?: number
    news_negative_ratio?: number
  }
  shap_explanations: {
    model_id: number
    model_name: string
    model_type: string
    symbol: string
    prediction_date: string
    prediction: number
    shap_explanations: Array<{
      feature: string
      shap_value: number
      feature_value: number
      impact: 'positive' | 'negative'
    }>
    base_value: number
  }
  analysis_date: string
  data_points: number
}

export default function AnalysisModal({
  isOpen,
  onClose,
  symbol,
  modelId,
  companyName,
  prediction,
  confidence
}: AnalysisModalProps) {
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('shap')

  useEffect(() => {
    if (isOpen && symbol && modelId) {
      loadAnalysisData()
    }
  }, [isOpen, symbol, modelId])

  const loadAnalysisData = async () => {
    setLoading(true)
    try {
      const data = await apiService.getDetailedAnalysis(symbol, modelId)
      setAnalysisData(data)
    } catch (error) {
      console.error('Erreur lors du chargement de l\'analyse:', error)
      toast.error('Erreur lors du chargement de l\'analyse détaillée')
    } finally {
      setLoading(false)
    }
  }

  const formatFeatureName = (feature: string): string => {
    return feature
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase())
  }

  const getImpactColor = (impact: 'positive' | 'negative') => {
    return impact === 'positive' ? 'text-green-600' : 'text-red-600'
  }

  const getImpactIcon = (impact: 'positive' | 'negative') => {
    return impact === 'positive' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" onClick={onClose}></div>
        
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-6xl sm:w-full">
          <div className="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div className="sm:flex sm:items-start">
              <div className="w-full">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg leading-6 font-medium text-gray-900 flex items-center gap-2">
                    <Brain className="w-5 h-5" />
                    Analyse Détaillée - {symbol}
                    {companyName && (
                      <span className="text-sm font-normal text-gray-600">
                        ({companyName})
                      </span>
                    )}
                  </h3>
                  <button
                    onClick={onClose}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <span className="sr-only">Fermer</span>
                    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {loading ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin" />
                    <span className="ml-2">Chargement de l'analyse...</span>
                  </div>
                ) : analysisData ? (
                  <div className="space-y-6">
                    {/* Informations du modèle */}
                    <div className="bg-gray-50 rounded-lg p-4">
                      <h4 className="text-md font-medium text-gray-900 flex items-center gap-2 mb-3">
                        <Target className="w-4 h-4" />
                        Informations du Modèle
                      </h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <p className="text-sm text-gray-600">Modèle</p>
                          <p className="font-medium">{analysisData.model_info.name}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Version</p>
                          <p className="font-medium">{analysisData.model_info.version}</p>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Type</p>
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                            {analysisData.model_info.type}
                          </span>
                        </div>
                        <div>
                          <p className="text-sm text-gray-600">Cible</p>
                          <p className="font-medium">
                            {analysisData.model_info.target_return}% en {analysisData.model_info.time_horizon}j
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Prédiction actuelle */}
                    {prediction !== undefined && confidence !== undefined && (
                      <div className="bg-gray-50 rounded-lg p-4">
                        <h4 className="text-md font-medium text-gray-900 flex items-center gap-2 mb-3">
                          <BarChart3 className="w-4 h-4" />
                          Prédiction Actuelle
                        </h4>
                        <div className="flex items-center gap-4">
                          <div className="text-center">
                            <p className="text-sm text-gray-600">Prédiction</p>
                            <p className={`text-2xl font-bold ${prediction === 1 ? 'text-green-600' : 'text-red-600'}`}>
                              {prediction === 1 ? 'ACHAT' : 'VENTE'}
                            </p>
                          </div>
                          <div className="text-center">
                            <p className="text-sm text-gray-600">Confiance</p>
                            <p className="text-2xl font-bold text-blue-600">
                              {(confidence * 100).toFixed(1)}%
                            </p>
                          </div>
                          <div className="text-center">
                            <p className="text-sm text-gray-600">Date d'analyse</p>
                            <p className="text-sm font-medium">
                              {new Date(analysisData.analysis_date).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Onglets d'analyse */}
                    <div>
                      <div className="border-b border-gray-200">
                        <nav className="-mb-px flex space-x-8">
                          <button
                            onClick={() => setActiveTab('shap')}
                            className={`py-2 px-1 border-b-2 font-medium text-sm ${
                              activeTab === 'shap'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                          >
                            <Brain className="w-4 h-4 inline mr-2" />
                            Explications SHAP
                          </button>
                          <button
                            onClick={() => setActiveTab('technical')}
                            className={`py-2 px-1 border-b-2 font-medium text-sm ${
                              activeTab === 'technical'
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                            }`}
                          >
                            <BarChart3 className="w-4 h-4 inline mr-2" />
                            Graphiques Techniques
                          </button>
                        </nav>
                      </div>

                      {/* Contenu des onglets */}
                      <div className="mt-6">
                        {activeTab === 'shap' && (
                          <div className="bg-gray-50 rounded-lg p-4">
                            <h4 className="text-md font-medium text-gray-900 mb-3">Explications SHAP</h4>
                            <p className="text-sm text-gray-600 mb-4">
                              Comprendre pourquoi le modèle a fait cette prédiction
                            </p>
                            {analysisData.shap_explanations.shap_explanations.length > 0 ? (
                              <div className="space-y-3">
                                {/* Valeur de base */}
                                <div className="p-3 bg-white rounded-lg">
                                  <p className="text-sm text-gray-600">Valeur de base</p>
                                  <p className="text-lg font-semibold">
                                    {analysisData.shap_explanations.base_value.toFixed(4)}
                                  </p>
                                </div>

                                {/* Explications SHAP */}
                                <div className="space-y-2">
                                  {analysisData.shap_explanations.shap_explanations.map((explanation, index) => (
                                    <div
                                      key={index}
                                      className="flex items-center justify-between p-3 bg-white border rounded-lg hover:bg-gray-50"
                                    >
                                      <div className="flex items-center gap-3">
                                        <div className={`${getImpactColor(explanation.impact)}`}>
                                          {getImpactIcon(explanation.impact)}
                                        </div>
                                        <div>
                                          <p className="font-medium">
                                            {formatFeatureName(explanation.feature)}
                                          </p>
                                          <p className="text-sm text-gray-600">
                                            Valeur: {explanation.feature_value.toFixed(4)}
                                          </p>
                                        </div>
                                      </div>
                                      <div className="text-right">
                                        <p className={`font-semibold ${getImpactColor(explanation.impact)}`}>
                                          {explanation.shap_value > 0 ? '+' : ''}{explanation.shap_value.toFixed(4)}
                                        </p>
                                        <p className="text-xs text-gray-500">
                                          {explanation.impact === 'positive' ? 'Favorise' : 'Défavorise'}
                                        </p>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ) : (
                              <p className="text-gray-500 text-center py-8">
                                Aucune explication SHAP disponible
                              </p>
                            )}
                          </div>
                        )}

                        {activeTab === 'technical' && (
                          <div className="space-y-4">
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                              {/* Indicateurs Techniques */}
                              <div className="bg-gray-50 rounded-lg p-4">
                                <h4 className="text-md font-medium text-gray-900 mb-3">Indicateurs Techniques</h4>
                                <div className="space-y-3">
                                  {Object.entries(analysisData.technical_indicators).map(([key, value]) => (
                                    <div key={key} className="flex justify-between items-center">
                                      <span className="text-sm font-medium">
                                        {formatFeatureName(key)}
                                      </span>
                                      <span className="text-sm text-gray-600">
                                        {value !== null && value !== undefined ? value.toFixed(4) : 'N/A'}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>

                              {/* Indicateurs de Sentiment */}
                              <div className="bg-gray-50 rounded-lg p-4">
                                <h4 className="text-md font-medium text-gray-900 mb-3">Indicateurs de Sentiment</h4>
                                <div className="space-y-3">
                                  {Object.entries(analysisData.sentiment_indicators).map(([key, value]) => (
                                    <div key={key} className="flex justify-between items-center">
                                      <span className="text-sm font-medium">
                                        {formatFeatureName(key)}
                                      </span>
                                      <span className="text-sm text-gray-600">
                                        {value !== null && value !== undefined ? value.toFixed(4) : 'N/A'}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </div>

                            {/* Graphique technique */}
                            <div className="bg-gray-50 rounded-lg p-4">
                              <h4 className="text-md font-medium text-gray-900 mb-3">Graphiques Techniques</h4>
                              <p className="text-sm text-gray-600 mb-3">
                                {analysisData.data_points} points de données disponibles
                              </p>
                              <TechnicalChart
                                chartData={analysisData.chart_data}
                                technicalIndicators={analysisData.technical_indicators}
                                symbol={analysisData.symbol}
                                height={400}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex justify-end gap-2 pt-4 border-t">
                      <button
                        onClick={onClose}
                        className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                      >
                        Fermer
                      </button>
                      <button
                        onClick={loadAnalysisData}
                        disabled={loading}
                        className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                      >
                        {loading ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin mr-2 inline" />
                            Actualiser
                          </>
                        ) : (
                          'Actualiser'
                        )}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-gray-500">Erreur lors du chargement des données</p>
                    <button
                      onClick={loadAnalysisData}
                      className="mt-4 px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      Réessayer
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
