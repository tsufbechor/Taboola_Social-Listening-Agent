import React from 'react';
import { Loader2 } from 'lucide-react';

export const Loading: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-900">
      <div className="text-center">
        <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
        <p className="text-slate-300 text-lg">Loading sentiment data...</p>
        <p className="text-slate-500 text-sm mt-2">
          Analyzing Taboola discussions and feedback
        </p>
      </div>
    </div>
  );
};
