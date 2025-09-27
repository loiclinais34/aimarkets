// frontend/src/app/advanced-analysis/progressive/page.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
  MagnifyingGlassIcon, 
  ChartBarIcon, 
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  Cog6ToothIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';

// Import progressif des composants pour identifier le problème
// import TechnicalSignalsChart from '@/components/AdvancedAnalysis/TechnicalSignalsChart';
// import SentimentAnalysisPanel from '@/components/AdvancedAnalysis/SentimentAnalysisPanel';
// import MarketIndicatorsWidget from '@/components/AdvancedAnalysis/MarketIndicatorsWidget';
// import HybridOpportunityCard from '@/components/AdvancedAnalysis/HybridOpportunityCard';
// import { advancedAnalysisApi, HybridAnalysisRequest, HybridAnalysisResponse } from '@/services/advancedAnalysisApi';

const ProgressiveAdvancedAnalysisPage: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [activeTab, setActiveTab] = useState<'overview' | 'technical' | 'sentiment' | 'market' | 'hybrid'>('overview');
  const [testResults, setTestResults] = useState<string[]>([]);

  const tabs = [
    { id: 'overview', name: 'Vue d\'ensemble', icon: ChartBarIcon },
    { id: 'technical', name: 'Technique', icon: ArrowTrendingUpIcon },
    { id: 'sentiment', name: 'Sentiment', icon: ExclamationTriangleIcon },
    { id: 'market', name: 'Marché', icon: ChartBarIcon },
    { id: 'hybrid', name: 'Hybride', icon: Cog6ToothIcon }
  ];

  useEffect(() => {
    const results = [
      '✅ Page de base chargée',
      '✅ Imports Heroicons fonctionnels',
      '✅ Navigation par onglets fonctionnelle',
      '⏳ Test des imports de composants...'
    ];
    setTestResults(results);

    // Test progressif des imports
    const testImports = async () => {
      try {
        // Test 1: Import du service API
        const { advancedAnalysisApi } = await import('@/services/advancedAnalysisApi');
        setTestResults(prev => [...prev, '✅ Service API importé avec succès']);
        
        // Test 2: Import des composants un par un
        try {
          const TechnicalSignalsChart = await import('@/components/AdvancedAnalysis/TechnicalSignalsChart');
          setTestResults(prev => [...prev, '✅ TechnicalSignalsChart importé']);
        } catch (error) {
          setTestResults(prev => [...prev, `❌ Erreur TechnicalSignalsChart: ${error}`]);
        }

        try {
          const SentimentAnalysisPanel = await import('@/components/AdvancedAnalysis/SentimentAnalysisPanel');
          setTestResults(prev => [...prev, '✅ SentimentAnalysisPanel importé']);
        } catch (error) {
          setTestResults(prev => [...prev, `❌ Erreur SentimentAnalysisPanel: ${error}`]);
        }

        try {
          const MarketIndicatorsWidget = await import('@/components/AdvancedAnalysis/MarketIndicatorsWidget');
          setTestResults(prev => [...prev, '✅ MarketIndicatorsWidget importé']);
        } catch (error) {
          setTestResults(prev => [...prev, `❌ Erreur MarketIndicatorsWidget: ${error}`]);
        }

        try {
          const HybridOpportunityCard = await import('@/components/AdvancedAnalysis/HybridOpportunityCard');
          setTestResults(prev => [...prev, '✅ HybridOpportunityCard importé']);
        } catch (error) {
          setTestResults(prev => [...prev, `❌ Erreur HybridOpportunityCard: ${error}`]);
        }

      } catch (error) {
        setTestResults(prev => [...prev, `❌ Erreur générale: ${error}`]);
      }
    };

    testImports();
  }, []);

  return (
    <div className="bg-gray-50 min-h-screen">
      {/* En-tête */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Test Progressif - Analyse Avancée
                </h1>
                <p className="mt-2 text-gray-600">
                  Diagnostic des imports et composants
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

        {/* Résultats des tests */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Résultats des Tests d'Import
          </h2>
          
          <div className="space-y-2">
            {testResults.map((result, index) => (
              <div key={index} className="flex items-center space-x-2">
                <span className="text-sm font-mono">{result}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Contenu des onglets */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Onglet Actif: {tabs.find(t => t.id === activeTab)?.name}
          </h2>
          
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="text-lg font-medium text-blue-800">🔍 Diagnostic en Cours</h3>
              <p className="text-blue-700">
                Cette page teste progressivement chaque import pour identifier le composant problématique.
              </p>
            </div>
            
            <div className="p-4 bg-gray-50 border border-gray-200 rounded-lg">
              <h3 className="text-lg font-medium text-gray-800">📊 Informations de Test</h3>
              <p className="text-gray-700">
                Symbole: <strong>{selectedSymbol}</strong><br/>
                Onglet: <strong>{activeTab}</strong><br/>
                Tests effectués: <strong>{testResults.length}</strong>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProgressiveAdvancedAnalysisPage;
