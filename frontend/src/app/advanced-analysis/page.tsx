// frontend/src/app/advanced-analysis/page.tsx
'use client';

import React from 'react';
import AdvancedAnalysisDashboard from '@/components/AdvancedAnalysis/AdvancedAnalysisDashboard';

const AdvancedAnalysisPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <AdvancedAnalysisDashboard />
    </div>
  );
};

export default AdvancedAnalysisPage;
