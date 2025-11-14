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

  // 处理输入的参考文献
  const handleProcess = async (refs: ReferenceItem[]) => {
    console.log('='.repeat(80));
    console.log(`【前端 App】开始处理 ${refs.length} 条参考文献`);
    
    setLoading(true);
    setReferences(refs);

    // 为每条参考文献搜索匹配的文章
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
    
    setLoading(false);
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
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-800">医学科研参考文献校验工具</h1>
        </div>
      </header>

      <main className="max-w-[1800px] mx-auto px-4 py-6">
        <div className="grid grid-cols-12 gap-6 h-[calc(100vh-120px)]">
          {/* 左侧：输入区和结果区 */}
          <div className="col-span-12 lg:col-span-5 flex flex-col gap-6">
            <div className="flex-shrink-0">
              <InputArea onProcess={handleProcess} loading={loading} />
            </div>
            <div className="flex-1 min-h-0">
              <ResultArea
                references={processedReferences}
                onUpdate={handleUpdateResults}
                detectedFormat={detectedFormat}
              />
            </div>
          </div>

          {/* 右侧：数据展示区 */}
          <div className="col-span-12 lg:col-span-7 min-h-0">
            <DataDisplayArea
              references={references}
              onReplace={handleReplace}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

