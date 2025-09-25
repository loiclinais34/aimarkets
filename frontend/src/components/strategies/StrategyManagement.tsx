'use client';

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { 
  TradingStrategy, 
  StrategyDetail, 
  StrategyRule, 
  PredefinedStrategy,
  StrategyTypeOption,
  StrategyCreateForm 
} from '../../types/strategies';
import { strategiesApi } from '../../services/strategiesApi';

interface StrategyCardProps {
  strategy: TradingStrategy;
  onEdit: (strategy: TradingStrategy) => void;
  onDelete: (strategyId: number) => void;
  onViewDetails: (strategyId: number) => void;
}

export const StrategyCard: React.FC<StrategyCardProps> = ({
  strategy,
  onEdit,
  onDelete,
  onViewDetails
}) => {
  const [isDeleting, setIsDeleting] = useState(false);

  const deleteMutation = useMutation(
    () => strategiesApi.deleteStrategy(strategy.id),
    {
      onSuccess: () => {
        onDelete(strategy.id);
      },
      onError: (error: any) => {
        alert(`Erreur lors de la suppression: ${error.message}`);
      }
    }
  );

  const handleDelete = async () => {
    if (window.confirm(`Êtes-vous sûr de vouloir supprimer la stratégie "${strategy.name}" ?`)) {
      setIsDeleting(true);
      try {
        await deleteMutation.mutateAsync();
      } finally {
        setIsDeleting(false);
      }
    }
  };

  const getStrategyTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      momentum: 'bg-blue-100 text-blue-800',
      mean_reversion: 'bg-green-100 text-green-800',
      breakout: 'bg-purple-100 text-purple-800',
      scalping: 'bg-yellow-100 text-yellow-800',
      swing: 'bg-indigo-100 text-indigo-800',
      conservative: 'bg-gray-100 text-gray-800',
      aggressive: 'bg-red-100 text-red-800'
    };
    return colors[type] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{strategy.name}</h3>
          <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getStrategyTypeColor(strategy.strategy_type)}`}>
            {strategy.strategy_type}
          </span>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={() => onViewDetails(strategy.id)}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            Détails
          </button>
          <button
            onClick={() => onEdit(strategy)}
            className="text-green-600 hover:text-green-800 text-sm font-medium"
          >
            Modifier
          </button>
          <button
            onClick={handleDelete}
            disabled={isDeleting}
            className="text-red-600 hover:text-red-800 text-sm font-medium disabled:opacity-50"
          >
            {isDeleting ? 'Suppression...' : 'Supprimer'}
          </button>
        </div>
      </div>
      
      <p className="text-gray-600 text-sm mb-4">{strategy.description}</p>
      
      <div className="flex justify-between items-center text-xs text-gray-500">
        <span>Créé par: {strategy.created_by}</span>
        <span>{new Date(strategy.created_at).toLocaleDateString('fr-FR')}</span>
      </div>
      
      <div className="mt-3 flex items-center">
        <span className={`inline-block w-2 h-2 rounded-full mr-2 ${strategy.is_active ? 'bg-green-500' : 'bg-gray-400'}`}></span>
        <span className="text-xs text-gray-600">
          {strategy.is_active ? 'Actif' : 'Inactif'}
        </span>
      </div>
    </div>
  );
};

interface StrategyListProps {
  onEdit: (strategy: TradingStrategy) => void;
  onDelete: (strategyId: number) => void;
  onViewDetails: (strategyId: number) => void;
}

export const StrategyList: React.FC<StrategyListProps> = ({
  onEdit,
  onDelete,
  onViewDetails
}) => {
  const [filters, setFilters] = useState({
    strategy_type: '',
    is_active: undefined as boolean | undefined
  });

  const [strategies, setStrategies] = useState<TradingStrategy[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [predefinedTypes, setPredefinedTypes] = useState<any[]>([]);

  // Test avec fetch direct
  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        console.log('Fetching strategies with filters:', filters);
        
        // Récupérer les stratégies
        const params = new URLSearchParams();
        if (filters?.strategy_type) params.append('strategy_type', filters.strategy_type);
        if (filters?.is_active !== undefined) params.append('is_active', filters.is_active.toString());
        // if (filters?.created_by) params.append('created_by', filters.created_by);

        const response = await fetch(`http://localhost:8000/api/v1/strategies/?${params.toString()}`);
        console.log('Response status:', response.status);
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Raw response:', data);
        
        setStrategies(data.strategies || []);
        setTotal(data.total || 0);

        // Récupérer les types prédéfinis
        const typesResponse = await fetch(`http://localhost:8000/api/v1/strategies/predefined/types`);
        if (typesResponse.ok) {
          const typesData = await typesResponse.json();
          setPredefinedTypes(typesData.data || []);
        }
      } catch (err) {
        console.error('Error fetching strategies:', err);
        setError(err instanceof Error ? err.message : 'Erreur inconnue');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [filters]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Erreur lors du chargement des stratégies</p>
        <button 
          onClick={() => window.location.reload()}
          className="mt-2 text-red-600 hover:text-red-800 text-sm font-medium"
        >
          Réessayer
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Filtres */}
      <div className="mb-6 bg-gray-50 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-3">Filtres</h3>
        <div className="flex space-x-4">
          <div>
            <label className="block text-xs text-gray-600 mb-1">Type de stratégie</label>
            <select
              value={filters.strategy_type}
              onChange={(e) => setFilters(prev => ({ ...prev, strategy_type: e.target.value }))}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="">Tous les types</option>
              {predefinedTypes?.map((type) => (
                <option key={type.type} value={type.type}>
                  {type.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-600 mb-1">Statut</label>
            <select
              value={filters.is_active === undefined ? '' : filters.is_active.toString()}
              onChange={(e) => setFilters(prev => ({ 
                ...prev, 
                is_active: e.target.value === '' ? undefined : e.target.value === 'true'
              }))}
              className="text-sm border border-gray-300 rounded px-2 py-1"
            >
              <option value="">Tous</option>
              <option value="true">Actif</option>
              <option value="false">Inactif</option>
            </select>
          </div>
        </div>
      </div>

      {/* Liste des stratégies */}
      <div className="mb-4">
        <p className="text-sm text-gray-600">
          {total} stratégie{total > 1 ? 's' : ''} trouvée{total > 1 ? 's' : ''}
        </p>
      </div>

      {strategies.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">Aucune stratégie trouvée</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {strategies.map((strategy) => (
            <StrategyCard
              key={strategy.id}
              strategy={strategy}
              onEdit={onEdit}
              onDelete={onDelete}
              onViewDetails={onViewDetails}
            />
          ))}
        </div>
      )}
    </div>
  );
};

