import React, { useState, useEffect } from 'react';
import { ProcessedReference } from '../types';

interface ResultAreaProps {
  references: ProcessedReference[];
  detectedFormat?: string;
}

export const ResultArea: React.FC<ResultAreaProps> = ({ references, detectedFormat = 'original' }) => {
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
      const formatted = references.map((ref) => ref.text).join('\n');
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
      const formatted = references.map((ref) => ref.text).join('\n');
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
      const formatted = references.map((ref) => ref.text).join('\n');
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
          const formatted = references.map((ref) => ref.text).join('\n');
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

  return (
    <div 
      className="bg-white rounded-lg shadow-lg p-6 flex flex-col h-full overflow-hidden relative"
    >
      <div className="flex justify-between items-center mb-4 flex-shrink-0">
        <div className="flex items-center gap-3">
          <h3 className="text-lg font-semibold text-gray-800">校验结果</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-700">切换文献格式：</span>
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
        </div>
      </div>
      {isFormatting && (
        <div className="mb-2 text-sm text-blue-600 flex-shrink-0">正在转换格式...</div>
      )}
      <div className="flex-1 flex flex-col min-h-0">
        <textarea
          value={text}
          readOnly
          placeholder="最终处理后的参考文献列表将显示在这里（只读，可通过格式下拉菜单转换格式）..."
          className="w-full flex-1 p-3 border-0 rounded-md bg-gray-50 resize-none font-mono text-sm overflow-y-auto cursor-default focus:outline-none"
        />
        {/* 复制按钮在textarea下方 */}
        <div className="flex justify-end mt-2">
          <button
            onClick={handleCopy}
            disabled={!text}
            className="px-4 py-2 bg-gray-600 text-white text-sm rounded-lg hover:bg-gray-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors shadow-md"
          >
            复制
          </button>
        </div>
      </div>
    </div>
  );
};

