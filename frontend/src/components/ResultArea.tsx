import React, { useState, useEffect, useRef } from 'react';
import { ProcessedReference } from '../types';

interface ResultAreaProps {
  references: ProcessedReference[];
  onUpdate: (references: ProcessedReference[]) => void;
  detectedFormat?: string;
}

const formatLabels: Record<string, string> = {
  'original': '原始格式',
  'apa': 'APA',
  'mla': 'MLA',
  'ama': 'AMA',
  'nlm': 'NLM',
  'gb2015': '国标2015',
  'numeric': '顺序编码制',
  'author_year': '著者出版年制',
};

export const ResultArea: React.FC<ResultAreaProps> = ({ references, onUpdate, detectedFormat = 'original' }) => {
  const [text, setText] = useState('');
  const [selectedFormat, setSelectedFormat] = useState('original');
  const [isFormatting, setIsFormatting] = useState(false);
  const resultAreaRef = useRef<HTMLDivElement>(null);
  const [isSticky, setIsSticky] = useState(false);
  const [topOffset, setTopOffset] = useState(0);

  // 处理悬浮效果 - 保持在页面中间
  useEffect(() => {
    let rafId: number;
    
    const handleScroll = () => {
      if (!resultAreaRef.current) return;
      
      rafId = requestAnimationFrame(() => {
        if (!resultAreaRef.current) return;
        
        const viewportHeight = window.innerHeight;
        const scrollY = window.scrollY;
        const element = resultAreaRef.current;
        const elementHeight = element.offsetHeight;
        
        // 获取父容器的位置信息
        const parent = element.parentElement;
        if (!parent) return;
        
        const parentRect = parent.getBoundingClientRect();
        const parentTop = parentRect.top + scrollY;
        const parentBottom = parentTop + parentRect.height;
        
        // 计算应该保持的位置（视口中间）
        const targetTop = (viewportHeight - elementHeight) / 2;
        
        // 当滚动到一定位置时，开始悬浮
        const shouldSticky = scrollY > parentTop + 200 && scrollY < parentBottom - elementHeight - 200;
        
        if (shouldSticky) {
          setIsSticky(true);
          setTopOffset(Math.max(20, targetTop)); // 至少距离顶部20px
        } else {
          setIsSticky(false);
        }
      });
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    window.addEventListener('resize', handleScroll, { passive: true });
    handleScroll(); // 初始调用

    return () => {
      cancelAnimationFrame(rafId);
      window.removeEventListener('scroll', handleScroll);
      window.removeEventListener('resize', handleScroll);
    };
  }, []);

  // 格式切换处理
  const handleFormatChange = async (newFormat: string) => {
    setSelectedFormat(newFormat);
    
    if (references.length === 0) {
      setText('');
      return;
    }

    if (newFormat === 'original') {
      // 原始格式：直接使用本地格式化
      const formatted = references.map((ref, idx) => `${idx + 1}. ${ref.text}`).join('\n');
      setText(formatted);
      return;
    }

    // 其他格式：调用后端API
    setIsFormatting(true);
    try {
      const response = await fetch('/api/format', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          references: references,
          target_format: newFormat
        }),
      });

      if (!response.ok) {
        throw new Error('格式化失败');
      }

      const data = await response.json();
      setText(data.formatted_text);
    } catch (error) {
      console.error('Error:', error);
      alert('格式转换失败，请重试');
      // 失败时回退到原始格式
      const formatted = references.map((ref, idx) => `${idx + 1}. ${ref.text}`).join('\n');
      setText(formatted);
      setSelectedFormat('original');
    } finally {
      setIsFormatting(false);
    }
  };

  // 当references变化时，更新文本（使用当前选中的格式）
  useEffect(() => {
    if (references.length === 0) {
      setText('');
      return;
    }

    // 如果选中的是原始格式，直接使用本地格式化
    if (selectedFormat === 'original') {
      const formatted = references.map((ref, idx) => `${idx + 1}. ${ref.text}`).join('\n');
      setText(formatted);
    } else {
      // 其他格式需要调用后端API
      const formatAsync = async () => {
        setIsFormatting(true);
        try {
          const response = await fetch('/api/format', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              references: references,
              target_format: selectedFormat
            }),
          });

          if (!response.ok) {
            throw new Error('格式化失败');
          }

          const data = await response.json();
          setText(data.formatted_text);
        } catch (error) {
          console.error('Error:', error);
          // 失败时回退到原始格式
          const formatted = references.map((ref, idx) => `${idx + 1}. ${ref.text}`).join('\n');
          setText(formatted);
        } finally {
          setIsFormatting(false);
        }
      };
      formatAsync();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [references]);

  // 当检测到格式变化时，更新选中格式
  useEffect(() => {
    if (detectedFormat && detectedFormat !== 'original') {
      setSelectedFormat(detectedFormat);
    }
  }, [detectedFormat]);

  const handleCopy = () => {
    navigator.clipboard.writeText(text);
    alert('已复制到剪贴板');
  };

  const handleExport = async () => {
    handleCopy();
  };

  const handleTextChange = (newText: string) => {
    setText(newText);
    // 可以在这里实现文本解析，更新references
  };

  return (
    <div 
      ref={resultAreaRef}
      className={`bg-white rounded-lg shadow-lg p-6 flex flex-col transition-all duration-300 ${
        isSticky ? 'fixed z-50' : 'relative'
      }`}
      style={isSticky ? (() => {
        const rect = resultAreaRef.current?.getBoundingClientRect();
        return {
          top: `${topOffset}px`, 
          left: rect ? rect.left + 'px' : 'auto',
          width: resultAreaRef.current?.offsetWidth + 'px',
          maxHeight: '80vh'
        };
      })() : {}}
    >
      <div className="flex justify-between items-center mb-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold text-gray-800">Final Output</h2>
          <span className="text-sm text-gray-500">
            {references.length} references ready
          </span>
        </div>
        <div className="flex gap-2">
          <select
            value={selectedFormat}
            onChange={(e) => handleFormatChange(e.target.value)}
            disabled={isFormatting || references.length === 0}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-100 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-purple-500"
          >
            <option value="original">原始格式</option>
            <option value="apa">APA</option>
            <option value="mla">MLA</option>
            <option value="ama">AMA</option>
            <option value="nlm">NLM</option>
            <option value="gb2015">国标2015</option>
            <option value="numeric">顺序编码制</option>
            <option value="author_year">著者出版年制</option>
          </select>
          <button
            onClick={handleCopy}
            disabled={!text}
            className="px-4 py-2 bg-gray-600 text-white text-sm rounded-lg hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            Copy
          </button>
          <button
            onClick={handleExport}
            disabled={!text}
            className="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed transition-colors"
          >
            Export
          </button>
        </div>
      </div>
      {isFormatting && (
        <div className="mb-2 text-sm text-blue-600 flex-shrink-0">正在转换格式...</div>
      )}
      <textarea
        value={text}
        onChange={(e) => handleTextChange(e.target.value)}
        placeholder="最终处理后的参考文献列表将显示在这里..."
        className="w-full flex-1 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 resize-none font-mono text-sm"
        style={isSticky ? { maxHeight: 'calc(80vh - 200px)' } : {}}
      />
    </div>
  );
};

