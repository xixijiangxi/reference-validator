import React, { useState } from 'react';
import { ReferenceItem, PubMedArticle } from '../types';

interface DataDisplayAreaProps {
  references: ReferenceItem[];
  onReplace: (refId: string, article: PubMedArticle) => void;
}

export const DataDisplayArea: React.FC<DataDisplayAreaProps> = ({
  references,
  onReplace,
}) => {
  const [expandedRefs, setExpandedRefs] = useState<Set<string>>(new Set());
  
  const toggleExpand = (refId: string) => {
    const newExpanded = new Set(expandedRefs);
    if (newExpanded.has(refId)) {
      newExpanded.delete(refId);
    } else {
      newExpanded.add(refId);
    }
    setExpandedRefs(newExpanded);
  };
  // 高亮显示差异字符
  const highlightDiff = (original: string, matched: string): JSX.Element => {
    if (!original || !matched) {
      return <span>{matched || original}</span>;
    }
    
    const orig = String(original).toLowerCase();
    const match = String(matched).toLowerCase();
    
    // 简单的高亮逻辑：找出不同的部分
    if (orig === match) {
      return <span>{matched}</span>;
    }
    
    // 如果完全不一样，高亮整个文本
    return (
      <span>
        <span className="bg-yellow-200 font-semibold">{matched}</span>
      </span>
    );
  };

  const renderKeywords = (keywords: any, differences: Record<string, any> = {}, isExtracted: boolean = false) => {
    const fields = [
      { key: 'title', label: '标题' },
      { key: 'authors', label: '作者' },
      { key: 'journal', label: '期刊' },
      { key: 'year', label: '年份' },
      { key: 'volume', label: '卷' },
      { key: 'issue', label: '期' },
      { key: 'pages', label: '页码' },
      { key: 'doi', label: 'DOI' },
    ];

    return (
      <div className="space-y-2 text-sm">
        {fields.map((field) => {
          const value = keywords[field.key];
          const diff = differences[field.key];
          const hasDiff = diff && diff.type === 'different';

          if (!value && !hasDiff) return null;

          return (
            <div key={field.key} className="flex items-start">
              <span className="font-semibold text-gray-600 w-24 flex-shrink-0">{field.label}:</span>
              <div className="flex-1">
                {hasDiff && !isExtracted ? (
                  <div>
                    <span className="text-gray-800">
                      {highlightDiff(diff.original, Array.isArray(value) ? value.join(', ') : value)}
                    </span>
                    <span className="ml-2 text-gray-500 text-xs">
                      (原: {Array.isArray(diff.original) ? diff.original.join(', ') : diff.original})
                    </span>
                  </div>
                ) : (
                  <span className="text-gray-800">
                    {Array.isArray(value) ? value.join(', ') : value}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // 获取文献的简短标题
  const getShortTitle = (title?: string, maxLength: number = 60) => {
    if (!title) return '无标题';
    return title.length > maxLength ? title.substring(0, maxLength) + '...' : title;
  };

  // 获取作者字符串
  const getAuthorsStr = (authors?: string[]) => {
    if (!authors || authors.length === 0) return '未知作者';
    if (authors.length <= 2) return authors.join(', ');
    return `${authors[0]}, ${authors[1]}, et al.`;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold mb-6 text-gray-800">Verification & Matching</h2>
      <div className="space-y-4">
        {references.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            暂无数据，请在左侧输入参考文献
          </div>
        ) : (
          references.map((ref) => {
            const isExpanded = expandedRefs.has(ref.id);
            const bestMatch = ref.matched_articles.length > 0 ? ref.matched_articles[0] : null;
            const matchScore = bestMatch ? (bestMatch.similarity_score * 100).toFixed(0) : null;
            const hasMatch = ref.status === 'matched' && bestMatch;

            return (
              <div 
                key={ref.id} 
                className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
              >
                {/* 折叠状态：显示基本信息 */}
                <div 
                  className="p-4 cursor-pointer bg-gray-50 hover:bg-gray-100 transition-colors"
                  onClick={() => toggleExpand(ref.id)}
                >
                  <div className="grid grid-cols-12 gap-4 items-center">
                    {/* Extracted Reference */}
                    <div className="col-span-4">
                      <div className="text-xs text-gray-500 mb-1">Extracted Reference</div>
                      <div className="font-medium text-sm text-gray-800">
                        {getShortTitle(ref.extracted_keywords.title)}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {getAuthorsStr(ref.extracted_keywords.authors)} ({ref.extracted_keywords.year || 'N/A'})
                      </div>
                    </div>

                    {/* PubMed Match */}
                    <div className="col-span-4">
                      <div className="text-xs text-gray-500 mb-1">PubMed Match</div>
                      {hasMatch ? (
                        <>
                          <div className="inline-block bg-green-100 text-green-800 text-xs font-semibold px-2 py-1 rounded mb-1">
                            {matchScore}%
                          </div>
                          <div className="font-medium text-sm text-gray-800">
                            {getShortTitle(bestMatch.title)}
                          </div>
                          <div className="text-xs text-gray-600 mt-1">
                            {getAuthorsStr(bestMatch.authors)} ({bestMatch.year || 'N/A'})
                          </div>
                        </>
                      ) : (
                        <div className="text-sm text-red-600 font-medium">
                          No Match found in PubMed
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="col-span-4 flex justify-end items-center gap-2">
                      {hasMatch && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onReplace(ref.id, bestMatch);
                          }}
                          className="w-10 h-10 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center justify-center"
                          title="替换"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          toggleExpand(ref.id);
                        }}
                        className="w-10 h-10 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors flex items-center justify-center"
                        title={isExpanded ? "收起" : "展开"}
                      >
                        <svg 
                          className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-180' : ''}`} 
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>

                {/* 展开状态：显示详细对比 */}
                {isExpanded && (
                  <div className="p-4 bg-white border-t border-gray-200">
                    <div className="grid grid-cols-2 gap-6">
                      {/* 左侧：Extracted Reference 详细信息 */}
                      <div>
                        <h4 className="font-semibold text-gray-700 mb-3 text-sm">Extracted Reference</h4>
                        {renderKeywords(ref.extracted_keywords, {}, true)}
                      </div>

                      {/* 右侧：PubMed Match 详细信息 */}
                      <div>
                        {hasMatch ? (
                          <>
                            <div className="flex items-center gap-2 mb-3">
                              <h4 className="font-semibold text-gray-700 text-sm">PubMed Match</h4>
                              <span className="bg-green-100 text-green-800 text-xs font-semibold px-2 py-1 rounded">
                                {matchScore}%
                              </span>
                            </div>
                            {renderKeywords(bestMatch.keywords, bestMatch.differences, false)}
                            <div className="mt-4">
                              <button
                                onClick={() => onReplace(ref.id, bestMatch)}
                                className="w-full px-4 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition-colors"
                              >
                                替换
                              </button>
                            </div>
                          </>
                        ) : (
                          <div className="text-sm text-red-600 font-medium">
                            No Match found in PubMed
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};

