# app/parsers/relation_extractor.py
from typing import List, Dict, Any
import re

class RelationExtractor:
    """关系提取器"""
    
    def __init__(self):
        self.relation_patterns = {
            "has_skill": [r"拥有技能", r"学习技能", r"掌握"],
            "drops_from": [r"掉落于", r"获得自", r"来源"],
            "requires": [r"需要", r"需求", r"条件"],
            "evolves_to": [r"进化", r"进阶", r"升级为"],
        }
        
    def extract_relations(self, text: str, entities: List[Dict]) -> List[Dict]:
        """提取实体间的关系"""
        relations = []
        
        # 简单的共现关系
        for i, e1 in enumerate(entities):
            for e2 in entities[i+1:]:
                # 检查是否在上下文中共现
                if self._check_cooccurrence(text, e1["name"], e2["name"]):
                    relation_type = self._determine_relation(text, e1["name"], e2["name"])
                    if relation_type:
                        relations.append({
                            "source": e1["name"],
                            "target": e2["name"],
                            "relation_type": relation_type,
                            "confidence": 0.7
                        })
                        
        return relations
        
    def _check_cooccurrence(self, text: str, name1: str, name2: str, window: int = 100) -> bool:
        """检查两个实体是否在上下文中共现"""
        pos1 = text.find(name1)
        pos2 = text.find(name2)
        
        if pos1 == -1 or pos2 == -1:
            return False
            
        return abs(pos1 - pos2) < window
        
    def _determine_relation(self, text: str, name1: str, name2: str) -> str:
        """判断关系类型"""
        context = self._extract_context(text, name1, name2)
        
        for rel_type, patterns in self.relation_patterns.items():
            for pattern in patterns:
                if pattern in context:
                    return rel_type
                    
        return "related_to"
        
    def _extract_context(self, text: str, name1: str, name2: str, window: int = 50) -> str:
        """提取包含两个实体的上下文"""
        pos1 = text.find(name1)
        pos2 = text.find(name2)
        
        start = min(pos1, pos2)
        end = max(pos1 + len(name1), pos2 + len(name2))
        
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        
        return text[context_start:context_end]