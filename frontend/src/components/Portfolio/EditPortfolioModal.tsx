'use client';

import React, { useState, useEffect } from 'react';
import { Portfolio, UpdatePortfolioRequest } from '@/services/portfolioApi';

interface EditPortfolioModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (data: UpdatePortfolioRequest) => void;
  portfolio: Portfolio | null;
  isLoading?: boolean;
}

export const EditPortfolioModal: React.FC<EditPortfolioModalProps> = ({
  isOpen,
  onClose,
  onSave,
  portfolio,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<UpdatePortfolioRequest>({
    name: '',
    description: '',
    risk_tolerance: 'MODERATE',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Mettre à jour le formulaire quand le portefeuille change
  useEffect(() => {
    if (portfolio) {
      setFormData({
        name: portfolio.name || '',
        description: portfolio.description || '',
        risk_tolerance: portfolio.risk_tolerance || 'MODERATE',
      });
    }
  }, [portfolio]);

  const handleInputChange = (field: keyof UpdatePortfolioRequest, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
    
    // Effacer l'erreur pour ce champ
    if (errors[field]) {
      setErrors(prev => ({
        ...prev,
        [field]: '',
      }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    const newErrors: Record<string, string> = {};
    if (!formData.name?.trim()) {
      newErrors.name = 'Le nom est requis';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    onSave(formData);
  };

  const handleClose = () => {
    setErrors({});
    onClose();
  };

  if (!isOpen || !portfolio) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900">
            Modifier le portefeuille
          </h2>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Nom */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-1">
              Nom du portefeuille
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

          {/* Boutons */}
          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 px-4 py-2 border border-gray-300 rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={isLoading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Sauvegarde...' : 'Sauvegarder'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
