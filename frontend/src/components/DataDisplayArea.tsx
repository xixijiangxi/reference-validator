import React, { useState } from 'react';
import { ReferenceItem, PubMedArticle, ReferenceKeyword } from '../types';
import { referenceAPI } from '../services/api';

interface DataDisplayAreaProps {
  references: ReferenceItem[];
  onReplace: (refId: string, article: PubMedArticle) => void;
  onUpdate?: (refId: string, updatedRef: ReferenceItem) => void;
  isLoading?: boolean;
  progressStatus?: string;
  useSmartMatching?: boolean;
}

export const DataDisplayArea: React.FC<DataDisplayAreaProps> = ({
  references,
  onReplace,
  onUpdate,
  isLoading = false,
  progressStatus = '',
  useSmartMatching = false,
}) => {
  const [expandedRefs, setExpandedRefs] = useState<Set<string>>(new Set());
  const [editingRefId, setEditingRefId] = useState<string | null>(null);
  const [editingData, setEditingData] = useState<ReferenceKeyword | null>(null);
  const [verifyingRefId, setVerifyingRefId] = useState<string | null>(null);
  const [verifyProgress, setVerifyProgress] = useState<string>('');
  const [selectedArticleIndex, setSelectedArticleIndex] = useState<Record<string, number>>({}); // 记录每条参考文献选中的文章索引
  
  const toggleExpand = (refId: string) => {
    // 如果正在编辑该条，不关闭展开状态
    if (editingRefId === refId) return;
    
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
      { key: 'pmid', label: 'PMID' },
      { key: 'doi', label: 'DOI' },
    ];

    return (
      <div className="space-y-2 text-sm">
        {fields.map((field) => {
          const value = keywords[field.key];
          const diff = differences[field.key];
          const hasDiff = diff && diff.type === 'different';

          // 对于原文献，显示所有有值的字段；对于匹配文献，也显示所有字段（即使值为空，如果有差异也显示）
          if (isExtracted) {
            // 原文献：只显示有值的字段
            if (!value) return null;
          } else {
            // 匹配文献：显示所有字段（包括有差异的）
            if (!value && !hasDiff) return null;
          }

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
                    {Array.isArray(value) ? value.join(', ') : (value !== null && value !== undefined ? String(value) : '')}
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

  // 进入编辑模式
  const enterEditMode = (refId: string) => {
    const ref = references.find(r => r.id === refId);
    if (ref) {
      setEditingRefId(refId);
      setEditingData({ ...ref.extracted_keywords });
      // 确保展开状态
      if (!expandedRefs.has(refId)) {
        setExpandedRefs(new Set([...expandedRefs, refId]));
      }
    }
  };

  // 取消编辑
  const cancelEdit = () => {
    setEditingRefId(null);
    setEditingData(null);
    setVerifyingRefId(null);
    setVerifyProgress('');
  };

  // 更新编辑数据
  const updateEditingField = (field: string, value: any) => {
    if (!editingData) return;
    setEditingData({ ...editingData, [field]: value });
  };

  // 删除字段
  const deleteField = (field: string) => {
    if (!editingData) return;
    const newData = { ...editingData };
    delete newData[field as keyof ReferenceKeyword];
    setEditingData(newData);
  };

  // 重新验证
  const handleReverify = async (refId: string) => {
    if (!editingData || !onUpdate) return;
    
    setVerifyingRefId(refId);
    setVerifyProgress('正在检索...');
    
    try {
      setVerifyProgress('正在检索PubMed数据库...');
      const result = await referenceAPI.searchReference(
        refId,
        editingData,
        useSmartMatching
      );
      
      setVerifyProgress('检索完成，正在更新结果...');
      
      const ref = references.find(r => r.id === refId);
      if (ref) {
        const updatedRef: ReferenceItem = {
          ...ref,
          extracted_keywords: editingData,
          matched_articles: result.matched_articles,
          status: result.status as any,
        };
        onUpdate(refId, updatedRef);
      }
      
      // 延迟一下再关闭编辑模式，让用户看到结果
      setTimeout(() => {
        setEditingRefId(null);
        setEditingData(null);
        setVerifyingRefId(null);
        setVerifyProgress('');
      }, 500);
    } catch (error) {
      console.error('重新验证失败:', error);
      setVerifyProgress('验证失败，请重试');
      // 错误时不清除验证状态，让用户看到错误信息
      setTimeout(() => {
        setVerifyingRefId(null);
        setVerifyProgress('');
      }, 2000);
    }
  };

  // 渲染编辑模式的字段
  const renderEditFields = (keywords: ReferenceKeyword) => {
    const standardFields = [
      { key: 'title', label: '标题', type: 'text' },
      { key: 'authors', label: '作者', type: 'authors' },
      { key: 'journal', label: '期刊', type: 'text' },
      { key: 'year', label: '年份', type: 'number' },
      { key: 'volume', label: '卷', type: 'text' },
      { key: 'issue', label: '期', type: 'text' },
      { key: 'pages', label: '页码', type: 'text' },
      { key: 'pmid', label: 'PMID', type: 'text' },
      { key: 'doi', label: 'DOI', type: 'text' },
    ];

    return (
      <div className="space-y-3">
        {standardFields.map((field) => {
          const value = keywords[field.key as keyof ReferenceKeyword];

          return (
            <div key={field.key} className="flex items-center gap-2">
              <label className="font-semibold text-gray-600 w-24 flex-shrink-0 text-sm">
                {field.label}:
              </label>
              <div className="flex-1 flex items-center gap-2">
                {field.type === 'authors' ? (
                  <input
                    type="text"
                    value={Array.isArray(value) ? value.join(', ') : (value as string || '')}
                    onChange={(e) => {
                      const authors = e.target.value.split(',').map(a => a.trim()).filter(a => a);
                      updateEditingField(field.key, authors.length > 0 ? authors : undefined);
                    }}
                    className="flex-1 px-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="多个作者用逗号分隔"
                  />
                ) : field.type === 'number' ? (
                  <input
                    type="number"
                    value={value as number || ''}
                    onChange={(e) => {
                      const numValue = e.target.value ? parseInt(e.target.value) : undefined;
                      updateEditingField(field.key, numValue);
                    }}
                    className="flex-1 px-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="-"
                  />
                ) : (
                  <input
                    type="text"
                    value={value as string || ''}
                    onChange={(e) => {
                      const newValue = e.target.value.trim();
                      updateEditingField(field.key, newValue || undefined);
                    }}
                    className="flex-1 px-3 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                    placeholder="-"
                  />
                )}
                <button
                  onClick={() => deleteField(field.key)}
                  className="w-8 h-8 flex items-center justify-center text-gray-400 hover:text-red-600 transition-colors"
                  title="删除字段"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 h-full flex flex-col overflow-hidden">
      <div className="flex justify-between items-center mb-6 flex-shrink-0">
        <h2 className="text-xl font-bold text-gray-800">验证结果</h2>
        {references.length > 0 && (
          <span className="text-sm text-gray-500">
            已验证{references.length}条参考文献
          </span>
        )}
      </div>
      <div className="space-y-4 flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600 mb-4"></div>
            <div className="text-gray-600 text-lg font-medium">处理中...</div>
            {progressStatus && (
              <div className="text-purple-600 text-sm mt-2 font-medium">{progressStatus}</div>
            )}
            {!progressStatus && (
              <div className="text-gray-500 text-sm mt-2">正在检索和匹配参考文献，请稍候</div>
            )}
          </div>
        ) : references.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            暂无数据，请在左侧输入参考文献
          </div>
        ) : (
          references.map((ref) => {
            const isExpanded = expandedRefs.has(ref.id);
            const hasMatch = ref.status === 'matched' && ref.matched_articles.length > 0;
            // 获取当前选中的文章索引，默认为0
            const currentIndex = selectedArticleIndex[ref.id] ?? 0;
            const selectedMatch = hasMatch ? ref.matched_articles[currentIndex] : null;
            const allMatches = ref.matched_articles;

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
                      <div className="text-xs text-gray-500 mb-1">
                        匹配文献 {hasMatch && allMatches.length > 1 ? `(${currentIndex + 1}/${allMatches.length})` : ''}
                      </div>
                      {hasMatch && selectedMatch ? (
                        <>
                          <div className="font-medium text-sm text-gray-800 flex items-center gap-2">
                            <span>{getShortTitle(selectedMatch.title)}</span>
                            {selectedMatch.pmid && (
                              <a
                                href={`https://pubmed.ncbi.nlm.nih.gov/${selectedMatch.pmid}/`}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                className="text-blue-600 hover:text-blue-800 transition-colors"
                                title="在PubMed中查看"
                              >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                </svg>
                              </a>
                            )}
                            {selectedMatch.match_type && (
                              <span className="ml-2 px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                                {selectedMatch.match_type === 'doi_match' ? 'DOI匹配' : selectedMatch.match_type === 'pmid_match' ? 'PMID匹配' : selectedMatch.match_type}
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-gray-600 mt-1">
                            {getAuthorsStr(selectedMatch.authors)} ({selectedMatch.year || 'N/A'})
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
                      {hasMatch && selectedMatch && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            onReplace(ref.id, selectedMatch);
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

                {/* 展开状态：显示详细对比或编辑模式 */}
                {isExpanded && (
                  <div className="p-4 bg-white border-t border-gray-200">
                    {editingRefId === ref.id ? (
                      /* 编辑模式 */
                      <div>
                        <div className="mb-4">
                          <h4 className="font-semibold text-gray-700 mb-2 text-sm">原文献</h4>
                          {/* 显示摘要信息 */}
                          <div className="text-sm text-gray-600 mb-4 p-2 bg-yellow-50 rounded">
                            <span className="font-medium">{getShortTitle(editingData?.title)}</span>
                            {' '}
                            <span>{getAuthorsStr(editingData?.authors)} ({editingData?.year || 'N/A'})</span>
                          </div>
                        </div>
                        
                        {/* 编辑字段 */}
                        {editingData && renderEditFields(editingData)}
                        
                        {/* 验证进度显示 */}
                        {verifyingRefId === ref.id && (
                          <div className="mt-4 p-3 bg-blue-50 rounded-lg flex items-center gap-2">
                            <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-purple-600"></div>
                            <span className="text-sm text-purple-600">{verifyProgress || '正在验证...'}</span>
                          </div>
                        )}
                        
                        {/* 操作按钮 */}
                        <div className="mt-6 flex justify-end gap-3">
                          <button
                            onClick={cancelEdit}
                            disabled={verifyingRefId === ref.id}
                            className="px-4 py-2 bg-gray-200 text-gray-700 text-sm rounded-lg hover:bg-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            取消
                          </button>
                          <button
                            onClick={() => handleReverify(ref.id)}
                            disabled={verifyingRefId === ref.id}
                            className="px-4 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                          >
                            {verifyingRefId === ref.id ? (
                              <>
                                <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                验证中...
                              </>
                            ) : (
                              <>
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                                重新验证
                              </>
                            )}
                          </button>
                        </div>
                      </div>
                    ) : (
                      /* 只读模式：显示详细对比 */
                      <div className="grid grid-cols-2 gap-6">
                        {/* 左侧：原文献 详细信息 */}
                        <div>
                          <div className="flex items-center justify-between mb-3">
                            <h4 className="font-semibold text-gray-700 text-sm">原文献</h4>
                            <button
                              onClick={() => enterEditMode(ref.id)}
                              className="text-xs text-purple-600 hover:text-purple-700 flex items-center gap-1"
                              title="编辑"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                              编辑
                            </button>
                          </div>
                          {renderKeywords(ref.extracted_keywords, {}, true)}
                        </div>

                        {/* 右侧：匹配文献 详细信息 */}
                        <div>
                          {hasMatch && allMatches.length > 0 ? (
                            <>
                              <div className="mb-3 flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <h4 className="font-semibold text-gray-700 text-sm">匹配文献</h4>
                                  {selectedMatch?.pmid && (
                                    <a
                                      href={`https://pubmed.ncbi.nlm.nih.gov/${selectedMatch.pmid}/`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-blue-600 hover:text-blue-800 transition-colors"
                                      title="在PubMed中查看"
                                    >
                                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                      </svg>
                                    </a>
                                  )}
                                </div>
                                {allMatches.length > 1 && (
                                  <div className="flex items-center gap-2">
                                    <button
                                      onClick={() => {
                                        const newIndex = currentIndex > 0 ? currentIndex - 1 : allMatches.length - 1;
                                        setSelectedArticleIndex({ ...selectedArticleIndex, [ref.id]: newIndex });
                                      }}
                                      className="w-8 h-8 flex items-center justify-center bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                                      title="上一个"
                                    >
                                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                                      </svg>
                                    </button>
                                    <span className="text-xs text-gray-600">
                                      {currentIndex + 1} / {allMatches.length}
                                    </span>
                                    <button
                                      onClick={() => {
                                        const newIndex = currentIndex < allMatches.length - 1 ? currentIndex + 1 : 0;
                                        setSelectedArticleIndex({ ...selectedArticleIndex, [ref.id]: newIndex });
                                      }}
                                      className="w-8 h-8 flex items-center justify-center bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                                      title="下一个"
                                    >
                                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                      </svg>
                                    </button>
                                  </div>
                                )}
                              </div>
                              
                              {/* 如果有多个匹配，显示所有匹配的列表 */}
                              {allMatches.length > 1 && (
                                <div className="mb-3 p-2 bg-gray-50 rounded-lg max-h-32 overflow-y-auto">
                                  {allMatches.map((article, idx) => (
                                    <div
                                      key={idx}
                                      onClick={() => setSelectedArticleIndex({ ...selectedArticleIndex, [ref.id]: idx })}
                                      className={`p-2 mb-1 rounded cursor-pointer transition-colors ${
                                        idx === currentIndex
                                          ? 'bg-purple-100 border-2 border-purple-500'
                                          : 'bg-white border border-gray-200 hover:bg-gray-100'
                                      }`}
                                    >
                                      <div className="flex items-center justify-between">
                                        <div className="flex-1">
                                          <div className="text-xs font-medium text-gray-800 flex items-center gap-1">
                                            <span>{getShortTitle(article.title, 40)}</span>
                                            {article.pmid && (
                                              <a
                                                href={`https://pubmed.ncbi.nlm.nih.gov/${article.pmid}/`}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                onClick={(e) => e.stopPropagation()}
                                                className="text-blue-600 hover:text-blue-800 transition-colors"
                                                title="在PubMed中查看"
                                              >
                                                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                                </svg>
                                              </a>
                                            )}
                                          </div>
                                          <div className="text-xs text-gray-600">
                                            {getAuthorsStr(article.authors)} ({article.year || 'N/A'})
                                          </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                          {article.match_type && (
                                            <span className="px-1.5 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                                              {article.match_type === 'doi_match' ? 'DOI' : article.match_type === 'pmid_match' ? 'PMID' : article.match_type}
                                            </span>
                                          )}
                                          <span className="text-xs text-gray-500">
                                            相似度: {(article.similarity_score * 100).toFixed(1)}%
                                          </span>
                                        </div>
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              )}
                              
                              {/* 使用 selectedMatch 对象的所有字段，构建完整的 keywords 对象 */}
                              {selectedMatch && (
                                <>
                                  {selectedMatch.match_type && (
                                    <div className="mb-2 p-2 bg-blue-50 rounded-lg">
                                      <span className="text-xs font-medium text-blue-700">
                                        {selectedMatch.match_type === 'doi_match' ? '✓ DOI匹配' : selectedMatch.match_type === 'pmid_match' ? '✓ PMID匹配' : `✓ ${selectedMatch.match_type}`}
                                      </span>
                                      <span className="text-xs text-gray-600 ml-2">
                                        相似度: {(selectedMatch.similarity_score * 100).toFixed(1)}%
                                      </span>
                                    </div>
                                  )}
                                  {renderKeywords({
                                    title: selectedMatch.title,
                                    authors: selectedMatch.authors,
                                    journal: selectedMatch.journal,
                                    year: selectedMatch.year,
                                    volume: selectedMatch.volume,
                                    issue: selectedMatch.issue,
                                    pages: selectedMatch.pages,
                                    pmid: selectedMatch.pmid,
                                    doi: selectedMatch.doi,
                                  }, selectedMatch.differences, false)}
                                  <div className="mt-4">
                                    <button
                                      onClick={() => onReplace(ref.id, selectedMatch)}
                                      className="w-full px-4 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 transition-colors"
                                    >
                                      替换
                                    </button>
                                  </div>
                                </>
                              )}
                            </>
                          ) : (
                            <div className="text-sm text-red-600 font-medium">
                              No Match found in PubMed
                            </div>
                          )}
                        </div>
                      </div>
                    )}
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

