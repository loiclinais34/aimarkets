'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Portfolio, getPortfolio, updatePortfolio, UpdatePortfolioRequest } from '@/services/portfolioApi';
import { EditPortfolioModal } from '@/components/Portfolio/EditPortfolioModal';
import { WalletManager } from '@/components/Portfolio/WalletManager';

export default function PortfolioDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  const portfolioId = parseInt(params.id as string);

  useEffect(() => {
    const fetchPortfolio = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const data = await getPortfolio(portfolioId);
        setPortfolio(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Erreur lors du chargement du portefeuille');
      } finally {
        setIsLoading(false);
      }
    };

    if (portfolioId) {
      fetchPortfolio();
    }
  }, [portfolioId]);

  const handleUpdatePortfolio = async (data: UpdatePortfolioRequest) => {
    if (!portfolio) return;
    
    try {
      setIsUpdating(true);
      await updatePortfolio(portfolio.id, data);
      // Recharger les données du portefeuille
      const updatedPortfolio = await getPortfolio(portfolioId);
      setPortfolio(updatedPortfolio);
      setIsEditModalOpen(false);
    } catch (err) {
      console.error('Erreur lors de la mise à jour:', err);
      alert('Erreur lors de la mise à jour du portefeuille');
    } finally {
      setIsUpdating(false);
    }
  };

  const handleWalletUpdate = async () => {
    // Recharger les données du portefeuille quand un wallet est modifié
    try {
      const updatedPortfolio = await getPortfolio(portfolioId);
      setPortfolio(updatedPortfolio);
    } catch (err) {
      console.error('Erreur lors du rechargement:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement du portefeuille...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-red-50 border border-red-200 rounded-md p-6 max-w-md w-full mx-4">
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
                  onClick={() => router.push('/portfolios')}
                  className="bg-red-100 text-red-800 px-3 py-1 rounded-md text-sm hover:bg-red-200 transition-colors duration-200"
                >
                  Retour aux portefeuilles
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!portfolio) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Portefeuille non trouvé</h1>
          <p className="text-gray-600 mb-6">Le portefeuille demandé n'existe pas.</p>
          <button
            onClick={() => router.push('/portfolios')}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors duration-200"
          >
            Retour aux portefeuilles
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* En-tête */}
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/portfolios')}
                className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <h1 className="text-3xl font-bold text-gray-900">{portfolio.name}</h1>
            </div>
            <button
              onClick={() => setIsEditModalOpen(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors duration-200 flex items-center space-x-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              <span>Modifier</span>
            </button>
          </div>
          {portfolio.description && (
            <p className="text-gray-600 ml-10">{portfolio.description}</p>
          )}
        </div>

        {/* Informations principales */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Carte principale */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Informations générales</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-500">Type</p>
                <p className="text-sm font-medium text-gray-900">
                  {portfolio.portfolio_type === 'personal' ? 'Personnel' :
                   portfolio.portfolio_type === 'joint' ? 'Conjoint' :
                   portfolio.portfolio_type === 'corporate' ? 'Entreprise' : 'Retraite'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Statut</p>
                <p className="text-sm font-medium text-gray-900">
                  {portfolio.status === 'active' ? 'Actif' :
                   portfolio.status === 'paused' ? 'En pause' : 'Fermé'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Tolérance au risque</p>
                <p className="text-sm font-medium text-gray-900">
                  {portfolio.risk_tolerance === 'CONSERVATIVE' ? 'Conservateur' :
                   portfolio.risk_tolerance === 'MODERATE' ? 'Modéré' : 'Agressif'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Capital initial</p>
                <p className="text-sm font-medium text-gray-900">
                  {new Intl.NumberFormat('fr-FR', {
                    style: 'currency',
                    currency: 'EUR',
                  }).format(portfolio.initial_capital || 0)}
                </p>
              </div>
            </div>
          </div>

          {/* Valeur du portefeuille */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Valeur du portefeuille</h2>
            {portfolio.total_value !== undefined ? (
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Valeur totale</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {new Intl.NumberFormat('fr-FR', {
                      style: 'currency',
                      currency: 'EUR',
                    }).format(portfolio.total_value)}
                  </p>
                </div>
                {portfolio.total_pnl !== undefined && (
                  <div>
                    <p className="text-sm text-gray-500">P&L</p>
                    <p className={`text-lg font-semibold ${
                      portfolio.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {new Intl.NumberFormat('fr-FR', {
                        style: 'currency',
                        currency: 'EUR',
                      }).format(portfolio.total_pnl)}
                      {portfolio.total_pnl_percent !== undefined && (
                        <span className="ml-2 text-sm">
                          ({portfolio.total_pnl_percent >= 0 ? '+' : ''}
                          {portfolio.total_pnl_percent.toFixed(2)}%)
                        </span>
                      )}
                    </p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500">Aucune donnée de valeur disponible</p>
            )}
          </div>
        </div>

        {/* Wallets */}
        <div className="mb-8">
          <WalletManager 
            wallets={portfolio.wallets || []} 
            portfolioId={portfolio.id}
            onWalletUpdate={handleWalletUpdate}
          />
        </div>
      </div>

      {/* Modal d'édition */}
      <EditPortfolioModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        onSave={handleUpdatePortfolio}
        portfolio={portfolio}
        isLoading={isUpdating}
      />
    </div>
  );
}
