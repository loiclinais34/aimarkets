'use client';

import React from 'react';
import { Position } from '@/services/tradingApi';

interface PositionCardProps {
  position: Position;
  onViewDetails?: (position: Position) => void;
  onEdit?: (position: Position) => void;
}

export default function PositionCard({ position, onViewDetails, onEdit }: PositionCardProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: position.currency,
      minimumFractionDigits: 2,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'percent',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value / 100);
  };

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-green-600';
    if (pnl < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getPnLBackgroundColor = (pnl: number) => {
    if (pnl > 0) return 'bg-green-50 border-green-200';
    if (pnl < 0) return 'bg-red-50 border-red-200';
    return 'bg-gray-50 border-gray-200';
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">{position.symbol}</h3>
            {position.company_name && (
              <p className="text-sm text-gray-600">{position.company_name}</p>
            )}
          </div>
        </div>

        {/* Position Details */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-sm text-gray-600">Quantité</p>
            <p className="text-lg font-semibold text-gray-900">
              {position.quantity.toLocaleString('fr-FR', { maximumFractionDigits: 6 })}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Prix moyen</p>
            <p className="text-lg font-semibold text-gray-900">
              {formatCurrency(position.average_cost)}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Prix actuel</p>
            <p className="text-lg font-semibold text-gray-900">
              {position.current_price ? formatCurrency(position.current_price) : 'N/A'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Coût total</p>
            <p className="text-lg font-semibold text-gray-900">
              {formatCurrency(position.total_cost)}
            </p>
          </div>
        </div>

        {/* Performance */}
        <div className={`p-4 rounded-lg border ${getPnLBackgroundColor(position.unrealized_pnl)}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Valeur actuelle</p>
              <p className="text-xl font-bold text-gray-900">
                {formatCurrency(position.current_value)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">P&L non réalisé</p>
              <p className={`text-xl font-bold ${getPnLColor(position.unrealized_pnl)}`}>
                {formatCurrency(position.unrealized_pnl)}
              </p>
              <p className={`text-sm ${getPnLColor(position.unrealized_pnl)}`}>
                {formatPercentage(position.unrealized_pnl_percentage)}
              </p>
            </div>
          </div>
        </div>

        {/* P&L Réalisé */}
        {position.realized_pnl !== 0 && (
          <div className="mt-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <p className="text-sm text-gray-600">P&L réalisé</p>
              <p className={`font-semibold ${getPnLColor(position.realized_pnl)}`}>
                {formatCurrency(position.realized_pnl)}
              </p>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between mt-6 pt-4 border-t border-gray-200">
          <div className="text-xs text-gray-500">
            Créé le {new Date(position.created_at).toLocaleDateString('fr-FR')}
          </div>
          <div className="flex space-x-2">
            {onEdit && (
              <button
                onClick={() => onEdit(position)}
                className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-md transition-colors"
              >
                Modifier
              </button>
            )}
            {onViewDetails && (
              <button
                onClick={() => onViewDetails(position)}
                className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-50 rounded-md transition-colors"
              >
                Détails →
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
