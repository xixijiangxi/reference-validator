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
  // 高亮显示差异字符（词级别）
  const highlightDiff = (original: string, matched: string): JSX.Element => {
    if (!original || !matched) {
      return <span>{matched || original}</span>;
    }
    
    const orig = String(original).toLowerCase();
    const match = String(matched).toLowerCase();
    
    // 如果完全相同，直接返回
    if (orig === match) {
      return <span>{matched}</span>;
    }
    
    // 词级别比较
    const origWords = original.split(/(\s+)/);
    const matchWords = matched.split(/(\s+)/);
    const origWordsLower = origWords.map(w => w.toLowerCase());
    const matchWordsLower = matchWords.map(w => w.toLowerCase());
    
    const result: JSX.Element[] = [];
    let origIdx = 0;
    let matchIdx = 0;
    
    while (matchIdx < matchWords.length) {
      const matchWord = matchWords[matchIdx];
      const matchWordLower = matchWordsLower[matchIdx];
      
      // 跳过空白字符
      if (/^\s+$/.test(matchWord)) {
        result.push(<span key={matchIdx}>{matchWord}</span>);
        matchIdx++;
        continue;
      }
      
      // 查找在原始文本中是否有匹配的词
      let found = false;
      for (let i = origIdx; i < origWordsLower.length; i++) {
        if (origWordsLower[i] === matchWordLower) {
          found = true;
          origIdx = i + 1;
          break;
        }
      }
      
      if (found) {
        // 匹配的词，不高亮
        result.push(<span key={matchIdx}>{matchWord}</span>);
      } else {
        // 不匹配的词，高亮显示
        result.push(
          <span key={matchIdx} className="bg-yellow-200 font-semibold">
            {matchWord}
          </span>
        );
      }
      
      matchIdx++;
    }
    
    return <span>{result}</span>;
  };
  
  // 高亮显示作者差异（词级别）
  const highlightAuthorsDiff = (original: string[], matched: string[]): JSX.Element => {
    if (!original || !matched) {
      return <span>{matched ? matched.join(', ') : original ? original.join(', ') : ''}</span>;
    }
    
    const origLower = original.map(a => a.toLowerCase());
    const matchedLower = matched.map(a => a.toLowerCase());
    
    const result: JSX.Element[] = [];
    
    matched.forEach((author, idx) => {
      const authorLower = author.toLowerCase();
      const found = origLower.some(orig => orig === authorLower);
      
      if (idx > 0) {
        result.push(<span key={`sep-${idx}`}>, </span>);
      }
      
      if (found) {
        result.push(<span key={idx}>{author}</span>);
      } else {
        result.push(
          <span key={idx} className="bg-yellow-200 font-semibold">
            {author}
          </span>
        );
      }
    });
    
    return <span>{result}</span>;
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
                  <span className="text-gray-800">
                    {field.key === 'authors' && Array.isArray(value) && Array.isArray(diff.original) ? (
                      highlightAuthorsDiff(diff.original, value)
                    ) : (
                      highlightDiff(
                        Array.isArray(diff.original) ? diff.original.join(', ') : String(diff.original || ''),
                        Array.isArray(value) ? value.join(', ') : String(value || '')
                      )
                    )}
                  </span>
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
    <div className="bg-white rounded-lg shadow-md p-6 h-full flex flex-col overflow-hidden">
      <h2 className="text-xl font-bold mb-6 text-gray-800 flex-shrink-0">验证结果</h2>
      <div className="space-y-4 flex-1 overflow-y-auto">
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
                    {/* 原文献 */}
                    <div className="col-span-4">
                      <div className="text-xs text-gray-500 mb-1">原文献</div>
                      <div className="font-medium text-sm text-gray-800">
                        {getShortTitle(ref.extracted_keywords.title)}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {getAuthorsStr(ref.extracted_keywords.authors)} ({ref.extracted_keywords.year || 'N/A'})
                      </div>
                    </div>

                    {/* 匹配文献 */}
                    <div className="col-span-4">
                      <div className="text-xs text-gray-500 mb-1">匹配文献</div>
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
                      {/* 左侧：原文献 详细信息 */}
                      <div>
                        <h4 className="font-semibold text-gray-700 mb-3 text-sm">原文献</h4>
                        {renderKeywords(ref.extracted_keywords, {}, true)}
                      </div>

                      {/* 右侧：匹配文献 详细信息 */}
                      <div>
                        {hasMatch ? (
                          <>
                            <div className="flex items-center gap-2 mb-3">
                              <h4 className="font-semibold text-gray-700 text-sm">匹配文献</h4>
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

