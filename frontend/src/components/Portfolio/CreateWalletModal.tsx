'use client';

import { useState } from 'react';
import { createWallet, CreateWalletRequest } from '@/services/portfolioApi';

interface CreateWalletModalProps {
  isOpen: boolean;
  onClose: () => void;
  portfolioId: number;
  onWalletCreated: () => void;
}

const CreateWalletModal: React.FC<CreateWalletModalProps> = ({
  isOpen,
  onClose,
  portfolioId,
  onWalletCreated
}) => {
  const [formData, setFormData] = useState({
    name: '',
    currency: 'USD',
    initial_balance: 0
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const currencies = [
    { code: 'USD', name: 'Dollar américain' },
    { code: 'EUR', name: 'Euro' },
    { code: 'GBP', name: 'Livre sterling' },
    { code: 'CHF', name: 'Franc suisse' },
    { code: 'CAD', name: 'Dollar canadien' },
    { code: 'JPY', name: 'Yen japonais' }
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const walletData: CreateWalletRequest = {
        name: formData.name,
        currency: formData.currency,
        initial_balance: formData.initial_balance,
        wallet_type: 'CASH' // Type par défaut
      };

      await createWallet(portfolioId, walletData);
      onWalletCreated();
      onClose();
      
      // Reset form
      setFormData({
        name: '',
        currency: 'USD',
        initial_balance: 0
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la création du wallet');
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    if (!isLoading) {
      setError(null);
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900">
            Créer un nouveau wallet
          </h2>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4">
          {error && (
            <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          <div className="mb-4">
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Nom du wallet
            </label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="ex: Wallet USD Principal"
              required
            />
          </div>

          <div className="mb-4">
            <label htmlFor="currency" className="block text-sm font-medium text-gray-700 mb-2">
              Devise
            </label>
            <select
              id="currency"
              value={formData.currency}
              onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {currencies.map((currency) => (
                <option key={currency.code} value={currency.code}>
                  {currency.code} - {currency.name}
                </option>
              ))}
            </select>
          </div>

          <div className="mb-6">
            <label htmlFor="balance" className="block text-sm font-medium text-gray-700 mb-2">
              Solde initial (optionnel)
            </label>
            <input
              type="number"
              id="balance"
              step="0.01"
              min="0"
              value={formData.initial_balance}
              onChange={(e) => setFormData({ ...formData, initial_balance: parseFloat(e.target.value) || 0 })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="0.00"
            />
          </div>

          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={handleClose}
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:border-transparent disabled:opacity-50"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50"
            >
              {isLoading ? 'Création...' : 'Créer le wallet'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateWalletModal;
