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
import { advancedAnalysisApi, HybridAnalysisRequest, HybridAnalysisResponse, AdvancedSearchFilters, GenerateDailyOpportunitiesRequest, GenerateDailyOpportunitiesResponse } from '@/services/advancedAnalysisApi';

interface AdvancedAnalysisDashboardProps {
  className?: string;
}

const AdvancedAnalysisDashboard: React.FC<AdvancedAnalysisDashboardProps> = ({ className = '' }) => {
  const [hybridOpportunities, setHybridOpportunities] = useState<HybridAnalysisResponse['opportunities']>([]);
  const [filteredOpportunities, setFilteredOpportunities] = useState<HybridAnalysisResponse['opportunities']>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatingOpportunities, setGeneratingOpportunities] = useState(false);
  const [generationMessage, setGenerationMessage] = useState<string | null>(null);
  const [showGenerationForm, setShowGenerationForm] = useState(false);
  const [generationParams, setGenerationParams] = useState<GenerateDailyOpportunitiesRequest>({
    limit_symbols: 50,
    time_horizon: 30,
    include_ml: true
  });
  
  // Filtres
  const [filters, setFilters] = useState({
    symbol: '',
    recommendation: '',
    minScore: '',
    maxScore: '',
    startDate: '',
    endDate: ''
  });
  
  // Tri
  const [sortBy, setSortBy] = useState('composite_score');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Fonction pour charger les opportunités par défaut
  const loadDefaultOpportunities = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const searchFilters: AdvancedSearchFilters = {
        limit: 50,
        sort_by: 'composite_score',
        sort_order: 'desc'
      };
      
      const response = await advancedAnalysisApi.searchStoredOpportunities(searchFilters);
      setHybridOpportunities(response.opportunities);
      setFilteredOpportunities(response.opportunities);
    } catch (err) {
      console.error('Erreur lors du chargement des opportunités:', err);
      setError('Erreur lors du chargement des opportunités');
    } finally {
      setLoading(false);
    }
  };

  // Fonction pour appliquer les filtres
  const applyFilters = () => {
    console.log('Applying filters:', filters);
    console.log('Original opportunities count:', hybridOpportunities.length);
    
    let filtered = [...hybridOpportunities];
    
    // Filtre par symbole
    if (filters.symbol) {
      filtered = filtered.filter(opp => 
        opp.symbol.toLowerCase().includes(filters.symbol.toLowerCase())
      );
      console.log('After symbol filter:', filtered.length);
    }
    
    // Filtre par recommandation
    if (filters.recommendation) {
      filtered = filtered.filter(opp => opp.recommendation === filters.recommendation);
      console.log('After recommendation filter:', filtered.length);
    }
    
    // Filtre par score minimum
    if (filters.minScore) {
      const minScore = parseFloat(filters.minScore);
      filtered = filtered.filter(opp => opp.hybrid_score >= minScore);
      console.log('After min score filter:', filtered.length);
    }
    
    // Filtre par score maximum
    if (filters.maxScore) {
      const maxScore = parseFloat(filters.maxScore);
      filtered = filtered.filter(opp => opp.hybrid_score <= maxScore);
      console.log('After max score filter:', filtered.length);
    }
    
    // Filtre par date
    if (filters.startDate) {
      const startDate = new Date(filters.startDate);
      filtered = filtered.filter(opp => new Date(opp.updated_at || '') >= startDate);
      console.log('After start date filter:', filtered.length);
    }
    
    if (filters.endDate) {
      const endDate = new Date(filters.endDate);
      filtered = filtered.filter(opp => new Date(opp.updated_at || '') <= endDate);
      console.log('After end date filter:', filtered.length);
    }
    
    console.log('Final filtered count:', filtered.length);
    setFilteredOpportunities(filtered);
  };

  // Fonction pour trier les opportunités
  const sortOpportunities = () => {
    setFilteredOpportunities(prevFiltered => {
      const sorted = [...prevFiltered].sort((a, b) => {
        let aValue: any, bValue: any;
        
        switch (sortBy) {
          case 'composite_score':
            aValue = a.hybrid_score;
            bValue = b.hybrid_score;
            break;
          case 'technical_score':
            aValue = a.technical_score;
            bValue = b.technical_score;
            break;
          case 'sentiment_score':
            aValue = a.sentiment_score;
            bValue = b.sentiment_score;
            break;
          case 'market_score':
            aValue = a.market_score;
            bValue = b.market_score;
            break;
          case 'confidence_level':
            aValue = a.confidence;
            bValue = b.confidence;
            break;
          case 'analysis_date':
            aValue = new Date(a.updated_at || '');
            bValue = new Date(b.updated_at || '');
            break;
          default:
            aValue = a.hybrid_score;
            bValue = b.hybrid_score;
        }
        
        if (sortOrder === 'asc') {
          return aValue > bValue ? 1 : -1;
        } else {
          return aValue < bValue ? 1 : -1;
        }
      });
      
      return sorted;
    });
  };

  // Fonction pour réinitialiser les filtres
  const resetFilters = () => {
    setFilters({
      symbol: '',
      recommendation: '',
      minScore: '',
      maxScore: '',
      startDate: '',
      endDate: ''
    });
    setFilteredOpportunities(hybridOpportunities);
  };

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
    min_score: 0.2,  // Score plus bas par défaut pour inclure les opportunités SELL
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
  const [showFilters, setShowFilters] = useState(false);
  const [showFiltersAndSort, setShowFiltersAndSort] = useState(false);
  const [selectedOpportunity, setSelectedOpportunity] = useState<{
    symbol: string;
    tab: 'technical' | 'sentiment' | 'market' | 'hybrid';
  } | null>(null);
  const [activeTab, setActiveTab] = useState<'technical' | 'sentiment' | 'market' | 'hybrid'>('technical');

  useEffect(() => {
    loadDefaultOpportunities();
  }, []);

  useEffect(() => {
    sortOpportunities();
  }, [sortBy, sortOrder]);

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

  const generateDailyOpportunities = async () => {
    setGeneratingOpportunities(true);
    setGenerationMessage(null);
    setError(null);

    try {
      const response = await advancedAnalysisApi.generateDailyOpportunities(generationParams);
      
      if (response.status === 'success') {
        setGenerationMessage(
          `✅ ${response.summary.total_opportunities_generated} opportunités générées pour ${response.summary.total_symbols_requested} symboles`
        );
        
        // Recharger les opportunités après génération
        setTimeout(() => {
          loadDefaultOpportunities();
        }, 1000);
      } else {
        setError('Erreur lors de la génération des opportunités');
      }
    } catch (err) {
      console.error('Erreur lors de la génération des opportunités:', err);
      setError('Erreur lors de la génération des opportunités du jour');
    } finally {
      setGeneratingOpportunities(false);
    }
  };

  const handleSymbolChange = (symbol: string) => {
    // No longer needed
  };

  const handleAnalyzeSymbol = (symbol: string) => {
    // No longer needed
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
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Analyse Avancée de Trading
              </h1>
              <p className="mt-2 text-gray-600">
                Système d'analyse combinée ML + conventionnelle pour des décisions éclairées
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Zone de génération d'opportunités */}
        <div className="mb-8 p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">
              Génération d'Opportunités
            </h2>
            <button
              onClick={() => setShowGenerationForm(!showGenerationForm)}
              className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              <Cog6ToothIcon className="w-4 h-4" />
              <span>Configurer la génération</span>
            </button>
          </div>
          
          {showGenerationForm && (
            <div className="mb-6 p-6 bg-gray-50 border border-gray-200 rounded-lg">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Configuration de la génération d'opportunités</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nombre de symboles à analyser
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="200"
                    value={generationParams.limit_symbols}
                    onChange={(e) => setGenerationParams({
                      ...generationParams,
                      limit_symbols: parseInt(e.target.value) || 50
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Entre 1 et 200 symboles</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Horizon temporel (jours)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="365"
                    value={generationParams.time_horizon}
                    onChange={(e) => setGenerationParams({
                      ...generationParams,
                      time_horizon: parseInt(e.target.value) || 30
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">Entre 1 et 365 jours</p>
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Inclure l'analyse ML
                  </label>
                  <div className="flex items-center">
                    <input
                      type="checkbox"
                      checked={generationParams.include_ml}
                      onChange={(e) => setGenerationParams({
                        ...generationParams,
                        include_ml: e.target.checked
                      })}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      {generationParams.include_ml ? 'Activé' : 'Désactivé'}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">Analyse par machine learning</p>
                </div>
              </div>
              
              <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-md">
                <p className="text-sm text-blue-800">
                  <strong>Résumé de la configuration :</strong> Analyse de {generationParams.limit_symbols} symboles 
                  sur un horizon de {generationParams.time_horizon} jours 
                  {generationParams.include_ml ? ' avec analyse ML' : ' sans analyse ML'}.
                </p>
              </div>
            </div>
          )}
          
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Générez de nouvelles opportunités d'investissement basées sur l'analyse avancée
            </div>
            <button
              onClick={generateDailyOpportunities}
              disabled={generatingOpportunities}
              className="flex items-center space-x-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {generatingOpportunities ? (
                <ArrowPathIcon className="w-5 h-5 animate-spin" />
              ) : (
                <ArrowTrendingUpIcon className="w-5 h-5" />
              )}
              <span>
                {generatingOpportunities ? 'Génération...' : 'Générer les opportunités du jour'}
              </span>
            </button>
          </div>
          
          {generationMessage && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center">
                <ArrowTrendingUpIcon className="w-5 h-5 text-green-400 mr-2" />
                <span className="text-green-800">{generationMessage}</span>
              </div>
            </div>
          )}
        </div>

        {/* Filtres et tri des opportunités */}
        <div className="mb-8 p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900">Filtres et Tri</h2>
            <button
              onClick={() => setShowFiltersAndSort(!showFiltersAndSort)}
              className="flex items-center space-x-2 px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200"
            >
              <Cog6ToothIcon className="w-4 h-4" />
              <span>{showFiltersAndSort ? 'Masquer' : 'Afficher'} les filtres</span>
            </button>
          </div>
          
          {showFiltersAndSort && (
            <div>
          
          {/* Filtres */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Symbole</label>
              <input
                type="text"
                value={filters.symbol}
                onChange={(e) => setFilters({...filters, symbol: e.target.value})}
                placeholder="Ex: AAPL, MSFT"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Recommandation</label>
              <select
                value={filters.recommendation}
                onChange={(e) => setFilters({...filters, recommendation: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Toutes</option>
                <option value="BUY_STRONG">BUY_STRONG</option>
                <option value="BUY_MODERATE">BUY_MODERATE</option>
                <option value="BUY_WEAK">BUY_WEAK</option>
                <option value="HOLD">HOLD</option>
                <option value="SELL_WEAK">SELL_WEAK</option>
                <option value="SELL_MODERATE">SELL_MODERATE</option>
                <option value="SELL_STRONG">SELL_STRONG</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Score minimum</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={filters.minScore}
                onChange={(e) => setFilters({...filters, minScore: e.target.value})}
                placeholder="0.0"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Score maximum</label>
              <input
                type="number"
                min="0"
                max="1"
                step="0.01"
                value={filters.maxScore}
                onChange={(e) => setFilters({...filters, maxScore: e.target.value})}
                placeholder="1.0"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Date de début</label>
              <input
                type="date"
                value={filters.startDate}
                onChange={(e) => setFilters({...filters, startDate: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Date de fin</label>
              <input
                type="date"
                value={filters.endDate}
                onChange={(e) => setFilters({...filters, endDate: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          {/* Tri */}
          <div className="flex items-center space-x-4 mb-4">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Trier par:</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="composite_score">Score composite</option>
                <option value="technical_score">Score technique</option>
                <option value="sentiment_score">Score sentiment</option>
                <option value="market_score">Score marché</option>
                <option value="confidence_level">Niveau de confiance</option>
                <option value="analysis_date">Date d'analyse</option>
              </select>
            </div>
            
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Ordre:</label>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="desc">Décroissant</option>
                <option value="asc">Croissant</option>
              </select>
            </div>
            
            <button
              onClick={resetFilters}
              className="px-4 py-2 text-sm bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200"
            >
              Réinitialiser
            </button>
            
            <button
              onClick={applyFilters}
              className="px-4 py-2 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Appliquer les filtres
            </button>
          </div>
            </div>
          )}
        </div>

        {/* Liste des opportunités */}
        <div>
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                Opportunités ({filteredOpportunities.length})
              </h2>
              <div className="text-sm text-gray-600">
                {filteredOpportunities.length} opportunité{filteredOpportunities.length > 1 ? 's' : ''} affichée{filteredOpportunities.length > 1 ? 's' : ''}
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
              {filteredOpportunities.map((opportunity, index) => (
                <HybridOpportunityCard
                  key={`${opportunity.symbol}-${opportunity.updated_at || index}`}
                  opportunity={opportunity}
                  onAnalyze={handleAnalyzeSymbol}
                  onViewDetails={handleViewDetails}
                />
              ))}
            </div>
          </div>
        
      </div>
    </div>
  );
};

export default AdvancedAnalysisDashboard;
