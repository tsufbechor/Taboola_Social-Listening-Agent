import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import { useDataLoader } from '../hooks/useDataLoader';
import { useFilters } from '../hooks/useFilters';
import type {
  SentimentResult,
  TrendData,
  FieldDistribution,
  SummaryReport,
  TopThemes,
  FilterState,
  SentimentType,
  ContextType,
  FieldName,
  DataSource,
} from '../types';

interface DataContextType {
  // Raw data
  sentimentResults: SentimentResult[];
  trends: TrendData[];
  fieldDistributions: FieldDistribution[];
  summaryReport: SummaryReport | null;
  topThemes: TopThemes | null;

  // Loading state
  isLoading: boolean;
  error: Error | null;

  // Data source
  dataSource: DataSource;
  setDataSource: (source: DataSource) => void;

  // Filtered data
  filteredData: SentimentResult[];

  // Filter state and actions
  filters: FilterState;
  updateDateRange: (start: number | null, end: number | null) => void;
  toggleSentiment: (sentiment: SentimentType) => void;
  toggleField: (field: FieldName) => void;
  toggleSubreddit: (subreddit: string) => void;
  togglePostType: (type: ContextType) => void;
  toggleEdgeCase: (caseType: keyof FilterState['edgeCases']) => void;
  setSearchQuery: (query: string) => void;
  clearFilters: () => void;
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export const DataProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Data source state (default to Reddit)
  const [dataSource, setDataSource] = useState<DataSource>('reddit');

  // Load all data
  const {
    sentimentResults,
    trends,
    fieldDistributions,
    summaryReport,
    topThemes,
    isLoading,
    error,
  } = useDataLoader(dataSource);

  // Set up filtering
  const filterHooks = useFilters(sentimentResults);

  const value: DataContextType = {
    sentimentResults,
    trends,
    fieldDistributions,
    summaryReport,
    topThemes,
    isLoading,
    error,
    dataSource,
    setDataSource,
    ...filterHooks,
  };

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};

export const useData = (): DataContextType => {
  const context = useContext(DataContext);
  if (context === undefined) {
    throw new Error('useData must be used within a DataProvider');
  }
  return context;
};
