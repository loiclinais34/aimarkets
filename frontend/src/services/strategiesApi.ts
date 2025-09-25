import { 
  TradingStrategy, 
  StrategyDetail, 
  StrategyRule, 
  StrategyPerformance, 
  PredefinedStrategy, 
  StrategyTypeOption,
  StrategyCreateForm,
  ApiResponse,
  PaginatedResponse,
  StrategyFilters,
  BacktestRun,
  BacktestResults,
  BacktestCreateForm,
  BacktestTrade,
  BacktestMetrics,
  BacktestEquityPoint,
  ModelPredictionDates
} from '../types/strategies';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Service pour les Stratégies de Trading
export const strategiesApi = {
  // Récupérer toutes les stratégies
  async getStrategies(filters?: StrategyFilters): Promise<PaginatedResponse<TradingStrategy>> {
    const params = new URLSearchParams();
    if (filters?.strategy_type) params.append('strategy_type', filters.strategy_type);
    if (filters?.is_active !== undefined) params.append('is_active', filters.is_active.toString());
    if (filters?.created_by) params.append('created_by', filters.created_by);

    const response = await fetch(`${API_BASE_URL}/api/v1/strategies/?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Erreur lors de la récupération des stratégies: ${response.statusText}`);
    }
    const data = await response.json();
    console.log('Raw API response:', data);
    // Adapter la réponse du backend au format attendu par le frontend
    return {
      success: data.success,
      data: data.strategies,
      total: data.total
    };
  },

  // Récupérer une stratégie spécifique
  async getStrategy(strategyId: number): Promise<StrategyDetail> {
    const response = await fetch(`${API_BASE_URL}/api/v1/strategies/${strategyId}`);
    if (!response.ok) {
      throw new Error(`Erreur lors de la récupération de la stratégie: ${response.statusText}`);
    }
    const result = await response.json();
    return result;
  },

  // Créer une nouvelle stratégie
  async createStrategy(strategyData: StrategyCreateForm): Promise<ApiResponse<{ strategy_id: number }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/strategies/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...strategyData,
        created_by: 'user'
      }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erreur lors de la création de la stratégie: ${response.statusText}`);
    }
    return response.json();
  },

  // Mettre à jour une stratégie
  async updateStrategy(strategyId: number, updates: Partial<TradingStrategy>): Promise<ApiResponse<void>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/strategies/${strategyId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erreur lors de la mise à jour de la stratégie: ${response.statusText}`);
    }
    return response.json();
  },

  // Supprimer une stratégie
  async deleteStrategy(strategyId: number): Promise<ApiResponse<void>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/strategies/${strategyId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erreur lors de la suppression de la stratégie: ${response.statusText}`);
    }
    return response.json();
  },

  // Ajouter une règle à une stratégie
  async addRule(strategyId: number, rule: Omit<StrategyRule, 'id'>): Promise<ApiResponse<{ rule_id: number }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/strategies/${strategyId}/rules`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(rule),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erreur lors de l'ajout de la règle: ${response.statusText}`);
    }
    return response.json();
  },

  // Mettre à jour une règle
  async updateRule(ruleId: number, updates: Partial<StrategyRule>): Promise<ApiResponse<void>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/strategies/rules/${ruleId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(updates),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erreur lors de la mise à jour de la règle: ${response.statusText}`);
    }
    return response.json();
  },

  // Supprimer une règle
  async deleteRule(ruleId: number): Promise<ApiResponse<void>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/strategies/rules/${ruleId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erreur lors de la suppression de la règle: ${response.statusText}`);
    }
    return response.json();
  },

  // Récupérer les performances d'une stratégie
  async getStrategyPerformance(strategyId: number): Promise<ApiResponse<{
    performances: StrategyPerformance[];
    statistics: {
      total_backtests: number;
      average_score: number;
      average_alpha: number;
      average_beta: number;
    };
  }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/strategies/${strategyId}/performance`);
    if (!response.ok) {
      throw new Error(`Erreur lors de la récupération des performances: ${response.statusText}`);
    }
    return response.json();
  },

  // Récupérer les types de stratégies prédéfinies
  async getPredefinedTypes(): Promise<ApiResponse<StrategyTypeOption[]>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/strategies/predefined/types`);
    if (!response.ok) {
      throw new Error(`Erreur lors de la récupération des types: ${response.statusText}`);
    }
    return response.json();
  },

  // Récupérer une stratégie prédéfinie par type
  async getPredefinedStrategy(strategyType: string): Promise<ApiResponse<PredefinedStrategy>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/strategies/predefined/${strategyType}`);
    if (!response.ok) {
      throw new Error(`Erreur lors de la récupération de la stratégie prédéfinie: ${response.statusText}`);
    }
    return response.json();
  },

  // Initialiser toutes les stratégies prédéfinies
  async initializePredefinedStrategies(): Promise<ApiResponse<{
    results: Array<{
      name: string;
      strategy_id?: number;
      status: 'created' | 'failed';
      error?: string;
    }>;
    message: string;
  }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/strategies/predefined/initialize`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erreur lors de l'initialisation: ${response.statusText}`);
    }
    return response.json();
  },

  // Initialiser une stratégie prédéfinie spécifique
  async initializePredefinedStrategy(strategyType: string): Promise<ApiResponse<{ strategy_id: number }>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/strategies/predefined/initialize/${strategyType}`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erreur lors de l'initialisation: ${response.statusText}`);
    }
    return response.json();
  }
};

