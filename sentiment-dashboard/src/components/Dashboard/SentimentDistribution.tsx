import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { useData } from '../../context/DataContext';
import { SENTIMENT_COLORS } from '../../utils/sentimentColors';
import type { SentimentType } from '../../types';
import { formatPercentage } from '../../utils/formatters';

export const SentimentDistribution: React.FC = () => {
  const { filteredData } = useData();

  const chartData = useMemo(() => {
    const distribution = {
      positive: 0,
      neutral: 0,
      negative: 0,
      mixed: 0,
    };

    filteredData.forEach((item) => {
      distribution[item.analysis.overall_sentiment]++;
    });

    return Object.entries(distribution).map(([sentiment, count]) => ({
      name: sentiment.charAt(0).toUpperCase() + sentiment.slice(1),
      value: count,
      percentage: filteredData.length > 0 ? (count / filteredData.length) * 100 : 0,
      color: SENTIMENT_COLORS[sentiment as SentimentType],
    }));
  }, [filteredData]);

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 shadow-lg">
          <p className="text-slate-100 font-semibold">{data.name}</p>
          <p className="text-slate-300">Count: {data.value}</p>
          <p className="text-slate-300">{formatPercentage(data.percentage)}</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
      <h3 className="text-xl font-bold text-slate-100 mb-4">
        Overall Sentiment Distribution
      </h3>
      <div className="grid md:grid-cols-2 gap-6">
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ payload }) =>
                  payload.percentage > 5 ? `${payload.percentage.toFixed(0)}%` : ''
                }
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>
        <div className="flex flex-col justify-center space-y-3">
          {chartData.map((item) => (
            <div key={item.name} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-slate-300">{item.name}</span>
              </div>
              <div className="text-right">
                <span className="text-slate-100 font-semibold">{item.value}</span>
                <span className="text-slate-400 text-sm ml-2">
                  ({formatPercentage(item.percentage)})
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
