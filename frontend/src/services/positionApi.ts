/**
 * Service API pour la gestion des positions et transactions de titres
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types pour les positions
export interface Position {
  id: number;
  portfolio_id: number;
  symbol: string;
  company_name?: string;
  quantity: number;
  average_cost: number;
  current_price?: number;
  total_cost: number;
  current_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percentage: number;
  realized_pnl: number;
  currency: string;
  created_at: string;
  updated_at?: string;
}

export interface PositionTransaction {
  id: number;
  position_id: number;
  transaction_type: 'BUY' | 'SELL' | 'DIVIDEND' | 'SPLIT';
  quantity: number;
  price: number;
  total_amount: number;
  fees: number;
  quantity_before: number;
  quantity_after: number;
  average_cost_before: number;
  average_cost_after: number;
  created_at: string;
}

export interface BuyOrderRequest {
  symbol: string;
  quantity: number;
  price: number;
  fee?: number;
  currency?: string;
  wallet_id?: number;
}

export interface SellOrderRequest {
  symbol: string;
  quantity: number;
  price: number;
  fee?: number;
  currency?: string;
  wallet_id?: number;
}

export interface PositionPerformance {
  position_id: number;
  symbol: string;
  quantity: number;
  average_buy_price: number;
  current_price: number;
  cost_basis: number;
  current_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percent: number;
  realized_pnl: number;
  total_pnl: number;
  total_return_percent: number;
}

export interface OrderExecutionResponse {
  position: Position;
  transaction: PositionTransaction;
  message: string;
}

export interface PortfolioSummary {
  total_positions: number;
  total_value: number;
  total_cost_basis: number;
  total_pnl: number;
  winning_positions: number;
  losing_positions: number;
  neutral_positions: number;
}

export interface PriceUpdateRequest {
  symbol: string;
  price: number;
}

// Fonction utilitaire pour les headers d'authentification
function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('auth_token');
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
}

// ==================== GESTION DES POSITIONS ====================

export async function getPositions(portfolioId: number): Promise<Position[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/${portfolioId}/positions`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return data.positions || [];
  } catch (error) {
    console.error('Erreur lors de la récupération des positions:', error);
    throw error;
  }
}

export async function getPosition(portfolioId: number, positionId: number): Promise<Position> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/positions/${positionId}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de la récupération de la position:', error);
    throw error;
  }
}

export async function getPositionTransactions(
  portfolioId: number, 
  positionId: number,
  limit: number = 50,
  skip: number = 0
): Promise<PositionTransaction[]> {
  try {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/positions/${positionId}/transactions?limit=${limit}&skip=${skip}`,
      {
        method: 'GET',
        headers: getAuthHeaders(),
      }
    );

    if (!response.ok) {
      throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return data.transactions || [];
  } catch (error) {
    console.error('Erreur lors de la récupération des transactions:', error);
    throw error;
  }
}

// ==================== ORDRES D'ACHAT/VENTE ====================

export async function executeBuyOrder(
  portfolioId: number, 
  order: BuyOrderRequest
): Promise<OrderExecutionResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/${portfolioId}/buy`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(order),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de l\'exécution de l\'ordre d\'achat:', error);
    throw error;
  }
}

export async function executeSellOrder(
  portfolioId: number, 
  order: SellOrderRequest
): Promise<OrderExecutionResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/${portfolioId}/sell`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(order),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de l\'exécution de l\'ordre de vente:', error);
    throw error;
  }
}

// ==================== PERFORMANCE ET STATISTIQUES ====================

export async function getPositionPerformance(
  portfolioId: number, 
  positionId: number
): Promise<PositionPerformance> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/positions/${positionId}/performance`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de la récupération de la performance:', error);
    throw error;
  }
}

export async function getPortfolioSummary(portfolioId: number): Promise<PortfolioSummary> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/${portfolioId}/summary`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de la récupération du résumé:', error);
    throw error;
  }
}

// ==================== MISE À JOUR DES PRIX ====================

export async function updatePositionPrice(
  portfolioId: number, 
  positionId: number, 
  priceUpdate: PriceUpdateRequest
): Promise<Position> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/positions/${positionId}/price`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(priceUpdate),
    });

    if (!response.ok) {
      throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de la mise à jour du prix:', error);
    throw error;
  }
}

export async function updateAllPositionsPrices(
  portfolioId: number, 
  priceUpdates: PriceUpdateRequest[]
): Promise<Position[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/${portfolioId}/prices/update`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({ price_updates: priceUpdates }),
    });

    if (!response.ok) {
      throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    return data.positions || [];
  } catch (error) {
    console.error('Erreur lors de la mise à jour des prix:', error);
    throw error;
  }
}
