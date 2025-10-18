'use client';

import React, { useState, useEffect } from 'react';
import { X, TrendingUp, TrendingDown, Search } from 'lucide-react';
import { buyStock, sellStock, BuyStockRequest, SellStockRequest, formatCurrency } from '@/services/tradingApi';
import { getWallets, Wallet } from '@/services/portfolioApi';
import { symbolsApi, Symbol } from '@/services/symbolsApi';

interface TradingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  portfolioId: number;
  mode: 'buy' | 'sell';
  symbol?: string;
  currentPrice?: number;
  availableQuantity?: number;
}

export default function TradingModal({
  isOpen,
  onClose,
  onSuccess,
  portfolioId,
  mode,
  symbol = '',
  currentPrice = 0,
  availableQuantity = 0
}: TradingModalProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [wallets, setWallets] = useState<Wallet[]>([]);
  const [symbols, setSymbols] = useState<Symbol[]>([]);
  const [symbolSearch, setSymbolSearch] = useState('');
  const [showSymbolSearch, setShowSymbolSearch] = useState(false);
  
  const [formData, setFormData] = useState({
    wallet_id: 0,
    symbol: symbol,
    quantity: 0,
    price: currentPrice,
    fees: 0,
    description: '',
    target_wallet_id: 0  // Wallet de destination pour les ventes
  });

  // Charger les wallets
  useEffect(() => {
    if (isOpen && portfolioId) {
      loadWallets();
      loadSymbols();
    }
  }, [isOpen, portfolioId]);

  // Réinitialiser le formulaire
  useEffect(() => {
    if (isOpen) {
      setFormData({
        wallet_id: wallets[0]?.id || 0,
        symbol: symbol,
        quantity: mode === 'sell' ? (availableQuantity || 0) : 0,
        price: currentPrice,
        fees: 0,
        description: '',
        target_wallet_id: wallets.find(w => w.currency === 'USD')?.id || wallets[0]?.id || 0
      });
      setError(null);
      setSuccess(null);
    }
  }, [isOpen, symbol, currentPrice, wallets, mode, availableQuantity]);

  const loadWallets = async () => {
    try {
      const walletsData = await getWallets(portfolioId);
      setWallets(walletsData);
    } catch (error) {
      console.error('Erreur lors du chargement des wallets:', error);
    }
  };

  const loadSymbols = async () => {
    try {
      const symbolsData = await symbolsApi.getSymbols('', 100);
      setSymbols(symbolsData);
    } catch (error) {
      console.error('Erreur lors du chargement des symboles:', error);
    }
  };

  // Recherche de symboles en temps réel
  useEffect(() => {
    const searchSymbols = async () => {
      if (symbolSearch.length > 1) {
        try {
          const results = await symbolsApi.searchSymbols(symbolSearch);
          setSymbols(results);
        } catch (error) {
          console.error('Erreur lors de la recherche de symboles:', error);
        }
      } else if (symbolSearch.length === 0) {
        loadSymbols();
      }
    };

    const timeoutId = setTimeout(searchSymbols, 300);
    return () => clearTimeout(timeoutId);
  }, [symbolSearch]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'wallet_id' ? parseInt(value) : 
              name === 'quantity' || name === 'price' || name === 'fees' ? parseFloat(value) || 0 :
              value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    try {
      if (mode === 'buy') {
        const request: BuyStockRequest = {
          wallet_id: formData.wallet_id,
          symbol: formData.symbol,
          quantity: formData.quantity,
          price: formData.price,
          fees: formData.fees,
          description: formData.description
        };

        const result = await buyStock(portfolioId, request);
        setSuccess(result.message);
      } else {
        const request: SellStockRequest = {
          wallet_id: formData.wallet_id,
          symbol: formData.symbol,
          quantity: formData.quantity,
          price: formData.price,
          fees: formData.fees,
          description: formData.description,
          target_wallet_id: formData.target_wallet_id || undefined
        };

        const result = await sellStock(portfolioId, request);
        setSuccess(result.message);
      }

      setTimeout(() => {
        onSuccess();
        onClose();
      }, 1500);

    } catch (error: any) {
      setError(error.message || 'Une erreur est survenue');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  const selectedWallet = wallets.find(w => w.id === formData.wallet_id);
  const totalCost = mode === 'buy' ? (formData.quantity * formData.price) + formData.fees : 0;
  const totalProceeds = mode === 'sell' ? (formData.quantity * formData.price) - formData.fees : 0;
  const maxQuantity = mode === 'sell' ? availableQuantity : 
                     selectedWallet ? selectedWallet.available_balance / formData.price : 0;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b sticky top-0 bg-white z-10">
          <div className="flex items-center space-x-2">
            {mode === 'buy' ? (
              <TrendingUp className="w-5 h-5 text-green-600" />
            ) : (
              <TrendingDown className="w-5 h-5 text-red-600" />
            )}
            <h2 className="text-xl font-semibold text-gray-900">
              {mode === 'buy' ? 'Acheter' : 'Vendre'} {symbol}
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Row 1: Wallet & Symbol */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Wallet Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {mode === 'sell' ? 'Wallet de la position' : 'Wallet'}
              </label>
              <select
                name="wallet_id"
                value={formData.wallet_id}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value={0}>Sélectionner un wallet</option>
                {wallets.map(wallet => (
                  <option key={wallet.id} value={wallet.id}>
                    {wallet.currency} - {formatCurrency(wallet.available_balance, wallet.currency)} disponible
                  </option>
                ))}
              </select>
            </div>

            {/* Target Wallet Selection (only for sell mode) */}
            {mode === 'sell' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Wallet de destination
                </label>
                <select
                  name="target_wallet_id"
                  value={formData.target_wallet_id}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value={0}>Sélectionner un wallet de destination</option>
                  {wallets.map(wallet => (
                    <option key={wallet.id} value={wallet.id}>
                      {wallet.currency} - {formatCurrency(wallet.available_balance, wallet.currency)} disponible
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  Le produit de la vente sera crédité sur ce wallet
                </p>
              </div>
            )}

            {/* Symbol */}
            <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Symbole
            </label>
            
            {mode === 'sell' ? (
              /* En mode vente, afficher le symbole en lecture seule */
              <div className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-900">
                {symbol || 'Aucun symbole sélectionné'}
              </div>
            ) : (
              /* En mode achat, permettre la recherche */
              <div className="relative">
                <input
                  type="text"
                  placeholder="Rechercher un symbole..."
                  value={symbolSearch}
                  onChange={(e) => setSymbolSearch(e.target.value)}
                  className="w-full px-3 py-2 pl-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  onFocus={() => setShowSymbolSearch(true)}
                />
                <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" />
              </div>
            )}

            {/* Symbol Dropdown */}
            {showSymbolSearch && (
              <div className="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-y-auto">
                {symbols.length > 0 ? (
                  symbols.map((symbol) => (
                    <div
                      key={symbol.symbol}
                      className="px-3 py-2 hover:bg-gray-100 cursor-pointer flex justify-between items-center"
                      onClick={() => {
                        setFormData(prev => ({ ...prev, symbol: symbol.symbol }));
                        setSymbolSearch('');
                        setShowSymbolSearch(false);
                      }}
                    >
                      <div>
                        <span className="font-medium text-gray-900">{symbol.symbol}</span>
                        <span className="text-gray-600 ml-2">{symbol.company_name}</span>
                      </div>
                      {symbol.sector && (
                        <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                          {symbol.sector}
                        </span>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="px-3 py-2 text-gray-500">
                    {symbolSearch.length > 1 ? 'Aucun symbole trouvé' : 'Tapez pour rechercher...'}
                  </div>
                )}
              </div>
            )}

            {/* Selected Symbol Display */}
            {formData.symbol && (
              <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded-md">
                <div className="flex justify-between items-center">
                  <div>
                    <span className="font-medium text-blue-900">{formData.symbol}</span>
                    {symbols.find(s => s.symbol === formData.symbol) && (
                      <span className="text-blue-700 ml-2">
                        {symbols.find(s => s.symbol === formData.symbol)?.company_name}
                      </span>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setFormData(prev => ({ ...prev, symbol: '' }));
                      setSymbolSearch('');
                    }}
                    className="text-blue-600 hover:text-blue-800"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Click outside to close dropdown */}
            {showSymbolSearch && (
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowSymbolSearch(false)}
              />
            )}
            </div>
          </div>

          {/* Row 2: Quantity, Price, Fees */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Quantity */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Quantité
              </label>
              <input
                type="number"
                name="quantity"
                value={formData.quantity}
                onChange={handleInputChange}
                min="0"
                max={maxQuantity}
                step="0.000001"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                {mode === 'sell' ? `Disponible: ${availableQuantity?.toLocaleString('fr-FR', { maximumFractionDigits: 6 }) || 0}` : 'Max: ∞'}
              </p>
              {mode === 'sell' && availableQuantity && availableQuantity > 0 && (
                <div className="flex space-x-2 mt-2">
                  <button
                    type="button"
                    onClick={() => setFormData(prev => ({ ...prev, quantity: availableQuantity * 0.25 }))}
                    className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                  >
                    25%
                  </button>
                  <button
                    type="button"
                    onClick={() => setFormData(prev => ({ ...prev, quantity: availableQuantity * 0.5 }))}
                    className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                  >
                    50%
                  </button>
                  <button
                    type="button"
                    onClick={() => setFormData(prev => ({ ...prev, quantity: availableQuantity * 0.75 }))}
                    className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                  >
                    75%
                  </button>
                  <button
                    type="button"
                    onClick={() => setFormData(prev => ({ ...prev, quantity: availableQuantity }))}
                    className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
                  >
                    100%
                  </button>
                </div>
              )}
            </div>

            {/* Price */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Prix unitaire
              </label>
              <input
                type="number"
                name="price"
                value={formData.price}
                onChange={handleInputChange}
                min="0"
                step="0.01"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            {/* Fees */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Frais
              </label>
              <input
                type="number"
                name="fees"
                value={formData.fees}
                onChange={handleInputChange}
                min="0"
                step="0.01"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Row 3: Description & Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Description (optionnel)
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
              />
            </div>

            {/* Summary */}
            <div>
              <h3 className="block text-sm font-medium text-gray-900 mb-2">Résumé</h3>
              <div className="bg-gray-50 p-4 rounded-md h-[calc(100%-2rem)]">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Quantité:</span>
                    <span className="font-medium">{formData.quantity.toLocaleString('fr-FR', { maximumFractionDigits: 6 })}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Prix unitaire:</span>
                    <span className="font-medium">{formatCurrency(formData.price, selectedWallet?.currency || 'USD')}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Frais:</span>
                    <span className="font-medium">{formatCurrency(formData.fees, selectedWallet?.currency || 'USD')}</span>
                  </div>
                  <div className="flex justify-between font-semibold border-t border-gray-300 pt-2 mt-2">
                    <span>{mode === 'buy' ? 'Coût total:' : 'Produit net:'}</span>
                    <span className={mode === 'buy' ? 'text-green-600' : 'text-red-600'}>
                      {formatCurrency(mode === 'buy' ? totalCost : totalProceeds, selectedWallet?.currency || 'USD')}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              {error}
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md">
              {success}
            </div>
          )}

          {/* Actions */}
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors"
              disabled={isLoading}
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={isLoading || formData.wallet_id === 0 || formData.quantity <= 0 || (mode === 'sell' && formData.target_wallet_id === 0)}
              className={`flex-1 px-4 py-2 rounded-md text-white transition-colors ${
                mode === 'buy' 
                  ? 'bg-green-600 hover:bg-green-700 disabled:bg-green-300' 
                  : 'bg-red-600 hover:bg-red-700 disabled:bg-red-300'
              }`}
            >
              {isLoading ? 'En cours...' : (mode === 'buy' ? 'Acheter' : 'Vendre')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
