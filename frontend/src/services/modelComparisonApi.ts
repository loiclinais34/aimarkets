/**
 * Service API pour le Framework de Comparaison de Modèles
 * ======================================================
 * 
 * Ce service gère toutes les interactions avec l'API de comparaison de modèles
 */

import { apiClient } from './api';

// Nouvelle interface pour les interprétations
export interface MetricInterpretation {
  value: number;
  grade: string;
  interpretation: string;
  recommendation: string;
  risk_level: string;
  color: string;
}

export interface ModelAnalysis {
  model_name: string;
  overall_grade: string;
  risk_level: string;
  is_tradable: boolean;
  confidence_score: number;
  key_strengths: string[];
  key_weaknesses: string[];
  recommendations: string[];
  warnings: string[];
  metrics_analysis: Record<string, MetricInterpretation>;
}

export interface GlobalRecommendations {
  trading_recommendation: string;
  risk_level: string;
  confidence: number;
  action_items: string[];
  warnings: string[];
  next_steps: string[];
}

export interface Summary {
  total_models: number;
  tradable_models: number;
  critical_models: number;
  average_confidence: number;
  best_model: string;
  overall_assessment: string;
}

export interface EnrichedComparisonResult {
  success: boolean;
  symbol: string;
  timestamp: string;
  results: {
    model_analyses: Record<string, { analysis: ModelAnalysis }>;
    best_model: string;
    best_model_score: number;
    global_recommendations: GlobalRecommendations;
    summary: Summary;
  };
}

// Interfaces TypeScript
export interface ModelInfo {
  name: string;
  description: string;
  type: string;
  parameters: Record<string, string>;
}

export interface ModelMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  roc_auc: number;
  sharpe_ratio: number;
  max_drawdown: number;
  total_return: number;
  win_rate: number;
  profit_factor: number;
  training_time: number;
  prediction_time: number;
  model_name: string;
  timestamp: string;
  parameters: Record<string, any>;
}

export interface ComparisonResult {
  success: boolean;
  symbol: string;
  results: Record<string, ModelMetrics>;
  best_model: {
    name: string;
    metrics: {
      accuracy: number;
      f1_score: number;
      sharpe_ratio: number;
      total_return: number;
    };
  };
  report: string;
  data_info: {
    train_samples: number;
    test_samples: number;
    features: number;
  };
  error?: string;
}

export interface MultiSymbolResult {
  success: boolean;
  summary: {
    total_symbols: number;
    successful_symbols: number;
    failed_symbols: number;
    success_rate: number;
  };
  model_wins: Record<string, number>;
  model_avg_metrics: Record<string, {
    accuracy: { mean: number; std: number; min: number; max: number };
    f1_score: { mean: number; std: number; min: number; max: number };
    sharpe_ratio: { mean: number; std: number; min: number; max: number };
    total_return: { mean: number; std: number; min: number; max: number };
  }>;
  results: Record<string, ComparisonResult>;
  failed_symbols: string[];
}

export interface ModelRecommendation {
  success: boolean;
  symbol: string;
  analysis: {
    volatility: number;
    volatility_class: 'high' | 'medium' | 'low';
    trend: number;
    trend_class: 'bullish' | 'bearish' | 'sideways';
    avg_volume: number;
    data_points: number;
  };
  recommendations: {
    primary: string[];
    secondary: string[];
    avoid: string[];
    reasoning: string[];
  };
  error?: string;
}

export interface SymbolAnalysis {
  success: boolean;
  symbol: string;
  analysis: {
    volatility: number;
    volatility_class: 'high' | 'medium' | 'low';
    trend: number;
    trend_class: 'bullish' | 'bearish' | 'sideways';
    avg_volume: number;
    data_points: number;
  };
}

export interface ComparisonRequest {
  symbol: string;
  models_to_test?: string[];
  start_date?: string;
  end_date?: string;
}

export interface MultiSymbolRequest {
  symbols: string[];
  models_to_test?: string[];
}

export interface RecommendationRequest {
  symbol: string;
}

