// ML Performance API Service
import { baseApi } from './baseApi';

export interface MLPerformanceSummary {
  timestamp: string;
  summary: {
    total_opportunities: number;
    success_rate: number;
    mean_return: number;
    volatility: number;
    sharpe_ratio: number;
    win_rate: number;
    profit_factor: number;
    max_drawdown: number;
  };
  recommendation_performance: {
    [key: string]: {
      count: number;
      success_rate: number;
      mean_return: number;
      avg_confidence: number;
      prediction_accuracy: number;
      volatility: number;
      sharpe_ratio: number;
      max_drawdown: number;
      win_rate: number;
      profit_factor: number;
    };
  };
  horizon_performance: {
    [key: string]: {
      count: number;
      success_rate: number;
      mean_return: number;
      sharpe_ratio: number;
      volatility: number;
      max_drawdown: number;
      win_rate: number;
      profit_factor: number;
    };
  };
  top_symbols: {
    [key: string]: {
      count: number;
      success_rate: number;
      mean_return: number;
      avg_confidence: number;
      volatility: number;
      sharpe_ratio: number;
      max_drawdown: number;
      win_rate: number;
      profit_factor: number;
    };
  };
}

export interface MLPerformanceStats {
  timestamp: string;
  status: string;
  data: {
    timestamp: string;
    analysis_summary: {
      total_opportunities_analyzed: number;
      date_range: {
        start: string;
        end: string;
      };
      symbols_covered: number;
      horizons_analyzed: number[];
    };
    overall_performance: {
      total_opportunities: number;
      successful_opportunities: number;
      success_rate: number;
      mean_return: number;
      median_return: number;
      volatility: number;
      sharpe_ratio: number;
      max_drawdown: number;
      win_rate: number;
      profit_factor: number;
      var_95: number;
      cvar_95: number;
      calmar_ratio: number;
      downside_deviation: number;
      sortino_ratio: number;
    };
    performance_by_recommendation: {
      [key: string]: {
        count: number;
        success_rate: number;
        mean_return: number;
        avg_confidence: number;
        prediction_accuracy: number;
        volatility: number;
        sharpe_ratio: number;
        max_drawdown: number;
        win_rate: number;
        profit_factor: number;
        var_95: number;
        cvar_95: number;
        calmar_ratio: number;
        downside_deviation: number;
        sortino_ratio: number;
      };
    };
    performance_by_horizon: {
      [key: string]: {
        count: number;
        success_rate: number;
        mean_return: number;
        sharpe_ratio: number;
        volatility: number;
        max_drawdown: number;
        win_rate: number;
        profit_factor: number;
        var_95: number;
        cvar_95: number;
        calmar_ratio: number;
        downside_deviation: number;
        sortino_ratio: number;
      };
    };
    performance_by_symbol: {
      [key: string]: {
        count: number;
        success_rate: number;
        mean_return: number;
        avg_confidence: number;
        volatility: number;
        sharpe_ratio: number;
        max_drawdown: number;
        win_rate: number;
        profit_factor: number;
        var_95: number;
        cvar_95: number;
        calmar_ratio: number;
        downside_deviation: number;
        sortino_ratio: number;
      };
    };
  };
}

class MLPerformanceApi {
  async getMLPerformanceSummary(limit?: number): Promise<MLPerformanceSummary> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    
    const response = await baseApi.get(`/analysis/ml-performance/summary?${params}`);
    return response.data;
  }

  async getMLPerformanceStats(limit?: number): Promise<MLPerformanceStats> {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    
    const response = await baseApi.get(`/analysis/ml-performance/stats?${params}`);
    return response.data;
  }

  async getMLPerformanceByRecommendation(recommendation?: string, limit?: number) {
    const params = new URLSearchParams();
    if (recommendation) params.append('recommendation', recommendation);
    if (limit) params.append('limit', limit.toString());
    
    const response = await baseApi.get(`/analysis/ml-performance/by-recommendation?${params}`);
    return response.data;
  }

  async getMLPerformanceByHorizon(horizon?: number, limit?: number) {
    const params = new URLSearchParams();
    if (horizon) params.append('horizon', horizon.toString());
    if (limit) params.append('limit', limit.toString());
    
    const response = await baseApi.get(`/analysis/ml-performance/by-horizon?${params}`);
    return response.data;
  }

  async getMLTopPerformers(topN: number = 10, limit?: number) {
    const params = new URLSearchParams();
    params.append('top_n', topN.toString());
    if (limit) params.append('limit', limit.toString());
    
    const response = await baseApi.get(`/analysis/ml-performance/top-performers?${params}`);
    return response.data;
  }

  async getMLPerformanceReport(limit?: number) {
    const params = new URLSearchParams();
    if (limit) params.append('limit', limit.toString());
    
    const response = await baseApi.get(`/analysis/ml-performance/report?${params}`);
    return response.data;
  }
}

export const mlPerformanceApi = new MLPerformanceApi();
