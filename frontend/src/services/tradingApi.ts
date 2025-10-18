/**
 * API service pour le trading de titres
 * Logique simplifiée: WalletTransaction -> Position
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ==================== INTERFACES ====================

export interface Position {
  id: number;
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
  total_dividends: number;
  total_fees: number;
  weight_percentage: number;
  currency: string;
  created_at: string;
  updated_at: string;
  first_purchase_date?: string;
  last_purchase_date?: string;
  last_sale_date?: string;
}

export interface WalletTransaction {
  id: number;
  wallet_id: number;
  transaction_type: 'DEPOSIT' | 'WITHDRAWAL' | 'TRANSFER' | 'BUY_STOCK' | 'SELL_STOCK';
  amount: number;
  balance_after: number;
  symbol?: string;
  quantity?: number;
  price?: number;
  fees?: number;
  description?: string;
  created_at: string;
}

export interface BuyStockRequest {
  wallet_id: number;
  symbol: string;
  quantity: number;
  price: number;
  fees?: number;
  description?: string;
}

export interface SellStockRequest {
  wallet_id: number;
  symbol: string;
  quantity: number;
  price: number;
  fees?: number;
  description?: string;
  target_wallet_id?: number;  // Wallet de destination pour le produit de la vente
}

export interface TradingResponse {
  transaction: WalletTransaction;
  position: Position;
  message: string;
}

// ==================== FONCTIONS UTILITAIRES ====================

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('auth_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
}

// ==================== FONCTIONS DE TRADING ====================

export async function buyStock(
  portfolioId: number,
  request: BuyStockRequest
): Promise<TradingResponse> {
  try {
    console.log('DEBUG: Achat de titres:', request);
    
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/${portfolioId}/buy`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('DEBUG: Erreur de réponse:', response.status, errorData);
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    console.log('DEBUG: Achat réussi:', result);
    return result;
  } catch (error) {
    console.error('Erreur lors de l\'achat de titres:', error);
    throw error;
  }
}

export async function sellStock(
  portfolioId: number,
  request: SellStockRequest
): Promise<TradingResponse> {
  try {
    console.log('DEBUG: Vente de titres:', request);
    
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/${portfolioId}/sell`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('DEBUG: Erreur de réponse:', response.status, errorData);
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    console.log('DEBUG: Vente réussie:', result);
    return result;
  } catch (error) {
    console.error('Erreur lors de la vente de titres:', error);
    throw error;
  }
}

// ==================== FONCTIONS DE RÉCUPÉRATION ====================

export async function getPositions(portfolioId: number): Promise<Position[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/trading/${portfolioId}/positions`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors du chargement des positions:', error);
    throw error;
  }
}

export async function getTradingHistory(
  portfolioId: number,
  symbol?: string,
  limit: number = 50
): Promise<WalletTransaction[]> {
  try {
    const params = new URLSearchParams();
    if (symbol) params.append('symbol', symbol);
    params.append('limit', limit.toString());

    const response = await fetch(`${API_BASE_URL}/api/v1/trading/${portfolioId}/history?${params}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors du chargement de l\'historique:', error);
    throw error;
  }
}

// ==================== FONCTIONS UTILITAIRES ====================

export function formatCurrency(amount: number, currency: string = 'USD'): string {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(amount);
}

export function formatPercentage(value: number): string {
  return new Intl.NumberFormat('fr-FR', {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value / 100);
}

export function getPnlColor(pnl: number): string {
  if (pnl > 0) return 'text-green-600';
  if (pnl < 0) return 'text-red-600';
  return 'text-gray-600';
}

export function getPnlBgColor(pnl: number): string {
  if (pnl > 0) return 'bg-green-50';
  if (pnl < 0) return 'bg-red-50';
  return 'bg-gray-50';
}
