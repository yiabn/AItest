# app/utils/entity_utils.py
import uuid
from typing import Optional

# 修复数据库会话导入
from app.db.session import db_session
# 修复实体模型导入
from app.models.entity import Entity

def get_or_create_entity_id(entity_name: str, entity_type: str) -> str:
    """
    获取实体ID（存在则返回，不存在则创建）
    :param entity_name: 实体名称
    :param entity_type: 实体类型（skill/pet/equipment等）
    :return: 实体ID（字符串格式）
    """
    # 先查询是否存在
    entity = db_session.query(Entity).filter(
        Entity.name == entity_name,
        Entity.type == entity_type
    ).first()

    if entity:
        return str(entity.id)  # 转为字符串（解决UUID序列化问题）
    
    # 不存在则创建新实体
    new_entity = Entity(
        id=uuid.uuid4(),
        name=entity_name,
        type=entity_type,
        attributes={},
        source_url=""
    )
    db_session.add(new_entity)
    db_session.commit()
    return str(new_entity.id)

def get_entity_id(entity_name: str, entity_type: str) -> Optional[str]:
    """仅获取实体ID（不存在返回None）"""
    entity = db_session.query(Entity).filter(
        Entity.name == entity_name,
        Entity.type == entity_type
    ).first()
    return str(entity.id) if entity else None