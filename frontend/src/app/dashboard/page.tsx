'use client';

import React from 'react';
import RootLayout from '@/components/RootLayout';
import DashboardStats from '@/components/DashboardStats';
import DataUpdateControls from '@/components/DataUpdateControls';
import LatestOpportunities from '@/components/LatestOpportunities';
import {
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon
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
            <LatestOpportunities />
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
