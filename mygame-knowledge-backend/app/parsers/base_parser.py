# backend/parsers/base_parser.py
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple, Optional

class BaseGameParser(ABC):
    """游戏页面解析器基类：定义统一解析接口"""
    def __init__(self, html: str, url: str):
        self.soup = BeautifulSoup(html, "lxml")  # 用lxml提升解析速度
        self.url = url
        self.entities: List[Dict] = []  # 提取的实体列表
        self.relations: List[Dict] = []  # 提取的关系列表

    @abstractmethod
    def parse(self) -> Tuple[List[Dict], List[Dict]]:
        """核心解析方法：返回(实体列表, 关系列表)"""
        pass

    def extract_text(self, selector: str, default: str = "") -> str:
        """通用CSS选择器文本提取"""
        elem = self.soup.select_one(selector)
        return elem.get_text(strip=True) if elem else default

    def extract_table(self, selector: str) -> List[Dict]:
        """通用表格解析（游戏属性表/技能表）"""
        table = self.soup.select_one(selector)
        if not table:
            return []
        
        rows = table.find_all("tr")
        parsed_table = []
        for row in rows:
            # 支持th/td混合的表格
            cols = row.find_all(["th", "td"])
            cols = [col.get_text(strip=True).replace("\xa0", "") for col in cols]
            if len(cols) >= 2:  # 至少key-value对
                parsed_table.append({
                    "key": cols[0],
                    "value": cols[1]
                })
        return parsed_table

    def extract_links(self, selector: str) -> List[Tuple[str, str]]:
        """提取链接（用于关系识别：如幻兽→技能链接）"""
        links = self.soup.select(selector)
        return [(link.get_text(strip=True), link.get("href", "")) for link in links]

    def normalize_attr_key(self, key: str, attr_type: str = "common") -> str:
        """标准化属性名（基于游戏术语）"""
        from app.utils.term_dict import term_mapping
        return term_mapping.get(attr_type, {}).get(key, key)