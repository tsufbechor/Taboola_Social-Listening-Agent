import React from 'react';
import { Database, Sparkles, Hash } from 'lucide-react';
import type { DataSource } from '../../types';

interface DataSourceToggleProps {
  dataSource: DataSource;
  onDataSourceChange: (source: DataSource) => void;
}

const DATA_SOURCES: Array<{ value: DataSource; label: string; icon: typeof Database }> = [
  { value: 'reddit', label: 'Reddit', icon: Database },
  { value: 'hackernews', label: 'Hacker News', icon: Hash },
  { value: 'ai-generated', label: 'AI Generated', icon: Sparkles },
];

export const DataSourceToggle: React.FC<DataSourceToggleProps> = ({
  dataSource,
  onDataSourceChange,
}) => {
  return (
    <div className="flex items-center gap-1 bg-slate-700/50 rounded-lg p-1">
      {DATA_SOURCES.map((source) => {
        const Icon = source.icon;
        const isActive = dataSource === source.value;

        return (
          <button
            key={source.value}
            onClick={() => onDataSourceChange(source.value)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
              isActive
                ? 'bg-blue-600 text-white shadow-lg'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700'
            }`}
          >
            <Icon className="w-4 h-4" />
            <span>{source.label}</span>
          </button>
        );
      })}
    </div>
  );
};
