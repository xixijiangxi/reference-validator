import React, { useState } from 'react';
import { InputArea } from './components/InputArea';
import { DataDisplayArea } from './components/DataDisplayArea';
import { ResultArea } from './components/ResultArea';
import { ReferenceItem, PubMedArticle, ProcessedReference, ReferenceKeyword } from './types';
import { referenceAPI } from './services/api';

function App() {
  const [references, setReferences] = useState<ReferenceItem[]>([]);
  const [processedReferences, setProcessedReferences] = useState<ProcessedReference[]>([]);
  const [loading, setLoading] = useState(false);
  const [detectedFormat, setDetectedFormat] = useState<string>('');
  const [hasProcessed, setHasProcessed] = useState(false); // 是否已处理过
  const [progressStatus, setProgressStatus] = useState<string>(''); // 进度状态
  const [isDataAreaCollapsed, setIsDataAreaCollapsed] = useState(false); // 右侧区域是否收缩
  const [inputAreaHeight, setInputAreaHeight] = useState<number>(80); // 输入区高度（像素），默认80px

  // 处理输入的参考文献
  const handleProcess = async (refs: ReferenceItem[]) => {
    console.log('='.repeat(80));
    console.log(`【前端 App】开始处理 ${refs.length} 条参考文献`);
    
    setLoading(true);
    setReferences(refs);

    // 关键词提取状态（拆分已在InputArea中显示）
    setProgressStatus('关键词提取...');
    await new Promise(resolve => setTimeout(resolve, 500));

    // 为每条参考文献搜索匹配的文章
    setProgressStatus('PubMed检索与匹配...');
    const updatedRefs = await Promise.all(
      refs.map(async (ref, idx) => {
        console.log(`\n【前端 App】处理第 ${idx + 1}/${refs.length} 条: ${ref.id}`);
        console.log(`  原始文本: ${ref.original_text.substring(0, 80)}...`);
        console.log(`  提取的关键词:`, ref.extracted_keywords);
        
        try {
          console.log(`  发送检索请求: POST /api/search/${ref.id}`);
          const result = await referenceAPI.searchReference(
            ref.id,
            ref.extracted_keywords
          );
          
          console.log(`  检索结果: status=${result.status}, 匹配文章数=${result.matched_articles.length}`);
          result.matched_articles.forEach((article: any, artIdx: number) => {
            console.log(`    [${artIdx + 1}] PMID=${article.pmid}, 相似度=${article.similarity_score}, 标题=${article.title?.substring(0, 50)}...`);
          });
          
          return {
            ...ref,
            matched_articles: result.matched_articles,
            status: result.status as any,
          };
        } catch (error) {
          console.error(`【前端 App】搜索 ${ref.id} 失败:`, error);
          return {
            ...ref,
            matched_articles: [],
            status: 'not_found' as any,
          };
        }
      })
    );

    console.log(`\n【前端 App】所有参考文献处理完成`);
    setReferences(updatedRefs);
    
    // 初始化处理后的参考文献，使用原始文本
    // 检测主要格式（取第一条的格式，或最常见的格式）
    const formatCounts: Record<string, number> = {};
    updatedRefs.forEach(ref => {
      const format = ref.format_type || 'original';
      formatCounts[format] = (formatCounts[format] || 0) + 1;
    });
    const mostCommonFormat = Object.keys(formatCounts).reduce((a, b) => 
      formatCounts[a] > formatCounts[b] ? a : b, 'original'
    );
    setDetectedFormat(mostCommonFormat);
    
    // 按顺序初始化processedReferences
    const initialProcessed: ProcessedReference[] = updatedRefs.map(ref => ({
      id: ref.id,
      text: ref.original_text,
      data: ref.extracted_keywords,
      format_type: ref.format_type || 'original',
    }));
    setProcessedReferences(initialProcessed);
    setHasProcessed(true); // 标记已处理
    
    setLoading(false);
    setProgressStatus(''); // 清除进度状态
  };

  // 替换参考文献（使用完整关键词，不含PMID）
  const handleReplace = (refId: string, article: PubMedArticle) => {
    const ref = references.find((r) => r.id === refId);
    if (!ref) return;

    // 使用完整的关键词格式化，但不包含PMID
    const keywords = { ...article.keywords };
    delete keywords.pmid; // 移除PMID
    
    const replacedText = formatReference(keywords, ref.format_type || 'original');
    const processed: ProcessedReference = {
      id: refId,
      text: replacedText,
      data: keywords,
      format_type: ref.format_type,
    };

    updateProcessedReference(refId, processed);
  };

  // 更新处理后的参考文献
  const updateProcessedReference = (refId: string, processed: ProcessedReference) => {
    const existing = processedReferences.findIndex((r) => r.id === refId);
    if (existing >= 0) {
      const updated = [...processedReferences];
      updated[existing] = processed;
      setProcessedReferences(updated);
    } else {
      setProcessedReferences([...processedReferences, processed]);
    }
  };

  // 格式化参考文献文本（使用关键词对象，不含PMID）
  const formatReference = (keywords: ReferenceKeyword, formatType: string): string => {
    const { title, authors, journal, year, volume, issue, pages, doi } = keywords;

    // 简单的格式化逻辑，可以根据formatType扩展
    const authorStr = authors && authors.length > 0 ? authors.join(', ') : '';
    const yearStr = year ? `(${year})` : '';
    const journalStr = journal || '';
    const volumeStr = volume || '';
    const issueStr = issue ? `(${issue})` : '';
    const pagesStr = pages ? `: ${pages}` : '';
    const doiStr = doi ? ` DOI: ${doi}` : '';

    // 基本格式：作者(年份). 标题. 期刊, 卷(期): 页码
    return `${authorStr} ${yearStr}. ${title || ''}. ${journalStr}, ${volumeStr}${issueStr}${pagesStr}${doiStr}`.trim();
  };

  // 更新最终结果
  const handleUpdateResults = (updated: ProcessedReference[]) => {
    setProcessedReferences(updated);
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-[1800px] mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">Research Reference Assistant</h1>
          {/* 隐藏右上角功能键 */}
        </div>
      </header>

      <main className="max-w-[1800px] mx-auto px-4 py-6 h-[calc(100vh-80px)] flex flex-col">
        {!hasProcessed ? (
          // 初始状态：只显示输入区
          <div className="max-w-4xl mx-auto w-full">
            <InputArea 
              onProcess={handleProcess} 
              loading={loading} 
              progressStatus={progressStatus}
              isCompact={false}
              onProgressChange={setProgressStatus}
            />
          </div>
        ) : (
          // 处理后的状态：显示三区域布局
          <div className="flex-1 flex gap-6 overflow-hidden">
            {/* 左侧：输入区和结果区 - 可拖拽调整高度 */}
            <div 
              className={`flex flex-col transition-all duration-300 ${isDataAreaCollapsed ? 'flex-1' : 'w-5/12'} relative`}
              style={{ height: '100%' }}
            >
              {/* 输入区 - 紧凑模式 */}
              <div 
                className="relative overflow-hidden"
                style={{ 
                  height: `${inputAreaHeight}px`, 
                  minHeight: '80px', 
                  maxHeight: 'calc(100% - 200px)',
                  flexShrink: 0
                }}
              >
                <div className="h-full">
                  <InputArea 
                    onProcess={handleProcess} 
                    loading={loading} 
                    progressStatus={progressStatus}
                    isCompact={true}
                    onProgressChange={setProgressStatus}
                  />
                </div>
              </div>
              {/* 拖拽条 */}
              <div
                className="h-2 bg-gray-200 hover:bg-purple-400 cursor-row-resize transition-colors z-20 flex items-center justify-center group flex-shrink-0"
                onMouseDown={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  const startY = e.clientY;
                  const startHeight = inputAreaHeight;
                  
                  const handleMouseMove = (moveEvent: MouseEvent) => {
                    const deltaY = moveEvent.clientY - startY;
                    const newHeight = Math.max(100, Math.min(window.innerHeight - 300, startHeight + deltaY));
                    setInputAreaHeight(newHeight);
                  };
                  
                  const handleMouseUp = () => {
                    document.removeEventListener('mousemove', handleMouseMove);
                    document.removeEventListener('mouseup', handleMouseUp);
                    document.body.style.cursor = '';
                    document.body.style.userSelect = '';
                  };
                  
                  document.body.style.cursor = 'row-resize';
                  document.body.style.userSelect = 'none';
                  document.addEventListener('mousemove', handleMouseMove);
                  document.addEventListener('mouseup', handleMouseUp);
                }}
              >
                <div className="w-12 h-0.5 bg-gray-400 group-hover:bg-purple-600 transition-colors"></div>
              </div>
              {/* 结果区 - 占据剩余高度 */}
              <div 
                className="flex-1 min-h-0 overflow-hidden"
                style={{ height: `calc(100% - ${inputAreaHeight + 8}px)` }}
              >
                <ResultArea
                  references={processedReferences}
                  onUpdate={handleUpdateResults}
                  detectedFormat={detectedFormat}
                />
              </div>
            </div>

            {/* 右侧：数据展示区 - 可收缩 */}
            <div className={`relative transition-all duration-300 ${isDataAreaCollapsed ? 'w-8' : 'w-7/12'}`}>
              {isDataAreaCollapsed ? (
                // 收缩状态：显示箭头按钮
                <button
                  onClick={() => setIsDataAreaCollapsed(false)}
                  className="w-full h-full bg-white rounded-lg shadow-md flex items-center justify-center hover:bg-gray-50 transition-colors group"
                  title="展开数据展示区"
                >
                  <svg 
                    className="w-6 h-6 text-gray-400 group-hover:text-purple-600 transition-colors" 
                    fill="none" 
                    stroke="currentColor" 
                    viewBox="0 0 24 24"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
              ) : (
                // 展开状态：显示数据展示区和收缩按钮
                <div className="h-full flex flex-col">
                  <div className="flex-1 min-h-0">
                    <DataDisplayArea
                      references={references}
                      onReplace={handleReplace}
                    />
                  </div>
                  {/* 收缩按钮 */}
                  <button
                    onClick={() => setIsDataAreaCollapsed(true)}
                    className="absolute top-1/2 -left-4 transform -translate-y-1/2 w-8 h-16 bg-white rounded-l-lg shadow-md flex items-center justify-center hover:bg-gray-50 transition-colors group border border-r-0 border-gray-200"
                    title="收缩数据展示区"
                  >
                    <svg 
                      className="w-5 h-5 text-gray-400 group-hover:text-purple-600 transition-colors" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;

