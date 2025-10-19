// frontend/src/components/AdvancedAnalysis/XGBoostOpportunityCard.tsx
'use client';

import React, { useState } from 'react';
import { 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon, 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon,
  CpuChipIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { XGBoostOpportunity } from '@/services/xgboostOpportunitiesApi';

interface XGBoostOpportunityCardProps {
  opportunity: XGBoostOpportunity;
  onAnalyze?: (symbol: string) => void;
  onViewDetails?: (symbol: string, tab: 'technical' | 'sentiment' | 'market' | 'bubble' | 'hybrid' | 'agent' | 'advanced') => void;
  onAgentAnalysis?: (symbol: string) => void;
  className?: string;
}

const XGBoostOpportunityCard: React.FC<XGBoostOpportunityCardProps> = ({ 
  opportunity, 
  onAnalyze,
  onViewDetails,
  onAgentAnalysis,
  className = '' 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation.toUpperCase()) {
      case 'BUY_STRONG':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'BUY_WEAK':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'SELL_STRONG':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'SELL_WEAK':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'HOLD':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getRecommendationIcon = (recommendation: string) => {
    switch (recommendation.toUpperCase()) {
      case 'BUY_STRONG':
      case 'BUY_WEAK':
        return <CheckCircleIcon className="w-5 h-5" />;
      case 'SELL_STRONG':
      case 'SELL_WEAK':
        return <XCircleIcon className="w-5 h-5" />;
      case 'HOLD':
        return <InformationCircleIcon className="w-5 h-5" />;
      default:
        return <InformationCircleIcon className="w-5 h-5" />;
    }
  };

  const getRiskColor = (riskScore: number | null) => {
    if (!riskScore) return 'text-gray-600 bg-gray-100';
    
    if (riskScore <= 0.3) return 'text-green-600 bg-green-100';
    if (riskScore <= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getRiskLevel = (riskScore: number | null) => {
    if (!riskScore) return 'N/A';
    
    if (riskScore <= 0.3) return 'LOW';
    if (riskScore <= 0.6) return 'MEDIUM';
    return 'HIGH';
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatRecommendation = (recommendation: string) => {
    return recommendation.replace('_', ' ').toUpperCase();
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getPotentialReturnColor = (returnValue: number | null) => {
    if (!returnValue) return 'text-gray-600';
    if (returnValue > 0) return 'text-green-600';
    return 'text-red-600';
  };

  const formatPotentialReturn = (returnValue: number | null) => {
    if (!returnValue) return 'N/A';
    return `${returnValue >= 0 ? '+' : ''}${(returnValue * 100).toFixed(2)}%`;
  };

  // Extraire les indicateurs techniques pour l'affichage
  const getTechnicalIndicatorsSummary = () => {
    if (!opportunity.technical_indicators) return null;
    
    try {
      const indicators = typeof opportunity.technical_indicators === 'string' 
        ? JSON.parse(opportunity.technical_indicators) 
        : opportunity.technical_indicators;
      
      return {
        rsi: indicators.rsi?.toFixed(1) || 'N/A',
        macd: indicators.macd?.toFixed(3) || 'N/A',
        bb_position: indicators.bb_position?.toFixed(2) || 'N/A',
        momentum_composite: indicators.momentum_composite?.toFixed(2) || 'N/A',
        volatility_composite: indicators.volatility_composite?.toFixed(2) || 'N/A',
        trend_strength: indicators.trend_strength?.toFixed(2) || 'N/A'
      };
    } catch (error) {
      console.error('Error parsing technical indicators:', error);
      return null;
    }
  };

  const technicalSummary = getTechnicalIndicatorsSummary();

  return (
    <div className={`bg-white rounded-lg shadow-md border border-gray-200 hover:shadow-lg transition-shadow ${className}`}>
      {/* En-tête de la carte */}
      <div className="p-6 border-b border-gray-200">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className="text-2xl font-bold text-gray-900">
              {opportunity.symbol}
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium border ${getRecommendationColor(opportunity.recommendation)}`}>
              <div className="flex items-center space-x-1">
                {getRecommendationIcon(opportunity.recommendation)}
                <span>{formatRecommendation(opportunity.recommendation)}</span>
              </div>
            </div>
          </div>
          
          <div className="text-right">
            <div className={`text-3xl font-bold ${getConfidenceColor(opportunity.confidence_level)}`}>
              {(opportunity.confidence_level * 100).toFixed(0)}%
            </div>
            <div className="text-sm text-gray-600">Confiance ML</div>
          </div>
        </div>

        {/* Barre de progression de la confiance */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Confiance du Modèle</span>
            <span>{(opportunity.confidence_level * 100).toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                opportunity.confidence_level >= 0.8 ? 'bg-green-500' :
                opportunity.confidence_level >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${opportunity.confidence_level * 100}%` }}
            ></div>
          </div>
        </div>

        {/* Métriques principales */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className={`text-lg font-semibold ${getPotentialReturnColor(opportunity.potential_return)}`}>
              {formatPotentialReturn(opportunity.potential_return)}
            </div>
            <div className="text-xs text-gray-600">Retour Potentiel</div>
          </div>
          
          <div className="text-center">
            <div className={`text-lg font-semibold ${getRiskColor(opportunity.risk_score).split(' ')[0]}`}>
              {getRiskLevel(opportunity.risk_score)}
            </div>
            <div className="text-xs text-gray-600">Risque</div>
          </div>
          
          <div className="text-center">
            <div className="text-sm font-medium text-gray-700">
              {formatDate(opportunity.date)}
            </div>
            <div className="text-xs text-gray-600">Date d'Analyse</div>
          </div>
        </div>

        {/* Informations du modèle ML */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center space-x-2">
              <CpuChipIcon className="w-4 h-4 text-purple-600" />
              <span className="text-gray-600">Modèle:</span>
              <span className="font-medium text-gray-900">{opportunity.ml_model_name}</span>
            </div>
            <div className="text-gray-500">
              v{opportunity.ml_model_version}
            </div>
          </div>
        </div>
      </div>

      {/* Contenu détaillé (expandable) */}
      {isExpanded && (
        <div className="p-6">
          {/* Indicateurs techniques */}
          {technicalSummary && (
            <div className="mb-6">
              <h4 className="text-md font-semibold text-gray-900 mb-3">Indicateurs Techniques Avancés</h4>
              <div className="grid grid-cols-2 lg:grid-cols-3 gap-3">
                <div className="bg-blue-50 p-3 rounded-lg text-center">
                  <div className="text-sm font-medium text-blue-800">RSI</div>
                  <div className="text-lg font-bold text-blue-900">{technicalSummary.rsi}</div>
                </div>
                
                <div className="bg-purple-50 p-3 rounded-lg text-center">
                  <div className="text-sm font-medium text-purple-800">MACD</div>
                  <div className="text-lg font-bold text-purple-900">{technicalSummary.macd}</div>
                </div>
                
                <div className="bg-green-50 p-3 rounded-lg text-center">
                  <div className="text-sm font-medium text-green-800">BB Position</div>
                  <div className="text-lg font-bold text-green-900">{technicalSummary.bb_position}</div>
                </div>
                
                <div className="bg-orange-50 p-3 rounded-lg text-center">
                  <div className="text-sm font-medium text-orange-800">Momentum</div>
                  <div className="text-lg font-bold text-orange-900">{technicalSummary.momentum_composite}</div>
                </div>
                
                <div className="bg-red-50 p-3 rounded-lg text-center">
                  <div className="text-sm font-medium text-red-800">Volatilité</div>
                  <div className="text-lg font-bold text-red-900">{technicalSummary.volatility_composite}</div>
                </div>
                
                <div className="bg-indigo-50 p-3 rounded-lg text-center">
                  <div className="text-sm font-medium text-indigo-800">Force Tendance</div>
                  <div className="text-lg font-bold text-indigo-900">{technicalSummary.trend_strength}</div>
                </div>
              </div>
            </div>
          )}

          {/* Analyse des composants */}
          <div className="mb-6">
            <h4 className="text-md font-semibold text-gray-900 mb-3">Analyse ML XGBoost</h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <CpuChipIcon className="w-4 h-4 text-purple-600" />
                  <span className="text-sm font-medium text-gray-700">Confiance du Modèle</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`text-sm font-semibold ${getConfidenceColor(opportunity.confidence_level)}`}>
                    {(opportunity.confidence_level * 100).toFixed(0)}%
                  </div>
                  <div className="w-16 bg-gray-200 rounded-full h-1">
                    <div 
                      className={`h-1 rounded-full ${
                        opportunity.confidence_level >= 0.8 ? 'bg-green-500' :
                        opportunity.confidence_level >= 0.6 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${opportunity.confidence_level * 100}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <ArrowTrendingUpIcon className="w-4 h-4 text-green-600" />
                  <span className="text-sm font-medium text-gray-700">Retour Potentiel</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`text-sm font-semibold ${getPotentialReturnColor(opportunity.potential_return)}`}>
                    {formatPotentialReturn(opportunity.potential_return)}
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <ExclamationTriangleIcon className="w-4 h-4 text-red-600" />
                  <span className="text-sm font-medium text-gray-700">Score de Risque</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`text-sm font-semibold ${getRiskColor(opportunity.risk_score).split(' ')[0]}`}>
                    {opportunity.risk_score ? (opportunity.risk_score * 100).toFixed(0) + '%' : 'N/A'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Informations détaillées */}
          <div className="mb-6">
            <h4 className="text-md font-semibold text-gray-900 mb-3">Informations Détaillées</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-gray-600">Date d'analyse:</span>
                <span className="ml-2 font-medium">{formatDate(opportunity.date)}</span>
              </div>
              <div>
                <span className="text-gray-600">Créé le:</span>
                <span className="ml-2 font-medium">{formatTimestamp(opportunity.created_at)}</span>
              </div>
              <div>
                <span className="text-gray-600">Modèle ML:</span>
                <span className="ml-2 font-medium">{opportunity.ml_model_name}</span>
              </div>
              <div>
                <span className="text-gray-600">Version:</span>
                <span className="ml-2 font-medium">{opportunity.ml_model_version}</span>
              </div>
            </div>
          </div>

          {/* Actions */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => setIsExpanded(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Réduire
            </button>
            {onAgentAnalysis && (
              <button
                onClick={() => onAgentAnalysis(opportunity.symbol)}
                className="px-4 py-2 text-sm font-medium text-white bg-purple-600 rounded-lg hover:bg-purple-700 transition-colors flex items-center space-x-2"
              >
                <CpuChipIcon className="w-4 h-4" />
                <span>Analyse Agent</span>
              </button>
            )}
            {onAnalyze && (
              <button
                onClick={() => onAnalyze(opportunity.symbol)}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Analyser en Détail
              </button>
            )}
          </div>
        </div>
      )}

      {/* Boutons d'action */}
      {!isExpanded && (
        <div className="p-4 border-t border-gray-200">
          <div className="flex space-x-2">
            <button
              onClick={() => onViewDetails && onViewDetails(opportunity.symbol, 'advanced')}
              className="flex-1 text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
            >
              Voir les détails →
            </button>
            {onAgentAnalysis && (
              <button
                onClick={() => onAgentAnalysis(opportunity.symbol)}
                className="px-3 py-1 text-sm font-medium text-white bg-purple-600 rounded hover:bg-purple-700 transition-colors flex items-center space-x-1"
              >
                <CpuChipIcon className="w-4 h-4" />
                <span>Analyse Agent</span>
              </button>
            )}
            <button
              onClick={() => setIsExpanded(true)}
              className="px-3 py-1 text-sm font-medium text-gray-600 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
            >
              <ChartBarIcon className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default XGBoostOpportunityCard;
