'use client';

import React from 'react';
import { useRequireAuth } from '@/contexts/AuthContext';
import AppLayout from '@/components/Layout/AppLayout';
import { PortfolioList } from '@/components/Portfolio/PortfolioList';

export default function PortfoliosPage() {
  const { isAuthenticated, isLoading } = useRequireAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <svg className="animate-spin mx-auto h-12 w-12 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p className="mt-4 text-lg text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <AppLayout>
      <div className="space-y-6">
        {/* En-tête */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <h1 className="text-2xl font-bold text-gray-900">💼 Portefeuilles</h1>
          <p className="mt-2 text-gray-600">
            Gérez vos portefeuilles d'investissement et suivez leurs performances
          </p>
        </div>

        {/* Liste des portefeuilles */}
        <PortfolioList />
      </div>
    </AppLayout>
  );
}
