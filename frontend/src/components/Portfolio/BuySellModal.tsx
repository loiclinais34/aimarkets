'use client';

import React, { useState, useEffect } from 'react';
import { BuyOrderRequest, SellOrderRequest, executeBuyOrder, executeSellOrder } from '@/services/positionApi';

interface BuySellModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: () => void;
  portfolioId: number;
  mode: 'buy' | 'sell';
  symbol?: string;
  currentQuantity?: number;
  currentPrice?: number;
}

export default function BuySellModal({
  isOpen,
  onClose,
  onSuccess,
  portfolioId,
  mode,
  symbol = '',
  currentQuantity = 0,
  currentPrice = 0
}: BuySellModalProps) {
  const [formData, setFormData] = useState({
    symbol: symbol,
    quantity: 0,
    price: currentPrice,
    fee: 0,
    currency: 'USD'
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      setFormData({
        symbol: symbol,
        quantity: 0,
        price: currentPrice,
        fee: 0,
        currency: 'USD'
      });
      setError('');
    }
  }, [isOpen, symbol, currentPrice]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'quantity' || name === 'price' || name === 'fee' 
        ? parseFloat(value) || 0 
        : value
    }));
  };

  const calculateTotal = () => {
    if (mode === 'buy') {
      return (formData.quantity * formData.price) + formData.fee;
    } else {
      return (formData.quantity * formData.price) - formData.fee;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      if (mode === 'buy') {
        const order: BuyOrderRequest = {
          symbol: formData.symbol,
          quantity: formData.quantity,
          price: formData.price,
          fee: formData.fee,
          currency: formData.currency
        };
        await executeBuyOrder(portfolioId, order);
      } else {
        const order: SellOrderRequest = {
          symbol: formData.symbol,
          quantity: formData.quantity,
          price: formData.price,
          fee: formData.fee
        };
        await executeSellOrder(portfolioId, order);
      }
      
      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Une erreur est survenue');
    } finally {
      setIsLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-gray-900">
              {mode === 'buy' ? 'Acheter' : 'Vendre'} des titres
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Current Position Info (for sell mode) */}
          {mode === 'sell' && currentQuantity > 0 && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800">
                Position actuelle: {currentQuantity.toLocaleString('fr-FR')} titres
              </p>
              {currentPrice > 0 && (
                <p className="text-sm text-blue-800">
                  Prix actuel: {new Intl.NumberFormat('fr-FR', {
                    style: 'currency',
                    currency: 'USD'
                  }).format(currentPrice)}
                </p>
              )}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Symbol */}
            <div>
              <label htmlFor="symbol" className="block text-sm font-medium text-gray-700 mb-1">
                Symbole
              </label>
              <input
                type="text"
                id="symbol"
                name="symbol"
                value={formData.symbol}
                onChange={handleInputChange}
                required
                disabled={symbol !== ''}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100"
                placeholder="Ex: AAPL"
              />
            </div>

            {/* Quantity */}
            <div>
              <label htmlFor="quantity" className="block text-sm font-medium text-gray-700 mb-1">
                Quantité
              </label>
              <input
                type="number"
                id="quantity"
                name="quantity"
                value={formData.quantity}
                onChange={handleInputChange}
                required
                min="0"
                step="0.000001"
                max={mode === 'sell' ? currentQuantity : undefined}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0"
              />
              {mode === 'sell' && currentQuantity > 0 && (
                <p className="text-xs text-gray-500 mt-1">
                  Maximum: {currentQuantity.toLocaleString('fr-FR')}
                </p>
              )}
            </div>

            {/* Price */}
            <div>
              <label htmlFor="price" className="block text-sm font-medium text-gray-700 mb-1">
                Prix par titre
              </label>
              <input
                type="number"
                id="price"
                name="price"
                value={formData.price}
                onChange={handleInputChange}
                required
                min="0"
                step="0.01"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0.00"
              />
            </div>

            {/* Fee */}
            <div>
              <label htmlFor="fee" className="block text-sm font-medium text-gray-700 mb-1">
                Frais
              </label>
              <input
                type="number"
                id="fee"
                name="fee"
                value={formData.fee}
                onChange={handleInputChange}
                min="0"
                step="0.01"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="0.00"
              />
            </div>

            {/* Currency (buy mode only) */}
            {mode === 'buy' && (
              <div>
                <label htmlFor="currency" className="block text-sm font-medium text-gray-700 mb-1">
                  Devise
                </label>
                <select
                  id="currency"
                  name="currency"
                  value={formData.currency}
                  onChange={(e) => setFormData(prev => ({ ...prev, currency: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="USD">USD</option>
                  <option value="EUR">EUR</option>
                  <option value="GBP">GBP</option>
                </select>
              </div>
            )}

            {/* Total Calculation */}
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg">
              <div className="flex justify-between items-center">
                <span className="font-medium text-gray-700">
                  {mode === 'buy' ? 'Coût total' : 'Montant net'}
                </span>
                <span className="text-lg font-bold text-gray-900">
                  {new Intl.NumberFormat('fr-FR', {
                    style: 'currency',
                    currency: formData.currency
                  }).format(calculateTotal())}
                </span>
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
              >
                Annuler
              </button>
              <button
                type="submit"
                disabled={isLoading || formData.quantity <= 0 || formData.price <= 0}
                className="flex-1 px-4 py-2 text-white bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 rounded-md transition-colors"
              >
                {isLoading ? 'En cours...' : (mode === 'buy' ? 'Acheter' : 'Vendre')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
