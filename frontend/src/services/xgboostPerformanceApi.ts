import { baseApi } from './baseApi';

export interface XGBoostPerformanceSummary {
  timestamp: string;
  summary: {
    total_opportunities: number;
    unique_symbols: number;
    horizons_count: number;
    date_range: {
      earliest: string;
      latest: string;
    };
    avg_confidence: number;
    avg_potential_return: number;
    avg_risk_score: number;
  };
  recommendation_performance: {
    [key: string]: {
      count: number;
      avg_confidence: number;
      avg_potential_return: number;
      avg_risk_score: number;
      min_confidence: number;
      max_confidence: number;
    };
  };
  horizon_performance: {
    [key: string]: {
      count: number;
      avg_confidence: number;
      avg_potential_return: number;
      avg_risk_score: number;
    };
  };
  top_symbols: {
    [key: string]: {
      count: number;
      avg_confidence: number;
      avg_potential_return: number;
      max_confidence: number;
    };
  };
  confidence_distribution: {
    [key: string]: {
      count: number;
      avg_confidence: number;
      avg_potential_return: number;
    };
  };
}

export interface XGBoostOpportunity {
  symbol: string;
  date: string;
  horizon_days: number;
  recommendation: string;
  confidence_level: number;
  potential_return: number;
  risk_score: number;
  ml_model_name?: string;
  ml_model_version?: string;
  created_at?: string;
}

export interface XGBoostTopOpportunities {
  timestamp: string;
  opportunities: XGBoostOpportunity[];
  total_returned: number;
}

export interface XGBoostRecentOpportunities {
  timestamp: string;
  opportunities: XGBoostOpportunity[];
  total_returned: number;
  date_range: {
    from: string;
    to: string;
  };
}

export interface XGBoostStatistics {
  timestamp: string;
  quality_metrics: {
    total_opportunities: number;
    high_confidence_count: number;
    very_high_confidence_count: number;
    positive_return_count: number;
    high_return_count: number;
    high_confidence_rate: number;
    very_high_confidence_rate: number;
    positive_return_rate: number;
    avg_confidence: number;
    confidence_std: number;
    avg_return: number;
    return_std: number;
  };
  model_performance: {
    [key: string]: {
      count: number;
      avg_confidence: number;
      avg_return: number;
    };
  };
  daily_trends: Array<{
    date: string;
    count: number;
    avg_confidence: number;
    avg_return: number;
  }>;
}

export const xgboostPerformanceApi = {
  getPerformanceSummary: async (limit?: number): Promise<XGBoostPerformanceSummary> => {
    const response = await baseApi.get('/analysis/xgboost-performance/summary', {
      params: { limit }
    });
    return response.data;
  },

  getTopOpportunities: async (
    limit: number = 20,
    recommendation?: string,
    horizon?: number
  ): Promise<XGBoostTopOpportunities> => {
    const response = await baseApi.get('/analysis/xgboost-performance/top-opportunities', {
      params: { limit, recommendation, horizon }
    });
    return response.data;
  },

  getRecentOpportunities: async (
    days: number = 7,
    limit: number = 50
  ): Promise<XGBoostRecentOpportunities> => {
    const response = await baseApi.get('/analysis/xgboost-performance/recent-opportunities', {
      params: { days, limit }
    });
    return response.data;
  },

  getStatistics: async (): Promise<XGBoostStatistics> => {
    const response = await baseApi.get('/analysis/xgboost-performance/statistics');
    return response.data;
  }
};
