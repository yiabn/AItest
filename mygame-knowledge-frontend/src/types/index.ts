// src/types/index.ts

// 实体信息
export interface Entity {
  id?: string;
  name: string;
  type: string;
  attributes: Record<string, any>;
  confidence?: number;
}

// 分析结果
export interface AnalysisResult {
  task_id: string;
  title: string;
  url: string;
  data_type: string;
  entities: Entity[];
  relations?: any[];
  raw_html?: string;
  raw_text?: string;
  suggestions: string[];
  analyze_time: string;
  source: string;
}

// 聊天消息
export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  sender: string;
  avatar?: string;
  content: string;
  timestamp?: string;
}

// 历史记录项
export interface HistoryItem {
  id: string;
  title: string;
  type: string;
  url: string;
  time: string;
  task_id: string;
}