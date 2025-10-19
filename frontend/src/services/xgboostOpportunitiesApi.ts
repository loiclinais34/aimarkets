// frontend/src/services/xgboostOpportunitiesApi.ts
'use client';

export interface XGBoostOpportunity {
  symbol: string;
  date: string;
  recommendation: string;
  confidence_level: number;
  potential_return: number | null;
  risk_score: number | null;
  ml_model_name: string;
  ml_model_version: string;
  technical_indicators: any;
  ml_features: any;
  created_at: string;
}

export interface XGBoostOpportunitiesResponse {
  opportunities: XGBoostOpportunity[];
  count: number;
  filters: {
    symbol?: string;
    min_confidence?: number;
    recommendation?: string;
    limit?: number;
  };
}

export interface XGBoostOpportunitiesSummary {
  summary: {
    total_opportunities: number;
    unique_symbols: number;
    avg_confidence: number;
    avg_return: number;
    date_range: {
      earliest: string | null;
      latest: string | null;
    };
  };
  recommendations: Array<{
    recommendation: string;
    count: number;
    avg_confidence: number;
  }>;
  top_symbols: Array<{
    symbol: string;
    count: number;
    avg_confidence: number;
  }>;
}

export interface XGBoostTopPerformersResponse {
  top_performers: XGBoostOpportunity[];
  count: number;
  min_confidence: number;
}

export interface XGBoostTestResponse {
  status: string;
  table_exists?: boolean;
  total_records?: number;
  sample_data?: Array<{
    symbol: string;
    recommendation: string;
    confidence_level: number;
    potential_return: number | null;
  }>;
  message?: string;
}

class XGBoostOpportunitiesApiService {
  private baseUrl = '/api/v1/analysis';

  async getOpportunities(params: {
    symbol?: string;
    limit?: number;
    min_confidence?: number;
    recommendation?: string;
  } = {}): Promise<XGBoostOpportunitiesResponse> {
    const searchParams = new URLSearchParams();
    
    if (params.symbol) searchParams.append('symbol', params.symbol);
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.min_confidence) searchParams.append('min_confidence', params.min_confidence.toString());
    if (params.recommendation) searchParams.append('recommendation', params.recommendation);

    const response = await fetch(`${this.baseUrl}/xgboost-opportunities?${searchParams}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }

  async getOpportunitiesSummary(): Promise<XGBoostOpportunitiesSummary> {
    const response = await fetch(`${this.baseUrl}/xgboost-opportunities/summary`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }

  async getTopPerformers(params: {
    limit?: number;
    min_confidence?: number;
  } = {}): Promise<XGBoostTopPerformersResponse> {
    const searchParams = new URLSearchParams();
    
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.min_confidence) searchParams.append('min_confidence', params.min_confidence.toString());

    const response = await fetch(`${this.baseUrl}/xgboost-opportunities/top-performers?${searchParams}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }

  async testConnection(): Promise<XGBoostTestResponse> {
    const response = await fetch(`${this.baseUrl}/xgboost-opportunities/test`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }

  // Méthode pour obtenir les opportunités avec filtres avancés
  async searchOpportunities(filters: {
    symbol?: string;
    recommendation?: string;
    min_confidence?: number;
    max_confidence?: number;
    date_from?: string;
    date_to?: string;
    limit?: number;
    sort_by?: 'confidence_level' | 'potential_return' | 'date' | 'risk_score';
    sort_order?: 'asc' | 'desc';
  } = {}): Promise<XGBoostOpportunitiesResponse> {
    const searchParams = new URLSearchParams();
    
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        searchParams.append(key, value.toString());
      }
    });

    const response = await fetch(`${this.baseUrl}/xgboost-opportunities?${searchParams}`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }
}

export const xgboostOpportunitiesApi = new XGBoostOpportunitiesApiService();
