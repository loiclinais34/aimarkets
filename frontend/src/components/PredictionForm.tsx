import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation } from 'react-query'
import { apiService, PredictionRequest, PredictionResponse, SymbolWithMetadata } from '@/services/api'
import { toast } from 'react-hot-toast'
import { CheckIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface PredictionFormProps {
  symbols: SymbolWithMetadata[]
  models: any[]
}

interface FormData {
  symbol: string
  model_id: number
  prediction_date: string
}

export default function PredictionForm({ symbols, models }: PredictionFormProps) {
  const [prediction, setPrediction] = useState<PredictionResponse | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<FormData>({
    defaultValues: {
      symbol: symbols[0]?.symbol || '',
      model_id: models[0]?.id || 0,
      prediction_date: new Date().toISOString().split('T')[0],
    },
  })

  const predictionMutation = useMutation(
    (data: PredictionRequest) => apiService.makePrediction(data),
    {
      onSuccess: (response) => {
        setPrediction(response)
        toast.success('Prédiction générée avec succès!')
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Erreur lors de la génération de la prédiction')
      },
    }
  )

  const onSubmit = async (data: FormData) => {
    setIsSubmitting(true)
    try {
      await predictionMutation.mutateAsync({
        symbol: data.symbol,
        model_id: data.model_id,
        prediction_date: data.prediction_date,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  const selectedModel = models.find(m => m.id === watch('model_id'))

  return (
    <div className="space-y-6">
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
          <label htmlFor="model_id" className="block text-sm font-medium text-gray-700">
            Modèle ML
          </label>
          <select
            id="model_id"
            {...register('model_id', { required: 'Le modèle est requis' })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          >
            {models.map((model) => (
              <option key={model.id} value={model.id}>
                {model.model_name} ({model.model_type})
              </option>
            ))}
          </select>
          {errors.model_id && (
            <p className="mt-1 text-sm text-red-600">{errors.model_id.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="prediction_date" className="block text-sm font-medium text-gray-700">
            Date de prédiction
          </label>
          <input
            type="date"
            id="prediction_date"
            {...register('prediction_date', { required: 'La date de prédiction est requise' })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
          {errors.prediction_date && (
            <p className="mt-1 text-sm text-red-600">{errors.prediction_date.message}</p>
          )}
        </div>

        {/* Aperçu de la configuration */}
        {selectedModel && (
          <div className="bg-blue-50 p-4 rounded-lg">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Configuration de la prédiction</h4>
            <div className="text-sm text-blue-700 space-y-1">
              <p><strong>Symbole:</strong> {watch('symbol')}</p>
              <p><strong>Modèle:</strong> {selectedModel.model_name}</p>
              <p><strong>Type:</strong> {selectedModel.model_type}</p>
              <p><strong>Date:</strong> {new Date(watch('prediction_date')).toLocaleDateString('fr-FR')}</p>
            </div>
          </div>
        )}

        <div className="flex justify-end space-x-3">
          <button
            type="button"
            onClick={() => {
              reset()
              setPrediction(null)
            }}
            className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <XMarkIcon className="h-4 w-4 mr-2" />
            Réinitialiser
          </button>
          <button
            type="submit"
            disabled={isSubmitting || models.length === 0}
            className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
                Génération...
              </>
            ) : (
              <>
                <CheckIcon className="h-4 w-4 mr-2" />
                Générer la prédiction
              </>
            )}
          </button>
        </div>

        {models.length === 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-700">
              Aucun modèle ML disponible. Entraînez d'abord un modèle pour pouvoir faire des prédictions.
            </p>
          </div>
        )}
      </form>

      {/* Résultat de la prédiction */}
      {prediction && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-green-900 mb-4">Résultat de la prédiction</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="text-sm font-medium text-green-800 mb-2">Informations générales</h4>
              <div className="space-y-2 text-sm text-green-700">
                <p><strong>Symbole:</strong> {prediction.symbol}</p>
                <p><strong>Modèle:</strong> {prediction.model_name}</p>
                <p><strong>Type de prédiction:</strong> {prediction.prediction_type}</p>
                <p><strong>Date:</strong> {new Date(prediction.prediction_date).toLocaleDateString('fr-FR')}</p>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-medium text-green-800 mb-2">Résultats</h4>
              <div className="space-y-2 text-sm text-green-700">
                <p><strong>Prédiction:</strong> {prediction.prediction.toFixed(4)}</p>
                <p><strong>Confiance:</strong> {(prediction.confidence * 100).toFixed(1)}%</p>
              </div>
            </div>
          </div>

          {prediction.features_used && prediction.features_used.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-green-800 mb-2">Features utilisées</h4>
              <div className="flex flex-wrap gap-2">
                {prediction.features_used.map((feature, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                  >
                    {feature}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Interprétation de la prédiction */}
          <div className="mt-4 p-4 bg-white rounded-lg border border-green-200">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Interprétation</h4>
            <div className="text-sm text-gray-700">
              {prediction.prediction_type === 'classification' ? (
                <p>
                  Le modèle prédit que l'objectif de rendement sera{' '}
                  <span className="font-semibold text-green-600">
                    {prediction.prediction > 0.5 ? 'atteint' : 'non atteint'}
                  </span>{' '}
                  avec une confiance de {(prediction.confidence * 100).toFixed(1)}%.
                </p>
              ) : (
                <p>
                  Le modèle prédit un rendement de{' '}
                  <span className="font-semibold text-blue-600">
                    {(prediction.prediction * 100).toFixed(2)}%
                  </span>{' '}
                  avec une confiance de {(prediction.confidence * 100).toFixed(1)}%.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
