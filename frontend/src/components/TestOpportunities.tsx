'use client';

import React, { useState, useEffect } from 'react';
import { StarIcon } from '@heroicons/react/24/outline';

export default function TestOpportunities() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('🎯 TestOpportunities useEffect déclenché');
    
    const fetchData = async () => {
      try {
        console.log('🔍 TestOpportunities: Début du fetch');
        setLoading(true);
        setError(null);
        
        const response = await fetch('/api/v1/screener/latest-opportunities');
        console.log('📡 TestOpportunities: Response status:', response.status);
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        console.log('✅ TestOpportunities: Résultat:', result);
        console.log('✅ TestOpportunities: Type:', typeof result);
        console.log('✅ TestOpportunities: Length:', Array.isArray(result) ? result.length : 'N/A');
        
        setData(result);
      } catch (err) {
        console.error('❌ TestOpportunities: Erreur:', err);
        setError(err instanceof Error ? err.message : 'Erreur inconnue');
      } finally {
        console.log('✅ TestOpportunities: setIsLoading(false)');
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  console.log('🔄 TestOpportunities render - loading:', loading, 'error:', error, 'data:', data);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <StarIcon className="h-5 w-5 mr-2 text-yellow-600" />
          Test Opportunités (Chargement...)
        </h3>
        <div className="text-sm text-gray-500">
          Loading: {loading.toString()}, Error: {error || 'null'}, Data: {data ? 'loaded' : 'null'}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <StarIcon className="h-5 w-5 mr-2 text-red-600" />
          Test Opportunités (Erreur)
        </h3>
        <div className="text-sm text-red-500">
          Erreur: {error}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
        <StarIcon className="h-5 w-5 mr-2 text-green-600" />
        Test Opportunités (Succès)
      </h3>
      <div className="text-sm text-gray-500 mb-4">
        Données chargées: {Array.isArray(data) ? data.length : 'N/A'} opportunités
      </div>
      {Array.isArray(data) && data.length > 0 && (
        <div className="space-y-2">
          {data.slice(0, 3).map((item: any, index: number) => (
            <div key={index} className="p-2 bg-gray-50 rounded">
              <div className="font-medium">{item.symbol}</div>
              <div className="text-sm text-gray-600">{item.company_name}</div>
              <div className="text-sm text-blue-600">Confiance: {(item.confidence * 100).toFixed(1)}%</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
