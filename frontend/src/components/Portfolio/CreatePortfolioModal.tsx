'use client';

import React, { useState } from 'react';
import { CreatePortfolioRequest } from '@/services/portfolioApi';

interface CreatePortfolioModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: CreatePortfolioRequest) => void;
  isLoading?: boolean;
}

export const CreatePortfolioModal: React.FC<CreatePortfolioModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<CreatePortfolioRequest>({
    name: '',
    description: '',
    portfolio_type: 'personal',
    initial_capital: 0,
    risk_tolerance: 'MODERATE',
    currency: 'EUR',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    const newErrors: Record<string, string> = {};
    if (!formData.name.trim()) {
      newErrors.name = 'Le nom est requis';
    }
    if (formData.initial_capital !== undefined && formData.initial_capital < 0) {
      newErrors.initial_capital = 'Le capital initial ne peut pas être négatif';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    onSubmit(formData);
  };

  const handleInputChange = (field: keyof CreatePortfolioRequest, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Créer un portefeuille</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors duration-200"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {/* Nom */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Nom du portefeuille *
            </label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.name ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="Mon portefeuille principal"
            />
            {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
          </div>

          {/* Description */}
          <div>
            <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              id="description"
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={3}
              placeholder="Description optionnelle du portefeuille"
            />
          </div>

          {/* Type de portefeuille */}
          <div>
            <label htmlFor="portfolio_type" className="block text-sm font-medium text-gray-700 mb-1">
              Type de portefeuille
            </label>
            <select
              id="portfolio_type"
              value={formData.portfolio_type}
              onChange={(e) => handleInputChange('portfolio_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="personal">Personnel</option>
              <option value="joint">Conjoint</option>
              <option value="corporate">Entreprise</option>
              <option value="retirement">Retraite</option>
            </select>
          </div>

          {/* Tolérance au risque */}
          <div>
            <label htmlFor="risk_tolerance" className="block text-sm font-medium text-gray-700 mb-1">
              Tolérance au risque
            </label>
            <select
              id="risk_tolerance"
              value={formData.risk_tolerance}
              onChange={(e) => handleInputChange('risk_tolerance', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="CONSERVATIVE">Conservateur</option>
              <option value="MODERATE">Modéré</option>
              <option value="AGGRESSIVE">Agressif</option>
            </select>
          </div>

          {/* Capital initial */}
          <div>
            <label htmlFor="initial_capital" className="block text-sm font-medium text-gray-700 mb-1">
              Capital initial
            </label>
            <input
              type="number"
              id="initial_capital"
              value={formData.initial_capital || ''}
              onChange={(e) => handleInputChange('initial_capital', e.target.value ? parseFloat(e.target.value) : 0)}
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                errors.initial_capital ? 'border-red-300' : 'border-gray-300'
              }`}
              placeholder="0.00"
              min="0"
              step="0.01"
            />
            {errors.initial_capital && <p className="mt-1 text-sm text-red-600">{errors.initial_capital}</p>}
          </div>

          {/* Devise */}
          <div>
            <label htmlFor="currency" className="block text-sm font-medium text-gray-700 mb-1">
              Devise
            </label>
            <select
              id="currency"
              value={formData.currency}
              onChange={(e) => handleInputChange('currency', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="EUR">EUR (Euro)</option>
              <option value="USD">USD (Dollar)</option>
              <option value="GBP">GBP (Livre Sterling)</option>
              <option value="CHF">CHF (Franc Suisse)</option>
            </select>
          </div>

          {/* Boutons */}
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors duration-200"
              disabled={isLoading}
            >
              Annuler
            </button>
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading}
            >
              {isLoading ? 'Création...' : 'Créer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
