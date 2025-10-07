/**
 * Service API pour l'analyse agent
 */

import { getAuthHeaders } from './authApi';

const API_BASE_URL = '/api/v1';

export interface AgentAnalysisRequest {
  symbol: string;
  days_back?: number;
}

export interface AgentAnalysisResponse {
  symbol: string;
  analysis_date: string;
  summary: {
    symbol: string;
    analysis_period: string;
    current_price: number;
    price_change: number;
    price_change_pct: number;
    sentiment_trend: string;
    news_impact: string;
    volatility: number;
    total_news_analyzed: number;
    executive_narrative?: string;
  };
  sentiment_evolution: Array<{
    date: string;
    sentiment_score: number;
    news_count: number;
    positive_count: number;
    negative_count: number;
    neutral_count: number;
    top_news_title?: string;
    analysis?: string;
  }>;
  price_evolution: Array<{
    date: string;
    open: number;
    close: number;
    high: number;
    low: number;
    volume: number;
  }>;
  correlation_analysis: {
    correlation: string;
    sentiment_trend: string;
    news_impact: string;
    average_sentiment: number;
    total_news: number;
  };
  key_insights: string[];
  recommendations: string[];
  executive_narrative: string;
}

class AgentAnalysisApi {
  /**
   * Génère une analyse agent complète pour un titre
   */
  async generateAnalysis(request: AgentAnalysisRequest): Promise<AgentAnalysisResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/analysis/agent-analysis`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeaders(),
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Erreur ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erreur lors de la génération de l\'analyse agent:', error);
      throw error;
    }
  }
}

export const agentAnalysisApi = new AgentAnalysisApi();
