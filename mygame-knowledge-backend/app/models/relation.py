# app/models/relation.py（通用关系模型，解决relations表为空问题）
from sqlalchemy import Column, String, JSON, Text
from app.models.database import BaseModel

class Relation(BaseModel):
    __tablename__ = "relations"
    __table_args__ = {"comment": "实体关系表（文档/页面内容关联）"}
    
    # 通用关系字段，适配任意内容的实体关联
    head_entity_name = Column(String(200), nullable=False, comment="头实体名称")
    head_entity_type = Column(String(50), nullable=False, comment="头实体类型")
    relation_type = Column(String(100), nullable=False, comment="关系类型（如包含、属于、拥有数值、规则描述）")
    tail_entity_name = Column(String(200), nullable=False, comment="尾实体名称")
    tail_entity_type = Column(String(50), nullable=False, comment="尾实体类型")
    description = Column(Text, comment="关系描述")
    properties = Column(JSON, default=dict, comment="关系属性（如位置、优先级）")