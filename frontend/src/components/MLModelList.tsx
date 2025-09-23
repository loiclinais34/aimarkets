import { useState } from 'react'
import { useMutation, useQueryClient } from 'react-query'
import { apiService, MLModel } from '@/services/api'
import { toast } from 'react-hot-toast'
import ShapExplanations from './ShapExplanations'
import { 
  EyeIcon,
  PlayIcon,
  StopIcon,
  TrashIcon,
  CheckCircleIcon,
  XCircleIcon,
  CpuChipIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline'

interface MLModelListProps {
  models: MLModel[]
  loading?: boolean
  onUpdate?: () => void
}

export default function MLModelList({ models, loading, onUpdate }: MLModelListProps) {
  const [selectedModel, setSelectedModel] = useState<MLModel | null>(null)
  const [showShapExplanations, setShowShapExplanations] = useState(false)
  const [shapParams, setShapParams] = useState<{
    modelId: number
    symbol: string
    predictionDate: string
  } | null>(null)
  const queryClient = useQueryClient()

  const activateMutation = useMutation(
    (id: number) => apiService.activateModel(id),
    {
      onSuccess: () => {
        toast.success('Modèle activé avec succès!')
        onUpdate?.()
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Erreur lors de l\'activation')
      },
    }
  )

  const deactivateMutation = useMutation(
    (id: number) => apiService.deactivateModel(id),
    {
      onSuccess: () => {
        toast.success('Modèle désactivé avec succès!')
        onUpdate?.()
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Erreur lors de la désactivation')
      },
    }
  )

  const deleteMutation = useMutation(
    (id: number) => apiService.deleteModel(id),
    {
      onSuccess: () => {
        toast.success('Modèle supprimé avec succès!')
        onUpdate?.()
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Erreur lors de la suppression')
      },
    }
  )

  const handleActivate = (id: number) => {
    activateMutation.mutate(id)
  }

  const handleDeactivate = (id: number) => {
    deactivateMutation.mutate(id)
  }

  const handleDelete = (id: number, name: string) => {
    if (window.confirm(`Êtes-vous sûr de vouloir supprimer le modèle "${name}" ?`)) {
      deleteMutation.mutate(id)
    }
  }

  const handleShowShapExplanations = (model: MLModel) => {
    // Utiliser la date d'aujourd'hui par défaut
    const today = new Date().toISOString().split('T')[0]
    setShapParams({
      modelId: model.id,
      symbol: model.symbol || 'AAPL', // Valeur par défaut
      predictionDate: today
    })
    setShowShapExplanations(true)
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="animate-pulse">
            <div className="h-24 bg-gray-200 rounded-lg"></div>
          </div>
        ))}
      </div>
    )
  }

  if (models.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <CpuChipIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
        <p>Aucun modèle ML entraîné</p>
        <p className="text-sm">Entraînez votre premier modèle pour commencer</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {models.map((model) => (
        <div
          key={model.id}
          className={`border rounded-lg p-4 ${
            model.is_active ? 'border-green-200 bg-green-50' : 'border-gray-200 bg-gray-50'
          }`}
        >
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <h4 className="text-lg font-medium text-gray-900">
                  {model.model_name}
                </h4>
                {model.is_active ? (
                  <CheckCircleIcon className="h-5 w-5 text-green-500" />
                ) : (
                  <XCircleIcon className="h-5 w-5 text-gray-400" />
                )}
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  model.model_type === 'classification' 
                    ? 'bg-blue-100 text-blue-800' 
                    : 'bg-purple-100 text-purple-800'
                }`}>
                  {model.model_type}
                </span>
              </div>
              
              <div className="mt-2 grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                <div>
                  <span className="text-gray-500">Symbole:</span>
                  <p className="font-medium">{model.symbol}</p>
                </div>
                <div>
                  <span className="text-gray-500">Version:</span>
                  <p className="font-medium">{model.model_version}</p>
                </div>
                <div>
                  <span className="text-gray-500">Score de validation:</span>
                  <p className="font-medium">
                    {model.validation_score ? (model.validation_score * 100).toFixed(1) + '%' : 'N/A'}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Score de test:</span>
                  <p className="font-medium">
                    {model.test_score ? (model.test_score * 100).toFixed(1) + '%' : 'N/A'}
                  </p>
                </div>
                <div>
                  <span className="text-gray-500">Période d'entraînement:</span>
                  <p className="font-medium">
                    {model.training_data_start && model.training_data_end 
                      ? `${new Date(model.training_data_start).toLocaleDateString('fr-FR')} - ${new Date(model.training_data_end).toLocaleDateString('fr-FR')}`
                      : 'N/A'
                    }
                  </p>
                </div>
              </div>

              <div className="mt-2 text-xs text-gray-500">
                Créé le {new Date(model.created_at).toLocaleDateString('fr-FR')}
                {model.updated_at !== model.created_at && (
                  <span> • Modifié le {new Date(model.updated_at).toLocaleDateString('fr-FR')}</span>
                )}
              </div>
            </div>

            <div className="flex items-center space-x-2 ml-4">
              <button
                onClick={() => handleShowShapExplanations(model)}
                className="p-2 text-gray-400 hover:text-purple-600 transition-colors"
                title="Voir les explications SHAP"
              >
                <ChartBarIcon className="h-4 w-4" />
              </button>
              
              <button
                onClick={() => setSelectedModel(model)}
                className="p-2 text-gray-400 hover:text-blue-600 transition-colors"
                title="Voir les détails"
              >
                <EyeIcon className="h-4 w-4" />
              </button>
              
              {model.is_active ? (
                <button
                  onClick={() => handleDeactivate(model.id)}
                  className="p-2 text-gray-400 hover:text-orange-600 transition-colors"
                  title="Désactiver"
                  disabled={deactivateMutation.isLoading}
                >
                  <StopIcon className="h-4 w-4" />
                </button>
              ) : (
                <button
                  onClick={() => handleActivate(model.id)}
                  className="p-2 text-gray-400 hover:text-green-600 transition-colors"
                  title="Activer"
                  disabled={activateMutation.isLoading}
                >
                  <PlayIcon className="h-4 w-4" />
                </button>
              )}
              
              <button
                onClick={() => handleDelete(model.id, model.model_name)}
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
      {selectedModel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-gray-900">
                  Détails du modèle
                </h3>
                <button
                  onClick={() => setSelectedModel(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <XCircleIcon className="h-6 w-6" />
                </button>
              </div>

              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Nom du modèle</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedModel.model_name}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Type</label>
                    <p className="mt-1 text-sm text-gray-900 capitalize">{selectedModel.model_type}</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Version</label>
                    <p className="mt-1 text-sm text-gray-900">{selectedModel.model_version}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Statut</label>
                    <p className="mt-1 text-sm">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        selectedModel.is_active 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {selectedModel.is_active ? 'Actif' : 'Inactif'}
                      </span>
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Score de validation</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {selectedModel.validation_score ? (selectedModel.validation_score * 100).toFixed(2) + '%' : 'N/A'}
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700">Score de test</label>
                    <p className="mt-1 text-sm text-gray-900">
                      {selectedModel.test_score ? (selectedModel.test_score * 100).toFixed(2) + '%' : 'N/A'}
                    </p>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Période d'entraînement</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {selectedModel.training_data_start && selectedModel.training_data_end 
                      ? `${new Date(selectedModel.training_data_start).toLocaleDateString('fr-FR')} - ${new Date(selectedModel.training_data_end).toLocaleDateString('fr-FR')}`
                      : 'Non spécifiée'
                    }
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">Paramètres du modèle</label>
                  <div className="mt-1 bg-gray-50 p-3 rounded-md">
                    <pre className="text-xs text-gray-700 overflow-x-auto">
                      {JSON.stringify(selectedModel.model_parameters, null, 2)}
                    </pre>
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-200">
                  <p className="text-xs text-gray-500">
                    Créé le {new Date(selectedModel.created_at).toLocaleString('fr-FR')}
                  </p>
                  {selectedModel.updated_at !== selectedModel.created_at && (
                    <p className="text-xs text-gray-500">
                      Modifié le {new Date(selectedModel.updated_at).toLocaleString('fr-FR')}
                    </p>
                  )}
                </div>
              </div>

              <div className="mt-6 flex justify-end">
                <button
                  onClick={() => setSelectedModel(null)}
                  className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Fermer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal SHAP Explanations */}
      {showShapExplanations && shapParams && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-6xl w-full max-h-[90vh] overflow-y-auto">
            <ShapExplanations
              modelId={shapParams.modelId}
              symbol={shapParams.symbol}
              predictionDate={shapParams.predictionDate}
              onClose={() => setShowShapExplanations(false)}
            />
          </div>
        </div>
      )}
    </div>
  )
}
