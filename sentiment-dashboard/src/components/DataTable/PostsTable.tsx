import React, { useState, useMemo } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { useData } from '../../context/DataContext';
import { TableRow } from './TableRow';

type SortField = 'date' | 'score' | 'sentiment' | 'subreddit' | 'mentions';
type SortDirection = 'asc' | 'desc';

const countTaboolaMentions = (text: string): number => {
  const regex = /taboola/gi;
  const matches = text.match(regex);
  return matches ? matches.length : 0;
};

export const PostsTable: React.FC = () => {
  const { filteredData, filters } = useData();
  const [sortField, setSortField] = useState<SortField>('mentions');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  // Sort data
  const sortedData = useMemo(() => {
    const sorted = [...filteredData];

    sorted.sort((a, b) => {
      let aVal: any, bVal: any;

      switch (sortField) {
        case 'date':
          aVal = a.metadata.created_utc;
          bVal = b.metadata.created_utc;
          break;
        case 'score':
          aVal = a.metadata.score;
          bVal = b.metadata.score;
          break;
        case 'sentiment':
          aVal = a.analysis.overall_sentiment;
          bVal = b.analysis.overall_sentiment;
          break;
        case 'subreddit':
          aVal = a.metadata.subreddit;
          bVal = b.metadata.subreddit;
          break;
        case 'mentions':
          aVal = countTaboolaMentions(a.text);
          bVal = countTaboolaMentions(b.text);
          break;
        default:
          return 0;
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [filteredData, sortField, sortDirection]);

  // Paginate data
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    return sortedData.slice(startIndex, endIndex);
  }, [sortedData, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(sortedData.length / itemsPerPage);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
    setCurrentPage(1);
  };

  const SortIcon: React.FC<{ field: SortField }> = ({ field }) => {
    if (sortField !== field) return <ArrowUpDown className="w-4 h-4" />;
    return sortDirection === 'asc' ? (
      <ArrowUp className="w-4 h-4" />
    ) : (
      <ArrowDown className="w-4 h-4" />
    );
  };

  if (sortedData.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg p-6 border border-slate-700">
        <div className="text-center py-12">
          <p className="text-slate-400 text-lg">No data matches your current filters</p>
          <p className="text-slate-500 text-sm mt-2">Try adjusting your filters to see results</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800 rounded-lg border border-slate-700">
      <div className="p-6 border-b border-slate-700">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-bold text-slate-100">Posts & Comments</h3>
          <div className="flex items-center gap-3">
            <span className="text-sm text-slate-400">
              Showing {paginatedData.length} of {sortedData.length} items
            </span>
            <select
              value={itemsPerPage}
              onChange={(e) => {
                setItemsPerPage(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="bg-slate-700 text-slate-300 text-sm rounded px-3 py-1.5 border border-slate-600"
            >
              <option value={10}>10 per page</option>
              <option value={25}>25 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
            </select>
          </div>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-slate-900/50">
            <tr className="border-b border-slate-700">
              <th className="p-4 w-12"></th>
              <th className="p-4 text-left">
                <button
                  onClick={() => handleSort('mentions')}
                  className="flex items-center gap-2 text-slate-300 hover:text-slate-100 transition-colors text-sm font-semibold"
                >
                  Mentions
                  <SortIcon field="mentions" />
                </button>
              </th>
              <th className="p-4 text-left">
                <button
                  onClick={() => handleSort('date')}
                  className="flex items-center gap-2 text-slate-300 hover:text-slate-100 transition-colors text-sm font-semibold"
                >
                  Date
                  <SortIcon field="date" />
                </button>
              </th>
              <th className="p-4 text-left">
                <button
                  onClick={() => handleSort('subreddit')}
                  className="flex items-center gap-2 text-slate-300 hover:text-slate-100 transition-colors text-sm font-semibold"
                >
                  Subreddit
                  <SortIcon field="subreddit" />
                </button>
              </th>
              <th className="p-4 text-left text-slate-300 text-sm font-semibold">Author</th>
              <th className="p-4 text-left">
                <button
                  onClick={() => handleSort('sentiment')}
                  className="flex items-center gap-2 text-slate-300 hover:text-slate-100 transition-colors text-sm font-semibold"
                >
                  Sentiment
                  <SortIcon field="sentiment" />
                </button>
              </th>
              <th className="p-4 text-left text-slate-300 text-sm font-semibold">Key Fields</th>
              <th className="p-4 text-left">
                <button
                  onClick={() => handleSort('score')}
                  className="flex items-center gap-2 text-slate-300 hover:text-slate-100 transition-colors text-sm font-semibold"
                >
                  Score
                  <SortIcon field="score" />
                </button>
              </th>
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((item) => (
              <TableRow
                key={item.metadata.id}
                item={item}
                searchQuery={filters.searchQuery}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="p-6 border-t border-slate-700 flex items-center justify-between">
          <button
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="px-4 py-2 bg-slate-700 text-slate-300 rounded hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Previous
          </button>
          <div className="flex items-center gap-2">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }

              return (
                <button
                  key={pageNum}
                  onClick={() => setCurrentPage(pageNum)}
                  className={`px-3 py-1.5 rounded transition-colors ${
                    currentPage === pageNum
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>
          <button
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="px-4 py-2 bg-slate-700 text-slate-300 rounded hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};