// Service pour le Backtesting
export const backtestingApi = {
  // Récupérer les symboles disponibles pour le backtesting
  async getAvailableSymbols(): Promise<{ success: boolean; symbols: Array<{ symbol: string; prediction_count: number; model_count: number }>; total: number }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/backtesting/symbols`);
    if (!response.ok) {
      throw new Error(`Erreur lors de la récupération des symboles: ${response.statusText}`);
    }
    return response.json();
  },

  // Récupérer les modèles disponibles pour un symbole
  async getModelsForSymbol(symbol: string, limit: number = 50, offset: number = 0, search?: string): Promise<{ success: boolean; symbol: string; models: Array<{ id: number; name: string; type: string; version: string; symbol: string; prediction_count: number; date_range: { start: string | null; end: string | null } }>; total: number; limit: number; offset: number; has_more: boolean }> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    params.append('offset', offset.toString());
    if (search) params.append('search', search);
    
    const response = await fetch(`${API_BASE_URL}/api/v1/backtesting/symbols/${symbol}/models?${params.toString()}`);
    if (!response.ok) {
      throw new Error(`Erreur lors de la récupération des modèles: ${response.statusText}`);
    }
    return response.json();
  },

  // Récupérer les dates disponibles pour un modèle
  async getAvailableDatesForModel(modelId: number): Promise<{ success: boolean; available_dates: string[]; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/backtesting/models/${modelId}/available-dates`);
    if (!response.ok) {
      throw new Error(`Erreur lors de la récupération des dates: ${response.statusText}`);
    }
    return response.json();
  },

  // Récupérer tous les backtests
  async getBacktestRuns(skip: number = 0, limit: number = 100): Promise<BacktestRun[]> {
    const response = await fetch(`${API_BASE_URL}/api/v1/backtesting/runs?skip=${skip}&limit=${limit}`);
    if (!response.ok) {
      throw new Error(`Erreur lors de la récupération des backtests: ${response.statusText}`);
    }
    return response.json();
  },

  // Récupérer un backtest spécifique
  async getBacktestRun(backtestId: number): Promise<BacktestRun> {
    const response = await fetch(`${API_BASE_URL}/api/v1/backtesting/runs/${backtestId}`);
    if (!response.ok) {
      throw new Error(`Erreur lors de la récupération du backtest: ${response.statusText}`);
    }
    return response.json();
  },

  // Créer un nouveau backtest
  async createBacktest(backtestData: any): Promise<ApiResponse<BacktestRun>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/backtesting/create`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        ...backtestData,
        created_by: 'user'
      }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erreur lors de la création du backtest: ${response.statusText}`);
    }
    return response.json();
  },

  // Exécuter un backtest
  async runBacktest(backtestId: number): Promise<ApiResponse<BacktestRun>> {
    const response = await fetch(`${API_BASE_URL}/api/v1/backtesting/run/${backtestId}`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erreur lors de l'exécution du backtest: ${response.statusText}`);
    }
    return response.json();
  },

  // Récupérer les résultats d'un backtest
  async getBacktestResults(backtestId: number): Promise<BacktestResults> {
    const response = await fetch(`${API_BASE_URL}/api/v1/backtesting/results/${backtestId}`);
    if (!response.ok) {
      throw new Error(`Erreur lors de la récupération des résultats: ${response.statusText}`);
    }
    return response.json();
  },

  // Récupérer les dates de prédiction disponibles pour un modèle
  async getModelPredictionDates(modelId: number): Promise<{ first_prediction_date: string; last_prediction_date: string }> {
    const response = await fetch(`${API_BASE_URL}/api/v1/backtesting/models/${modelId}/available-dates`);
    if (!response.ok) {
      throw new Error(`Erreur lors de la récupération des dates: ${response.statusText}`);
    }
    return response.json();
  },

  // Supprimer un backtest
  async deleteBacktest(backtestId: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/backtesting/runs/${backtestId}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || `Erreur lors de la suppression du backtest: ${response.statusText}`);
    }
  }
};
