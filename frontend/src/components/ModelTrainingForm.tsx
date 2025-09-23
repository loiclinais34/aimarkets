import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from 'react-query'
import { apiService, ModelTrainingRequest, SymbolWithMetadata } from '@/services/api'
import { toast } from 'react-hot-toast'
import { CheckIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface ModelTrainingFormProps {
  symbols: SymbolWithMetadata[]
  targetParameters: any[]
  onSuccess?: () => void
}

interface FormData {
  symbol: string
  target_parameter_id: number
  model_type: 'classification' | 'regression'
  test_size: number
  random_state: number
}

export default function ModelTrainingForm({ symbols, targetParameters, onSuccess }: ModelTrainingFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)
  const queryClient = useQueryClient()

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<FormData>({
    defaultValues: {
      symbol: symbols[0]?.symbol || '',
      target_parameter_id: targetParameters[0]?.id || 0,
      model_type: 'classification',
      test_size: 0.2,
      random_state: 42,
    },
  })

  const createMutation = useMutation(
    (data: ModelTrainingRequest) => apiService.trainModel(data),
    {
      onSuccess: (response) => {
        toast.success(`Modèle ${response.model_type} entraîné avec succès!`)
        queryClient.invalidateQueries('mlModels')
        reset()
        onSuccess?.()
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Erreur lors de l\'entraînement du modèle')
      },
    }
  )

  const onSubmit = async (data: FormData) => {
    setIsSubmitting(true)
    try {
      await createMutation.mutateAsync(data)
    } finally {
      setIsSubmitting(false)
    }
  }

  const selectedTargetParam = targetParameters.find(p => p.id === watch('target_parameter_id'))

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <label htmlFor="symbol" className="block text-sm font-medium text-gray-700">
          Symbole
        </label>
        <select
          id="symbol"
          {...register('symbol', { required: 'Le symbole est requis' })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        >
          {symbols.map((symbolData) => (
            <option key={symbolData.symbol} value={symbolData.symbol}>
              {symbolData.symbol} - {symbolData.company_name}
            </option>
          ))}
        </select>
        {errors.symbol && (
          <p className="mt-1 text-sm text-red-600">{errors.symbol.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="target_parameter_id" className="block text-sm font-medium text-gray-700">
          Paramètre de cible
        </label>
        <select
          id="target_parameter_id"
          {...register('target_parameter_id', { required: 'Le paramètre de cible est requis' })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        >
          {targetParameters.map((param) => (
            <option key={param.id} value={param.id}>
              {param.parameter_name} ({param.target_return_percentage}% sur {param.time_horizon_days} jours)
            </option>
          ))}
        </select>
        {errors.target_parameter_id && (
          <p className="mt-1 text-sm text-red-600">{errors.target_parameter_id.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="model_type" className="block text-sm font-medium text-gray-700">
          Type de modèle
        </label>
        <select
          id="model_type"
          {...register('model_type')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        >
          <option value="classification">Classification (Atteinte de cible)</option>
          <option value="regression">Régression (Rendement exact)</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="test_size" className="block text-sm font-medium text-gray-700">
            Proportion des données de test
          </label>
          <input
            type="number"
            id="test_size"
            step="0.1"
            min="0.1"
            max="0.5"
            {...register('test_size', {
              required: 'La proportion de test est requise',
              min: { value: 0.1, message: 'Minimum 0.1' },
              max: { value: 0.5, message: 'Maximum 0.5' },
            })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
          {errors.test_size && (
            <p className="mt-1 text-sm text-red-600">{errors.test_size.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="random_state" className="block text-sm font-medium text-gray-700">
            Seed aléatoire
          </label>
          <input
            type="number"
            id="random_state"
            min="0"
            {...register('random_state', {
              required: 'Le seed aléatoire est requis',
              min: { value: 0, message: 'Le seed doit être positif' },
            })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
          {errors.random_state && (
            <p className="mt-1 text-sm text-red-600">{errors.random_state.message}</p>
          )}
        </div>
      </div>

      {/* Aperçu de la configuration */}
      {selectedTargetParam && (
        <div className="bg-blue-50 p-4 rounded-lg">
          <h4 className="text-sm font-medium text-blue-900 mb-2">Configuration du modèle</h4>
          <div className="text-sm text-blue-700 space-y-1">
            <p><strong>Symbole:</strong> {watch('symbol')}</p>
            <p><strong>Paramètre:</strong> {selectedTargetParam.parameter_name}</p>
            <p><strong>Type:</strong> {watch('model_type') === 'classification' ? 'Classification' : 'Régression'}</p>
            <p><strong>Données de test:</strong> {(watch('test_size') * 100).toFixed(0)}%</p>
          </div>
        </div>
      )}

      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={() => reset()}
          className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <XMarkIcon className="h-4 w-4 mr-2" />
          Annuler
        </button>
        <button
          type="submit"
          disabled={isSubmitting || targetParameters.length === 0}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {isSubmitting ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
              Entraînement...
            </>
          ) : (
            <>
              <CheckIcon className="h-4 w-4 mr-2" />
              Entraîner le modèle
            </>
          )}
        </button>
      </div>

      {targetParameters.length === 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-700">
            Aucun paramètre de cible disponible. Créez d'abord un paramètre de cible pour pouvoir entraîner un modèle.
          </p>
        </div>
      )}
    </form>
  )
}
