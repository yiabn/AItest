# app/crawlers/m99_crawler.py
import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional

# 修复导入路径：从 app/ 目录下导入（适配你的实际结构）
from app.parsers.skill_parser import SkillParser
from app.parsers.quest_parser import QuestParser
from app.parsers.equipment_parser import EquipmentParser
from app.parsers.base_parser import BaseGameParser

class M99Crawler:
    """魔域爬虫增强版：整合专用解析器"""
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        # 页面类型→解析器映射
        self.parser_map = {
            "skill": SkillParser,
            "quest": QuestParser,
            "equipment": EquipmentParser,
            # 可扩展其他类型：pet/activity等
        }

    def _fetch_html(self, url: str) -> Optional[str]:
        """基础爬取：获取页面HTML"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            return response.text
        except Exception as e:
            print(f"❌ 爬取失败 {url}: {str(e)}")
            return None

    def _judge_page_type(self, html: str) -> str:
        """判断页面类型（原有逻辑，可优化）"""
        soup = BeautifulSoup(html, "lxml")
        # 示例规则：根据页面特征判断类型
        if "skill-name" in html or "技能" in soup.title.text:
            return "skill"
        elif "quest-name" in html or "任务" in soup.title.text:
            return "quest"
        elif "equip-name" in html or "装备" in soup.title.text:
            return "equipment"
        else:
            return "unknown"

    def crawl_and_parse(self, url: str) -> Dict:
        """核心方法：爬取+解析→返回实体+关系+html"""
        # 1. 爬取页面
        html = self._fetch_html(url)
        if not html:
            return {"entities": [], "relations": [], "page_type": "unknown", "html": ""}
        
        # 2. 判断页面类型
        page_type = self._judge_page_type(html)
        
        # 3. 选择解析器
        parser_cls: BaseGameParser = self.parser_map.get(page_type)
        if not parser_cls:
            return {"entities": [], "relations": [], "page_type": page_type, "html": html}
        
        # 4. 解析页面
        parser = parser_cls(html, url)
        entities, relations = parser.parse()

        return {
            "entities": entities,
            "relations": relations,
            "page_type": page_type,
            "source_url": url,
            "html": html  # 新增：返回页面HTML
        }