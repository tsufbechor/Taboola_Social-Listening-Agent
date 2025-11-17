import React from 'react';
import { X, ExternalLink, ThumbsUp } from 'lucide-react';
import type { TopTheme } from '../../types';
import { getSentimentBgClass } from '../../utils/sentimentColors';

interface QuoteModalProps {
  quote: TopTheme['representative_quotes'][0] | null;
  onClose: () => void;
}

export const QuoteModal: React.FC<QuoteModalProps> = ({ quote, onClose }) => {
  if (!quote) return null;

  return (
    <div
      className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="bg-slate-800 border border-slate-700 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-y-auto scrollbar-thin"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-slate-800 border-b border-slate-700 p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h3 className="text-xl font-bold text-slate-100">Full Quote</h3>
            <span
              className={`px-3 py-1 rounded-full text-sm font-medium ${getSentimentBgClass(
                quote.sentiment
              )}`}
            >
              {quote.sentiment}
            </span>
            <div className="flex items-center gap-1.5 px-3 py-1 bg-blue-500/20 text-blue-400 rounded-full">
              <ThumbsUp className="w-4 h-4" />
              <span className="text-sm font-semibold">{quote.score}</span>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-100 transition-colors"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6">
          <div className="bg-slate-900/50 rounded-lg p-6 mb-6 border border-slate-700/50">
            <p className="text-slate-100 text-base leading-relaxed whitespace-pre-wrap">
              "{quote.text}"
            </p>
          </div>

          <a
            href={quote.link}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <ExternalLink className="w-4 h-4" />
            View Original Post
          </a>
        </div>
      </div>
    </div>
  );
};
