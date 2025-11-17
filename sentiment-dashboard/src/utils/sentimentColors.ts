import type { SentimentType } from '../types';

export const SENTIMENT_COLORS: Record<SentimentType, string> = {
  positive: '#10b981', // green-500
  neutral: '#6b7280',  // gray-500
  negative: '#ef4444', // red-500
  mixed: '#f59e0b',    // amber-500
};

export const getSentimentColor = (sentiment: SentimentType): string => {
  return SENTIMENT_COLORS[sentiment];
};

export const getSentimentLabel = (sentiment: SentimentType): string => {
  return sentiment.charAt(0).toUpperCase() + sentiment.slice(1);
};

export const getSentimentBgClass = (sentiment: SentimentType): string => {
  const classMap: Record<SentimentType, string> = {
    positive: 'bg-green-500/20 text-green-400',
    neutral: 'bg-gray-500/20 text-gray-400',
    negative: 'bg-red-500/20 text-red-400',
    mixed: 'bg-amber-500/20 text-amber-400',
  };
  return classMap[sentiment];
};
