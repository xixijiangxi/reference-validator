import axios from 'axios';
import { ReferenceItem, ReferenceKeyword, PubMedArticle } from '../types';

const API_BASE_URL = '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const referenceAPI = {
  // 拆分参考文献
  splitReferences: async (text: string): Promise<ReferenceItem[]> => {
    const response = await api.post('/split', { text });
    return response.data.references;
  },

  // 搜索参考文献
  searchReference: async (
    referenceId: string,
    keywords: ReferenceKeyword
  ): Promise<{ matched_articles: PubMedArticle[]; status: string }> => {
    const response = await api.post(`/search/${referenceId}`, keywords);
    return response.data;
  },

  // 格式化参考文献
  formatReferences: async (
    references: any[],
    targetFormat: string
  ): Promise<string> => {
    const response = await api.post('/format', references, {
      params: { target_format: targetFormat },
    });
    return response.data.formatted_text;
  },
};

