// src/api/config.ts
import axios from 'axios';
import type { AxiosResponse } from 'axios';  // 使用 type-only 导入
import { ElMessage } from 'element-plus';
import type { AnalysisResult } from '@/types';

// 定义 API 响应类型
export interface ApiResponse<T = any> {
  data: T;
  status: number;
  message?: string;
}

// 创建 axios 实例
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 30000,
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log(`发送请求: ${config.method?.toUpperCase()} ${config.url}`, config.data || config.params);
    return config;
  },
  (error) => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器 - 直接返回 data
api.interceptors.response.use(
  (response: AxiosResponse) => {
    console.log('收到响应:', response.data);
    return response.data;
  },
  (error) => {
    console.error('响应错误:', error);
    let message = '请求失败';
    if (error.response) {
      message = error.response.data?.detail || error.response.statusText;
    } else if (error.request) {
      message = '无法连接到服务器';
    } else {
      message = error.message;
    }
    ElMessage.error(message);
    return Promise.reject(error);
  }
);

// ========== 类型定义 ==========

export interface Entity {
  id: string;
  name: string;
  type: string;
  attributes: Record<string, any>;
  confidence: number;
  source_url?: string;
  source_game: string;
  created_at: string;
  updated_at: string;
}

export interface Relation {
  id: string;
  source_id: string;
  source_name: string;
  source_type: string;
  target_id: string;
  target_name: string;
  target_type: string;
  relation_type: string;
  properties: Record<string, any>;
  confidence: number;
}

export interface EntityDetail {
  entity: Entity;
  relations: Relation[];
  supplements: any[];
}

export interface TypeStat {
  type: string;
  count: number;
}

export interface SearchResult {
  results: Entity[];
  total: number;
  keyword: string;
}

export interface KnowledgeStats {
  total_entities: number;
  total_relations: number;
  total_supplements: number;
  total_test_points: number;
  today_new: number;
  type_distribution: TypeStat[];
  last_update: string;
}

export interface ChatResponse {
  reply: string;
  updated_entity?: Record<string, any>;
}

// ========== 分析相关 API ==========
export const analyzeApi = {
  analyzeUrl: (data: { url: string; depth?: number; include_raw?: boolean }): Promise<AnalysisResult> => {
    return api.post('/analyze/url', data);
  },
  
  getTask: (taskId: string): Promise<AnalysisResult> => {
    return api.get(`/analyze/task/${taskId}`);
  },
  
  getPageTypes: (): Promise<{ types: Array<{ value: string; label: string }> }> => {
    return api.get('/analyze/types');
  },
  submitUrl: (data: { url: string; depth?: number; include_raw?: boolean }) => {
    return api.post('/analyze/url', data);
  }
};



// ========== 对话相关 API ==========
export const chatApi = {
  supplementEntity: (data: { entity_id: string; entity_name: string; message: string }): Promise<ChatResponse> => {
    return api.post('/chat/supplement', data);
  },
  
  getChatHistory: (entityId: string): Promise<any> => {
    return api.get(`/chat/history/${entityId}`);
  },
  
  getEntityInfo: (entityId: string): Promise<EntityDetail> => {
    return api.get(`/chat/entity/${entityId}`);
  },
  
  searchEntities: (keyword: string, type?: string): Promise<SearchResult> => {
    return api.post('/chat/search', { keyword, entity_type: type });
  }
};

// ========== 知识库相关 API ==========
export const knowledgeApi = {
  // 获取实体列表
  getEntities: (params?: { type?: string; limit?: number; offset?: number }): Promise<Entity[]> => {
    return api.get('/knowledge/entities', { params });
  },
  
  // 获取实体详情
  getEntityDetail: (entityId: string): Promise<EntityDetail> => {
    return api.get(`/knowledge/entities/${entityId}`);
  },
  
  // 获取类型统计
  getTypeStats: (): Promise<TypeStat[]> => {
    return api.get('/knowledge/types');
  },
  
  // 搜索实体
  search: (keyword: string, type?: string): Promise<SearchResult> => {
    return api.get('/knowledge/search', { params: { keyword, type } });
  },
  
  // 获取实体关系
  getRelations: (entityId: string): Promise<Relation[]> => {
    return api.get(`/knowledge/relations/${entityId}`);
  },
  
  // 获取最近添加的实体
  getRecent: (limit?: number): Promise<Entity[]> => {
    return api.get('/knowledge/recent', { params: { limit } });
  },
  
  // 获取知识库统计
  getStats: (): Promise<KnowledgeStats> => {
    return api.get('/knowledge/stats');
  }
};

export default api;