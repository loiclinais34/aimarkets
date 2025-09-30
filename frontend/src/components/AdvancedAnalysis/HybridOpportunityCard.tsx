// frontend/src/components/AdvancedAnalysis/HybridOpportunityCard.tsx
'use client';

import React, { useState } from 'react';
import { 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon, 
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

interface HybridOpportunityCardProps {
  opportunity: {
    symbol: string;
    hybrid_score: number;
    confidence: number;
    recommendation: string;
    risk_level: string;
    technical_score: number;
    sentiment_score: number;
    market_score: number;
    ml_score: number;
    candlestick_score: number;
    garch_score: number;
    monte_carlo_score: number;
    markov_score: number;
    volatility_score: number;
    analysis_timestamp?: string;
    // Indicateurs de marché
    momentum_trend?: string;
    correlation_strength?: string;
    market_regime?: string;
    overall_score?: number;
    // Indicateur de bulle
    bubble_score?: number;
    bubble_level?: string;
  };
  onAnalyze?: (symbol: string) => void;
  onViewDetails?: (symbol: string, tab: 'technical' | 'sentiment' | 'market' | 'hybrid' | 'bubble') => void;
  className?: string;
}

const HybridOpportunityCard: React.FC<HybridOpportunityCardProps> = ({ 
  opportunity, 
  onAnalyze,
  onViewDetails,
  className = '' 
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation.toLowerCase()) {
      case 'strong_buy':
      case 'buy':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'strong_sell':
      case 'sell':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'hold':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getRecommendationIcon = (recommendation: string) => {
    switch (recommendation.toLowerCase()) {
      case 'strong_buy':
      case 'buy':
        return <CheckCircleIcon className="w-5 h-5" />;
      case 'strong_sell':
      case 'sell':
        return <XCircleIcon className="w-5 h-5" />;
      case 'hold':
        return <InformationCircleIcon className="w-5 h-5" />;
      default:
        return <InformationCircleIcon className="w-5 h-5" />;
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel.toLowerCase()) {
      case 'low':
        return 'text-green-600 bg-green-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'high':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return 'text-green-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreColorHex = (score: number) => {
    if (score > 70) return '#10b981';
    if (score > 50) return '#f59e0b';
    return '#ef4444';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatRecommendation = (recommendation: string) => {
    return recommendation.replace('_', ' ').toUpperCase();
  };

  const formatTimestamp = (timestamp?: string) => {
    if (!timestamp) return 'Maintenant';
    return new Date(timestamp).toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTrendColor = (trend: string) => {
    switch (trend.toLowerCase()) {
      case 'bullish': return '#10b981';
      case 'bearish': return '#ef4444';
      default: return '#6b7280';
    }
  };

  const getRegimeColor = (regime: string) => {
    switch (regime.toLowerCase()) {
      case 'bull market': return '#10b981';
      case 'bear market': return '#ef4444';
      case 'high volatility': return '#f59e0b';
      default: return '#6b7280';
    }
  };

  const getBubbleLevelColor = (level?: string) => {
    if (!level) return 'bg-gray-100 text-gray-600';
    switch (level.toUpperCase()) {
      case 'NORMAL':
        return 'bg-green-100 text-green-700';
      case 'WATCH':
        return 'bg-yellow-100 text-yellow-700';
      case 'RISK':
        return 'bg-orange-100 text-orange-700';
      case 'PROBABLE':
        return 'bg-red-100 text-red-700';
      case 'CRITICAL':
        return 'bg-red-200 text-red-900';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  const getBubbleLevelIcon = (level?: string) => {
    if (!level) return null;
    switch (level.toUpperCase()) {
      case 'RISK':
      case 'PROBABLE':
      case 'CRITICAL':
        return '🚨';
      case 'WATCH':
        return '⚡';
      case 'NORMAL':
        return '✅';
      default:
        return null;
    }
  };

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
            <div className={`text-3xl font-bold ${getScoreColor(opportunity.hybrid_score)}`}>
              {opportunity.hybrid_score.toFixed(0)}
            </div>
            <div className="text-sm text-gray-600">Score Hybride</div>
          </div>
        </div>

        {/* Barre de progression du score */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Score Global</span>
            <span>{opportunity.hybrid_score.toFixed(1)}/100</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div 
              className={`h-2 rounded-full transition-all duration-300 ${
                opportunity.hybrid_score >= 70 ? 'bg-green-500' :
                opportunity.hybrid_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
              }`}
              style={{ width: `${opportunity.hybrid_score}%` }}
            ></div>
          </div>
        </div>

        {/* Métriques principales */}
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center">
            <div className={`text-lg font-semibold ${getConfidenceColor(opportunity.confidence)}`}>
              {(opportunity.confidence * 100).toFixed(0)}%
            </div>
            <div className="text-xs text-gray-600">Confiance</div>
          </div>
          
          <div className="text-center">
            <div className={`text-lg font-semibold ${getRiskColor(opportunity.risk_level).split(' ')[0]}`}>
              {opportunity.risk_level.toUpperCase()}
            </div>
            <div className="text-xs text-gray-600">Risque</div>
          </div>
          
          <div className="text-center">
            <div className="text-sm font-medium text-gray-700">
              {formatTimestamp(opportunity.analysis_timestamp)}
            </div>
            <div className="text-xs text-gray-600">Analyse</div>
          </div>
        </div>

        {/* Indicateurs de marché */}
        {(opportunity.momentum_trend || opportunity.correlation_strength || opportunity.market_regime || opportunity.overall_score) && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-2 gap-4">
              {/* Tendances Actuelles */}
              <div>
                <h5 className="text-sm font-semibold text-gray-900 mb-2">Tendances Actuelles</h5>
                <div className="space-y-2">
                  {opportunity.momentum_trend && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-600">Tendance Momentum</span>
                      <span 
                        className="px-2 py-1 rounded text-xs font-medium text-white"
                        style={{ 
                          backgroundColor: getTrendColor(opportunity.momentum_trend)
                        }}
                      >
                        {opportunity.momentum_trend}
                      </span>
                    </div>
                  )}
                  {opportunity.correlation_strength && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-600">Force Corrélation</span>
                      <span className="text-xs font-bold text-gray-900">
                        {opportunity.correlation_strength}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              {/* Régime de Marché */}
              <div>
                <h5 className="text-sm font-semibold text-gray-900 mb-2">Régime de Marché</h5>
                <div className="space-y-2">
                  {opportunity.market_regime && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-600">Régime Principal</span>
                      <span 
                        className="px-2 py-1 rounded text-xs font-medium text-white"
                        style={{ 
                          backgroundColor: getRegimeColor(opportunity.market_regime)
                        }}
                      >
                        {opportunity.market_regime}
                      </span>
                    </div>
                  )}
                  {opportunity.overall_score && (
                    <div className="flex items-center justify-between">
                      <span className="text-xs text-gray-600">Score Global</span>
                      <span 
                        className="text-xs font-bold"
                        style={{ 
                          color: getScoreColorHex(opportunity.overall_score)
                        }}
                      >
                        {opportunity.overall_score.toFixed(0)}/100
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Contenu détaillé (expandable) */}
      {isExpanded && (
        <div className="p-6">
          {/* Scores détaillés */}
          <div className="mb-6">
            <h4 className="text-md font-semibold text-gray-900 mb-3">Scores Détaillés</h4>
            <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-3">
              <div className="bg-blue-50 p-3 rounded-lg text-center">
                <div className="text-sm font-medium text-blue-800">Technique</div>
                <div className={`text-xl font-bold ${getScoreColor(opportunity.technical_score)}`}>
                  {opportunity.technical_score.toFixed(0)}
                </div>
              </div>
              
              <div className="bg-purple-50 p-3 rounded-lg text-center">
                <div className="text-sm font-medium text-purple-800">Sentiment</div>
                <div className={`text-xl font-bold ${getScoreColor(opportunity.sentiment_score)}`}>
                  {opportunity.sentiment_score.toFixed(0)}
                </div>
              </div>
              
              <div className="bg-green-50 p-3 rounded-lg text-center">
                <div className="text-sm font-medium text-green-800">Marché</div>
                <div className={`text-xl font-bold ${getScoreColor(opportunity.market_score)}`}>
                  {opportunity.market_score.toFixed(0)}
                </div>
              </div>
              
              <div className="bg-orange-50 p-3 rounded-lg text-center">
                <div className="text-sm font-medium text-orange-800">ML</div>
                <div className={`text-xl font-bold ${getScoreColor(opportunity.ml_score)}`}>
                  {opportunity.ml_score.toFixed(0)}
                </div>
              </div>

              <div className="bg-indigo-50 p-3 rounded-lg text-center">
                <div className="text-sm font-medium text-indigo-800">Chandeliers</div>
                <div className={`text-xl font-bold ${getScoreColor(opportunity.candlestick_score)}`}>
                  {opportunity.candlestick_score.toFixed(0)}
                </div>
              </div>

              <div className="bg-pink-50 p-3 rounded-lg text-center">
                <div className="text-sm font-medium text-pink-800">GARCH</div>
                <div className={`text-xl font-bold ${getScoreColor(opportunity.garch_score)}`}>
                  {opportunity.garch_score.toFixed(0)}
                </div>
              </div>

              <div className="bg-teal-50 p-3 rounded-lg text-center">
                <div className="text-sm font-medium text-teal-800">Monte Carlo</div>
                <div className={`text-xl font-bold ${getScoreColor(opportunity.monte_carlo_score)}`}>
                  {opportunity.monte_carlo_score.toFixed(0)}
                </div>
              </div>

              <div className="bg-cyan-50 p-3 rounded-lg text-center">
                <div className="text-sm font-medium text-cyan-800">Markov</div>
                <div className={`text-xl font-bold ${getScoreColor(opportunity.markov_score)}`}>
                  {opportunity.markov_score.toFixed(0)}
                </div>
              </div>

              <div className="bg-amber-50 p-3 rounded-lg text-center">
                <div className="text-sm font-medium text-amber-800">Volatilité</div>
                <div className={`text-xl font-bold ${getScoreColor(opportunity.volatility_score)}`}>
                  {opportunity.volatility_score.toFixed(0)}
                </div>
              </div>
            </div>
          </div>

          {/* Analyse des composants */}
          <div className="mb-6">
            <h4 className="text-md font-semibold text-gray-900 mb-3">Analyse des Composants</h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-2">
                <ArrowTrendingUpIcon className="w-4 h-4 text-blue-600" />
                <span className="text-sm font-medium text-gray-700">Analyse Technique</span>
              </div>
                <div className="flex items-center space-x-2">
                  <div className={`text-sm font-semibold ${getScoreColor(opportunity.technical_score)}`}>
                    {opportunity.technical_score.toFixed(0)}/100
                  </div>
                  <div className="w-16 bg-gray-200 rounded-full h-1">
                    <div 
                      className={`h-1 rounded-full ${
                        opportunity.technical_score >= 70 ? 'bg-green-500' :
                        opportunity.technical_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${opportunity.technical_score}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <ExclamationTriangleIcon className="w-4 h-4 text-purple-600" />
                  <span className="text-sm font-medium text-gray-700">Analyse de Sentiment</span>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={`text-sm font-semibold ${getScoreColor(opportunity.sentiment_score)}`}>
                    {opportunity.sentiment_score.toFixed(0)}/100
                  </div>
                  <div className="w-16 bg-gray-200 rounded-full h-1">
                    <div 
                      className={`h-1 rounded-full ${
                        opportunity.sentiment_score >= 70 ? 'bg-green-500' :
                        opportunity.sentiment_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${opportunity.sentiment_score}%` }}
                    ></div>
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center space-x-2">
                <ArrowTrendingDownIcon className="w-4 h-4 text-green-600" />
                <span className="text-sm font-medium text-gray-700">Indicateurs de Marché</span>
              </div>
                <div className="flex items-center space-x-2">
                  <div className={`text-sm font-semibold ${getScoreColor(opportunity.market_score)}`}>
                    {opportunity.market_score.toFixed(0)}/100
                  </div>
                  <div className="w-16 bg-gray-200 rounded-full h-1">
                    <div 
                      className={`h-1 rounded-full ${
                        opportunity.market_score >= 70 ? 'bg-green-500' :
                        opportunity.market_score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${opportunity.market_score}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Indicateur de Bulle */}
          {opportunity.bubble_level && (
            <div className="mb-6">
              <h4 className="text-md font-semibold text-gray-900 mb-3">Risque de Bulle Spéculative</h4>
              <div className={`p-4 rounded-lg ${getBubbleLevelColor(opportunity.bubble_level)}`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-lg">{getBubbleLevelIcon(opportunity.bubble_level)}</span>
                    <span className="font-semibold">{opportunity.bubble_level}</span>
                  </div>
                  <span className="text-xl font-bold">
                    {opportunity.bubble_score?.toFixed(1)}/100
                  </span>
                </div>
                {opportunity.bubble_level !== 'NORMAL' && (
                  <p className="text-xs mt-2 opacity-90">
                    {opportunity.bubble_level === 'WATCH' && 'Surveillance recommandée - Valorisation élevée'}
                    {opportunity.bubble_level === 'RISK' && '⚠️ Risque significatif de correction - Prudence'}
                    {opportunity.bubble_level === 'PROBABLE' && '🚨 Bulle probable - Éviter toute nouvelle position'}
                    {opportunity.bubble_level === 'CRITICAL' && '🚨🚨 Bulle critique - Réduction de position recommandée'}
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={() => setIsExpanded(false)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Réduire
            </button>
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

      {/* Bouton d'expansion */}
      {!isExpanded && (
        <div className="p-4 border-t border-gray-200">
          <button
            onClick={() => onViewDetails && onViewDetails(opportunity.symbol, 'technical')}
            className="w-full text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
          >
            Voir les détails →
          </button>
        </div>
      )}
    </div>
  );
};

export default HybridOpportunityCard;
