import { useQuery } from 'react-query'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'
import { apiService } from '@/services/api'
import LoadingSpinner from './LoadingSpinner'
import ErrorMessage from './ErrorMessage'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
)

interface PriceChartProps {
  symbol: string
  days?: number
}

export default function PriceChart({ symbol, days = 30 }: PriceChartProps) {
  const { data: historicalData, isLoading, error, refetch } = useQuery(
    ['historicalData', symbol, days],
    () => apiService.getHistoricalDataBySymbol(symbol, { limit: days }),
    {
      enabled: !!symbol,
      staleTime: 5 * 60 * 1000, // 5 minutes
    }
  )

  if (isLoading) {
    return <LoadingSpinner message="Chargement des données de prix..." />
  }

  if (error) {
    return (
      <ErrorMessage
        message="Erreur lors du chargement des données de prix"
        onRetry={() => refetch()}
      />
    )
  }

  if (!historicalData || historicalData.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        Aucune donnée disponible pour {symbol}
      </div>
    )
  }

  // Préparer les données pour le graphique
  const chartData = {
    labels: historicalData
      .slice()
      .reverse()
      .map((item) => new Date(item.date).toLocaleDateString('fr-FR')),
    datasets: [
      {
        label: 'Prix de clôture',
        data: historicalData
          .slice()
          .reverse()
          .map((item) => item.close),
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.1,
      },
      {
        label: 'VWAP',
        data: historicalData
          .slice()
          .reverse()
          .map((item) => item.vwap || item.close),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.1,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: $${context.parsed.y.toFixed(2)}`
          }
        }
      },
    },
    scales: {
      x: {
        display: true,
        title: {
          display: true,
          text: 'Date',
        },
      },
      y: {
        display: true,
        title: {
          display: true,
          text: 'Prix ($)',
        },
        ticks: {
          callback: function(value: any) {
            return '$' + value.toFixed(2)
          }
        }
      },
    },
    interaction: {
      mode: 'nearest' as const,
      axis: 'x' as const,
      intersect: false,
    },
  }

  // Calculer les statistiques
  const latestPrice = historicalData[0]?.close || 0
  const previousPrice = historicalData[1]?.close || latestPrice
  const change = latestPrice - previousPrice
  const changePercent = previousPrice !== 0 ? (change / previousPrice) * 100 : 0

  return (
    <div className="space-y-4">
      {/* Statistiques rapides */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div>
            <p className="text-sm text-gray-500">Prix actuel</p>
            <p className="text-2xl font-bold text-gray-900">${latestPrice.toFixed(2)}</p>
          </div>
          <div>
            <p className="text-sm text-gray-500">Variation</p>
            <p className={`text-lg font-semibold ${change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {change >= 0 ? '+' : ''}${change.toFixed(2)} ({changePercent >= 0 ? '+' : ''}{changePercent.toFixed(2)}%)
            </p>
          </div>
        </div>
        <div className="text-sm text-gray-500">
          {historicalData.length} jours de données
        </div>
      </div>

      {/* Graphique */}
      <div className="h-80">
        <Line data={chartData} options={options} />
      </div>
    </div>
  )
}
