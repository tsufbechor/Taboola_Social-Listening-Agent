// Data source types
export type DataSource = 'reddit' | 'hackernews' | 'ai-generated';

// Sentiment types
export type SentimentType = 'positive' | 'neutral' | 'negative' | 'mixed';
export type ContextType = 'post' | 'comment';
export type FieldName =
  | 'product_quality'
  | 'user_experience'
  | 'business_practices'
  | 'financial_performance'
  | 'publisher_relations'
  | 'advertiser_value';

// Metadata structure
export interface Metadata {
  id: string;
  type: 'post' | 'comment';
  subreddit: string;
  author: string;
  created_utc: number;
  score: number;
  num_comments: number;
  url: string;
}

// Field sentiment structure
export interface FieldSentiment {
  sentiment: SentimentType;
  confidence: number;
  key_phrases: string[];
}

// Theme structure
export interface Theme {
  theme: string;
  relevance: number;
}

// Edge cases structure
export interface EdgeCases {
  is_sarcastic: boolean;
  has_mixed_sentiment: boolean;
  is_non_english: boolean;
  language: string;
  is_spam: boolean;
}

// Analysis structure
export interface Analysis {
  overall_sentiment: SentimentType;
  field_sentiments: Record<FieldName, FieldSentiment>;
  edge_cases: EdgeCases;
  themes: Theme[];
  reasoning: string;
}

// Main sentiment result structure
export interface SentimentResult {
  text: string;
  context: ContextType;
  metadata: Metadata;
  analysis: Analysis;
}

// Trend data structure (from CSV)
export interface TrendData {
  period: string;
  total_items: number;
  avg_score: number;
  overall_positive_pct: number;
  overall_neutral_pct: number;
  overall_negative_pct: number;
  overall_mixed_pct: number;
  product_quality_mentions: number;
  product_quality_positive_pct: number;
  product_quality_neutral_pct: number;
  product_quality_negative_pct: number;
  user_experience_mentions: number;
  user_experience_positive_pct: number;
  user_experience_neutral_pct: number;
  user_experience_negative_pct: number;
  business_practices_mentions: number;
  business_practices_positive_pct: number;
  business_practices_neutral_pct: number;
  business_practices_negative_pct: number;
  financial_performance_mentions: number;
  financial_performance_positive_pct: number;
  financial_performance_neutral_pct: number;
  financial_performance_negative_pct: number;
  publisher_relations_mentions: number;
  publisher_relations_positive_pct: number;
  publisher_relations_neutral_pct: number;
  publisher_relations_negative_pct: number;
  advertiser_value_mentions: number;
  advertiser_value_positive_pct: number;
  advertiser_value_neutral_pct: number;
  advertiser_value_negative_pct: number;
}

// Field distribution structure (from CSV)
export interface FieldDistribution {
  field: FieldName;
  positive: number;
  mixed: number;
  negative: number;
  neutral: number;
  total_mentions: number;
}

// Summary report structure
export interface SummaryReport {
  summary: {
    total_items: number;
    total_posts: number;
    total_comments: number;
    unique_subreddits: number;
    date_range: {
      earliest: number;
      latest: number;
    };
  };
  overall_sentiment_distribution: Record<SentimentType, number>;
  field_distributions: Record<FieldName, {
    positive: number;
    mixed: number;
    negative: number;
    neutral: number;
    total_mentions: number;
  }>;
  edge_cases: {
    total_sarcastic: number;
    total_mixed_sentiment: number;
    total_non_english: number;
    total_spam: number;
  };
  top_themes_by_field: Record<FieldName, Array<{
    theme: string;
    count: number;
    avg_relevance: number;
  }>>;
}

// Top themes structure
export interface TopTheme {
  theme: string;
  frequency: number;
  avg_relevance: number;
  representative_quotes: Array<{
    text: string;
    link: string;
    sentiment: SentimentType;
    score: number;
  }>;
}

export interface TopThemes {
  [field: string]: TopTheme[];
}

// Filter state
export interface FilterState {
  dateRange: {
    start: number | null;
    end: number | null;
  };
  sentiments: SentimentType[];
  fields: FieldName[];
  subreddits: string[];
  postTypes: ContextType[];
  edgeCases: {
    sarcastic: boolean;
    mixedSentiment: boolean;
    nonEnglish: boolean;
    spam: boolean;
  };
  searchQuery: string;
}

// Chart data types
export interface FieldChartData {
  name: string;
  Positive: number;
  Neutral: number;
  Negative: number;
  Mixed: number;
  mentions: number;
}

export interface TrendChartData {
  period: string;
  [key: string]: string | number;
}
