# app/api/knowledge.py
import json
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from loguru import logger
from pydantic import BaseModel
from datetime import datetime
from app.database import db
import traceback

router = APIRouter()

# ========== 响应模型 ==========
class EntityResponse(BaseModel):
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

class TestPointResponse(BaseModel):
    id: str
    entity_id: Optional[str] = None
    category: str
    description: str
    expected_result: Optional[str] = None
    test_steps: Optional[str] = None
    priority: str = "medium"
    status: str = "pending"
    confidence: float = 1.0
    created_at: datetime

class EntityDetailResponse(BaseModel):
    entity: EntityResponse
    relations: List[RelationResponse]
    supplements: List[Dict[str, Any]]
    test_points: List[TestPointResponse]   # 新增测试点字段

class TypeStatResponse(BaseModel):
    type: str
    count: int

class SearchResponse(BaseModel):
    results: List[EntityResponse]
    total: int
    keyword: str

# ========== 辅助函数：处理 attributes ==========
def safe_parse_attributes(attr_val):
    if attr_val is None:
        return {}
    if isinstance(attr_val, dict):
        return attr_val
    if isinstance(attr_val, str):
        try:
            return json.loads(attr_val)
        except json.JSONDecodeError:
            logger.warning(f"JSON解析失败: {attr_val[:100]}")
            return {}
    return {}

def row_to_entity(row) -> dict:
    entity = dict(row)
    if 'id' in entity and not isinstance(entity['id'], str):
        entity['id'] = str(entity['id'])
    entity['attributes'] = safe_parse_attributes(entity.get('attributes'))
    return entity

def row_to_relation(row) -> dict:
    rel = dict(row)
    for key in ['id', 'source_id', 'target_id']:
        if key in rel and not isinstance(rel[key], str):
            rel[key] = str(rel[key])
    if rel.get('properties'):
        rel['properties'] = safe_parse_attributes(rel['properties'])
    return rel

def row_to_test_point(row) -> dict:
    tp = dict(row)
    if 'id' in tp and not isinstance(tp['id'], str):
        tp['id'] = str(tp['id'])
    if tp.get('entity_id') and not isinstance(tp['entity_id'], str):
        tp['entity_id'] = str(tp['entity_id'])
    return tp

# ========== 接口 ==========
@router.get("/test-db")
async def test_db():
    try:
        result = await db.fetchval("SELECT 1")
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entities", response_model=List[EntityResponse])
async def get_entities(
    type: Optional[str] = Query(None, description="实体类型过滤"),
    limit: int = Query(100, description="返回数量限制", ge=1, le=1000),
    offset: int = Query(0, description="分页偏移量", ge=0)
):
    try:
        if type:
            query = """
                SELECT * FROM entities 
                WHERE type = $1 
                ORDER BY created_at DESC 
                LIMIT $2 OFFSET $3
            """
            rows = await db.fetch(query, type, limit, offset)
        else:
            query = """
                SELECT * FROM entities 
                ORDER BY created_at DESC 
                LIMIT $1 OFFSET $2
            """
            rows = await db.fetch(query, limit, offset)
        return [row_to_entity(row) for row in rows]
    except Exception as e:
        logger.error(f"获取实体列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/entities/{entity_id}", response_model=EntityDetailResponse)
