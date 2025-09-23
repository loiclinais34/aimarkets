import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useMutation, useQueryClient } from 'react-query'
import { apiService, TargetParameterCreate } from '@/services/api'
import { toast } from 'react-hot-toast'
import { CheckIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface TargetParameterFormProps {
  userId: string
  onSuccess?: () => void
}

interface FormData {
  parameter_name: string
  target_return_percentage: number
  time_horizon_days: number
  risk_tolerance: 'low' | 'medium' | 'high'
  min_confidence_threshold: number
  max_drawdown_percentage: number
}

export default function TargetParameterForm({ userId, onSuccess }: TargetParameterFormProps) {
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
      parameter_name: '',
      target_return_percentage: 1.5,
      time_horizon_days: 7,
      risk_tolerance: 'medium',
      min_confidence_threshold: 0.7,
      max_drawdown_percentage: 5.0,
    },
  })

  const watchedValues = watch()

  const createMutation = useMutation(
    (data: TargetParameterCreate) => apiService.createTargetParameter(data),
    {
      onSuccess: () => {
        toast.success('Paramètre de cible créé avec succès!')
        queryClient.invalidateQueries(['targetParameters', userId])
        reset()
        onSuccess?.()
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Erreur lors de la création du paramètre')
      },
    }
  )

  const onSubmit = async (data: FormData) => {
    setIsSubmitting(true)
    try {
      await createMutation.mutateAsync({
        user_id: userId,
        ...data,
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  // Calculer le prix cible pour un exemple
  const calculateExampleTargetPrice = () => {
    const currentPrice = 100
    const targetReturn = watchedValues.target_return_percentage / 100
    const timeHorizon = watchedValues.time_horizon_days
    const dailyReturn = Math.pow(1 + targetReturn, 1 / timeHorizon) - 1
    const targetPrice = currentPrice * (1 + dailyReturn * timeHorizon)
    return targetPrice
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <label htmlFor="parameter_name" className="block text-sm font-medium text-gray-700">
          Nom du paramètre
        </label>
        <input
          type="text"
          id="parameter_name"
          {...register('parameter_name', { required: 'Le nom est requis' })}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          placeholder="Ex: Objectif 1.5% sur 7 jours"
        />
        {errors.parameter_name && (
          <p className="mt-1 text-sm text-red-600">{errors.parameter_name.message}</p>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="target_return_percentage" className="block text-sm font-medium text-gray-700">
            Rendement cible (%)
          </label>
          <input
            type="number"
            id="target_return_percentage"
            step="0.1"
            min="0"
            max="100"
            {...register('target_return_percentage', {
              required: 'Le rendement cible est requis',
              min: { value: 0, message: 'Le rendement doit être positif' },
              max: { value: 100, message: 'Le rendement ne peut pas dépasser 100%' },
            })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
          {errors.target_return_percentage && (
            <p className="mt-1 text-sm text-red-600">{errors.target_return_percentage.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="time_horizon_days" className="block text-sm font-medium text-gray-700">
            Horizon temporel (jours)
          </label>
          <input
            type="number"
            id="time_horizon_days"
            min="1"
            max="365"
            {...register('time_horizon_days', {
              required: 'L\'horizon temporel est requis',
              min: { value: 1, message: 'L\'horizon doit être d\'au moins 1 jour' },
              max: { value: 365, message: 'L\'horizon ne peut pas dépasser 365 jours' },
            })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
          {errors.time_horizon_days && (
            <p className="mt-1 text-sm text-red-600">{errors.time_horizon_days.message}</p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="risk_tolerance" className="block text-sm font-medium text-gray-700">
          Tolérance au risque
        </label>
        <select
          id="risk_tolerance"
          {...register('risk_tolerance')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
        >
          <option value="low">Faible</option>
          <option value="medium">Moyenne</option>
          <option value="high">Élevée</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label htmlFor="min_confidence_threshold" className="block text-sm font-medium text-gray-700">
            Seuil de confiance minimum
          </label>
          <input
            type="number"
            id="min_confidence_threshold"
            step="0.1"
            min="0"
            max="1"
            {...register('min_confidence_threshold', {
              required: 'Le seuil de confiance est requis',
              min: { value: 0, message: 'Le seuil doit être entre 0 et 1' },
              max: { value: 1, message: 'Le seuil doit être entre 0 et 1' },
            })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
          {errors.min_confidence_threshold && (
            <p className="mt-1 text-sm text-red-600">{errors.min_confidence_threshold.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="max_drawdown_percentage" className="block text-sm font-medium text-gray-700">
            Drawdown maximum (%)
          </label>
          <input
            type="number"
            id="max_drawdown_percentage"
            step="0.1"
            min="0"
            max="50"
            {...register('max_drawdown_percentage', {
              required: 'Le drawdown maximum est requis',
              min: { value: 0, message: 'Le drawdown doit être positif' },
              max: { value: 50, message: 'Le drawdown ne peut pas dépasser 50%' },
            })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
          {errors.max_drawdown_percentage && (
            <p className="mt-1 text-sm text-red-600">{errors.max_drawdown_percentage.message}</p>
          )}
        </div>
      </div>

      {/* Aperçu du calcul */}
      <div className="bg-blue-50 p-4 rounded-lg">
        <h4 className="text-sm font-medium text-blue-900 mb-2">Aperçu du calcul</h4>
        <p className="text-sm text-blue-700">
          Pour un prix actuel de $100, le prix cible serait de{' '}
          <span className="font-semibold">${calculateExampleTargetPrice().toFixed(2)}</span>
          {' '}sur {watchedValues.time_horizon_days} jours
        </p>
      </div>

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
          disabled={isSubmitting}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
        >
          {isSubmitting ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent mr-2" />
              Création...
            </>
          ) : (
            <>
              <CheckIcon className="h-4 w-4 mr-2" />
              Créer le paramètre
            </>
          )}
        </button>
      </div>
    </form>
  )
}
