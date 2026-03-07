# app/models/relation.py
import uuid
from datetime import datetime

# 修复第三方库导入（确保已安装sqlalchemy）
from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID

# 修复内部导入路径（从app.db.base导入）
from app.db.base import Base

class Relation(Base):
    """实体关系表：解决原有relations表为空问题"""
    __tablename__ = "relations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)  # 源实体ID
    target_id = Column(UUID(as_uuid=True), ForeignKey("entities.id"), nullable=False)  # 目标实体ID
    relation_type = Column(String(50), nullable=False)  # 关系类型（has_skill/apply_to等）
    description = Column(Text, nullable=True)  # 关系描述
    created_at = Column(DateTime, default=datetime.utcnow)

    # 解决UUID序列化问题：返回时转为字符串
    def to_dict(self):
        return {
            "id": str(self.id),
            "source_id": str(self.source_id),
            "target_id": str(self.target_id),
            "relation_type": self.relation_type,
            "description": self.description,
            "created_at": self.created_at
        }