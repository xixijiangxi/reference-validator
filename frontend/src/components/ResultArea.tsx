import React, { useState, useEffect } from 'react';
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
    <div className="bg-white rounded-lg shadow-md p-6 h-full flex flex-col">
      <div className="flex justify-between items-center mb-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-bold text-gray-800">最终结果区</h2>
          {detectedFormat && detectedFormat !== 'original' && (
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
              检测到格式: {formatLabels[detectedFormat] || detectedFormat}
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <select
            value={selectedFormat}
            onChange={(e) => handleFormatChange(e.target.value)}
            disabled={isFormatting || references.length === 0}
            className="px-3 py-1 border border-gray-300 rounded text-sm disabled:bg-gray-100 disabled:cursor-not-allowed"
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
            className="px-4 py-1 bg-gray-600 text-white text-sm rounded hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            复制
          </button>
          <button
            onClick={handleExport}
            disabled={!text}
            className="px-4 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:bg-green-400 disabled:cursor-not-allowed"
          >
            导出
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
      />
      <div className="mt-2 text-sm text-gray-500 flex-shrink-0">
        共 {references.length} 条参考文献
      </div>
    </div>
  );
};

