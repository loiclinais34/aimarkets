/**
 * Service API pour la gestion des portefeuilles
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

// Types pour les portefeuilles
export interface Wallet {
  id: number;
  portfolio_id: number;
  name: string;
  description?: string;
  wallet_type: 'CASH' | 'MARGIN' | 'OPTIONS' | 'CRYPTO';
  currency: string;
  status: 'active' | 'suspended' | 'closed';
  available_balance: number;
  total_balance: number;
  created_at: string;
  updated_at?: string;
}

export interface WalletTransaction {
  id: number;
  wallet_id: number;
  transaction_type: 'DEPOSIT' | 'WITHDRAWAL' | 'TRANSFER';
  amount: number;
  balance_after: number;
  description?: string;
  reference?: string;
  created_at: string;
  target_wallet_id?: number;
}

export interface CreateTransactionRequest {
  transaction_type: 'DEPOSIT' | 'WITHDRAWAL' | 'TRANSFER';
  amount: number;
  description?: string;
  target_wallet_id?: number;
  exchange_rate?: number;
}

export interface Portfolio {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  portfolio_type: 'personal' | 'joint' | 'corporate' | 'retirement';
  status: 'active' | 'paused' | 'closed';
  risk_tolerance: 'CONSERVATIVE' | 'MODERATE' | 'AGGRESSIVE';
  initial_capital?: number;
  current_value?: number;
  total_invested?: number;
  total_withdrawn?: number;
  total_return?: number;
  total_return_percentage?: number;
  currency?: string;
  auto_rebalance?: boolean;
  created_at: string;
  updated_at?: string;
  wallets?: Wallet[];
  positions?: Position[];
}

export interface CreatePortfolioRequest {
  name: string;
  description?: string;
  portfolio_type: 'personal' | 'joint' | 'corporate' | 'retirement';
  initial_capital?: number;
  risk_tolerance?: string;
}

export interface UpdatePortfolioRequest {
  name?: string;
  description?: string;
  risk_tolerance?: 'CONSERVATIVE' | 'MODERATE' | 'AGGRESSIVE';
}

export interface CreateWalletRequest {
  name: string;
  description?: string;
  wallet_type: 'CASH' | 'MARGIN' | 'OPTIONS' | 'CRYPTO';
  currency: string;
  initial_balance?: number;
}

export interface PortfolioPerformance {
  date: string;
  total_value: number;
  daily_return: number;
  cumulative_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  beta: number;
  alpha: number;
}

// Fonctions utilitaires pour les tokens
function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('auth_token');
  console.log('DEBUG: Token from localStorage:', token ? 'Found' : 'Not found');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

// ==================== GESTION DES PORTEFEUILLES ====================

export async function getPortfolios(): Promise<Portfolio[]> {
  try {
    const headers = getAuthHeaders();
    console.log('DEBUG: Headers being sent:', headers);
    const response = await fetch(`${API_BASE_URL}/api/v1/portfolios/`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }

    const data = await response.json();
    // L'API retourne un objet avec portfolios, total, skip, limit
    // On retourne seulement le tableau portfolios
    return data.portfolios || [];
  } catch (error) {
    console.error('Erreur lors de la récupération des portefeuilles:', error);
    throw error;
  }
}

export async function getPortfolio(portfolioId: number): Promise<Portfolio> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/portfolios/${portfolioId}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de la récupération du portefeuille:', error);
    throw error;
  }
}

export async function getWallets(portfolioId: number): Promise<Wallet[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/portfolios/${portfolioId}/wallets`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de la récupération des wallets:', error);
    throw error;
  }
}

export async function createPortfolio(portfolioData: CreatePortfolioRequest): Promise<Portfolio> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/portfolios`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(portfolioData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de la création du portefeuille:', error);
    throw error;
  }
}

export async function updatePortfolio(
  portfolioId: number,
  portfolioData: UpdatePortfolioRequest
): Promise<Portfolio> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/portfolios/${portfolioId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(portfolioData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de la mise à jour du portefeuille:', error);
    throw error;
  }
}

export async function deletePortfolio(portfolioId: number): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/portfolios/${portfolioId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }
  } catch (error) {
    console.error('Erreur lors de la suppression du portefeuille:', error);
    throw error;
  }
}

// ==================== INTERFACES POUR LES POSITIONS ====================

export interface Position {
  id: number;
  symbol: string;
  quantity: number;
  average_cost: number;
  current_price: number;
  total_cost: number;
  current_value: number;
  unrealized_pnl: number;
  unrealized_pnl_percentage: number;
  realized_pnl: number;
  currency: string;
  created_at: string;
  updated_at: string;
}


// ==================== FONCTIONS POUR LES WALLETS ====================

export async function createWallet(
  portfolioId: number,
  walletData: CreateWalletRequest
): Promise<Wallet> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/portfolios/${portfolioId}/wallets`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(walletData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de la création du wallet:', error);
    throw error;
  }
}

// ==================== FONCTIONS POUR LES TRANSACTIONS DE WALLETS ====================

export async function createWalletTransaction(
  portfolioId: number,
  walletId: number,
  transactionData: CreateTransactionRequest
): Promise<WalletTransaction> {
  try {
    console.log('DEBUG: Données de transaction envoyées:', transactionData);
    
    const response = await fetch(`${API_BASE_URL}/api/v1/portfolios/${portfolioId}/wallets/${walletId}/transactions`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(transactionData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('DEBUG: Erreur de réponse:', response.status, errorData);
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    console.log('DEBUG: Transaction créée avec succès:', result);
    return result;
  } catch (error) {
    console.error('Erreur lors de la création de la transaction:', error);
    throw error;
  }
}

export async function getWalletTransactions(
  portfolioId: number,
  walletId: number,
  limit: number = 50,
  skip: number = 0
): Promise<WalletTransaction[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/portfolios/${portfolioId}/wallets/${walletId}/transactions?limit=${limit}&skip=${skip}`, {
      method: 'GET',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors du chargement des transactions:', error);
    throw error;
  }
}

export async function updateWallet(
  portfolioId: number,
  walletId: number,
  walletData: Partial<CreateWalletRequest>
): Promise<Wallet> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/portfolios/${portfolioId}/wallets/${walletId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(walletData),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de la mise à jour du wallet:', error);
    throw error;
  }
}

export async function deleteWallet(portfolioId: number, walletId: number): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/portfolios/${portfolioId}/wallets/${walletId}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erreur ${response.status}: ${response.statusText}`);
    }
  } catch (error) {
    console.error('Erreur lors de la suppression du wallet:', error);
    throw error;
  }
}

// ==================== PERFORMANCE DES PORTEFEUILLES ====================

export async function getPortfolioPerformance(
  portfolioId: number,
  period?: string
): Promise<PortfolioPerformance[]> {
  try {
    const url = new URL(`${API_BASE_URL}/api/v1/portfolios/${portfolioId}/performance`);
    if (period) {
      url.searchParams.append('period', period);
    }

    const response = await fetch(url.toString(), {
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

// ==================== STATISTIQUES DES PORTEFEUILLES ====================

export async function getPortfolioSummary(portfolioId: number) {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/portfolios/${portfolioId}/summary`, {
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
