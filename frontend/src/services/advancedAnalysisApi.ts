// frontend/src/services/advancedAnalysisApi.ts
import axios from 'axios';

// Configuration de l'API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

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
  threshold?: number;
}

export interface AdvancedSearchFilters {
  // Filtres de base
  min_score?: number;
  max_risk?: string;
  limit?: number;
  
  // Filtres de dates
  date_from?: string; // YYYY-MM-DD
  date_to?: string;   // YYYY-MM-DD
  
  // Filtres de scores individuels
  min_technical_score?: number;
  min_sentiment_score?: number;
  min_market_score?: number;
  min_ml_score?: number;
  min_candlestick_score?: number;
  min_garch_score?: number;
  min_monte_carlo_score?: number;
  min_markov_score?: number;
  min_volatility_score?: number;
  
  // Filtres de recommandation et confiance
  recommendations?: string; // BUY,SELL,HOLD,STRONG_BUY,STRONG_SELL
  min_confidence?: number;
  max_confidence?: number;
  
  // Filtres de symboles
  symbols?: string; // AAPL,MSFT,GOOGL
  
  // Tri
  sort_by?: string; // composite_score, confidence_level, analysis_date, updated_at
  sort_order?: string; // asc, desc
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
    candlestick_score: number;
    garch_score: number;
    monte_carlo_score: number;
    markov_score: number;
    volatility_score: number;
    analysis_timestamp?: string;
    updated_at?: string;
    // Indicateurs de marché
    momentum_trend?: string;
    correlation_strength?: string;
    market_regime?: string;
    // Indicateur de bulle
    bubble_score?: number;
    bubble_level?: string;
  }>;
  analysis_timestamp: string;
  metadata?: {
    total_found: number;
    total_available: number;
    filters_applied: any;
  };
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
   * Recherche d'opportunités stockées dans la base de données avec filtres avancés
   */
  async searchStoredOpportunities(
    filters: AdvancedSearchFilters = {}
  ): Promise<HybridAnalysisResponse> {
    // Valeurs par défaut
    const defaultFilters = {
      min_score: 0.2,  // Score plus bas par défaut pour inclure les opportunités SELL
      max_risk: "HIGH",
      limit: 10,
      sort_by: "composite_score",
      sort_order: "desc"
    };
    
    const searchParams = { ...defaultFilters, ...filters };
    
    const response = await apiClient.get('/api/v1/advanced-analysis/opportunities/search', {
      params: searchParams
    });
    
    const data = response.data;
    
    // Convertir les opportunités stockées en format hybride
    const opportunities = data.opportunities.map((opp: any) => ({
      symbol: opp.symbol,
      hybrid_score: opp.composite_score * 100, // Convertir en pourcentage
      composite_score: opp.composite_score,
      confidence: opp.confidence_level,
      recommendation: opp.recommendation,
      risk_level: opp.risk_level,
      technical_score: opp.scores.technical * 100,
      sentiment_score: opp.scores.sentiment * 100,
      market_score: opp.scores.market * 100,
      ml_score: opp.scores.ml * 100,
      candlestick_score: opp.scores.candlestick * 100,
      garch_score: opp.scores.garch * 100,
      monte_carlo_score: opp.scores.monte_carlo * 100,
      markov_score: opp.scores.markov * 100,
      volatility_score: opp.scores.volatility * 100,
      analysis_timestamp: opp.analysis_date,
      updated_at: opp.updated_at,
      // Indicateurs de marché (données réelles du backend)
      momentum_trend: opp.market_indicators?.momentum_trend,
      correlation_strength: opp.market_indicators?.correlation_strength,
      market_regime: opp.market_indicators?.market_regime,
      overall_score: opp.market_indicators?.overall_score
    }));
    
    return {
      opportunities: opportunities,
      analysis_timestamp: data.analysis_timestamp || new Date().toISOString(),
      metadata: {
        total_found: data.total_found,
        total_available: data.total_available,
        filters_applied: data.filters_applied
      }
    };
  }

  /**
   * Recherche hybride d'opportunités (utilise les opportunités stockées)
   */
  async hybridSearch(request: HybridAnalysisRequest): Promise<HybridAnalysisResponse> {
    // Construire les filtres à partir de la requête
    const filters: AdvancedSearchFilters = {
      min_score: request.threshold || 0.5,
      limit: request.symbols.length > 0 ? request.symbols.length * 2 : 20,
      symbols: request.symbols.join(',') // Convertir le tableau en string séparée par virgules
    };
    
    return await this.searchStoredOpportunities(filters);
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

  /**
   * Génération des opportunités du jour
   */
  async generateDailyOpportunities(request: GenerateDailyOpportunitiesRequest = {}): Promise<GenerateDailyOpportunitiesResponse> {
    try {
      const response = await apiClient.post('/api/v1/advanced-analysis/generate-daily-opportunities', null, {
        params: request
      });
      return response.data;
    } catch (error: any) {
      console.error('Erreur lors de la génération des opportunités:', error);
      
      // Gérer les erreurs de réponse
      if (error.response) {
        throw new Error(`Erreur serveur: ${error.response.status} - ${error.response.data?.detail || error.response.statusText}`);
      } else if (error.request) {
        throw new Error('Erreur de connexion au serveur');
      } else {
        throw new Error(`Erreur: ${error.message}`);
      }
    }
  }
}

export interface GenerateDailyOpportunitiesRequest {
  limit_symbols?: number;
  time_horizon?: number;
  include_ml?: boolean;
}

export interface GenerateDailyOpportunitiesResponse {
  status: string;
  generation_date: string;
  summary: {
    total_symbols_requested: number;
    total_opportunities_generated: number;
    total_errors: number;
    success_rate: number;
  };
  statistics: {
    recommendations: Record<string, number>;
    risk_levels: Record<string, number>;
    average_composite_score: number;
    average_confidence: number;
  };
  top_opportunities: Array<{
    symbol: string;
    recommendation: string;
    composite_score: number;
    technical_score: number;
    confidence_level: number;
  }>;
  all_opportunities: Array<any>;
  errors: Array<any>;
}

export const advancedAnalysisApi = new AdvancedAnalysisApi();
