# app/models/response.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class EntityInfo(BaseModel):
    """实体信息（用于分析响应）"""
    id: Optional[str] = None
    name: str
    type: str
    attributes: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(1.0, ge=0, le=1)

class RelationInfo(BaseModel):
    """关系信息（用于分析响应）"""
    source: str
    target: str
    relation_type: str
    properties: Dict[str, Any] = Field(default_factory=dict)

class TestPoint(BaseModel):
    """测试点模型"""
    id: Optional[str] = None
    entity_id: Optional[str] = Field(None, description="关联的实体ID")
    task_id: Optional[str] = Field(None, description="关联的任务ID")
    category: str = Field(..., description="测试点类别：数值验证、机制验证等")
    description: str = Field(..., description="测试点描述")
    expected_result: Optional[str] = Field(None, description="预期结果")
    test_steps: Optional[str] = Field(None, description="测试步骤")
    priority: str = Field("medium", description="优先级：high/medium/low")
    status: str = Field("pending", description="状态：pending/passed/failed/blocked")
    confidence: float = Field(1.0, ge=0, le=1, description="AI生成置信度")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")

class AnalyzeResponse(BaseModel):
    """分析URL的响应模型"""
    task_id: str
    title: str
    url: str
    data_type: str
    entities: List[EntityInfo] = []
    relations: List[RelationInfo] = []
    raw_html: Optional[str] = None
    raw_text: Optional[str] = None
    suggestions: List[str] = []
    test_points: List[TestPoint] = Field(default_factory=list, description="生成的测试点")
    analyze_time: datetime = Field(default_factory=datetime.now)
    source: str = "魔域官方资料库"

class EntityResponse(BaseModel):
    """知识库实体响应模型（用于列表和详情）"""
    id: str
    name: str
    type: str
    attributes: Dict[str, Any]
    confidence: float
    source_url: Optional[str] = None
    source_game: str
    created_at: datetime
    updated_at: datetime

class RelationResponse(BaseModel):
    """知识库关系响应模型"""
    id: str
    source_id: str
    source_name: str
    source_type: str
    target_id: str
    target_name: str
    target_type: str
    relation_type: str
    properties: Dict[str, Any]
    confidence: float

class EntityDetailResponse(BaseModel):
    """实体详情响应模型（包含关系、补充历史和测试点）"""
    entity: EntityResponse
    relations: List[RelationResponse]
    supplements: List[Dict[str, Any]]
    test_points: List[TestPoint]

class TypeStatResponse(BaseModel):
    """类型统计响应模型"""
    type: str
    count: int

class SearchResponse(BaseModel):
    """搜索响应模型"""
    results: List[EntityResponse]
    total: int
    keyword: str

class ChatResponse(BaseModel):
    """对话补充响应模型"""
    reply: str
    updated_entity: Optional[Dict[str, Any]] = None