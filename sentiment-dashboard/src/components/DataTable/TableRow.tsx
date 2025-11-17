import React, { useState } from 'react';
import { ChevronDown, ChevronRight, ExternalLink, Tag } from 'lucide-react';
import type { SentimentResult } from '../../types';
import { formatDate, formatFieldName, formatPercentage } from '../../utils/formatters';
import { getSentimentBgClass } from '../../utils/sentimentColors';

interface TableRowProps {
  item: SentimentResult;
  searchQuery?: string;
}

const countTaboolaMentions = (text: string): number => {
  const regex = /taboola/gi;
  const matches = text.match(regex);
  return matches ? matches.length : 0;
};

export const TableRow: React.FC<TableRowProps> = ({ item, searchQuery }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Get the top fields mentioned (confidence > 0.5)
  const topFields = Object.entries(item.analysis.field_sentiments)
    .filter(([_, sentiment]) => sentiment.confidence > 0.5)
    .sort((a, b) => b[1].confidence - a[1].confidence)
    .slice(0, 3);

  // Count Taboola mentions
  const taboolaMentions = countTaboolaMentions(item.text);

  // Highlight search terms in text
  const highlightText = (text: string) => {
    if (!searchQuery || !searchQuery.trim()) return text;
    const regex = new RegExp(`(${searchQuery})`, 'gi');
    const parts = text.split(regex);
    return parts.map((part, i) =>
      regex.test(part) ? (
        <mark key={i} className="bg-yellow-500/30 text-yellow-200">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  return (
    <>
      <tr className="border-b border-slate-700 hover:bg-slate-800/50 transition-colors">
        <td className="p-4">
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-slate-400 hover:text-slate-100 transition-colors"
          >
            {isExpanded ? (
              <ChevronDown className="w-5 h-5" />
            ) : (
              <ChevronRight className="w-5 h-5" />
            )}
          </button>
        </td>
        <td className="p-4">
          <span className={`text-sm font-semibold ${taboolaMentions > 0 ? 'text-blue-400' : 'text-slate-500'}`}>
            {taboolaMentions}
          </span>
        </td>
        <td className="p-4">
          <div className="text-sm text-slate-300">
            {formatDate(item.metadata.created_utc)}
          </div>
          <div className="text-xs text-slate-500">
            {item.metadata.created_utc}
          </div>
        </td>
        <td className="p-4">
          <span className="text-sm px-2 py-1 bg-slate-700 text-slate-300 rounded">
            r/{item.metadata.subreddit}
          </span>
        </td>
        <td className="p-4">
          <span className="text-sm text-slate-400">{item.metadata.author}</span>
        </td>
        <td className="p-4">
          <span
            className={`px-3 py-1 rounded-full text-xs font-medium ${getSentimentBgClass(
              item.analysis.overall_sentiment
            )}`}
          >
            {item.analysis.overall_sentiment}
          </span>
        </td>
        <td className="p-4">
          <div className="flex flex-wrap gap-1">
            {topFields.map(([field, sentiment]) => (
              <span
                key={field}
                className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs"
                title={`Confidence: ${formatPercentage(sentiment.confidence * 100)}`}
              >
                {formatFieldName(field)}
              </span>
            ))}
          </div>
        </td>
        <td className="p-4">
          <div className="flex items-center gap-1">
            <span className="text-sm text-slate-300">{item.metadata.score}</span>
            <span className="text-xs text-slate-500">
              ({item.metadata.num_comments} comments)
            </span>
          </div>
        </td>
      </tr>

      {isExpanded && (
        <tr className="border-b border-slate-700 bg-slate-800/30">
          <td colSpan={8} className="p-6">
            <div className="space-y-4">
              {/* Full text */}
              <div>
                <h4 className="text-sm font-semibold text-slate-300 mb-2">Full Text:</h4>
                <p className="text-slate-100 leading-relaxed bg-slate-900/50 p-4 rounded-lg">
                  {highlightText(item.text)}
                </p>
              </div>

              {/* Field sentiments */}
              <div>
                <h4 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                  <Tag className="w-4 h-4" />
                  Field Analysis:
                </h4>
                <div className="grid md:grid-cols-2 gap-3">
                  {Object.entries(item.analysis.field_sentiments).map(([field, sentiment]) => (
                    <div
                      key={field}
                      className="bg-slate-900/50 p-3 rounded-lg border border-slate-700/50"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm font-medium text-slate-300">
                          {formatFieldName(field)}
                        </span>
                        <div className="flex items-center gap-2">
                          <span
                            className={`px-2 py-0.5 rounded text-xs ${getSentimentBgClass(
                              sentiment.sentiment
                            )}`}
                          >
                            {sentiment.sentiment}
                          </span>
                          <span className="text-xs text-slate-500">
                            {formatPercentage(sentiment.confidence * 100)}
                          </span>
                        </div>
                      </div>
                      {sentiment.key_phrases.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {sentiment.key_phrases.map((phrase, idx) => (
                            <span
                              key={idx}
                              className="text-xs px-2 py-0.5 bg-slate-800 text-slate-400 rounded"
                            >
                              {phrase}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Edge cases */}
              {(item.analysis.edge_cases.is_sarcastic ||
                item.analysis.edge_cases.has_mixed_sentiment ||
                item.analysis.edge_cases.is_non_english ||
                item.analysis.edge_cases.is_spam) && (
                <div>
                  <h4 className="text-sm font-semibold text-slate-300 mb-2">Edge Cases:</h4>
                  <div className="flex flex-wrap gap-2">
                    {item.analysis.edge_cases.is_sarcastic && (
                      <span className="px-2 py-1 bg-orange-500/20 text-orange-400 rounded text-xs">
                        Sarcastic
                      </span>
                    )}
                    {item.analysis.edge_cases.has_mixed_sentiment && (
                      <span className="px-2 py-1 bg-amber-500/20 text-amber-400 rounded text-xs">
                        Mixed Sentiment
                      </span>
                    )}
                    {item.analysis.edge_cases.is_non_english && (
                      <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded text-xs">
                        Non-English ({item.analysis.edge_cases.language})
                      </span>
                    )}
                    {item.analysis.edge_cases.is_spam && (
                      <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs">
                        Spam
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Link to original */}
              <div>
                <a
                  href={item.metadata.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors text-sm"
                >
                  <ExternalLink className="w-4 h-4" />
                  View Original Post
                </a>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
};
