'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Plus, History, TrendingUp } from 'lucide-react';
import { getPositions, getTradingHistory, Position, WalletTransaction } from '@/services/tradingApi';
import { getPortfolio } from '@/services/portfolioApi';
import PositionCard from '@/components/Trading/PositionCard';
import TradingModal from '@/components/Trading/TradingModal';
import { formatCurrency } from '@/services/tradingApi';

export default function TradingPage() {
  const params = useParams();
  const router = useRouter();
  const portfolioId = parseInt(params.id as string);

  const [portfolio, setPortfolio] = useState<any>(null);
  const [positions, setPositions] = useState<Position[]>([]);
  const [tradingHistory, setTradingHistory] = useState<WalletTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'positions' | 'history'>('positions');
  
  // Modal states
  const [isTradingModalOpen, setIsTradingModalOpen] = useState(false);
  const [tradingMode, setTradingMode] = useState<'buy' | 'sell'>('buy');
  const [selectedPosition, setSelectedPosition] = useState<Position | null>(null);

  useEffect(() => {
    if (portfolioId) {
      loadData();
    }
  }, [portfolioId]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Charger le portfolio
      const portfolioData = await getPortfolio(portfolioId);
      setPortfolio(portfolioData);

      // Charger les positions
      const positionsData = await getPositions(portfolioId);
      setPositions(positionsData);

      // Charger l'historique
      const historyData = await getTradingHistory(portfolioId);
      setTradingHistory(historyData);

    } catch (error: any) {
      console.error('Erreur lors du chargement des données:', error);
      setError(error.message || 'Erreur lors du chargement des données');
    } finally {
      setIsLoading(false);
    }
  };

  const handleTradingSuccess = () => {
    // Recharger les données après une transaction réussie
    loadData();
  };

  const handleBuy = (position: Position | null = null) => {
    setSelectedPosition(position);
    setTradingMode('buy');
    setIsTradingModalOpen(true);
  };

  const handleSell = (position: Position | null = null) => {
    setSelectedPosition(position);
    setTradingMode('sell');
    setIsTradingModalOpen(true);
  };

  const closeTradingModal = () => {
    setIsTradingModalOpen(false);
    setSelectedPosition(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error}
        </div>
      </div>
    );
  }

  const totalValue = positions.reduce((sum, pos) => sum + pos.current_value, 0);
  const totalPnL = positions.reduce((sum, pos) => sum + pos.unrealized_pnl, 0);

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Trading - {portfolio?.name}
            </h1>
            <p className="text-gray-600">Gestion des positions et du trading</p>
          </div>
          <button
            onClick={() => handleBuy()}
            className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors flex items-center space-x-2"
          >
            <Plus className="w-4 h-4" />
            <span>Acheter</span>
          </button>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <p className="text-sm text-gray-600">Valeur totale</p>
            <p className="text-2xl font-bold">{formatCurrency(totalValue, 'USD')}</p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <p className="text-sm text-gray-600">P&L Non Réalisé</p>
            <p className={`text-2xl font-bold ${totalPnL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {totalPnL >= 0 ? '+' : ''}{formatCurrency(totalPnL, 'USD')}
            </p>
          </div>
          <div className="bg-white p-4 rounded-lg shadow-sm border">
            <p className="text-sm text-gray-600">Nombre de positions</p>
            <p className="text-2xl font-bold">{positions.length}</p>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            <button
              onClick={() => setActiveTab('positions')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'positions'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <TrendingUp className="w-4 h-4 inline mr-2" />
              Positions ({positions.length})
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'history'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <History className="w-4 h-4 inline mr-2" />
              Historique ({tradingHistory.length})
            </button>
          </nav>
        </div>
      </div>

      {/* Content */}
      {activeTab === 'positions' && (
        <div>
          {positions.length === 0 ? (
            <div className="text-center py-12">
              <TrendingUp className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Aucune position</h3>
              <p className="text-gray-600 mb-4">Commencez par acheter des titres</p>
              <button
                onClick={() => handleBuy()}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
              >
                Premier achat
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {positions.map(position => (
                <PositionCard
                  key={position.id}
                  position={position}
                  onBuy={() => handleBuy(position)}
                  onSell={() => handleSell(position)}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'history' && (
        <div>
          {tradingHistory.length === 0 ? (
            <div className="text-center py-12">
              <History className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Aucun historique</h3>
              <p className="text-gray-600">Vos transactions apparaîtront ici</p>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Date
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Type
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Symbole
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quantité
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Prix
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Montant
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Solde après
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {tradingHistory.map(transaction => (
                      <tr key={transaction.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {new Date(transaction.created_at).toLocaleDateString('fr-FR')}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                            transaction.transaction_type === 'BUY_STOCK' 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {transaction.transaction_type === 'BUY_STOCK' ? 'Achat' : 'Vente'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {transaction.symbol}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {transaction.quantity?.toLocaleString('fr-FR', { maximumFractionDigits: 6 }) || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {transaction.price ? formatCurrency(transaction.price, 'USD') : '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          <span className={transaction.amount >= 0 ? 'text-green-600' : 'text-red-600'}>
                            {transaction.amount >= 0 ? '+' : ''}{formatCurrency(transaction.amount, 'USD')}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatCurrency(transaction.balance_after, 'USD')}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Trading Modal */}
      <TradingModal
        isOpen={isTradingModalOpen}
        onClose={closeTradingModal}
        onSuccess={handleTradingSuccess}
        portfolioId={portfolioId}
        mode={tradingMode}
        symbol={selectedPosition?.symbol}
        currentPrice={selectedPosition?.current_price}
        availableQuantity={selectedPosition?.quantity}
      />
    </div>
  );
}
