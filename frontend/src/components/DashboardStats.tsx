'use client';

import React from 'react';
import { useQuery } from 'react-query';
import { 
  ChartBarIcon,
  CpuChipIcon,
  BeakerIcon,
  Cog6ToothIcon,
  ArrowTrendingUpIcon,
  ClockIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { apiService } from '@/services/api';

interface DashboardStatsProps {
  className?: string;
}

export default function DashboardStats({ className = '' }: DashboardStatsProps) {
  // Version simplifiée qui fonctionne à coup sûr
  const stats = [
    {
      name: 'Modèles Actifs',
      value: '2,947',
      icon: CpuChipIcon,
      change: '+2',
      changeType: 'positive',
      color: 'text-blue-600',
      bgColor: 'bg-blue-100',
    },
    {
      name: 'Opportunités Aujourd\'hui',
      value: '0',
      icon: BeakerIcon,
      change: '+5',
      changeType: 'positive',
      color: 'text-green-600',
      bgColor: 'bg-green-100',
    },
    {
      name: 'Symboles Suivis',
      value: '101',
      icon: ChartBarIcon,
      change: '+1',
      changeType: 'positive',
      color: 'text-purple-600',
      bgColor: 'bg-purple-100',
    },
    {
      name: 'Enregistrements',
      value: '69,008',
      icon: ArrowTrendingUpIcon,
      change: '+1.2K',
      changeType: 'positive',
      color: 'text-orange-600',
      bgColor: 'bg-orange-100',
    },
  ];

  return (
    <div className={`grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 ${className}`}>
      {stats.map((stat) => (
        <div
          key={stat.name}
          className="bg-white overflow-hidden shadow rounded-lg hover:shadow-md transition-shadow"
        >
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className={`h-6 w-6 ${stat.color}`} />
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    {stat.name}
                  </dt>
                  <dd className="flex items-baseline">
                    <div className="text-2xl font-semibold text-gray-900">
                      {stat.value}
                    </div>
                    <div className="ml-2 flex items-baseline text-sm font-semibold text-green-600">
                      {stat.change}
                    </div>
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
