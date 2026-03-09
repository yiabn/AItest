# app/database.py
import asyncpg
from asyncpg import Pool, Record
from typing import Optional, List, Dict, Any, Union
from loguru import logger
from app.config import settings
import uuid
import json

class Database:
    """PostgreSQL 数据库连接池管理类"""

    def __init__(self):
        self.pool: Optional[Pool] = None
        self._connected = False

    async def connect(self):
        """创建数据库连接池"""
        try:
            self.pool = await asyncpg.create_pool(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                database=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                min_size=settings.DB_POOL_MIN_SIZE,
                max_size=settings.DB_POOL_MAX_SIZE,
                command_timeout=60,
                max_queries=50000,
                max_inactive_connection_lifetime=300,
            )
            self._connected = True
            logger.info(f"✅ 数据库连接池创建成功: {settings.DB_NAME}@{settings.DB_HOST}")

            # 测试连接
            async with self.pool.acquire() as conn:
                await conn.execute("SELECT 1")
            logger.info("✅ 数据库连接测试成功")

        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            self._connected = False
            raise

    async def close(self):
        """关闭连接池"""
        if self.pool:
            await self.pool.close()
            self._connected = False
            logger.info("数据库连接池已关闭")

    @property
    def is_connected(self) -> bool:
        return self._connected

    # ========== 通用查询方法 ==========

    async def fetch(self, query: str, *args) -> List[Record]:
        """执行查询并返回多条记录"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *args)
            logger.debug(f"查询返回 {len(rows)} 行")
            return rows

    async def fetchrow(self, query: str, *args) -> Optional[Record]:
        """执行查询并返回单条记录"""
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def fetchval(self, query: str, *args) -> Any:
        """执行查询并返回单个值"""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(query, *args)

    async def execute(self, query: str, *args) -> str:
        """执行SQL命令（INSERT/UPDATE/DELETE）"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    # ========== 事务支持 ==========

    async def transaction(self):
        """获取事务对象，用于上下文管理"""
        if not self.pool:
            raise Exception("数据库连接池未初始化")
        conn = await self.pool.acquire()
        return conn.transaction()

    # ========== 实体相关方法 ==========

    async def create_entity(self, **kwargs) -> str:
        """创建新实体，返回实体ID"""
        entity_id = kwargs.get('id') or str(uuid.uuid4())

        query = """
            INSERT INTO entities (
                id, name, type, source_url, source_game,
                version, attributes, confidence
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id
        """

        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                query,
                entity_id,
                kwargs.get('name'),
                kwargs.get('type'),
                kwargs.get('source_url'),
                kwargs.get('source_game', '魔域'),
                kwargs.get('version', '1.0'),
                json.dumps(kwargs.get('attributes', {})),  # 转换为JSON字符串
                kwargs.get('confidence', 1.0)
            )
            logger.debug(f"创建实体: {kwargs.get('name')} ({entity_id})")
            return result

    async def get_entity(self, entity_id: str) -> Optional[Dict]:
        """根据ID获取实体"""
        query = "SELECT * FROM entities WHERE id = $1"
        row = await self.fetchrow(query, entity_id)

        if row:
            # 将Record转换为字典
            entity = dict(row)
            # 解析JSONB字段
            if entity.get('attributes'):
                entity['attributes'] = json.loads(entity['attributes'])
            return entity
        return None

    async def get_entities_by_type(self, entity_type: str, limit: int = 100) -> List[Dict]:
        """根据类型获取实体列表"""
        query = "SELECT * FROM entities WHERE type = $1 ORDER BY created_at DESC LIMIT $2"
        rows = await self.fetch(query, entity_type, limit)

        entities = []
        for row in rows:
            entity = dict(row)
            if entity.get('attributes'):
                entity['attributes'] = json.loads(entity['attributes'])
            entities.append(entity)
        return entities

    async def update_entity_attributes(self, entity_id: str, attributes: Dict) -> bool:
        """更新实体的attributes字段"""
        query = """
            UPDATE entities
            SET attributes = attributes || $1::jsonb, updated_at = NOW()
            WHERE id = $2
        """
        result = await self.execute(query, json.dumps(attributes), entity_id)
        return 'UPDATE 1' in result

    async def delete_entity(self, entity_id: str) -> bool:
        """删除实体"""
        query = "DELETE FROM entities WHERE id = $1"
        result = await self.execute(query, entity_id)
        return 'DELETE 1' in result

    # ========== 关系相关方法 ==========

    async def create_relation(self, **kwargs) -> str:
        """创建实体关系"""
        relation_id = str(uuid.uuid4())

        query = """
            INSERT INTO relations (
                id, source_id, target_id, relation_type, properties, confidence
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (source_id, target_id, relation_type)
            DO UPDATE SET
                properties = EXCLUDED.properties,
                confidence = EXCLUDED.confidence
            RETURNING id
        """

        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                query,
                relation_id,
                kwargs.get('source_id'),
                kwargs.get('target_id'),
                kwargs.get('relation_type'),
                json.dumps(kwargs.get('properties', {})),
                kwargs.get('confidence', 1.0)
            )
            logger.debug(f"创建关系: {kwargs.get('relation_type')} ({relation_id})")
            return result

    async def get_relations(self, entity_id: str) -> List[Dict]:
        """获取实体的所有关系（包括源和目标）"""
        query = """
            SELECT r.*,
                   e1.name as source_name, e1.type as source_type,
                   e2.name as target_name, e2.type as target_type
            FROM relations r
            JOIN entities e1 ON r.source_id = e1.id
            JOIN entities e2 ON r.target_id = e2.id
            WHERE r.source_id = $1 OR r.target_id = $1
        """
        rows = await self.fetch(query, entity_id)

        relations = []
        for row in rows:
            rel = dict(row)
            if rel.get('properties'):
                rel['properties'] = json.loads(rel['properties'])
            relations.append(rel)
        return relations

    # ========== 用户补充相关方法 ==========

    async def add_user_supplement(self, entity_id: str, user_id: Optional[str],
                                  field_name: str, field_value: str,
                                  original_value: Optional[str] = None,
                                  source: str = 'chat') -> str:
        """添加用户补充信息"""
        supplement_id = str(uuid.uuid4())

        query = """
            INSERT INTO user_supplements (
                id, entity_id, user_id, field_name, field_value, original_value, source, status
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, 'pending')
            RETURNING id
        """

        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                query,
                supplement_id,
                entity_id,
                user_id,
                field_name,
                field_value,
                original_value,
                source
            )
            logger.debug(f"用户补充已记录: {supplement_id}")
            return result

    # ========== 页面快照相关方法 ==========

    async def save_page_snapshot(self, url: str, title: str, html: str, text: str) -> str:
        """保存页面快照"""
        snapshot_id = str(uuid.uuid4())

        query = """
            INSERT INTO page_snapshots (id, url, title, raw_html, raw_text)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (url) DO UPDATE SET
                title = EXCLUDED.title,
                raw_html = EXCLUDED.raw_html,
                raw_text = EXCLUDED.raw_text,
                fetch_time = NOW()
            RETURNING id
        """

        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                query,
                snapshot_id,
                url,
                title,
                html,
                text
            )
            return result

    # ========== 搜索方法 ==========

    async def search_entities(self, keyword: str, entity_type: Optional[str] = None) -> List[Dict]:
        """搜索实体（基于名称和属性）"""
        # 使用 PostgreSQL 的全文搜索（简单 ILIKE 版本，可后续优化为 tsvector）
        query = """
            SELECT * FROM entities
            WHERE
                name ILIKE $1
                OR attributes::text ILIKE $1
                {type_filter}
            ORDER BY
                CASE WHEN name ILIKE $1 THEN 1 ELSE 2 END,
                created_at DESC
            LIMIT 50
        """

        type_filter = ""
        params = [f'%{keyword}%']

        if entity_type:
            type_filter = "AND type = $2"
            params.append(entity_type)

        query = query.format(type_filter=type_filter)
        rows = await self.fetch(query, *params)

        entities = []
        for row in rows:
            entity = dict(row)
            if entity.get('attributes'):
                entity['attributes'] = json.loads(entity['attributes'])
            entities.append(entity)
        return entities

    async def save_test_point(self, test_point: dict) -> str:
        # 插入测试点，返回 ID
        query = """
            INSERT INTO test_points (id, entity_id, task_id, category, description, expected_result, test_steps, priority, confidence)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id
        """
        tp_id = str(uuid.uuid4())
        await self.execute(query, tp_id, test_point['entity_id'], test_point['task_id'],
                        test_point['category'], test_point['description'],
                        test_point.get('expected_result'), test_point.get('test_steps'),
                        test_point.get('priority', 'medium'), test_point.get('confidence', 1.0))
        return tp_id

    async def get_test_points_by_entity(self, entity_id: str) -> List[Dict]:
        query = "SELECT * FROM test_points WHERE entity_id = $1 ORDER BY created_at DESC"
        rows = await self.fetch(query, entity_id)
        return [dict(row) for row in rows]

