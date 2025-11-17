import React, { useMemo } from 'react';
import { Calendar, X } from 'lucide-react';
import { useData } from '../../context/DataContext';
import { getDateRange } from '../../utils/dataTransformers';
import { formatDate } from '../../utils/formatters';

export const DateRangePicker: React.FC = () => {
  const { sentimentResults, filters, updateDateRange } = useData();

  const { min, max } = useMemo(() => getDateRange(sentimentResults), [sentimentResults]);

  const handleStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const timestamp = e.target.value ? new Date(e.target.value).getTime() / 1000 : null;
    updateDateRange(timestamp, filters.dateRange.end);
  };

  const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const timestamp = e.target.value ? new Date(e.target.value).getTime() / 1000 : null;
    updateDateRange(filters.dateRange.start, timestamp);
  };

  const clearDateRange = () => {
    updateDateRange(null, null);
  };

  const formatDateForInput = (timestamp: number | null) => {
    if (!timestamp) return '';
    const date = new Date(timestamp * 1000);
    return date.toISOString().split('T')[0];
  };

  const hasDateFilter = filters.dateRange.start !== null || filters.dateRange.end !== null;

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <label className="block text-sm font-semibold text-slate-300">Date Range</label>
        {hasDateFilter && (
          <button
            onClick={clearDateRange}
            className="text-xs text-slate-400 hover:text-slate-100 transition-colors flex items-center gap-1"
          >
            <X className="w-3 h-3" />
            Clear
          </button>
        )}
      </div>

      <div className="space-y-3">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <Calendar className="w-3 h-3" />
          <span>
            Available: {formatDate(min)} - {formatDate(max)}
          </span>
        </div>

        <div className="space-y-2">
          <div>
            <label className="block text-xs text-slate-400 mb-1">From</label>
            <input
              type="date"
              value={formatDateForInput(filters.dateRange.start)}
              onChange={handleStartChange}
              min={formatDateForInput(min)}
              max={formatDateForInput(max)}
              className="w-full bg-slate-700 text-slate-300 text-sm rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs text-slate-400 mb-1">To</label>
            <input
              type="date"
              value={formatDateForInput(filters.dateRange.end)}
              onChange={handleEndChange}
              min={formatDateForInput(min)}
              max={formatDateForInput(max)}
              className="w-full bg-slate-700 text-slate-300 text-sm rounded px-3 py-2 border border-slate-600 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
            />
          </div>
        </div>

        {hasDateFilter && (
          <div className="bg-blue-500/10 border border-blue-500/30 rounded px-3 py-2">
            <p className="text-xs text-blue-400">
              Showing: {filters.dateRange.start ? formatDate(filters.dateRange.start) : 'Start'} -{' '}
              {filters.dateRange.end ? formatDate(filters.dateRange.end) : 'End'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
