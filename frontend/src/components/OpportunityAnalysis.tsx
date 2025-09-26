'use client';

import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  EyeIcon, 
  XMarkIcon,
  ArrowLeftIcon,
  ArrowRightIcon,
  DocumentTextIcon,
  CpuChipIcon,
  ArrowTrendingUpIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';
import TechnicalChart from './TechnicalChart';
import ShapExplanations from './ShapExplanations';
import { apiService } from '@/services/api';

interface Opportunity {
  symbol: string;
  company_name: string;
  prediction: number;
  confidence: number;
  model_id: number;
  model_name: string;
  target_return: number;
  time_horizon: number;
  rank: number;
  prediction_date: string | null;
  screener_run_id: number;
}

interface OpportunityAnalysisProps {
  opportunity: Opportunity;
  isOpen: boolean;
  onClose: () => void;
  onPrevious?: () => void;
  onNext?: () => void;
  hasPrevious?: boolean;
  hasNext?: boolean;
}

export default function OpportunityAnalysis({
  opportunity,
  isOpen,
  onClose,
  onPrevious,
  onNext,
  hasPrevious = false,
  hasNext = false
}: OpportunityAnalysisProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'chart' | 'shap' | 'interpretations'>('overview');
  const [chartData, setChartData] = useState<any>(null);
  const [technicalIndicators, setTechnicalIndicators] = useState<any>(null);
  const [isLoadingChart, setIsLoadingChart] = useState(false);
  const [chartError, setChartError] = useState<string | null>(null);

  // Charger les données du graphique quand l'onglet chart est sélectionné
  useEffect(() => {
    if (activeTab === 'chart' && !chartData && !isLoadingChart) {
      loadChartData();
    }
  }, [activeTab, chartData, isLoadingChart]);

  const loadChartData = async () => {
    setIsLoadingChart(true);
    setChartError(null);
    
    try {
      // Appeler l'API d'analyse détaillée pour récupérer les données du graphique
      const response = await apiService.getDetailedAnalysis(opportunity.symbol, opportunity.model_id);
      
      if (response.chart_data && response.technical_indicators) {
        setChartData(response.chart_data);
        setTechnicalIndicators(response.technical_indicators);
      } else {
        setChartError('Données du graphique non disponibles');
      }
    } catch (error) {
      console.error('Erreur lors du chargement des données du graphique:', error);
      setChartError('Erreur lors du chargement des données');
    } finally {
      setIsLoadingChart(false);
    }
  };

  if (!isOpen) return null;

  const formatModelName = (modelName: string) => {
    if (modelName.includes('xgboost')) return 'XGBoost';
    if (modelName.includes('lightgbm')) return 'LightGBM';
    if (modelName.includes('randomforest')) return 'RandomForest';
    if (modelName.includes('neural')) return 'Neural Network';
    return 'ML Model';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'Élevée';
    if (confidence >= 0.6) return 'Moyenne';
    return 'Faible';
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Récent';
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const tabs = [
    { id: 'overview', name: 'Vue d\'ensemble', icon: InformationCircleIcon },
    { id: 'chart', name: 'Graphique Technique', icon: ChartBarIcon },
    { id: 'shap', name: 'Explications SHAP', icon: CpuChipIcon },
    { id: 'interpretations', name: 'Interprétations', icon: DocumentTextIcon }
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-7xl w-full max-h-[95vh] flex flex-col">
        {/* En-tête */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-lg font-semibold text-blue-600">
                {opportunity.symbol}
              </span>
            </div>
            <div>
              <h3 className="text-xl font-semibold text-gray-900">
                {opportunity.company_name}
              </h3>
              <p className="text-sm text-gray-500">
                {formatModelName(opportunity.model_name)} • {opportunity.target_return}% sur {opportunity.time_horizon} jours
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {/* Navigation entre opportunités */}
            <div className="flex items-center space-x-2">
              <button
                onClick={onPrevious}
                disabled={!hasPrevious}
                className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ArrowLeftIcon className="h-5 w-5" />
              </button>
              <button
                onClick={onNext}
                disabled={!hasNext}
                className="p-2 text-gray-400 hover:text-gray-600 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ArrowRightIcon className="h-5 w-5" />
              </button>
            </div>
            
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>
        </div>

        {/* Onglets */}
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Contenu scrollable */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Métriques principales */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-blue-50 p-6 rounded-lg">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <ChartBarIcon className="h-8 w-8 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-blue-600">Rendement Cible</div>
                      <div className="text-2xl font-bold text-blue-900">{opportunity.target_return}%</div>
                    </div>
                  </div>
                </div>

                <div className="bg-green-50 p-6 rounded-lg">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                        <span className="text-green-600 font-bold">✓</span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-green-600">Confiance</div>
                      <div className="text-2xl font-bold text-green-900">{(opportunity.confidence * 100).toFixed(1)}%</div>
                    </div>
                  </div>
                </div>

                <div className="bg-purple-50 p-6 rounded-lg">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center">
                        <span className="text-purple-600 font-bold">📅</span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-purple-600">Horizon</div>
                      <div className="text-2xl font-bold text-purple-900">{opportunity.time_horizon} jours</div>
                    </div>
                  </div>
                </div>

                <div className="bg-yellow-50 p-6 rounded-lg">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="h-8 w-8 bg-yellow-100 rounded-full flex items-center justify-center">
                        <span className="text-yellow-600 font-bold">#</span>
                      </div>
                    </div>
                    <div className="ml-4">
                      <div className="text-sm font-medium text-yellow-600">Rang</div>
                      <div className="text-2xl font-bold text-yellow-900">#{opportunity.rank}</div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Informations détaillées */}
              <div className="bg-gray-50 p-6 rounded-lg">
                <h4 className="text-lg font-semibold text-gray-900 mb-4">Informations du Modèle</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Type de Modèle</label>
                    <p className="mt-1 text-sm text-gray-900">{formatModelName(opportunity.model_name)}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">ID du Modèle</label>
                    <p className="mt-1 text-sm text-gray-900">{opportunity.model_id}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Date de Prédiction</label>
                    <p className="mt-1 text-sm text-gray-900">{formatDate(opportunity.prediction_date)}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Niveau de Confiance</label>
                    <div className="mt-1">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(opportunity.confidence)}`}>
                        {getConfidenceLabel(opportunity.confidence)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Recommandation */}
              <div className="bg-blue-50 p-6 rounded-lg">
                <h4 className="text-lg font-semibold text-blue-900 mb-4">Recommandation</h4>
                <div className="flex items-start space-x-3">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <span className="text-blue-600 font-bold">💡</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-blue-900">
                      Basé sur l'analyse du modèle {formatModelName(opportunity.model_name)}, 
                      cette opportunité présente un potentiel de rendement de {opportunity.target_return}% 
                      sur {opportunity.time_horizon} jours avec un niveau de confiance de {(opportunity.confidence * 100).toFixed(1)}%.
                    </p>
                    <p className="text-blue-700 mt-2 text-sm">
                      Consultez les onglets "Graphique Technique" et "Explications SHAP" pour une analyse plus approfondie.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'chart' && (
            <div className="h-96">
              {isLoadingChart ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Chargement des données du graphique...</p>
                  </div>
                </div>
              ) : chartError ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="text-red-600 mb-2">Erreur</div>
                    <p className="text-gray-600">{chartError}</p>
                    <button
                      onClick={loadChartData}
                      className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                    >
                      Réessayer
                    </button>
                  </div>
                </div>
              ) : chartData && technicalIndicators ? (
                <TechnicalChart 
                  chartData={chartData}
                  technicalIndicators={technicalIndicators}
                  symbol={opportunity.symbol}
                  height={384}
                />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="text-gray-600 mb-2">Aucune donnée disponible</div>
                    <p className="text-sm text-gray-500">Les données du graphique ne sont pas disponibles pour cette opportunité.</p>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'shap' && (
            <div>
              <ShapExplanations
                modelId={opportunity.model_id}
                symbol={opportunity.symbol}
                predictionDate={opportunity.prediction_date || new Date().toISOString().split('T')[0]}
              />
            </div>
          )}

          {activeTab === 'interpretations' && (
            <div className="p-6 space-y-6">
              {/* Informations du modèle */}
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Informations du Modèle</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="font-medium text-gray-700">Type de modèle:</span>
                    <p className="text-gray-900">{formatModelName(opportunity.model_name)}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Symbole:</span>
                    <p className="text-gray-900">{opportunity.symbol}</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Rendement cible:</span>
                    <p className="text-gray-900">{opportunity.target_return}%</p>
                  </div>
                  <div>
                    <span className="font-medium text-gray-700">Horizon temporel:</span>
                    <p className="text-gray-900">{opportunity.time_horizon} jours</p>
                  </div>
                </div>
              </div>

              {/* Métriques de performance */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-blue-900 mb-4">Métriques de Performance</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-900">{(opportunity.confidence * 100).toFixed(1)}%</div>
                    <div className="text-sm text-blue-700">Confiance</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{opportunity.target_return}%</div>
                    <div className="text-sm text-green-700">Rendement Cible</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">{opportunity.time_horizon}</div>
                    <div className="text-sm text-purple-700">Jours</div>
                  </div>
                </div>
              </div>

              {/* Analyse de la prédiction */}
              <div className="bg-green-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-green-900 mb-4">Analyse de la Prédiction</h3>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-green-700">Prédiction:</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      opportunity.prediction === 1 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {opportunity.prediction === 1 ? 'Opportunité Positive' : 'Opportunité Négative'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-green-700">Niveau de confiance:</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      opportunity.confidence > 0.8 
                        ? 'bg-green-100 text-green-800' 
                        : opportunity.confidence > 0.6 
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {opportunity.confidence > 0.8 ? 'Élevé' : opportunity.confidence > 0.6 ? 'Modéré' : 'Faible'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-green-700">Potentiel de rendement:</span>
                    <span className="text-green-900 font-semibold">{opportunity.target_return}%</span>
                  </div>
                </div>
              </div>

              {/* Recommandations */}
              <div className="bg-yellow-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-yellow-900 mb-4">Recommandations</h3>
                <div className="space-y-2 text-sm">
                  {opportunity.confidence > 0.8 ? (
                    <>
                      <div className="flex items-start space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-yellow-800">Confiance élevée - Cette opportunité présente un fort potentiel de réussite.</p>
                      </div>
                      <div className="flex items-start space-x-2">
                        <div className="w-2 h-2 bg-green-500 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-yellow-800">Considérez cette opportunité comme prioritaire dans votre portefeuille.</p>
                      </div>
                    </>
                  ) : opportunity.confidence > 0.6 ? (
                    <>
                      <div className="flex items-start space-x-2">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-yellow-800">Confiance modérée - Surveillez cette opportunité de près.</p>
                      </div>
                      <div className="flex items-start space-x-2">
                        <div className="w-2 h-2 bg-yellow-500 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-yellow-800">Considérez une position plus petite ou un suivi renforcé.</p>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex items-start space-x-2">
                        <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-yellow-800">Confiance faible - Approche prudente recommandée.</p>
                      </div>
                      <div className="flex items-start space-x-2">
                        <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                        <p className="text-yellow-800">Attendez des signaux plus forts avant d'investir.</p>
                      </div>
                    </>
                  )}
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-yellow-800">Horizon de {opportunity.time_horizon} jours - Planifiez votre sortie en conséquence.</p>
                  </div>
                </div>
              </div>

              {/* Facteurs de risque */}
              <div className="bg-red-50 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-red-900 mb-4">Facteurs de Risque</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-red-800">Les prédictions passées ne garantissent pas les résultats futurs.</p>
                  </div>
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-red-800">Les conditions de marché peuvent évoluer rapidement.</p>
                  </div>
                  <div className="flex items-start space-x-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full mt-2 flex-shrink-0"></div>
                    <p className="text-red-800">Diversifiez votre portefeuille pour réduire les risques.</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
