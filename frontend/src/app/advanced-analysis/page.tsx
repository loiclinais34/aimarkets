// frontend/src/app/advanced-analysis/page.tsx
'use client';

import React, { useState } from 'react';
import { useRequireAuth } from '@/contexts/AuthContext';
import AppLayout from '@/components/Layout/AppLayout';
import DynamicSymbolSelector from '@/components/AdvancedAnalysis/DynamicSymbolSelector';
import AnalysisDetailsView from '@/components/AdvancedAnalysis/AnalysisDetailsView';

const AdvancedAnalysisPage: React.FC = () => {
  const { isAuthenticated, isLoading } = useRequireAuth();
  const [selectedSymbol, setSelectedSymbol] = useState<string>('');
  const [selectedCompany, setSelectedCompany] = useState<string>('');
  const [showAnalysisDetails, setShowAnalysisDetails] = useState<boolean>(false);

  const handleSymbolSelect = (symbol: string, companyName: string) => {
    setSelectedSymbol(symbol);
    setSelectedCompany(companyName);
    setShowAnalysisDetails(true);
  };

  const handleBackToSelection = () => {
    setShowAnalysisDetails(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <svg className="animate-spin mx-auto h-12 w-12 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="mt-4 text-lg text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  // Si un symbole est sélectionné, afficher les analyses détaillées
  if (showAnalysisDetails && selectedSymbol) {
    return (
      <AppLayout>
        <AnalysisDetailsView
          symbol={selectedSymbol}
          companyName={selectedCompany}
          showBackButton={true}
          onBack={handleBackToSelection}
          initialTab="technical"
        />
      </AppLayout>
    );
  }

  // Page de sélection de symbole
  return (
    <AppLayout>
      <div className="space-y-6">
        {/* En-tête */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h1 className="text-2xl font-bold text-gray-900">📈 Analyses Avancées</h1>
          <p className="mt-2 text-gray-600">
            Analysez n'importe quel titre avec nos outils d'analyse avancés (technique, sentiment, marché, bulle)
          </p>
        </div>

        {/* Sélecteur de symboles */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Sélection du Titre à Analyser
          </h2>
          <DynamicSymbolSelector 
            onSymbolSelect={handleSymbolSelect}
            placeholder="Rechercher un symbole ou une entreprise (ex: AAPL, Apple, Microsoft)"
            className="mb-4"
          />
          
          {selectedSymbol && !showAnalysisDetails && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-12 h-12 bg-green-600 text-white rounded-lg flex items-center justify-center font-bold text-lg">
                    {selectedSymbol.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{selectedSymbol}</h3>
                    <p className="text-sm text-gray-600">{selectedCompany}</p>
                  </div>
                </div>
                <div className="text-sm text-green-700">
                  ✅ Prêt pour l'analyse
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
};

export default AdvancedAnalysisPage;
