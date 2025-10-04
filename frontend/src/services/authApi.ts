/**
 * Service API pour l'authentification
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api/v1';

export interface User {
  id: number;
  email: string;
  username: string;
  first_name: string;
  last_name: string;
  role: string;
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
  first_name: string;
  last_name: string;
}

export interface PasswordResetRequest {
  email: string;
}

export interface PasswordReset {
  token: string;
  new_password: string;
}

export interface PasswordChange {
  current_password: string;
  new_password: string;
}

export interface UserStats {
  user_id: number;
  email: string;
  username: string;
  role: string;
  is_active: boolean;
  active_sessions: number;
  created_at: string;
  last_login: string;
}

class AuthApiService {
  private getAuthHeaders(): HeadersInit {
    const token = localStorage.getItem('auth_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` }),
    };
  }

  /**
   * Inscription d'un nouvel utilisateur
   */
  async register(userData: RegisterRequest): Promise<{ user: User; message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de l\'inscription');
      }

      const user = await response.json();
      return { user, message: 'Inscription réussie' };
    } catch (error) {
      console.error('Erreur lors de l\'inscription:', error);
      throw error;
    }
  }

  /**
   * Connexion d'un utilisateur
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Email ou mot de passe incorrect');
      }

      const authResponse: AuthResponse = await response.json();
      
      // Stocker le token dans localStorage
      localStorage.setItem('auth_token', authResponse.access_token);
      localStorage.setItem('user', JSON.stringify(authResponse.user));
      
      return authResponse;
    } catch (error) {
      console.error('Erreur lors de la connexion:', error);
      throw error;
    }
  }

  /**
   * Déconnexion de l'utilisateur
   */
  async logout(): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });

      // Nettoyer le localStorage même si l'appel échoue
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');

      if (!response.ok) {
        console.warn('Erreur lors de la déconnexion côté serveur');
      }
    } catch (error) {
      console.error('Erreur lors de la déconnexion:', error);
      // Nettoyer quand même le localStorage
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user');
    }
  }

  /**
   * Récupérer les informations de l'utilisateur actuel
   */
  async getCurrentUser(): Promise<User> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/me`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        if (response.status === 401) {
          // Token invalide, nettoyer le localStorage
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          throw new Error('Session expirée');
        }
        throw new Error('Erreur lors de la récupération des informations utilisateur');
      }

      const user: User = await response.json();
      
      // Mettre à jour le localStorage
      localStorage.setItem('user', JSON.stringify(user));
      
      return user;
    } catch (error) {
      console.error('Erreur lors de la récupération de l\'utilisateur:', error);
      throw error;
    }
  }

  /**
   * Demander une réinitialisation de mot de passe
   */
  async requestPasswordReset(email: string): Promise<{ message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/password-reset-request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de la demande de réinitialisation');
      }

      const result = await response.json();
      return { message: result.message };
    } catch (error) {
      console.error('Erreur lors de la demande de réinitialisation:', error);
      throw error;
    }
  }

  /**
   * Réinitialiser le mot de passe avec un token
   */
  async resetPassword(token: string, newPassword: string): Promise<{ message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/password-reset`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token, new_password: newPassword }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Token invalide ou expiré');
      }

      const result = await response.json();
      return { message: result.message };
    } catch (error) {
      console.error('Erreur lors de la réinitialisation:', error);
      throw error;
    }
  }

  /**
   * Changer le mot de passe
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors du changement de mot de passe');
      }

      const result = await response.json();
      return { message: result.message };
    } catch (error) {
      console.error('Erreur lors du changement de mot de passe:', error);
      throw error;
    }
  }

  /**
   * Déconnecter de toutes les sessions
   */
  async logoutAllSessions(): Promise<{ message: string; revoked_sessions: number }> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/logout-all`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de la déconnexion de toutes les sessions');
      }

      const result = await response.json();
      return result;
    } catch (error) {
      console.error('Erreur lors de la déconnexion de toutes les sessions:', error);
      throw error;
    }
  }

  /**
   * Récupérer les statistiques de l'utilisateur
   */
  async getUserStats(): Promise<UserStats> {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/stats`, {
        method: 'GET',
        headers: this.getAuthHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Erreur lors de la récupération des statistiques');
      }

      const stats: UserStats = await response.json();
      return stats;
    } catch (error) {
      console.error('Erreur lors de la récupération des statistiques:', error);
      throw error;
    }
  }

  /**
   * Vérifier si l'utilisateur est authentifié
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('auth_token');
    const user = localStorage.getItem('user');
    return !!(token && user);
  }

  /**
   * Récupérer l'utilisateur depuis le localStorage
   */
  getStoredUser(): User | null {
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;
    
    try {
      return JSON.parse(userStr);
    } catch (error) {
      console.error('Erreur lors du parsing de l\'utilisateur stocké:', error);
      localStorage.removeItem('user');
      return null;
    }
  }

  /**
   * Récupérer le token d'authentification
   */
  getToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  /**
   * Nettoyer le localStorage
   */
  clearAuth(): void {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  }
}

export const authApi = new AuthApiService();
export default authApi;
