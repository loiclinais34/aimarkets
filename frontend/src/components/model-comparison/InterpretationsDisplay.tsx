"use client";

import React, { useState } from 'react';
import { 
  CheckCircleIcon, 
  ExclamationTriangleIcon, 
  XCircleIcon,
  InformationCircleIcon,
  ChartBarIcon,
  ShieldExclamationIcon
} from '@heroicons/react/24/outline';

interface MetricInterpretation {
  value: number;
  grade: string;
  interpretation: string;
  recommendation: string;
  risk_level: string;
  color: string;
}

interface ModelAnalysis {
  model_name: string;
  overall_grade: string;
  risk_level: string;
  is_tradable: boolean;
  confidence_score: number;
  key_strengths: string[];
  key_weaknesses: string[];
  recommendations: string[];
  warnings: string[];
  metrics_analysis: Record<string, MetricInterpretation>;
}

interface GlobalRecommendations {
  trading_recommendation: string;
  risk_level: string;
  confidence: number;
  action_items: string[];
  warnings: string[];
  next_steps: string[];
}

interface Summary {
  total_models: number;
  tradable_models: number;
  critical_models: number;
  average_confidence: number;
  best_model: string;
  overall_assessment: string;
}

interface InterpretationsDisplayProps {
  modelAnalyses: Record<string, { analysis: ModelAnalysis }>;
  globalRecommendations: GlobalRecommendations;
  summary: Summary;
  bestModel: string;
}

