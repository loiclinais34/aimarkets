'use client';

import React, { useState, useEffect } from 'react';
import { Wallet, WalletTransaction, getWalletTransactions } from '@/services/portfolioApi';

interface TransactionHistoryProps {
  wallet: Wallet | null;
  portfolioId: number;
  onTransactionAdded?: () => void;
}

export const TransactionHistory: React.FC<TransactionHistoryProps> = ({
  wallet,
  portfolioId,
  onTransactionAdded,
}) => {
  const [transactions, setTransactions] = useState<WalletTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<'ALL' | 'DEPOSIT' | 'WITHDRAWAL' | 'TRANSFER'>('ALL');

  const fetchTransactions = async () => {
    if (!wallet) return;

    try {
      setIsLoading(true);
      setError(null);
      
      // Appeler l'API pour récupérer les transactions
      const response = await getWalletTransactions(portfolioId, wallet.id);
      setTransactions(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors du chargement des transactions');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTransactions();
  }, [wallet]);

  const getTransactionTypeLabel = (type: string) => {
    switch (type) {
      case 'DEPOSIT':
        return 'Dépôt';
      case 'WITHDRAWAL':
        return 'Retrait';
      case 'TRANSFER':
        return 'Virement';
      default:
        return type;
    }
  };

  const getTransactionTypeColor = (type: string) => {
    switch (type) {
      case 'DEPOSIT':
        return 'bg-green-100 text-green-800';
      case 'WITHDRAWAL':
        return 'bg-red-100 text-red-800';
      case 'TRANSFER':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getAmountColor = (type: string, amount: number) => {
    if (type === 'DEPOSIT') {
      return 'text-green-600';
    } else if (type === 'WITHDRAWAL') {
      return 'text-red-600';
    } else {
      return 'text-blue-600';
    }
  };

  const getAmountPrefix = (type: string) => {
    switch (type) {
      case 'DEPOSIT':
        return '+';
      case 'WITHDRAWAL':
        return '-';
      case 'TRANSFER':
        return '±';
      default:
        return '';
    }
  };

  const filteredTransactions = transactions.filter(transaction => {
    if (filter === 'ALL') return true;
    return transaction.transaction_type === filter;
  });

  if (!wallet) {
    return (
      <div className="text-center py-8 text-gray-500">
        Sélectionnez un wallet pour voir l'historique des transactions
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement des transactions...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Erreur</h3>
            <div className="mt-2 text-sm text-red-700">
              <p>{error}</p>
            </div>
            <div className="mt-4">
              <button
                onClick={fetchTransactions}
                className="bg-red-100 text-red-800 px-3 py-1 rounded-md text-sm hover:bg-red-200 transition-colors duration-200"
              >
                Réessayer
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* En-tête avec filtres */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">
          Historique des transactions
        </h3>
        <div className="flex space-x-2">
          {(['ALL', 'DEPOSIT', 'WITHDRAWAL', 'TRANSFER'] as const).map((filterType) => (
            <button
              key={filterType}
              onClick={() => setFilter(filterType)}
              className={`px-3 py-1 rounded-md text-sm transition-colors duration-200 ${
                filter === filterType
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {filterType === 'ALL' ? 'Toutes' : getTransactionTypeLabel(filterType)}
            </button>
          ))}
        </div>
      </div>

      {/* Liste des transactions */}
      {filteredTransactions.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p>Aucune transaction trouvée</p>
          <p className="text-sm">Les transactions apparaîtront ici une fois effectuées</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="divide-y divide-gray-200">
            {filteredTransactions.map((transaction) => (
              <div key={transaction.id} className="p-4 hover:bg-gray-50 transition-colors duration-200">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getTransactionTypeColor(
                          transaction.transaction_type
                        )}`}
                      >
                        {getTransactionTypeLabel(transaction.transaction_type)}
                      </span>
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {transaction.description || 'Transaction'}
                        </p>
                        <p className="text-xs text-gray-500">
                          {new Date(transaction.created_at).toLocaleDateString('fr-FR', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </p>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className={`text-sm font-semibold ${getAmountColor(transaction.transaction_type, transaction.amount)}`}>
                      {getAmountPrefix(transaction.transaction_type)}
                      {new Intl.NumberFormat('fr-FR', {
                        style: 'currency',
                        currency: wallet.currency,
                      }).format(transaction.amount)}
                    </p>
                    <p className="text-xs text-gray-500">
                      Solde: {new Intl.NumberFormat('fr-FR', {
                        style: 'currency',
                        currency: wallet.currency,
                      }).format(transaction.balance_after)}
                    </p>
                  </div>
                </div>
                {transaction.reference && (
                  <div className="mt-2">
                    <p className="text-xs text-gray-500">
                      Référence: {transaction.reference}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Statistiques */}
      {transactions.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-green-800">Total dépôts</p>
                <p className="text-lg font-semibold text-green-900">
                  {new Intl.NumberFormat('fr-FR', {
                    style: 'currency',
                    currency: wallet.currency,
                  }).format(
                    transactions
                      .filter(t => t.transaction_type === 'DEPOSIT')
                      .reduce((sum, t) => sum + t.amount, 0)
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-red-50 p-4 rounded-lg">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-red-800">Total retraits</p>
                <p className="text-lg font-semibold text-red-900">
                  {new Intl.NumberFormat('fr-FR', {
                    style: 'currency',
                    currency: wallet.currency,
                  }).format(
                    transactions
                      .filter(t => t.transaction_type === 'WITHDRAWAL')
                      .reduce((sum, t) => sum + t.amount, 0)
                  )}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm font-medium text-blue-800">Nombre de transactions</p>
                <p className="text-lg font-semibold text-blue-900">
                  {transactions.length}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
