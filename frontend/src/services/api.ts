import axios from 'axios'

// Configuration de l'API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// Instance axios configurée
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Intercepteur pour les requêtes
apiClient.interceptors.request.use(
  (config) => {
    // Ajouter un token d'authentification si nécessaire
    // const token = localStorage.getItem('auth_token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Intercepteur pour les réponses
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Gestion des erreurs globales
    if (error.response?.status === 401) {
      // Rediriger vers la page de connexion
      // window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Types pour les réponses API
export interface APIResponse<T> {
  success: boolean
  message: string
  data?: T
}

// Types pour les métadonnées des symboles
export interface SymbolMetadata {
  id: number
  symbol: string
  company_name: string
  sector?: string
  industry?: string
  market_cap_category?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface SymbolWithMetadata {
  symbol: string
  company_name: string
  sector: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// Types pour les données
export interface HistoricalData {
  id: number
  symbol: string
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  vwap?: number
  created_at: string
  updated_at: string
}

export interface SentimentData {
  id: number
  symbol: string
  date: string
  news_count: number
  news_sentiment_score: number
  news_sentiment_std: number
  news_positive_count: number
  news_negative_count: number
  news_neutral_count: number
  top_news_title?: string
  top_news_sentiment?: number
  top_news_url?: string
  short_interest_ratio?: number
  short_interest_volume?: number
  short_interest_date?: string
  short_volume?: number
  short_exempt_volume?: number
  total_volume?: number
  short_volume_ratio?: number
  sentiment_momentum_5d?: number
  sentiment_momentum_20d?: number
  sentiment_volatility_5d?: number
  sentiment_relative_strength?: number
  data_quality_score: number
  processing_notes?: string
  created_at: string
  updated_at: string
}

export interface TechnicalIndicators {
  id: number
  symbol: string
  date: string
  sma_5?: number
  sma_10?: number
  sma_20?: number
  sma_50?: number
  sma_200?: number
  ema_5?: number
  ema_10?: number
  ema_20?: number
  ema_50?: number
  ema_200?: number
  rsi_14?: number
  macd?: number
  macd_signal?: number
  macd_histogram?: number
  stochastic_k?: number
  stochastic_d?: number
  williams_r?: number
  roc?: number
  cci?: number
  bb_upper?: number
  bb_middle?: number
  bb_lower?: number
  bb_width?: number
  bb_position?: number
  obv?: number
  volume_roc?: number
  volume_sma_20?: number
  atr_14?: number
  created_at: string
  updated_at: string
}

export interface TradingSignal {
  id: number
  symbol: string
  date: string
  signal_type: 'BUY' | 'SELL' | 'HOLD'
  confidence: number
  target_price?: number
  stop_loss?: number
  take_profit?: number
  horizon_days: number
  model_id?: number
  reasoning?: string
  created_at: string
}

export interface CorrelationMatrix {
  id: number
  symbol: string
  date: string
  correlation_type: string
  variable1: string
  variable2: string
  correlation_value: number
  correlation_method: string
  window_size: number
  created_at: string
}

export interface CrossAssetCorrelation {
  id: number
  symbol1: string
  symbol2: string
  date: string
  correlation_type: string
  correlation_value: number
  correlation_method: string
  window_size: number
  created_at: string
}

// Types pour les paramètres de cible
export interface TargetParameter {
  id: number
  user_id: string
  parameter_name: string
  target_return_percentage: number
  time_horizon_days: number
  risk_tolerance: 'low' | 'medium' | 'high'
  min_confidence_threshold: number
  max_drawdown_percentage: number
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TargetParameterCreate {
  user_id: string
  parameter_name: string
  target_return_percentage: number
  time_horizon_days: number
  risk_tolerance?: 'low' | 'medium' | 'high'
  min_confidence_threshold?: number
  max_drawdown_percentage?: number
}

export interface TargetPriceCalculation {
  current_price: number
  target_return_percentage: number
  time_horizon_days: number
  target_price: number
  expected_return: number
  daily_return: number
}

// Types pour les modèles ML
export interface MLModel {
  id: number
  model_name: string
  model_type: 'classification' | 'regression'
  model_version: string
  symbol: string
  model_parameters: Record<string, any>
  training_data_start?: string
  training_data_end?: string
  validation_score?: number
  test_score?: number
  model_path?: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ModelTrainingRequest {
  symbol: string
  target_parameter_id: number
  model_type: 'classification' | 'regression'
  test_size?: number
  random_state?: number
}

export interface ModelTrainingResponse {
  model_id: number
  model_name: string
  model_type: string
  performance_metrics: Record<string, number>
  feature_importance: Record<string, number>
  training_data_info: Record<string, any>
  message: string
}

export interface PredictionRequest {
  symbol: string
  model_id: number
  prediction_date: string
}

export interface PredictionResponse {
  symbol: string
  prediction_date: string
  prediction: number
  confidence: number
  prediction_type: string
  model_name: string
  features_used: string[]
  data_date_used?: string
}

// Interfaces pour l'interprétabilité SHAP
export interface ShapExplanation {
  feature: string
  shap_value: number
  feature_value: number
  impact: 'positive' | 'negative'
}

export interface ShapExplanationsResponse {
  model_id: number
  model_name: string
  model_type: string
  symbol: string
  prediction_date: string
  prediction: number
  shap_explanations: ShapExplanation[]
  base_value: number
}

export interface FeatureImportance {
  feature: string
  importance: number
}

export interface FeatureImportanceResponse {
  model_id: number
  model_name: string
  model_type: string
  feature_importances: FeatureImportance[]
}

// Service API
export const apiService = {
  // Données historiques
  getHistoricalData: async (params?: {
    symbol?: string
    start_date?: string
    end_date?: string
    page?: number
    size?: number
  }): Promise<PaginatedResponse<HistoricalData>> => {
    const response = await apiClient.get('/api/v1/data/historical', { params })
    return response.data
  },

  getHistoricalDataBySymbol: async (
    symbol: string,
    params?: {
      start_date?: string
      end_date?: string
      limit?: number
    }
  ): Promise<HistoricalData[]> => {
    const response = await apiClient.get(`/api/v1/data/historical/${symbol}`, { params })
    return response.data
  },

  // Données de sentiment
  getSentimentData: async (params?: {
    symbol?: string
    start_date?: string
    end_date?: string
    page?: number
    size?: number
  }): Promise<PaginatedResponse<SentimentData>> => {
    const response = await apiClient.get('/api/v1/data/sentiment', { params })
    return response.data
  },

  getSentimentDataBySymbol: async (
    symbol: string,
    params?: {
      start_date?: string
      end_date?: string
      limit?: number
    }
  ): Promise<SentimentData[]> => {
    const response = await apiClient.get(`/api/v1/data/sentiment/${symbol}`, { params })
    return response.data
  },

  // Symboles disponibles
  getAvailableSymbols: async (): Promise<SymbolWithMetadata[]> => {
    const response = await apiClient.get('/api/v1/data/symbols')
    return response.data
  },

  // Statistiques des données
  getDataStats: async (): Promise<{
    total_symbols: number
    total_historical_records: number
    total_technical_indicators: number
    total_sentiment_indicators: number
    total_ml_models: number
    total_predictions: number
    data_coverage: {
      symbols_with_technical: number
      symbols_with_sentiment: number
      technical_coverage_percentage: number
      sentiment_coverage_percentage: number
    }
    last_updated: string
  }> => {
    const response = await apiClient.get('/api/v1/data/stats')
    return response.data
  },

  // Indicateurs techniques
  getTechnicalIndicators: async (params?: {
    symbol?: string
    start_date?: string
    end_date?: string
    limit?: number
  }): Promise<TechnicalIndicators[]> => {
    const response = await apiClient.get('/api/v1/indicators/technical', { params })
    return response.data
  },

  getTechnicalIndicatorsBySymbol: async (
    symbol: string,
    params?: {
      start_date?: string
      end_date?: string
      limit?: number
    }
  ): Promise<TechnicalIndicators[]> => {
    const response = await apiClient.get(`/api/v1/indicators/technical/${symbol}`, { params })
    return response.data
  },

  // Signaux de trading
  getTradingSignals: async (params?: {
    symbol?: string
    signal_type?: string
    min_confidence?: number
    start_date?: string
    end_date?: string
    limit?: number
  }): Promise<TradingSignal[]> => {
    const response = await apiClient.get('/api/v1/signals/trading', { params })
    return response.data
  },

  getTradingSignalsBySymbol: async (
    symbol: string,
    params?: {
      signal_type?: string
      min_confidence?: number
      start_date?: string
      end_date?: string
      limit?: number
    }
  ): Promise<TradingSignal[]> => {
    const response = await apiClient.get(`/api/v1/signals/trading/${symbol}`, { params })
    return response.data
  },

  // Corrélations
  getCorrelationMatrices: async (params?: {
    symbol?: string
    correlation_type?: string
    start_date?: string
    end_date?: string
    limit?: number
  }): Promise<CorrelationMatrix[]> => {
    const response = await apiClient.get('/api/v1/correlations/matrices', { params })
    return response.data
  },

  getCrossAssetCorrelations: async (params?: {
    symbol1?: string
    symbol2?: string
    correlation_type?: string
    start_date?: string
    end_date?: string
    limit?: number
  }): Promise<CrossAssetCorrelation[]> => {
    const response = await apiClient.get('/api/v1/correlations/cross-asset', { params })
    return response.data
  },

  // Santé de l'API
  healthCheck: async (): Promise<{
    status: string
    version: string
    environment: string
  }> => {
    const response = await apiClient.get('/health')
    return response.data
  },

  // Paramètres de cible
  createTargetParameter: async (data: TargetParameterCreate): Promise<TargetParameter> => {
    const response = await apiClient.post('/api/v1/target-parameters/', data)
    return response.data
  },

  getTargetParameters: async (userId: string, activeOnly: boolean = true): Promise<TargetParameter[]> => {
    const response = await apiClient.get(`/api/v1/target-parameters/user/${userId}`, {
      params: { active_only: activeOnly }
    })
    return response.data
  },

  getTargetParameter: async (id: number): Promise<TargetParameter> => {
    const response = await apiClient.get(`/api/v1/target-parameters/${id}`)
    return response.data
  },

  updateTargetParameter: async (id: number, data: Partial<TargetParameterCreate>): Promise<TargetParameter> => {
    const response = await apiClient.put(`/api/v1/target-parameters/${id}`, data)
    return response.data
  },

  deleteTargetParameter: async (id: number): Promise<{ message: string; success: boolean }> => {
    const response = await apiClient.delete(`/api/v1/target-parameters/${id}`)
    return response.data
  },

  calculateTargetPrice: async (params: {
    current_price: number
    target_return_percentage: number
    time_horizon_days: number
  }): Promise<TargetPriceCalculation> => {
    const response = await apiClient.post('/api/v1/target-parameters/calculate-target-price', null, { params })
    return response.data
  },

  // Modèles ML
  trainModel: async (data: ModelTrainingRequest): Promise<ModelTrainingResponse> => {
    const response = await apiClient.post('/api/v1/ml-models/train', data)
    return response.data
  },

  getMLModels: async (params?: {
    model_type?: string
    active_only?: boolean
    skip?: number
    limit?: number
  }): Promise<MLModel[]> => {
    const response = await apiClient.get('/api/v1/ml-models/', { params })
    return response.data
  },

  getMLModel: async (id: number): Promise<MLModel> => {
    const response = await apiClient.get(`/api/v1/ml-models/${id}`)
    return response.data
  },

  getMLModelsForSymbol: async (symbol: string, params?: {
    model_type?: string
    active_only?: boolean
  }): Promise<MLModel[]> => {
    const response = await apiClient.get(`/api/v1/ml-models/symbol/${symbol}`, { params })
    return response.data
  },

  makePrediction: async (data: PredictionRequest): Promise<PredictionResponse> => {
    const response = await apiClient.post('/api/v1/ml-models/predict', data)
    return response.data
  },

  activateModel: async (id: number): Promise<{ message: string; success: boolean }> => {
    const response = await apiClient.put(`/api/v1/ml-models/${id}/activate`)
    return response.data
  },

  deactivateModel: async (id: number): Promise<{ message: string; success: boolean }> => {
    const response = await apiClient.put(`/api/v1/ml-models/${id}/deactivate`)
    return response.data
  },

  deleteModel: async (id: number): Promise<{ message: string; success: boolean }> => {
    const response = await apiClient.delete(`/api/v1/ml-models/${id}`)
    return response.data
  },

  getModelStats: async (): Promise<{
    total_models: number
    classification_models: number
    regression_models: number
    average_validation_score?: number
    average_test_score?: number
    models_with_validation: number
    models_with_test: number
  }> => {
    const response = await apiClient.get('/api/v1/ml-models/stats/overview')
    return response.data
  },

  // Interprétabilité SHAP
  getShapExplanations: async (params: {
    model_id: number
    symbol: string
    prediction_date: string
  }): Promise<ShapExplanationsResponse> => {
    const response = await apiClient.get(`/api/v1/ml-models/${params.model_id}/shap-explanations`, {
      params: {
        symbol: params.symbol,
        prediction_date: params.prediction_date
      }
    })
    return response.data
  },

  getModelFeatureImportance: async (model_id: number): Promise<FeatureImportanceResponse> => {
    const response = await apiClient.get(`/api/v1/ml-models/${model_id}/feature-importance`)
    return response.data
  },
}

// API pour les métadonnées des symboles
export const symbolMetadataAPI = {
  // Récupérer toutes les métadonnées
  getAll: async (params?: {
    skip?: number
    limit?: number
    sector?: string
    is_active?: boolean
  }): Promise<SymbolMetadata[]> => {
    const response = await apiClient.get('/api/v1/symbol-metadata/', { params })
    return response.data
  },

  // Récupérer les métadonnées d'un symbole
  getBySymbol: async (symbol: string): Promise<SymbolMetadata> => {
    const response = await apiClient.get(`/api/v1/symbol-metadata/${symbol}`)
    return response.data
  },

  // Rechercher par nom d'entreprise
  searchByCompany: async (companyName: string, limit?: number): Promise<SymbolMetadata[]> => {
    const response = await apiClient.get('/api/v1/symbol-metadata/search/company', {
      params: { company_name: companyName, limit }
    })
    return response.data
  },

  // Récupérer la liste des secteurs
  getSectors: async (): Promise<string[]> => {
    const response = await apiClient.get('/api/v1/symbol-metadata/sectors/list')
    return response.data
  },
}

// API Screener
export const screenerApi = {
  // Lancer un screener synchrone
  runScreener: async (params: {
    target_return_percentage: number
    time_horizon_days: number
    risk_tolerance: number
  }): Promise<any> => {
    const response = await apiClient.post('/api/v1/screener/run', params)
    return response.data
  },

  // Lancer un screener asynchrone
  runScreenerAsync: async (params: {
    target_return_percentage: number
    time_horizon_days: number
    risk_tolerance: number
  }): Promise<{ task_id: string; status: string; message: string }> => {
    const response = await apiClient.post('/api/v1/screener/run-async', params)
    return response.data
  },

  // Récupérer le statut d'une tâche
  getTaskStatus: async (taskId: string): Promise<{
    state: string
    status: string
    progress: number
    meta?: any
    result?: any
  }> => {
    const response = await apiClient.get(`/api/v1/screener/task/${taskId}/status`)
    return response.data
  },

  // Récupérer l'historique des screeners
  getHistory: async (limit?: number): Promise<any[]> => {
    const response = await apiClient.get('/api/v1/screener/history', {
      params: { limit }
    })
    return response.data
  },

  // Récupérer les statistiques des screeners
  getStats: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/screener/stats')
    return response.data
  },

  // Récupérer les résultats d'un screener
  getResults: async (screenerRunId: number): Promise<any[]> => {
    const response = await apiClient.get(`/api/v1/screener/results/${screenerRunId}`)
    return response.data
  },

  // Lancer un screener de démonstration
  runDemoScreener: async (params: {
    target_return_percentage: number
    time_horizon_days: number
    risk_tolerance: number
  }): Promise<{ task_id: string; status: string; message: string }> => {
    const response = await apiClient.post('/api/v1/screener/run-demo', params)
    return response.data
  },

  // Lancer un screener réel
  runRealScreener: async (params: {
    target_return_percentage: number
    time_horizon_days: number
    risk_tolerance: number
  }): Promise<{ task_id: string; status: string; message: string }> => {
    const response = await apiClient.post('/api/v1/screener/run-real', params)
    return response.data
  },

  // Lancer un screener complet
  runFullScreener: async (params: {
    target_return_percentage: number
    time_horizon_days: number
    risk_tolerance: number
  }): Promise<{ task_id: string; status: string; message: string }> => {
    const response = await apiClient.post('/api/v1/screener/run-full-ml-web', params)
    return response.data
  },
}

export default apiService
