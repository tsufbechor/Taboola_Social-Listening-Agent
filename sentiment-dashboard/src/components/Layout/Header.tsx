import React from 'react';
import { BarChart3 } from 'lucide-react';
import { useData } from '../../context/DataContext';
import { DataSourceToggle } from './DataSourceToggle';

export const Header: React.FC = () => {
  const { dataSource, setDataSource } = useData();

  return (
    <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-50">
      <div className="px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-blue-500/20 p-2 rounded-lg">
              <BarChart3 className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-100">
                Taboola Sentiment Analysis
              </h1>
              <p className="text-sm text-slate-400">
                Social Listening Dashboard - Realize Product
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <DataSourceToggle
              dataSource={dataSource}
              onDataSourceChange={setDataSource}
            />
          </div>
        </div>
      </div>
    </header>
  );
};
