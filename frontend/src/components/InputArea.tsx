import React, { useState } from 'react';
import { ReferenceItem } from '../types';

interface InputAreaProps {
  onProcess: (references: ReferenceItem[], useSmartMatching: boolean) => void;
  loading: boolean;
  progressStatus?: string;
  isCompact?: boolean;
  onProgressChange?: (status: string) => void;
  showProgressInCompact?: boolean; // 紧凑模式下是否显示进度
}

export const InputArea: React.FC<InputAreaProps> = ({ onProcess, loading, progressStatus = '', isCompact = false, onProgressChange, showProgressInCompact = false }) => {
  const [text, setText] = useState('');
  // 默认使用智能匹配模式，前端不显示勾选框
  const [useSmartMatching] = useState(true);

  const handleSubmit = async () => {
    console.log('='.repeat(80));
    console.log('【前端】用户点击提交按钮');
    
    if (!text.trim()) {
      console.warn('【前端】输入文本为空');
      alert('请输入参考文献内容');
      return;
    }

    console.log(`【前端】输入文本长度: ${text.length} 字符`);
    console.log(`【前端】输入文本预览: ${text.substring(0, 200)}...`);

    try {
      // 显示拆分状态（立即更新，确保UI能立即显示）
      onProgressChange?.('拆分参考文献...');
      // 使用requestAnimationFrame确保状态立即更新
      await new Promise(resolve => requestAnimationFrame(resolve));
      
      console.log('【前端】发送 POST /api/split 请求');
      const response = await fetch('/api/split', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });

      console.log(`【前端】收到响应: status=${response.status}`);

      if (!response.ok) {
        throw new Error('拆分参考文献失败');
      }

      const data = await response.json();
      console.log(`【前端】拆分成功，收到 ${data.references.length} 条参考文献`);
      data.references.forEach((ref: any, idx: number) => {
        console.log(`  [${idx + 1}] ID=${ref.id}, 格式=${ref.format_type}, 文本=${ref.original_text.substring(0, 60)}...`);
        console.log(`      关键词:`, ref.extracted_keywords);
      });
      
      // 显示拆分完成状态
      onProgressChange?.(`已拆分 ${data.references.length} 条参考文献`);
      await new Promise(resolve => setTimeout(resolve, 100));
      
      // 在调用 onProcess 之前，先更新进度状态为"提取关键词..."
      // 这样当 handleProcess 被调用时，进度状态已经是最新的
      onProgressChange?.('提取关键词...');
      await new Promise(resolve => requestAnimationFrame(resolve));
      
      console.log('【前端】调用 onProcess 回调');
      onProcess(data.references, useSmartMatching);
    } catch (error) {
      console.error('【前端】处理失败:', error);
      alert('处理失败，请重试');
      onProgressChange?.('');
    }
  };

  return (
    <div className={`bg-white rounded-lg shadow-md h-full flex flex-col ${isCompact ? 'p-3' : 'p-6'}`}>
      {isCompact ? (
        // 紧凑模式：可调整高度的输入
        <div className="flex flex-col flex-1 min-h-0">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="输入新的参考文献，开启下一次校验..."
            className="flex-1 w-full p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none text-sm"
            disabled={loading}
            style={{ minHeight: '40px' }}
          />
          {/* 紧凑模式下，如果右侧展示区收缩，在输入框下显示进度 */}
          {showProgressInCompact && progressStatus && (
            <div className="mt-2 flex items-center gap-2 text-xs text-purple-600">
              <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="font-medium">{progressStatus}</span>
            </div>
          )}
          <div className="flex justify-end mt-2">
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium flex items-center gap-2 text-sm"
            >
            {loading ? (
              <>
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>处理中...</span>
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <span>开始校验</span>
              </>
            )}
            </button>
          </div>
        </div>
      ) : (
        // 完整模式：大输入框
        <>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="请输入需要验证的参考文献列表，支持多种格式（APA、MLA、AMA、NLM、国标2015等）..."
            className="w-full h-64 p-4 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none text-sm"
            disabled={loading}
          />
          {/* 进度状态显示（非紧凑模式） */}
          {!isCompact && progressStatus && (
            <div className="mt-4 flex items-center gap-3 text-sm text-purple-600">
              <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              <span className="font-medium">{progressStatus}</span>
            </div>
          )}
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium flex items-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  处理中...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                  开始校验
                </>
              )}
            </button>
          </div>
        </>
      )}
    </div>
  );
};

