// frontend/src/services/advancedAnalysisApi.ts
import axios from 'axios';

// Configuration de l'API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Instance axios configurée
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface AnalysisRequest {
  symbol: string;
  time_horizon?: number;
  analysis_types?: string[];
}

export interface AnalysisResponse {
  symbol: string;
  technical_analysis: {
    composite_score: number;
    signals: any[];
    indicators: any[];
  };
  sentiment_analysis: {
    volatility_forecast: number;
    var_95: number;
    var_99: number;
    market_state: string;
    confidence: number;
  };
  market_indicators: {
    volatility_score: number;
    momentum_score: number;
    correlation_score: number;
  };
  composite_score: number;
  recommendation: string;
  confidence: number;
  risk_level: string;
  analysis_timestamp: string;
}

export interface HybridAnalysisRequest {
  symbols: string[];
  analysis_types?: string[];
  time_horizon?: number;
  weights?: Record<string, number>;
}

export interface HybridAnalysisResponse {
  opportunities: Array<{
    symbol: string;
    hybrid_score: number;
    confidence: number;
    recommendation: string;
    risk_level: string;
    technical_score: number;
    sentiment_score: number;
    market_score: number;
    ml_score: number;
  }>;
  analysis_timestamp: string;
}

export interface CompositeAnalysisRequest {
  symbol: string;
  analysis_types: string[];
  weights?: Record<string, number>;
}

export interface CompositeAnalysisResponse {
  symbol: string;
  composite_score: number;
  individual_scores: Record<string, number>;
  convergence_quality: number;
  recommendation: string;
  confidence: number;
  analysis_timestamp: string;
}

class AdvancedAnalysisApi {
  /**
   * Analyse complète d'une opportunité
   */
  async analyzeOpportunity(request: AnalysisRequest): Promise<AnalysisResponse> {
    const response = await apiClient.post('/api/v1/advanced-analysis/opportunity', request);
    return response.data;
  }

  /**
   * Recherche hybride d'opportunités
   */
  async hybridSearch(request: HybridAnalysisRequest): Promise<HybridAnalysisResponse> {
    const response = await apiClient.post('/api/v1/advanced-analysis/hybrid-search', request);
    return response.data;
  }

  /**
   * Score composite d'un symbole
   */
  async getCompositeScore(request: CompositeAnalysisRequest): Promise<CompositeAnalysisResponse> {
    const response = await apiClient.post('/api/v1/advanced-analysis/composite-score', request);
    return response.data;
  }

  /**
   * Analyse technique d'un symbole
   */
  async getTechnicalAnalysis(symbol: string): Promise<any> {
    const response = await apiClient.get(`/api/v1/technical-analysis/signals/${symbol}`);
    return response.data;
  }

  /**
   * Analyse de sentiment d'un symbole
   */
  async getSentimentAnalysis(symbol: string): Promise<any> {
    const response = await apiClient.get(`/api/v1/sentiment-analysis/garch/${symbol}`);
    return response.data;
  }

  /**
   * Indicateurs de marché d'un symbole
   */
  async getMarketIndicators(symbol: string): Promise<any> {
    const response = await apiClient.get(`/api/v1/market-indicators/volatility/${symbol}`);
    return response.data;
  }
}

export const advancedAnalysisApi = new AdvancedAnalysisApi();
