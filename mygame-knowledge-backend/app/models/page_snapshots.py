# app/models/page_snapshots.py（通用页面/文档快照）
from sqlalchemy import Column, String, Text, Enum
import enum
from app.models.database import BaseModel

# 通用内容类型枚举
class ContentType(enum.Enum):
    HTML = "html"
    DOCX = "docx"
    TXT = "txt"
    PDF = "pdf"

class PageSnapshot(BaseModel):
    __tablename__ = "page_snapshots"
    __table_args__ = {"comment": "页面/文档快照表"}
    
    source = Column(String(500), nullable=False, comment="来源（URL/文件路径）")
    content_type = Column(Enum(ContentType), nullable=False, comment="内容类型")
    raw_content = Column(Text, comment="原始内容（HTML/文档文本）")
    parsed_content = Column(Text, comment="解析后的纯文本")
    parse_status = Column(String(20), default="unparsed", comment="解析状态：unparsed/parsed/failed")