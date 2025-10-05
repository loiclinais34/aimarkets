// frontend/src/components/AdvancedAnalysis/AnalysisDetailsView.tsx
'use client';

import React, { useState } from 'react';
import { 
  ChartBarIcon, 
  ArrowTrendingUpIcon,
  ExclamationTriangleIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';
import TechnicalSignalsChart from './TechnicalSignalsChart';
import SentimentAnalysisPanel from './SentimentAnalysisPanel';
import MarketIndicatorsWidget from './MarketIndicatorsWidget';
import BubbleRiskPanel from './BubbleRiskPanel';

interface AnalysisDetailsViewProps {
  symbol: string;
  companyName?: string;
  showBackButton?: boolean;
  onBack?: () => void;
  initialTab?: 'technical' | 'sentiment' | 'market' | 'bubble' | 'composite';
  className?: string;
}

const AnalysisDetailsView: React.FC<AnalysisDetailsViewProps> = ({
  symbol,
  companyName,
  showBackButton = true,
  onBack,
  initialTab = 'technical',
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState(initialTab);

  const tabs = [
    { id: 'technical', name: 'Technique', icon: ArrowTrendingUpIcon },
    { id: 'sentiment', name: 'Sentiment', icon: ExclamationTriangleIcon },
    { id: 'market', name: 'Marché', icon: ChartBarIcon },
    { id: 'bubble', name: 'Bulle', icon: ExclamationTriangleIcon },
    { id: 'composite', name: 'Composite', icon: Cog6ToothIcon }
  ];

  return (
    <div className={`space-y-6 ${className}`}>
      {/* En-tête avec bouton retour */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            {showBackButton && onBack && (
              <button
                onClick={onBack}
                className="flex items-center space-x-2 px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                <ArrowTrendingUpIcon className="w-4 h-4 rotate-90" />
                <span>Retour</span>
              </button>
            )}
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Analyse {activeTab === 'composite' ? 'Composite' : activeTab === 'technical' ? 'Technique' : activeTab === 'sentiment' ? 'Sentiment' : activeTab === 'market' ? 'Marché' : 'Bulle'} - {companyName || symbol}
              </h1>
              <p className="mt-1 text-gray-600">
                Analyse détaillée pour {symbol}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {/* Navigation par onglets */}
        <div className="bg-white rounded-lg shadow-sm p-6">
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

        {/* Contenu de l'analyse sélectionnée */}
        {activeTab === 'technical' && (
          <TechnicalSignalsChart symbol={symbol} />
        )}
        
        {activeTab === 'sentiment' && (
          <SentimentAnalysisPanel symbol={symbol} />
        )}
        
        {activeTab === 'market' && (
          <MarketIndicatorsWidget symbol={symbol} />
        )}
        
        {activeTab === 'bubble' && (
          <BubbleRiskPanel symbol={symbol} />
        )}
        
        {activeTab === 'composite' && (
          <div className="space-y-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Analyse Composite Complète - {symbol}
              </h3>
              <p className="text-gray-600 mb-6">
                Cette vue combine l'analyse technique, de sentiment, de marché et ML pour {symbol}.
              </p>
              
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <TechnicalSignalsChart symbol={symbol} />
                <SentimentAnalysisPanel symbol={symbol} />
              </div>
              
              <div className="mt-6">
                <MarketIndicatorsWidget symbol={symbol} />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisDetailsView;
