# app/models/entity.py
import uuid
from sqlalchemy import Column, String, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.base import Base

class Entity(Base):
    """实体表（原有模型，补全）"""
    __tablename__ = "entities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, comment="实体名称")
    type = Column(String(50), nullable=False, comment="实体类型（skill/pet/equipment等）")
    attributes = Column(JSON, default={}, comment="实体属性")
    source_url = Column(String(500), nullable=True, comment="来源URL")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.type,
            "attributes": self.attributes,
            "source_url": self.source_url,
            "created_at": self.created_at
        }