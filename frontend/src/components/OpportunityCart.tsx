'use client';

import React, { useState, useEffect } from 'react';
import { 
  ShoppingCartIcon, 
  XMarkIcon, 
  TrashIcon,
  ChartBarIcon,
  EyeIcon
} from '@heroicons/react/24/outline';

interface Opportunity {
  symbol: string;
  company_name: string;
  prediction: number;
  confidence: number;
  model_id: number;
  model_name: string;
  target_return: number;
  time_horizon: number;
  rank: number;
  prediction_date: string | null;
  screener_run_id: number;
}

interface OpportunityCartProps {
  className?: string;
}

export default function OpportunityCart({ className = '' }: OpportunityCartProps) {
  const [cart, setCart] = useState<Opportunity[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  // Charger le panier depuis localStorage au montage
  useEffect(() => {
    const loadCart = () => {
      const savedCart = localStorage.getItem('opportunity-cart');
      if (savedCart) {
        try {
          setCart(JSON.parse(savedCart));
        } catch (error) {
          console.error('Erreur lors du chargement du panier:', error);
        }
      }
    };

    loadCart();

    // Écouter les changements de localStorage
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'opportunity-cart') {
        loadCart();
      }
    };

    // Écouter les événements personnalisés
    const handleCartUpdate = () => {
      loadCart();
    };

    window.addEventListener('storage', handleStorageChange);
    window.addEventListener('cartUpdated', handleCartUpdate);

    return () => {
      window.removeEventListener('storage', handleStorageChange);
      window.removeEventListener('cartUpdated', handleCartUpdate);
    };
  }, []);

  // Sauvegarder le panier dans localStorage à chaque changement
  useEffect(() => {
    localStorage.setItem('opportunity-cart', JSON.stringify(cart));
  }, [cart]);

  const addToCart = (opportunity: Opportunity) => {
    setCart(prev => {
      // Vérifier si l'opportunité n'est pas déjà dans le panier
      const exists = prev.some(item => 
        item.symbol === opportunity.symbol && 
        item.model_id === opportunity.model_id
      );
      
      if (!exists) {
        return [...prev, opportunity];
      }
      return prev;
    });
  };

  const removeFromCart = (opportunity: Opportunity) => {
    setCart(prev => prev.filter(item => 
      !(item.symbol === opportunity.symbol && item.model_id === opportunity.model_id)
    ));
  };

  const clearCart = () => {
    setCart([]);
  };

  const formatModelName = (modelName: string) => {
    if (modelName.includes('xgboost')) return 'XGBoost';
    if (modelName.includes('lightgbm')) return 'LightGBM';
    if (modelName.includes('randomforest')) return 'RandomForest';
    if (modelName.includes('neural')) return 'Neural Network';
    return 'ML Model';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 bg-green-100';
    if (confidence >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getConfidenceLabel = (confidence: number) => {
    if (confidence >= 0.8) return 'Élevée';
    if (confidence >= 0.6) return 'Moyenne';
    return 'Faible';
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Récent';
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    });
  };

  const totalValue = cart.reduce((sum, item) => sum + item.target_return, 0);
  const averageConfidence = cart.length > 0 
    ? cart.reduce((sum, item) => sum + item.confidence, 0) / cart.length 
    : 0;

  return (
    <>
      {/* Bouton du panier */}
      <div className={`relative ${className}`}>
        <button
          onClick={() => setIsOpen(true)}
          className="relative p-2 text-gray-600 hover:text-blue-600 transition-colors"
        >
          <ShoppingCartIcon className="h-6 w-6" />
          {cart.length > 0 && (
            <span className="absolute -top-1 -right-1 bg-blue-600 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
              {cart.length}
            </span>
          )}
        </button>
      </div>

      {/* Modal du panier */}
      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] flex flex-col">
            {/* En-tête */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Panier d'Opportunités
                </h3>
                <p className="text-sm text-gray-500">
                  {cart.length} opportunité{cart.length > 1 ? 's' : ''} sélectionnée{cart.length > 1 ? 's' : ''}
                </p>
              </div>
              <div className="flex items-center space-x-2">
                {cart.length > 0 && (
                  <button
                    onClick={clearCart}
                    className="text-sm text-red-600 hover:text-red-800"
                  >
                    Vider le panier
                  </button>
                )}
                <button
                  onClick={() => setIsOpen(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>
            </div>

            {/* Contenu scrollable */}
            <div className="p-6 flex-1 overflow-y-auto">
              {cart.length === 0 ? (
                <div className="text-center py-12">
                  <ShoppingCartIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">Panier vide</h4>
                  <p className="text-gray-500">
                    Ajoutez des opportunités à votre panier pour les analyser
                  </p>
                </div>
              ) : (
                <>
                  {/* Statistiques du panier */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                    <div className="bg-blue-50 p-4 rounded-lg">
                      <div className="text-sm text-blue-600 font-medium">Rendement Total</div>
                      <div className="text-2xl font-bold text-blue-900">
                        {totalValue.toFixed(1)}%
                      </div>
                    </div>
                    <div className="bg-green-50 p-4 rounded-lg">
                      <div className="text-sm text-green-600 font-medium">Confiance Moyenne</div>
                      <div className="text-2xl font-bold text-green-900">
                        {(averageConfidence * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="bg-purple-50 p-4 rounded-lg">
                      <div className="text-sm text-purple-600 font-medium">Symboles Uniques</div>
                      <div className="text-2xl font-bold text-purple-900">
                        {new Set(cart.map(item => item.symbol)).size}
                      </div>
                    </div>
                  </div>

                  {/* Liste des opportunités */}
                  <div className="space-y-3">
                    {cart.map((opportunity, index) => (
                      <div key={`${opportunity.symbol}-${opportunity.model_id}-${index}`} className="p-4 border border-gray-200 rounded-lg">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <div className="flex-shrink-0">
                              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                <span className="text-xs font-semibold text-blue-600">
                                  {opportunity.symbol}
                                </span>
                              </div>
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="text-sm font-medium text-gray-900">
                                {opportunity.company_name}
                              </div>
                              <div className="text-xs text-gray-500">
                                {formatModelName(opportunity.model_name)} • {opportunity.target_return}% sur {opportunity.time_horizon} jours
                                {opportunity.prediction_date && (
                                  <span className="ml-2">• {formatDate(opportunity.prediction_date)}</span>
                                )}
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center space-x-3">
                            <div className="text-right">
                              <div className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getConfidenceColor(opportunity.confidence)}`}>
                                {getConfidenceLabel(opportunity.confidence)}
                              </div>
                              <div className="text-xs text-gray-500 mt-1">
                                {(opportunity.confidence * 100).toFixed(1)}%
                              </div>
                            </div>
                            <button
                              onClick={() => removeFromCart(opportunity)}
                              className="text-red-400 hover:text-red-600"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </div>

            {/* Pied de page */}
            {cart.length > 0 && (
              <div className="p-6 border-t border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-500">
                    Prêt pour l'analyse détaillée
                  </div>
                  <button
                    onClick={() => {
                      setIsOpen(false);
                      // Navigation vers la page d'analyse
                      window.location.href = '/analysis';
                    }}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <ChartBarIcon className="h-4 w-4 mr-2" />
                    Analyser les opportunités
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}

// Export de la fonction pour ajouter au panier
export const addOpportunityToCart = (opportunity: Opportunity) => {
  const savedCart = localStorage.getItem('opportunity-cart');
  let cart: Opportunity[] = [];
  
  if (savedCart) {
    try {
      cart = JSON.parse(savedCart);
    } catch (error) {
      console.error('Erreur lors du chargement du panier:', error);
    }
  }
  
  // Vérifier si l'opportunité n'est pas déjà dans le panier
  const exists = cart.some(item => 
    item.symbol === opportunity.symbol && 
    item.model_id === opportunity.model_id
  );
  
  if (!exists) {
    cart.push(opportunity);
    localStorage.setItem('opportunity-cart', JSON.stringify(cart));
    
    // Déclencher un événement personnalisé pour notifier les composants
    window.dispatchEvent(new CustomEvent('cartUpdated'));
    
    return true; // Ajouté avec succès
  }
  
  return false; // Déjà dans le panier
};
