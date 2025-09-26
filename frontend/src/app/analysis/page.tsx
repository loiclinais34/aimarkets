'use client';

import React, { useState, useEffect } from 'react';
import RootLayout from '@/components/RootLayout';
import OpportunityAnalysis from '@/components/OpportunityAnalysis';
import { 
  ChartBarIcon, 
  ShoppingCartIcon, 
  TrashIcon,
  ArrowLeftIcon,
  EyeIcon,
  DocumentTextIcon
} from '@heroicons/react/24/outline';

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

export default function AnalysisPage() {
  const [cart, setCart] = useState<Opportunity[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedOpportunity, setSelectedOpportunity] = useState<Opportunity | null>(null);
  const [analysisOpen, setAnalysisOpen] = useState(false);

  // Charger le panier depuis localStorage
  useEffect(() => {
    const savedCart = localStorage.getItem('opportunity-cart');
    if (savedCart) {
      try {
        setCart(JSON.parse(savedCart));
      } catch (error) {
        console.error('Erreur lors du chargement du panier:', error);
      }
    }
    setIsLoading(false);
  }, []);

  const removeFromCart = (opportunity: Opportunity) => {
    const newCart = cart.filter(item => 
      !(item.symbol === opportunity.symbol && item.model_id === opportunity.model_id)
    );
    setCart(newCart);
    localStorage.setItem('opportunity-cart', JSON.stringify(newCart));
  };

  const clearCart = () => {
    setCart([]);
    localStorage.setItem('opportunity-cart', JSON.stringify([]));
  };

  const handleAnalyzeOpportunity = (opportunity: Opportunity) => {
    setSelectedOpportunity(opportunity);
    setAnalysisOpen(true);
  };

  const handleCloseAnalysis = () => {
    setAnalysisOpen(false);
    setSelectedOpportunity(null);
  };

  const getCurrentIndex = () => {
    if (!selectedOpportunity) return -1;
    return cart.findIndex(opp => 
      opp.symbol === selectedOpportunity.symbol && 
      opp.model_id === selectedOpportunity.model_id
    );
  };

  const handlePrevious = () => {
    const currentIndex = getCurrentIndex();
    if (currentIndex > 0) {
      setSelectedOpportunity(cart[currentIndex - 1]);
    }
  };

  const handleNext = () => {
    const currentIndex = getCurrentIndex();
    if (currentIndex < cart.length - 1) {
      setSelectedOpportunity(cart[currentIndex + 1]);
    }
  };

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

  const totalValue = cart.reduce((sum, item) => sum + item.target_return, 0);
  const averageConfidence = cart.length > 0 
    ? cart.reduce((sum, item) => sum + item.confidence, 0) / cart.length 
    : 0;
  const uniqueSymbols = new Set(cart.map(item => item.symbol)).size;

  if (isLoading) {
    return (
      <RootLayout>
        <div className="min-h-screen bg-gray-100 p-8">
          <div className="max-w-7xl mx-auto">
            <div className="animate-pulse">
              <div className="h-8 bg-gray-200 rounded w-1/4 mb-8"></div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {[...Array(3)].map((_, i) => (
                  <div key={i} className="h-24 bg-gray-200 rounded-lg"></div>
                ))}
              </div>
              <div className="space-y-4">
                {[...Array(5)].map((_, i) => (
                  <div key={i} className="h-20 bg-gray-200 rounded-lg"></div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </RootLayout>
    );
  }

  if (cart.length === 0) {
    return (
      <RootLayout>
        <div className="min-h-screen bg-gray-100 p-8">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-center mb-8">
              <button
                onClick={() => window.history.back()}
                className="mr-4 p-2 text-gray-600 hover:text-gray-900"
              >
                <ArrowLeftIcon className="h-6 w-6" />
              </button>
              <h1 className="text-3xl font-bold text-gray-900">Analyse des Opportunités</h1>
            </div>

            <div className="text-center py-12">
              <ShoppingCartIcon className="h-24 w-24 text-gray-300 mx-auto mb-6" />
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Panier vide</h2>
              <p className="text-gray-600 mb-8 max-w-md mx-auto">
                Votre panier d'opportunités est vide. Retournez au dashboard pour sélectionner des opportunités à analyser.
              </p>
              <button
                onClick={() => window.location.href = '/dashboard'}
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <ArrowLeftIcon className="h-5 w-5 mr-2" />
                Retour au Dashboard
              </button>
            </div>
          </div>
        </div>
      </RootLayout>
    );
  }

  return (
    <RootLayout>
      <div className="min-h-screen bg-gray-100 p-8">
        <div className="max-w-7xl mx-auto">
          {/* En-tête */}
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center">
              <button
                onClick={() => window.history.back()}
                className="mr-4 p-2 text-gray-600 hover:text-gray-900"
              >
                <ArrowLeftIcon className="h-6 w-6" />
              </button>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Analyse des Opportunités</h1>
                <p className="mt-2 text-gray-600">
                  Analyse détaillée de {cart.length} opportunité{cart.length > 1 ? 's' : ''} sélectionnée{cart.length > 1 ? 's' : ''}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={clearCart}
                className="text-sm text-red-600 hover:text-red-800"
              >
                Vider le panier
              </button>
              <button
                onClick={() => window.location.href = '/dashboard'}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <ArrowLeftIcon className="h-4 w-4 mr-2" />
                Retour au Dashboard
              </button>
            </div>
          </div>

          {/* Statistiques globales */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <ChartBarIcon className="h-8 w-8 text-blue-600" />
                </div>
                <div className="ml-4">
                  <div className="text-sm font-medium text-gray-500">Opportunités</div>
                  <div className="text-2xl font-bold text-gray-900">{cart.length}</div>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 bg-green-100 rounded-full flex items-center justify-center">
                    <span className="text-green-600 font-bold">%</span>
                  </div>
                </div>
                <div className="ml-4">
                  <div className="text-sm font-medium text-gray-500">Rendement Total</div>
                  <div className="text-2xl font-bold text-gray-900">{totalValue.toFixed(1)}%</div>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 bg-yellow-100 rounded-full flex items-center justify-center">
                    <span className="text-yellow-600 font-bold">✓</span>
                  </div>
                </div>
                <div className="ml-4">
                  <div className="text-sm font-medium text-gray-500">Confiance Moyenne</div>
                  <div className="text-2xl font-bold text-gray-900">{(averageConfidence * 100).toFixed(1)}%</div>
                </div>
              </div>
            </div>

            <div className="bg-white p-6 rounded-lg shadow">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center">
                    <span className="text-purple-600 font-bold">🏢</span>
                  </div>
                </div>
                <div className="ml-4">
                  <div className="text-sm font-medium text-gray-500">Symboles Uniques</div>
                  <div className="text-2xl font-bold text-gray-900">{uniqueSymbols}</div>
                </div>
              </div>
            </div>
          </div>

          {/* Analyse par symbole */}
          <div className="bg-white rounded-lg shadow mb-8">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Analyse par Symbole</h2>
            </div>
            <div className="p-6">
              <div className="space-y-6">
                {Array.from(new Set(cart.map(item => item.symbol))).map(symbol => {
                  const symbolOpportunities = cart.filter(item => item.symbol === symbol);
                  const bestOpportunity = symbolOpportunities.reduce((best, current) => 
                    current.confidence > best.confidence ? current : best
                  );
                  const totalReturn = symbolOpportunities.reduce((sum, item) => sum + item.target_return, 0);
                  const avgConfidence = symbolOpportunities.reduce((sum, item) => sum + item.confidence, 0) / symbolOpportunities.length;

                  return (
                    <div key={symbol} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-4">
                        <div className="flex items-center space-x-3">
                          <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                            <span className="text-sm font-semibold text-blue-600">{symbol}</span>
                          </div>
                          <div>
                            <h3 className="text-lg font-semibold text-gray-900">
                              {bestOpportunity.company_name}
                            </h3>
                            <p className="text-sm text-gray-500">
                              {symbolOpportunities.length} opportunité{symbolOpportunities.length > 1 ? 's' : ''}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-semibold text-gray-900">
                            {totalReturn.toFixed(1)}%
                          </div>
                          <div className="text-sm text-gray-500">Rendement total</div>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-blue-600">{totalReturn.toFixed(1)}%</div>
                          <div className="text-sm text-gray-500">Rendement Total</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-green-600">{(avgConfidence * 100).toFixed(1)}%</div>
                          <div className="text-sm text-gray-500">Confiance Moyenne</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-purple-600">{symbolOpportunities.length}</div>
                          <div className="text-sm text-gray-500">Modèles</div>
                        </div>
                      </div>

                      <div className="space-y-2">
                        {symbolOpportunities.map((opportunity, index) => (
                          <div key={`${opportunity.model_id}-${index}`} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div className="flex items-center space-x-3">
                              <div className="text-sm font-medium text-gray-900">
                                {formatModelName(opportunity.model_name)}
                              </div>
                              <div className="text-xs text-gray-500">
                                {opportunity.target_return}% sur {opportunity.time_horizon} jours
                                {opportunity.prediction_date && (
                                  <span className="ml-2">• {formatDate(opportunity.prediction_date)}</span>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center space-x-3">
                              <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(opportunity.confidence)}`}>
                                {getConfidenceLabel(opportunity.confidence)}
                              </div>
                              <div className="text-sm font-semibold text-gray-900">
                                {(opportunity.confidence * 100).toFixed(1)}%
                              </div>
                              <div className="flex items-center space-x-2">
                                <button
                                  onClick={() => handleAnalyzeOpportunity(opportunity)}
                                  className="p-2 text-blue-400 hover:text-blue-600"
                                  title="Analyser cette opportunité"
                                >
                                  <EyeIcon className="h-4 w-4" />
                                </button>
                                <button
                                  onClick={() => removeFromCart(opportunity)}
                                  className="p-2 text-red-400 hover:text-red-600"
                                  title="Supprimer du panier"
                                >
                                  <TrashIcon className="h-4 w-4" />
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Actions</h3>
                <p className="text-sm text-gray-500">
                  Exportez vos analyses ou retournez au dashboard
                </p>
              </div>
              <div className="flex items-center space-x-4">
                <button
                  onClick={() => {
                    // TODO: Implémenter l'export
                    alert('Fonctionnalité d\'export à venir');
                  }}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <DocumentTextIcon className="h-4 w-4 mr-2" />
                  Exporter
                </button>
                <button
                  onClick={() => window.location.href = '/dashboard'}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <ArrowLeftIcon className="h-4 w-4 mr-2" />
                  Retour au Dashboard
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Modal d'analyse détaillée */}
      {selectedOpportunity && (
        <OpportunityAnalysis
          opportunity={selectedOpportunity}
          isOpen={analysisOpen}
          onClose={handleCloseAnalysis}
          onPrevious={handlePrevious}
          onNext={handleNext}
          hasPrevious={getCurrentIndex() > 0}
          hasNext={getCurrentIndex() < cart.length - 1}
        />
      )}
    </RootLayout>
  );
}
