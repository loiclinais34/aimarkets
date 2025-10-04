'use client';

import React, { useState, useEffect } from 'react';
import { Portfolio, getPortfolios, deletePortfolio } from '@/services/portfolioApi';
import { PortfolioCard } from './PortfolioCard';
import { CreatePortfolioModal } from './CreatePortfolioModal';
import { CreatePortfolioRequest, createPortfolio } from '@/services/portfolioApi';

interface PortfolioListProps {
  onPortfolioSelect?: (portfolio: Portfolio) => void;
}

export const PortfolioList: React.FC<PortfolioListProps> = ({ onPortfolioSelect }) => {
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isCreating, setIsCreating] = useState(false);

  const fetchPortfolios = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getPortfolios();
      setPortfolios(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors du chargement des portefeuilles');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolios();
  }, []);

  const handleCreatePortfolio = async (portfolioData: CreatePortfolioRequest) => {
    try {
      setIsCreating(true);
      await createPortfolio(portfolioData);
      await fetchPortfolios();
      setIsCreateModalOpen(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la création du portefeuille');
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeletePortfolio = async (portfolioId: number) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce portefeuille ? Cette action est irréversible.')) {
      return;
    }

    try {
      await deletePortfolio(portfolioId);
      await fetchPortfolios();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la suppression du portefeuille');
    }
  };

  const handleEditPortfolio = (portfolio: Portfolio) => {
    // TODO: Implémenter la modification de portefeuille
    console.log('Modifier portefeuille:', portfolio);
  };

  const handleViewDetails = (portfolio: Portfolio) => {
    if (onPortfolioSelect) {
      onPortfolioSelect(portfolio);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement des portefeuilles...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4 mx-4">
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
                onClick={fetchPortfolios}
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
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Mes Portefeuilles</h1>
          <p className="text-gray-600 mt-1">
            Gérez vos portefeuilles d'investissement
          </p>
        </div>
        <button
          onClick={() => setIsCreateModalOpen(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors duration-200 flex items-center space-x-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          <span>Nouveau portefeuille</span>
        </button>
      </div>

      {/* Liste des portefeuilles */}
      {portfolios.length === 0 ? (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Aucun portefeuille</h3>
          <p className="mt-1 text-sm text-gray-500">
            Commencez par créer votre premier portefeuille d'investissement.
          </p>
          <div className="mt-6">
            <button
              onClick={() => setIsCreateModalOpen(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors duration-200"
            >
              Créer un portefeuille
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {portfolios.map((portfolio) => (
            <PortfolioCard
              key={portfolio.id}
              portfolio={portfolio}
              onEdit={handleEditPortfolio}
              onDelete={handleDeletePortfolio}
              onViewDetails={handleViewDetails}
            />
          ))}
        </div>
      )}

      {/* Modal de création */}
      <CreatePortfolioModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreatePortfolio}
        isLoading={isCreating}
      />
    </div>
  );
};
