# backend/parsers/equipment_parser.py
from .base_parser import BaseGameParser
from typing import Tuple, List, Dict

class EquipmentParser(BaseGameParser):
    """装备页面专用解析器：提取装备属性+关联关系"""
    def parse(self) -> Tuple[List[Dict], List[Dict]]:
        # 1. 提取装备基础信息
        equip_name = self.extract_text("h1.equip-name", "未知装备")
        equip_type = self.extract_text(".equip-type", "普通装备")
        
        # 2. 提取装备属性（表格）
        equip_attrs = self.extract_table(".equip-attr-table")
        normalized_attrs = {}
        for attr in equip_attrs:
            key = self.normalize_attr_key(attr["key"], "equipment")
            normalized_attrs[key] = attr["value"]
        
        # 3. 构建装备实体
        equip_entity = {
            "name": equip_name,
            "type": "equipment",
            "attributes": normalized_attrs,
            "category": equip_type,
            "source_url": self.url
        }
        self.entities.append(equip_entity)

        # 4. 提取关系（装备→适用职业/装备→获取方式）
        apply_career = self.extract_text(".apply-career", "通用")
        if apply_career != "通用":
            self.relations.append({
                "source_name": equip_name,
                "source_type": "equipment",
                "target_name": apply_career,
                "target_type": "career",
                "relation_type": "apply_to",
                "description": f"{equip_name}适用于{apply_career}"
            })

        return self.entities, self.relations