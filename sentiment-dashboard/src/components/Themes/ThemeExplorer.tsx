import React, { useState } from 'react';
import { useData } from '../../context/DataContext';
import { ThemeCard } from './ThemeCard';
import { QuoteModal } from './QuoteModal';
import type { FieldName, TopTheme } from '../../types';
import { formatFieldName } from '../../utils/formatters';
import { Sparkles } from 'lucide-react';

const FIELD_OPTIONS: FieldName[] = [
  'product_quality',
  'user_experience',
  'business_practices',
  'financial_performance',
  'publisher_relations',
  'advertiser_value',
];

export const ThemeExplorer: React.FC = () => {
  const { topThemes } = useData();
  const [selectedField, setSelectedField] = useState<FieldName>('product_quality');
  const [selectedQuote, setSelectedQuote] = useState<TopTheme['representative_quotes'][0] | null>(
    null
  );

  const currentThemes = topThemes?.[selectedField] || [];

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-6 h-6 text-purple-400" />
          <h3 className="text-xl font-bold text-slate-100">Top Themes by Field</h3>
        </div>
        <p className="text-sm text-slate-400">
          Explore the most frequently mentioned themes and topics for each field
        </p>
      </div>

      {/* Field selector */}
      <div className="mb-6">
        <div className="flex flex-wrap gap-2">
          {FIELD_OPTIONS.map((field) => (
            <button
              key={field}
              onClick={() => setSelectedField(field)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedField === field
                  ? 'bg-purple-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {formatFieldName(field)}
            </button>
          ))}
        </div>
      </div>

      {/* Theme cards */}
      <div className="space-y-4">
        {currentThemes.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <p>No themes found for this field</p>
          </div>
        ) : (
          currentThemes.slice(0, 5).map((theme, idx) => (
            <ThemeCard
              key={idx}
              theme={theme}
              onViewQuote={setSelectedQuote}
            />
          ))
        )}
      </div>

      {/* Quote modal */}
      <QuoteModal quote={selectedQuote} onClose={() => setSelectedQuote(null)} />
    </div>
  );
};
