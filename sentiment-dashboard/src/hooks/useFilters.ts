import { useState, useMemo } from 'react';
import type { FilterState, SentimentResult, SentimentType, ContextType, FieldName } from '../types';

const initialFilterState: FilterState = {
  dateRange: {
    start: null,
    end: null,
  },
  sentiments: [],
  fields: [],
  subreddits: [],
  postTypes: [],
  edgeCases: {
    sarcastic: false,
    mixedSentiment: false,
    nonEnglish: false,
    spam: false,
  },
  searchQuery: '',
};

export const useFilters = (sentimentResults: SentimentResult[]) => {
  const [filters, setFilters] = useState<FilterState>(initialFilterState);

  // Apply all filters to sentiment results
  const filteredData = useMemo(() => {
    let filtered = sentimentResults;

    // Date range filter
    if (filters.dateRange.start !== null || filters.dateRange.end !== null) {
      filtered = filtered.filter((item) => {
        const timestamp = item.metadata.created_utc;
        const afterStart = filters.dateRange.start === null || timestamp >= filters.dateRange.start;
        const beforeEnd = filters.dateRange.end === null || timestamp <= filters.dateRange.end;
        return afterStart && beforeEnd;
      });
    }

    // Sentiment filter
    if (filters.sentiments.length > 0) {
      filtered = filtered.filter((item) =>
        filters.sentiments.includes(item.analysis.overall_sentiment)
      );
    }

    // Field filter (items that mention selected fields with confidence > 0.5)
    if (filters.fields.length > 0) {
      filtered = filtered.filter((item) =>
        filters.fields.some(
          (field) => item.analysis.field_sentiments[field].confidence > 0.5
        )
      );
    }

    // Subreddit filter
    if (filters.subreddits.length > 0) {
      filtered = filtered.filter((item) =>
        filters.subreddits.includes(item.metadata.subreddit)
      );
    }

    // Post type filter
    if (filters.postTypes.length > 0) {
      filtered = filtered.filter((item) => filters.postTypes.includes(item.context));
    }

    // Edge cases filters
    if (filters.edgeCases.sarcastic) {
      filtered = filtered.filter((item) => item.analysis.edge_cases.is_sarcastic);
    }
    if (filters.edgeCases.mixedSentiment) {
      filtered = filtered.filter((item) => item.analysis.edge_cases.has_mixed_sentiment);
    }
    if (filters.edgeCases.nonEnglish) {
      filtered = filtered.filter((item) => item.analysis.edge_cases.is_non_english);
    }
    if (filters.edgeCases.spam) {
      filtered = filtered.filter((item) => item.analysis.edge_cases.is_spam);
    }

    // Search query filter
    if (filters.searchQuery.trim()) {
      const query = filters.searchQuery.toLowerCase();
      filtered = filtered.filter(
        (item) =>
          item.text.toLowerCase().includes(query) ||
          item.metadata.author.toLowerCase().includes(query) ||
          Object.values(item.analysis.field_sentiments).some((field) =>
            field.key_phrases.some((phrase) => phrase.toLowerCase().includes(query))
          )
      );
    }

    return filtered;
  }, [sentimentResults, filters]);

  // Update individual filter properties
  const updateDateRange = (start: number | null, end: number | null) => {
    setFilters((prev) => ({ ...prev, dateRange: { start, end } }));
  };

  const toggleSentiment = (sentiment: SentimentType) => {
    setFilters((prev) => ({
      ...prev,
      sentiments: prev.sentiments.includes(sentiment)
        ? prev.sentiments.filter((s) => s !== sentiment)
        : [...prev.sentiments, sentiment],
    }));
  };

  const toggleField = (field: FieldName) => {
    setFilters((prev) => ({
      ...prev,
      fields: prev.fields.includes(field)
        ? prev.fields.filter((f) => f !== field)
        : [...prev.fields, field],
    }));
  };

  const toggleSubreddit = (subreddit: string) => {
    setFilters((prev) => ({
      ...prev,
      subreddits: prev.subreddits.includes(subreddit)
        ? prev.subreddits.filter((s) => s !== subreddit)
        : [...prev.subreddits, subreddit],
    }));
  };

  const togglePostType = (type: ContextType) => {
    setFilters((prev) => ({
      ...prev,
      postTypes: prev.postTypes.includes(type)
        ? prev.postTypes.filter((t) => t !== type)
        : [...prev.postTypes, type],
    }));
  };

  const toggleEdgeCase = (caseType: keyof FilterState['edgeCases']) => {
    setFilters((prev) => ({
      ...prev,
      edgeCases: {
        ...prev.edgeCases,
        [caseType]: !prev.edgeCases[caseType],
      },
    }));
  };

  const setSearchQuery = (query: string) => {
    setFilters((prev) => ({ ...prev, searchQuery: query }));
  };

  const clearFilters = () => {
    setFilters(initialFilterState);
  };

  return {
    filters,
    filteredData,
    updateDateRange,
    toggleSentiment,
    toggleField,
    toggleSubreddit,
    togglePostType,
    toggleEdgeCase,
    setSearchQuery,
    clearFilters,
  };
};
