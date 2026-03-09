# app/models/entity.py（通用实体模型，适配文档/页面内容）
from sqlalchemy import Column, String, JSON, Float, Text
from app.models.database import BaseModel

class Entity(BaseModel):
    __tablename__ = "entities"
    __table_args__ = {"comment": "通用实体表（文档/页面提取）"}
    
    # 通用实体字段，适配任意内容（而非游戏）
    name = Column(String(200), nullable=False, comment="实体名称（如规则名称、奖励名称、参数名）")
    type = Column(String(50), nullable=False, comment="实体类型（如冷却时间、任务奖励、印记规则、表格单元格）")
    content = Column(Text, comment="实体原始内容")
    attributes = Column(JSON, default=dict, comment="实体属性（如数值、单位、所属模块）")
    source = Column(String(500), comment="来源（文档路径/页面URL）")
    confidence = Column(Float, default=1.0, comment="提取置信度")