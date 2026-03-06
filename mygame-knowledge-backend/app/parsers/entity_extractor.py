import re
import jieba
import jieba.posseg as pseg
from typing import List, Dict, Any, Set, Optional
from loguru import logger

class GameEntityExtractor:
    """游戏实体提取器"""
    
    def __init__(self):
        # 初始化自定义词典
        self._init_dictionary()
        
        # 实体类型关键词
        self.entity_keywords = {
            "pet": ["幻兽", "宠物", "宝宝", "坐骑"],
            "skill": ["技能", "天赋", "魔法", "战技"],
            "equipment": ["装备", "武器", "防具", "饰品", "项链", "戒指"],
            "item": ["道具", "药品", "材料", "卷轴"],
            "map": ["地图", "场景", "区域", "副本"],
            "npc": ["NPC", "商人", "守卫", "长老"],
            "monster": ["怪物", "BOSS", "精英", "守卫"]
        }
        
        # 属性关键词
        self.attr_keywords = {
            "攻击": ["攻击", "伤害", "力量"],
            "防御": ["防御", "护甲", "格挡"],
            "生命": ["生命", "血量", "HP"],
            "魔法": ["魔法", "法力", "MP"],
            "速度": ["速度", "敏捷", "攻速"],
            "暴击": ["暴击", "致命", "会心"],
            "命中": ["命中", "精准"],
            "闪避": ["闪避", "躲避"]
        }
        
    def _init_dictionary(self):
        """初始化词典"""
        # 添加游戏专有名词
        game_words = [
            "幻兽", "魔域", "奇迹龙", "众神之袍", "冰封要塞",
            "战斗力", "魔石", "幻化", "出征", "合体"
        ]
        for word in game_words:
            jieba.add_word(word)
            
    def extract_entities(self, text: str, page_type: str = None) -> List[Dict[str, Any]]:
        """从文本中提取实体"""
        entities = []
        
        # 分词和词性标注
        words = pseg.cut(text)
        
        # 统计词频
        word_freq = {}
        entity_candidates = {}
        
        for word, flag in words:
            # 过滤掉单字和标点
            if len(word) < 2:
                continue
                
            # 统计词频
            word_freq[word] = word_freq.get(word, 0) + 1
            
            # 识别可能的实体（名词）
            if flag.startswith('n'):
                entity_type = self._classify_entity(word, text)
                if entity_type:
                    if word not in entity_candidates:
                        entity_candidates[word] = {
                            "name": word,
                            "type": entity_type,
                            "count": 0,
                            "contexts": []
                        }
                    entity_candidates[word]["count"] += 1
                    
        # 提取上下文
        for word, cand in entity_candidates.items():
            if cand["count"] >= 2:  # 出现至少2次
                context = self._extract_context(text, word)
                if context:
                    cand["contexts"].append(context)
                    
                # 提取属性
                attributes = self._extract_attributes(context, cand["type"])
                
                entities.append({
                    "name": word,
                    "type": cand["type"],
                    "attributes": attributes,
                    "confidence": min(cand["count"] / 10, 1.0)
                })
                
        # 如果指定了页面类型，过滤实体
        if page_type:
            entities = [e for e in entities if e["type"] == page_type or e["confidence"] > 0.5]
            
        logger.info(f"提取到 {len(entities)} 个实体")
        return entities[:10]  # 最多返回10个
        
    def _classify_entity(self, word: str, context: str) -> str:
        """判断实体类型"""
        # 检查上下文中的关键词
        context_lower = context.lower()
        
        for entity_type, keywords in self.entity_keywords.items():
            for keyword in keywords:
                if keyword in context_lower:
                    # 检查词性
                    return entity_type
                    
        # 默认类型
        return "unknown"
        
    def _extract_context(self, text: str, word: str, window: int = 30) -> str:
        """提取上下文"""
        # 找到词的位置
        pattern = re.compile(re.escape(word))
        match = pattern.search(text)
        
        if match:
            start = max(0, match.start() - window)
            end = min(len(text), match.end() + window)
            context = text[start:end]
            return context.strip()
            
        return ""
        
    def _extract_attributes(self, context: str, entity_type: str) -> Dict[str, Any]:
        """从上下文中提取属性"""
        attributes = {}
        
        # 提取数值属性
        numbers = re.findall(r'(\d+\.?\d*)', context)
        
        # 根据实体类型提取特定属性
        if entity_type == "pet":
            # 提取等级
            level_match = re.search(r'等级[：:]?\s*(\d+)', context)
            if level_match:
                attributes["level"] = int(level_match.group(1))
                
            # 提取元素
            elements = ["火", "水", "土", "风", "光", "暗"]
            for elem in elements:
                if elem in context:
                    attributes["element"] = elem
                    break
                    
        elif entity_type == "equipment":
            # 提取品质
            qualities = ["白", "绿", "蓝", "紫", "橙", "红"]
            for q in qualities:
                if q in context:
                    attributes["quality"] = q
                    break
                    
        # 提取通用属性
        for attr_name, keywords in self.attr_keywords.items():
            for keyword in keywords:
                if keyword in context:
                    # 查找附近的数值
                    nearby_num = self._find_nearby_number(context, keyword)
                    if nearby_num:
                        attributes[attr_name] = nearby_num
                        break
                        
        return attributes
        
    def _find_nearby_number(self, text: str, keyword: str) -> Optional[int]:
        """在关键词附近查找数值"""
        # 查找关键词位置
        keyword_pos = text.find(keyword)
        if keyword_pos == -1:
            return None
            
        # 在关键词前后查找数字
        search_area = text[max(0, keyword_pos - 20):min(len(text), keyword_pos + 20)]
        numbers = re.findall(r'(\d+\.?\d*)', search_area)
        
        if numbers:
            return float(numbers[0])
        return None