import { baseApi } from './baseApi';
import { AxiosResponse } from 'axios';

interface RecommendationMetrics {
  total_opportunities: number;
  successful_predictions: number;
  success_rate: number;
  mean_return: number;
  median_return: number;
  std_return: number;
  mean_confidence: number;
  risk_adjusted_return: number;
  win_rate: number;
  avg_win: number;
  avg_loss: number;
  profit_factor: number;
  gross_profit: number;
  gross_loss: number;
}

interface PerformanceStats {
  total_opportunities: number;
  analyzed_opportunities: number;
  overall_success_rate: number;
  recommendation_performance: {
    [key: string]: RecommendationMetrics;
  };
}

export const performanceApi = {
  getOpportunityPerformanceStats: async (): Promise<PerformanceStats> => {
    const response: AxiosResponse<PerformanceStats> = await baseApi.get('/analysis/opportunities/performance/kpis');
    return response.data;
  }
};