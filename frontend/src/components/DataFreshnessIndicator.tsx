'use client'

import React, { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { dataUpdateApi, DataFreshnessStatus, MarketStatus } from '@/services/api'
import { 
  ClockIcon, 
  ExclamationTriangleIcon, 
  CheckCircleIcon,
  ArrowPathIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

interface DataFreshnessIndicatorProps {
  className?: string
  showDetails?: boolean
  compact?: boolean
}

export default function DataFreshnessIndicator({ 
  className = '', 
  showDetails = false,
  compact = false
}: DataFreshnessIndicatorProps) {
  const [isUpdating, setIsUpdating] = useState(false)

  // Récupérer le statut de fraîcheur des données
  const { 
    data: freshnessStatus, 
    isLoading: isLoadingFreshness,
    error: freshnessError,
    refetch: refetchFreshness
  } = useQuery({
    queryKey: ['data-freshness'],
    queryFn: dataUpdateApi.getDataFreshnessStatus,
    refetchInterval: 30000, // Rafraîchir toutes les 30 secondes
    retry: 3
  })

  // Récupérer le statut du marché
  const { 
    data: marketStatus, 
    isLoading: isLoadingMarket,
    error: marketError
  } = useQuery({
    queryKey: ['market-status'],
    queryFn: dataUpdateApi.getMarketStatus,
    refetchInterval: 60000, // Rafraîchir toutes les minutes
    retry: 3
  })

  // Fonction pour déclencher une mise à jour
  const handleUpdateData = async () => {
    setIsUpdating(true)
    try {
      await dataUpdateApi.updateAllData(false, 5) // Limiter à 5 symboles pour la démo
      await refetchFreshness()
    } catch (error) {
      console.error('Erreur lors de la mise à jour des données:', error)
    } finally {
      setIsUpdating(false)
    }
  }

  // Fonction pour formater la date
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric'
    })
  }

  // Fonction pour obtenir le statut et la couleur basé sur les données historiques uniquement
  const getStatusInfo = (historicalStatus: boolean, daysBehind: number | null) => {
    if (historicalStatus) {
      return {
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        icon: CheckCircleIcon,
        text: 'À jour'
      }
    } else if (daysBehind !== null && daysBehind <= 1) {
      return {
        color: 'text-yellow-600',
        bgColor: 'bg-yellow-50',
        icon: ExclamationTriangleIcon,
        text: 'Mise à jour recommandée'
      }
    } else if (daysBehind !== null && daysBehind <= 3) {
      return {
        color: 'text-orange-600',
        bgColor: 'bg-orange-50',
        icon: ExclamationTriangleIcon,
        text: 'Mise à jour nécessaire'
      }
    } else {
      return {
        color: 'text-red-600',
        bgColor: 'bg-red-50',
        icon: ExclamationTriangleIcon,
        text: 'Mise à jour urgente'
      }
    }
  }

  if (isLoadingFreshness || isLoadingMarket) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
        <span className="text-sm text-gray-600">Chargement...</span>
      </div>
    )
  }

  if (freshnessError || marketError) {
    return (
      <div className={`flex items-center space-x-2 ${className}`}>
        <ExclamationTriangleIcon className="h-4 w-4 text-red-500" />
        <span className="text-sm text-red-600">Erreur de chargement</span>
      </div>
    )
  }

  const statusInfo = getStatusInfo(
    freshnessStatus?.historical_data?.is_fresh || false,
    freshnessStatus?.historical_data?.days_behind || null
  )
  const StatusIcon = statusInfo.icon

  // Version compacte
  if (compact) {
    return (
      <div className={`flex items-center justify-between ${className}`}>
        <div className="flex items-center space-x-2">
          <StatusIcon className={`h-4 w-4 ${statusInfo.color}`} />
          <span className={`text-sm font-medium ${statusInfo.color}`}>
            Données historiques {statusInfo.text}
          </span>
        </div>
        
        <button
          onClick={handleUpdateData}
          disabled={isUpdating}
          className={`flex items-center space-x-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
            isUpdating 
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {isUpdating ? (
            <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
          ) : (
            <ArrowPathIcon className="h-3 w-3" />
          )}
        </button>
      </div>
    )
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Indicateur principal */}
      <div className={`flex items-center justify-between p-3 rounded-lg border ${statusInfo.bgColor}`}>
        <div className="flex items-center space-x-3">
          <StatusIcon className={`h-5 w-5 ${statusInfo.color}`} />
          <div>
            <p className={`text-sm font-medium ${statusInfo.color}`}>
              Données historiques {statusInfo.text}
            </p>
            {freshnessStatus && (
              <p className="text-xs text-gray-500">
                Dernier trading: {formatDate(freshnessStatus.last_trading_day)}
                {freshnessStatus.historical_data.days_behind !== null && (
                  <span className="ml-2">
                    ({freshnessStatus.historical_data.days_behind} jour{freshnessStatus.historical_data.days_behind > 1 ? 's' : ''} de retard)
                  </span>
                )}
              </p>
            )}
          </div>
        </div>
        
        <button
          onClick={handleUpdateData}
          disabled={isUpdating}
          className={`flex items-center space-x-1 px-3 py-1 rounded-md text-xs font-medium transition-colors ${
            isUpdating 
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed' 
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {isUpdating ? (
            <>
              <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-white"></div>
              <span>Mise à jour...</span>
            </>
          ) : (
            <>
              <ArrowPathIcon className="h-3 w-3" />
              <span>Mettre à jour</span>
            </>
          )}
        </button>
      </div>

      {/* Détails si demandés */}
      {showDetails && freshnessStatus && (
        <div className="bg-white border rounded-lg p-4 space-y-3">
          <h4 className="text-sm font-medium text-gray-900 flex items-center">
            <ChartBarIcon className="h-4 w-4 mr-2" />
            Détails des Données Historiques
          </h4>
          
          {/* Données historiques - Focus principal */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Données historiques:</span>
              <span className={`text-sm font-medium ${
                freshnessStatus.historical_data.is_fresh ? 'text-green-600' : 'text-yellow-600'
              }`}>
                {freshnessStatus.historical_data.is_fresh ? 'À jour' : 'Mise à jour nécessaire'}
              </span>
            </div>
            <div className="text-xs text-gray-500 space-y-1">
              <p>Dernière date: {formatDate(freshnessStatus.historical_data.latest_date)}</p>
              {freshnessStatus.historical_data.days_behind !== null && (
                <p>Retard: {freshnessStatus.historical_data.days_behind} jour{freshnessStatus.historical_data.days_behind > 1 ? 's' : ''}</p>
              )}
            </div>
          </div>

          {/* Statut du marché */}
          {marketStatus && (
            <div className="pt-2 border-t">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Marché Nasdaq:</span>
                <span className={`text-sm font-medium ${
                  marketStatus.is_open ? 'text-green-600' : 'text-gray-600'
                }`}>
                  {marketStatus.is_open ? 'Ouvert' : 'Fermé'}
                </span>
              </div>
              <div className="text-xs text-gray-500 mt-1">
                <p>Fuseau horaire: {marketStatus.timezone_info.market_timezone}</p>
                <p>Serveur: {marketStatus.timezone_info.server_timezone}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
