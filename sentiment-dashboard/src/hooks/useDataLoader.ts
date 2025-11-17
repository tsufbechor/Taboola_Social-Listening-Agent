import { useState, useEffect } from 'react';
import type {
  SentimentResult,
  TrendData,
  FieldDistribution,
  SummaryReport,
  TopThemes,
  DataSource,
} from '../types';
import { parseCsv } from '../utils/csvParser';

interface DataState {
  sentimentResults: SentimentResult[];
  trends: TrendData[];
  fieldDistributions: FieldDistribution[];
  summaryReport: SummaryReport | null;
  topThemes: TopThemes | null;
  isLoading: boolean;
  error: Error | null;
}

export const useDataLoader = (dataSource: DataSource) => {
  const [data, setData] = useState<DataState>({
    sentimentResults: [],
    trends: [],
    fieldDistributions: [],
    summaryReport: null,
    topThemes: null,
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    async function loadAllData() {
      try {
        setData((prev) => ({ ...prev, isLoading: true, error: null }));

        // Construct paths based on data source
        const basePath = `/data/${dataSource}`;

        // Load all files in parallel
        const [resultsRes, trendsRes, distributionsRes, summaryRes, themesRes] =
          await Promise.all([
            fetch(`${basePath}/sentiment_results.json`),
            fetch(`${basePath}/sentiment_trends.csv`),
            fetch(`${basePath}/field_distributions.csv`),
            fetch(`${basePath}/summary_report.json`),
            fetch(`${basePath}/top_themes.json`),
          ]);

        // Parse JSON files
        const results = await resultsRes.json();
        const summary = await summaryRes.json();
        const themes = await themesRes.json();

        // Parse CSV files
        const trendsText = await trendsRes.text();
        const trends = parseCsv<TrendData>(trendsText);

        const distributionsText = await distributionsRes.text();
        const distributions = parseCsv<FieldDistribution>(distributionsText);

        setData({
          sentimentResults: results,
          trends,
          fieldDistributions: distributions,
          summaryReport: summary,
          topThemes: themes,
          isLoading: false,
          error: null,
        });
      } catch (error) {
        console.error('Error loading data:', error);
        setData((prev) => ({
          ...prev,
          isLoading: false,
          error: error as Error,
        }));
      }
    }

    loadAllData();
  }, [dataSource]);

  return data;
};
