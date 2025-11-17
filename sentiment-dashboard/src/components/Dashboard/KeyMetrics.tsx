import React from 'react';
import { FileText, MessageSquare, TrendingUp, Calendar } from 'lucide-react';
import { useData } from '../../context/DataContext';
import { formatDate, formatNumber } from '../../utils/formatters';

export const KeyMetrics: React.FC = () => {
  const { summaryReport, filteredData } = useData();

  if (!summaryReport) return null;

  const metrics = [
    {
      label: 'Total Items',
      value: formatNumber(filteredData.length),
      total: formatNumber(summaryReport.summary.total_items),
      icon: FileText,
      color: 'blue',
    },
    {
      label: 'Posts',
      value: formatNumber(filteredData.filter(item => item.context === 'post').length),
      total: formatNumber(summaryReport.summary.total_posts),
      icon: MessageSquare,
      color: 'green',
    },
    {
      label: 'Comments',
      value: formatNumber(filteredData.filter(item => item.context === 'comment').length),
      total: formatNumber(summaryReport.summary.total_comments),
      icon: MessageSquare,
      color: 'purple',
    },
    {
      label: 'Subreddits',
      value: summaryReport.summary.unique_subreddits,
      icon: TrendingUp,
      color: 'amber',
    },
  ];

  const dateRange = summaryReport.summary.date_range;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          const colorClasses = {
            blue: 'bg-blue-500/20 text-blue-400',
            green: 'bg-green-500/20 text-green-400',
            purple: 'bg-purple-500/20 text-purple-400',
            amber: 'bg-amber-500/20 text-amber-400',
          };

          return (
            <div
              key={metric.label}
              className="bg-slate-800 rounded-lg p-6 border border-slate-700 hover:border-slate-600 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <p className="text-slate-400 text-sm font-medium mb-1">
                    {metric.label}
                  </p>
                  <p className="text-3xl font-bold text-slate-100">
                    {metric.value}
                  </p>
                  {metric.total && metric.value !== metric.total && (
                    <p className="text-xs text-slate-500 mt-1">
                      of {metric.total} total
                    </p>
                  )}
                </div>
                <div className={`p-3 rounded-lg ${colorClasses[metric.color as keyof typeof colorClasses]}`}>
                  <Icon className="w-5 h-5" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Date Range Card */}
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <div className="flex items-center gap-3">
          <div className="bg-slate-700 p-3 rounded-lg">
            <Calendar className="w-5 h-5 text-slate-400" />
          </div>
          <div>
            <p className="text-sm text-slate-400 mb-1">Data Range</p>
            <p className="text-lg font-semibold text-slate-100">
              {formatDate(dateRange.earliest)} - {formatDate(dateRange.latest)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
