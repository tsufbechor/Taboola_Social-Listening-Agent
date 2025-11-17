import React, { useState, useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useData } from '../../context/DataContext';
import { calculateTrendData } from '../../utils/dataTransformers';
import { SENTIMENT_COLORS } from '../../utils/sentimentColors';
import type { FieldName } from '../../types';
import { formatPercentage } from '../../utils/formatters';

const FIELD_OPTIONS: Array<{ value: 'overall' | FieldName; label: string }> = [
  { value: 'overall', label: 'Overall Sentiment' },
  { value: 'product_quality', label: 'Product Quality' },
  { value: 'user_experience', label: 'User Experience' },
  { value: 'business_practices', label: 'Business Practices' },
  { value: 'financial_performance', label: 'Financial Performance' },
  { value: 'publisher_relations', label: 'Publisher Relations' },
  { value: 'advertiser_value', label: 'Advertiser Value' },
];

export const TrendLineChart: React.FC = () => {
  const { filteredData } = useData();
  const [selectedMetric, setSelectedMetric] = useState<'overall' | FieldName>('overall');
  const [visibleLines, setVisibleLines] = useState({
    Positive: true,
    Neutral: true,
    Negative: true,
    Mixed: true,
  });

  const chartData = useMemo(() => {
    return calculateTrendData(filteredData, selectedMetric);
  }, [filteredData, selectedMetric]);

  const toggleLine = (line: keyof typeof visibleLines) => {
    setVisibleLines((prev) => ({ ...prev, [line]: !prev[line] }));
  };

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 shadow-lg">
          <p className="text-slate-100 font-semibold mb-2">{label}</p>
          {payload.map((entry: any) => (
            <div key={entry.name} className="flex items-center justify-between gap-4 mb-1">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-slate-300 text-sm">{entry.name}</span>
              </div>
              <span className="text-slate-100 font-medium text-sm">
                {formatPercentage(entry.value)}
              </span>
            </div>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
      <div className="mb-6">
        <h3 className="text-xl font-bold text-slate-100 mb-3">
          Sentiment Trends Over Time
        </h3>

        {/* Metric selector */}
        <div className="flex flex-wrap gap-2 mb-4">
          {FIELD_OPTIONS.map((option) => (
            <button
              key={option.value}
              onClick={() => setSelectedMetric(option.value)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedMetric === option.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>

        {/* Line toggles */}
        <div className="flex flex-wrap gap-3">
          {Object.entries(visibleLines).map(([line, visible]) => (
            <button
              key={line}
              onClick={() => toggleLine(line as keyof typeof visibleLines)}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-all ${
                visible
                  ? 'bg-slate-700 text-slate-100'
                  : 'bg-slate-900 text-slate-500 opacity-50'
              }`}
            >
              <div
                className={`w-3 h-3 rounded-full ${visible ? '' : 'opacity-30'}`}
                style={{
                  backgroundColor: SENTIMENT_COLORS[line.toLowerCase() as keyof typeof SENTIMENT_COLORS],
                }}
              />
              <span>{line}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis
              dataKey="period"
              stroke="#94a3b8"
              tick={{ fill: '#cbd5e1', fontSize: 12 }}
            />
            <YAxis
              domain={[0, 100]}
              stroke="#94a3b8"
              tick={{ fill: '#cbd5e1', fontSize: 12 }}
              label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft', fill: '#94a3b8' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            {visibleLines.Positive && (
              <Line
                type="monotone"
                dataKey="Positive"
                stroke={SENTIMENT_COLORS.positive}
                strokeWidth={2}
                dot={{ fill: SENTIMENT_COLORS.positive, r: 4 }}
                activeDot={{ r: 6 }}
              />
            )}
            {visibleLines.Mixed && chartData[0]?.Mixed !== undefined && (
              <Line
                type="monotone"
                dataKey="Mixed"
                stroke={SENTIMENT_COLORS.mixed}
                strokeWidth={2}
                dot={{ fill: SENTIMENT_COLORS.mixed, r: 4 }}
                activeDot={{ r: 6 }}
              />
            )}
            {visibleLines.Negative && (
              <Line
                type="monotone"
                dataKey="Negative"
                stroke={SENTIMENT_COLORS.negative}
                strokeWidth={2}
                dot={{ fill: SENTIMENT_COLORS.negative, r: 4 }}
                activeDot={{ r: 6 }}
              />
            )}
            {visibleLines.Neutral && (
              <Line
                type="monotone"
                dataKey="Neutral"
                stroke={SENTIMENT_COLORS.neutral}
                strokeWidth={2}
                dot={{ fill: SENTIMENT_COLORS.neutral, r: 4 }}
                activeDot={{ r: 6 }}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
