'use client';

import React from 'react';
import RootLayout from '@/components/RootLayout';
import DashboardStats from '@/components/DashboardStats';
import DataUpdateControls from '@/components/DataUpdateControls';
import OpportunitySearch from '@/components/OpportunitySearch';
import OpportunityCart from '@/components/OpportunityCart';
import CartDebug from '@/components/CartDebug';
import dynamic from 'next/dynamic';

// Import dynamique du composant OpportunitiesBySymbol
const OpportunitiesBySymbol = dynamic(() => import('@/components/OpportunitiesBySymbol'), {
  ssr: false,
  loading: () => (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <StarIcon className="h-5 w-5 mr-2 text-yellow-600" />
        Opportunités par Titre
      </h3>
      <div className="space-y-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="h-20 bg-gray-200 rounded-lg"></div>
          </div>
        ))}
      </div>
      <div className="mt-4 text-sm text-gray-500 text-center">
        Chargement des opportunités...
      </div>
    </div>
  )
});
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
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
              <p className="mt-2 text-gray-600">
                Vue d'ensemble de votre plateforme AIMarkets
              </p>
            </div>
            <OpportunityCart />
          </div>
        </div>

        {/* Stats Grid */}
        <DashboardStats className="mb-8" />

        {/* Recherche d'opportunités */}
        <OpportunitySearch className="mb-8" />

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Contrôles de mise à jour des données */}
          <div className="lg:col-span-1">
            <DataUpdateControls />
          </div>

          {/* Opportunités par titre */}
          <div className="lg:col-span-2">
            <OpportunitiesBySymbol />
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
      <CartDebug />
    </RootLayout>
  );
}
