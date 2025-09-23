import { InformationCircleIcon } from '@heroicons/react/24/outline'

interface DataStatsProps {
  stats?: {
    total_symbols: number
    total_historical_records: number
    total_technical_indicators: number
    total_sentiment_indicators: number
    total_ml_models: number
    total_predictions: number
    data_coverage: {
      symbols_with_technical: number
      symbols_with_sentiment: number
      technical_coverage_percentage: number
      sentiment_coverage_percentage: number
    }
    last_updated: string
  }
  loading?: boolean
}

export default function DataStats({ stats, loading }: DataStatsProps) {
  if (loading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-20 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (!stats) {
    return null
  }

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M'
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K'
    }
    return num.toString()
  }

  const formatPercentage = (num: number) => {
    return num.toFixed(1) + '%'
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center mb-4">
        <InformationCircleIcon className="h-5 w-5 text-blue-500 mr-2" />
        <h2 className="text-lg font-semibold text-gray-900">Statistiques des Données</h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Symboles</h3>
          <p className="text-2xl font-bold text-gray-900">{stats.total_symbols}</p>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Données Historiques</h3>
          <p className="text-2xl font-bold text-gray-900">{formatNumber(stats.total_historical_records)}</p>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Indicateurs Techniques</h3>
          <p className="text-2xl font-bold text-gray-900">{formatNumber(stats.total_technical_indicators)}</p>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Indicateurs de Sentiment</h3>
          <p className="text-2xl font-bold text-gray-900">{formatNumber(stats.total_sentiment_indicators)}</p>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Modèles ML</h3>
          <p className="text-2xl font-bold text-gray-900">{stats.total_ml_models}</p>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-sm font-medium text-gray-500 mb-2">Prédictions</h3>
          <p className="text-2xl font-bold text-gray-900">{formatNumber(stats.total_predictions)}</p>
        </div>
      </div>

      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-medium text-gray-900 mb-4">Couverture des Données</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Indicateurs Techniques</span>
              <span>{formatPercentage(stats.data_coverage.technical_coverage_percentage)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full"
                style={{ width: `${stats.data_coverage.technical_coverage_percentage}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {stats.data_coverage.symbols_with_technical} / {stats.total_symbols} symboles
            </p>
          </div>

          <div>
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Indicateurs de Sentiment</span>
              <span>{formatPercentage(stats.data_coverage.sentiment_coverage_percentage)}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full"
                style={{ width: `${stats.data_coverage.sentiment_coverage_percentage}%` }}
              ></div>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {stats.data_coverage.symbols_with_sentiment} / {stats.total_symbols} symboles
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4 text-xs text-gray-500">
        Dernière mise à jour: {new Date(stats.last_updated).toLocaleString('fr-FR')}
      </div>
    </div>
  )
}
