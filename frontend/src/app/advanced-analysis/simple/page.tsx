// frontend/src/app/advanced-analysis/simple/page.tsx
'use client';

import React, { useState } from 'react';
import { 
  MagnifyingGlassIcon, 
  ChartBarIcon, 
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  Cog6ToothIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

const SimpleAdvancedAnalysisPage: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [activeTab, setActiveTab] = useState<'overview' | 'technical' | 'sentiment' | 'market' | 'hybrid'>('overview');

  const tabs = [
    { id: 'overview', name: 'Vue d\'ensemble', icon: ChartBarIcon },
    { id: 'technical', name: 'Technique', icon: ArrowTrendingUpIcon },
    { id: 'sentiment', name: 'Sentiment', icon: ExclamationTriangleIcon },
    { id: 'market', name: 'Marché', icon: ChartBarIcon },
    { id: 'hybrid', name: 'Hybride', icon: Cog6ToothIcon }
  ];

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* En-tête */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Analyse Avancée de Trading (Version Simple)
                </h1>
                <p className="mt-2 text-gray-600">
                  Version simplifiée pour tester les imports
                </p>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <MagnifyingGlassIcon className="w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={selectedSymbol}
                    onChange={(e) => setSelectedSymbol(e.target.value.toUpperCase())}
                    placeholder="Symbole (ex: AAPL)"
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <button className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                  <MagnifyingGlassIcon className="w-4 h-4" />
                  <span>Rechercher</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Navigation par onglets */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.name}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Contenu des onglets */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Onglet Actif: {tabs.find(t => t.id === activeTab)?.name}
          </h2>
          
          <div className="space-y-4">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h3 className="text-lg font-medium text-green-800">✅ Version Simple Fonctionnelle</h3>
              <p className="text-green-700">
                Cette version simplifiée fonctionne correctement. Le problème vient des composants complexes.
              </p>
            </div>
            
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="text-lg font-medium text-blue-800">🔍 Diagnostic</h3>
              <p className="text-blue-700">
                Symbole sélectionné: <strong>{selectedSymbol}</strong><br/>
                Onglet actif: <strong>{activeTab}</strong><br/>
                Icônes Heroicons: <strong>✅ Fonctionnelles</strong>
              </p>
            </div>
            
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <h3 className="text-lg font-medium text-yellow-800">⚠️ Problème Identifié</h3>
              <p className="text-yellow-700">
                Le problème vient probablement de l'import des composants Recharts ou des services API dans AdvancedAnalysisDashboard.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SimpleAdvancedAnalysisPage;
