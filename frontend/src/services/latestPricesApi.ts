/**
 * Service API pour récupérer les derniers cours des titres
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

// Types pour les cours
export interface LatestPrice {
  symbol: string;
  price: number;
  date: string;
  volume: number;
  currency: string;
}

export interface LatestPricesResponse {
  prices: LatestPrice[];
  timestamp: string;
  total_symbols: number;
  found_symbols: number;
}

export interface LatestPricesRequest {
  symbols: string[];
}

// Fonctions utilitaires pour les tokens
function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('auth_token');
  return {
    'Content-Type': 'application/json',
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

// ==================== FONCTIONS POUR LES DERNIERS COURS ====================

/**
 * Récupère le dernier cours connu pour un symbole
 */
export async function getLatestPrice(symbol: string): Promise<LatestPrice> {
  try {
    const response = await fetch(`${API_BASE_URL}/test-prices/${symbol}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de la récupération du cours:', error);
    throw error;
  }
}

/**
 * Récupère les derniers cours pour une liste de symboles (POST)
 */
export async function getLatestPrices(symbols: string[]): Promise<LatestPricesResponse> {
  try {
    const response = await fetch(`${API_BASE_URL}/latest-prices`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ symbols }),
    });

    if (!response.ok) {
      throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de la récupération des cours:', error);
    throw error;
  }
}

/**
 * Récupère les derniers cours pour une liste de symboles (GET avec query params)
 */
export async function getLatestPricesBatch(symbols: string[]): Promise<LatestPricesResponse> {
  try {
    const symbolsParam = symbols.join(',');
    const response = await fetch(`${API_BASE_URL}/latest-prices/batch?symbols=${symbolsParam}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Erreur ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Erreur lors de la récupération des cours:', error);
    throw error;
  }
}

/**
 * Fonction utilitaire pour créer un dictionnaire de prix à partir d'une liste de symboles
 */
export async function getPricesMap(symbols: string[]): Promise<Record<string, number>> {
  try {
    const response = await getLatestPrices(symbols);
    const pricesMap: Record<string, number> = {};
    
    response.prices.forEach(price => {
      // Vérifier que le prix est valide (nombre fini)
      const safePrice = isNaN(price.price) || !isFinite(price.price) ? 0 : Number(price.price);
      pricesMap[price.symbol] = safePrice;
    });
    
    return pricesMap;
  } catch (error) {
    console.error('Erreur lors de la création du dictionnaire de prix:', error);
    // Retourner un objet vide avec des prix à 0 en cas d'erreur
    const fallbackPricesMap: Record<string, number> = {};
    symbols.forEach(symbol => {
      fallbackPricesMap[symbol] = 0;
    });
    return fallbackPricesMap;
  }
}
