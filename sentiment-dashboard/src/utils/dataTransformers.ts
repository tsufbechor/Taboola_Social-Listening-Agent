import type {
  FieldDistribution,
  FieldChartData,
  TrendData,
  TrendChartData,
  SentimentResult,
  FieldName,
  TopThemes,
  SentimentType,
} from '../types';
import { formatFieldName } from './formatters';

/**
 * Transform field distributions to chart data format
 */
export const transformFieldDistributions = (
  distributions: FieldDistribution[]
): FieldChartData[] => {
  return distributions.map((field) => ({
    name: formatFieldName(field.field),
    Positive: field.positive || 0,
    Neutral: field.neutral || 0,
    Negative: field.negative || 0,
    Mixed: field.mixed || 0,
    mentions: field.total_mentions,
  }));
};

/**
 * Transform trend data for line charts
 */
export const transformTrendData = (
  trends: TrendData[],
  metric: 'overall' | FieldName = 'overall'
): TrendChartData[] => {
  if (metric === 'overall') {
    return trends.map((trend) => ({
      period: trend.period,
      Positive: trend.overall_positive_pct || 0,
      Neutral: trend.overall_neutral_pct || 0,
      Negative: trend.overall_negative_pct || 0,
      Mixed: trend.overall_mixed_pct || 0,
    }));
  }

  // For specific fields
  return trends.map((trend) => {
    const fieldKey = metric.replace(/_/g, '_');
    return {
      period: trend.period,
      Positive: (trend as any)[`${fieldKey}_positive_pct`] || 0,
      Neutral: (trend as any)[`${fieldKey}_neutral_pct`] || 0,
      Negative: (trend as any)[`${fieldKey}_negative_pct`] || 0,
    };
  });
};

/**
 * Calculate sentiment distribution from results
 */
export const calculateSentimentDistribution = (
  results: SentimentResult[]
): Record<string, number> => {
  const distribution = {
    positive: 0,
    neutral: 0,
    negative: 0,
    mixed: 0,
  };

  results.forEach((result) => {
    distribution[result.analysis.overall_sentiment]++;
  });

  return distribution;
};

/**
 * Get unique subreddits from results
 */
export const getUniqueSubreddits = (results: SentimentResult[]): string[] => {
  const subreddits = new Set<string>();
  results.forEach((result) => {
    subreddits.add(result.metadata.subreddit);
  });
  return Array.from(subreddits).sort();
};

/**
 * Get date range from results
 */
export const getDateRange = (
  results: SentimentResult[]
): { min: number; max: number } => {
  if (results.length === 0) {
    return { min: 0, max: 0 };
  }

  let min = results[0].metadata.created_utc;
  let max = results[0].metadata.created_utc;

  results.forEach((result) => {
    const timestamp = result.metadata.created_utc;
    if (timestamp < min) min = timestamp;
    if (timestamp > max) max = timestamp;
  });

  return { min, max };
};

/**
 * Calculate field distributions from filtered results
 */
export const calculateFieldDistributions = (
  results: SentimentResult[]
): FieldChartData[] => {
  const fields: FieldName[] = [
    'product_quality',
    'user_experience',
    'business_practices',
    'financial_performance',
    'publisher_relations',
    'advertiser_value',
  ];

  return fields.map((field) => {
    const distribution = {
      positive: 0,
      neutral: 0,
      negative: 0,
      mixed: 0,
    };
    let totalMentions = 0;

    results.forEach((result) => {
      const fieldSentiment = result.analysis.field_sentiments[field];
      if (fieldSentiment.confidence > 0.5) {
        totalMentions++;
        distribution[fieldSentiment.sentiment]++;
      }
    });

    // Convert to percentages
    const total = totalMentions || 1;
    return {
      name: formatFieldName(field),
      Positive: (distribution.positive / total) * 100,
      Neutral: (distribution.neutral / total) * 100,
      Negative: (distribution.negative / total) * 100,
      Mixed: (distribution.mixed / total) * 100,
      mentions: totalMentions,
    };
  });
};

/**
 * Calculate trend data from filtered results
 */
export const calculateTrendData = (
  results: SentimentResult[],
  metric: 'overall' | FieldName = 'overall'
): TrendChartData[] => {
  // Group by month
  const groupedByMonth: Record<string, SentimentResult[]> = {};

  results.forEach((result) => {
    const date = new Date(result.metadata.created_utc * 1000);
    const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;

    if (!groupedByMonth[monthKey]) {
      groupedByMonth[monthKey] = [];
    }
    groupedByMonth[monthKey].push(result);
  });

  // Calculate percentages for each month
  const trendData = Object.entries(groupedByMonth)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([period, items]) => {
      const distribution = {
        positive: 0,
        neutral: 0,
        negative: 0,
        mixed: 0,
      };

      if (metric === 'overall') {
        items.forEach((item) => {
          distribution[item.analysis.overall_sentiment]++;
        });
      } else {
        items.forEach((item) => {
          const fieldSentiment = item.analysis.field_sentiments[metric];
          if (fieldSentiment.confidence > 0.5) {
            distribution[fieldSentiment.sentiment]++;
          }
        });
      }

      const total = Object.values(distribution).reduce((sum, val) => sum + val, 0) || 1;

      return {
        period,
        Positive: (distribution.positive / total) * 100,
        Neutral: (distribution.neutral / total) * 100,
        Negative: (distribution.negative / total) * 100,
        Mixed: (distribution.mixed / total) * 100,
      };
    });

  return trendData;
};

/**
 * Calculate top themes from filtered results
 */
export const calculateTopThemes = (results: SentimentResult[]): TopThemes => {
  const fields: FieldName[] = [
    'product_quality',
    'user_experience',
    'business_practices',
    'financial_performance',
    'publisher_relations',
    'advertiser_value',
  ];

  const topThemes: TopThemes = {};

  fields.forEach((field) => {
    const themeMap: Record<string, {
      theme: string;
      count: number;
      relevanceSum: number;
      quotes: Array<{
        text: string;
        link: string;
        sentiment: SentimentType;
        score: number;
      }>;
    }> = {};

    results.forEach((result) => {
      const fieldSentiment = result.analysis.field_sentiments[field];
      if (fieldSentiment.confidence > 0.5) {
        result.analysis.themes.forEach((theme) => {
          if (theme.relevance > 0.5) {
            if (!themeMap[theme.theme]) {
              themeMap[theme.theme] = {
                theme: theme.theme,
                count: 0,
                relevanceSum: 0,
                quotes: [],
              };
            }
            themeMap[theme.theme].count++;
            themeMap[theme.theme].relevanceSum += theme.relevance;

            // Add as representative quote if score is high enough
            if (result.metadata.score >= 1 && themeMap[theme.theme].quotes.length < 5) {
              themeMap[theme.theme].quotes.push({
                text: result.text,
                link: result.metadata.url,
                sentiment: fieldSentiment.sentiment as SentimentType,
                score: result.metadata.score,
              });
            }
          }
        });
      }
    });

    // Convert to TopTheme array and sort by frequency
    topThemes[field] = Object.values(themeMap)
      .map((item) => ({
        theme: item.theme,
        frequency: item.count,
        avg_relevance: item.relevanceSum / item.count,
        representative_quotes: item.quotes.slice(0, 3),
      }))
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 10);
  });

  return topThemes;
};
