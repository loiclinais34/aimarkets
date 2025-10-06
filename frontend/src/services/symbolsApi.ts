import axios from 'axios';

// Utiliser le même base URL que les autres services (sans localhost)
const API_BASE_URL = '/api/v1';

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
  /**
   * Récupère la liste des symboles disponibles
   */
  async getSymbols(search?: string, limit: number = 100): Promise<Symbol[]> {
    try {
      const params: any = { limit };
      if (search) params.search = search;
      
      const response = await axios.get(`${API_BASE_URL}/data/symbols`, { params });
      return response.data;
    } catch (error) {
      console.error('Symbols API Error:', error);
      throw error;
    }
  }

  /**
   * Récupère les détails d'un symbole spécifique
   */
  async getSymbolDetails(symbol: string): Promise<SymbolApiResponse> {
    try {
      const response = await axios.get(`${API_BASE_URL}/data/symbols/${symbol}`);
      return response.data;
    } catch (error) {
      console.error('Symbol Details API Error:', error);
      throw error;
    }
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
