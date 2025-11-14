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
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      <h2 className="text-xl font-bold mb-4 text-gray-800">用户输入区</h2>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="请输入参考文献列表，支持多种格式（APA、MLA、AMA、NLM、国标2015等）..."
        className="w-full h-48 p-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
        disabled={loading}
      />
      <div className="mt-4 flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? '处理中...' : '提交'}
        </button>
      </div>
    </div>
  );
};

