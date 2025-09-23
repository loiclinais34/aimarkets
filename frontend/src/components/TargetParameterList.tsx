import { useState } from 'react'
import { useMutation, useQueryClient } from 'react-query'
import { apiService, TargetParameter } from '@/services/api'
import { toast } from 'react-hot-toast'
import { 
  PencilIcon, 
  TrashIcon, 
  EyeIcon,
  CheckCircleIcon,
  XCircleIcon,
  ChartBarSquareIcon
} from '@heroicons/react/24/outline'

interface TargetParameterListProps {
  parameters: TargetParameter[]
  loading?: boolean
  onUpdate?: () => void
}

export default function TargetParameterList({ parameters, loading, onUpdate }: TargetParameterListProps) {
  const [selectedParameter, setSelectedParameter] = useState<TargetParameter | null>(null)
  const queryClient = useQueryClient()

  const deleteMutation = useMutation(
    (id: number) => apiService.deleteTargetParameter(id),
    {
      onSuccess: () => {
        toast.success('Paramètre supprimé avec succès!')
        onUpdate?.()
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Erreur lors de la suppression')
      },
    }
  )

  const handleDelete = (id: number, name: string) => {
    if (window.confirm(`Êtes-vous sûr de vouloir supprimer le paramètre "${name}" ?`)) {
      deleteMutation.mutate(id)
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="h-20 bg-gray-200 rounded-lg"></div>
          </div>
        ))}
      </div>
    )
  }

  if (parameters.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <ChartBarSquareIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
        <p>Aucun paramètre de cible configuré</p>
        <p className="text-sm">Créez votre premier paramètre pour commencer</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {parameters.map((parameter) => (
        <div
          key={parameter.id}
          className={`border rounded-lg p-4 ${
            parameter.is_active ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <h4 className="text-lg font-medium text-gray-900">
                  {parameter.parameter_name}
                </h4>
                {parameter.is_active ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircleIcon className="h-5 w-5 text-gray-400" />
                )}
              </div>
              
              <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Rendement cible:</span>
                  <p className="font-medium text-green-600">
                    {parameter.target_return_percentage}%
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Horizon:</span>
                  <p className="font-medium">
                    {parameter.time_horizon_days} jours
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Risque:</span>
                  <p className="font-medium capitalize">
                    {parameter.risk_tolerance}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Confiance min:</span>
                  <p className="font-medium">
                    {(parameter.min_confidence_threshold * 100).toFixed(0)}%
                  </p>
                </div>
              </div>

              <div className="mt-2 text-xs text-gray-500">
                Créé le {new Date(parameter.created_at).toLocaleDateString('fr-FR')}
                {parameter.updated_at !== parameter.created_at && (
                  <span> • Modifié le {new Date(parameter.updated_at).toLocaleDateString('fr-FR')}</span>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-2 ml-4">
              <button
                onClick={() => setSelectedParameter(parameter)}
                className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                title="Voir les détails"
              >
                <EyeIcon className="h-4 w-4" />
              </button>
              <button
                onClick={() => handleDelete(parameter.id, parameter.parameter_name)}
                className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                title="Supprimer"
                disabled={deleteMutation.isLoading}
              >
                <TrashIcon className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      ))}

      {/* Modal de détails */}
      {selectedParameter && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Détails du paramètre
                </h3>
                <button
                  onClick={() => setSelectedParameter(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircleIcon className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700">Nom</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedParameter.parameter_name}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Rendement cible</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedParameter.target_return_percentage}%</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Horizon temporel</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedParameter.time_horizon_days} jours</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Tolérance au risque</label>
                    <p className="mt-1 text-sm text-gray-900 capitalize">{selectedParameter.risk_tolerance}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Seuil de confiance</label>
                    <p className="mt-1 text-sm text-gray-900">{(selectedParameter.min_confidence_threshold * 100).toFixed(1)}%</p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Drawdown maximum</label>
                  <p className="mt-1 text-sm text-gray-900">{selectedParameter.max_drawdown_percentage}%</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Statut</label>
                  <p className="mt-1 text-sm">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      selectedParameter.is_active 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {selectedParameter.is_active ? 'Actif' : 'Inactif'}
                    </span>
                  </p>
                </div>

                <div className="pt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-500">
                    Créé le {new Date(selectedParameter.created_at).toLocaleString('fr-FR')}
                  </p>
                  {selectedParameter.updated_at !== selectedParameter.created_at && (
                    <p className="text-xs text-gray-500">
                      Modifié le {new Date(selectedParameter.updated_at).toLocaleString('fr-FR')}
                    </p>
                  )}
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setSelectedParameter(null)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Fermer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
