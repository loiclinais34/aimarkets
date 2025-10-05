/**
 * Hook pour calculer la valorisation des portefeuilles
 */

import { useState, useEffect, useCallback } from 'react';
import { Portfolio, Position } from '../services/portfolioApi';
import { getPricesMap } from '../services/latestPricesApi';

export interface PortfolioValuation {
  portfolio: Portfolio;
  totalValue: number;
  totalCost: number;
  totalPnL: number;
  totalPnLPercent: number;
  positionsWithValuation: PositionWithValuation[];
  lastUpdated: Date;
  isLoading: boolean;
  error: string | null;
}

export interface PositionWithValuation extends Position {
  currentValuation: number;
  pnl: number;
  pnlPercent: number;
  lastPrice?: number;
  lastPriceDate?: string;
}

export function usePortfolioValuation(portfolio: Portfolio): PortfolioValuation {
  const [valuation, setValuation] = useState<PortfolioValuation>({
    portfolio,
    totalValue: 0,
    totalCost: 0,
    totalPnL: 0,
    totalPnLPercent: 0,
    positionsWithValuation: [],
    lastUpdated: new Date(),
    isLoading: true,
    error: null,
  });

  const calculateValuation = useCallback(async () => {
    if (!portfolio.positions || portfolio.positions.length === 0) {
      setValuation(prev => ({
        ...prev,
        totalValue: portfolio.initial_capital || 0,
        totalCost: portfolio.initial_capital || 0,
        totalPnL: 0,
        totalPnLPercent: 0,
        positionsWithValuation: [],
        isLoading: false,
        error: null,
      }));
      return;
    }

    try {
      setValuation(prev => ({ ...prev, isLoading: true, error: null }));

      // Extraire les symboles des positions
      const symbols = portfolio.positions.map(pos => pos.symbol);
      
      // Récupérer les derniers cours
      const pricesMap = await getPricesMap(symbols);
      
      // Calculer la valorisation pour chaque position
      const positionsWithValuation: PositionWithValuation[] = portfolio.positions.map(position => {
        const currentPrice = pricesMap[position.symbol] || position.current_price || 0;
        const currentValuation = position.quantity * currentPrice;
        const pnl = currentValuation - position.total_cost;
        const pnlPercent = position.total_cost > 0 ? (pnl / position.total_cost) * 100 : 0;

        return {
          ...position,
          currentValuation,
          pnl,
          pnlPercent,
          lastPrice: currentPrice,
          lastPriceDate: new Date().toISOString(),
        };
      });

      // Calculer les totaux
      const totalValue = positionsWithValuation.reduce((sum, pos) => sum + pos.currentValuation, 0);
      const totalCost = positionsWithValuation.reduce((sum, pos) => sum + pos.total_cost, 0);
      const totalPnL = totalValue - totalCost;
      const totalPnLPercent = totalCost > 0 ? (totalPnL / totalCost) * 100 : 0;

      setValuation({
        portfolio,
        totalValue,
        totalCost,
        totalPnL,
        totalPnLPercent,
        positionsWithValuation,
        lastUpdated: new Date(),
        isLoading: false,
        error: null,
      });

    } catch (error) {
      console.error('Erreur lors du calcul de la valorisation:', error);
      setValuation(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Erreur inconnue',
      }));
    }
  }, [portfolio]);

  // Recalculer la valorisation quand le portefeuille change
  useEffect(() => {
    calculateValuation();
  }, [calculateValuation]);

  // Recalculer la valorisation toutes les 5 minutes
  useEffect(() => {
    const interval = setInterval(calculateValuation, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [calculateValuation]);

  return valuation;
}

/**
 * Hook pour calculer la valorisation de plusieurs portefeuilles
 */
export function usePortfoliosValuation(portfolios: Portfolio[]): PortfolioValuation[] {
  const [valuations, setValuations] = useState<PortfolioValuation[]>([]);

  useEffect(() => {
    // Créer les valuations initiales
    const initialValuations: PortfolioValuation[] = portfolios.map(portfolio => ({
      portfolio,
      totalValue: 0,
      totalCost: 0,
      totalPnL: 0,
      totalPnLPercent: 0,
      positionsWithValuation: [],
      lastUpdated: new Date(),
      isLoading: true,
      error: null,
    }));

    setValuations(initialValuations);
  }, [portfolios]);

  // Calculer la valorisation pour chaque portefeuille
  useEffect(() => {
    const calculateAllValuations = async () => {
      for (let i = 0; i < portfolios.length; i++) {
        const portfolio = portfolios[i];
        if (!portfolio.positions || portfolio.positions.length === 0) {
          setValuations(prev => prev.map((val, idx) => 
            idx === i ? {
              ...val,
              totalValue: portfolio.initial_capital || 0,
              totalCost: portfolio.initial_capital || 0,
              totalPnL: 0,
              totalPnLPercent: 0,
              positionsWithValuation: [],
              isLoading: false,
              error: null,
            } : val
          ));
          continue;
        }

        try {
          setValuations(prev => prev.map((val, idx) => 
            idx === i ? { ...val, isLoading: true, error: null } : val
          ));

          const symbols = portfolio.positions.map(pos => pos.symbol);
          const pricesMap = await getPricesMap(symbols);
          
          const positionsWithValuation: PositionWithValuation[] = portfolio.positions.map(position => {
            const currentPrice = pricesMap[position.symbol] || position.current_price || 0;
            const currentValuation = position.quantity * currentPrice;
            const pnl = currentValuation - position.total_cost;
            const pnlPercent = position.total_cost > 0 ? (pnl / position.total_cost) * 100 : 0;

            return {
              ...position,
              currentValuation,
              pnl,
              pnlPercent,
              lastPrice: currentPrice,
              lastPriceDate: new Date().toISOString(),
            };
          });

          const totalValue = positionsWithValuation.reduce((sum, pos) => sum + pos.currentValuation, 0);
          const totalCost = positionsWithValuation.reduce((sum, pos) => sum + pos.total_cost, 0);
          const totalPnL = totalValue - totalCost;
          const totalPnLPercent = totalCost > 0 ? (totalPnL / totalCost) * 100 : 0;

          setValuations(prev => prev.map((val, idx) => 
            idx === i ? {
              ...val,
              totalValue,
              totalCost,
              totalPnL,
              totalPnLPercent,
              positionsWithValuation,
              lastUpdated: new Date(),
              isLoading: false,
              error: null,
            } : val
          ));

        } catch (error) {
          console.error(`Erreur lors du calcul de la valorisation pour le portefeuille ${portfolio.id}:`, error);
          setValuations(prev => prev.map((val, idx) => 
            idx === i ? {
              ...val,
              isLoading: false,
              error: error instanceof Error ? error.message : 'Erreur inconnue',
            } : val
          ));
        }
      }
    };

    calculateAllValuations();
  }, [portfolios]);

  return valuations;
}
