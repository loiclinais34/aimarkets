'use client'

import React, { useState, useMemo } from 'react'
import {
  ComposedChart,
  Line,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Legend
} from 'recharts'
import { TrendingUp, TrendingDown, Activity } from 'lucide-react'

interface ChartData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  vwap?: number
  sma_20?: number
  sma_50?: number
  ema_20?: number
  bb_upper?: number
  bb_middle?: number
  bb_lower?: number
  rsi_14?: number
  macd?: number
  macd_signal?: number
}

interface TechnicalIndicators {
  sma_20?: number
  sma_50?: number
  ema_20?: number
  rsi_14?: number
  macd?: number
  macd_signal?: number
  bb_upper?: number
  bb_middle?: number
  bb_lower?: number
  atr_14?: number
  obv?: number
}

interface TechnicalChartProps {
  chartData: ChartData[]
  technicalIndicators: TechnicalIndicators
  symbol: string
  height?: number
}

interface CandlestickData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  change: number
  changePercent: number
}

export default function TechnicalChart({
  chartData,
  technicalIndicators,
  symbol,
  height = 400
}: TechnicalChartProps) {
  const [activeChart, setActiveChart] = useState<'price' | 'volume' | 'rsi' | 'macd'>('price')

  // Transformer les données pour les candlesticks
  const candlestickData = useMemo(() => {
    return chartData.map((item, index) => {
      const change = item.close - item.open
      const changePercent = (change / item.open) * 100
      
      return {
        date: new Date(item.date).toLocaleDateString('fr-FR', { 
          month: 'short', 
          day: 'numeric' 
        }),
        fullDate: item.date,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
        volume: item.volume,
        change,
        changePercent,
        sma_20: item.sma_20,
        sma_50: item.sma_50,
        ema_20: item.ema_20,
        bb_upper: item.bb_upper,
        bb_middle: item.bb_middle,
        bb_lower: item.bb_lower,
        rsi_14: item.rsi_14,
        macd: item.macd,
        macd_signal: item.macd_signal
      }
    })
  }, [chartData])

  // Fonction pour calculer les niveaux de support et résistance
  const calculateSupportResistance = (data: CandlestickData[]) => {
    if (data.length < 20) return { support: [], resistance: [] }
    
    // Prendre les 20 dernières périodes pour le calcul
    const recentData = data.slice(-20)
    
    // Trouver les plus hauts et plus bas locaux
    const highs: number[] = []
    const lows: number[] = []
    
    for (let i = 1; i < recentData.length - 1; i++) {
      const current = recentData[i]
      const prev = recentData[i - 1]
      const next = recentData[i + 1]
      
      // Plus haut local (pivot haut)
      if (current.high > prev.high && current.high > next.high) {
        highs.push(current.high)
      }
      
      // Plus bas local (pivot bas)
      if (current.low < prev.low && current.low < next.low) {
        lows.push(current.low)
      }
    }
    
    // Calculer les niveaux de résistance (plus hauts significatifs)
    const resistanceLevels = highs
      .sort((a, b) => b - a)
      .slice(0, 3) // Top 3
      .filter(level => level > data[data.length - 1].close) // Au-dessus du prix actuel
    
    // Calculer les niveaux de support (plus bas significatifs)
    const supportLevels = lows
      .sort((a, b) => a - b)
      .slice(0, 3) // Top 3
      .filter(level => level < data[data.length - 1].close) // En-dessous du prix actuel
    
    // Ajouter des niveaux psychologiques basés sur le prix actuel
    const currentPrice = data[data.length - 1].close
    const psychologicalLevels = []
    
    // Niveaux psychologiques (arrondis)
    const roundToNearest = (price: number, roundTo: number) => {
      return Math.round(price / roundTo) * roundTo
    }
    
    // Niveaux de résistance psychologiques
    const resistance50 = roundToNearest(currentPrice + (currentPrice * 0.05), 5) // +5%
    const resistance100 = roundToNearest(currentPrice + (currentPrice * 0.10), 10) // +10%
    
    // Niveaux de support psychologiques
    const support50 = roundToNearest(currentPrice - (currentPrice * 0.05), 5) // -5%
    const support100 = roundToNearest(currentPrice - (currentPrice * 0.10), 10) // -10%
    
    // Combiner et dédupliquer les niveaux
    const allResistance = [...resistanceLevels, resistance50, resistance100]
      .filter((level, index, arr) => arr.indexOf(level) === index) // Dédupliquer
      .sort((a, b) => a - b)
      .slice(0, 3) // Garder les 3 plus proches
    
    const allSupport = [...supportLevels, support50, support100]
      .filter((level, index, arr) => arr.indexOf(level) === index) // Dédupliquer
      .sort((a, b) => b - a)
      .slice(0, 3) // Garder les 3 plus proches
    
    return {
      support: allSupport,
      resistance: allResistance
    }
  }

  // Calculer les statistiques et les niveaux de support/résistance
  const stats = useMemo(() => {
    if (candlestickData.length === 0) return null
    
    const latest = candlestickData[candlestickData.length - 1]
    const previous = candlestickData[candlestickData.length - 2]
    
    const priceChange = latest.close - (previous?.close || latest.open)
    const priceChangePercent = ((priceChange / (previous?.close || latest.open)) * 100)
    
    const avgVolume = candlestickData.reduce((sum, item) => sum + item.volume, 0) / candlestickData.length
    
    // Calculer les niveaux de support et résistance
    const supportResistanceLevels = calculateSupportResistance(candlestickData)
    
    return {
      currentPrice: latest.close,
      priceChange,
      priceChangePercent,
      currentVolume: latest.volume,
      avgVolume,
      volumeChange: latest.volume - avgVolume,
      volumeChangePercent: ((latest.volume - avgVolume) / avgVolume) * 100,
      supportResistance: supportResistanceLevels
    }
  }, [candlestickData])

  const formatPrice = (value: number) => {
    return `$${value.toFixed(2)}`
  }

  const formatVolume = (value: number) => {
    if (value >= 1e9) return `${(value / 1e9).toFixed(1)}B`
    if (value >= 1e6) return `${(value / 1e6).toFixed(1)}M`
    if (value >= 1e3) return `${(value / 1e3).toFixed(1)}K`
    return value.toString()
  }

  const formatPercent = (value: number) => {
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{data.fullDate}</p>
          <div className="space-y-1 mt-2">
            <div className="flex justify-between gap-4">
              <span className="text-gray-600">Ouverture:</span>
              <span className="font-medium">{formatPrice(data.open)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-gray-600">Plus haut:</span>
              <span className="font-medium text-green-600">{formatPrice(data.high)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-gray-600">Plus bas:</span>
              <span className="font-medium text-red-600">{formatPrice(data.low)}</span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-gray-600">Fermeture:</span>
              <span className={`font-medium ${data.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {formatPrice(data.close)}
              </span>
            </div>
            <div className="flex justify-between gap-4">
              <span className="text-gray-600">Volume:</span>
              <span className="font-medium">{formatVolume(data.volume)}</span>
            </div>
            {data.change !== undefined && (
              <div className="flex justify-between gap-4">
                <span className="text-gray-600">Variation:</span>
                <span className={`font-medium ${data.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercent(data.changePercent)}
                </span>
              </div>
            )}
          </div>
        </div>
      )
    }
    return null
  }

  const renderChart = () => {
    switch (activeChart) {
      case 'price':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <ComposedChart data={candlestickData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="date" 
                stroke="#666"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                domain={['dataMin - 5', 'dataMax + 5']}
                stroke="#666"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={formatPrice}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              
              {/* Bollinger Bands */}
              {candlestickData[0]?.bb_upper && (
                <>
                  <Line
                    type="monotone"
                    dataKey="bb_upper"
                    stroke="#ff6b6b"
                    strokeWidth={1.5}
                    dot={false}
                    name="BB Upper"
                    strokeDasharray="3 3"
                  />
                  <Line
                    type="monotone"
                    dataKey="bb_middle"
                    stroke="#4ecdc4"
                    strokeWidth={2}
                    dot={false}
                    name="BB Middle (SMA 20)"
                  />
                  <Line
                    type="monotone"
                    dataKey="bb_lower"
                    stroke="#ff6b6b"
                    strokeWidth={1.5}
                    dot={false}
                    name="BB Lower"
                    strokeDasharray="3 3"
                  />
                </>
              )}
              
              {/* Moving Averages */}
              {candlestickData[0]?.sma_20 && (
                <Line
                  type="monotone"
                  dataKey="sma_20"
                  stroke="#3b82f6"
                  strokeWidth={2.5}
                  dot={false}
                  name="SMA 20"
                />
              )}
              
              {candlestickData[0]?.sma_50 && (
                <Line
                  type="monotone"
                  dataKey="sma_50"
                  stroke="#f59e0b"
                  strokeWidth={2.5}
                  dot={false}
                  name="SMA 50"
                />
              )}
              
              {candlestickData[0]?.ema_20 && (
                <Line
                  type="monotone"
                  dataKey="ema_20"
                  stroke="#8b5cf6"
                  strokeWidth={2}
                  dot={false}
                  name="EMA 20"
                  strokeDasharray="5 5"
                />
              )}
              
              {/* Price Line */}
              <Line
                type="monotone"
                dataKey="close"
                stroke="#1f2937"
                strokeWidth={3}
                dot={false}
                name="Prix de clôture"
              />
              
              {/* Support and Resistance Lines */}
              {stats?.supportResistance && (
                <>
                  {/* Support Lines */}
                  {stats.supportResistance.support.map((level, index) => (
                    <ReferenceLine
                      key={`support-${index}`}
                      y={level}
                      stroke="#10b981"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      label={{ 
                        value: `Support ${formatPrice(level)}`, 
                        position: "topLeft",
                        style: { fontSize: '10px', fill: '#10b981' }
                      }}
                    />
                  ))}
                  
                  {/* Resistance Lines */}
                  {stats.supportResistance.resistance.map((level, index) => (
                    <ReferenceLine
                      key={`resistance-${index}`}
                      y={level}
                      stroke="#ef4444"
                      strokeWidth={2}
                      strokeDasharray="5 5"
                      label={{ 
                        value: `Résistance ${formatPrice(level)}`, 
                        position: "topRight",
                        style: { fontSize: '10px', fill: '#ef4444' }
                      }}
                    />
                  ))}
                </>
              )}
            </ComposedChart>
          </ResponsiveContainer>
        )

      case 'volume':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <ComposedChart data={candlestickData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="date" 
                stroke="#666"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                stroke="#666"
                fontSize={12}
                tickLine={false}
                axisLine={false}
                tickFormatter={formatVolume}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              
              {/* Volume Bars */}
              <Bar
                dataKey="volume"
                fill="#3b82f6"
                opacity={0.7}
                name="Volume"
              />
              
              {/* Average Volume Line */}
              {stats && (
                <ReferenceLine
                  y={stats.avgVolume}
                  stroke="#ef4444"
                  strokeDasharray="5 5"
                  label={{ value: "Volume Moyen", position: "topRight" }}
                />
              )}
            </ComposedChart>
          </ResponsiveContainer>
        )

      case 'rsi':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <ComposedChart data={candlestickData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="date" 
                stroke="#666"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                domain={[0, 100]}
                stroke="#666"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              
              {/* RSI Line */}
              <Line
                type="monotone"
                dataKey="rsi_14"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={false}
                name="RSI 14"
              />
              
              {/* RSI Levels */}
              <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="5 5" label={{ value: "Surachat (70)", position: "topRight" }} />
              <ReferenceLine y={30} stroke="#10b981" strokeDasharray="5 5" label={{ value: "Survente (30)", position: "bottomRight" }} />
              <ReferenceLine y={50} stroke="#6b7280" strokeDasharray="2 2" />
            </ComposedChart>
          </ResponsiveContainer>
        )

      case 'macd':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <ComposedChart data={candlestickData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="date" 
                stroke="#666"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <YAxis 
                stroke="#666"
                fontSize={12}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              
              {/* MACD Line */}
              <Line
                type="monotone"
                dataKey="macd"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={false}
                name="MACD"
              />
              
              {/* MACD Signal */}
              <Line
                type="monotone"
                dataKey="macd_signal"
                stroke="#ef4444"
                strokeWidth={2}
                dot={false}
                name="Signal MACD"
              />
              
              {/* Zero Line */}
              <ReferenceLine y={0} stroke="#6b7280" strokeDasharray="2 2" />
            </ComposedChart>
          </ResponsiveContainer>
        )

      default:
        return null
    }
  }

  if (!candlestickData.length) {
    return (
      <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
        <p className="text-gray-500">Aucune donnée disponible pour le graphique</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Statistiques rapides */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white p-3 rounded-lg border">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">Prix actuel</span>
            </div>
            <p className="text-lg font-bold text-gray-900">{formatPrice(stats.currentPrice)}</p>
            <p className={`text-sm ${stats.priceChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatPercent(stats.priceChangePercent)}
            </p>
            {/* Distance aux niveaux clés */}
            {stats.supportResistance && (
              <div className="mt-2 text-xs text-gray-500">
                {stats.supportResistance.support.length > 0 && (
                  <p>Proche support: {formatPrice(stats.supportResistance.support[0])}</p>
                )}
                {stats.supportResistance.resistance.length > 0 && (
                  <p>Proche résistance: {formatPrice(stats.supportResistance.resistance[0])}</p>
                )}
              </div>
            )}
          </div>
          
          <div className="bg-white p-3 rounded-lg border">
            <div className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4 text-gray-500" />
              <span className="text-sm text-gray-600">Volume</span>
            </div>
            <p className="text-lg font-bold text-gray-900">{formatVolume(stats.currentVolume)}</p>
            <p className={`text-sm ${stats.volumeChange >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatPercent(stats.volumeChangePercent)}
            </p>
          </div>
          
          <div className="bg-white p-3 rounded-lg border">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">SMA 50</span>
            </div>
            <p className="text-lg font-bold text-gray-900">
              {technicalIndicators.sma_50 ? formatPrice(technicalIndicators.sma_50) : 'N/A'}
            </p>
            <p className="text-sm text-gray-500">
              {technicalIndicators.sma_50 && stats ? 
                (stats.currentPrice > technicalIndicators.sma_50 ? 'Au-dessus' : 'En-dessous') : 
                'N/A'}
            </p>
          </div>
          
          <div className="bg-white p-3 rounded-lg border">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">RSI</span>
            </div>
            <p className="text-lg font-bold text-gray-900">
              {technicalIndicators.rsi_14?.toFixed(1) || 'N/A'}
            </p>
            <p className="text-sm text-gray-500">
              {technicalIndicators.rsi_14 ? 
                (technicalIndicators.rsi_14 > 70 ? 'Surachat' : 
                 technicalIndicators.rsi_14 < 30 ? 'Survente' : 'Neutre') : 
                'N/A'}
            </p>
          </div>
          
          <div className="bg-white p-3 rounded-lg border">
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">MACD</span>
            </div>
            <p className="text-lg font-bold text-gray-900">
              {technicalIndicators.macd?.toFixed(3) || 'N/A'}
            </p>
            <p className="text-sm text-gray-500">
              {technicalIndicators.macd && technicalIndicators.macd_signal ? 
                (technicalIndicators.macd > technicalIndicators.macd_signal ? 'Haussier' : 'Baissier') : 
                'N/A'}
            </p>
          </div>
        </div>
      )}

      {/* Niveaux de Support et Résistance */}
      {stats?.supportResistance && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Support Levels */}
          <div className="bg-white p-4 rounded-lg border">
            <h4 className="text-sm font-medium text-gray-900 mb-3 flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full"></div>
              Niveaux de Support
            </h4>
            <div className="space-y-2">
              {stats.supportResistance.support.length > 0 ? (
                stats.supportResistance.support.map((level, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Support {index + 1}</span>
                    <span className="text-sm font-medium text-green-600">{formatPrice(level)}</span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500">Aucun niveau de support identifié</p>
              )}
            </div>
          </div>

          {/* Resistance Levels */}
          <div className="bg-white p-4 rounded-lg border">
            <h4 className="text-sm font-medium text-gray-900 mb-3 flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              Niveaux de Résistance
            </h4>
            <div className="space-y-2">
              {stats.supportResistance.resistance.length > 0 ? (
                stats.supportResistance.resistance.map((level, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Résistance {index + 1}</span>
                    <span className="text-sm font-medium text-red-600">{formatPrice(level)}</span>
                  </div>
                ))
              ) : (
                <p className="text-sm text-gray-500">Aucun niveau de résistance identifié</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Onglets de graphiques */}
      <div className="bg-white rounded-lg border">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {[
              { key: 'price', label: 'Prix & Moyennes', icon: TrendingUp },
              { key: 'volume', label: 'Volume', icon: Activity },
              { key: 'rsi', label: 'RSI', icon: TrendingDown },
              { key: 'macd', label: 'MACD', icon: TrendingUp }
            ].map(({ key, label, icon: Icon }) => (
              <button
                key={key}
                onClick={() => setActiveChart(key as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                  activeChart === key
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </nav>
        </div>
        
        <div className="p-6">
          {renderChart()}
        </div>
      </div>
    </div>
  )
}
