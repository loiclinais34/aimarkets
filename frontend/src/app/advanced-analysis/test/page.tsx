// frontend/src/app/advanced-analysis/test/page.tsx
'use client';

import React from 'react';

const TestPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">
          Test Page - Analyse Avancée
        </h1>
        
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            Test des Composants
          </h2>
          
          <div className="space-y-4">
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <h3 className="text-lg font-medium text-green-800">✅ Page de Test</h3>
              <p className="text-green-700">
                Cette page fonctionne correctement. Le problème vient probablement des imports dans AdvancedAnalysisDashboard.
              </p>
            </div>
            
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h3 className="text-lg font-medium text-blue-800">🔧 Prochaines Étapes</h3>
              <p className="text-blue-700">
                1. Tester les imports un par un<br/>
                2. Vérifier les dépendances<br/>
                3. Corriger les erreurs d'import
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TestPage;
