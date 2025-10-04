'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Portfolio, getPortfolio } from '@/services/portfolioApi';

export default function PortfolioDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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
          <div className="flex items-center space-x-4 mb-4">
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
                  {portfolio.portfolio_type === 'PERSONAL' ? 'Personnel' :
                   portfolio.portfolio_type === 'JOINT' ? 'Conjoint' :
                   portfolio.portfolio_type === 'CORPORATE' ? 'Entreprise' : 'Retraite'}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Statut</p>
                <p className="text-sm font-medium text-gray-900">
                  {portfolio.status === 'ACTIVE' ? 'Actif' :
                   portfolio.status === 'INACTIVE' ? 'Inactif' : 'Archivé'}
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
                <p className="text-sm text-gray-500">Rééquilibrage</p>
                <p className="text-sm font-medium text-gray-900">
                  {portfolio.rebalancing_frequency === 'MONTHLY' ? 'Mensuel' :
                   portfolio.rebalancing_frequency === 'QUARTERLY' ? 'Trimestriel' :
                   portfolio.rebalancing_frequency === 'SEMI_ANNUALLY' ? 'Semestriel' :
                   portfolio.rebalancing_frequency === 'ANNUALLY' ? 'Annuel' : 'Manuel'}
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

        {/* Objectifs et paramètres */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Objectifs d'investissement</h2>
            {portfolio.investment_goal ? (
              <p className="text-gray-700">{portfolio.investment_goal}</p>
            ) : (
              <p className="text-gray-500">Aucun objectif défini</p>
            )}
          </div>

          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Paramètres de risque</h2>
            <div className="space-y-3">
              {portfolio.target_return !== undefined && (
                <div>
                  <p className="text-sm text-gray-500">Rendement cible</p>
                  <p className="text-sm font-medium text-gray-900">{portfolio.target_return}%</p>
                </div>
              )}
              {portfolio.max_drawdown !== undefined && (
                <div>
                  <p className="text-sm text-gray-500">Drawdown maximum</p>
                  <p className="text-sm font-medium text-gray-900">{portfolio.max_drawdown}%</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Wallets */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Wallets</h2>
            <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors duration-200">
              Ajouter un wallet
            </button>
          </div>
          {portfolio.wallets && portfolio.wallets.length > 0 ? (
            <div className="space-y-4">
              {portfolio.wallets.map((wallet) => (
                <div key={wallet.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="font-medium text-gray-900">{wallet.name}</h3>
                      {wallet.description && (
                        <p className="text-sm text-gray-600 mt-1">{wallet.description}</p>
                      )}
                      <div className="flex space-x-4 mt-2 text-sm text-gray-500">
                        <span>{wallet.wallet_type}</span>
                        <span>{wallet.currency}</span>
                        <span>{wallet.status}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-semibold text-gray-900">
                        {new Intl.NumberFormat('fr-FR', {
                          style: 'currency',
                          currency: wallet.currency,
                        }).format(wallet.total_balance)}
                      </p>
                      <p className="text-sm text-gray-500">
                        Disponible: {new Intl.NumberFormat('fr-FR', {
                          style: 'currency',
                          currency: wallet.currency,
                        }).format(wallet.available_balance)}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">Aucun wallet configuré</p>
          )}
        </div>
      </div>
    </div>
  );
}
