/**
 * Page Opportunités - Recherche et filtrage des opportunités
 */

'use client';

import React, { useState, useEffect } from 'react';
import { useRequireAuth } from '@/contexts/AuthContext';
import AppLayout from '@/components/Layout/AppLayout';
import OpportunitiesDashboard from '@/components/AdvancedAnalysis/OpportunitiesDashboard';

export default function OpportunitiesPage() {
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
          <h1 className="text-2xl font-bold text-gray-900">🎯 Opportunités</h1>
          <p className="mt-2 text-gray-600">
            Découvrez les meilleures opportunités d'investissement basées sur l'analyse avancée et le machine learning
          </p>
        </div>

        {/* Dashboard des opportunités */}
        <OpportunitiesDashboard />
      </div>
    </AppLayout>
  );
}
