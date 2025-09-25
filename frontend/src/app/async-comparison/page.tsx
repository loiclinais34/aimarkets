import AsyncModelComparison from '@/components/AsyncModelComparison';

export default function AsyncComparisonPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <div className="flex items-center">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="h-8 w-8 text-blue-600 mr-3">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Comparaison Asynchrone de Modèles</h1>
                <p className="text-gray-600 mt-1">Entraînement asynchrone avec suivi en temps réel</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AsyncModelComparison />
      </div>
    </div>
  );
}