# 创建全局数据库实例
db = Database()


# 为了方便测试，提供一个同步的测试函数
async def test_database():
    """测试数据库连接和基本操作"""
    try:
        await db.connect()

        # 测试创建实体
        entity_id = await db.create_entity(
            name="奇迹龙",
            type="pet",
            source_url="https://my.99.com/data/pet/123.html",
            attributes={
                "攻击力": "8500-12000",
                "防御力": 4500,
                "生命值": 58000,
                "元素": "光"
            }
        )
        print(f"创建实体成功: {entity_id}")

        entity = await db.get_entity(entity_id)
        print(f"获取实体: {entity['name']}, 属性: {entity['attributes']}")

        await db.update_entity_attributes(entity_id, {"获取方式": "冰封要塞掉落"})
        print("更新实体成功")

        results = await db.search_entities("奇迹")
        print(f"搜索结果: {len(results)} 个")

        # 测试关系创建
        rel_id = await db.create_relation(
            source_id=entity_id,
            target_id=entity_id,  # 自环用于测试
            relation_type="test_relation",
            properties={"test": True}
        )
        print(f"创建关系成功: {rel_id}")

        relations = await db.get_relations(entity_id)
        print(f"获取关系: {len(relations)} 个")

        await db.close()
        print("所有测试通过！")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_database())