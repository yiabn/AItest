from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AnalyzeRequest(BaseModel):
    """分析请求模型"""
    url: str = Field(..., description="要分析的网址")
    depth: int = Field(1, description="分析深度", ge=1, le=3)
    include_raw: bool = Field(False, description="是否包含原始内容")

class ChatRequest(BaseModel):
    """对话请求模型"""
    entity_id: str = Field(..., description="实体ID")
    entity_name: str = Field(..., description="实体名称")
    message: str = Field(..., description="用户消息")
    context: Optional[Dict[str, Any]] = Field(None, description="上下文信息")

class ChatResponse(BaseModel):
    """对话响应模型"""
    reply: str = Field(..., description="AI回复")
    updated_entity: Optional[Dict[str, Any]] = Field(None, description="更新后的实体")