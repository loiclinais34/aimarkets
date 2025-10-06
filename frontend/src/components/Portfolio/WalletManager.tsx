'use client';

import React, { useState } from 'react';
import { Wallet, createWalletTransaction, CreateTransactionRequest } from '@/services/portfolioApi';
import { TransactionModal } from './TransactionModal';
import { TransactionHistory } from './TransactionHistory';
import CreateWalletModal from './CreateWalletModal';

interface WalletManagerProps {
  wallets: Wallet[];
  portfolioId: number;
  onWalletUpdate?: () => void;
}

export const WalletManager: React.FC<WalletManagerProps> = ({
  wallets,
  portfolioId,
  onWalletUpdate,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedWallet, setSelectedWallet] = useState<Wallet | null>(null);
  const [isTransactionModalOpen, setIsTransactionModalOpen] = useState(false);
  const [isTransactionHistoryOpen, setIsTransactionHistoryOpen] = useState(false);
  const [isProcessingTransaction, setIsProcessingTransaction] = useState(false);
  const [isCreateWalletModalOpen, setIsCreateWalletModalOpen] = useState(false);

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: currency,
    }).format(amount);
  };

  const getWalletTypeLabel = (type: string) => {
    switch (type) {
      case 'CASH': return 'Compte espèce';
      case 'MARGIN': return 'Compte marge';
      case 'CRYPTO': return 'Crypto-monnaies';
      default: return type;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'suspended': return 'bg-yellow-100 text-yellow-800';
      case 'closed': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'active': return 'Actif';
      case 'suspended': return 'Suspendu';
      case 'closed': return 'Fermé';
      default: return status;
    }
  };

  const handleTransaction = (wallet: Wallet) => {
    setSelectedWallet(wallet);
    setIsTransactionModalOpen(true);
  };

  const handleTransactionHistory = (wallet: Wallet) => {
    setSelectedWallet(wallet);
    setIsTransactionHistoryOpen(true);
  };

  const handleTransactionSubmit = async (data: CreateTransactionRequest) => {
    if (!selectedWallet) return;
    
    try {
      setIsProcessingTransaction(true);
      
      // Appeler l'API pour effectuer la transaction
      await createWalletTransaction(portfolioId, selectedWallet.id, data);
      
      setIsTransactionModalOpen(false);
      setIsProcessingTransaction(false);
      
      // Recharger les données du portefeuille
      if (onWalletUpdate) {
        onWalletUpdate();
      }
      
      alert('Transaction effectuée avec succès !');
    } catch (error) {
      console.error('Erreur lors de la transaction:', error);
      alert(`Erreur lors de la transaction: ${error instanceof Error ? error.message : 'Erreur inconnue'}`);
      setIsProcessingTransaction(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <div 
        className="flex justify-between items-center cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div>
          <h3 className="text-lg font-medium text-gray-900">Wallets ({wallets.length})</h3>
          <p className="text-sm text-gray-500">
            Gérer les comptes de ce portefeuille
          </p>
        </div>
        <button className="text-gray-400 hover:text-gray-600">
          <svg 
            className={`w-5 h-5 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {isExpanded && (
        <div className="mt-4 space-y-3">
          {/* Bouton pour créer un nouveau wallet */}
          <div className="flex justify-end">
            <button
              onClick={() => setIsCreateWalletModalOpen(true)}
              className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              + Nouveau wallet
            </button>
          </div>

          {wallets.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <p className="mt-2">Aucun wallet configuré</p>
            </div>
          ) : (
            wallets.map((wallet) => (
              <div key={wallet.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <h4 className="font-medium text-gray-900">{wallet.name}</h4>
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(wallet.status)}`}>
                        {getStatusLabel(wallet.status)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 mb-1">
                      {getWalletTypeLabel(wallet.wallet_type)} • {wallet.currency}
                    </p>
                    {wallet.description && (
                      <p className="text-sm text-gray-600 mb-2">{wallet.description}</p>
                    )}
                  </div>
                </div>
                
                <div className="mt-3 grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs font-medium text-gray-500 uppercase">Solde disponible</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatCurrency(Number(wallet.available_balance), wallet.currency)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-500 uppercase">Solde total</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatCurrency(Number(wallet.total_balance), wallet.currency)}
                    </p>
                  </div>
                </div>

                <div className="mt-3 flex space-x-2">
                  <button 
                    onClick={() => handleTransaction(wallet)}
                    className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors duration-200"
                  >
                    Transaction
                  </button>
                  <button 
                    onClick={() => handleTransactionHistory(wallet)}
                    className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors duration-200"
                  >
                    Historique
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Modal de transaction */}
      <TransactionModal
        isOpen={isTransactionModalOpen}
        onClose={() => setIsTransactionModalOpen(false)}
        onSubmit={handleTransactionSubmit}
        wallet={selectedWallet}
        portfolioId={portfolioId}
        isLoading={isProcessingTransaction}
      />

      {/* Modal d'historique des transactions */}
      {isTransactionHistoryOpen && selectedWallet && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden">
            <div className="flex justify-between items-center p-6 border-b">
              <h2 className="text-lg font-semibold text-gray-900">
                Historique des transactions - {selectedWallet.name}
              </h2>
              <button
                onClick={() => setIsTransactionHistoryOpen(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
              <TransactionHistory 
                wallet={selectedWallet}
                portfolioId={portfolioId}
                onTransactionAdded={() => {
                  if (onWalletUpdate) onWalletUpdate();
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Modal de création de wallet */}
      <CreateWalletModal
        isOpen={isCreateWalletModalOpen}
        onClose={() => setIsCreateWalletModalOpen(false)}
        portfolioId={portfolioId}
        onWalletCreated={() => {
          if (onWalletUpdate) onWalletUpdate();
        }}
      />
    </div>
  );
};
