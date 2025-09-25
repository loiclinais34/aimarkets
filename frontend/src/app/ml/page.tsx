'use client';

import React from 'react';
import RootLayout from '@/components/RootLayout';
import Link from 'next/link';
import {
  Cog6ToothIcon,
  ChartBarIcon,
  BeakerIcon,
} from '@heroicons/react/24/outline';

const mlFeatures = [
  {
    name: 'Paramétrage',
    description: 'Configurez les paramètres des modèles ML et les cibles de trading',
    href: '/ml/parameters',
    icon: Cog6ToothIcon,
    color: 'bg-blue-500',
  },
  {
    name: 'Comparaisons',
    description: 'Comparez les performances de différents modèles ML',
    href: '/ml/comparisons',
    icon: ChartBarIcon,
    color: 'bg-green-500',
  },
  {
    name: 'Prédictions',
    description: 'Générez des prédictions avec vos modèles entraînés',
    href: '/ml/predictions',
    icon: BeakerIcon,
    color: 'bg-purple-500',
  },
];

export default function MLPage() {
  return (
    <RootLayout>
      <div className="px-4 py-6 sm:px-0">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Modèles ML</h1>
          <p className="mt-2 text-gray-600">
            Gérez vos modèles de machine learning et leurs performances
          </p>
        </div>

        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {mlFeatures.map((feature) => (
            <Link
              key={feature.name}
              href={feature.href}
              className="group relative bg-white p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-gray-200 hover:border-gray-300"
            >
              <div>
                <span className={`${feature.color} rounded-lg inline-flex p-3 ring-4 ring-white`}>
                  <feature.icon className="h-6 w-6 text-white" />
                </span>
              </div>
              <div className="mt-8">
                <h3 className="text-lg font-medium text-gray-900 group-hover:text-blue-600">
                  {feature.name}
                </h3>
                <p className="mt-2 text-sm text-gray-500">
                  {feature.description}
                </p>
              </div>
              <span
                className="absolute top-6 right-6 text-gray-300 group-hover:text-gray-400"
                aria-hidden="true"
              >
                →
              </span>
            </Link>
          ))}
        </div>
      </div>
    </RootLayout>
  );
}
