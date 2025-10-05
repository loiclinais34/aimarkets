'use client';

import React from 'react';
import { Position } from '@/services/tradingApi';

interface PositionTableProps {
  positions: Position[];
  onViewDetails?: (position: Position) => void;
  onEdit?: (position: Position) => void;
}

export default function PositionTable({ positions, onViewDetails, onEdit }: PositionTableProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'USD', // Par défaut USD, pourrait être dynamique
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
    if (pnl > 0) return 'bg-green-50';
    if (pnl < 0) return 'bg-red-50';
    return 'bg-gray-50';
  };

  return (
    <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Titre
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Quantité
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Prix moyen
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Prix actuel
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Coût total
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Valeur actuelle
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                P&L non réalisé
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {positions.map((position) => (
              <tr key={position.id} className="hover:bg-gray-50">
                {/* Titre */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">{position.symbol}</div>
                    {position.company_name && (
                      <div className="text-sm text-gray-500">{position.company_name}</div>
                    )}
                  </div>
                </td>

                {/* Quantité */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {position.quantity.toLocaleString('fr-FR', { maximumFractionDigits: 6 })}
                  </div>
                </td>

                {/* Prix moyen */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {formatCurrency(position.average_cost)}
                  </div>
                </td>

                {/* Prix actuel */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {position.current_price ? formatCurrency(position.current_price) : 'N/A'}
                  </div>
                </td>

                {/* Coût total */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">
                    {formatCurrency(position.total_cost)}
                  </div>
                </td>

                {/* Valeur actuelle */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-semibold text-gray-900">
                    {formatCurrency(position.current_value)}
                  </div>
                </td>

                {/* P&L non réalisé */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className={`p-2 rounded-md ${getPnLBackgroundColor(position.unrealized_pnl)}`}>
                    <div className={`text-sm font-semibold ${getPnLColor(position.unrealized_pnl)}`}>
                      {formatCurrency(position.unrealized_pnl)}
                    </div>
                    <div className={`text-xs ${getPnLColor(position.unrealized_pnl)}`}>
                      {formatPercentage(position.unrealized_pnl_percentage)}
                    </div>
                  </div>
                </td>

                {/* Actions */}
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex space-x-2">
                    {onEdit && (
                      <button
                        onClick={() => onEdit(position)}
                        className="text-blue-600 hover:text-blue-900 hover:bg-blue-50 px-2 py-1 rounded-md transition-colors"
                      >
                        Modifier
                      </button>
                    )}
                    {onViewDetails && (
                      <button
                        onClick={() => onViewDetails(position)}
                        className="text-gray-600 hover:text-gray-900 hover:bg-gray-50 px-2 py-1 rounded-md transition-colors"
                      >
                        Détails
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
