// frontend/src/components/AdvancedAnalysis/AdvancedAnalysisDashboard.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
  MagnifyingGlassIcon, 
  ChartBarIcon, 
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  Cog6ToothIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import TechnicalSignalsChart from './TechnicalSignalsChart';
import SentimentAnalysisPanel from './SentimentAnalysisPanel';
import MarketIndicatorsWidget from './MarketIndicatorsWidget';
import HybridOpportunityCard from './HybridOpportunityCard';
import { advancedAnalysisApi, HybridAnalysisRequest, HybridAnalysisResponse, AdvancedSearchFilters } from '@/services/advancedAnalysisApi';

interface AdvancedAnalysisDashboardProps {
  className?: string;
}

const AdvancedAnalysisDashboard: React.FC<AdvancedAnalysisDashboardProps> = ({ className = '' }) => {
  const [selectedSymbol, setSelectedSymbol] = useState('AAPL');
  const [hybridOpportunities, setHybridOpportunities] = useState<HybridAnalysisResponse['opportunities']>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fonction pour obtenir le nom de l'entreprise à partir du symbole
  const getCompanyName = (symbol: string): string => {
    console.log('getCompanyName called with symbol:', symbol);
      const companyNames: { [key: string]: string } = {
        'AAPL': 'Apple Inc.',
        'ABNB': 'Airbnb Inc.',
        'ADBE': 'Adobe Inc.',
        'ADI': 'Analog Devices Inc.',
        'ADP': 'Automatic Data Processing Inc.',
        'ADSK': 'Autodesk Inc.',
        'AEP': 'American Electric Power Company Inc.',
        'AMAT': 'Applied Materials Inc.',
        'AMD': 'Advanced Micro Devices Inc.',
        'AMGN': 'Amgen Inc.',
        'AMZN': 'Amazon.com Inc.',
        'APP': 'AppLovin Corporation',
        'ARM': 'Arm Holdings plc',
        'ASML': 'ASML Holding N.V.',
        'AVGO': 'Broadcom Inc.',
        'AXON': 'Axon Enterprise Inc.',
        'AZN': 'AstraZeneca plc',
        'BIIB': 'Biogen Inc.',
        'BKNG': 'Booking Holdings Inc.',
        'BKR': 'Baker Hughes Company',
        'CCEP': 'Coca-Cola Europacific Partners plc',
        'CDNS': 'Cadence Design Systems Inc.',
        'CDW': 'CDW Corporation',
        'CEG': 'Constellation Energy Corporation',
        'CHTR': 'Charter Communications Inc.',
        'CMCSA': 'Comcast Corporation',
        'COST': 'Costco Wholesale Corporation',
        'CPRT': 'Copart Inc.',
        'CRWD': 'CrowdStrike Holdings Inc.',
        'CSCO': 'Cisco Systems Inc.',
        'CSGP': 'CoStar Group Inc.',
        'CSX': 'CSX Corporation',
        'CTAS': 'Cintas Corporation',
        'CTSH': 'Cognizant Technology Solutions Corporation',
        'DASH': 'DoorDash Inc.',
        'DDOG': 'Datadog Inc.',
        'DXCM': 'Dexcom Inc.',
        'EA': 'Electronic Arts Inc.',
        'EXC': 'Exelon Corporation',
        'FANG': 'Diamondback Energy Inc.',
        'FAST': 'Fastenal Company',
        'FTNT': 'Fortinet Inc.',
        'GEHC': 'GE HealthCare Technologies Inc.',
        'GFS': 'GlobalFoundries Inc.',
        'GILD': 'Gilead Sciences Inc.',
        'GOOG': 'Alphabet Inc. Class C',
        'GOOGL': 'Alphabet Inc. Class A',
        'HON': 'Honeywell International Inc.',
        'IDXX': 'IDEXX Laboratories Inc.',
        'INTC': 'Intel Corporation',
        'INTU': 'Intuit Inc.',
        'ISRG': 'Intuitive Surgical Inc.',
        'KDP': 'Keurig Dr Pepper Inc.',
        'KHC': 'The Kraft Heinz Company',
        'KLAC': 'KLA Corporation',
        'LIN': 'Linde plc',
        'LRCX': 'Lam Research Corporation',
        'LULU': 'Lululemon Athletica Inc.',
        'MAR': 'Marriott International Inc.',
        'MCHP': 'Microchip Technology Incorporated',
        'MDLZ': 'Mondelez International Inc.',
        'MELI': 'MercadoLibre Inc.',
        'META': 'Meta Platforms Inc.',
        'MNST': 'Monster Beverage Corporation',
        'MRVL': 'Marvell Technology Inc.',
        'MSFT': 'Microsoft Corporation',
        'MSTR': 'MicroStrategy Incorporated',
        'MU': 'Micron Technology Inc.',
        'NFLX': 'Netflix Inc.',
        'NVDA': 'NVIDIA Corporation',
        'NXPI': 'NXP Semiconductors N.V.',
        'ODFL': 'Old Dominion Freight Line Inc.',
        'ON': 'ON Semiconductor Corporation',
        'ORLY': 'O\'Reilly Automotive Inc.',
        'PANW': 'Palo Alto Networks Inc.',
        'PAYX': 'Paychex Inc.',
        'PCAR': 'PACCAR Inc.',
        'PDD': 'PDD Holdings Inc.',
        'PEP': 'PepsiCo Inc.',
        'PLTR': 'Palantir Technologies Inc.',
        'PYPL': 'PayPal Holdings Inc.',
        'QCOM': 'QUALCOMM Incorporated',
        'REGN': 'Regeneron Pharmaceuticals Inc.',
        'ROP': 'Roper Technologies Inc.',
        'ROST': 'Ross Stores Inc.',
        'SBUX': 'Starbucks Corporation',
        'SHOP': 'Shopify Inc.',
        'SNPS': 'Synopsys Inc.',
        'TEAM': 'Atlassian Corporation',
        'TMUS': 'T-Mobile US Inc.',
        'TRI': 'Thomson Reuters Corporation',
        'TSLA': 'Tesla Inc.',
        'TTD': 'The Trade Desk Inc.',
        'TTWO': 'Take-Two Interactive Software Inc.',
        'TXN': 'Texas Instruments Incorporated',
        'VRSK': 'Verisk Analytics Inc.',
        'VRTX': 'Vertex Pharmaceuticals Incorporated',
        'WBD': 'Warner Bros. Discovery Inc.',
        'WDAY': 'Workday Inc.',
        'XEL': 'Xcel Energy Inc.',
        'ZS': 'Zscaler Inc.'
      };
    
    const result = companyNames[symbol] || symbol;
    console.log('getCompanyName result:', result);
    return result;
  };
  const [searchConfig, setSearchConfig] = useState({
    symbols: ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA'],
    weights: {
      technical: 0.15,
      sentiment: 0.15,
      market: 0.15,
      ml: 0.10,
      candlestick: 0.10,
      garch: 0.10,
      monte_carlo: 0.10,
      markov: 0.10,
      volatility: 0.05
    },
    threshold: 0.7
  });
  
  const [advancedFilters, setAdvancedFilters] = useState<AdvancedSearchFilters>({
    min_score: 0.5,
    max_risk: "HIGH",
    limit: 20,
    recommendations: "",
    symbols: "",
    sort_by: "composite_score",
    sort_order: "desc",
    min_confidence: undefined,
    max_confidence: undefined,
    date_from: undefined,
    date_to: undefined
  });
  const [showFilters, setShowFilters] = useState(true);
  const [selectedOpportunity, setSelectedOpportunity] = useState<{
    symbol: string;
    tab: 'technical' | 'sentiment' | 'market' | 'hybrid';
  } | null>(null);
  const [activeTab, setActiveTab] = useState<'technical' | 'sentiment' | 'market' | 'hybrid'>('technical');

  useEffect(() => {
    performHybridSearch();
  }, []);

  const performHybridSearch = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Construire les filtres avancés
      const filters: AdvancedSearchFilters = {
        ...advancedFilters,
        // Ne pas filtrer par symboles si aucun n'est spécifié dans les filtres avancés
        symbols: advancedFilters.symbols || undefined,
        limit: advancedFilters.limit || 20
      };
      
      const response = await advancedAnalysisApi.searchStoredOpportunities(filters);
      setHybridOpportunities(response.opportunities);
      
      // Masquer les filtres après une recherche réussie
      setShowFilters(false);
      
    } catch (err) {
      setError('Erreur lors de la récupération des opportunités stockées');
      console.error('Error performing hybrid search:', err);
      
      // En cas d'erreur, vider la liste des opportunités
      setHybridOpportunities([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSymbolChange = (symbol: string) => {
    setSelectedSymbol(symbol);
  };

  const handleAnalyzeSymbol = (symbol: string) => {
    setSelectedSymbol(symbol);
  };

  const handleViewDetails = (symbol: string, tab: 'technical' | 'sentiment' | 'market' | 'hybrid') => {
    setSelectedOpportunity({ symbol, tab });
    setActiveTab(tab);
  };

  const handleBackToSearch = () => {
    setSelectedOpportunity(null);
  };

  const tabs = [
    { id: 'overview', name: 'Vue d\'ensemble', icon: ChartBarIcon },
    { id: 'technical', name: 'Technique', icon: ArrowTrendingUpIcon },
    { id: 'sentiment', name: 'Sentiment', icon: ExclamationTriangleIcon },
    { id: 'market', name: 'Marché', icon: ChartBarIcon },
    { id: 'hybrid', name: 'Composite', icon: Cog6ToothIcon }
  ];

  // Si une opportunité est sélectionnée, afficher les détails
  if (selectedOpportunity) {
    return (
      <div className={`bg-gray-50 min-h-screen ${className}`}>
        {/* En-tête avec bouton retour */}
        <div className="bg-white shadow-sm border-b border-gray-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="py-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <button
                    onClick={handleBackToSearch}
                    className="flex items-center space-x-2 px-4 py-2 text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <ArrowTrendingUpIcon className="w-4 h-4 rotate-90" />
                    <span>Retour à la recherche</span>
                  </button>
                  <div>
                    <h1 className="text-3xl font-bold text-gray-900">
                      Analyse {selectedOpportunity.tab === 'hybrid' ? 'Composite' : selectedOpportunity.tab === 'technical' ? 'Technique' : selectedOpportunity.tab} - {getCompanyName(selectedOpportunity.symbol)}
                    </h1>
                    <p className="mt-2 text-gray-600">
                      Analyse détaillée pour {selectedOpportunity.symbol}
                    </p>
                    {/* Debug info */}
                    <p className="mt-1 text-xs text-gray-400">
                      Debug: symbol={selectedOpportunity.symbol}, companyName={getCompanyName(selectedOpportunity.symbol)}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Navigation par onglets */}
          <div className="mb-8">
            <nav className="flex space-x-8">
              {tabs.filter(tab => tab.id !== 'overview').map((tab) => {
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id as any)}
                    className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{tab.name}</span>
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Contenu de l'analyse sélectionnée */}
          {activeTab === 'technical' && (
            <TechnicalSignalsChart symbol={selectedOpportunity.symbol} />
          )}
          
          {activeTab === 'sentiment' && (
            <SentimentAnalysisPanel symbol={selectedOpportunity.symbol} />
          )}
          
          {activeTab === 'market' && (
            <MarketIndicatorsWidget symbol={selectedOpportunity.symbol} />
          )}
          
          {activeTab === 'hybrid' && (
            <div className="space-y-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">
                  Analyse Composite Complète - {selectedOpportunity.symbol}
                </h3>
                <p className="text-gray-600 mb-6">
                  Cette vue combine l'analyse technique, de sentiment, de marché et ML pour {selectedOpportunity.symbol}.
                </p>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <TechnicalSignalsChart symbol={selectedOpportunity.symbol} />
                  <SentimentAnalysisPanel symbol={selectedOpportunity.symbol} />
                </div>
                
                <div className="mt-6">
                  <MarketIndicatorsWidget symbol={selectedOpportunity.symbol} />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Page de recherche par défaut
  return (
    <div className={`bg-gray-50 min-h-screen ${className}`}>
      {/* En-tête */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900">
                  Analyse Avancée de Trading
                </h1>
                <p className="mt-2 text-gray-600">
                  Système d'analyse combinée ML + conventionnelle pour des décisions éclairées
                </p>
              </div>
              
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <MagnifyingGlassIcon className="w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    value={selectedSymbol}
                    onChange={(e) => setSelectedSymbol(e.target.value.toUpperCase())}
                    placeholder="Symbole (ex: AAPL)"
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <button
                  onClick={performHybridSearch}
                  disabled={loading}
                  className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <ArrowPathIcon className="w-4 h-4 animate-spin" />
                  ) : (
                    <MagnifyingGlassIcon className="w-4 h-4" />
                  )}
                  <span>Rechercher</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Page de recherche */}
        <div className="space-y-8">
          {/* Filtres avancés - affichés seulement si showFilters est true */}
          {showFilters && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Filtres Avancés
              </h3>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
                  {/* Symboles spécifiques */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Symboles Spécifiques (optionnel)
                    </label>
                    <input
                      type="text"
                      value={advancedFilters.symbols || ""}
                      onChange={(e) => setAdvancedFilters({
                        ...advancedFilters,
                        symbols: e.target.value
                      })}
                      placeholder="AAPL, MSFT, GOOGL (vide = tous les titres)"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  
                  {/* Recommandations */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Recommandations
                    </label>
                    <select
                      value={advancedFilters.recommendations || ""}
                      onChange={(e) => setAdvancedFilters({
                        ...advancedFilters,
                        recommendations: e.target.value
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">Toutes</option>
                      <option value="BUY">BUY</option>
                      <option value="SELL">SELL</option>
                      <option value="HOLD">HOLD</option>
                      <option value="STRONG_BUY">STRONG_BUY</option>
                      <option value="STRONG_SELL">STRONG_SELL</option>
                    </select>
                  </div>
                  
                  {/* Niveau de risque */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Niveau de Risque Max
                    </label>
                    <select
                      value={advancedFilters.max_risk || "HIGH"}
                      onChange={(e) => setAdvancedFilters({
                        ...advancedFilters,
                        max_risk: e.target.value
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="LOW">LOW</option>
                      <option value="MEDIUM">MEDIUM</option>
                      <option value="HIGH">HIGH</option>
                    </select>
                  </div>
                  
                  {/* Tri */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Trier par
                    </label>
                    <select
                      value={advancedFilters.sort_by || "composite_score"}
                      onChange={(e) => setAdvancedFilters({
                        ...advancedFilters,
                        sort_by: e.target.value
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="composite_score">Score Composite</option>
                      <option value="confidence_level">Niveau de Confiance</option>
                      <option value="analysis_date">Date d'Analyse</option>
                      <option value="updated_at">Date de Mise à Jour</option>
                      <option value="technical_score">Score Technique</option>
                      <option value="sentiment_score">Score Sentiment</option>
                      <option value="market_score">Score Marché</option>
                    </select>
                  </div>
                  
                  {/* Ordre de tri */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Ordre
                    </label>
                    <select
                      value={advancedFilters.sort_order || "desc"}
                      onChange={(e) => setAdvancedFilters({
                        ...advancedFilters,
                        sort_order: e.target.value
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="desc">Décroissant</option>
                      <option value="asc">Croissant</option>
                    </select>
                  </div>
                  
                  {/* Confiance minimum */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Confiance Min ({advancedFilters.min_confidence || 0})
                    </label>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.05"
                      value={advancedFilters.min_confidence || 0}
                      onChange={(e) => setAdvancedFilters({
                        ...advancedFilters,
                        min_confidence: parseFloat(e.target.value)
                      })}
                      className="w-full"
                    />
                  </div>
                  
                  {/* Limite de résultats */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Nombre de Résultats
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="100"
                      value={advancedFilters.limit || 20}
                      onChange={(e) => setAdvancedFilters({
                        ...advancedFilters,
                        limit: parseInt(e.target.value)
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
                
                {/* Filtres de dates */}
                <div className="mt-4 grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Date de Début
                    </label>
                    <input
                      type="date"
                      value={advancedFilters.date_from || ""}
                      onChange={(e) => setAdvancedFilters({
                        ...advancedFilters,
                        date_from: e.target.value
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Date de Fin
                    </label>
                    <input
                      type="date"
                      value={advancedFilters.date_to || ""}
                      onChange={(e) => setAdvancedFilters({
                        ...advancedFilters,
                        date_to: e.target.value
                      })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
            </div>
          )}

          {/* Opportunités composite */}
          <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                Opportunités Composite Détectées
              </h2>
              <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-600">
                  {hybridOpportunities.length} opportunité{hybridOpportunities.length > 1 ? 's' : ''} trouvée{hybridOpportunities.length > 1 ? 's' : ''}
                </div>
                {!showFilters && (
                  <button
                    onClick={() => setShowFilters(true)}
                    className="flex items-center space-x-2 px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200"
                  >
                    <Cog6ToothIcon className="w-4 h-4" />
                    <span>Modifier les filtres</span>
                  </button>
                )}
              </div>
            </div>
            
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center">
                  <ExclamationTriangleIcon className="w-5 h-5 text-red-400 mr-2" />
                  <span className="text-red-800">{error}</span>
                </div>
              </div>
            )}
            
            <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
              {hybridOpportunities.map((opportunity) => (
                <HybridOpportunityCard
                  key={opportunity.symbol}
                  opportunity={opportunity}
                  onAnalyze={handleAnalyzeSymbol}
                  onViewDetails={handleViewDetails}
                />
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdvancedAnalysisDashboard;
