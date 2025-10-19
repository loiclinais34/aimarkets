// frontend/src/components/AdvancedAnalysis/OpportunitiesDashboard.tsx
'use client';

import React, { useState, useEffect } from 'react';
import { 
  MagnifyingGlassIcon, 
  ChartBarIcon, 
  ExclamationTriangleIcon,
  ArrowTrendingUpIcon,
  Cog6ToothIcon,
  ArrowPathIcon,
  CpuChipIcon
} from '@heroicons/react/24/outline';
import TechnicalSignalsChart from './TechnicalSignalsChart';
import SentimentAnalysisPanel from './SentimentAnalysisPanel';
import MarketIndicatorsWidget from './MarketIndicatorsWidget';
import BubbleRiskPanel from './BubbleRiskPanel';
import XGBoostOpportunityCard from './XGBoostOpportunityCard';
import AdvancedTechnicalIndicators from './AdvancedTechnicalIndicators';
import { AgentAnalysisModal } from './AgentAnalysisModal';
import { advancedAnalysisApi, HybridAnalysisRequest, HybridAnalysisResponse, AdvancedSearchFilters, GenerateDailyOpportunitiesRequest, GenerateDailyOpportunitiesResponse } from '@/services/advancedAnalysisApi';
import { xgboostOpportunitiesApi, XGBoostOpportunity, XGBoostOpportunitiesResponse } from '@/services/xgboostOpportunitiesApi';
import { agentAnalysisApi } from '../../services/agentAnalysisApi';

interface OpportunitiesDashboardProps {
  className?: string;
}

