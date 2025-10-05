import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

export interface Symbol {
  symbol: string;
  company_name: string;
  sector?: string;
  industry?: string;
  market_cap_category?: string;
}

export interface SymbolApiResponse {
  symbol: string;
  company_name: string;
  sector?: string;
  industry?: string;
  market_cap_category?: string;
}

class SymbolsApi {
  private baseURL: string;

  constructor() {
    this.baseURL = API_BASE_URL;
  }

  private async makeRequest<T>(url: string): Promise<T> {
    try {
      const response = await axios.get<T>(url);
      return response.data;
    } catch (error) {
      console.error('Symbols API Error:', error);
      throw error;
    }
  }

  /**
   * Récupère la liste des symboles disponibles
   */
  async getSymbols(search?: string, limit: number = 100): Promise<Symbol[]> {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    params.append('limit', limit.toString());
    
    const url = `${this.baseURL}/symbols?${params.toString()}`;
    return this.makeRequest<Symbol[]>(url);
  }

  /**
   * Récupère les détails d'un symbole spécifique
   */
  async getSymbolDetails(symbol: string): Promise<SymbolApiResponse> {
    const url = `${this.baseURL}/symbols/${symbol}`;
    return this.makeRequest<SymbolApiResponse>(url);
  }

  /**
   * Recherche des symboles par nom d'entreprise ou symbole
   */
  async searchSymbols(query: string): Promise<Symbol[]> {
    return this.getSymbols(query, 50);
  }
}

export const symbolsApi = new SymbolsApi();
export default symbolsApi;
