import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useData } from '../../context/DataContext';
import { calculateFieldDistributions } from '../../utils/dataTransformers';
import { SENTIMENT_COLORS } from '../../utils/sentimentColors';
import { formatPercentage } from '../../utils/formatters';

export const FieldSentimentChart: React.FC = () => {
  const { filteredData } = useData();

  const chartData = useMemo(() => {
    return calculateFieldDistributions(filteredData);
  }, [filteredData]);

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-slate-800 border border-slate-700 rounded-lg p-4 shadow-lg">
          <p className="text-slate-100 font-semibold mb-2">{label}</p>
          <p className="text-slate-400 text-sm mb-2">
            Total Mentions: {payload[0].payload.mentions}
          </p>
          {payload.map((entry: any) => (
            <div key={entry.name} className="flex items-center justify-between gap-4 mb-1">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-sm"
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
      <div className="mb-4">
        <h3 className="text-xl font-bold text-slate-100">
          Sentiment by Field
        </h3>
        <p className="text-sm text-slate-400 mt-1">
          Distribution of sentiment across all analyzed fields
        </p>
      </div>
      <div className="h-96">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            layout="vertical"
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis type="number" domain={[0, 100]} stroke="#94a3b8" />
            <YAxis
              type="category"
              dataKey="name"
              width={150}
              stroke="#94a3b8"
              tick={{ fill: '#cbd5e1', fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ fill: '#1e293b' }} />
            <Legend
              wrapperStyle={{ paddingTop: '20px' }}
              iconType="circle"
            />
            <Bar
              dataKey="Positive"
              stackId="a"
              fill={SENTIMENT_COLORS.positive}
              radius={[0, 0, 0, 0]}
            />
            <Bar
              dataKey="Mixed"
              stackId="a"
              fill={SENTIMENT_COLORS.mixed}
              radius={[0, 0, 0, 0]}
            />
            <Bar
              dataKey="Negative"
              stackId="a"
              fill={SENTIMENT_COLORS.negative}
              radius={[0, 0, 0, 0]}
            />
            <Bar
              dataKey="Neutral"
              stackId="a"
              fill={SENTIMENT_COLORS.neutral}
              radius={[0, 4, 4, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
