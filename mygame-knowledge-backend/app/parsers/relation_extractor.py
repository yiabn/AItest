# app/parsers/relation_extractor.py
import re
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from loguru import logger

class RelationExtractor:
    """从页面中提取实体间的关系"""

    # 常见关系类型及其关键词
    RELATION_PATTERNS = {
        'has_skill': ['拥有技能', '可学习', '技能'],
        'drops_from': ['掉落于', '掉落自', '获得自'],
        'rewards': ['奖励', '获得', '完成任务可得'],
        'located_in': ['位于', '出现在', '出没于'],
        'requires': ['需要', '要求', '前置'],
        'evolves_to': ['进化', '进阶', '升级为'],
        'part_of': ['属于', '归属于'],
    }

    def __init__(self):
        pass

    def extract_relations(
        self,
        soup: BeautifulSoup,
        text: str,
        entities: List[Dict],
        entity_id_map: Dict[str, str]
    ) -> List[Dict]:
        """
        从页面中提取关系
        :param soup: 解析后的 BeautifulSoup 对象
        :param text: 页面纯文本
        :param entities: 实体列表（包含临时ID和名称、类型等）
        :param entity_id_map: 临时ID -> 数据库UUID 的映射
        :return: 关系列表，每个关系为 dict {source_id, target_id, relation_type, properties, confidence}
        """
        relations = []
        # 将实体按名称索引，便于查找
        name_to_temp_id = {e['name']: e['id'] for e in entities}
        temp_id_to_uuid = entity_id_map

        # 1. 从超链接中提取关系
        links_relations = self._extract_from_links(soup, name_to_temp_id, temp_id_to_uuid)
        relations.extend(links_relations)

        # 2. 从文本中提取关系
        text_relations = self._extract_from_text(text, name_to_temp_id, temp_id_to_uuid)
        relations.extend(text_relations)

        # 3. 从实体属性中提取关系（例如技能列表）
        attr_relations = self._extract_from_attributes(entities, name_to_temp_id, temp_id_to_uuid)
        relations.extend(attr_relations)

        # 去重（同一对实体同一关系只保留一次）
        seen = set()
        unique_relations = []
        for rel in relations:
            key = (rel['source_id'], rel['target_id'], rel['relation_type'])
            if key not in seen:
                seen.add(key)
                unique_relations.append(rel)
        return unique_relations

    def _extract_from_links(
        self,
        soup: BeautifulSoup,
        name_to_temp_id: Dict[str, str],
        temp_id_to_uuid: Dict[str, str]
    ) -> List[Dict]:
        """分析页面中的超链接，如果链接文本是已知实体名，则建立关系"""
        relations = []
        for a in soup.find_all('a', href=True):
            link_text = a.get_text().strip()
            if link_text in name_to_temp_id:
                # 假设链接指向的是目标实体，当前页面实体是源实体？
                # 这里需要更精细的逻辑：通常页面本身的实体是源，链接到的实体是目标
                # 但我们不知道当前页面的主实体是哪个。一种简单方法：如果页面中只有一个主要实体（如幻兽详情页），则那个实体就是源。
                # 但为了简化，我们可以先不处理这种，或者作为双向关系？暂时跳过，后续优化。
                # 更好的方式：在解析页面时，我们已经有了主实体（如第一个实体），可以用它作为源。
                pass
        return relations

    def _extract_from_text(
        self,
        text: str,
        name_to_temp_id: Dict[str, str],
        temp_id_to_uuid: Dict[str, str]
    ) -> List[Dict]:
        """分析文本，根据关键词和实体共现提取关系"""
        relations = []
        entity_names = list(name_to_temp_id.keys())

        # 遍历所有关系类型
        for rel_type, keywords in self.RELATION_PATTERNS.items():
            for keyword in keywords:
                # 在文本中查找包含关键词的句子
                # 简单起见，我们查找关键词附近一定范围内的实体对
                pattern = r'([^。]*?({})[^。]*?)'.format('|'.join(keywords))
                matches = re.finditer(pattern, text, re.MULTILINE)
                for match in matches:
                    sentence = match.group(0)
                    # 找出句子中出现的所有实体
                    found_entities = [name for name in entity_names if name in sentence]
                    # 如果有两个及以上实体，则考虑它们之间的关系
                    if len(found_entities) >= 2:
                        # 假设第一个是源，第二个是目标（需要更智能的判断）
                        source_name = found_entities[0]
                        target_name = found_entities[1]
                        # 检查关键词是否在两个实体之间出现（简单规则）
                        if source_name in sentence and target_name in sentence:
                            src_temp = name_to_temp_id[source_name]
                            tgt_temp = name_to_temp_id[target_name]
                            if src_temp in temp_id_to_uuid and tgt_temp in temp_id_to_uuid:
                                relations.append({
                                    'source_id': temp_id_to_uuid[src_temp],
                                    'target_id': temp_id_to_uuid[tgt_temp],
                                    'relation_type': rel_type,
                                    'properties': {'extracted_from': 'text'},
                                    'confidence': 0.7
                                })
        return relations

    def _extract_from_attributes(
        self,
        entities: List[Dict],
        name_to_temp_id: Dict[str, str],
        temp_id_to_uuid: Dict[str, str]
    ) -> List[Dict]:
        """从实体的属性中提取关系，比如某个实体拥有技能列表"""
        relations = []
        # 遍历每个实体，检查其 attributes 中是否包含其他实体的名称
        for entity in entities:
            src_temp = entity['id']
            if src_temp not in temp_id_to_uuid:
                continue
            attrs = entity.get('attributes', {})
            # 例如，如果属性中包含 '技能' 且值是列表或字符串
            for key, value in attrs.items():
                if '技能' in key or key in ['skills', '技能']:
                    # 将值视为技能名称列表（可能是字符串，需分割）
                    if isinstance(value, str):
                        # 可能包含多个技能名，用分隔符分割
                        skill_names = re.split(r'[、，, \n]+', value)
                    elif isinstance(value, list):
                        skill_names = value
                    else:
                        continue
                    for skill_name in skill_names:
                        if skill_name in name_to_temp_id:
                            tgt_temp = name_to_temp_id[skill_name]
                            if tgt_temp in temp_id_to_uuid:
                                relations.append({
                                    'source_id': temp_id_to_uuid[src_temp],
                                    'target_id': temp_id_to_uuid[tgt_temp],
                                    'relation_type': 'has_skill',
                                    'properties': {},
                                    'confidence': 0.9
                                })
        return relations