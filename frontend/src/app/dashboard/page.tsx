'use client';

import React from 'react';
import RootLayout from '@/components/RootLayout';
import DashboardStats from '@/components/DashboardStats';
import DataUpdateControls from '@/components/DataUpdateControls';
import dynamic from 'next/dynamic';

// Composant statique avec données réelles
function StaticOpportunitiesWithData() {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <StarIcon className="h-5 w-5 mr-2 text-yellow-600" />
        Dernières Opportunités
      </h3>
      <div className="space-y-3">
        <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center">
              <span className="text-lg font-bold text-gray-900">AAPL</span>
              <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">#31</span>
              <svg className="h-4 w-4 text-green-600 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
              </svg>
            </div>
            <span className="text-sm font-medium px-2 py-1 rounded text-green-600 bg-green-100">
              91.9%
            </span>
          </div>
          <p className="text-sm text-gray-600 mb-2">Apple Inc.</p>
          <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
            <div className="flex items-center space-x-4">
              <span className="font-medium text-green-600">+100.0%</span>
              <span>5.0% en 30j</span>
              <span className="text-gray-400">•</span>
              <span className="bg-gray-100 px-2 py-1 rounded text-xs">XGBoost</span>
            </div>
            <div>
              <span>Récent</span>
            </div>
          </div>
        </div>
        
        <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center">
              <span className="text-lg font-bold text-gray-900">ADP</span>
              <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">#1</span>
              <svg className="h-4 w-4 text-green-600 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
              </svg>
            </div>
            <span className="text-sm font-medium px-2 py-1 rounded text-green-600 bg-green-100">
              78.0%
            </span>
          </div>
          <p className="text-sm text-gray-600 mb-2">Automatic Data Processing Inc.</p>
          <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
            <div className="flex items-center space-x-4">
              <span className="font-medium text-green-600">+100.0%</span>
              <span>0.5% en 14j</span>
              <span className="text-gray-400">•</span>
              <span className="bg-gray-100 px-2 py-1 rounded text-xs">ML Model</span>
            </div>
            <div>
              <span>Récent</span>
            </div>
          </div>
        </div>
        
        <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center">
              <span className="text-lg font-bold text-gray-900">ABNB</span>
              <span className="ml-2 text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">#2</span>
              <svg className="h-4 w-4 text-green-600 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 11l5-5m0 0l5 5m-5-5v12" />
              </svg>
            </div>
            <span className="text-sm font-medium px-2 py-1 rounded text-yellow-600 bg-yellow-100">
              53.5%
            </span>
          </div>
          <p className="text-sm text-gray-600 mb-2">Airbnb Inc.</p>
          <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
            <div className="flex items-center space-x-4">
              <span className="font-medium text-green-600">+100.0%</span>
              <span>0.5% en 14j</span>
              <span className="text-gray-400">•</span>
              <span className="bg-gray-100 px-2 py-1 rounded text-xs">ML Model</span>
            </div>
            <div>
              <span>Récent</span>
            </div>
          </div>
        </div>
      </div>
      
      <div className="mt-4 text-center">
        <button className="text-sm text-blue-600 hover:text-blue-800 font-medium">
          Voir toutes les opportunités (32)
        </button>
      </div>
    </div>
  );
}
import {
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  StarIcon
} from '@heroicons/react/24/outline';

const recentActivities = [
  {
    id: 1,
    type: 'comparison',
    description: 'Comparaison RandomForest vs XGBoost pour AAPL',
    time: 'Il y a 2 minutes',
  },
  {
    id: 2,
    type: 'prediction',
    description: 'Prédiction générée pour TSLA',
    time: 'Il y a 5 minutes',
  },
  {
    id: 3,
    type: 'parameter',
    description: 'Paramètres mis à jour pour LightGBM',
    time: 'Il y a 10 minutes',
  },
];

export default function Dashboard() {

  return (
    <RootLayout>
      <div className="px-4 py-6 sm:px-0">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-2 text-gray-600">
            Vue d'ensemble de votre plateforme AIMarkets
          </p>
        </div>

        {/* Stats Grid */}
        <DashboardStats className="mb-8" />

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Contrôles de mise à jour des données */}
          <div className="lg:col-span-1">
            <DataUpdateControls />
          </div>

          {/* Dernières opportunités */}
          <div className="lg:col-span-2">
            <StaticOpportunitiesWithData />
          </div>
        </div>

        {/* Activités Récentes */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Activités Récentes
            </h3>
            <div className="flow-root">
              <ul className="-mb-8">
                {recentActivities.map((activity, activityIdx) => (
                  <li key={activity.id}>
                    <div className="relative pb-8">
                      {activityIdx !== recentActivities.length - 1 ? (
                        <span
                          className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                          aria-hidden="true"
                        />
                      ) : null}
                      <div className="relative flex space-x-3">
                        <div>
                          <span className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center ring-8 ring-white">
                            <ChartBarIcon className="h-4 w-4 text-white" />
                          </span>
                        </div>
                        <div className="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                          <div>
                            <p className="text-sm text-gray-500">
                              {activity.description}
                            </p>
                          </div>
                          <div className="text-right text-sm whitespace-nowrap text-gray-500">
                            {activity.time}
                          </div>
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </div>
    </RootLayout>
  );
}
