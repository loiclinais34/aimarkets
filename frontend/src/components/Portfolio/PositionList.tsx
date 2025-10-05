'use client';

import React, { useState, useEffect } from 'react';
import { Position, getPositions } from '@/services/positionApi';
import PositionCard from './PositionCard';
import BuySellModal from './BuySellModal';

interface PositionListProps {
  portfolioId: number;
  onRefresh?: () => void;
}

export default function PositionList({ portfolioId, onRefresh }: PositionListProps) {
  const [positions, setPositions] = useState<Position[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [buySellModal, setBuySellModal] = useState<{
    isOpen: boolean;
    mode: 'buy' | 'sell';
    symbol?: string;
    currentQuantity?: number;
    currentPrice?: number;
  }>({
    isOpen: false,
    mode: 'buy'
  });

  const fetchPositions = async () => {
    try {
      setIsLoading(true);
      setError('');
      const data = await getPositions(portfolioId);
      setPositions(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors du chargement des positions');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPositions();
  }, [portfolioId]);

  const handleBuyOrder = () => {
    setBuySellModal({
      isOpen: true,
      mode: 'buy'
    });
  };

  const handleSellOrder = (position: Position) => {
    setBuySellModal({
      isOpen: true,
      mode: 'sell',
      symbol: position.symbol,
      currentQuantity: position.quantity,
      currentPrice: position.current_price || 0
    });
  };

  const handleModalClose = () => {
    setBuySellModal({
      isOpen: false,
      mode: 'buy'
    });
  };

  const handleOrderSuccess = () => {
    fetchPositions();
    if (onRefresh) onRefresh();
  };

  const handleViewDetails = (position: Position) => {
    // TODO: Implement position details view
    console.log('View details for position:', position);
  };

  const handleEditPosition = (position: Position) => {
    // TODO: Implement position editing
    console.log('Edit position:', position);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Chargement des positions...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
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
            <div className="mt-3">
              <button
                onClick={fetchPositions}
                className="text-sm bg-red-100 text-red-800 hover:bg-red-200 px-3 py-1 rounded-md transition-colors"
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Positions</h2>
          <p className="text-gray-600">
            {positions.length} position{positions.length !== 1 ? 's' : ''} trouvée{positions.length !== 1 ? 's' : ''}
          </p>
        </div>
        <button
          onClick={handleBuyOrder}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Acheter des titres
        </button>
      </div>

      {/* Positions Grid */}
      {positions.length === 0 ? (
        <div className="text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">Aucune position</h3>
          <p className="mt-1 text-sm text-gray-500">
            Commencez par acheter des titres pour créer votre premier portefeuille.
          </p>
          <div className="mt-6">
            <button
              onClick={handleBuyOrder}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <svg className="-ml-1 mr-2 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              Acheter des titres
            </button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {positions.map((position) => (
            <PositionCard
              key={position.id}
              position={position}
              onViewDetails={handleViewDetails}
              onEdit={() => handleSellOrder(position)}
            />
          ))}
        </div>
      )}

      {/* Buy/Sell Modal */}
      <BuySellModal
        isOpen={buySellModal.isOpen}
        onClose={handleModalClose}
        onSuccess={handleOrderSuccess}
        portfolioId={portfolioId}
        mode={buySellModal.mode}
        symbol={buySellModal.symbol}
        currentQuantity={buySellModal.currentQuantity}
        currentPrice={buySellModal.currentPrice}
      />
    </div>
  );
}