// Service principal
export const modelComparisonApi = {
  /**
   * Obtenir la liste des modèles disponibles
   */
  async getAvailableModels(): Promise<{ success: boolean; available_models: Record<string, ModelInfo>; total: number }> {
    const response = await apiClient.get('/api/v1/model-comparison/available-models');
    return response.data;
  },

  /**
   * Obtenir la liste des symboles disponibles
   */
  async getAvailableSymbols(): Promise<{ success: boolean; symbols: string[]; total: number }> {
    const response = await apiClient.get('/api/v1/model-comparison/available-symbols');
    return response.data;
  },

  /**
   * Comparer les modèles pour un symbole donné
   */
  async compareSingleSymbol(request: ComparisonRequest): Promise<ComparisonResult> {
    const response = await apiClient.post('/api/v1/model-comparison/compare-single', request);
    return response.data;
  },

  /**
   * Comparer les modèles pour plusieurs symboles
   */
  async compareMultipleSymbols(request: MultiSymbolRequest): Promise<MultiSymbolResult> {
    const response = await apiClient.post('/api/v1/model-comparison/compare-multiple', request);
    return response.data;
  },

  /**
   * Comparer les modèles avec interprétations intelligentes
   */
  async compareWithInterpretations(request: ComparisonRequest): Promise<EnrichedComparisonResult> {
    const response = await apiClient.post('/api/v1/model-comparison/compare-with-interpretations', request);
    return response.data;
  },

  /**
   * Obtenir des recommandations de modèles pour un symbole
   */
  async getModelRecommendations(request: RecommendationRequest): Promise<ModelRecommendation> {
    const response = await apiClient.post('/api/v1/model-comparison/recommendations', request);
    return response.data;
  },

  /**
   * Analyser les caractéristiques d'un symbole
   */
  async analyzeSymbol(symbol: string): Promise<SymbolAnalysis> {
    const response = await apiClient.get(`/api/v1/model-comparison/symbols/${symbol}/analysis`);
    return response.data;
  },

  /**
   * Obtenir les résultats de comparaison précédents
   */
  async getComparisonResults(limit: number = 10, offset: number = 0): Promise<{
    success: boolean;
    results: any[];
    total: number;
    limit: number;
    offset: number;
  }> {
    const response = await apiClient.get(`/api/v1/model-comparison/results?limit=${limit}&offset=${offset}`);
    return response.data;
  },

  /**
   * Vérifier la santé du service
   */
  async healthCheck(): Promise<{
    success: boolean;
    service: string;
    status: string;
    timestamp: string;
    version: string;
  }> {
    const response = await apiClient.get('/api/v1/model-comparison/health');
    return response.data;
  }
};

// Utilitaires pour l'affichage
export const modelComparisonUtils = {
  /**
   * Formater les métriques pour l'affichage
   */
  formatMetrics(metrics: ModelMetrics) {
    return {
      accuracy: (metrics.accuracy * 100).toFixed(1) + '%',
      f1Score: (metrics.f1_score * 100).toFixed(1) + '%',
      sharpeRatio: metrics.sharpe_ratio.toFixed(3),
      totalReturn: (metrics.total_return * 100).toFixed(1) + '%',
      maxDrawdown: (metrics.max_drawdown * 100).toFixed(1) + '%',
      winRate: (metrics.win_rate * 100).toFixed(1) + '%',
      profitFactor: metrics.profit_factor.toFixed(2),
      trainingTime: metrics.training_time.toFixed(2) + 's',
      predictionTime: metrics.prediction_time.toFixed(3) + 's'
    };
  },

  /**
   * Obtenir la couleur selon la performance
   */
  getPerformanceColor(value: number, type: 'accuracy' | 'f1' | 'sharpe' | 'return'): string {
    switch (type) {
      case 'accuracy':
      case 'f1':
        if (value >= 0.8) return 'text-green-600';
        if (value >= 0.7) return 'text-yellow-600';
        return 'text-red-600';
      
      case 'sharpe':
        if (value >= 2.0) return 'text-green-600';
        if (value >= 1.0) return 'text-yellow-600';
        return 'text-red-600';
      
      case 'return':
        if (value >= 0.1) return 'text-green-600';
        if (value >= 0.05) return 'text-yellow-600';
        return 'text-red-600';
      
      default:
        return 'text-gray-600';
    }
  },

  /**
   * Obtenir l'icône selon le type de modèle
   */
  getModelIcon(modelName: string): string {
    if (modelName.toLowerCase().includes('random')) return '🌲';
    if (modelName.toLowerCase().includes('xgboost')) return '🚀';
    if (modelName.toLowerCase().includes('lightgbm')) return '💡';
    if (modelName.toLowerCase().includes('neural')) return '🧠';
    return '🤖';
  },

  /**
   * Obtenir la description du modèle
   */
  getModelDescription(modelName: string): string {
    const descriptions: Record<string, string> = {
      'RandomForest': 'Modèle d\'ensemble robuste et interprétable',
      'XGBoost': 'Gradient boosting optimisé pour les performances',
      'LightGBM': 'Gradient boosting rapide et efficace',
      'NeuralNetwork': 'Réseau de neurones multi-couches'
    };
    
    return descriptions[modelName] || 'Modèle d\'apprentissage automatique';
  },

  /**
   * Trier les modèles par métrique
   */
  sortModelsByMetric(models: Record<string, ModelMetrics>, metric: keyof ModelMetrics): Array<{ name: string; metrics: ModelMetrics }> {
    return Object.entries(models)
      .map(([name, metrics]) => ({ name, metrics }))
      .sort((a, b) => (b.metrics[metric] as number) - (a.metrics[metric] as number));
  }
};
