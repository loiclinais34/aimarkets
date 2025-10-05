'use client';

import React from 'react';
import { TrendingUp, TrendingDown, DollarSign } from 'lucide-react';
import { Position, formatCurrency, formatPercentage, getPnlColor, getPnlBgColor } from '@/services/tradingApi';

interface PositionCardProps {
  position: Position;
  onBuy: (position: Position) => void;
  onSell: (position: Position) => void;
}

export default function PositionCard({ position, onBuy, onSell }: PositionCardProps) {
  const isProfit = position.unrealized_pnl > 0;
  const isLoss = position.unrealized_pnl < 0;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{position.symbol}</h3>
          {position.company_name && (
            <p className="text-sm text-gray-600">{position.company_name}</p>
          )}
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${getPnlBgColor(position.unrealized_pnl)}`}>
          <span className={getPnlColor(position.unrealized_pnl)}>
            {isProfit && '+'}{formatCurrency(position.unrealized_pnl, position.currency)}
          </span>
        </div>
      </div>

      {/* Position Details */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-600">Quantité</p>
          <p className="font-medium">{position.quantity.toLocaleString('fr-FR', { maximumFractionDigits: 6 })}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Prix moyen</p>
          <p className="font-medium">{formatCurrency(position.average_cost, position.currency)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Prix actuel</p>
          <p className="font-medium">
            {position.current_price 
              ? formatCurrency(position.current_price, position.currency)
              : 'N/A'
            }
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Valeur totale</p>
          <p className="font-medium">{formatCurrency(position.current_value, position.currency)}</p>
        </div>
      </div>

      {/* Performance */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-sm text-gray-600">P&L Non Réalisé</p>
          <div className="flex items-center space-x-1">
            {isProfit && <TrendingUp className="w-4 h-4 text-green-600" />}
            {isLoss && <TrendingDown className="w-4 h-4 text-red-600" />}
            <span className={`font-medium ${getPnlColor(position.unrealized_pnl)}`}>
              {isProfit && '+'}{formatCurrency(position.unrealized_pnl, position.currency)}
            </span>
          </div>
          <p className={`text-sm ${getPnlColor(position.unrealized_pnl)}`}>
            {isProfit && '+'}{formatPercentage(position.unrealized_pnl_percentage)}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">P&L Réalisé</p>
          <div className="flex items-center space-x-1">
            {position.realized_pnl > 0 && <TrendingUp className="w-4 h-4 text-green-600" />}
            {position.realized_pnl < 0 && <TrendingDown className="w-4 h-4 text-red-600" />}
            <span className={`font-medium ${getPnlColor(position.realized_pnl)}`}>
              {position.realized_pnl > 0 && '+'}{formatCurrency(position.realized_pnl, position.currency)}
            </span>
          </div>
        </div>
      </div>

      {/* Additional Info */}
      <div className="grid grid-cols-2 gap-4 mb-4 text-sm text-gray-600">
        <div>
          <p>Coût total</p>
          <p className="font-medium">{formatCurrency(position.total_cost, position.currency)}</p>
        </div>
        <div>
          <p>Frais totaux</p>
          <p className="font-medium">{formatCurrency(position.total_fees, position.currency)}</p>
        </div>
      </div>

      {/* Dates */}
      <div className="text-xs text-gray-500 mb-4">
        {position.first_purchase_date && (
          <p>Premier achat: {new Date(position.first_purchase_date).toLocaleDateString('fr-FR')}</p>
        )}
        {position.last_purchase_date && (
          <p>Dernier achat: {new Date(position.last_purchase_date).toLocaleDateString('fr-FR')}</p>
        )}
        {position.last_sale_date && (
          <p>Dernière vente: {new Date(position.last_sale_date).toLocaleDateString('fr-FR')}</p>
        )}
      </div>

      {/* Actions */}
      <div className="flex space-x-2">
        <button
          onClick={() => onBuy(position)}
          className="flex-1 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors text-sm font-medium"
        >
          Acheter
        </button>
        <button
          onClick={() => onSell(position)}
          disabled={position.quantity <= 0}
          className="flex-1 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors text-sm font-medium"
        >
          Vendre
        </button>
      </div>
    </div>
  );
}
