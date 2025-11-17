import React, { useMemo } from 'react';
import { Filter, X } from 'lucide-react';
import { useData } from '../../context/DataContext';
import { SearchBar } from './SearchBar';
import { DateRangePicker } from './DateRangePicker';
import type { SentimentType, ContextType, FieldName } from '../../types';
import { formatFieldName } from '../../utils/formatters';
import { getSentimentBgClass } from '../../utils/sentimentColors';
import { getUniqueSubreddits } from '../../utils/dataTransformers';

const SENTIMENT_OPTIONS: SentimentType[] = ['positive', 'neutral', 'negative', 'mixed'];
const POST_TYPE_OPTIONS: ContextType[] = ['post', 'comment'];
const FIELD_OPTIONS: FieldName[] = [
  'product_quality',
  'user_experience',
  'business_practices',
  'financial_performance',
  'publisher_relations',
  'advertiser_value',
];

export const FilterPanel: React.FC = () => {
  const {
    sentimentResults,
    filters,
    toggleSentiment,
    toggleField,
    toggleSubreddit,
    togglePostType,
    toggleEdgeCase,
    setSearchQuery,
    clearFilters,
  } = useData();

  const subreddits = useMemo(() => getUniqueSubreddits(sentimentResults), [sentimentResults]);

  const activeFilterCount = useMemo(() => {
    let count = 0;
    if (filters.dateRange.start !== null || filters.dateRange.end !== null) count++;
    if (filters.sentiments.length > 0) count++;
    if (filters.fields.length > 0) count++;
    if (filters.subreddits.length > 0) count++;
    if (filters.postTypes.length > 0) count++;
    if (Object.values(filters.edgeCases).some((v) => v)) count++;
    if (filters.searchQuery) count++;
    return count;
  }, [filters]);

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700 sticky top-20">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-bold text-slate-100">Filters</h3>
          {activeFilterCount > 0 && (
            <span className="px-2 py-0.5 bg-blue-600 text-white rounded-full text-xs font-semibold">
              {activeFilterCount}
            </span>
          )}
        </div>
        {activeFilterCount > 0 && (
          <button
            onClick={clearFilters}
            className="text-sm text-slate-400 hover:text-slate-100 transition-colors flex items-center gap-1"
          >
            <X className="w-4 h-4" />
            Clear all
          </button>
        )}
      </div>

      <div className="space-y-6">
        {/* Search */}
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-2">Search</label>
          <SearchBar value={filters.searchQuery} onChange={setSearchQuery} />
        </div>

        {/* Date Range */}
        <DateRangePicker />

        {/* Sentiment Filter */}
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-2">
            Sentiment
          </label>
          <div className="flex flex-wrap gap-2">
            {SENTIMENT_OPTIONS.map((sentiment) => (
              <button
                key={sentiment}
                onClick={() => toggleSentiment(sentiment)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  filters.sentiments.includes(sentiment)
                    ? getSentimentBgClass(sentiment) + ' ring-2 ring-offset-2 ring-offset-slate-800'
                    : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                }`}
              >
                {sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Field Filter */}
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-2">
            Focus Fields
          </label>
          <div className="space-y-2">
            {FIELD_OPTIONS.map((field) => (
              <label key={field} className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={filters.fields.includes(field)}
                  onChange={() => toggleField(field)}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-blue-500 focus:ring-offset-slate-800"
                />
                <span className="text-sm text-slate-300 group-hover:text-slate-100 transition-colors">
                  {formatFieldName(field)}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Post Type Filter */}
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-2">
            Post Type
          </label>
          <div className="flex gap-2">
            {POST_TYPE_OPTIONS.map((type) => (
              <button
                key={type}
                onClick={() => togglePostType(type)}
                className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  filters.postTypes.includes(type)
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-400 hover:bg-slate-600'
                }`}
              >
                {type.charAt(0).toUpperCase() + type.slice(1)}s
              </button>
            ))}
          </div>
        </div>

        {/* Subreddit Filter */}
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-2">
            Subreddits
          </label>
          <div className="space-y-2 max-h-48 overflow-y-auto scrollbar-thin">
            {subreddits.map((subreddit) => (
              <label key={subreddit} className="flex items-center gap-2 cursor-pointer group">
                <input
                  type="checkbox"
                  checked={filters.subreddits.includes(subreddit)}
                  onChange={() => toggleSubreddit(subreddit)}
                  className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-blue-500 focus:ring-offset-slate-800"
                />
                <span className="text-sm text-slate-300 group-hover:text-slate-100 transition-colors">
                  r/{subreddit}
                </span>
              </label>
            ))}
          </div>
        </div>

        {/* Edge Cases Filter */}
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-2">
            Edge Cases
          </label>
          <div className="space-y-2">
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                checked={filters.edgeCases.sarcastic}
                onChange={() => toggleEdgeCase('sarcastic')}
                className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-orange-600 focus:ring-orange-500 focus:ring-offset-slate-800"
              />
              <span className="text-sm text-slate-300 group-hover:text-slate-100 transition-colors">
                Sarcastic only
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                checked={filters.edgeCases.mixedSentiment}
                onChange={() => toggleEdgeCase('mixedSentiment')}
                className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-amber-600 focus:ring-amber-500 focus:ring-offset-slate-800"
              />
              <span className="text-sm text-slate-300 group-hover:text-slate-100 transition-colors">
                Mixed sentiment only
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                checked={filters.edgeCases.nonEnglish}
                onChange={() => toggleEdgeCase('nonEnglish')}
                className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-blue-500 focus:ring-offset-slate-800"
              />
              <span className="text-sm text-slate-300 group-hover:text-slate-100 transition-colors">
                Non-English only
              </span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer group">
              <input
                type="checkbox"
                checked={filters.edgeCases.spam}
                onChange={() => toggleEdgeCase('spam')}
                className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-red-600 focus:ring-red-500 focus:ring-offset-slate-800"
              />
              <span className="text-sm text-slate-300 group-hover:text-slate-100 transition-colors">
                Spam only
              </span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );
};
