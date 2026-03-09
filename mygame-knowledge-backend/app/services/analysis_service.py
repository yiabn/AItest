# app/services/analysis_service.py
import uuid
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from bs4 import BeautifulSoup

from app.crawlers.m99_crawler import M99Crawler
from app.services.ai_analyzer import DoubaoAnalyzer  # 新增
from app.models.response import AnalyzeResponse, EntityInfo, RelationInfo, TestPoint
from app.database import db

class AnalysisService:
    """分析服务 - 使用 AI 分析页面，提取技能和测试点"""

    def __init__(self):
        self.crawler = M99Crawler()
        # self.extractor = GameEntityExtractor()  # 不再使用
        # self.relation_extractor = RelationExtractor()  # 关系提取暂时保留（可选）
        self.ai_analyzer = DoubaoAnalyzer()  # 新增
        # self.test_point_generator = TestPointGenerator()  # 不再使用

    async def analyze_url(self, url: str, depth: int = 1, include_raw: bool = False) -> AnalyzeResponse:
        task_id = str(uuid.uuid4())
        logger.info(f"开始分析任务 {task_id}: {url}")

        try:
            # 1. 抓取页面
            page_data = self.crawler.analyze_page(url)
            if "error" in page_data:
                raise Exception(page_data["error"])

            # 2. 保存页面快照
            try:
                snapshot_id = await db.save_page_snapshot(
                    url=url,
                    title=page_data.get("title", ""),
                    html=page_data.get("html", ""),
                    text=page_data.get("text", "")
                )
                logger.debug(f"页面快照已保存: {snapshot_id}")
            except Exception as e:
                logger.warning(f"保存页面快照失败: {e}")

            # ========== AI 分析 ==========
            ai_result = self.ai_analyzer.analyze(page_data["text"])
            skills = ai_result.get("skills", [])
            ai_test_points = ai_result.get("test_points", [])

            # 3. 将技能转化为实体存入数据库
            entities = []
            entity_id_map = {}
            id_to_entity = {}

            for idx, skill in enumerate(skills):
                temp_id = f"{task_id}_skill_{idx}"
                # 存入数据库
                db_id = await db.create_entity(
                    name=skill.get("name", "未知技能"),
                    type="skill",
                    source_url=url,
                    attributes=skill,  # 存储完整的技能信息
                    confidence=0.95,
                    version="1.0"
                )
                entity_info = EntityInfo(
                    id=temp_id,
                    name=skill.get("name", "未知技能"),
                    type="skill",
                    attributes=skill,
                    confidence=0.95
                )
                entities.append(entity_info)
                entity_id_map[temp_id] = db_id
                id_to_entity[db_id] = entity_info

            # 4. 将测试点存入数据库（可选，并关联实体）
            test_point_objs = []
            for tp in ai_test_points:
                # 查找关联的技能实体（通过名称匹配，简单处理）
                related_entity_id = None
                skill_name = tp.get("skill_name")
                if skill_name:
                    for entity in entities:
                        if entity.name == skill_name:
                            related_entity_id = entity_id_map.get(entity.id)
                            break

                db_tp = {
                    "entity_id": related_entity_id,
                    "task_id": task_id,
                    "category": tp.get("category", "未知"),
                    "description": tp.get("description", ""),
                    "expected_result": tp.get("expected_result", ""),
                    "test_steps": tp.get("test_steps"),
                    "priority": tp.get("priority", "medium"),
                    "confidence": 0.9
                }
                try:
                    await db.save_test_point(db_tp)
                except Exception as e:
                    logger.warning(f"保存测试点失败: {e}")
                test_point_objs.append(TestPoint(**tp))  # 假设 tp 已包含必要字段

            # 5. 生成建议
            suggestions = self._generate_suggestions(page_data, entities)
            if test_point_objs:
                suggestions.append(f"AI 生成 {len(test_point_objs)} 个测试点")

            # 6. 构建响应
            response = AnalyzeResponse(
                task_id=task_id,
                title=page_data["title"],
                url=url,
                data_type=page_data["type"],
                entities=entities,
                relations=[],  # 关系提取暂未集成，可留空
                raw_html=page_data.get("html") if include_raw else None,
                raw_text=page_data.get("text") if include_raw else None,
                suggestions=suggestions,
                test_points=test_point_objs,
                analyze_time=datetime.now()
            )

            # 7. 保存任务记录
            try:
                await self._save_analysis_task(task_id, url, depth, response)
            except Exception as e:
                logger.warning(f"保存任务记录失败: {e}")

            logger.success(f"分析完成: {task_id}，AI 提取到 {len(entities)} 个技能，{len(test_point_objs)} 个测试点")
            return response

        except Exception as e:
            logger.error(f"分析失败 {url}: {e}")
            raise

    async def _save_analysis_task(self, task_id: str, url: str, depth: int, response: AnalyzeResponse):
        task_data = {
            "task_id": task_id,
            "title": response.title,
            "url": url,
            "data_type": response.data_type,
            "entities_count": len(response.entities),
            "test_points_count": len(response.test_points),
            "suggestions": response.suggestions
        }
        query = """
            INSERT INTO analysis_tasks (task_id, url, depth, status, result, completed_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, NOW())
        """
        try:
            await db.execute(
                query,
                task_id,
                url,
                depth,
                "completed",
                json.dumps(task_data, ensure_ascii=False)
            )
        except Exception as e:
            logger.warning(f"保存任务记录失败: {e}")

    def _generate_suggestions(self, page_data: Dict, entities: List[EntityInfo]) -> List[str]:
        suggestions = []
        page_type = page_data.get("type", "unknown")
        if page_type == "skill":
            if len(entities) == 0:
                suggestions.append("未提取到技能实体，可能需要手动补充")
            else:
                suggestions.append(f"AI 提取到 {len(entities)} 个技能")
        # 其他类型可类似处理
        return suggestions[:4]

    async def get_task(self, task_id: str) -> Optional[AnalyzeResponse]:
        return None  # 暂不实现

    async def update_entity(self, task_id: str, entity_id: str, new_data: Dict) -> Optional[AnalyzeResponse]:
        try:
            success = await db.update_entity_attributes(entity_id, new_data)
            if success:
                logger.info(f"实体更新成功: {entity_id}")
                return None
            else:
                logger.warning(f"实体不存在: {entity_id}")
                return None
        except Exception as e:
            logger.error(f"更新实体失败: {e}")
            return None

    async def get_entities_by_type(self, entity_type: str, limit: int = 100) -> List[Dict]:
        return await db.get_entities_by_type(entity_type, limit)

    async def search_entities(self, keyword: str, entity_type: Optional[str] = None) -> List[Dict]:
        return await db.search_entities(keyword, entity_type)

    async def analyze_url_async(self, url: str, depth: int, include_raw: bool, task_id: str, callback):
        """异步执行分析，完成后调用回调函数"""
        try:
            result = await self.analyze_url(url, depth, include_raw)
            await callback(task_id, result, None)
        except Exception as e:
            await callback(task_id, None, e)

analysis_service = AnalysisService()