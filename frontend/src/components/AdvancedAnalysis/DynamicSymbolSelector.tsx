// frontend/src/components/AdvancedAnalysis/DynamicSymbolSelector.tsx
'use client';

import React, { useState, useEffect, useRef } from 'react';
import { MagnifyingGlassIcon, ChevronDownIcon } from '@heroicons/react/24/outline';

interface SymbolData {
  symbol: string;
  company_name: string;
  sector: string;
}

interface DynamicSymbolSelectorProps {
  onSymbolSelect: (symbol: string, companyName: string) => void;
  placeholder?: string;
  className?: string;
}

const DynamicSymbolSelector: React.FC<DynamicSymbolSelectorProps> = ({
  onSymbolSelect,
  placeholder = "Rechercher un symbole ou une entreprise...",
  className = ""
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [symbols, setSymbols] = useState<SymbolData[]>([]);
  const [filteredSymbols, setFilteredSymbols] = useState<SymbolData[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState<SymbolData | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Charger les symboles populaires au montage
  useEffect(() => {
    loadPopularSymbols();
  }, []);

  // Gestion de la recherche en temps réel
  useEffect(() => {
    if (searchQuery.length > 1) {
      searchSymbols(searchQuery);
    } else if (searchQuery.length === 0) {
      setFilteredSymbols(symbols);
    }
  }, [searchQuery, symbols]);

  // Fermer le dropdown en cliquant à l'extérieur
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const loadPopularSymbols = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/data/symbols?limit=20');
      if (response.ok) {
        const data = await response.json();
        setSymbols(data);
        setFilteredSymbols(data);
      }
    } catch (error) {
      console.error('Erreur lors du chargement des symboles:', error);
      // Fallback avec des symboles statiques
      const fallbackSymbols: SymbolData[] = [
        { symbol: 'AAPL', company_name: 'Apple Inc.', sector: 'Technology' },
        { symbol: 'MSFT', company_name: 'Microsoft Corporation', sector: 'Technology' },
        { symbol: 'GOOGL', company_name: 'Alphabet Inc.', sector: 'Technology' },
        { symbol: 'AMZN', company_name: 'Amazon.com Inc.', sector: 'Consumer Discretionary' },
        { symbol: 'TSLA', company_name: 'Tesla Inc.', sector: 'Consumer Discretionary' },
        { symbol: 'NVDA', company_name: 'NVIDIA Corporation', sector: 'Technology' },
        { symbol: 'META', company_name: 'Meta Platforms Inc.', sector: 'Communication Services' },
        { symbol: 'NFLX', company_name: 'Netflix Inc.', sector: 'Communication Services' }
      ];
      setSymbols(fallbackSymbols);
      setFilteredSymbols(fallbackSymbols);
    } finally {
      setLoading(false);
    }
  };

  const searchSymbols = async (query: string) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/data/symbols?search=${encodeURIComponent(query)}&limit=20`);
      if (response.ok) {
        const data = await response.json();
        setFilteredSymbols(data);
      }
    } catch (error) {
      console.error('Erreur lors de la recherche:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSymbolSelect = (symbolData: SymbolData) => {
    setSelectedSymbol(symbolData);
    setSearchQuery('');
    setIsOpen(false);
    onSymbolSelect(symbolData.symbol, symbolData.company_name);
  };

  const handleInputFocus = () => {
    setIsOpen(true);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    if (!isOpen) {
      setIsOpen(true);
    }
  };

  const clearSelection = () => {
    setSelectedSymbol(null);
    setSearchQuery('');
    setIsOpen(false);
  };

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <div className="relative">
        <div className="relative">
          <input
            ref={inputRef}
            type="text"
            placeholder={selectedSymbol ? `${selectedSymbol.symbol} - ${selectedSymbol.company_name}` : placeholder}
            value={searchQuery}
            onChange={handleInputChange}
            onFocus={handleInputFocus}
            className="w-full px-4 py-3 pl-12 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 placeholder-gray-500"
          />
          <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center space-x-1">
            {selectedSymbol && (
              <button
                onClick={clearSelection}
                className="p-1 text-gray-400 hover:text-gray-600"
                type="button"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
            <ChevronDownIcon className={`h-5 w-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </div>
        </div>
      </div>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {loading ? (
            <div className="px-4 py-3 text-center text-gray-500">
              <div className="flex items-center justify-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <span>Recherche...</span>
              </div>
            </div>
          ) : filteredSymbols.length > 0 ? (
            <div className="py-1">
              {filteredSymbols.map((symbolData) => (
                <button
                  key={symbolData.symbol}
                  onClick={() => handleSymbolSelect(symbolData)}
                  className="w-full px-4 py-3 text-left hover:bg-gray-50 focus:bg-gray-50 focus:outline-none border-b border-gray-100 last:border-b-0"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
                          {symbolData.symbol.charAt(0)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold text-gray-900 truncate">
                            {symbolData.symbol}
                          </div>
                          <div className="text-sm text-gray-600 truncate">
                            {symbolData.company_name}
                          </div>
                        </div>
                      </div>
                    </div>
                    {symbolData.sector && (
                      <div className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded ml-2">
                        {symbolData.sector}
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="px-4 py-3 text-center text-gray-500">
              {searchQuery ? 'Aucun symbole trouvé' : 'Tapez pour rechercher un symbole'}
            </div>
          )}
        </div>
      )}

      {/* Overlay pour fermer le dropdown */}
      {isOpen && (
        <div 
          className="fixed inset-0 z-40" 
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default DynamicSymbolSelector;
