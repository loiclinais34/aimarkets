'use client';

import React from 'react';
import { Portfolio } from '@/services/portfolioApi';

interface PortfolioCardProps {
  portfolio: Portfolio;
  onEdit: (portfolio: Portfolio) => void;
  onDelete: (portfolioId: number) => void;
  onViewDetails: (portfolio: Portfolio) => void;
}

export const PortfolioCard: React.FC<PortfolioCardProps> = ({
  portfolio,
  onEdit,
  onDelete,
  onViewDetails,
}) => {
  const getPortfolioTypeColor = (type: string) => {
    switch (type) {
      case 'PERSONAL':
        return 'bg-blue-100 text-blue-800';
      case 'JOINT':
        return 'bg-green-100 text-green-800';
      case 'CORPORATE':
        return 'bg-purple-100 text-purple-800';
      case 'RETIREMENT':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-green-100 text-green-800';
      case 'INACTIVE':
        return 'bg-yellow-100 text-yellow-800';
      case 'ARCHIVED':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRiskToleranceColor = (risk: string) => {
    switch (risk) {
      case 'CONSERVATIVE':
        return 'text-green-600';
      case 'MODERATE':
        return 'text-yellow-600';
      case 'AGGRESSIVE':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6 hover:shadow-lg transition-shadow duration-200">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 mb-1">{portfolio.name}</h3>
          {portfolio.description && (
            <p className="text-sm text-gray-600 mb-2">{portfolio.description}</p>
          )}
        </div>
        <div className="flex space-x-2">
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPortfolioTypeColor(
              portfolio.portfolio_type
            )}`}
          >
            {portfolio.portfolio_type === 'PERSONAL' ? 'Personnel' :
             portfolio.portfolio_type === 'JOINT' ? 'Conjoint' :
             portfolio.portfolio_type === 'CORPORATE' ? 'Entreprise' : 'Retraite'}
          </span>
          <span
            className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
              portfolio.status
            )}`}
          >
            {portfolio.status === 'ACTIVE' ? 'Actif' :
             portfolio.status === 'INACTIVE' ? 'Inactif' : 'Archivé'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">Tolérance au risque</p>
          <p className={`text-sm font-medium ${getRiskToleranceColor(portfolio.risk_tolerance)}`}>
            {portfolio.risk_tolerance === 'CONSERVATIVE' ? 'Conservateur' :
             portfolio.risk_tolerance === 'MODERATE' ? 'Modéré' : 'Agressif'}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">Rééquilibrage</p>
          <p className="text-sm font-medium text-gray-900">
            {portfolio.rebalancing_frequency === 'MONTHLY' ? 'Mensuel' :
             portfolio.rebalancing_frequency === 'QUARTERLY' ? 'Trimestriel' :
             portfolio.rebalancing_frequency === 'SEMI_ANNUALLY' ? 'Semestriel' :
             portfolio.rebalancing_frequency === 'ANNUALLY' ? 'Annuel' : 'Manuel'}
          </p>
        </div>
      </div>

      {portfolio.total_value !== undefined && (
        <div className="mb-4">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-500">Valeur totale</span>
            <span className="text-lg font-semibold text-gray-900">
              {new Intl.NumberFormat('fr-FR', {
                style: 'currency',
                currency: 'EUR',
              }).format(portfolio.total_value)}
            </span>
          </div>
          {portfolio.total_pnl !== undefined && (
            <div className="flex justify-between items-center mt-1">
              <span className="text-sm text-gray-500">P&L</span>
              <span
                className={`text-sm font-medium ${
                  portfolio.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {new Intl.NumberFormat('fr-FR', {
                  style: 'currency',
                  currency: 'EUR',
                }).format(portfolio.total_pnl)}
                {portfolio.total_pnl_percent !== undefined && (
                  <span className="ml-1">
                    ({portfolio.total_pnl_percent >= 0 ? '+' : ''}
                    {portfolio.total_pnl_percent.toFixed(2)}%)
                  </span>
                )}
              </span>
            </div>
          )}
        </div>
      )}

      <div className="flex justify-between items-center text-xs text-gray-500 mb-4">
        <span>
          {portfolio.wallets?.length || 0} wallet{portfolio.wallets?.length !== 1 ? 's' : ''}
        </span>
        <span>
          Créé le {new Date(portfolio.created_at).toLocaleDateString('fr-FR')}
        </span>
      </div>

      <div className="flex space-x-2">
        <button
          onClick={() => onViewDetails(portfolio)}
          className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors duration-200"
        >
          Voir détails
        </button>
        <button
          onClick={() => onEdit(portfolio)}
          className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md text-sm font-medium hover:bg-gray-50 transition-colors duration-200"
        >
          Modifier
        </button>
        <button
          onClick={() => onDelete(portfolio.id)}
          className="px-4 py-2 border border-red-300 text-red-700 rounded-md text-sm font-medium hover:bg-red-50 transition-colors duration-200"
        >
          Supprimer
        </button>
      </div>
    </div>
  );
};