const OpportunitiesDashboard: React.FC<OpportunitiesDashboardProps> = ({ className = '' }) => {
  const [xgboostOpportunities, setXGBoostOpportunities] = useState<XGBoostOpportunity[]>([]);
  const [filteredOpportunities, setFilteredOpportunities] = useState<XGBoostOpportunity[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatingOpportunities, setGeneratingOpportunities] = useState(false);
  const [generationMessage, setGenerationMessage] = useState<string | null>(null);
  const [showGenerationForm, setShowGenerationForm] = useState(false);
  const [generationParams, setGenerationParams] = useState<GenerateDailyOpportunitiesRequest>({
    limit_symbols: 101,
    time_horizon: 30,
    include_ml: true
  });
  
  // État pour la modale d'analyse agent
  const [agentAnalysisModal, setAgentAnalysisModal] = useState<{
    isOpen: boolean;
    symbol: string;
  }>({
    isOpen: false,
    symbol: ''
  });

  const [agentAnalysisData, setAgentAnalysisData] = useState<any>(null);
  const [agentAnalysisLoading, setAgentAnalysisLoading] = useState(false);
  const [agentAnalysisError, setAgentAnalysisError] = useState<string | null>(null);
  
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
  const [sortBy, setSortBy] = useState('confidence_level');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Fonction pour charger les opportunités XGBoost par défaut
  const loadDefaultOpportunities = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Charger les opportunités XGBoost avec une confiance minimale élevée
      const response = await xgboostOpportunitiesApi.getOpportunities({
        limit: 100,
        min_confidence: 0.7, // Confiance minimale de 70%
        sort_by: 'confidence_level',
        sort_order: 'desc'
      });
      
      setXGBoostOpportunities(response.opportunities);
      setFilteredOpportunities(response.opportunities);
    } catch (err) {
      console.error('Erreur lors du chargement des opportunités XGBoost:', err);
      setError('Erreur lors du chargement des opportunités XGBoost');
    } finally {
      setLoading(false);
    }
  };

  // Fonction pour appliquer les filtres
  const applyFilters = async () => {
    console.log('Applying filters:', filters);
    console.log('Sort by:', sortBy, 'Sort order:', sortOrder);
    
    setLoading(true);
    setError(null);
    
    try {
      // Construire les filtres pour l'API XGBoost
      const apiFilters = {
        symbol: filters.symbol || undefined,
        recommendation: filters.recommendation || undefined,
        min_confidence: filters.minScore ? parseFloat(filters.minScore) : undefined,
        max_confidence: filters.maxScore ? parseFloat(filters.maxScore) : undefined,
        date_from: filters.startDate || undefined,
        date_to: filters.endDate || undefined,
        limit: 100,
        sort_by: sortBy === 'analysis_date' ? 'date' : 
                 sortBy === 'composite_score' ? 'confidence_level' : 
                 sortBy === 'confidence_level' ? 'confidence_level' : 'confidence_level',
        sort_order: sortOrder
      };
      
      console.log('XGBoost API filters being sent:', apiFilters);
      
      // Appeler l'API XGBoost avec les filtres
      const response = await xgboostOpportunitiesApi.searchOpportunities(apiFilters);
      setXGBoostOpportunities(response.opportunities);
      setFilteredOpportunities(response.opportunities);
      
      console.log('XGBoost API response count:', response.opportunities.length);
      console.log('First few recommendations:', response.opportunities.slice(0, 5).map(op => ({ symbol: op.symbol, recommendation: op.recommendation })));
    } catch (err) {
      console.error('Erreur lors de l\'application des filtres XGBoost:', err);
      setError('Erreur lors de l\'application des filtres XGBoost');
    } finally {
      setLoading(false);
    }
  };

  // Fonction pour trier les opportunités
  const sortOpportunities = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Construire les filtres pour l'API XGBoost avec TOUS les filtres actuels ET le tri
      const apiFilters = {
        symbol: filters.symbol || undefined,
        recommendation: filters.recommendation || undefined,
        min_confidence: filters.minScore ? parseFloat(filters.minScore) : undefined,
        max_confidence: filters.maxScore ? parseFloat(filters.maxScore) : undefined,
        date_from: filters.startDate || undefined,
        date_to: filters.endDate || undefined,
        limit: 100,
        sort_by: sortBy === 'analysis_date' ? 'date' : 
                 sortBy === 'composite_score' ? 'confidence_level' : 
                 sortBy === 'confidence_level' ? 'confidence_level' : 'confidence_level',
        sort_order: sortOrder
      };
      
      console.log('Sort XGBoost API filters being sent:', apiFilters);
      
      // Appeler l'API XGBoost avec le tri et tous les filtres
      const response = await xgboostOpportunitiesApi.searchOpportunities(apiFilters);
      setXGBoostOpportunities(response.opportunities);
      setFilteredOpportunities(response.opportunities);
      
      console.log('Sorted XGBoost opportunities count:', response.opportunities.length);
    } catch (err) {
      console.error('Erreur lors du tri des opportunités XGBoost:', err);
      setError('Erreur lors du tri des opportunités XGBoost');
    } finally {
      setLoading(false);
    }
  };

  // Fonction pour réinitialiser les filtres
  const resetFilters = async () => {
    setFilters({
      symbol: '',
      recommendation: '',
      minScore: '',
      maxScore: '',
      startDate: '',
      endDate: ''
    });
    // Recharger les opportunités par défaut
    await loadDefaultOpportunities();
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
    tab: 'technical' | 'sentiment' | 'market' | 'bubble' | 'hybrid' | 'agent' | 'advanced';
  } | null>(null);
  const [activeTab, setActiveTab] = useState<'technical' | 'sentiment' | 'market' | 'bubble' | 'hybrid' | 'agent' | 'advanced'>('technical');

  useEffect(() => {
    loadDefaultOpportunities();
  }, []);

  // Ne pas déclencher automatiquement le tri pour éviter les conflits avec les filtres
  // Le tri sera appliqué via les boutons ou via applyFilters

  // Réinitialiser l'analyse agent quand on change de symbole
  useEffect(() => {
    if (selectedOpportunity) {
      setAgentAnalysisData(null);
      setAgentAnalysisError(null);
    }
  }, [selectedOpportunity?.symbol]);

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

  const handleViewDetails = (symbol: string, tab: 'technical' | 'sentiment' | 'market' | 'bubble' | 'hybrid' | 'agent' | 'advanced') => {
    setSelectedOpportunity({ symbol, tab });
    setActiveTab(tab);
    
    // Réinitialiser l'analyse agent quand on change de symbole
    if (tab === 'agent') {
      setAgentAnalysisData(null);
      setAgentAnalysisError(null);
    }
  };

  const handleAgentAnalysis = (symbol: string) => {
    setAgentAnalysisModal({
      isOpen: true,
      symbol
    });
  };

  const handleAgentAnalysisInTab = async (symbol: string) => {
    setAgentAnalysisLoading(true);
    setAgentAnalysisError(null);
    
    try {
      const response = await agentAnalysisApi.generateAnalysis({
        symbol,
        days_back: 7
      });
      setAgentAnalysisData(response);
    } catch (error) {
      console.error('Erreur lors de la génération de l\'analyse agent:', error);
      setAgentAnalysisError('Erreur lors de la génération de l\'analyse');
    } finally {
      setAgentAnalysisLoading(false);
    }
  };

  const handleCloseAgentAnalysis = () => {
    setAgentAnalysisModal({
      isOpen: false,
      symbol: ''
    });
  };

  const handleBackToSearch = () => {
    setSelectedOpportunity(null);
  };

  const tabs = [
    { id: 'overview', name: 'Vue d\'ensemble', icon: ChartBarIcon },
    { id: 'technical', name: 'Technique', icon: ArrowTrendingUpIcon },
    { id: 'sentiment', name: 'Sentiment', icon: ExclamationTriangleIcon },
    { id: 'market', name: 'Marché', icon: ChartBarIcon },
    { id: 'bubble', name: 'Bulle', icon: ExclamationTriangleIcon },
    { id: 'hybrid', name: 'Composite', icon: Cog6ToothIcon },
    { id: 'advanced', name: 'Indicateurs Avancés', icon: CpuChipIcon },
    { id: 'agent', name: 'La rubrique de l\'agent', icon: CpuChipIcon }
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
                    <span>Retour aux opportunités</span>
                  </button>
                  <div>
                    <h1 className="text-3xl font-bold text-gray-900">
                      Analyse {selectedOpportunity.tab === 'hybrid' ? 'Composite' : selectedOpportunity.tab === 'technical' ? 'Technique' : selectedOpportunity.tab} - {getCompanyName(selectedOpportunity.symbol)}
                    </h1>
                    <p className="mt-2 text-gray-600">
                      Analyse détaillée pour {selectedOpportunity.symbol}
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
          
          {activeTab === 'bubble' && (
            <BubbleRiskPanel symbol={selectedOpportunity.symbol} />
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

          {activeTab === 'advanced' && (
            <AdvancedTechnicalIndicators symbol={selectedOpportunity.symbol} />
          )}

          {activeTab === 'agent' && (
            <div className="space-y-8">
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="flex items-center space-x-3 mb-6">
                  <CpuChipIcon className="w-8 h-8 text-purple-600" />
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">
                      La rubrique de l'agent - {selectedOpportunity.symbol}
                    </h3>
                    <p className="text-gray-600">
                      Analyse intelligente basée sur les données de sentiment et de cours
                    </p>
                  </div>
                </div>
                
                <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-6 mb-6">
                  <h4 className="text-md font-semibold text-gray-900 mb-4">
                    🤖 Analyse Agent IA
                  </h4>
                  <p className="text-gray-700 mb-4">
                    Notre agent IA analyse en temps réel les données de sentiment, les cours historiques 
                    et les actualités pour vous fournir des insights détaillés sur {selectedOpportunity.symbol}.
                  </p>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <div className="flex items-center space-x-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                      <span>Données de sentiment</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                      <span>Cours historiques</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                      <span>Actualités récentes</span>
                    </div>
                  </div>
                </div>

                {!agentAnalysisLoading && !agentAnalysisData && (
                  <div className="text-center py-8">
                    <CpuChipIcon className="w-16 h-16 text-purple-600 mx-auto mb-4" />
                    <h4 className="text-lg font-medium text-gray-900 mb-2">
                      Générer l'analyse agent pour {selectedOpportunity.symbol}
                    </h4>
                    <p className="text-gray-600 mb-6">
                      Cliquez sur le bouton ci-dessous pour obtenir une analyse complète basée sur 
                      les dernières données de sentiment et de cours.
                    </p>
                    <button
                      onClick={() => handleAgentAnalysisInTab(selectedOpportunity.symbol)}
                      className="bg-purple-600 text-white px-8 py-3 rounded-lg hover:bg-purple-700 transition-colors flex items-center space-x-2 mx-auto"
                    >
                      <CpuChipIcon className="w-5 h-5" />
                      <span>Lancer l'analyse agent</span>
                    </button>
                  </div>
                )}

                {agentAnalysisLoading && (
                  <div className="text-center py-12">
                    <div className="flex flex-col items-center space-y-4">
                      {/* Spinner animé */}
                      <div className="relative">
                        <div className="w-16 h-16 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin"></div>
                        <CpuChipIcon className="w-8 h-8 text-purple-600 absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2" />
                      </div>
                      <div className="text-center">
                        <h4 className="text-lg font-medium text-gray-900 mb-2">
                          🤖 L'agent analyse {selectedOpportunity.symbol}...
                        </h4>
                        <p className="text-gray-600">
                          Analyse des données de sentiment, cours historiques et actualités récentes
                        </p>
                        <div className="mt-4 flex justify-center space-x-1">
                          <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                          <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                          <div className="w-2 h-2 bg-purple-600 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Affichage de l'analyse */}
                {agentAnalysisError && (
                  <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-red-600">{agentAnalysisError}</p>
                  </div>
                )}

                {agentAnalysisData && (
                  <div className="mt-6 space-y-6">
                    {/* Résumé exécutif amélioré */}
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h4 className="text-lg font-semibold text-gray-900 mb-4">📊 Résumé Exécutif</h4>
                      
                      {/* Métriques clés */}
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                        <div className="text-center">
                          <div className="text-2xl font-bold text-gray-900">${agentAnalysisData.summary.current_price}</div>
                          <div className="text-sm text-gray-600">Prix actuel</div>
                        </div>
                        <div className="text-center">
                          <div className={`text-2xl font-bold ${agentAnalysisData.summary.price_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {agentAnalysisData.summary.price_change >= 0 ? '+' : ''}{agentAnalysisData.summary.price_change.toFixed(2)}
                          </div>
                          <div className="text-sm text-gray-600">Variation</div>
                        </div>
                        <div className="text-center">
                          <div className={`text-2xl font-bold ${agentAnalysisData.summary.price_change_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {agentAnalysisData.summary.price_change_pct >= 0 ? '+' : ''}{agentAnalysisData.summary.price_change_pct.toFixed(2)}%
                          </div>
                          <div className="text-sm text-gray-600">Variation %</div>
                        </div>
                        <div className="text-center">
                          <div className="text-2xl font-bold text-purple-600">{agentAnalysisData.summary.total_news_analyzed}</div>
                          <div className="text-sm text-gray-600">News analysées</div>
                        </div>
                      </div>

                      {/* Récit exécutif */}
                      {agentAnalysisData.executive_narrative && (
                        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6">
                          <h5 className="text-md font-semibold text-gray-900 mb-3">🎯 Analyse Contextuelle</h5>
                          <p className="text-gray-700 leading-relaxed text-justify">
                            {agentAnalysisData.executive_narrative}
                          </p>
                        </div>
                      )}
                    </div>

                    {/* Insights clés */}
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h4 className="text-lg font-semibold text-gray-900 mb-4">💡 Insights Clés</h4>
                      <ul className="space-y-2">
                        {agentAnalysisData.key_insights.map((insight: string, index: number) => (
                          <li key={index} className="flex items-start space-x-2">
                            <div className="w-2 h-2 bg-purple-600 rounded-full mt-2 flex-shrink-0"></div>
                            <span className="text-gray-700">{insight}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Recommandations */}
                    <div className="bg-white border border-gray-200 rounded-lg p-6">
                      <h4 className="text-lg font-semibold text-gray-900 mb-4">🎯 Recommandations</h4>
                      <ul className="space-y-2">
                        {agentAnalysisData.recommendations.map((recommendation: string, index: number) => (
                          <li key={index} className="flex items-start space-x-2">
                            <div className="w-2 h-2 bg-green-600 rounded-full mt-2 flex-shrink-0"></div>
                            <span className="text-gray-700">{recommendation}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                )}
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
                🎯 Opportunités XGBoost ML
              </h1>
              <p className="mt-2 text-gray-600">
                Découvrez les meilleures opportunités basées sur l'intelligence artificielle XGBoost et les indicateurs techniques avancés TA-Lib
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
              Génération d'Opportunités XGBoost ML
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
                    value={generationParams.limit_symbols}
                    onChange={(e) => setGenerationParams({
                      ...generationParams,
                      limit_symbols: parseInt(e.target.value) || 0
                    })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">0 pour analyser tous les titres disponibles</p>
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
              Générez de nouvelles opportunités d'investissement basées sur les modèles XGBoost ML optimisés
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
                <option value="BUY_WEAK">BUY_WEAK</option>
                <option value="HOLD">HOLD</option>
                <option value="SELL_WEAK">SELL_WEAK</option>
                <option value="SELL_STRONG">SELL_STRONG</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Confiance minimale</label>
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
              <label className="block text-sm font-medium text-gray-700 mb-2">Confiance maximale</label>
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
                <option value="confidence_level">Confiance ML</option>
                <option value="potential_return">Retour potentiel</option>
                <option value="risk_score">Score de risque</option>
                <option value="date">Date d'analyse</option>
                <option value="symbol">Symbole</option>
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
                <XGBoostOpportunityCard
                  key={`${opportunity.symbol}-${opportunity.date}-${index}`}
                  opportunity={opportunity}
                  onAnalyze={handleAnalyzeSymbol}
                  onViewDetails={handleViewDetails}
                  onAgentAnalysis={handleAgentAnalysis}
                />
              ))}
            </div>
          </div>
        
      </div>

      {/* Modale d'analyse agent */}
      <AgentAnalysisModal
        isOpen={agentAnalysisModal.isOpen}
        onClose={handleCloseAgentAnalysis}
        symbol={agentAnalysisModal.symbol}
      />
    </div>
  );
};

export default OpportunitiesDashboard;
