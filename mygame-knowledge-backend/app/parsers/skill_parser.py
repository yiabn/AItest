# app/parsers/skill_parser.py
from .base_parser import BaseGameParser  # 相对导入（同目录）
from typing import Tuple, List, Dict

# 修复工具类导入路径
from app.utils.term_dict import term_mapping

class SkillParser(BaseGameParser):
    """技能页面专用解析器：提取技能属性+关联关系"""
    def parse(self) -> Tuple[List[Dict], List[Dict]]:
        # 1. 提取技能基础信息
        skill_name = self.extract_text("h1.skill-name", "未知技能")
        skill_category = self.extract_text(".skill-category", "普通技能")
        
        # 2. 提取技能核心属性（表格/列表）
        skill_attrs = self.extract_table(".skill-attr-table")
        # 标准化属性名（如“CD”→“冷却时间”）
        normalized_attrs = {}
        for attr in skill_attrs:
            key = term_mapping.get("skill", {}).get(attr["key"], attr["key"])
            normalized_attrs[key] = attr["value"]
        
        # 3. 构建技能实体
        skill_entity = {
            "name": skill_name,
            "type": "skill",
            "attributes": normalized_attrs,
            "category": skill_category,
            "source_url": self.url
        }
        self.entities.append(skill_entity)

        # 4. 提取关系（如“技能所属幻兽/职业”）
        # 从页面关联链接提取（示例：<a class="related-pet" href="/pet/123">幻兽A</a>）
        related_pets = self.extract_links(".related-pet a")
        for pet_name, pet_url in related_pets:
            if pet_name and pet_url:
                self.relations.append({
                    "source_name": pet_name,    # 源实体名称（后续转ID）
                    "source_type": "pet",       # 源实体类型
                    "target_name": skill_name,  # 目标实体名称
                    "target_type": "skill",     # 目标实体类型
                    "relation_type": "has_skill",  # 关系类型
                    "description": f"{pet_name}拥有技能{skill_name}"
                })

        # 5. 提取技能间关联（如“技能A触发技能B”）
        related_skills = self.extract_links(".related-skill a")
        for rel_skill_name, rel_skill_url in related_skills:
            if rel_skill_name and rel_skill_url:
                self.relations.append({
                    "source_name": skill_name,
                    "source_type": "skill",
                    "target_name": rel_skill_name,
                    "target_type": "skill",
                    "relation_type": "trigger_skill",
                    "description": f"{skill_name}可触发{rel_skill_name}"
                })

        return self.entities, self.relations