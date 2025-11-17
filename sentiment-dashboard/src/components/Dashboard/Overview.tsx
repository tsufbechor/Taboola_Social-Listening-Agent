import React from 'react';
import { KeyMetrics } from './KeyMetrics';
import { SentimentDistribution } from './SentimentDistribution';

export const Overview: React.FC = () => {
  return (
    <div className="space-y-6">
      <KeyMetrics />
      <SentimentDistribution />
    </div>
  );
};