async def get_entity_detail(entity_id: str):
    try:
        # 获取实体
        row = await db.fetchrow("SELECT * FROM entities WHERE id = $1", entity_id)
        if not row:
            raise HTTPException(status_code=404, detail="实体不存在")
        entity = row_to_entity(row)

        # 获取关系
        rel_rows = await db.fetch("""
            SELECT r.*, 
                   e1.name as source_name, e1.type as source_type,
                   e2.name as target_name, e2.type as target_type
            FROM relations r
            JOIN entities e1 ON r.source_id = e1.id
            JOIN entities e2 ON r.target_id = e2.id
            WHERE r.source_id = $1 OR r.target_id = $1
        """, entity_id)
        relations = [row_to_relation(r) for r in rel_rows]

        # 获取补充历史
        supp_rows = await db.fetch(
            "SELECT * FROM user_supplements WHERE entity_id = $1 ORDER BY created_at DESC LIMIT 20",
            entity_id
        )
        supplements = []
        for s in supp_rows:
            sup = dict(s)
            supplements.append({
                "id": sup['id'],
                "field_name": sup['field_name'],
                "field_value": sup['field_value'],
                "original_value": sup['original_value'],
                "source": sup['source'],
                "created_at": sup['created_at'].isoformat() if sup['created_at'] else None,
                "status": sup['status']
            })

        # 获取测试点
        tp_rows = await db.fetch("SELECT * FROM test_points WHERE entity_id = $1 ORDER BY created_at DESC", entity_id)
        test_points = [row_to_test_point(tp) for tp in tp_rows]

        return {
            "entity": entity,
            "relations": relations,
            "supplements": supplements,
            "test_points": test_points
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取实体详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/types", response_model=List[TypeStatResponse])
async def get_entity_types():
    try:
        rows = await db.fetch("SELECT type, COUNT(*) as count FROM entities GROUP BY type ORDER BY count DESC")
        return [{"type": r['type'], "count": r['count']} for r in rows]
    except Exception as e:
        logger.error(f"获取类型统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=SearchResponse)
async def search(
    keyword: str = Query(..., description="搜索关键词", min_length=1),
    type: Optional[str] = Query(None, description="限定实体类型")
):
    try:
        results = await db.search_entities(keyword, type)
        for entity in results:
            if 'id' in entity and not isinstance(entity['id'], str):
                entity['id'] = str(entity['id'])
            entity['attributes'] = safe_parse_attributes(entity.get('attributes'))
        return {"results": results, "total": len(results), "keyword": keyword}
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/relations/{entity_id}", response_model=List[RelationResponse])
async def get_entity_relations(entity_id: str):
    try:
        rows = await db.fetch("""
            SELECT r.*, 
                   e1.name as source_name, e1.type as source_type,
                   e2.name as target_name, e2.type as target_type
            FROM relations r
            JOIN entities e1 ON r.source_id = e1.id
            JOIN entities e2 ON r.target_id = e2.id
            WHERE r.source_id = $1 OR r.target_id = $1
        """, entity_id)
        return [row_to_relation(r) for r in rows]
    except Exception as e:
        logger.error(f"获取关系失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recent", response_model=List[EntityResponse])
async def get_recent_entities(limit: int = Query(10, ge=1, le=50)):
    try:
        rows = await db.fetch("SELECT * FROM entities ORDER BY created_at DESC LIMIT $1", limit)
        return [row_to_entity(row) for row in rows]
    except Exception as e:
        logger.error(f"获取最近实体失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_knowledge_stats():
    try:
        total = await db.fetchval("SELECT COUNT(*) FROM entities")
        type_rows = await db.fetch("SELECT type, COUNT(*) as count FROM entities GROUP BY type ORDER BY count DESC")
        type_stats = [{"type": r['type'], "count": r['count']} for r in type_rows]
        relation_count = await db.fetchval("SELECT COUNT(*) FROM relations")
        supplement_count = await db.fetchval("SELECT COUNT(*) FROM user_supplements")
        test_point_count = await db.fetchval("SELECT COUNT(*) FROM test_points")
        today_count = await db.fetchval("SELECT COUNT(*) FROM entities WHERE created_at >= CURRENT_DATE")
        return {
            "total_entities": total,
            "total_relations": relation_count,
            "total_supplements": supplement_count,
            "total_test_points": test_point_count,
            "today_new": today_count,
            "type_distribution": type_stats,
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/entities/{entity_id}")
async def delete_entity(entity_id: str):
    try:
        row = await db.fetchrow("SELECT id, name FROM entities WHERE id = $1", entity_id)
        if not row:
            raise HTTPException(status_code=404, detail="实体不存在")
        await db.execute("DELETE FROM entities WHERE id = $1", entity_id)
        logger.warning(f"实体已删除: {entity_id} - {row['name']}")
        return {"message": "删除成功", "entity_id": entity_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除实体失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/entities/{entity_id}/verify")
async def verify_entity(entity_id: str):
    try:
        result = await db.fetchval(
            "UPDATE entities SET confidence = 1.0, updated_at = NOW() WHERE id = $1 RETURNING id",
            entity_id
        )
        if not result:
            raise HTTPException(status_code=404, detail="实体不存在")
        return {"message": "已验证", "entity_id": entity_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"验证实体失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))