const InterpretationsDisplay: React.FC<InterpretationsDisplayProps> = ({
  modelAnalyses,
  globalRecommendations,
  summary,
  bestModel
}) => {
  const [selectedModel, setSelectedModel] = useState<string>(bestModel || Object.keys(modelAnalyses)[0]);
  const [activeTab, setActiveTab] = useState<'overview' | 'details' | 'recommendations'>('overview');

  const getGradeColor = (grade: string) => {
    switch (grade) {
      case 'A+': return 'text-green-600 bg-green-50';
      case 'A': return 'text-green-500 bg-green-50';
      case 'B': return 'text-yellow-500 bg-yellow-50';
      case 'C': return 'text-orange-500 bg-orange-50';
      case 'D': return 'text-red-500 bg-red-50';
      case 'F': return 'text-red-600 bg-red-50';
      default: return 'text-gray-500 bg-gray-50';
    }
  };

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'very_low': return 'text-green-600 bg-green-50';
      case 'low': return 'text-green-500 bg-green-50';
      case 'medium': return 'text-yellow-500 bg-yellow-50';
      case 'high': return 'text-orange-500 bg-orange-50';
      case 'very_high': return 'text-red-500 bg-red-50';
      case 'critical': return 'text-red-600 bg-red-50';
      default: return 'text-gray-500 bg-gray-50';
    }
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'STRONG_BUY': return 'text-green-600 bg-green-50';
      case 'BUY': return 'text-green-500 bg-green-50';
      case 'HOLD': return 'text-yellow-500 bg-yellow-50';
      case 'AVOID': return 'text-red-500 bg-red-50';
      default: return 'text-gray-500 bg-gray-50';
    }
  };

  const getRecommendationIcon = (recommendation: string) => {
    switch (recommendation) {
      case 'STRONG_BUY':
      case 'BUY':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'HOLD':
        return <InformationCircleIcon className="h-5 w-5 text-yellow-500" />;
      case 'AVOID':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      default:
        return <InformationCircleIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const selectedAnalysis = modelAnalyses[selectedModel]?.analysis;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header avec recommandation globale */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-2xl font-bold text-gray-900">
            Analyse Intelligente des Modèles
          </h2>
          <div className={`px-4 py-2 rounded-lg ${getRecommendationColor(globalRecommendations.trading_recommendation)}`}>
            <div className="flex items-center space-x-2">
              {getRecommendationIcon(globalRecommendations.trading_recommendation)}
              <span className="font-semibold">
                {globalRecommendations.trading_recommendation}
              </span>
            </div>
          </div>
        </div>

        {/* Résumé global */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-blue-600">Modèles Analysés</div>
            <div className="text-2xl font-bold text-blue-900">{summary.total_models}</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-green-600">Modèles Tradables</div>
            <div className="text-2xl font-bold text-green-900">{summary.tradable_models}</div>
          </div>
          <div className="bg-red-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-red-600">Modèles Critiques</div>
            <div className="text-2xl font-bold text-red-900">{summary.critical_models}</div>
          </div>
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-purple-600">Confiance Moyenne</div>
            <div className="text-2xl font-bold text-purple-900">
              {(summary.average_confidence * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Alertes critiques */}
        {globalRecommendations.warnings.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <div className="flex items-start">
              <ShieldExclamationIcon className="h-5 w-5 text-red-500 mt-0.5 mr-3" />
              <div>
                <h3 className="text-sm font-medium text-red-800">Alertes Critiques</h3>
                <ul className="mt-2 text-sm text-red-700">
                  {globalRecommendations.warnings.map((warning, index) => (
                    <li key={index} className="mb-1">• {warning}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Navigation par onglets */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'overview'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Vue d'ensemble
          </button>
          <button
            onClick={() => setActiveTab('details')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'details'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Détails par Modèle
          </button>
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'recommendations'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Recommandations
          </button>
        </nav>
      </div>

      {/* Contenu des onglets */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Actions recommandées */}
          <div className="bg-blue-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-4">
              Actions Recommandées
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-medium text-blue-800 mb-2">Actions Immédiates</h4>
                <ul className="space-y-1">
                  {globalRecommendations.action_items.map((item, index) => (
                    <li key={index} className="text-blue-700 text-sm flex items-start">
                      <span className="mr-2">•</span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="font-medium text-blue-800 mb-2">Prochaines Étapes</h4>
                <ul className="space-y-1">
                  {globalRecommendations.next_steps.map((step, index) => (
                    <li key={index} className="text-blue-700 text-sm flex items-start">
                      <span className="mr-2">•</span>
                      {step}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Comparaison des modèles */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Comparaison des Modèles
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(modelAnalyses).map(([modelName, data]) => {
                const analysis = data.analysis;
                return (
                  <div
                    key={modelName}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      selectedModel === modelName
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedModel(modelName)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-gray-900">{modelName}</h4>
                      <div className={`px-2 py-1 rounded text-xs font-medium ${getGradeColor(analysis.overall_grade)}`}>
                        {analysis.overall_grade}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Confiance:</span>
                        <span className="font-medium">{(analysis.confidence_score * 100).toFixed(1)}%</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Risque:</span>
                        <span className={`px-2 py-1 rounded text-xs ${getRiskColor(analysis.risk_level)}`}>
                          {analysis.risk_level}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Tradable:</span>
                        <span className={analysis.is_tradable ? 'text-green-600' : 'text-red-600'}>
                          {analysis.is_tradable ? 'Oui' : 'Non'}
                        </span>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'details' && selectedAnalysis && (
        <div className="space-y-6">
          {/* Informations générales du modèle sélectionné */}
          <div className="bg-gray-50 rounded-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900">{selectedModel}</h3>
              <div className="flex space-x-2">
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${getGradeColor(selectedAnalysis.overall_grade)}`}>
                  Note: {selectedAnalysis.overall_grade}
                </div>
                <div className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(selectedAnalysis.risk_level)}`}>
                  Risque: {selectedAnalysis.risk_level}
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold text-gray-800 mb-2">Forces</h4>
                <ul className="space-y-1">
                  {selectedAnalysis.key_strengths.map((strength, index) => (
                    <li key={index} className="text-green-700 text-sm flex items-start">
                      <CheckCircleIcon className="h-4 w-4 text-green-500 mt-0.5 mr-2" />
                      {strength}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="font-semibold text-gray-800 mb-2">Faiblesses</h4>
                <ul className="space-y-1">
                  {selectedAnalysis.key_weaknesses.map((weakness, index) => (
                    <li key={index} className="text-red-700 text-sm flex items-start">
                      <XCircleIcon className="h-4 w-4 text-red-500 mt-0.5 mr-2" />
                      {weakness}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          {/* Analyse détaillée des métriques */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Analyse Détaillée des Métriques
            </h3>
            <div className="space-y-4">
              {Object.entries(selectedAnalysis.metrics_analysis).map(([metricName, interpretation]) => (
                <div key={metricName} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-800 capitalize">
                      {metricName.replace('_', ' ')}
                    </h4>
                    <div className="flex items-center space-x-2">
                      <div className={`px-2 py-1 rounded text-xs font-medium ${getGradeColor(interpretation.grade)}`}>
                        {interpretation.grade}
                      </div>
                      <span className="text-lg font-bold text-gray-900">
                        {typeof interpretation.value === 'number' 
                          ? interpretation.value.toFixed(3)
                          : interpretation.value
                        }
                      </span>
                    </div>
                  </div>
                  <p className="text-gray-700 text-sm mb-2">{interpretation.interpretation}</p>
                  <div className={`p-3 rounded ${interpretation.color.includes('red') ? 'bg-red-50' : 
                    interpretation.color.includes('green') ? 'bg-green-50' : 
                    interpretation.color.includes('yellow') ? 'bg-yellow-50' : 'bg-gray-50'}`}>
                    <p className="text-sm font-medium">{interpretation.recommendation}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'recommendations' && selectedAnalysis && (
        <div className="space-y-6">
          {/* Recommandations spécifiques au modèle */}
          <div className="bg-blue-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-blue-900 mb-4">
              Recommandations pour {selectedModel}
            </h3>
            <div className="space-y-3">
              {selectedAnalysis.recommendations.map((recommendation, index) => (
                <div key={index} className="flex items-start">
                  <InformationCircleIcon className="h-5 w-5 text-blue-500 mt-0.5 mr-3" />
                  <p className="text-blue-800 text-sm">{recommendation}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Avertissements */}
          {selectedAnalysis.warnings.length > 0 && (
            <div className="bg-red-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-red-900 mb-4">
                Avertissements pour {selectedModel}
              </h3>
              <div className="space-y-3">
                {selectedAnalysis.warnings.map((warning, index) => (
                  <div key={index} className="flex items-start">
                    <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mt-0.5 mr-3" />
                    <p className="text-red-800 text-sm">{warning}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Score de confiance */}
          <div className="bg-purple-50 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-purple-900 mb-4">
              Score de Confiance
            </h3>
            <div className="flex items-center space-x-4">
              <div className="flex-1">
                <div className="bg-white rounded-full h-4 overflow-hidden">
                  <div 
                    className="bg-purple-500 h-full transition-all duration-500"
                    style={{ width: `${selectedAnalysis.confidence_score * 100}%` }}
                  />
                </div>
              </div>
              <span className="text-2xl font-bold text-purple-900">
                {(selectedAnalysis.confidence_score * 100).toFixed(1)}%
              </span>
            </div>
            <p className="text-purple-700 text-sm mt-2">
              Ce score reflète la confiance globale dans ce modèle basée sur toutes ses métriques.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default InterpretationsDisplay;
