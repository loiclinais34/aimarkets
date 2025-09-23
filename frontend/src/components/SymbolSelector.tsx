import { useState } from 'react'
import { ChevronDownIcon } from '@heroicons/react/24/outline'
import { SymbolWithMetadata } from '../services/api'

interface SymbolSelectorProps {
  symbols: SymbolWithMetadata[]
  selectedSymbol: string
  onSymbolChange: (symbol: string) => void
  loading?: boolean
}

export default function SymbolSelector({ symbols, selectedSymbol, onSymbolChange, loading }: SymbolSelectorProps) {
  const [isOpen, setIsOpen] = useState(false)

  if (loading) {
    return (
      <div className="w-32 h-10 bg-gray-200 rounded-md animate-pulse" />
    )
  }

  // Trouver le symbole sélectionné pour afficher son nom
  const selectedSymbolData = symbols.find(s => s.symbol === selectedSymbol)

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-80 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <div className="flex flex-col items-start">
          <span className="font-semibold">{selectedSymbol}</span>
          {selectedSymbolData && (
            <span className="text-xs text-gray-500 truncate max-w-64">
              {selectedSymbolData.company_name}
            </span>
          )}
        </div>
        <ChevronDownIcon className="h-4 w-4 ml-2" />
      </button>

      {isOpen && (
        <div className="absolute right-0 z-10 mt-1 w-80 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          {symbols
            .sort((a, b) => a.symbol.localeCompare(b.symbol))
            .map((symbolData) => (
            <button
              key={symbolData.symbol}
              onClick={() => {
                onSymbolChange(symbolData.symbol)
                setIsOpen(false)
              }}
              className={`w-full px-3 py-2 text-left hover:bg-gray-100 ${
                symbolData.symbol === selectedSymbol ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
              }`}
            >
              <div className="flex flex-col">
                <span className="font-semibold text-sm">{symbolData.symbol}</span>
                <span className="text-xs text-gray-500 truncate">
                  {symbolData.company_name}
                </span>
                {symbolData.sector && symbolData.sector !== 'Unknown' && (
                  <span className="text-xs text-blue-600">
                    {symbolData.sector}
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
