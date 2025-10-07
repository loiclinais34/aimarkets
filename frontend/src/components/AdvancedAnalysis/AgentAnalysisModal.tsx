'use client';

import React, { useState } from 'react';
import { X, TrendingUp, TrendingDown, BarChart3, Lightbulb, Target, Calendar, DollarSign, Newspaper, Brain } from 'lucide-react';
import { agentAnalysisApi, AgentAnalysisResponse } from '@/services/agentAnalysisApi';

interface AgentAnalysisModalProps {
  isOpen: boolean;
  onClose: () => void;
  symbol: string;
}

export const AgentAnalysisModal: React.FC<AgentAnalysisModalProps> = ({
  isOpen,
  onClose,
  symbol,
}) => {
  const [analysis, setAnalysis] = useState<AgentAnalysisResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const generateAnalysis = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const result = await agentAnalysisApi.generateAnalysis({
        symbol,
        days_back: 7
      });
      setAnalysis(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la génération de l\'analyse');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b sticky top-0 bg-white z-10">
          <div className="flex items-center space-x-3">
            <Brain className="w-6 h-6 text-blue-600" />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Analyse Agent - {symbol}
              </h2>
              <p className="text-sm text-gray-500">
                Analyse complète basée sur les données de sentiment et de cours
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {!analysis && !isLoading && !error && (
            <div className="text-center py-12">
              <Brain className="w-16 h-16 text-blue-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Générer l'analyse agent pour {symbol}
              </h3>
              <p className="text-gray-600 mb-6">
                Cette analyse combine les données de sentiment, les cours historiques et les actualités
                pour vous fournir des insights détaillés sur le titre.
              </p>
              <button
                onClick={generateAnalysis}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 mx-auto"
              >
                <Brain className="w-5 h-5" />
                <span>Générer l'analyse</span>
              </button>
            </div>
          )}

          {isLoading && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Génération de l'analyse en cours...</p>
            </div>
          )}

          {error && (
            <div className="text-center py-12">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <p className="text-red-600">{error}</p>
              </div>
              <button
                onClick={generateAnalysis}
                className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Réessayer
              </button>
            </div>
          )}

          {analysis && (
            <div className="space-y-6">
              {/* Résumé exécutif */}
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <BarChart3 className="w-5 h-5 mr-2" />
                  Résumé Exécutif
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <DollarSign className="w-8 h-8 text-green-600 mx-auto mb-2" />
                    <p className="text-sm text-gray-600">Prix Actuel</p>
                    <p className="text-lg font-semibold">${analysis.summary.current_price.toFixed(2)}</p>
                  </div>
                  <div className="text-center">
                    {analysis.summary.price_change_pct >= 0 ? (
                      <TrendingUp className="w-8 h-8 text-green-600 mx-auto mb-2" />
                    ) : (
                      <TrendingDown className="w-8 h-8 text-red-600 mx-auto mb-2" />
                    )}
                    <p className="text-sm text-gray-600">Variation</p>
                    <p className={`text-lg font-semibold ${analysis.summary.price_change_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {analysis.summary.price_change_pct >= 0 ? '+' : ''}{analysis.summary.price_change_pct.toFixed(2)}%
                    </p>
                  </div>
                  <div className="text-center">
                    <Newspaper className="w-8 h-8 text-blue-600 mx-auto mb-2" />
                    <p className="text-sm text-gray-600">News Analysées</p>
                    <p className="text-lg font-semibold">{analysis.summary.total_news_analyzed}</p>
                  </div>
                  <div className="text-center">
                    <Calendar className="w-8 h-8 text-purple-600 mx-auto mb-2" />
                    <p className="text-sm text-gray-600">Période</p>
                    <p className="text-lg font-semibold">{analysis.summary.analysis_period}</p>
                  </div>
                </div>
              </div>

              {/* Insights clés */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Lightbulb className="w-5 h-5 mr-2" />
                  Insights Clés
                </h3>
                <div className="space-y-3">
                  {analysis.key_insights.map((insight, index) => (
                    <div key={index} className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-blue-600 rounded-full mt-2 flex-shrink-0"></div>
                      <p className="text-gray-700">{insight}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recommandations */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <Target className="w-5 h-5 mr-2" />
                  Recommandations
                </h3>
                <div className="space-y-3">
                  {analysis.recommendations.map((recommendation, index) => (
                    <div key={index} className="flex items-start space-x-3">
                      <div className="w-2 h-2 bg-green-600 rounded-full mt-2 flex-shrink-0"></div>
                      <p className="text-gray-700">{recommendation}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Évolution du sentiment */}
              {analysis.sentiment_evolution.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Évolution du Sentiment
                  </h3>
                  <div className="space-y-4">
                    {analysis.sentiment_evolution.map((sentiment, index) => (
                      <div key={index} className="border-l-4 border-blue-200 pl-4">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-gray-900">{sentiment.date}</span>
                          <div className="flex items-center space-x-4">
                            <span className={`px-2 py-1 rounded text-sm ${
                              sentiment.sentiment_score > 0.3 ? 'bg-green-100 text-green-800' :
                              sentiment.sentiment_score < -0.3 ? 'bg-red-100 text-red-800' :
                              'bg-gray-100 text-gray-800'
                            }`}>
                              Score: {sentiment.sentiment_score.toFixed(3)}
                            </span>
                            <span className="text-sm text-gray-600">
                              {sentiment.news_count} news
                            </span>
                          </div>
                        </div>
                        {sentiment.top_news_title && (
                          <p className="text-sm text-gray-600 mb-1">
                            <strong>News principale:</strong> {sentiment.top_news_title}
                          </p>
                        )}
                        {sentiment.analysis && (
                          <p className="text-sm text-gray-700">
                            <strong>Analyse:</strong> {sentiment.analysis}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Évolution des cours */}
              {analysis.price_evolution.length > 0 && (
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">
                    Évolution des Cours
                  </h3>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Date
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Ouverture
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Clôture
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Plus Haut
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Plus Bas
                          </th>
                          <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                            Volume
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {analysis.price_evolution.map((price, index) => (
                          <tr key={index}>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                              {price.date}
                            </td>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                              ${price.open.toFixed(2)}
                            </td>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                              ${price.close.toFixed(2)}
                            </td>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                              ${price.high.toFixed(2)}
                            </td>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                              ${price.low.toFixed(2)}
                            </td>
                            <td className="px-4 py-2 whitespace-nowrap text-sm text-gray-900">
                              {price.volume.toLocaleString()}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Analyse de corrélation */}
              <div className="bg-white border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Analyse de Corrélation
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600">Tendance Sentiment</p>
                    <p className={`text-lg font-semibold ${
                      analysis.correlation_analysis.sentiment_trend === 'positif' ? 'text-green-600' :
                      analysis.correlation_analysis.sentiment_trend === 'négatif' ? 'text-red-600' :
                      'text-gray-600'
                    }`}>
                      {analysis.correlation_analysis.sentiment_trend}
                    </p>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600">Impact News</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {analysis.correlation_analysis.news_impact}
                    </p>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600">Sentiment Moyen</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {analysis.correlation_analysis.average_sentiment.toFixed(3)}
                    </p>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600">Total News</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {analysis.correlation_analysis.total_news}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
