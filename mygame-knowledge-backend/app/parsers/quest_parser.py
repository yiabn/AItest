# backend/parsers/quest_parser.py
from .base_parser import BaseGameParser
from typing import Tuple, List, Dict

class QuestParser(BaseGameParser):
    """任务页面专用解析器：提取任务属性+关联奖励/NPC"""
    def parse(self) -> Tuple[List[Dict], List[Dict]]:
        # 1. 提取任务基础信息
        quest_name = self.extract_text("h1.quest-name", "未知任务")
        quest_type = self.extract_text(".quest-type", "日常任务")
        quest_reward = self.extract_text(".quest-reward", "无奖励")
        
        # 2. 提取任务属性
        quest_attrs = {
            "任务类型": quest_type,
            "奖励": quest_reward,
            "接取NPC": self.extract_text(".quest-npc", "未知"),
            "完成条件": self.extract_text(".quest-condition", "无"),
            "等级要求": self.extract_text(".quest-level", "0")
        }

        # 3. 构建任务实体
        quest_entity = {
            "name": quest_name,
            "type": "quest",
            "attributes": quest_attrs,
            "source_url": self.url
        }
        self.entities.append(quest_entity)

        # 4. 提取关系（任务→奖励/任务→NPC）
        # 奖励关系
        if quest_reward != "无奖励":
            self.relations.append({
                "source_name": quest_name,
                "source_type": "quest",
                "target_name": quest_reward,
                "target_type": "equipment" if "装备" in quest_reward else "item",
                "relation_type": "reward_with",
                "description": f"{quest_name}奖励{quest_reward}"
            })
        
        # NPC关系
        npc_name = self.extract_text(".quest-npc", "未知")
        if npc_name != "未知":
            self.relations.append({
                "source_name": quest_name,
                "source_type": "quest",
                "target_name": npc_name,
                "target_type": "npc",
                "relation_type": "accept_from",
                "description": f"{quest_name}从{npc_name}接取"
            })

        return self.entities, self.relations