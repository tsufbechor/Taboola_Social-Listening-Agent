import React from 'react';
import { ExternalLink, Quote } from 'lucide-react';
import type { TopTheme } from '../../types';
import { truncateText } from '../../utils/formatters';
import { getSentimentBgClass } from '../../utils/sentimentColors';

interface ThemeCardProps {
  theme: TopTheme;
  onViewQuote: (quote: TopTheme['representative_quotes'][0]) => void;
}

export const ThemeCard: React.FC<ThemeCardProps> = ({ theme, onViewQuote }) => {
  return (
    <div className="bg-slate-800 border border-slate-700 rounded-lg p-5 hover:border-slate-600 transition-all">
      <div className="flex items-start justify-between mb-3">
        <h4 className="text-lg font-bold text-slate-100 flex-1">{theme.theme}</h4>
        <div className="flex gap-2">
          <span className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full text-xs font-semibold">
            {theme.frequency} mentions
          </span>
          <span className="px-3 py-1 bg-purple-500/20 text-purple-400 rounded-full text-xs font-semibold">
            {(theme.avg_relevance * 100).toFixed(0)}% relevance
          </span>
        </div>
      </div>

      {theme.representative_quotes.length > 0 && (
        <div className="space-y-3 mt-4">
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <Quote className="w-4 h-4" />
            <span>Representative Quotes:</span>
          </div>
          {theme.representative_quotes.slice(0, 2).map((quote, idx) => (
            <div
              key={idx}
              className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50"
            >
              <div className="flex items-start justify-between gap-3 mb-2">
                <span
                  className={`px-2 py-1 rounded text-xs font-medium ${getSentimentBgClass(
                    quote.sentiment
                  )}`}
                >
                  {quote.sentiment}
                </span>
              </div>
              <p className="text-slate-300 text-sm mb-3 leading-relaxed">
                "{truncateText(quote.text, 120)}"
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => onViewQuote(quote)}
                  className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
                >
                  Read full quote
                </button>
                <a
                  href={quote.link}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-slate-400 hover:text-slate-300 transition-colors flex items-center gap-1"
                >
                  <ExternalLink className="w-3 h-3" />
                  View source
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
