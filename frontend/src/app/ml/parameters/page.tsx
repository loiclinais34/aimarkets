'use client';

import React, { useState, useEffect } from 'react';
import RootLayout from '@/components/RootLayout';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { targetParametersApi } from '@/services/targetParametersApi';

interface TargetParameter {
  id: number;
  symbol: string;
  parameter_name: string;
  parameter_value: number;
  created_at: string;
  updated_at: string;
}

export default function MLParameters() {
  const [isEditing, setIsEditing] = useState(false);
  const [editingParam, setEditingParam] = useState<TargetParameter | null>(null);
  const [formData, setFormData] = useState({
    symbol: '',
    parameter_name: '',
    parameter_value: 0,
  });

  const queryClient = useQueryClient();

  const { data: parameters, isLoading, error } = useQuery(
    'targetParameters',
    targetParametersApi.getTargetParameters
  );

  const createMutation = useMutation(targetParametersApi.createTargetParameter, {
    onSuccess: () => {
      queryClient.invalidateQueries('targetParameters');
      setIsEditing(false);
      setFormData({ symbol: '', parameter_name: '', parameter_value: 0 });
    },
  });

  const updateMutation = useMutation(
    ({ id, data }: { id: number; data: Partial<TargetParameter> }) =>
      targetParametersApi.updateTargetParameter(id, data),
    {
      onSuccess: () => {
        queryClient.invalidateQueries('targetParameters');
        setIsEditing(false);
        setEditingParam(null);
        setFormData({ symbol: '', parameter_name: '', parameter_value: 0 });
      },
    }
  );

  const deleteMutation = useMutation(targetParametersApi.deleteTargetParameter, {
    onSuccess: () => {
      queryClient.invalidateQueries('targetParameters');
    },
  });

  const handleEdit = (param: TargetParameter) => {
    setEditingParam(param);
    setFormData({
      symbol: param.symbol,
      parameter_name: param.parameter_name,
      parameter_value: param.parameter_value,
    });
    setIsEditing(true);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (editingParam) {
      updateMutation.mutate({
        id: editingParam.id,
        data: formData,
      });
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleDelete = (id: number) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce paramètre ?')) {
      deleteMutation.mutate(id);
    }
  };

  if (isLoading) return <RootLayout><div>Chargement...</div></RootLayout>;
  if (error) return <RootLayout><div>Erreur lors du chargement</div></RootLayout>;

  return (
    <RootLayout>
      <div className="px-4 py-6 sm:px-0">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Paramétrage ML</h1>
          <p className="mt-2 text-gray-600">
            Configurez les paramètres des modèles et les cibles de trading
          </p>
        </div>

        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg leading-6 font-medium text-gray-900">
                Paramètres de Cibles
              </h3>
              <button
                onClick={() => setIsEditing(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
              >
                Ajouter un paramètre
              </button>
            </div>

            {isEditing && (
              <form onSubmit={handleSubmit} className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Symbole
                    </label>
                    <input
                      type="text"
                      value={formData.symbol}
                      onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="AAPL"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Nom du paramètre
                    </label>
                    <input
                      type="text"
                      value={formData.parameter_name}
                      onChange={(e) => setFormData({ ...formData, parameter_name: e.target.value })}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="target_return"
                      required
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">
                      Valeur
                    </label>
                    <input
                      type="number"
                      step="0.01"
                      value={formData.parameter_value}
                      onChange={(e) => setFormData({ ...formData, parameter_value: parseFloat(e.target.value) })}
                      className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                      placeholder="0.05"
                      required
                    />
                  </div>
                </div>
                <div className="mt-4 flex justify-end space-x-3">
                  <button
                    type="button"
                    onClick={() => {
                      setIsEditing(false);
                      setEditingParam(null);
                      setFormData({ symbol: '', parameter_name: '', parameter_value: 0 });
                    }}
                    className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-md text-sm font-medium"
                  >
                    Annuler
                  </button>
                  <button
                    type="submit"
                    className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium"
                  >
                    {editingParam ? 'Mettre à jour' : 'Créer'}
                  </button>
                </div>
              </form>
            )}

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Symbole
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Paramètre
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Valeur
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Dernière mise à jour
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {parameters?.map((param) => (
                    <tr key={param.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {param.symbol}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {param.parameter_name}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {param.parameter_value}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {new Date(param.updated_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button
                          onClick={() => handleEdit(param)}
                          className="text-blue-600 hover:text-blue-900 mr-3"
                        >
                          Modifier
                        </button>
                        <button
                          onClick={() => handleDelete(param.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Supprimer
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </RootLayout>
  );
}
