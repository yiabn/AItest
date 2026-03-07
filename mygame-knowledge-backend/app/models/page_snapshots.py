# app/models/page_snapshots.py
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class PageSnapshot(Base):
    """页面快照表"""
    __tablename__ = "page_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    url = Column(String(500), unique=True, nullable=False, comment="页面URL")
    html_content = Column(Text, nullable=False, comment="页面原始HTML")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, comment="更新时间")

    def to_dict(self):
        return {
            "id": str(self.id),
            "url": self.url,
            "html_content": self.html_content,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }