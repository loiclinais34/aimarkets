/**
 * Page d'analyse des performances - Analyse détaillée des opportunités XGBoost
 */

'use client';

import React from 'react';
import { useRequireAuth } from '@/contexts/AuthContext';
import AppLayout from '@/components/Layout/AppLayout';
import XGBoostPerformanceKPIs from '@/components/XGBoostPerformanceKPIs';

export default function PerformanceAnalysisPage() {
  const { isAuthenticated, isLoading } = useRequireAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <svg className="animate-spin mx-auto h-12 w-12 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="mt-4 text-lg text-gray-600">Chargement de l'analyse des performances...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null; // Redirection en cours
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* En-tête de la page */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-700 text-white rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold mb-2">📊 Analyse des Performances</h1>
              <p className="text-blue-100 text-lg">
                Analyse détaillée des opportunités XGBoost et de leurs performances
              </p>
            </div>
            <div className="hidden md:block">
              <div className="bg-white bg-opacity-20 rounded-lg p-4">
                <div className="text-center">
                  <div className="text-2xl font-bold">🚀</div>
                  <div className="text-sm text-blue-100">Modèles ML</div>
                  <div className="text-sm text-blue-100">Optimisés</div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Informations sur les modèles */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">🔬 Informations sur les Modèles</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">18</div>
              <div className="text-sm text-gray-600">Indicateurs Techniques</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">154K+</div>
              <div className="text-sm text-gray-600">Opportunités Analysées</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">101</div>
              <div className="text-sm text-gray-600">Symboles Couverts</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">3</div>
              <div className="text-sm text-gray-600">Horizons Temporels</div>
            </div>
          </div>
        </div>

        {/* Composant principal des KPIs */}
        <XGBoostPerformanceKPIs />

        {/* Section d'actions rapides */}
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">⚡ Actions Rapides</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left">
              <div className="flex items-center">
                <div className="text-2xl mr-3">📈</div>
                <div>
                  <div className="font-medium text-gray-900">Exporter les Données</div>
                  <div className="text-sm text-gray-500">Télécharger les performances en CSV</div>
                </div>
              </div>
            </button>
            <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left">
              <div className="flex items-center">
                <div className="text-2xl mr-3">🔄</div>
                <div>
                  <div className="font-medium text-gray-900">Actualiser</div>
                  <div className="text-sm text-gray-500">Recharger les dernières données</div>
                </div>
              </div>
            </button>
            <button className="p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left">
              <div className="flex items-center">
                <div className="text-2xl mr-3">⚙️</div>
                <div>
                  <div className="font-medium text-gray-900">Paramètres</div>
                  <div className="text-sm text-gray-500">Configurer l'affichage</div>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
