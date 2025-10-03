// frontend/src/components/AdvancedAnalysis/BubbleRiskPanel.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { ExclamationTriangleIcon, CheckCircleIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline';

interface BubbleRiskPanelProps {
  symbol: string;
  className?: string;
}

interface BubbleRiskData {
  symbol: string;
  analysis_date: string;
  bubble_score: number;
  bubble_level: string;
  scores: {
    valuation: number;
    momentum: number;
    statistical: number;
    sentiment: number;
  };
  ratios: {
    pe_ratio: number | null;
    ps_ratio: number | null;
    pb_ratio: number | null;
    peg_ratio: number | null;
  };
  momentum_indicators: {
    price_growth_30d: number | null;
    price_growth_90d: number | null;
    price_growth_180d: number | null;
    rsi_14d: number | null;
    distance_from_sma50: number | null;
    distance_from_sma200: number | null;
  };
  statistical_indicators: {
    price_zscore: number | null;
    volatility_ratio: number | null;
    returns_skewness: number | null;
    returns_kurtosis: number | null;
  };
}

const BubbleRiskPanel: React.FC<BubbleRiskPanelProps> = ({ symbol, className = '' }) => {
  const [bubbleData, setBubbleData] = useState<BubbleRiskData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBubbleRisk();
  }, [symbol]);

  const fetchBubbleRisk = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/v1/bubble-detection/bubble-risk/${symbol}`);
      
      if (!response.ok) {
        throw new Error(`Erreur HTTP: ${response.status}`);
      }
      
      const data = await response.json();
      setBubbleData(data);
    } catch (err) {
      console.error('Erreur lors de la récupération des données de bulle:', err);
      setError('Impossible de charger les données de bulle');
    } finally {
      setLoading(false);
    }
  };

  const getBubbleLevelColor = (level: string) => {
    switch (level.toUpperCase()) {
      case 'NORMAL':
        return 'bg-green-50 border-green-200 text-green-900';
      case 'WATCH':
        return 'bg-yellow-50 border-yellow-200 text-yellow-900';
      case 'RISK':
        return 'bg-orange-50 border-orange-200 text-orange-900';
      case 'PROBABLE':
        return 'bg-red-50 border-red-200 text-red-900';
      case 'CRITICAL':
        return 'bg-red-100 border-red-300 text-red-950';
      default:
        return 'bg-gray-50 border-gray-200 text-gray-900';
    }
  };

  const getBubbleLevelIcon = (level: string) => {
    switch (level.toUpperCase()) {
      case 'CRITICAL':
      case 'PROBABLE':
      case 'RISK':
        return <ExclamationTriangleIcon className="w-8 h-8 text-red-600" />;
      case 'WATCH':
        return <ExclamationTriangleIcon className="w-8 h-8 text-yellow-600" />;
      case 'NORMAL':
        return <CheckCircleIcon className="w-8 h-8 text-green-600" />;
      default:
        return null;
    }
  };

  const getScoreColor = (score: number) => {
    if (score < 30) return 'text-green-600';
    if (score < 50) return 'text-yellow-600';
    if (score < 70) return 'text-orange-600';
    return 'text-red-600';
  };

  const getBubbleLevelDescription = (level: string, score: number) => {
    switch (level.toUpperCase()) {
      case 'NORMAL':
        return {
          title: 'Valorisation Normale',
          description: 'Les indicateurs ne montrent pas de signes de bulle spéculative. Les ratios de valorisation sont cohérents avec les fondamentaux et le secteur.',
          recommendation: 'Analyse fondamentale standard applicable'
        };
      case 'WATCH':
        return {
          title: 'Surveillance Recommandée',
          description: 'Certains indicateurs suggèrent une valorisation élevée. Le titre mérite une attention particulière mais n\'est pas encore en zone critique.',
          recommendation: 'Surveiller l\'évolution des ratios P/E, P/S, P/B et du momentum'
        };
      case 'RISK':
        return {
          title: 'Risque de Bulle Significatif',
          description: 'Plusieurs indicateurs pointent vers une possible surévaluation. Le ratio risque/rendement devient défavorable.',
          recommendation: 'Prudence recommandée - Éviter les nouvelles positions ou réduire l\'exposition'
        };
      case 'PROBABLE':
        return {
          title: 'Bulle Probable',
          description: 'Les caractéristiques d\'une bulle spéculative sont clairement présentes. Risque élevé de correction importante.',
          recommendation: 'Ne pas initier de position - Envisager la sortie des positions existantes'
        };
      case 'CRITICAL':
        return {
          title: 'Bulle Critique',
          description: 'Tous les signaux d\'alerte sont au rouge. La valorisation est déconnectée des fondamentaux. Correction imminente probable.',
          recommendation: 'Sortir immédiatement de toute position - Risque de perte importante'
        };
      default:
        return {
          title: 'Niveau Inconnu',
          description: 'Données insuffisantes',
          recommendation: ''
        };
    }
  };

  if (loading) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        </div>
      </div>
    );
  }

  if (error || !bubbleData) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="flex items-center space-x-3 text-red-600">
          <ExclamationTriangleIcon className="w-6 h-6" />
          <span>{error || 'Aucune donnée disponible'}</span>
        </div>
      </div>
    );
  }

  // Protection globale pour éviter les erreurs si les données sont incomplètes
  if (!bubbleData.ratios || !bubbleData.momentum_indicators || !bubbleData.statistical_indicators) {
    return (
      <div className={`bg-yellow-50 rounded-lg shadow-md p-6 ${className}`}>
        <div className="flex items-center space-x-3 text-yellow-700">
          <ExclamationTriangleIcon className="w-6 h-6" />
          <div>
            <p className="font-medium">Données de bulle incomplètes</p>
            <p className="text-sm text-yellow-600">Les indicateurs de bulle ne sont pas encore calculés pour ce symbole.</p>
          </div>
        </div>
      </div>
    );
  }

  const levelInfo = getBubbleLevelDescription(bubbleData.bubble_level, bubbleData.bubble_score);

  return (
    <div className={`space-y-6 ${className}`}>
      {/* En-tête avec score global */}
      <div className={`rounded-lg shadow-md border-2 p-6 ${getBubbleLevelColor(bubbleData.bubble_level)}`}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-4">
            {getBubbleLevelIcon(bubbleData.bubble_level)}
            <div>
              <h2 className="text-2xl font-bold">{levelInfo.title}</h2>
              <p className="text-sm opacity-75">Analyse du {new Date(bubbleData.analysis_date).toLocaleDateString('fr-FR')}</p>
            </div>
          </div>
          <div className="text-right">
            <div className={`text-5xl font-bold ${getScoreColor(bubbleData.bubble_score)}`}>
              {bubbleData.bubble_score.toFixed(1)}
            </div>
            <div className="text-sm font-medium opacity-75">/ 100</div>
          </div>
        </div>
        
        <div className="mb-4">
          <p className="text-sm leading-relaxed">{levelInfo.description}</p>
        </div>
        
        {levelInfo.recommendation && (
          <div className="p-3 bg-white bg-opacity-50 rounded-lg">
            <p className="text-sm font-semibold">💡 Recommandation:</p>
            <p className="text-sm">{levelInfo.recommendation}</p>
          </div>
        )}
      </div>

      {/* Scores par catégorie */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Répartition du Score de Bulle</h3>
        
        <div className="grid grid-cols-2 gap-4">
          {/* Valorisation */}
          <div className="p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg">
            <div className="flex justify-between items-start mb-2">
              <div>
                <p className="text-sm font-medium text-blue-800">Valorisation</p>
                <p className="text-xs text-blue-600">Poids: 30%</p>
              </div>
              <p className={`text-2xl font-bold ${getScoreColor(bubbleData.scores.valuation)}`}>
                {bubbleData.scores.valuation.toFixed(0)}
              </p>
            </div>
            <div className="w-full bg-blue-200 rounded-full h-2">
              <div 
                className="h-2 rounded-full bg-blue-600"
                style={{ width: `${bubbleData.scores.valuation}%` }}
              ></div>
            </div>
          </div>

          {/* Momentum */}
          <div className="p-4 bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg">
            <div className="flex justify-between items-start mb-2">
              <div>
                <p className="text-sm font-medium text-purple-800">Momentum</p>
                <p className="text-xs text-purple-600">Poids: 25%</p>
              </div>
              <p className={`text-2xl font-bold ${getScoreColor(bubbleData.scores.momentum)}`}>
                {bubbleData.scores.momentum.toFixed(0)}
              </p>
            </div>
            <div className="w-full bg-purple-200 rounded-full h-2">
              <div 
                className="h-2 rounded-full bg-purple-600"
                style={{ width: `${bubbleData.scores.momentum}%` }}
              ></div>
            </div>
          </div>

          {/* Statistique */}
          <div className="p-4 bg-gradient-to-br from-indigo-50 to-indigo-100 rounded-lg">
            <div className="flex justify-between items-start mb-2">
              <div>
                <p className="text-sm font-medium text-indigo-800">Statistique</p>
                <p className="text-xs text-indigo-600">Poids: 25%</p>
              </div>
              <p className={`text-2xl font-bold ${getScoreColor(bubbleData.scores.statistical)}`}>
                {bubbleData.scores.statistical.toFixed(0)}
              </p>
            </div>
            <div className="w-full bg-indigo-200 rounded-full h-2">
              <div 
                className="h-2 rounded-full bg-indigo-600"
                style={{ width: `${bubbleData.scores.statistical}%` }}
              ></div>
            </div>
          </div>

          {/* Sentiment */}
          <div className="p-4 bg-gradient-to-br from-pink-50 to-pink-100 rounded-lg">
            <div className="flex justify-between items-start mb-2">
              <div>
                <p className="text-sm font-medium text-pink-800">Sentiment</p>
                <p className="text-xs text-pink-600">Poids: 20%</p>
              </div>
              <p className={`text-2xl font-bold ${getScoreColor(bubbleData.scores.sentiment)}`}>
                {bubbleData.scores.sentiment.toFixed(0)}
              </p>
            </div>
            <div className="w-full bg-pink-200 rounded-full h-2">
              <div 
                className="h-2 rounded-full bg-pink-600"
                style={{ width: `${bubbleData.scores.sentiment}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>

      {/* Ratios financiers */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Ratios de Valorisation</h3>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">P/E Ratio</p>
            <p className="text-2xl font-bold text-gray-900">
              {bubbleData.ratios && bubbleData.ratios.pe_ratio !== null && bubbleData.ratios.pe_ratio !== undefined ? bubbleData.ratios.pe_ratio.toFixed(2) : 'N/A'}
            </p>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">P/S Ratio</p>
            <p className="text-2xl font-bold text-gray-900">
              {bubbleData.ratios && bubbleData.ratios.ps_ratio !== null && bubbleData.ratios.ps_ratio !== undefined ? bubbleData.ratios.ps_ratio.toFixed(2) : 'N/A'}
            </p>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">P/B Ratio</p>
            <p className="text-2xl font-bold text-gray-900">
              {bubbleData.ratios && bubbleData.ratios.pb_ratio !== null && bubbleData.ratios.pb_ratio !== undefined ? bubbleData.ratios.pb_ratio.toFixed(2) : 'N/A'}
            </p>
          </div>
          
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600 mb-1">PEG Ratio</p>
            <p className="text-2xl font-bold text-gray-900">
              {bubbleData.ratios && bubbleData.ratios.peg_ratio !== null && bubbleData.ratios.peg_ratio !== undefined ? bubbleData.ratios.peg_ratio.toFixed(2) : 'N/A'}
            </p>
          </div>
        </div>
        
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-xs text-blue-800">
            <strong>Note:</strong> Les ratios P/E, P/S et P/B sont comparés à la moyenne sectorielle Technology (30, 10, 15 respectivement).
            Des valeurs 2x supérieures indiquent une surévaluation potentielle.
          </p>
        </div>
      </div>

      {/* Indicateurs de momentum */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Indicateurs de Momentum</h3>
        
        <div className="space-y-3">
          <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <span className="text-sm font-medium text-gray-700">Croissance 30 jours</span>
            <span className={`text-lg font-bold ${bubbleData.momentum_indicators && bubbleData.momentum_indicators.price_growth_30d && bubbleData.momentum_indicators.price_growth_30d > 20 ? 'text-orange-600' : 'text-gray-900'}`}>
              {bubbleData.momentum_indicators && bubbleData.momentum_indicators.price_growth_30d !== null && bubbleData.momentum_indicators.price_growth_30d !== undefined ? `${bubbleData.momentum_indicators.price_growth_30d.toFixed(2)}%` : 'N/A'}
            </span>
          </div>
          
          <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <span className="text-sm font-medium text-gray-700">Croissance 90 jours</span>
            <span className={`text-lg font-bold ${bubbleData.momentum_indicators && bubbleData.momentum_indicators.price_growth_90d && bubbleData.momentum_indicators.price_growth_90d > 40 ? 'text-orange-600' : 'text-gray-900'}`}>
              {bubbleData.momentum_indicators && bubbleData.momentum_indicators.price_growth_90d !== null && bubbleData.momentum_indicators.price_growth_90d !== undefined ? `${bubbleData.momentum_indicators.price_growth_90d.toFixed(2)}%` : 'N/A'}
            </span>
          </div>
          
          <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <span className="text-sm font-medium text-gray-700">Croissance 180 jours</span>
            <span className={`text-lg font-bold ${bubbleData.momentum_indicators && bubbleData.momentum_indicators.price_growth_180d && bubbleData.momentum_indicators.price_growth_180d > 60 ? 'text-orange-600' : 'text-gray-900'}`}>
              {bubbleData.momentum_indicators && bubbleData.momentum_indicators.price_growth_180d !== null && bubbleData.momentum_indicators.price_growth_180d !== undefined ? `${bubbleData.momentum_indicators.price_growth_180d.toFixed(2)}%` : 'N/A'}
            </span>
          </div>
          
          <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <span className="text-sm font-medium text-gray-700">RSI 14 jours</span>
            <span className={`text-lg font-bold ${bubbleData.momentum_indicators && bubbleData.momentum_indicators.rsi_14d && bubbleData.momentum_indicators.rsi_14d > 70 ? 'text-red-600' : 'text-gray-900'}`}>
              {bubbleData.momentum_indicators && bubbleData.momentum_indicators.rsi_14d !== null && bubbleData.momentum_indicators.rsi_14d !== undefined ? bubbleData.momentum_indicators.rsi_14d.toFixed(2) : 'N/A'}
            </span>
          </div>
          
          <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <span className="text-sm font-medium text-gray-700">Distance SMA 50</span>
            <span className={`text-lg font-bold ${bubbleData.momentum_indicators && bubbleData.momentum_indicators.distance_from_sma50 && Math.abs(bubbleData.momentum_indicators.distance_from_sma50) > 20 ? 'text-orange-600' : 'text-gray-900'}`}>
              {bubbleData.momentum_indicators && bubbleData.momentum_indicators.distance_from_sma50 !== null && bubbleData.momentum_indicators.distance_from_sma50 !== undefined ? `${bubbleData.momentum_indicators.distance_from_sma50.toFixed(2)}%` : 'N/A'}
            </span>
          </div>
          
          <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <span className="text-sm font-medium text-gray-700">Distance SMA 200</span>
            <span className={`text-lg font-bold ${bubbleData.momentum_indicators && bubbleData.momentum_indicators.distance_from_sma200 && Math.abs(bubbleData.momentum_indicators.distance_from_sma200) > 30 ? 'text-orange-600' : 'text-gray-900'}`}>
              {bubbleData.momentum_indicators && bubbleData.momentum_indicators.distance_from_sma200 !== null && bubbleData.momentum_indicators.distance_from_sma200 !== undefined ? `${bubbleData.momentum_indicators.distance_from_sma200.toFixed(2)}%` : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {/* Indicateurs statistiques */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Indicateurs Statistiques</h3>
        
        <div className="space-y-3">
          <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <div>
              <span className="text-sm font-medium text-gray-700">Z-Score Prix</span>
              <p className="text-xs text-gray-500">Écart par rapport à la moyenne</p>
            </div>
            <span className={`text-lg font-bold ${bubbleData.statistical_indicators && bubbleData.statistical_indicators.price_zscore && Math.abs(bubbleData.statistical_indicators.price_zscore) > 2 ? 'text-red-600' : 'text-gray-900'}`}>
              {bubbleData.statistical_indicators && bubbleData.statistical_indicators.price_zscore !== null && bubbleData.statistical_indicators.price_zscore !== undefined ? bubbleData.statistical_indicators.price_zscore.toFixed(4) : 'N/A'}
            </span>
          </div>
          
          <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <div>
              <span className="text-sm font-medium text-gray-700">Ratio de Volatilité</span>
              <p className="text-xs text-gray-500">Actuelle vs Historique</p>
            </div>
            <span className="text-lg font-bold text-gray-900">
              {bubbleData.statistical_indicators && bubbleData.statistical_indicators.volatility_ratio !== null && bubbleData.statistical_indicators.volatility_ratio !== undefined ? bubbleData.statistical_indicators.volatility_ratio.toFixed(4) : 'N/A'}
            </span>
          </div>
          
          <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <div>
              <span className="text-sm font-medium text-gray-700">Skewness</span>
              <p className="text-xs text-gray-500">Asymétrie des rendements</p>
            </div>
            <span className="text-lg font-bold text-gray-900">
              {bubbleData.statistical_indicators && bubbleData.statistical_indicators.returns_skewness !== null && bubbleData.statistical_indicators.returns_skewness !== undefined ? bubbleData.statistical_indicators.returns_skewness.toFixed(4) : 'N/A'}
            </span>
          </div>
          
          <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
            <div>
              <span className="text-sm font-medium text-gray-700">Kurtosis</span>
              <p className="text-xs text-gray-500">Queues de distribution</p>
            </div>
            <span className={`text-lg font-bold ${bubbleData.statistical_indicators && bubbleData.statistical_indicators.returns_kurtosis && bubbleData.statistical_indicators.returns_kurtosis > 5 ? 'text-orange-600' : 'text-gray-900'}`}>
              {bubbleData.statistical_indicators && bubbleData.statistical_indicators.returns_kurtosis !== null && bubbleData.statistical_indicators.returns_kurtosis !== undefined ? bubbleData.statistical_indicators.returns_kurtosis.toFixed(4) : 'N/A'}
            </span>
          </div>
        </div>
      </div>

      {/* Interprétation */}
      {bubbleData.bubble_level !== 'NORMAL' && (
        <div className="bg-orange-50 border-2 border-orange-200 rounded-lg p-6">
          <div className="flex items-start space-x-3">
            <ExclamationTriangleIcon className="w-6 h-6 text-orange-600 flex-shrink-0 mt-1" />
            <div>
              <h4 className="font-semibold text-orange-900 mb-2">Facteurs de Risque Identifiés</h4>
              <ul className="space-y-2 text-sm text-orange-800">
                {bubbleData.scores.valuation > 60 && (
                  <li>• <strong>Valorisation excessive:</strong> Ratios financiers {bubbleData.scores.valuation.toFixed(0)}/100 au-dessus des moyennes sectorielles</li>
                )}
                {bubbleData.scores.momentum > 60 && (
                  <li>• <strong>Momentum excessif:</strong> Croissance trop rapide ({bubbleData.scores.momentum.toFixed(0)}/100), risque de correction</li>
                )}
                {bubbleData.scores.statistical > 60 && (
                  <li>• <strong>Anomalies statistiques:</strong> Prix en zone anormale ({bubbleData.scores.statistical.toFixed(0)}/100)</li>
                )}
                {bubbleData.scores.sentiment > 60 && (
                  <li>• <strong>Euphorie détectée:</strong> Sentiment extrêmement positif ({bubbleData.scores.sentiment.toFixed(0)}/100), FOMO possible</li>
                )}
                {bubbleData.momentum_indicators.rsi_14d && bubbleData.momentum_indicators.rsi_14d > 80 && (
                  <li>• <strong>RSI critique:</strong> {bubbleData.momentum_indicators.rsi_14d.toFixed(2)} (zone extrême >80)</li>
                )}
                {bubbleData.statistical_indicators.price_zscore && Math.abs(bubbleData.statistical_indicators.price_zscore) > 3 && (
                  <li>• <strong>Anomalie statistique:</strong> Z-score de {bubbleData.statistical_indicators.price_zscore.toFixed(2)} (événement rare)</li>
                )}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BubbleRiskPanel;
