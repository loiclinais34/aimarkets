// Interfaces pour les Stratégies de Trading
export interface TradingStrategy {
  id: number;
  name: string;
  description: string;
  strategy_type: string;
  parameters: Record<string, any>;
  is_active: boolean;
  created_by: string;
  created_at: string;
  updated_at?: string;
}

export interface StrategyRule {
  id: number;
  rule_type: 'entry' | 'exit' | 'position_sizing' | 'risk_management';
  rule_name: string;
  rule_condition: string;
  rule_action: string;
  priority: number;
  is_active: boolean;
}

export interface StrategyParameter {
  id: number;
  parameter_name: string;
  parameter_type: 'float' | 'int' | 'boolean' | 'string' | 'choice';
  default_value: string;
  min_value?: number;
  max_value?: number;
  choices?: string[];
  description?: string;
  is_required: boolean;
}

export interface StrategyDetail {
  strategy: TradingStrategy;
  rules: StrategyRule[];
  parameters: StrategyParameter[];
}

export interface StrategyPerformance {
  id: number;
  backtest_run_id: number;
  strategy_score: number;
  rule_effectiveness: Record<string, any>;
  parameter_sensitivity: Record<string, any>;
  market_conditions: Record<string, any>;
  benchmark_return?: number;
  alpha?: number;
  beta?: number;
  information_ratio?: number;
  created_at: string;
}

export interface PredefinedStrategy {
  name: string;
  description: string;
  strategy_type: string;
  parameters: Record<string, any>;
  rules: Array<{
    rule_type: string;
    rule_name: string;
    rule_condition: string;
    rule_action: string;
    priority: number;
  }>;
}

// Interfaces pour le Backtesting
export interface BacktestRun {
  id: number;
  name: string;
  description?: string;
  model_id: number;
  model_name?: string;
  strategy_id?: number;
  strategy_name?: string;
  start_date: string;
  end_date: string;
  initial_capital: number;
  position_size_percentage: number;
  commission_rate: number;
  slippage_rate: number;
  confidence_threshold: number;
  max_positions: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_by: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
}

export interface BacktestTrade {
  id: number;
  symbol: string;
  entry_date: string;
  exit_date: string;
  entry_price: number;
  exit_price: number;
  quantity: number;
  position_type: 'long' | 'short';
  entry_confidence: number;
  exit_reason: string;
  gross_pnl: number;
  commission: number;
  slippage: number;
  net_pnl: number;
  return_percentage: number;
  holding_days: number;
}

export interface BacktestMetrics {
  id: number;
  total_return: number;
  annualized_return: number;
  total_trades: number;
  winning_trades: number;
  losing_trades: number;
  win_rate: number;
  max_drawdown: number;
  max_drawdown_duration: number;
  volatility: number;
  sharpe_ratio: number;
  sortino_ratio: number;
  avg_return_per_trade: number;
  avg_winning_trade: number;
  avg_losing_trade: number;
  profit_factor: number;
  avg_holding_period: number;
  final_capital: number;
  max_capital: number;
  min_capital: number;
  calmar_ratio: number;
  recovery_factor: number;
  expectancy: number;
}

export interface BacktestEquityPoint {
  date: string;
  equity_value: number;
  drawdown: number;
  daily_return: number;
  cumulative_return: number;
}

export interface BacktestResults {
  backtest_run: BacktestRun;
  trades: BacktestTrade[];
  metrics: BacktestMetrics;
  equity_curve: BacktestEquityPoint[];
}

export interface BacktestCreateRequest {
  name: string;
  description?: string;
  model_id: number;
  strategy_id?: number;
  start_date: string;
  end_date: string;
  initial_capital?: number;
  position_size_percentage?: number;
  commission_rate?: number;
  slippage_rate?: number;
  confidence_threshold?: number;
  max_positions?: number;
  created_by?: string;
}

export interface ModelPredictionDates {
  first_prediction_date: string;
  last_prediction_date: string;
}

// Types pour les réponses API
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  total: number;
  page?: number;
  limit?: number;
}

// Types pour les formulaires
export interface StrategyCreateForm {
  name: string;
  description: string;
  strategy_type: string;
  parameters: Record<string, any>;
  rules: Array<{
    rule_type: string;
    rule_name: string;
    rule_condition: string;
    rule_action: string;
    priority: number;
  }>;
}

export interface BacktestCreateForm {
  name: string;
  description?: string;
  model_id: number;
  strategy_id?: number;
  start_date: string;
  end_date: string;
  initial_capital: number;
  position_size_percentage: number;
  commission_rate: number;
  slippage_rate: number;
  confidence_threshold: number;
  max_positions: number;
}

// Types pour les filtres et options
export interface StrategyFilters {
  strategy_type?: string;
  is_active?: boolean;
  created_by?: string;
}

export interface BacktestFilters {
  status?: string;
  model_id?: number;
  strategy_id?: number;
  created_by?: string;
}

export interface StrategyTypeOption {
  type: string;
  name: string;
  description: string;
}
