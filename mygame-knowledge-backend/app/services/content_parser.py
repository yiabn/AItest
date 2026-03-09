# app/services/content_parser.py
import re
import json
from typing import List, Dict, Tuple
from docx import Document
import PyPDF2
from bs4 import BeautifulSoup
from app.db.session import db_session
from app.models.entity import Entity
from app.models.relation import Relation
from app.models.page_snapshots import PageSnapshot, ContentType

class ContentParser:
    """通用内容解析器：解析文档/页面，提取实体+结构化数据，填充relations表"""
    
    def __init__(self):
        # 通用正则规则（适配任意内容的关键数值提取）
        self.patterns = {
            "冷却时间": re.compile(r"冷却时间[：:](\d+(?:\.\d+)?)[秒分钟小时]"),
            "数值": re.compile(r"(\d+(?:\.\d+)?)[个元次天%]"),
            "奖励": re.compile(r"奖励[：:](.*?)(；|。|$)"),
            "规则": re.compile(r"规则[：:](.*?)(；|。|$)"),
            "任务名称": re.compile(r"任务[：:](.*?)(；|。|$)")
        }

    # ========== 问题1：复杂内容解析（提取关键数值） ==========
    def parse_raw_content(self, content: str, content_type: str, source: str) -> Tuple[List[Dict], List[Dict]]:
        """
        解析任意内容（HTML/TXT/DOCX/PDF），提取实体和关系
        :param content: 原始内容
        :param content_type: 内容类型（html/txt/docx/pdf）
        :param source: 来源（URL/文件路径）
        :return: 实体列表、关系列表
        """
        # 第一步：提取纯文本（适配不同内容类型）
        parsed_text = self._extract_text(content, content_type)
        
        # 第二步：提取实体（解决复杂内容解析弱）
        entities = self._extract_entities(parsed_text, source)
        
        # 第三步：提取关系（解决relations表为空）
        relations = self._extract_relations(entities, parsed_text)
        
        return entities, relations

    def _extract_text(self, content: str, content_type: str) -> str:
        """提取不同类型内容的纯文本"""
        if content_type == ContentType.HTML.value:
            soup = BeautifulSoup(content, "lxml")
            return soup.get_text(separator="\n", strip=True)
        elif content_type == ContentType.DOCX.value:
            doc = Document(content)  # content为docx文件路径
            return "\n".join([para.text for para in doc.paragraphs])
        elif content_type == ContentType.PDF.value:
            with open(content, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                return "\n".join([page.extract_text() for page in reader.pages])
        elif content_type == ContentType.TXT.value:
            return content
        else:
            return content

    def _extract_entities(self, text: str, source: str) -> List[Dict]:
        """提取实体（解决复杂内容解析弱）"""
        entities = []
        # 1. 基于正则提取关键实体
        for entity_type, pattern in self.patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                entity_name = match.strip()
                # 构造实体（贴合你的Entity模型）
                entity = {
                    "name": entity_name,
                    "type": entity_type,
                    "content": match,
                    "attributes": {"source": source},
                    "source": source,
                    "confidence": 1.0
                }
                entities.append(entity)
        # 2. 去重
        seen = {(e["name"], e["type"]) for e in entities}
        unique_entities = [e for e in entities if (e["name"], e["type"]) in seen and not seen.remove((e["name"], e["type"]))]
        return unique_entities

    # ========== 问题3：关系提取（解决relations表为空） ==========
    def _extract_relations(self, entities: List[Dict], text: str) -> List[Dict]:
        """提取实体关系（填充relations表）"""
        relations = []
        # 1. 规则式关系提取（通用适配任意内容）
        for entity in entities:
            if entity["type"] == "任务名称":
                # 任务-包含-奖励
                reward_match = self.patterns["奖励"].search(text)
                if reward_match:
                    relations.append({
                        "head_entity_name": entity["name"],
                        "head_entity_type": "任务名称",
                        "relation_type": "包含奖励",
                        "tail_entity_name": reward_match.group(1).strip(),
                        "tail_entity_type": "奖励",
                        "description": f"{entity['name']}的奖励为{reward_match.group(1).strip()}"
                    })
            if entity["type"] == "规则":
                # 规则-描述-数值
                num_match = self.patterns["数值"].search(text)
                if num_match:
                    relations.append({
                        "head_entity_name": entity["name"],
                        "head_entity_type": "规则",
                        "relation_type": "包含数值",
                        "tail_entity_name": num_match.group(1).strip(),
                        "tail_entity_type": "数值",
                        "description": f"{entity['name']}包含数值{num_match.group(1).strip()}"
                    })
        return relations

    # ========== 问题2：结构化数据提取（表格/列表，解决属性缺失） ==========
    def parse_structured_data(self, content: str, content_type: str, source: str) -> List[Dict]:
        """
        提取表格/列表等结构化数据（解决属性缺失）
        :param content: 原始内容（HTML/文档）
        :param content_type: 内容类型
        :param source: 来源
        :return: 结构化实体列表
        """
        structured_entities = []
        # 1. HTML表格提取
        if content_type == ContentType.HTML.value:
            soup = BeautifulSoup(content, "lxml")
            tables = soup.find_all("table")
            for table in tables:
                rows = table.find_all("tr")
                headers = [th.text.strip() for th in rows[0].find_all("th")] if rows else []
                for row in rows[1:]:
                    cells = [td.text.strip() for td in row.find_all("td")]
                    if len(cells) != len(headers):
                        continue
                    # 每行作为一个实体，列作为属性（解决属性缺失）
                    row_entity = {
                        "name": f"表格行_{source[-10:]}",
                        "type": "表格行",
                        "content": ", ".join(cells),
                        "attributes": dict(zip(headers, cells)),  # 完整属性，不缺失
                        "source": source,
                        "confidence": 1.0
                    }
                    structured_entities.append(row_entity)
        # 2. 文档列表提取（适配DOCX/TXT）
        elif content_type in [ContentType.DOCX.value, ContentType.TXT.value]:
            lines = self._extract_text(content, content_type).split("\n")
            for i, line in enumerate(lines):
                if line.strip() and "- " in line:  # 列表项（如：- 奖励：500元）
                    list_entity = {
                        "name": f"列表项_{i}",
                        "type": "列表项",
                        "content": line.strip(),
                        "attributes": self._parse_list_attributes(line.strip()),
                        "source": source,
                        "confidence": 1.0
                    }
                    structured_entities.append(list_entity)
        return structured_entities

    def _parse_list_attributes(self, line: str) -> Dict:
        """解析列表项属性（避免缺失）"""
        attrs = {}
        # 提取键值对（如：奖励：500元 → {"奖励": "500元"}）
        kv_pattern = re.compile(r"([^：:]+)[：:](.*)")
        match = kv_pattern.search(line)
        if match:
            attrs[match.group(1).strip()] = match.group(2).strip()
        return attrs

    # ========== 入库：保存实体和关系到PostgreSQL ==========
    def save_to_db(self, entities: List[Dict], relations: List[Dict], content: str, content_type: str, source: str):
        """保存解析结果到数据库（贴合你的模型）"""
        try:
            # 1. 保存页面/文档快照
            snapshot = PageSnapshot(
                source=source,
                content_type=ContentType(content_type),
                raw_content=content,
                parsed_content=self._extract_text(content, content_type),
                parse_status="parsed"
            )
            db_session.add(snapshot)

            # 2. 保存实体（避免重复）
            for entity_data in entities:
                existing = db_session.query(Entity).filter(
                    Entity.name == entity_data["name"],
                    Entity.type == entity_data["type"],
                    Entity.source == entity_data["source"]
                ).first()
                if not existing:
                    entity = Entity(**entity_data)
                    db_session.add(entity)

            # 3. 保存关系（解决relations表为空）
            for relation_data in relations:
                existing = db_session.query(Relation).filter(
                    Relation.head_entity_name == relation_data["head_entity_name"],
                    Relation.relation_type == relation_data["relation_type"],
                    Relation.tail_entity_name == relation_data["tail_entity_name"]
                ).first()
                if not existing:
                    relation = Relation(**relation_data)
                    db_session.add(relation)

            db_session.commit()
            print(f"✅ 解析结果已入库：实体{len(entities)}个，关系{len(relations)}个")
        except Exception as e:
            db_session.rollback()
            raise Exception(f"入库失败：{str(e)}")