interface StrategyFormProps {
  strategy?: TradingStrategy;
  predefinedStrategy?: PredefinedStrategy;
  onSave: (strategy: StrategyCreateForm) => void;
  onCancel: () => void;
}

export const StrategyForm: React.FC<StrategyFormProps> = ({
  strategy,
  predefinedStrategy,
  onSave,
  onCancel
}) => {
  const [formData, setFormData] = useState<StrategyCreateForm>({
    name: '',
    description: '',
    strategy_type: '',
    parameters: {},
    rules: []
  });

  const [newRule, setNewRule] = useState({
    rule_type: 'entry',
    rule_name: '',
    rule_condition: '',
    rule_action: '',
    priority: 1
  });

  useEffect(() => {
    if (strategy) {
      setFormData({
        name: strategy.name,
        description: strategy.description,
        strategy_type: strategy.strategy_type,
        parameters: strategy.parameters,
        rules: [] // Les règles seront chargées séparément
      });
    } else if (predefinedStrategy) {
      setFormData({
        name: predefinedStrategy.name,
        description: predefinedStrategy.description,
        strategy_type: predefinedStrategy.strategy_type,
        parameters: predefinedStrategy.parameters,
        rules: predefinedStrategy.rules
      });
    }
  }, [strategy, predefinedStrategy]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(formData);
  };

  const addRule = () => {
    if (newRule.rule_name && newRule.rule_condition && newRule.rule_action) {
      setFormData(prev => ({
        ...prev,
        rules: [...prev.rules, { ...newRule }]
      }));
      setNewRule({
        rule_type: 'entry',
        rule_name: '',
        rule_condition: '',
        rule_action: '',
        priority: formData.rules.length + 1
      });
    }
  };

  const removeRule = (index: number) => {
    setFormData(prev => ({
      ...prev,
      rules: prev.rules.filter((_, i) => i !== index)
    }));
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Nom de la stratégie *
          </label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Type de stratégie *
          </label>
          <select
            value={formData.strategy_type}
            onChange={(e) => setFormData(prev => ({ ...prev, strategy_type: e.target.value }))}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="">Sélectionner un type</option>
            <option value="momentum">Momentum</option>
            <option value="mean_reversion">Mean Reversion</option>
            <option value="breakout">Breakout</option>
            <option value="scalping">Scalping</option>
            <option value="swing">Swing</option>
            <option value="conservative">Conservative</option>
            <option value="aggressive">Aggressive</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Description
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
          rows={3}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Règles */}
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Règles de Trading</h3>
        
        {/* Liste des règles existantes */}
        {formData.rules.map((rule, index) => (
          <div key={index} className="bg-gray-50 rounded-lg p-4 mb-3">
            <div className="flex justify-between items-start mb-2">
              <h4 className="font-medium text-gray-900">{rule.rule_name}</h4>
              <button
                type="button"
                onClick={() => removeRule(index)}
                className="text-red-600 hover:text-red-800 text-sm"
              >
                Supprimer
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <span className="text-gray-600">Type:</span> {rule.rule_type}
              </div>
              <div>
                <span className="text-gray-600">Priorité:</span> {rule.priority}
              </div>
            </div>
            <div className="mt-2 text-sm">
              <span className="text-gray-600">Condition:</span> {rule.rule_condition}
            </div>
            <div className="text-sm">
              <span className="text-gray-600">Action:</span> {rule.rule_action}
            </div>
          </div>
        ))}

        {/* Formulaire pour ajouter une nouvelle règle */}
        <div className="bg-blue-50 rounded-lg p-4">
          <h4 className="font-medium text-gray-900 mb-3">Ajouter une règle</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-600 mb-1">Nom de la règle</label>
              <input
                type="text"
                value={newRule.rule_name}
                onChange={(e) => setNewRule(prev => ({ ...prev, rule_name: e.target.value }))}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                placeholder="ex: Take Profit"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Type</label>
              <select
                value={newRule.rule_type}
                onChange={(e) => setNewRule(prev => ({ ...prev, rule_type: e.target.value as any }))}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
              >
                <option value="entry">Entrée</option>
                <option value="exit">Sortie</option>
                <option value="position_sizing">Taille de position</option>
                <option value="risk_management">Gestion des risques</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Condition</label>
              <input
                type="text"
                value={newRule.rule_condition}
                onChange={(e) => setNewRule(prev => ({ ...prev, rule_condition: e.target.value }))}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                placeholder="ex: current_return > 0.05"
              />
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Action</label>
              <input
                type="text"
                value={newRule.rule_action}
                onChange={(e) => setNewRule(prev => ({ ...prev, rule_action: e.target.value }))}
                className="w-full border border-gray-300 rounded px-2 py-1 text-sm"
                placeholder="ex: SELL"
              />
            </div>
          </div>
          <button
            type="button"
            onClick={addRule}
            className="mt-3 bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700"
          >
            Ajouter la règle
          </button>
        </div>
      </div>

      {/* Boutons */}
      <div className="flex justify-end space-x-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
        >
          Annuler
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          {strategy ? 'Mettre à jour' : 'Créer'} la stratégie
        </button>
      </div>
    </form>
  );
};
