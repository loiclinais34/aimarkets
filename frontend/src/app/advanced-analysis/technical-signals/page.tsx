// frontend/src/app/advanced-analysis/technical-signals/page.tsx
'use client';

import React, { useState } from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import TechnicalSignalsChart from '@/components/AdvancedAnalysis/TechnicalSignalsChart';

const TechnicalSignalsPage: React.FC = () => {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');

  return (
    <div className="min-h-screen bg-gray-50">
      {/* En-tête */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Signaux Techniques
                </h1>
                <p className="mt-2 text-gray-600">
                  Analyse technique avancée avec indicateurs multiples
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

      {/* Contenu principal */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <TechnicalSignalsChart symbol={selectedSymbol} />
      </div>
    </div>
  );
};

export default TechnicalSignalsPage;
