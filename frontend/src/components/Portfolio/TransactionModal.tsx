'use client';

import React, { useState, useEffect } from 'react';
import { Wallet, getWallets } from '@/services/portfolioApi';

interface TransactionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: TransactionData) => void;
  wallet: Wallet | null;
  portfolioId: number;
  isLoading?: boolean;
}

interface TransactionData {
  transaction_type: 'DEPOSIT' | 'WITHDRAWAL' | 'TRANSFER';
  amount: number;
  description?: string;
  target_wallet_id?: number;
  exchange_rate?: number;
}

export const TransactionModal: React.FC<TransactionModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  wallet,
  portfolioId,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<TransactionData>({
    transaction_type: 'DEPOSIT',
    amount: 0,
    description: '',
    exchange_rate: 1.0,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [availableWallets, setAvailableWallets] = useState<Wallet[]>([]);
  const [loadingWallets, setLoadingWallets] = useState(false);

  // Charger les wallets du portefeuille
  useEffect(() => {
    const loadWallets = async () => {
      if (isOpen && portfolioId) {
        try {
          setLoadingWallets(true);
          const wallets = await getWallets(portfolioId);
          // Filtrer pour exclure le wallet source
          setAvailableWallets(wallets.filter(w => w.id !== wallet?.id));
        } catch (error) {
          console.error('Erreur lors du chargement des wallets:', error);
        } finally {
          setLoadingWallets(false);
        }
      }
    };

    loadWallets();
  }, [isOpen, portfolioId, wallet?.id]);

  useEffect(() => {
    if (isOpen) {
      setFormData({
        transaction_type: 'DEPOSIT',
        amount: 0,
        description: '',
        exchange_rate: 1.0,
      });
      setErrors({});
    }
  }, [isOpen]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (formData.amount <= 0) {
      newErrors.amount = 'Le montant doit être positif';
    }

    if (formData.transaction_type === 'WITHDRAWAL' && wallet && formData.amount > wallet.available_balance) {
      newErrors.amount = 'Montant insuffisant';
    }

    if (formData.transaction_type === 'TRANSFER' && !formData.target_wallet_id) {
      newErrors.target_wallet_id = 'Veuillez sélectionner un wallet de destination';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      onSubmit(formData);
    }
  };

  const handleClose = () => {
    setErrors({});
    onClose();
  };

  if (!isOpen || !wallet) {
    return null;
  }

  const selectedTargetWallet = availableWallets.find(w => w.id === formData.target_wallet_id);
  const isDifferentCurrency = selectedTargetWallet && selectedTargetWallet.currency !== wallet.currency;
  const convertedAmount = isDifferentCurrency && formData.exchange_rate 
    ? formData.amount * formData.exchange_rate 
    : formData.amount;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            Nouvelle transaction
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Wallet</span>
            <span className="font-medium">{wallet.name}</span>
          </div>
          <div className="flex justify-between items-center mt-1">
            <span className="text-sm text-gray-600">Solde disponible</span>
            <span className="font-semibold text-green-600">
              {new Intl.NumberFormat('fr-FR', {
                style: 'currency',
                currency: wallet.currency,
              }).format(wallet.available_balance)}
            </span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Type de transaction */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Type de transaction
            </label>
            <select
              value={formData.transaction_type}
              onChange={(e) => setFormData({ ...formData, transaction_type: e.target.value as any })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="DEPOSIT">Dépôt</option>
              <option value="WITHDRAWAL">Retrait</option>
              <option value="TRANSFER">Virement</option>
            </select>
          </div>

          {/* Montant */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Montant ({wallet.currency})
            </label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={formData.amount || ''}
              onChange={(e) => setFormData({ ...formData, amount: parseFloat(e.target.value) || 0 })}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.amount ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="0.00"
            />
            {errors.amount && (
              <p className="mt-1 text-sm text-red-600">{errors.amount}</p>
            )}
          </div>

          {/* Wallet de destination (pour les virements) */}
          {formData.transaction_type === 'TRANSFER' && (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Wallet de destination
                </label>
                <select
                  value={formData.target_wallet_id || ''}
                  onChange={(e) => setFormData({ ...formData, target_wallet_id: parseInt(e.target.value) })}
                  className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                    errors.target_wallet_id ? 'border-red-500' : 'border-gray-300'
                  }`}
                  disabled={loadingWallets}
                >
                  <option value="">Sélectionner un wallet</option>
                  {availableWallets.map((w) => (
                    <option key={w.id} value={w.id}>
                      {w.name} ({w.currency}) - {new Intl.NumberFormat('fr-FR', {
                        style: 'currency',
                        currency: w.currency,
                      }).format(w.available_balance)}
                    </option>
                  ))}
                </select>
                {errors.target_wallet_id && (
                  <p className="mt-1 text-sm text-red-600">{errors.target_wallet_id}</p>
                )}
              </div>

              {/* Taux de change (pour les virements entre devises différentes) */}
              {isDifferentCurrency && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Taux de change ({wallet.currency} → {selectedTargetWallet.currency})
                  </label>
                  <input
                    type="number"
                    step="0.000001"
                    min="0"
                    value={formData.exchange_rate || ''}
                    onChange={(e) => setFormData({ ...formData, exchange_rate: parseFloat(e.target.value) || 1.0 })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    placeholder="1.0"
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    {formData.amount} {wallet.currency} = {convertedAmount.toFixed(2)} {selectedTargetWallet.currency}
                  </p>
                </div>
              )}
            </>
          )}

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Description (optionnel)
            </label>
            <textarea
              value={formData.description || ''}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={3}
              placeholder="Description de la transaction..."
            />
          </div>

          {/* Résumé de la transaction */}
          <div className="p-3 bg-blue-50 rounded-lg">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Résumé</h4>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between">
                <span className="text-blue-700">Type:</span>
                <span className="text-blue-900">
                  {formData.transaction_type === 'DEPOSIT' ? 'Dépôt' :
                   formData.transaction_type === 'WITHDRAWAL' ? 'Retrait' : 'Virement'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-blue-700">Montant:</span>
                <span className="text-blue-900">
                  {new Intl.NumberFormat('fr-FR', {
                    style: 'currency',
                    currency: wallet.currency,
                  }).format(formData.amount)}
                </span>
              </div>
              {formData.transaction_type === 'TRANSFER' && isDifferentCurrency && (
                <>
                  <div className="flex justify-between">
                    <span className="text-blue-700">Taux:</span>
                    <span className="text-blue-900">
                      1 {wallet.currency} = {formData.exchange_rate?.toFixed(6)} {selectedTargetWallet.currency}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-blue-700">Montant converti:</span>
                    <span className="text-blue-900 font-semibold">
                      {new Intl.NumberFormat('fr-FR', {
                        style: 'currency',
                        currency: selectedTargetWallet.currency,
                      }).format(convertedAmount)}
                    </span>
                  </div>
                </>
              )}
              {formData.transaction_type === 'DEPOSIT' && (
                <div className="flex justify-between">
                  <span className="text-blue-700">Nouveau solde:</span>
                  <span className="text-blue-900 font-semibold">
                    {new Intl.NumberFormat('fr-FR', {
                      style: 'currency',
                      currency: wallet.currency,
                    }).format(wallet.available_balance + formData.amount)}
                  </span>
                </div>
              )}
              {formData.transaction_type === 'WITHDRAWAL' && (
                <div className="flex justify-between">
                  <span className="text-blue-700">Nouveau solde:</span>
                  <span className="text-blue-900 font-semibold">
                    {new Intl.NumberFormat('fr-FR', {
                      style: 'currency',
                      currency: wallet.currency,
                    }).format(wallet.available_balance - formData.amount)}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Boutons */}
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors duration-200"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              {isLoading ? 'En cours...' : 'Confirmer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
