import React from 'react';
import { ReferenceItem, PubMedArticle } from '../types';

interface DataDisplayAreaProps {
  references: ReferenceItem[];
  onReplace: (refId: string, article: PubMedArticle) => void;
}

export const DataDisplayArea: React.FC<DataDisplayAreaProps> = ({
  references,
  onReplace,
}) => {
  const renderKeywords = (keywords: any, differences: Record<string, any> = {}) => {
    const fields = [
      { key: 'title', label: '标题' },
      { key: 'authors', label: '作者' },
      { key: 'journal', label: '期刊' },
      { key: 'year', label: '年份' },
      { key: 'volume', label: '卷' },
      { key: 'issue', label: '期' },
      { key: 'pages', label: '页码' },
      { key: 'pmid', label: 'PMID' },
      { key: 'doi', label: 'DOI' },
    ];

    return (
      <div className="space-y-1 text-sm">
        {fields.map((field) => {
          const value = keywords[field.key];
          const diff = differences[field.key];
          const hasDiff = diff && diff.type === 'different';

          if (!value && !hasDiff) return null;

          return (
            <div key={field.key} className="flex">
              <span className="font-semibold text-gray-600 w-20">{field.label}:</span>
              <span className={hasDiff ? 'text-red-600' : 'text-gray-800'}>
                {Array.isArray(value) ? value.join(', ') : value}
                {hasDiff && (
                  <span className="ml-2 text-gray-500">
                    (原: {Array.isArray(diff.original) ? diff.original.join(', ') : diff.original})
                  </span>
                )}
              </span>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 h-[calc(100vh-200px)] flex flex-col">
      <h2 className="text-xl font-bold mb-4 text-gray-800">数据展示区</h2>
      <div className="flex-1 overflow-y-auto space-y-6 pr-2">
        {references.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            暂无数据，请在左侧输入参考文献
          </div>
        ) : (
          references.map((ref) => (
            <div key={ref.id} className="border border-gray-200 rounded-lg p-4">
              <div className="mb-3">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-semibold text-gray-800">原始参考文献</h3>
                  <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                    {ref.format_type || '未知格式'}
                  </span>
                </div>
                <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded">
                  {ref.original_text}
                </p>
              </div>

              <div className="mb-3">
                <h4 className="font-semibold text-gray-700 mb-2">提取的关键词</h4>
                {renderKeywords(ref.extracted_keywords)}
              </div>

              {ref.status === 'not_found' && (
                <div className="bg-yellow-50 border border-yellow-200 rounded p-3 mb-3">
                  <p className="text-yellow-800 text-sm">未检索到对应文献（相似度低于50%）</p>
                </div>
              )}

              {ref.matched_articles.length > 0 && (
                <div className="mb-3">
                  <h4 className="font-semibold text-gray-700 mb-2">
                    匹配的文献 ({ref.matched_articles.length}条)
                  </h4>
                  <div className="space-y-3">
                    {ref.matched_articles.map((article, idx) => (
                      <div
                        key={idx}
                        className="border border-blue-200 rounded p-3 bg-blue-50"
                      >
                        <div className="flex justify-between items-start mb-2">
                          <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded">
                            相似度: {(article.similarity_score * 100).toFixed(1)}%
                          </span>
                        </div>
                        {renderKeywords(article.keywords, article.differences)}
                        <div className="mt-3 flex gap-2">
                          <button
                            onClick={() => onReplace(ref.id, article)}
                            className="px-4 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                          >
                            替换
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

