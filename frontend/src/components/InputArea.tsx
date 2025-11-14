import React, { useState } from 'react';
import { ReferenceItem } from '../types';

interface InputAreaProps {
  onProcess: (references: ReferenceItem[]) => void;
  loading: boolean;
}

export const InputArea: React.FC<InputAreaProps> = ({ onProcess, loading }) => {
  const [text, setText] = useState('');

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
      
      console.log('【前端】调用 onProcess 回调');
      onProcess(data.references);
    } catch (error) {
      console.error('【前端】处理失败:', error);
      alert('处理失败，请重试');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold mb-4 text-gray-800">Paste Your References</h2>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="请输入参考文献列表，支持多种格式（APA、MLA、AMA、NLM、国标2015等）..."
        className="w-full h-64 p-4 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none text-sm"
        disabled={loading}
      />
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
              Process References
            </>
          )}
        </button>
      </div>
    </div>
  );
};

