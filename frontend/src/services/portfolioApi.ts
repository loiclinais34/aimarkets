/**
 * Service API pour la gestion des portefeuilles
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Types pour les portefeuilles
export interface Wallet {
  id: number;
  portfolio_id: number;
  name: string;
  description?: string;
  wallet_type: 'CASH' | 'MARGIN' | 'OPTIONS' | 'CRYPTO';
  currency: string;
  status: 'ACTIVE' | 'INACTIVE' | 'SUSPENDED';
  available_balance: number;
  total_balance: number;
  created_at: string;
  updated_at?: string;
}

export interface Portfolio {
  id: number;
  user_id: number;
  name: string;
  description?: string;
  portfolio_type: 'PERSONAL' | 'JOINT' | 'CORPORATE' | 'RETIREMENT';
  status: 'ACTIVE' | 'INACTIVE' | 'ARCHIVED';
  risk_tolerance: 'CONSERVATIVE' | 'MODERATE' | 'AGGRESSIVE';
  investment_goal?: string;
  target_return?: number;
  max_drawdown?: number;
  rebalancing_frequency: 'MONTHLY' | 'QUARTERLY' | 'SEMI_ANNUALLY' | 'ANNUALLY' | 'MANUAL';
  created_at: string;
  updated_at?: string;
  wallets?: Wallet[];
  total_value?: number;
  total_pnl?: number;
  total_pnl_percent?: number;
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
  investment_goal?: string;
  target_return?: number;
  max_drawdown?: number;
  rebalancing_frequency?: 'MONTHLY' | 'QUARTERLY' | 'SEMI_ANNUALLY' | 'ANNUALLY' | 'MANUAL';
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
    const response = await fetch(`${API_BASE_URL}/portfolios`, {
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
    const response = await fetch(`${API_BASE_URL}/portfolios/${portfolioId}`, {
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

export async function createPortfolio(portfolioData: CreatePortfolioRequest): Promise<Portfolio> {
  try {
    const response = await fetch(`${API_BASE_URL}/portfolios`, {
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
    const response = await fetch(`${API_BASE_URL}/portfolios/${portfolioId}`, {
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
    const response = await fetch(`${API_BASE_URL}/portfolios/${portfolioId}`, {
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

// ==================== GESTION DES WALLETS ====================

export async function createWallet(
  portfolioId: number,
  walletData: CreateWalletRequest
): Promise<Wallet> {
  try {
    const response = await fetch(`${API_BASE_URL}/portfolios/${portfolioId}/wallets`, {
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

export async function updateWallet(
  portfolioId: number,
  walletId: number,
  walletData: Partial<CreateWalletRequest>
): Promise<Wallet> {
  try {
    const response = await fetch(`${API_BASE_URL}/portfolios/${portfolioId}/wallets/${walletId}`, {
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
    const response = await fetch(`${API_BASE_URL}/portfolios/${portfolioId}/wallets/${walletId}`, {
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
    const url = new URL(`${API_BASE_URL}/portfolios/${portfolioId}/performance`);
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
    const response = await fetch(`${API_BASE_URL}/portfolios/${portfolioId}/summary`, {
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
