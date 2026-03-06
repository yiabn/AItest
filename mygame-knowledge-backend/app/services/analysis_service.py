# app/services/analysis_service.py
import uuid
from typing import Dict, List, Set, Optional
from urllib.parse import urljoin, urlparse
import asyncio
from datetime import datetime
from app.db.session import db_session
from app.models.entity import Entity
from app.models.relation import Relation
from app.models.page_snapshots import PageSnapshot
from app.crawlers.m99_crawler import M99Crawler
from app.utils.entity_utils import get_or_create_entity_id

# 新增：任务存储（简易版，生产环境建议用Redis/数据库）
TASK_STORAGE = {}

class AnalysisService:
    """分析服务：支持深度爬取+返回原始内容"""
    def __init__(self):
        self.crawler = M99Crawler()
        self.crawled_urls: Set[str] = set()

    async def analyze_url(
        self, 
        url: str, 
        depth: int = 1, 
        include_raw: bool = False
    ) -> Dict:
        # 生成任务ID
        task_id = str(uuid.uuid4())
        self.crawled_urls.clear()  # 每次分析重置已爬取URL
        
        try:
            # 异步执行爬取（优化：避免线程池嵌套）
            crawl_result = await asyncio.to_thread(
                self._crawl_and_analyze, url, depth, include_raw
            )
            
            # 构造符合AnalyzeResponse的返回结构
            title = self._extract_title(crawl_result.get("raw_html", "")) or f"分析结果-{task_id[:8]}"
            data_type = crawl_result.get("page_type", "general")
            
            # 转换实体格式（适配Response模型）
            entities = [
                {
                    "id": str(get_or_create_entity_id(e["name"], e["type"])),
                    "name": e["name"],
                    "type": e["type"],
                    "attributes": e.get("attributes", {}),
                    "confidence": 1.0
                } for e in crawl_result["entities"]
            ]
            
            # 转换关系格式
            relations = [
                {
                    "source": r["source_name"],
                    "target": r["target_name"],
                    "relation_type": r["relation_type"],
                    "properties": r.get("properties", {})
                } for r in crawl_result["relations"]
            ]
            
            # 生成AI建议
            suggestions = self._generate_suggestions(entities, data_type)
            
            # 组装最终结果
            result = {
                "task_id": task_id,
                "title": title,
                "url": url,
                "data_type": data_type,
                "entities": entities,
                "relations": relations,
                "raw_html": crawl_result.get("raw_html") if include_raw else None,
                "raw_text": self._extract_text(crawl_result.get("raw_html", "")),
                "suggestions": suggestions,
                "analyze_time": datetime.now(),
                "source": "魔域官方资料库"
            }
            
            # 保存任务结果
            TASK_STORAGE[task_id] = result
            return result
            
        except Exception as e:
            raise Exception(f"分析失败: {str(e)}")

    def _crawl_and_analyze(self, url: str, depth: int, include_raw: bool) -> Dict:
        """同步爬取逻辑（单线程）"""
        if depth > 3:
            depth = 3
        if url in self.crawled_urls:
            return {"entities": [], "relations": [], "page_type": "unknown", "raw_html": ""}
        
        self.crawled_urls.add(url)
        # 1. 爬取当前页面
        crawl_result = self.crawler.crawl_and_parse(url)
        entities = crawl_result["entities"]
        relations = crawl_result["relations"]
        page_type = crawl_result["page_type"]
        raw_html = crawl_result.get("html", "")

        # 2. 入库
        self._save_entities_and_relations(entities, relations)
        if include_raw:
            self._save_page_snapshot(url, raw_html)

        # 3. 深度爬取（优化：限制递归深度，避免栈溢出）
        if depth > 1:
            child_urls = self._extract_child_urls(url, raw_html)[:5]  # 限制子链接数量
            for child_url in child_urls:
                child_result = self._crawl_and_analyze(child_url, depth-1, include_raw)
                entities.extend(child_result["entities"])
                relations.extend(child_result["relations"])

        # 4. 去重
        entities = self._deduplicate_entities(entities)
        relations = self._deduplicate_relations(relations)

        return {
            "entities": entities,
            "relations": relations,
            "page_type": page_type,
            "raw_html": raw_html
        }

    # 新增：获取任务结果
    def get_task(self, task_id: str) -> Optional[Dict]:
        return TASK_STORAGE.get(task_id)

    # 新增：提取页面标题
    def _extract_title(self, html: str) -> Optional[str]:
        from bs4 import BeautifulSoup
        if not html:
            return None
        soup = BeautifulSoup(html, "lxml")
        title_tag = soup.find("title")
        return title_tag.get_text().strip() if title_tag else None

    # 新增：提取纯文本
    def _extract_text(self, html: str) -> str:
        from bs4 import BeautifulSoup
        if not html:
            return ""
        soup = BeautifulSoup(html, "lxml")
        return soup.get_text(separator="\n", strip=True)

    # 新增：生成AI建议
    def _generate_suggestions(self, entities: List[Dict], data_type: str) -> List[str]:
        suggestions = []
        type_map = {
            "pet": "幻兽",
            "equipment": "装备",
            "skill": "技能",
            "dungeon": "副本"
        }
        type_name = type_map.get(data_type, "数据")
        
        if not entities:
            suggestions.append(f"未提取到{type_name}实体，建议检查URL是否有效")
        else:
            suggestions.append(f"成功提取{len(entities)}个{type_name}实体，可补充详细属性信息")
            
            # 按类型生成针对性建议
            if data_type == "pet":
                suggestions.append("建议补充幻兽的成长率、亲密度、幻化次数等信息")
            elif data_type == "equipment":
                suggestions.append("建议补充装备的强化等级、追加属性、宝石镶嵌等信息")
            elif data_type == "skill":
                suggestions.append("建议补充技能的冷却时间、释放条件、伤害系数等信息")
        
        suggestions.append("可通过对话功能补充实体缺失的属性信息")
        return suggestions

    # 保留原有方法（_save_entities_and_relations/_save_page_snapshot等）
    def _save_entities_and_relations(self, entities: List[Dict], relations: List[Dict]):
        entity_ids = {}
        for entity in entities:
            existing_entity = db_session.query(Entity).filter(
                Entity.name == entity["name"],
                Entity.type == entity["type"]
            ).first()
            if existing_entity:
                existing_entity.attributes.update(entity.get("attributes", {}))
                existing_entity.source_url = entity.get("source_url", "")
                db_session.commit()
                entity_ids[entity["name"]] = str(existing_entity.id)
            else:
                new_entity = Entity(
                    id=uuid.uuid4(),
                    name=entity["name"],
                    type=entity["type"],
                    attributes=entity.get("attributes", {}),
                    source_url=entity.get("source_url", "")
                )
                db_session.add(new_entity)
                db_session.commit()
                entity_ids[entity["name"]] = str(new_entity.id)

        for relation in relations:
            source_id = entity_ids.get(relation["source_name"]) or get_or_create_entity_id(
                relation["source_name"], relation["source_type"]
            )
            target_id = entity_ids.get(relation["target_name"]) or get_or_create_entity_id(
                relation["target_name"], relation["target_type"]
            )
            existing_relation = db_session.query(Relation).filter(
                Relation.source_id == uuid.UUID(source_id),
                Relation.target_id == uuid.UUID(target_id),
                Relation.relation_type == relation["relation_type"]
            ).first()
            if not existing_relation:
                new_relation = Relation(
                    source_id=uuid.UUID(source_id),
                    target_id=uuid.UUID(target_id),
                    relation_type=relation["relation_type"],
                    description=relation.get("description", "")
                )
                db_session.add(new_relation)
                db_session.commit()

    def _save_page_snapshot(self, url: str, html: str):
        existing_snapshot = db_session.query(PageSnapshot).filter(PageSnapshot.url == url).first()
        if existing_snapshot:
            existing_snapshot.html_content = html
            existing_snapshot.updated_at = datetime.utcnow()
        else:
            new_snapshot = PageSnapshot(
                id=uuid.uuid4(),
                url=url,
                html_content=html,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db_session.add(new_snapshot)
        db_session.commit()

    def _extract_child_urls(self, base_url: str, html: str) -> List[str]:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "lxml")
        child_urls = []
        base_domain = urlparse(base_url).netloc
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            full_url = urljoin(base_url, href)
            if urlparse(full_url).netloc == base_domain and full_url not in self.crawled_urls:
                child_urls.append(full_url)
        return child_urls[:10]

    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        seen = set()
        unique_entities = []
        for entity in entities:
            key = (entity["name"], entity["type"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        return unique_entities

    def _deduplicate_relations(self, relations: List[Dict]) -> List[Dict]:
        seen = set()
        unique_relations = []
        for relation in relations:
            key = (relation["source_name"], relation["target_name"], relation["relation_type"])
            if key not in seen:
                seen.add(key)
                unique_relations.append(relation)
        return unique_relations