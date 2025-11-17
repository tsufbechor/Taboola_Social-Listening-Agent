import React from 'react';
import { DataProvider, useData } from './context/DataContext';
import { Header } from './components/Layout/Header';
import { Loading } from './components/Layout/Loading';
import { ErrorDisplay } from './components/Layout/ErrorDisplay';
import { Overview } from './components/Dashboard/Overview';
import { FieldSentimentChart } from './components/Charts/FieldSentimentChart';
import { TrendLineChart } from './components/Charts/TrendLineChart';
import { ThemeExplorer } from './components/Themes/ThemeExplorer';
import { PostsTable } from './components/DataTable/PostsTable';
import { FilterPanel } from './components/Filters/FilterPanel';

// Main dashboard content
const DashboardContent: React.FC = () => {
  const { isLoading, error } = useData();

  if (isLoading) {
    return <Loading />;
  }

  if (error) {
    return <ErrorDisplay error={error} />;
  }

  return (
    <div className="min-h-screen bg-slate-900">
      <Header />
      <div className="container mx-auto px-4 lg:px-6 py-8">
        <div className="grid lg:grid-cols-12 gap-6">
          {/* Main content */}
          <div className="lg:col-span-9 space-y-8">
            {/* Overview section */}
            <section>
              <Overview />
            </section>

            {/* Field sentiment analysis */}
            <section>
              <FieldSentimentChart />
            </section>

            {/* Trend analysis */}
            <section>
              <TrendLineChart />
            </section>

            {/* Theme explorer */}
            <section>
              <ThemeExplorer />
            </section>

            {/* Data table */}
            <section>
              <PostsTable />
            </section>
          </div>

          {/* Sidebar with filters */}
          <aside className="lg:col-span-3">
            <FilterPanel />
          </aside>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-800 mt-12">
        <div className="container mx-auto px-6 py-6">
          <p className="text-center text-slate-500 text-sm">
            Taboola Sentiment Analysis Dashboard &copy; {new Date().getFullYear()}
          </p>
        </div>
      </footer>
    </div>
  );
};

function App() {
  return (
    <DataProvider>
      <DashboardContent />
    </DataProvider>
  );
}

export default App;
