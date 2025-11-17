import React from 'react';
import { AlertCircle } from 'lucide-react';

interface ErrorDisplayProps {
  error: Error;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = ({ error }) => {
  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-900">
      <div className="text-center max-w-md">
        <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-slate-100 mb-2">
          Error Loading Data
        </h2>
        <p className="text-slate-400 mb-4">
          There was a problem loading the sentiment analysis data.
        </p>
        <div className="bg-slate-800 rounded-lg p-4 text-left">
          <p className="text-sm text-red-400 font-mono">{error.message}</p>
        </div>
        <button
          onClick={() => window.location.reload()}
          className="mt-6 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          Reload Page
        </button>
      </div>
    </div>
  );
};
