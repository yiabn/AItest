# app/services/analysis_service.py
import uuid
from typing import Dict, List, Set, Optional
from urllib.parse import urljoin, urlparse

# 数据库/模型导入
from app.db.session import db_session
from app.models.entity import Entity
from app.models.relation import Relation
from app.models.page_snapshots import PageSnapshot  # 导入页面快照表（若有）
# 爬虫/工具类导入
from app.crawlers.m99_crawler import M99Crawler
from app.utils.entity_utils import get_or_create_entity_id

class AnalysisService:
    """分析服务：支持深度爬取+返回原始内容"""
    def __init__(self):
        self.crawler = M99Crawler()
        self.crawled_urls: Set[str] = set()  # 记录已爬取URL

    def analyze_url(
        self, 
        url: str, 
        depth: int = 1, 
        include_raw: bool = False  # 新增：是否返回原始HTML
    ) -> Dict:
        """
        分析URL（支持深度爬取+返回原始内容）
        :param url: 目标URL
        :param depth: 爬取深度（1=仅当前页面）
        :param include_raw: 是否返回原始HTML/快照
        :return: 解析结果（含/不含原始内容）
        """
        if depth > 3:
            depth = 3
        if url in self.crawled_urls:
            return {
                "entities": [], 
                "relations": [], 
                "page_type": "unknown", 
                "message": "URL已爬取",
                "raw_html": "" if include_raw else None
            }
        self.crawled_urls.add(url)

        # 1. 爬取并解析当前页面
        crawl_result = self.crawler.crawl_and_parse(url)
        entities = crawl_result["entities"]
        relations = crawl_result["relations"]
        page_type = crawl_result["page_type"]
        raw_html = crawl_result.get("html", "")  # 获取原始HTML

        # 2. 入库实体/关系/页面快照
        self._save_entities_and_relations(entities, relations)
        if include_raw:
            self._save_page_snapshot(url, raw_html)  # 保存页面快照

        # 3. 深度爬取（若depth>1）
        if depth > 1:
            child_urls = self._extract_child_urls(url, raw_html)
            for child_url in child_urls:
                child_result = self.analyze_url(child_url, depth=depth-1, include_raw=include_raw)
                entities.extend(child_result["entities"])
                relations.extend(child_result["relations"])

        # 4. 去重
        entities = self._deduplicate_entities(entities)
        relations = self._deduplicate_relations(relations)

        # 5. 构造返回结果（含/不含原始内容）
        result = {
            "page_type": page_type,
            "entities": entities,
            "relations": relations,
            "crawled_urls": list(self.crawled_urls),
            "message": f"成功解析：{len(entities)}个实体，{len(relations)}个关系"
        }
        # 若include_raw=True，添加原始HTML
        if include_raw:
            result["raw_html"] = raw_html
            # 可选：返回快照ID
            snapshot = db_session.query(PageSnapshot).filter(PageSnapshot.url == url).first()
            if snapshot:
                result["snapshot_id"] = str(snapshot.id)

        return result

    def _save_entities_and_relations(self, entities: List[Dict], relations: List[Dict]):
        """入库实体和关系（原有逻辑）"""
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
        """保存页面快照到数据库"""
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
        """提取子链接（原有逻辑）"""
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
        """实体去重（原有逻辑）"""
        seen = set()
        unique_entities = []
        for entity in entities:
            key = (entity["name"], entity["type"])
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        return unique_entities

    def _deduplicate_relations(self, relations: List[Dict]) -> List[Dict]:
        """关系去重（原有逻辑）"""
        seen = set()
        unique_relations = []
        for relation in relations:
            key = (relation["source_name"], relation["target_name"], relation["relation_type"])
            if key not in seen:
                seen.add(key)
                unique_relations.append(relation)
        return unique_relations