# app/services/analysis_service.py
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
import json

from app.crawlers.m99_crawler import M99Crawler
from app.parsers.entity_extractor import GameEntityExtractor
from app.models.response import AnalyzeResponse, EntityInfo, RelationInfo
from app.database import db  # 导入数据库实例

class AnalysisService:
    """分析服务 - 支持数据库持久化"""
    
    def __init__(self):
        self.crawler = M99Crawler()
        self.extractor = GameEntityExtractor()
        # 移除内存中的 tasks 字典，改用数据库存储
        # self.tasks: Dict[str, AnalyzeResponse] = {}
        
    async def analyze_url(self, url: str, depth: int = 1, include_raw: bool = False) -> AnalyzeResponse:
        """分析URL并将结果存入数据库"""
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
            
            # 3. 提取实体
            entities_data = self.extractor.extract_entities(
                page_data["text"], 
                page_data["type"]
            )
            
            # 4. 转换为实体对象并存入数据库
            entities = []
            entity_id_map = {}  # 用于记录临时索引和数据库ID的映射
            
            for idx, e in enumerate(entities_data):
                # 创建实体对象（用于返回给前端）
                entity_info = EntityInfo(
                    id=f"{task_id}_entity_{idx}",
                    name=e["name"],
                    type=e["type"],
                    attributes=e.get("attributes", {}),
                    confidence=e.get("confidence", 0.8)
                )
                entities.append(entity_info)
                
                # 存入数据库
                try:
                    db_entity_id = await db.create_entity(
                        name=e["name"],
                        type=e["type"],
                        source_url=url,
                        attributes=e.get("attributes", {}),
                        confidence=e.get("confidence", 0.8),
                        version="1.0"
                    )
                    # 记录映射关系（临时索引 -> 数据库ID）
                    entity_id_map[f"{task_id}_entity_{idx}"] = db_entity_id
                    logger.debug(f"实体已存入数据库: {e['name']} -> {db_entity_id}")
                except Exception as e:
                    logger.error(f"保存实体到数据库失败: {e}")
            
            # 5. 生成建议
            suggestions = self._generate_suggestions(page_data, entities)
            
            # 6. 构建响应
            response = AnalyzeResponse(
                task_id=task_id,
                title=page_data["title"],
                url=url,
                data_type=page_data["type"],
                entities=entities,
                relations=[],  # 暂时留空
                raw_html=page_data.get("html") if include_raw else None,
                raw_text=page_data.get("text") if include_raw else None,
                suggestions=suggestions,
                analyze_time=datetime.now()
            )
            
            # 7. 保存分析任务记录
            try:
                await self._save_analysis_task(task_id, url, depth, response)
            except Exception as e:
                logger.error(f"保存任务记录失败: {e}")
            
            logger.success(f"分析完成: {task_id}，已保存 {len(entities)} 个实体到数据库")
            return response
            
        except Exception as e:
            logger.error(f"分析失败 {url}: {e}")
            raise
    
    async def _save_analysis_task(self, task_id: str, url: str, depth: int, response: AnalyzeResponse):
        """保存分析任务记录"""
        # 将响应对象转换为可序列化的字典
        task_data = {
            "task_id": task_id,
            "title": response.title,
            "url": url,
            "data_type": response.data_type,
            "entities_count": len(response.entities),
            "suggestions": response.suggestions
        }
        
        # 这里可以创建 analysis_tasks 表来存储任务记录
        # 暂时用 execute 直接插入
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
            # 如果表不存在，记录警告但不中断流程
            logger.warning(f"保存任务记录失败（可能表不存在）: {e}")
    
    def _build_entities(self, entities_data: List[Dict], task_id: str) -> List[EntityInfo]:
        """构建实体对象列表"""
        entities = []
        for idx, e in enumerate(entities_data):
            entity = EntityInfo(
                id=f"{task_id}_entity_{idx}",
                name=e.get("name", "未知"),
                type=e.get("type", "unknown"),
                attributes=e.get("attributes", {}),
                confidence=e.get("confidence", 0.8)
            )
            entities.append(entity)
        return entities
    
    def _generate_suggestions(self, page_data: Dict, entities: List[EntityInfo]) -> List[str]:
        """生成分析建议"""
        suggestions = []
        
        # 根据页面类型生成建议
        page_type = page_data.get("type", "unknown")
        
        if page_type == "pet":
            if len(entities) == 0:
                suggestions.append("未提取到幻兽实体，可能需要手动补充")
            else:
                suggestions.append(f"检测到 {len(entities)} 个幻兽实体，建议补充幻兽技能")
                
        elif page_type == "equipment":
            suggestions.append("建议补充装备获取方式和掉落来源")
            
        elif page_type == "skill":
            suggestions.append("建议补充技能升级效果和消耗")
            
        # 检查数据完整性
        if page_data.get("text"):
            text_len = len(page_data["text"])
            if text_len < 100:
                suggestions.append("页面内容较少，可能需要补充详细信息")
        
        # 添加数据库相关的建议
        suggestions.append("数据已自动保存到知识库，可通过历史记录查看")
                
        return suggestions[:4]  # 最多4条建议
    
    async def get_task(self, task_id: str) -> Optional[AnalyzeResponse]:
        """从数据库获取任务结果"""
        try:
            # 从 analysis_tasks 表查询
            query = "SELECT result FROM analysis_tasks WHERE task_id = $1"
            row = await db.fetchrow(query, task_id)
            
            if row and row['result']:
                # 这里需要将存储的数据转换回 AnalyzeResponse 对象
                # 简单起见，先返回 None，后续完善
                logger.info(f"找到任务记录: {task_id}")
                # TODO: 实现从存储数据重建响应对象
                return None
            else:
                logger.warning(f"任务不存在: {task_id}")
                return None
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            return None
    
    async def update_entity(self, task_id: str, entity_id: str, new_data: Dict) -> Optional[AnalyzeResponse]:
        """更新实体信息（同时更新数据库）"""
        try:
            # 从 entity_id 中提取临时ID格式: task_id_entity_index
            parts = entity_id.split('_')
            if len(parts) >= 3 and parts[0] == task_id:
                # 这是临时ID，需要找到对应的数据库实体
                # 实际上我们需要在创建实体时就建立映射关系
                # 这里简化处理，先不实现
                logger.warning(f"暂不支持通过临时ID更新实体: {entity_id}")
                return None
            else:
                # 可能是数据库实体的UUID
                # 更新数据库中的实体属性
                success = await db.update_entity_attributes(entity_id, new_data)
                if success:
                    logger.info(f"实体更新成功: {entity_id}")
                    # 返回更新后的实体信息
                    # 简化处理，先返回 None
                    return None
                else:
                    logger.warning(f"实体不存在: {entity_id}")
                    return None
        except Exception as e:
            logger.error(f"更新实体失败: {e}")
            return None
    
    async def get_entities_by_type(self, entity_type: str, limit: int = 100) -> List[Dict]:
        """根据类型获取实体列表"""
        return await db.get_entities_by_type(entity_type, limit)
    
    async def search_entities(self, keyword: str, entity_type: Optional[str] = None) -> List[Dict]:
        """搜索实体"""
        return await db.search_entities(keyword, entity_type)


# 为了保持向后兼容，创建服务实例
analysis_service = AnalysisService()