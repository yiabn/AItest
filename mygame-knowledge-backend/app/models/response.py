# app/models/response.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class EntityInfo(BaseModel):
    """实体信息"""
    id: Optional[str] = None
    name: str
    type: str  # pet, equipment, skill, etc.
    attributes: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(1.0, ge=0, le=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123_entity_0",
                "name": "奇迹龙",
                "type": "pet",
                "attributes": {"level": 150, "攻击力": 8500},
                "confidence": 0.95
            }
        }

class RelationInfo(BaseModel):
    """关系信息"""
    source: str
    target: str
    relation_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "source": "奇迹龙",
                "target": "龙息术",
                "relation_type": "has_skill",
                "properties": {}
            }
        }

class AnalyzeResponse(BaseModel):
    """分析响应模型"""
    task_id: str
    title: str = ""
    url: str = ""
    data_type: str = "general"
    entities: List[EntityInfo] = Field(default_factory=list)
    relations: List[RelationInfo] = Field(default_factory=list)
    raw_html: Optional[str] = None
    raw_text: Optional[str] = None
    suggestions: List[str] = Field(default_factory=list)
    analyze_time: datetime = Field(default_factory=datetime.now)
    source: str = "魔域官方资料库"
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "abc123",
                "title": "幻兽·奇迹龙",
                "url": "https://my.99.com/data/pet/123.html",
                "data_type": "pet",
                "entities": [],
                "suggestions": ["建议补充技能信息"],
                "source": "魔域官方资料库"
            }
        }

class ChatResponse(BaseModel):
    """对话响应模型"""
    reply: str = Field(..., description="AI回复")
    updated_entity: Optional[Dict[str, Any]] = Field(None, description="更新后的实体")
    
    class Config:
        json_schema_extra = {
            "example": {
                "reply": "已记录获取方式，还有需要补充的吗？",
                "updated_entity": {"acquisition": "冰封要塞掉落"}
            }
        }

# 为了兼容性，也导出这些类型
__all__ = [
    'EntityInfo',
    'RelationInfo', 
    'AnalyzeResponse',
    'ChatResponse'
]