import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

interface ErrorMessageProps {
  title?: string
  message: string
  onRetry?: () => void
}

export default function ErrorMessage({ title = 'Erreur', message, onRetry }: ErrorMessageProps) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <div className="flex">
        <div className="flex-shrink-0">
          <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-red-800">{title}</h3>
          <div className="mt-2 text-sm text-red-700">
            <p>{message}</p>
          </div>
          {onRetry && (
            <div className="mt-4">
              <button
                onClick={onRetry}
                className="bg-red-100 text-red-800 px-3 py-2 rounded-md text-sm font-medium hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-red-500"
              >
                Réessayer
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
